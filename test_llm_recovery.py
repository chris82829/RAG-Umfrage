"""Offline fault injection: recover an LLM call, never replay a committed chat turn."""
import copy
import io
import json
import logging
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch

import httpx2 as httpx
import pytest
from openai import OpenAI

from llm_service import ChatDecision, OpenAIService, LLMUnavailable, _complete
from test_system_prompts import neutral_patch, PROFILE, JOBS
import test_survey_chat_limit as chat_fixture
from system_prompt_store import DEFAULT_SYSTEM_PROMPTS


def payload():
    return dict(action='answer', profile_patch=neutral_patch(), assistant_message='Python passt zur Aufgabe.')


class Responses:
    def __init__(self, failures=1, error=None):
        self.failures = failures
        self.calls = []
        self.error = error

    def parse(self, **options):
        self.calls.append(('parse', copy.deepcopy(options)))
        if self.failures:
            self.failures -= 1
            if self.error:
                raise self.error
            # Valid JSON, but an invalid structured action; no raw input in logs.
            options['text_format'].model_validate({**payload(), 'action': 'PRIVATE_TEXT'})
        return SimpleNamespace(status='completed', usage=None, output_parsed=payload())

    def stream(self, **options):
        self.calls.append(('stream', copy.deepcopy(options)))
        owner = self
        class Events:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def __iter__(self):
                yield SimpleNamespace(type='response.output_text.delta', snapshot=json.dumps(payload()))
            def get_final_response(self):
                if owner.failures:
                    owner.failures -= 1
                    raise owner.error or RuntimeError("Didn't receive a `response.completed` event.")
                return SimpleNamespace(status='completed', usage=None, output_parsed=payload())
        return Events()


@pytest.fixture(autouse=True)
def no_delay():
    with patch('llm_service.sleep'):
        yield


@pytest.mark.parametrize('policy', ['unprompted', 'career_fixed', 'custom_career'])
def test_broken_stream_recovers_same_message_and_prompt(policy):
    responses = Responses()
    service = OpenAIService('', client=SimpleNamespace(responses=responses))
    answer = _complete(service.plan_chat_steps(PROFILE, [], 'Warum?', jobs=JOBS,
        prompt_policy=policy, system_prompt=DEFAULT_SYSTEM_PROMPTS[policy], stream=True))
    assert answer['action'] == 'answer'
    assert [kind for kind, _ in responses.calls] == ['stream', 'parse']
    assert responses.calls[0][1] == responses.calls[1][1]
    if policy == 'unprompted':
        assert [part['role'] for part in responses.calls[0][1]['input']] == ['user']


def test_invalid_structure_retries_once_and_logs_no_input():
    output = io.StringIO()
    log = logging.Logger('recovery-test', logging.INFO)
    log.addHandler(logging.StreamHandler(output))
    responses = Responses()
    service = OpenAIService('', client=SimpleNamespace(responses=responses), performance_logger=log)
    result = service._parse(None, {'message':'PRIVATE_MESSAGE'}, ChatDecision)
    assert result.action == 'answer'
    assert len(responses.calls) == 2
    assert 'failure_kind=invalid_structure' in output.getvalue()
    assert 'validation_types=literal_error' in output.getvalue()
    assert 'attempt=2' in output.getvalue()
    assert 'PRIVATE' not in output.getvalue()


@pytest.mark.parametrize('stream', [False, True])
def test_two_failures_stop_without_accepting_partial_output(stream):
    responses = Responses(failures=2)
    service = OpenAIService('', client=SimpleNamespace(responses=responses))
    with pytest.raises(LLMUnavailable):
        _complete(service._parse_steps(None, {}, ChatDecision, stream=stream))
    assert len(responses.calls) == 2


def test_disconnect_does_not_restart_a_cancelled_generator():
    responses = Responses()
    service = OpenAIService('', client=SimpleNamespace(responses=responses))
    steps = service._parse_steps(None, {}, ChatDecision, stream=True)
    assert next(steps)['type'] == 'assistant_preview'
    steps.close()
    assert len(responses.calls) == 1


@pytest.mark.parametrize('status,code,expected_calls', [
    (401,'invalid_api_key',1), (400,'invalid_request_error',1),
    (429,'insufficient_quota',1), (429,'rate_limit_exceeded',2), (503,'server_error',2)])
