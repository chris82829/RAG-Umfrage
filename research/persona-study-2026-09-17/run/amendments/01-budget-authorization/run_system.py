#!/usr/bin/env python3
"""Two synthetic users through A/B/C and three adaptive messages each.

prepare is offline. run explicitly permits bounded production-model requests.
No user simulator or relevance-judge API is used. Codex writes each message
after reading the preceding actual response; message inputs are hash-bound.
Only a jobs-only temporary database is created; no real survey data is opened.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import platform
import random
import re
import sqlite3
import sys
import tempfile
import threading
import time
from types import SimpleNamespace

STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(STUDY))

import httpx
from dotenv import dotenv_values
from openai.lib._parsing._responses import type_to_text_format_param
from app import create_app
from advisor import AdvisorConfig
from data_store import JobStore
from llm_service import MODEL, REASONING_EFFORT, MAX_OUTPUT_TOKENS, RERANK_OUTPUT_TOKENS, OpenAIService
from retrieval import HybridRetriever, MODEL_ID, MODEL_REVISION
from schemas import Profile, SearchInput
from budget import BudgetLedger, BudgetError, _usage_tokens
from persona_mlds import load_standard_advisor, load_templates

ENDPOINT = 'https://api.openai.com/v1/responses'
SEED = 20260917
DEFAULT_OUT = STUDY / 'run'
EXPECTED_MODEL = 'gpt-5.4-2026-03-05'
BUDGET_USD = '3'
MAX_POSTS = 80
MAX_WORKERS = 2
TLS = threading.local()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name, delete=False) as handle:
        temp = Path(handle.name)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def load_cases(path):
    data = read(path)
    cases = data.get('personas', data.get('cases')) if isinstance(data, dict) else data
    if not isinstance(cases, list) or len(cases) != 6:
        raise ValueError('Exactly two personas in all three arms are required.')
    ids = []
    for row in cases:
        cid = row.get('case_id', row['id'])
        row['case_id'] = cid
        row['start_profile'] = row['initial_profile']
        arm = row['assigned_arm']
        if arm not in ('A', 'B', 'C'):
            raise ValueError('Unknown study arm.')
        row['advisor'] = (load_standard_advisor() if arm == 'A' else
                          load_templates()[row['preferred_template']]['advisor'] if arm == 'B' else row['advisor_config'])
        row['selection'] = (None if arm == 'A' else
                            {'source': 'template', 'template_id': row['preferred_template']} if arm == 'B' else
                            {'source': 'custom', 'template_id': None})
        if not isinstance(cid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', cid):
            raise ValueError('Unsafe case identifier.')
        if row.get('fictional') is not True:
            raise ValueError('Only synthetic personas are permitted.')
        ids.append(cid)
        Profile.model_validate(row['start_profile'])
        Profile.model_validate(row['full_profile'])
        advisor = AdvisorConfig.model_validate(row['advisor'])
        row['advisor'] = advisor.model_dump()
        if arm == 'C' and advisor.mode != 'custom':
            raise ValueError('C requires a custom configuration.')
        messages = row['planned_messages']
        if not isinstance(messages, list) or len(messages) != 3 or any(
            not isinstance(m, str) or not m.strip() or len(m) > 3000 for m in messages
        ):
            raise ValueError('Each persona requires three planned information stages.')
        row['messages'] = messages
        SearchInput.model_validate({'profile': row['start_profile'], 'advisor': row['advisor'],
                                    'advisor_selection': row['selection']})
    if len(set(ids)) != 6:
        raise ValueError('Persona identifiers must be unique.')
    sources = {row['source_id'] for row in cases}
    if len(sources) != 2:
        raise ValueError('Exactly two underlying personas required.')
    for source in sources:
        group = [row for row in cases if row['source_id'] == source]
        if {row['assigned_arm'] for row in group} != {'A', 'B', 'C'}:
            raise ValueError('Each persona must occur once in every arm.')
        for field in ('initial_profile', 'full_profile', 'full_information_need', 'adaptive_message_stages'):
            if any(row[field] != group[0][field] for row in group):
                raise ValueError('Information differs across arms: ' + field)
    return cases


def source_paths():
    # test_access.py is application code, despite its name.
    result = [p for p in ROOT.glob('*.py') if not p.name.startswith('test_') or p.name == 'test_access.py']
    result += list(ROOT.glob('survey_definition*.json'))
    result += [p for p in (ROOT / 'personas').glob('*') if p.is_file()]
    result += [STUDY / 'run_system.py', STUDY / 'budget.py', STUDY / 'metrics.py', STUDY / 'PROTOCOL.md']
    return sorted(set(result))


def verify(out):
    manifest = read(out / 'manifest.json')
    for name, expected in manifest['source_sha256'].items():
        if sha(ROOT / name) != expected or sha(out / 'source' / name) != expected:
            raise RuntimeError('Frozen production or runner source changed: ' + name)
    for name, expected in manifest['input_sha256'].items():
        if sha(out / name) != expected:
            raise RuntimeError('Frozen study input changed: ' + name)
    return manifest


def prepare(out, personas, corpus_db):
    if (out / 'manifest.json').exists():
        verify(out)
        print('Prepared files already exist and match their hashes; nothing overwritten.', flush=True)
        return
    if MODEL != EXPECTED_MODEL or REASONING_EFFORT != 'none':
        raise RuntimeError('Unexpected production model/settings; review protocol before preparation.')
    cases = load_cases(personas)
    with sqlite3.connect(corpus_db.resolve().as_uri() + '?mode=ro', uri=True) as db:
        jobs = [json.loads(row[0]) for row in db.execute('SELECT payload FROM jobs ORDER BY id')]
    if len(jobs) != 8537 or len({j['id'] for j in jobs}) != len(jobs):
        raise RuntimeError('Expected the unchanged original 8,537 distinct job records.')
    out.mkdir(parents=True, exist_ok=True)
    save(out / 'personas.json', cases)
    with gzip.GzipFile(filename=str(out / 'corpus.json.gz'), mode='wb', mtime=0) as handle:
        handle.write(json.dumps(jobs, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode())
    frozen = {}
    for path in source_paths():
        name = path.relative_to(ROOT).as_posix()
        destination = out / 'source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())
        frozen[name] = sha(path)
    packages = {}
    for name in ['openai', 'httpx', 'Flask', 'pydantic', 'torch', 'transformers', 'sentence-transformers', 'numpy', 'rank-bm25']:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    save(out / 'manifest.json', {
        'created_utc': now(), 'synthetic': True, 'conditions': ['A','B','C'], 'planned_personas': 2,
        'planned_sessions': 6, 'messages_per_session': 3, 'snapshots_per_session': 4, 'planned_snapshots': 24,
        'model': MODEL, 'reasoning_effort': REASONING_EFFORT, 'chat_persona_output_limit': MAX_OUTPUT_TOKENS,
        'rerank_output_limit': RERANK_OUTPUT_TOKENS, 'store': False, 'service_tier': 'default',
        'streaming_tested': False, 'http_retries': 0, 'endpoint': ENDPOINT,
        'embedding_model': MODEL_ID, 'embedding_revision': MODEL_REVISION,
        'max_workers': MAX_WORKERS, 'budget_usd': BUDGET_USD, 'max_posts': MAX_POSTS,
        'judge': 'Codex assistant reads shuffled complete job texts; no separate judge API',
        'simulator': 'Codex composes three adaptive messages against frozen information stages; no simulator API',
        'database_isolation': 'Jobs-only temporary database; no real survey rows or assignments',
        'application_entrypoints': ['/api/onboard', '/api/chat'], 'chat_mode': 'auto',
        'personality_policy': 'Production A/B/C rules enforced via separate X-Diana-Test contexts and isolated synthetic consent',
        'job_count': len(jobs), 'python': platform.python_version(), 'packages': packages,
        'shuffle_seed': SEED, 'source_sha256': frozen,
        'input_sha256': {name: sha(out / name) for name in ['personas.json', 'corpus.json.gz']},
    })
    save(out / 'preparation.json', {'prepared_utc': now(), 'paid_requests': 0, 'personas': 2, 'sessions': 6, 'jobs': len(jobs)})
    print('Prepared two personas in A/B/C against 8,537 original jobs. No API calls.', flush=True)


class StudyHalted(RuntimeError):
    pass


class Runtime:
    def __init__(self, out, key):
        self.out, self.key = out, key
        self.ledger = BudgetLedger(out / 'budget-ledger.json', budget_usd=BUDGET_USD,
                                   max_posts=MAX_POSTS, generation_budget_usd=None)
        self.lock = threading.RLock()
        self.stop = threading.Event()
        if (out / 'halt.json').exists():
            raise StudyHalted('Recorded halt requires review; no automatic retries.')
        ledger = self.ledger.snapshot()
        if ledger['uncertain_reserved_usd'] != '0' or ledger['in_flight_reserved_usd'] != '0' or ledger['halted_reason']:
            raise StudyHalted('Uncertain prior billing or ledger halt; no further calls.')

    def halt(self, reason, task=None):
        with self.lock:
            self.stop.set()
            if not (self.out / 'halt.json').exists():
                save(self.out / 'halt.json', {'utc': now(), 'reason': reason, 'task': task})

    def reserve(self, task, payload):
        with self.lock:
            if self.stop.is_set():
                raise StudyHalted('Run halted before request.')
            verify(self.out)
            save(self.out / 'requests' / (task + '.json'), payload)
            return self.ledger.begin(task, payload)


class RecordedResponses:
    def __init__(self, runtime):
        self.runtime = runtime

    def parse(self, **options):
        runtime = self.runtime
        schema = options.pop('text_format')
        if options['model'] != EXPECTED_MODEL or options.get('reasoning') != {'effort': 'none'}:
            raise RuntimeError('Unexpected production request configuration.')
        options.update(text={'format': type_to_text_format_param(schema)}, service_tier='default')
        if not options.get('max_output_tokens'):
            raise RuntimeError('Production requests must have finite output limits.')
        TLS.counter += 1
        task = f'{TLS.case_id}.T{TLS.turn}.{schema.__name__}.{TLS.counter:02d}'
        runtime.reserve(task, options)
        record = {'task': task, 'started_utc': now(), 'ok': False, 'request_sha256': sha(runtime.out / 'requests' / (task + '.json'))}
        usage = None
        try:
            with httpx.Client(timeout=180, transport=httpx.HTTPTransport(retries=0), follow_redirects=False) as client:
                response = client.post(ENDPOINT, headers={'Authorization': 'Bearer ' + runtime.key}, json=options)
            record['http_status'] = response.status_code
            if response.status_code != 200:
                runtime.halt('provider_http_' + str(response.status_code), task)
                raise StudyHalted('Provider request failed; no retry.')
            body = response.json()
            usage = body.get('usage')
            # Keep provider metadata and generated content, never request headers.
            record.update(response=body, usage=usage)
            if _usage_tokens(usage) is None:
                runtime.halt('usage_missing_or_invalid', task)
                raise StudyHalted('Usage unavailable; retaining complete reservation.')
            if body.get('status') != 'completed' or body.get('model') != EXPECTED_MODEL:
                raise ValueError('Unexpected model or incomplete provider response.')
            result_text = ''.join(part['text'] for item in body.get('output', []) if item.get('type') == 'message'
                                  for part in item.get('content', []) if part.get('type') == 'output_text')
            parsed = schema.model_validate_json(result_text)
            record.update(ok=True, result=parsed.model_dump(), raw_text=result_text)
            return SimpleNamespace(status='completed', output_parsed=parsed,
                                   usage=SimpleNamespace(**usage))
        except Exception as error:
            record['error_type'] = type(error).__name__
            runtime.halt('request_error_' + type(error).__name__, task)
            raise
        finally:
            record['finished_utc'] = now()
            record['budget'] = runtime.ledger.settle(task, usage)
            if record['budget']['status'] != 'settled' or record['budget']['reservation_overrun']:
                runtime.halt('uncertain_billing_or_reservation_overrun', task)
            save(runtime.out / 'raw' / (task + '.json'), record)
            print(task, 'OK' if record['ok'] else 'FAILED', 'USD', record['budget']['charged_usd'], flush=True)


class LockedRetriever:
    def __init__(self):
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        import torch
        torch.set_num_threads(2)
        self.engine = HybridRetriever(ROOT / '.cache/embeddings', device='cpu', batch_size=8)
        self.lock = threading.Lock()

    def warm(self):
        with self.lock:
            self.engine.prepare_query_encoder()

    def search(self, jobs, query, top_k=20):
        with self.lock:
            return self.engine.search(jobs, query, top_k=top_k)


def isolated_app(folder, jobs, retriever, language_model):
    database = folder / 'synthetic.sqlite3'
    store = JobStore(database)
    store.initialize()
    with store._connection() as db:
        store._upsert(db, jobs)
    privacy = folder / 'privacy.json'
    save(privacy, dict(approved=False, controller='Synthetic evaluation', retention='Temporary isolated database',
                      openai_processing='Synthetic profiles only', technical_processing='Local test client'))
    return create_app({'TESTING': True, 'DATABASE_PATH': str(database), 'OPENAI_API_KEY': '',
                       'SEED_DUMMY_DATA': False, 'REQUIRE_COMPLETE_INDEX': False,
                       'PRIVACY_REQUIRED': False, 'PERSIST_CHAT_SESSIONS': True,
                       'PRIVACY_SETTINGS_PATH': privacy}, retriever=retriever, llm=language_model)


def write_persona_outputs(out, case, jobs_by_id):
    destination = out / 'cases' / case['case_id']
    snapshots = [read(p) for p in sorted(destination.glob('T[0-3].json'))]
    if not snapshots:
        return
    latest = snapshots[-1]
    save(destination / 'transcript.json', {
        'case_id': case['case_id'], 'source_id': case['source_id'], 'condition': case['assigned_arm'], 'advisor': case['advisor'],
        'messages': latest['public_state']['messages'],
        'operations': [{k: s[k] for k in ['turn', 'action', 'elapsed_seconds', 'profile', 'ranking', 'scores']} for s in snapshots],
    })


def write_judge_pools(out, cases, jobs_by_id):
    for source_id in sorted({case['source_id'] for case in cases}):
        group = [case for case in cases if case['source_id'] == source_id]
        snapshots = [read(path) for case in group for path in sorted((out / 'cases' / case['case_id']).glob('T[0-3].json'))]
        ids = sorted({job_id for snapshot in snapshots for job_id in snapshot['ranking']})
        random.Random(f'{SEED}:{source_id}').shuffle(ids)
        # Do not expose source arm, scores, position, model reasons or timepoint to the judge.
        save(out / 'judge-pools' / (source_id + '.json'), {
            'source_id': source_id, 'synthetic': True,
            'reference_need': group[0]['full_information_need'],
            'reference_profile': group[0]['full_profile'],
            'rubric': group[0]['evaluation_relevance_rules'],
            'complete_snapshots': len(snapshots), 'expected_snapshots': 12,
            'candidate_count': len(ids), 'order': 'deterministically shuffled without source arm or position',
            'jobs': [{k:v for k,v in jobs_by_id[job_id].items() if k not in ('raw','search_text')} for job_id in ids],
        })


def message_input(out, case, turn):
    if turn == 0:
        return None
    path = out / 'messages' / f'{case["case_id"]}.T{turn}.json'
    data = read(path)
    previous = out / 'cases' / case['case_id'] / f'T{turn-1}.json'
    if (data.get('case_id') != case['case_id'] or data.get('turn') != turn
            or data.get('previous_snapshot_sha256') != sha(previous)
            or data.get('disclosed_stage') != turn or not data.get('adaptation_note')):
        raise ValueError('Adaptive message must reference the actual previous response and frozen information stage.')
    if not isinstance(data.get('message'),str) or not data['message'].strip() or len(data['message']) > 3000:
        raise ValueError('Invalid user message.')
    return data


def consent_client(app, case):
    client = app.test_client()
    arm = case['assigned_arm']
    token = hashlib.sha256(('synthetic-evaluation:' + case['case_id']).encode()).hexdigest()
    headers = {'X-Diana-Test': arm, 'X-Diana-Consent': token}
    notice = client.get('/api/privacy',headers=headers).get_json()['notice']
    response = client.post('/api/privacy/consent',headers=headers,
                           json={'token':token,'version':notice['version'],'accepted':True,'purpose':'test_'+arm.lower()})
    if response.status_code != 200:
        raise ValueError('Isolated synthetic consent failed.')
    return client, headers, token, notice


def run_case(case, runtime, retriever, jobs, jobs_by_id, target_turn):
    cid = case['case_id']
    directory = runtime.out / 'cases' / cid
    directory.mkdir(parents=True, exist_ok=True)
    completed = [read(directory / f'T{i}.json') for i in range(4) if (directory / f'T{i}.json').exists()]
    if [s['turn'] for s in completed] != list(range(len(completed))):
        raise RuntimeError('Non-contiguous saved turns; manual review required.')
    if len(completed) > target_turn:
        write_persona_outputs(runtime.out, case, jobs_by_id)
        return {'case_id': cid, 'complete': len(completed)==4, 'snapshots': len(completed), 'already_saved': True}
    next_turn = len(completed)
    if next_turn != target_turn:
        raise RuntimeError('Run each message wave in order; earlier snapshots are required.')
    # Never reissue an incomplete turn, including interruption before a snapshot.
    if any(task.startswith(f'{cid}.T{next_turn}.') for task in runtime.ledger.snapshot()['entries']):
        raise StudyHalted('Incomplete charged turn requires review; it will not be repeated.')
    TLS.case_id, TLS.turn, TLS.counter = cid, next_turn, 0
    model = OpenAIService('', client=SimpleNamespace(responses=RecordedResponses(runtime)),
                          performance_logger=logging.Logger('synthetic-persona-study'))
    try:
        with tempfile.TemporaryDirectory(prefix='diana-synthetic-' + cid + '-') as temporary:
            app = isolated_app(Path(temporary), jobs, retriever, model)
            client, headers, token, notice = consent_client(app,case)
            session_id = None
            if completed:
                # Restore only the exact completed application state in an isolated session.
                session_id = app.extensions['chat_store'].create(deepcopy(completed[-1]['private_state']),
                    before_save=lambda db, sid: app.extensions['privacy_store'].attach(token,notice,'chat',sid,db))
            for turn in [target_turn]:
                if runtime.stop.is_set():
                    raise StudyHalted('Global stop is active.')
                verify(runtime.out)
                TLS.turn, TLS.counter = turn, 0
                adaptive = message_input(runtime.out,case,turn)
                body = ({'profile': case['start_profile'], 'advisor': case['advisor'], 'advisor_selection': case['selection']}
                        if turn == 0 else {'session_id': session_id, 'message': adaptive['message'], 'mode': 'auto'})
                endpoint = '/api/onboard' if turn == 0 else '/api/chat'
                save(directory / f'T{turn}-input.json', {'endpoint': endpoint, 'body': body, 'adaptive_message':adaptive, 'started_utc': now()})
                started = time.monotonic()
                response = client.post(endpoint, json=body, headers=headers)
                public = response.get_json()
                if response.status_code != (201 if turn == 0 else 200) or not isinstance(public, dict) or 'error' in public:
                    save(directory / f'T{turn}-failure.json', {'http_status': response.status_code, 'data': public, 'utc': now()})
                    raise RuntimeError('Application operation failed; no automatic retry.')
                session_id = public['session_id']
                private, version = app.extensions['chat_store'].get(session_id)
                expected_policy = {'A':'standard','B':'templates','C':'configurable'}[case['assigned_arm']]
                if private.get('_study_arm') != case['assigned_arm'] or private.get('_personality_policy') != expected_policy:
                    raise RuntimeError('Production study arm enforcement failed.')
                if public['advisor'] != case['advisor']:
                    raise RuntimeError('The assigned advisor unexpectedly changed.')
                ranking = [j['id'] for j in public['jobs']]
                if len(ranking) != len(set(ranking)) or len(ranking) > 20 or not set(ranking).issubset(jobs_by_id):
                    raise RuntimeError('Invalid application ranking.')
                snapshot = {'case_id': cid, 'source_id':case['source_id'], 'condition': case['assigned_arm'], 'turn': turn, 'completed_utc': now(),
                            'action': public.get('chat_action', 'search'), 'elapsed_seconds': round(time.monotonic() - started, 3),
                            'profile': public['profile'], 'ranking': ranking,
                            'scores': [j['match']['score'] for j in public['jobs']],
                            'public_state': public, 'private_state': private, 'session_version': version,
                            'production_requests_in_turn': TLS.counter}
                save(directory / f'T{turn}.json', snapshot)
                write_persona_outputs(runtime.out, case, jobs_by_id)
                verify(runtime.out)
                print(cid, f'T{turn}', snapshot['action'], len(ranking), 'jobs; snapshot saved', flush=True)
            with sqlite3.connect(app.config['DATABASE_PATH']) as db:
                survey_counts = {table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                                 for table in ['survey_responses', 'survey_drafts', 'study_assignments', 'study_runs']}
            if any(survey_counts.values()):
                raise RuntimeError('Synthetic execution unexpectedly created survey data.')
            save(directory / 'verification.json', {'complete': target_turn==3, 'snapshots': target_turn+1, 'user_messages': target_turn,
                                                    'arm_enforced':case['assigned_arm'], 'personality_policy':expected_policy,
                                                    'isolated_survey_table_counts': survey_counts})
        return {'case_id': cid, 'complete': target_turn==3, 'snapshots': target_turn+1}
    except Exception as error:
        runtime.halt('case_error_' + type(error).__name__, cid)
        write_persona_outputs(runtime.out, case, jobs_by_id)
        saved = len(list(directory.glob('T[0-3].json')))
        save(directory / 'failure.json', {'utc': now(), 'error_type': type(error).__name__, 'saved_snapshots': saved})
        return {'case_id': cid, 'complete': False, 'snapshots': saved, 'error_type': type(error).__name__}


@contextmanager
def exclusive_run(out):
    with (out / '.run.lock').open('a+b') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def run(out, turn, resume=False):
    verify(out)
    if (out / 'run-started.json').exists() and not resume:
        raise StudyHalted('Existing run: explicit --resume required; charged failed turns are never replayed.')
    cases = load_cases(out / 'personas.json')
    # Validate the entire wave before any provider request. Counterbalance arms
    # between the two profiles instead of finishing A for everyone first.
    by_key = {(case['source_id'],case['assigned_arm']):case for case in cases}
    people = sorted({case['source_id'] for case in cases})
    cases = [by_key[key] for key in [(people[0],'A'),(people[1],'B'),(people[0],'B'),
                                    (people[1],'C'),(people[0],'C'),(people[1],'A')]]
    for case in cases:
        if not (out / 'cases' / case['case_id'] / f'T{turn}.json').exists():
            if turn and not (out / 'cases' / case['case_id'] / f'T{turn-1}.json').exists():
                raise RuntimeError('Previous message wave is incomplete.')
            message_input(out,case,turn)
    with gzip.open(out / 'corpus.json.gz', 'rt') as handle:
        jobs = json.load(handle)
    jobs_by_id = {j['id']: j for j in jobs}
    key = dotenv_values(ROOT / '.env').get('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('OpenAI credential unavailable.')
    with exclusive_run(out):
        runtime = Runtime(out, key)
        retriever = LockedRetriever()
        retriever.warm()
        if not (out / 'run-started.json').exists():
            save(out / 'run-started.json', {'utc': now(), 'model': MODEL, 'max_usd': BUDGET_USD,
                                           'max_posts': MAX_POSTS, 'concurrency': MAX_WORKERS})
        results = []
        try:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix='synthetic-abc') as executor:
                futures = {executor.submit(run_case, case, runtime, retriever, jobs, jobs_by_id, turn): case['case_id'] for case in cases}
                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as error:
                        runtime.halt('worker_error_' + type(error).__name__, futures[future])
                        results.append({'case_id': futures[future], 'complete': False, 'error_type': type(error).__name__})
                    save(out / 'progress.json', {'utc': now(), 'results': results,
                                               'turn':turn, 'complete_sessions': sum(r['complete'] for r in results),
                                               'budget': runtime.ledger.snapshot()})
        finally:
            verify(out)
            counts = {case['case_id']: len(list((out / 'cases' / case['case_id']).glob('T[0-3].json'))) for case in cases}
            write_judge_pools(out,cases,jobs_by_id)
            save(out / 'run-status.json', {'finished_utc': now(), 'complete': all(n == 4 for n in counts.values()),
                                          'completed_wave': turn if all(n>turn for n in counts.values()) else None,
                                          'awaiting_next_messages': turn < 3 and all(n>turn for n in counts.values()),
                                          'completed_snapshots': sum(counts.values()), 'snapshots_per_session': counts,
                                          'budget': runtime.ledger.snapshot(), 'halted': runtime.stop.is_set(),
                                          'judge_calls': 0, 'simulator_calls': 0})
            save(out / 'artifact-sha256.json', {p.relative_to(out).as_posix(): sha(p) for p in sorted(out.rglob('*'))
                                               if p.is_file() and not p.name.endswith('.lock') and p.name != 'artifact-sha256.json'})
    print(json.dumps({'complete': all(n == 4 for n in counts.values()), 'snapshots': sum(counts.values()),
                      'committed_usd': runtime.ledger.snapshot()['committed_usd']}, ensure_ascii=False), flush=True)


def selfcheck():
    # No app endpoint or transport is called: exercise failure-closed accounting.
    payload = {'model': EXPECTED_MODEL, 'store': False, 'reasoning': {'effort': 'none'},
               'service_tier': 'default', 'max_output_tokens': 2, 'input': [{'role': 'user', 'content': 'Offline'}]}
    with tempfile.TemporaryDirectory(prefix='diana-budget-check-') as temporary:
        ledger = BudgetLedger(Path(temporary) / 'ledger.json', budget_usd=BUDGET_USD, max_posts=MAX_POSTS, generation_budget_usd=None)
        ledger.begin('offline.once', payload)
        row = ledger.settle('offline.once', {'input_tokens': 1, 'output_tokens': 1, 'total_tokens': 2})
        if row['status'] != 'settled':
            raise AssertionError('Usage was not settled.')
        try:
            ledger.begin('offline.once', payload)
        except BudgetError:
            pass
        else:
            raise AssertionError('Duplicate task was accepted.')
        ledger.begin('offline.unknown', payload)
        row = ledger.settle('offline.unknown', None)
        if row['charged_usd'] != row['reserved_usd'] or row['status'] != 'uncertain':
            raise AssertionError('Unknown usage did not retain its reservation.')
    print('Offline budget self-check passed. No API requests.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'run', 'verify', 'selfcheck'])
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--personas', type=Path, default=STUDY / 'selected-personas.json')
    parser.add_argument('--corpus-db', type=Path, default=ROOT / 'instance/real-jobs.sqlite3')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--turn', type=int, choices=range(4), default=0,
                        help='Run one wave; later waves require actual-response-bound Codex messages.')
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.out, args.personas, args.corpus_db)
    elif args.command == 'run':
        run(args.out, args.turn, resume=args.resume)
    elif args.command == 'verify':
        verify(args.out)
        print('Frozen source and inputs verified; no API calls.')
    else:
        selfcheck()
