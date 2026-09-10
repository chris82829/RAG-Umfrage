"""Exercise the real OpenAI SDK's SSE parser without network requests."""
import json

import httpx
import pytest
from openai import OpenAI

from llm_service import LLMUnavailable, OpenAIService


PROFILE = {'query': 'Python', 'skills': ['Python'], 'preferences': [], 'cv_text': '',
           'filters': {'employment_types': [], 'locations': [], 'remote': [], 'max_hours': None}}
PATCH = {'query': None, 'skills': None, 'preferences': None,
         'filters': {'employment_types': None, 'locations': None, 'remote': None,
                     'max_hours': None, 'clear_max_hours': False}}


class ResponseStream(httpx.SyncByteStream):
    def __init__(self, output, *, fail=False):
        self.output = output
        self.fail = fail
        self.completed = False
        self.closed = False

    def __iter__(self):
        text = json.dumps(self.output, ensure_ascii=True)
        response = {'id': 'resp_test', 'object': 'response', 'created_at': 1,
                    'model': 'gpt-5.4-2026-03-05', 'status': 'in_progress', 'output': [], 'error': None}
        item = {'id': 'msg_test', 'type': 'message', 'role': 'assistant',
                'status': 'in_progress', 'content': []}
        part = {'type': 'output_text', 'text': '', 'annotations': []}
        events = [
            {'type': 'response.created', 'response': response},
            {'type': 'response.output_item.added', 'output_index': 0, 'item': item},
            {'type': 'response.content_part.added', 'output_index': 0, 'content_index': 0,
             'item_id': 'msg_test', 'part': part},
            {'type': 'response.reasoning_summary_text.delta', 'output_index': 0,
             'item_id': 'reasoning_test', 'summary_index': 0, 'delta': 'PRIVATE reasoning'},
        ]
        # Split JSON escapes and unicode across real SSE events.
        events += [{'type': 'response.output_text.delta', 'output_index': 0, 'content_index': 0,
                    'item_id': 'msg_test', 'delta': char, 'logprobs': []} for char in text]
        for sequence, event in enumerate(events):
            yield ('data: ' + json.dumps({**event, 'sequence_number': sequence}) + '\n\n').encode()
        if self.fail:
            raise httpx.ReadError('SECRET provider body')
        self.completed = True
        final = {**response, 'status': 'completed', 'output': [
            {**item, 'status': 'completed', 'content': [{**part, 'text': text}]}]}
        yield ('data: ' + json.dumps({'type': 'response.completed', 'sequence_number': len(events),
                                     'response': final}) + '\n\n').encode()

    def close(self):
        self.closed = True


def sdk_service(output, **kwargs):
    stream = ResponseStream(output, **kwargs)
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, headers={'Content-Type': 'text/event-stream'}, stream=stream)

    client = OpenAI(api_key='offline-test-key', http_client=httpx.Client(transport=httpx.MockTransport(handle)))
    return OpenAIService('offline-test-key', client=client), stream, requests


def test_chat_stream_is_incremental_decodes_escapes_and_disables_reasoning():
    output = {'action': 'answer', 'profile_patch': PATCH,
              'assistant_message': 'Python passt.\n„München“ und Teamarbeit 🧭 sind deine Wünsche.'}
    service, transport, requests = sdk_service(output)
    steps = service.plan_chat_steps(PROFILE, [], 'Warum passt die Stelle?', jobs=[], stream=True)
    first = next(steps)
    assert not transport.completed
    assert first['data']['assistant_message'] == 'P'
    previews = [first]
    while True:
        try:
            previews.append(next(steps))
        except StopIteration as completed:
            assert completed.value == output
            break
    assert previews[-1]['data']['assistant_message'] == output['assistant_message']
    assert all(output['assistant_message'].startswith(p['data']['assistant_message']) for p in previews)
    assert 'PRIVATE' not in json.dumps(previews)
    assert transport.closed and transport.completed
    assert len(requests) == 1
    assert requests[0]['model'] == 'gpt-5.4-2026-03-05'
    assert requests[0]['reasoning'] == {'effort': 'none'}
    assert requests[0]['store'] is False and requests[0]['stream'] is True
    assert requests[0]['text']['format']['type'] == 'json_schema'


@pytest.mark.parametrize('abort', [True, False])
def test_stream_cancellation_and_connection_failure_close_upstream(abort):
    service, transport, requests = sdk_service(
        {'action': 'answer', 'profile_patch': PATCH, 'assistant_message': 'Eine Antwort.'}, fail=True)
    steps = service.plan_chat_steps(PROFILE, [], 'Warum?', jobs=[], stream=True)
    assert next(steps)['data']['assistant_message'] == 'E'
    if abort:
        steps.close()
    else:
        with pytest.raises(LLMUnavailable) as error:
            list(steps)
        assert 'SECRET' not in str(error.value)
    assert transport.closed and len(requests) == 1


@pytest.mark.parametrize('cached', [False, True])
def test_rerank_stream_keeps_all_twenty_jobs_reasons_without_reasoning(cached):
    from test_llm_service import candidate, ranking
    candidates = [candidate(str(i)) for i in range(20)]
    rankings = [ranking(str(i)) for i in range(20)]
    persona = {'persona_prompt': 'Python passt.', 'retrieval_query': 'Python'}
    # Obtain a valid cache via the ordinary, already validated scoring path.
    from test_llm_service import service_with_output
    sync, _ = service_with_output({'rankings': rankings, 'assistant_message': 'Python passt.'})
    baseline = sync.rerank(persona, PROFILE, candidates)
    output_rankings = [{k: v for k, v in rank.items() if k != 'components'} for rank in rankings] if cached else rankings
    service, transport, requests = sdk_service({'rankings': output_rankings, 'assistant_message': 'Python passt.'})
    steps = service.rerank_steps(persona, PROFILE, candidates, stream=True,
                                assessment_cache=baseline['assessment_cache'] if cached else None)
    assert next(steps)['data']['assistant_message'] == 'P'
    assert not transport.completed
    while True:
        try:
            next(steps)
        except StopIteration as completed:
            result = completed.value
            break
    assert result == baseline
    assert len(result['rankings']) == 20
    assert all(len(job['reasons']) == 2 for job in result['rankings'])
    assert requests[0]['model'] == 'gpt-5.4-2026-03-05'
    assert requests[0]['reasoning'] == {'effort': 'none'}