def test_real_sdk_http_failures_obey_single_retry_budget(status, code, expected_calls):
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(status, json={'error':{'message':'PRIVATE_PROVIDER_BODY', 'type':code, 'code':code}})
    client = OpenAI(api_key='offline-key', max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)))
    service = OpenAIService('', client=client)
    with client, pytest.raises(LLMUnavailable) as failure:
        service._parse(None, {}, ChatDecision)
    assert len(calls) == expected_calls
    assert 'PRIVATE' not in str(failure.value)


def test_real_sdk_json_validation_then_success():
    calls = []
    def handle(request):
        calls.append(request)
        data = payload()
        if len(calls) == 1:
            data['action'] = 'invalid'
        return httpx.Response(200, json=dict(id='resp_test', object='response', created_at=0,
            model='offline', status='completed', output=[dict(id='msg_test', type='message',
                role='assistant', status='completed', content=[dict(type='output_text', annotations=[],
                text=json.dumps(data))])]))
    client = OpenAI(api_key='offline-key', max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)))
    with client:
        assert OpenAIService('', client=client)._parse(None, {}, ChatDecision).action == 'answer'
    assert len(calls) == 2


def test_refusal_is_not_retried():
    response = SimpleNamespace(status='completed', output_parsed=None,
        output=[SimpleNamespace(content=[SimpleNamespace(type='refusal')])])
    with patch.object(Responses, 'parse', return_value=response) as call:
        with pytest.raises(LLMUnavailable):
            OpenAIService('', client=SimpleNamespace(responses=Responses()))._parse(None, {}, ChatDecision)
        assert call.call_count == 1


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
@pytest.mark.parametrize('failures', [1, 2])
def test_http_stream_recovery_commits_exactly_one_turn_or_none(arm, failures):
    fixture = chat_fixture.SurveyChatLimitTests()
    fixture.setUp()
    try:
        headers = fixture.grant(arm)
        state = fixture.onboard(headers)
        responses = Responses(failures=failures)
        service = OpenAIService('', client=SimpleNamespace(responses=responses))
        fixture.model.plan_chat_steps = service.plan_chat_steps
        response = fixture.chat({**headers, 'Accept':'application/x-ndjson'}, state)
        events = [json.loads(line) for line in response.data.splitlines()]
        assert len(responses.calls) == 2
        assert events[-1]['type'] == ('result' if failures == 1 else 'error')
        restored = fixture.client.get('/api/sessions/'+state['session_id'], headers=headers).json
        expected = int(failures == 1)
        assert restored['chat_usage']['used'] == expected
        assert restored['chat_usage']['pending'] == 0
        assert sum(m['role']=='user' for m in restored['messages']) == expected
        assert restored['profile'] == state['profile']
        assert restored['jobs'] == state['jobs']
        with sqlite3.connect(fixture.app.config['DATABASE_PATH']) as db:
            assert db.execute("SELECT COUNT(*) FROM track_events WHERE event_type='chat_turn'").fetchone()[0] == expected
    finally:
        fixture.doCleanups()


def test_real_sdk_stream_schema_error_recovers_with_complete_response():
    calls = []
    def response_doc(data, status='completed'):
        return dict(id='resp_test', object='response', created_at=0, model='offline', status=status,
            output=[dict(id='msg_test', type='message', role='assistant', status='completed',
                content=[dict(type='output_text', annotations=[], text=json.dumps(data))])])
    def handle(request):
        body = json.loads(request.content)
        calls.append(body)
        if not body.get('stream'):
            return httpx.Response(200, json=response_doc(payload()))
        invalid = {**payload(), 'action':'invalid'}
        doc = response_doc(invalid)
        start = {**doc, 'status':'in_progress', 'output':[]}
        events = [
            dict(type='response.created', response=start, sequence_number=0),
            dict(type='response.output_item.added', output_index=0, sequence_number=1,
                 item={**doc['output'][0], 'content':[]}),
            dict(type='response.content_part.added', output_index=0, content_index=0,
                 item_id='msg_test', sequence_number=2, part=dict(type='output_text', annotations=[], text='')),
            dict(type='response.output_text.delta', output_index=0, content_index=0,
                 item_id='msg_test', sequence_number=3, delta=json.dumps(invalid), logprobs=[]),
            dict(type='response.output_text.done', output_index=0, content_index=0,
                 item_id='msg_test', sequence_number=4, text=json.dumps(invalid), logprobs=[]),
            dict(type='response.completed', response=doc, sequence_number=5),
        ]
        stream = ''.join('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events)
        return httpx.Response(200, headers={'content-type':'text/event-stream'}, content=stream)
    client = OpenAI(api_key='offline-key', max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)))
    with client:
        result = _complete(OpenAIService('', client=client)._parse_steps(None, {}, ChatDecision, stream=True))
    assert result.action == 'answer'
    assert len(calls) == 2
    assert calls[0]['stream'] is True
    assert not calls[1].get('stream')


