"""C's conclusion follows committed turns, including reranking and standalone tests."""
import json

import pytest

from chat_completion import (C_SELECTION_CONCLUSION, C_EMPTY_CONCLUSION,
                             conclude_custom_chat, custom_chat_preview)
from chat_text import MAX_BC_ANSWER_CHARS
import test_survey_chat_limit as fixtures


@pytest.fixture
def study(monkeypatch):
    fixture = fixtures.SurveyChatLimitTests(methodName='runTest')
    fixture.setUp()
    plan = fixture.model.plan_chat
    rank = fixture.model.rerank

    def plan_with_question(*args, **kwargs):
        result = plan(*args, **kwargs)
        result['assistant_message'] = 'Python passt zu den Aufgaben.\n\nWelche Aufgabe bevorzugst du?'
        return result

    def rank_with_question(*args, **kwargs):
        result = rank(*args, **kwargs)
        result['assistant_message'] = 'Die Stellen passen zu Python.\n\nWelche Aufgabe bevorzugst du?'
        return result

    monkeypatch.setattr(fixture.model, 'plan_chat', plan_with_question)
    monkeypatch.setattr(fixture.model, 'rerank', rank_with_question)
    yield fixture
    fixture.doCleanups()


@pytest.mark.parametrize('action', ['answer', 'rerank', 'search'])
def test_third_successful_c_turn_answers_then_concludes_for_every_action(study, action):
    headers = study.grant('C')
    state = study.onboard(headers)
    for _ in range(2):
        state = study.chat(headers, state).json
        assert C_SELECTION_CONCLUSION not in state['assistant_message']
        assert state['assistant_message'].endswith('?')
    study.model.action = action
    response = study.chat(headers, state)
    assert response.status_code == 200
    result = response.json
    assert result['chat_usage']['used'] == 3
    assert result['assistant_message'].endswith(C_SELECTION_CONCLUSION)
    assert '?' not in result['assistant_message']
    assert 'Python' in result['assistant_message']
    assert len(result['assistant_message']) <= MAX_BC_ANSWER_CHARS
    assert result['messages'][-1]['content'] == result['assistant_message']
    assert study.model.follow_up_flags[-1] is False
    if action != 'answer':
        assert study.model.ranking_follow_up_flags[-1] is False
    restored = study.client.get('/api/sessions/' + state['session_id'], headers=headers).json
    assert restored['messages'][-1] == result['messages'][-1]


@pytest.mark.parametrize('arm', ['A', 'B'])
def test_a_b_messages_are_unchanged(study, arm):
    headers = study.grant(arm)
    state = study.onboard(headers)
    for _ in range(3):
        state = study.chat(headers, state).json
    assert state['assistant_message'] == 'Python passt zu den Aufgaben.\n\nWelche Aufgabe bevorzugst du?'


def test_counter_is_shared_across_sessions_and_failed_third_turn_is_not_counted(study):
    headers = study.grant('C')
    first, second = study.onboard(headers), study.onboard(headers)
    first = study.chat(headers, first).json
    second = study.chat(headers, second).json
    study.model.fail = True
    assert study.chat(headers, first).status_code == 503
    restored = study.client.get('/api/sessions/' + first['session_id'], headers=headers).json
    assert restored['chat_usage']['used'] == 2
    assert C_SELECTION_CONCLUSION not in restored['assistant_message']
    study.model.fail = False
    third = study.chat(headers, first).json
    assert third['chat_usage']['used'] == 3
    assert third['assistant_message'].endswith(C_SELECTION_CONCLUSION)


def test_final_count_is_read_during_commit_not_guessed_before_model_finishes(study, monkeypatch):
    headers = study.grant('C')
    first, other = study.onboard(headers), study.onboard(headers)
    study.chat(headers, first)
    model_plan = study.model.plan_chat
    interleaved = False

    def interleaved_chat(*args, **kwargs):
        nonlocal interleaved
        result = model_plan(*args, **kwargs)
        if not interleaved:
            interleaved = True
            # A separate successful request finishes while the outer model call
            # is pending; only the outer commit becomes the third success.
            with study.app.test_client() as client:
                response = client.post('/api/chat', headers=headers,
                    json={'session_id': other['session_id'], 'message': 'Noch eine Frage'})
                assert response.status_code == 200
                assert C_SELECTION_CONCLUSION not in response.json['assistant_message']
        return result

    monkeypatch.setattr(study.model, 'plan_chat', interleaved_chat)
    response = study.chat(headers, first)
    assert response.status_code == 200
    assert response.json['chat_usage']['used'] == 3
    assert response.json['assistant_message'].endswith(C_SELECTION_CONCLUSION)


def test_standalone_c_has_one_intermediate_conclusion_and_remains_unlimited(study):
    headers = study.grant('C', standalone=True)
    state = study.onboard(headers)
    for index in range(5):
        state = study.chat(headers, state).json
        assert state['chat_usage']['limit'] is None
        assert state['chat_usage']['used'] == index + 1
        assert (C_SELECTION_CONCLUSION in state['assistant_message']) == (index == 2)
        assert study.model.follow_up_flags[-1] is (index != 2)
        assert 'Umfrage' not in state['assistant_message']


def test_search_without_message_does_not_trigger_conclusion(study):
    headers = study.grant('C')
    state = study.onboard(headers)
    for _ in range(2):
        state = study.chat(headers, state).json
    response = study.client.post('/api/chat', headers=headers,
        json={'session_id': state['session_id'], 'mode': 'search'})
    assert response.status_code == 200
    assert response.json['chat_usage']['used'] == 2
    assert C_SELECTION_CONCLUSION not in response.json['assistant_message']


def test_third_stream_has_no_question_preview(study):
    headers = study.grant('C')
    state = study.onboard(headers)
    for _ in range(2):
        state = study.chat(headers, state).json
    response = study.chat({**headers, 'Accept': 'application/x-ndjson'}, state)
    events = [json.loads(line) for line in response.data.splitlines()]
    assert not any(item['type'] == 'assistant_text' for item in events)
    assert events[-1]['data']['assistant_message'].endswith(C_SELECTION_CONCLUSION)
    assert events[-1]['data']['chat_usage']['used'] == 3


def test_empty_pool_conclusion_does_not_claim_matching_favorites(study):
    headers = study.grant('C')
    state = study.onboard(headers)
    for _ in range(2):
        state = study.chat(headers, state).json
    sessions = study.app.extensions['chat_store']
    stored, version = sessions.get(state['session_id'])
    stored['jobs'] = []
    sessions.update(state['session_id'], stored, version)
    result = study.chat(headers, state).json
    assert result['assistant_message'].endswith(C_EMPTY_CONCLUSION)
    assert 'Favoriten' not in result['assistant_message']


def test_conclusion_is_bounded_and_drops_followup_question():
    result = conclude_custom_chat('Python passt zu den Aufgaben. ' * 30 + '\nWelche Stelle bevorzugst du?', [{}])
    assert result.startswith('Python passt')
    assert result.endswith(C_SELECTION_CONCLUSION)
    assert len(result) <= MAX_BC_ANSWER_CHARS
    assert '?' not in result
    assert conclude_custom_chat(result, [{}]) == result


def test_previews_delay_questions_even_before_concurrent_third_turn_is_known():
    text = 'Python passt. Welche Aufgabe bevorzugst du?'
    for length in range(1, len(text) + 1):
        preview = custom_chat_preview(text[:length])
        assert 'Welche' not in preview
        assert '?' not in preview
