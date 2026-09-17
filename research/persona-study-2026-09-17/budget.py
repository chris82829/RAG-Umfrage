#!/usr/bin/env python3
"""Offline, fail-closed reservation ledger for the bounded ABC Responses pilot.

Call begin BEFORE a single HTTP POST, with transport/SDK retries disabled.
Every reserved ID is permanently consumed, also across restarts or uncertain
responses. Unknown usage retains the full reservation. This module performs no
network requests and stores no prompts, credentials or provider error messages.

Reservation: compact JSON UTF-8 bytes + 8192 input tokens, plus the explicit
max_output_tokens. Combined input/output bound must fit 272000 tokens. Fixed
undiscounted prices and optional generation allocation leave budget for judging.
This conservative accounting rule is not a provider tokenization guarantee.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import fcntl
import json
import os
from pathlib import Path
import tempfile
import threading
from typing import Any, Mapping

SCHEMA_VERSION = 1
ABSOLUTE_BUDGET_USD = Decimal('4.50')
ABSOLUTE_MAX_POSTS = 80
MAX_CONTEXT_TOKENS = 272000
INPUT_TOKEN_OVERHEAD = 8192
MILLION = Decimal(1000000)
GENERATION_MODEL = 'gpt-5.4-2026-03-05'
PRICES = {
    GENERATION_MODEL: {'input': Decimal('2.50'), 'output': Decimal('15')},
}
RESERVATION_RULE = 'compact_json_utf8_bytes_plus_8192_input_and_max_output_tokens_output'


class BudgetError(RuntimeError):
    """A request must not be sent."""


class BudgetExceeded(BudgetError):
    pass


class DuplicateTask(BudgetError):
    pass


class InvalidPayload(BudgetError):
    pass


class LedgerIntegrityError(BudgetError):
    pass


@dataclass(frozen=True)
class Reservation:
    task_id: str
    model: str
    serialized_input_bytes: int
    max_tokens: int
    reserved_usd: Decimal
    post_number: int


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _money(value: Decimal) -> str:
    return format(value, 'f')


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _task_id(value: Any) -> str:
    if (not isinstance(value, str) or not value or len(value) > 200
            or not value.isascii() or not all(c.isalnum() or c in '._:-' for c in value)):
        raise BudgetError('A stable ASCII identifier of at most 200 safe characters is required.')
    return value


def _allocation(model: str) -> str:
    if model != GENERATION_MODEL:
        raise InvalidPayload('Only the frozen production model is permitted.')
    return 'generation'


def _reservation_cost(model: str, input_bound: int, output_bound: int) -> Decimal:
    price = PRICES[model]
    return (Decimal(input_bound) * price['input'] + Decimal(output_bound) * price['output']) / MILLION


def _plain_text_input(value: Any) -> bool:
    """No server-resolved IDs, images or files outside the serialized bound."""
    if isinstance(value, str):
        return True
    if not isinstance(value, list) or not value:
        return False
    for message in value:
        if (not isinstance(message, Mapping)
                or set(message) - {'type', 'role', 'content'}
                or message.get('type', 'message') != 'message'
                or message.get('role') not in ('system', 'developer', 'user', 'assistant')):
            return False
        content = message.get('content')
        if isinstance(content, str):
            continue
        if not isinstance(content, list) or not content:
            return False
        for part in content:
            if (not isinstance(part, Mapping) or set(part) != {'type', 'text'}
                    or part['type'] != 'input_text' or not isinstance(part['text'], str)):
                return False
    return True


def estimate_reservation(payload: Mapping[str, Any]) -> dict:
    """Validate a Responses payload and compute its worst-case USD reservation."""
    if not isinstance(payload, Mapping):
        raise InvalidPayload('The JSON payload must be a mapping.')
    model = payload.get('model')
    if not isinstance(model, str) or model not in PRICES:
        raise InvalidPayload('The model is outside the fixed price allowlist.')
    maximum = payload.get('max_output_tokens')
    if not _positive_int(maximum):
        raise InvalidPayload('A positive integer max_output_tokens is required.')
    if payload.get('store') is not False:
        raise InvalidPayload('store=false is required.')
    reasoning = payload.get('reasoning')
    if not isinstance(reasoning, Mapping) or reasoning.get('effort') != 'none':
        raise InvalidPayload('reasoning.effort=none is required.')
    if payload.get('service_tier') != 'default':
        raise InvalidPayload('An explicit default service tier is required.')
    if payload.get('tools') not in (None, []):
        raise InvalidPayload('Tools with additional billing are prohibited.')
    if payload.get('background') not in (None, False):
        raise InvalidPayload('Background requests are prohibited.')
    if any(payload.get(k) is not None for k in ('previous_response_id', 'conversation')):
        raise InvalidPayload('Server-side context is excluded from the input bound.')
    if payload.get('prompt') is not None or not _plain_text_input(payload.get('input')):
        raise InvalidPayload('Only explicit text messages without stored prompts, files or images are allowed.')
    if payload.get('instructions') is not None and not isinstance(payload['instructions'], str):
        raise InvalidPayload('Instructions must be explicit text.')
    try:
        serialized = json.dumps(dict(payload), ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, OverflowError, UnicodeError, RecursionError):
        raise InvalidPayload('The payload must serialize as finite UTF-8 JSON.') from None
    size = len(serialized)
    bound = size + INPUT_TOKEN_OVERHEAD
    if bound + maximum > MAX_CONTEXT_TOKENS:
        raise InvalidPayload('The conservative input/output bound exceeds 272000 tokens.')
    return {'model': model, 'allocation': _allocation(model), 'serialized_input_bytes': size,
            'input_token_bound': bound, 'max_tokens': maximum,
            'reserved_usd': _money(_reservation_cost(model, bound, maximum))}


def _usage_tokens(usage: Any) -> dict | None:
    if not isinstance(usage, Mapping):
        return None
    result = {}
    for key in ('input_tokens', 'output_tokens'):
        if key not in usage or not _nonnegative_int(usage[key]):
            return None
        result[key] = usage[key]
    total = result['input_tokens'] + result['output_tokens']
    if 'total_tokens' in usage and (not _nonnegative_int(usage['total_tokens']) or usage['total_tokens'] != total):
        return None
    # Conflicting legacy aliases are not complete trustworthy usage.
    for alias, key in (('prompt_tokens', 'input_tokens'), ('completion_tokens', 'output_tokens')):
        if alias in usage and (not _nonnegative_int(usage[alias]) or usage[alias] != result[key]):
            return None
    result['total_tokens'] = total
    return result


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


class BudgetLedger:
    """Atomically enforce global/per-model allocations under thread + process lock.

    check_plan validates a supplied request group but does NOT reserve it.
    The runner must call begin before each POST; begin rechecks current limits
    atomically. Only the frozen production model is allowed, never a judge API.
    Every entry counts towards max_posts, even if no POST ultimately was sent.
    generation_budget_usd=None disables only the extra generation allocation.
    """

    def __init__(self, path: str | Path, budget_usd: str | Decimal = '4.50',
                 max_posts: int = 80, generation_budget_usd: str | Decimal | None = None):
        try:
            budget = Decimal(str(budget_usd))
            generation = None if generation_budget_usd is None else Decimal(str(generation_budget_usd))
        except (InvalidOperation, TypeError, ValueError):
            raise BudgetError('Invalid USD budget.') from None
        if not budget.is_finite() or not Decimal('0') < budget <= ABSOLUTE_BUDGET_USD:
            raise BudgetError('Budget must be positive and at most 4.50 USD.')
        if generation is not None and (not generation.is_finite() or not Decimal('0') <= generation <= budget):
            raise BudgetError('Generation allocation must be finite and between zero and the global budget.')
        if not _positive_int(max_posts) or max_posts > ABSOLUTE_MAX_POSTS:
            raise BudgetError('The POST ceiling must be between 1 and 80.')
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path = self.path.with_name(self.path.name + '.lock')
        self._thread_lock = threading.RLock()
        self.budget_usd = budget
        self.generation_budget_usd = generation
        self.max_posts = max_posts
        with self._locked():
            if self.path.exists():
                self._read()
            else:
                self._write({'schema_version': SCHEMA_VERSION, 'currency': 'USD',
                             'budget_usd': _money(budget), 'max_posts': max_posts,
                             'generation_budget_usd': None if generation is None else _money(generation),
                             'prices_per_million_tokens': self._price_json(),
                             'reservation_rule': RESERVATION_RULE, 'context_bound_tokens': MAX_CONTEXT_TOKENS,
                             'created_utc': _utc(), 'halted_reason': None, 'entries': {}})

    @staticmethod
    def _price_json() -> dict:
        return {model: {kind: _money(value) for kind, value in price.items()} for model, price in PRICES.items()}

    @contextmanager
    def _locked(self):
        with self._thread_lock:
            with self._lock_path.open('a+b') as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _read(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'), object_pairs_hook=_unique_object)
            expected_generation = None if self.generation_budget_usd is None else _money(self.generation_budget_usd)
            if (data['schema_version'] != SCHEMA_VERSION or data['currency'] != 'USD'
                    or Decimal(data['budget_usd']) != self.budget_usd
                    or data['generation_budget_usd'] != expected_generation
                    or data['max_posts'] != self.max_posts
                    or data['prices_per_million_tokens'] != self._price_json()
                    or data['reservation_rule'] != RESERVATION_RULE
                    or data['context_bound_tokens'] != MAX_CONTEXT_TOKENS
                    or not isinstance(data['entries'], dict)):
                raise ValueError
            numbers = []
            for task_id, entry in data['entries'].items():
                _task_id(task_id)
                if (entry['task_id'] != task_id or entry['model'] not in PRICES
                        or entry['allocation'] != _allocation(entry['model'])
                        or entry['status'] not in ('in_flight', 'uncertain', 'settled')
                        or not _positive_int(entry['post_number'])
                        or not _positive_int(entry['max_tokens'])
                        or not _nonnegative_int(entry['serialized_input_bytes'])
                        or not _positive_int(entry['input_token_bound'])
                        or entry['input_token_bound'] != entry['serialized_input_bytes'] + INPUT_TOKEN_OVERHEAD
                        or entry['input_token_bound'] + entry['max_tokens'] > MAX_CONTEXT_TOKENS):
                    raise ValueError
                numbers.append(entry['post_number'])
                reserve = Decimal(entry['reserved_usd'])
                charged = Decimal(entry['charged_usd'])
                if (not reserve.is_finite() or not charged.is_finite() or charged < 0
                        or reserve != _reservation_cost(entry['model'], entry['input_token_bound'], entry['max_tokens'])):
                    raise ValueError
                if entry['status'] == 'settled':
                    tokens = _usage_tokens(entry['usage'])
                    if tokens is None or charged != _reservation_cost(entry['model'], tokens['input_tokens'], tokens['output_tokens']):
                        raise ValueError
                    if (charged > reserve or tokens['input_tokens'] > entry['input_token_bound']
                            or tokens['output_tokens'] > entry['max_tokens']) and not data.get('halted_reason'):
                        raise ValueError
                elif charged != reserve or entry['usage'] is not None:
                    raise ValueError
            if sorted(numbers) != list(range(1, len(numbers) + 1)) or len(numbers) > self.max_posts:
                raise ValueError
            committed = sum((Decimal(e['charged_usd']) for e in data['entries'].values()), Decimal('0'))
            generation = sum((Decimal(e['charged_usd']) for e in data['entries'].values()
                              if e['allocation'] == 'generation'), Decimal('0'))
            if (committed > self.budget_usd or (self.generation_budget_usd is not None
                    and generation > self.generation_budget_usd)) and not data.get('halted_reason'):
                raise ValueError
            return data
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, InvalidOperation, BudgetError):
            raise LedgerIntegrityError('Ledger is unreadable or inconsistent; sending requests is prohibited.') from None

    def _write(self, data: dict) -> None:
        data['updated_utc'] = _utc()
        text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        fd, name = tempfile.mkstemp(prefix='.' + self.path.name + '.', suffix='.tmp', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.path)
            directory_fd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def _snapshot(self, data: dict) -> dict:
        amounts = {status: sum((Decimal(e['charged_usd']) for e in data['entries'].values() if e['status'] == status), Decimal('0'))
                   for status in ('in_flight', 'uncertain', 'settled')}
        committed = sum(amounts.values(), Decimal('0'))
        generation = sum((Decimal(e['charged_usd']) for e in data['entries'].values() if e['allocation'] == 'generation'), Decimal('0'))
        global_available = max(Decimal('0'), self.budget_usd - committed)
        generation_available = global_available if self.generation_budget_usd is None else min(global_available, max(Decimal('0'), self.generation_budget_usd - generation))
        return {'schema_version': SCHEMA_VERSION, 'currency': 'USD',
                'budget_usd': _money(self.budget_usd), 'max_posts': self.max_posts,
                'generation_budget_usd': None if self.generation_budget_usd is None else _money(self.generation_budget_usd),
                'posts_reserved': len(data['entries']), 'posts_remaining': self.max_posts - len(data['entries']),
                'settled_actual_usd': _money(amounts['settled']), 'uncertain_reserved_usd': _money(amounts['uncertain']),
                'in_flight_reserved_usd': _money(amounts['in_flight']), 'committed_usd': _money(committed),
                'available_usd': _money(global_available), 'generation_committed_usd': _money(generation),
                'generation_available_usd': _money(generation_available), 'judge_committed_usd': _money(committed - generation),
                'halted_reason': data.get('halted_reason'), 'entries': data['entries']}

    def snapshot(self) -> dict:
        with self._locked():
            return self._snapshot(self._read())

    def _check(self, data: dict, estimates: dict) -> dict:
        if set(estimates).intersection(data['entries']):
            raise DuplicateTask('A task was already reserved; no retry or reissue is permitted.')
        if data.get('halted_reason'):
            raise BudgetExceeded('The ledger is halted; no requests may be sent.')
        snapshot = self._snapshot(data)
        planned = sum((Decimal(e['reserved_usd']) for e in estimates.values()), Decimal('0'))
        generation = sum((Decimal(e['reserved_usd']) for e in estimates.values() if e['allocation'] == 'generation'), Decimal('0'))
        combined = Decimal(snapshot['committed_usd']) + planned
        if len(data['entries']) + len(estimates) > self.max_posts or combined > self.budget_usd:
            raise BudgetExceeded('The complete worst-case plan exceeds the global budget or POST ceiling.')
        if self.generation_budget_usd is not None and Decimal(snapshot['generation_committed_usd']) + generation > self.generation_budget_usd:
            raise BudgetExceeded('The plan exceeds the generation allocation reserved for this pilot.')
        return {'planned_posts': len(estimates), 'planned_worst_case_usd': _money(planned),
                'planned_generation_usd': _money(generation), 'combined_worst_case_usd': _money(combined),
                'budget_usd': _money(self.budget_usd), 'max_posts': self.max_posts, 'estimates': estimates}

    def check_plan(self, tasks: Mapping[str, Mapping[str, Any]]) -> dict:
        """Read-only group sufficiency check; every begin still rechecks limits."""
        if not isinstance(tasks, Mapping) or not tasks:
            raise BudgetError('The plan must map nonempty unique task identifiers to payloads.')
        estimates = {_task_id(task_id): estimate_reservation(payload) for task_id, payload in tasks.items()}
        with self._locked():
            return self._check(self._read(), estimates)

    def begin(self, task_id: str, payload: Mapping[str, Any]) -> Reservation:
        """Persist full reservation before exactly one attempted HTTP POST."""
        task_id = _task_id(task_id)
        estimate = estimate_reservation(payload)
        with self._locked():
            data = self._read()
            self._check(data, {task_id: estimate})
            post_number = len(data['entries']) + 1
            data['entries'][task_id] = {**estimate, 'task_id': task_id, 'post_number': post_number,
                                       'status': 'in_flight', 'charged_usd': estimate['reserved_usd'],
                                       'usage': None, 'created_utc': _utc(), 'settled_utc': None,
                                       'reservation_overrun': False}
            self._write(data)
            return Reservation(task_id, estimate['model'], estimate['serialized_input_bytes'],
                               estimate['max_tokens'], Decimal(estimate['reserved_usd']), post_number)

    def settle(self, task_id: str, usage: Mapping[str, Any] | None = None) -> dict:
        """Settle complete provider usage once; otherwise retain full reserve."""
        task_id = _task_id(task_id)
        tokens = _usage_tokens(usage)
        with self._locked():
            data = self._read()
            entry = data['entries'].get(task_id)
            if entry is None:
                raise BudgetError('Cannot settle an unreserved task.')
            if entry['status'] != 'in_flight':
                raise DuplicateTask('An entry may be settled only once.')
            entry['settled_utc'] = _utc()
            if tokens is None:
                entry.update(status='uncertain', usage=None, charged_usd=entry['reserved_usd'],
                             accounting_reason='usage_unavailable_or_invalid_full_reserve_retained')
            else:
                actual = _reservation_cost(entry['model'], tokens['input_tokens'], tokens['output_tokens'])
                overrun = (actual > Decimal(entry['reserved_usd']) or tokens['input_tokens'] > entry['input_token_bound'] or tokens['output_tokens'] > entry['max_tokens'])
                entry.update(status='settled', usage=tokens, charged_usd=_money(actual),
                             accounting_reason='provider_token_usage', reservation_overrun=overrun)
                if overrun:
                    data['halted_reason'] = 'provider_usage_exceeded_conservative_reservation_bound'
            self._write(data)
            return dict(entry)