def test_success_uses_one_request_and_production_sdk_has_no_nested_retries():
    responses = Responses(failures=0)
    assert OpenAIService('', client=SimpleNamespace(responses=responses))._parse(None, {}, ChatDecision)
    assert len(responses.calls) == 1
    client = OpenAIService('offline-key')._get_client()
    try:
        assert client.max_retries == 0
    finally:
        client.close()


def test_output_limit_and_programming_errors_are_not_retried():
    response = SimpleNamespace(status='incomplete', incomplete_details=SimpleNamespace(reason='max_output_tokens'))
    with patch.object(Responses, 'parse', return_value=response) as call:
        with pytest.raises(LLMUnavailable):
            OpenAIService('', client=SimpleNamespace(responses=Responses()))._parse(None, {}, ChatDecision)
        assert call.call_count == 1
    responses = Responses(error=TypeError('PRIVATE_INTERNAL_ERROR'))
    with pytest.raises(LLMUnavailable):
        OpenAIService('', client=SimpleNamespace(responses=responses))._parse(None, {}, ChatDecision)
    assert len(responses.calls) == 1


def test_hours_cannot_be_set_and_cleared_in_provider_schema():
    from openai.lib._pydantic import to_strict_json_schema
    from pydantic import ValidationError
    schema = to_strict_json_schema(ChatDecision)
    # Check the exact schema sent to the provider, not just local validation.
    branches = schema['$defs']['ProfilePatch']['properties']['filters']['anyOf']
    variants = [schema['$defs'][branch['$ref'].split('/')[-1]]['properties'] for branch in branches]
    assert len(variants) == 2
    assert variants[0]['clear_max_hours']['const'] is False
    assert variants[1]['clear_max_hours']['const'] is True
    assert variants[1]['max_hours']['type'] == 'null'
    for hours, clear in [(None, False), (None, True), (39, False)]:
        data = payload()
        data['profile_patch']['filters'].update(max_hours=hours, clear_max_hours=clear)
        ChatDecision.model_validate(data)
    data['profile_patch']['filters'].update(max_hours=39, clear_max_hours=True)
    with pytest.raises(ValidationError):
        ChatDecision.model_validate(data)


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
def test_retries_allow_exactly_three_study_messages_and_survey_transition(arm):
    fixture = chat_fixture.SurveyChatLimitTests()
    fixture.setUp()
    try:
        headers = fixture.grant(arm)
        state = fixture.onboard(headers)
        for count in (1, 2, 3):
            responses = Responses(failures=1)
            service = OpenAIService('', client=SimpleNamespace(responses=responses))
            fixture.model.plan_chat_steps = service.plan_chat_steps
            response = fixture.chat({**headers, 'Accept':'application/x-ndjson'}, state)
            events = [json.loads(line) for line in response.data.splitlines()]
            assert events[-1]['type'] == 'result'
            state = events[-1]['data']
            assert len(responses.calls) == 2
            assert state['chat_usage']['used'] == count
            assert state['chat_usage']['pending'] == 0
        assert fixture.client.post('/api/proceed_to_survey', headers=headers).status_code == 200
        assert fixture.chat(headers, state).status_code == 409
        with sqlite3.connect(fixture.app.config['DATABASE_PATH']) as db:
            assert db.execute("SELECT COUNT(*) FROM track_events WHERE event_type='chat_turn'").fetchone()[0] == 3
    finally:
        fixture.doCleanups()
