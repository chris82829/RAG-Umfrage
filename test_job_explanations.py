"""On-demand explanations preserve scores, ownership and the chat allowance."""
import copy
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from advisor import SCORING_VERSION, SCORING_WEIGHTS, score_from_components
from llm_service import LLMUnavailable
import test_survey_chat_limit as fixtures


EXPLANATION = {
    'reasons': ['Python passt zu den beschriebenen Datenaufgaben.',
                'Die Aufgaben in der Anzeige sind konkret beschrieben.'],
    'matched_skills': ['Python'], 'missing_skills': [],
}


@pytest.fixture
def study(monkeypatch):
    fixture = fixtures.SurveyChatLimitTests(methodName='runTest')
    fixture.setUp()
    original_rank = fixture.model.rerank
    control = SimpleNamespace(calls=[], failure=None, payload=copy.deepcopy(EXPLANATION), on_call=None)

    def rank_with_components(*args, **kwargs):
        result = original_rank(*args, **kwargs)
        for index, match in enumerate(result['rankings']):
            components = dict(technical_fit=80-index, preferences_fit=70,
                technical_depth=65, learning=60, innovation=55, clarity=75)
            match.update(components=components, score=score_from_components(components),
                scoring_weights=dict(SCORING_WEIGHTS), scoring_version=SCORING_VERSION,
                reasons=[], reason='', matched_skills=[], missing_skills=[])
        return result

    def explain(profile, job, **kwargs):
        control.calls.append((copy.deepcopy(profile), copy.deepcopy(job), copy.deepcopy(kwargs)))
        if control.on_call:
            control.on_call()
        if control.failure:
            raise control.failure
        return copy.deepcopy(control.payload)

    monkeypatch.setattr(fixture.model, 'rerank', rank_with_components)
    monkeypatch.setattr(fixture.model, 'explain_job', explain, raising=False)
    try:
        yield fixture, control
    finally:
        fixture.doCleanups()


def endpoint(state, job_id=None):
    job_id = state['jobs'][0]['id'] if job_id is None else job_id
    return f"/api/sessions/{state['session_id']}/jobs/{job_id}/explanation"


def invariant_state(state):
    result = copy.deepcopy(state)
    for job in result['jobs']:
        for field in ('reason', 'reasons', 'matched_skills', 'missing_skills'):
            job['match'].pop(field, None)
    return result


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
def test_explanation_only_changes_target_prose_and_repeat_is_cached(study, arm):
    fixture, control = study
    headers = fixture.grant(arm)
    state = fixture.onboard(headers)
    store = fixture.app.extensions['chat_store']
    before, version = store.get(state['session_id'])
    usage = copy.deepcopy(state['chat_usage'])
    response = fixture.client.post(endpoint(state), headers=headers, json={})
    assert response.status_code == 200, response.json
    after, updated_version = store.get(state['session_id'])
    assert invariant_state(after) == invariant_state(before)
    assert updated_version == version + 1
    assert after['jobs'][0]['match']['reasons'] == EXPLANATION['reasons']
    assert after['jobs'][0]['match']['reason'] == ' '.join(EXPLANATION['reasons'])
    assert after['jobs'][1:] == before['jobs'][1:]
    assert response.json['chat_usage'] == usage
    assert len(control.calls) == 1
    assert control.calls[0][2]['prompt_policy'] == {'A': 'unprompted', 'B': 'career_fixed', 'C': 'custom_career'}[arm]
    assert control.calls[0][2]['system_prompt'] == before['_system_prompt_snapshot']
    repeated = fixture.client.post(endpoint(state), headers=headers, json={})
    assert repeated.status_code == 200
    assert len(control.calls) == 1
    assert store.get(state['session_id']) == (after, updated_version)
    with fixture.app.extensions['survey_store'].connect() as db:
        assert db.execute("SELECT count(*) FROM study_operation_events WHERE operation_kind='chat'").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM track_events WHERE event_type='chat_turn'").fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM study_chat_reservations').fetchone()[0] == 0


def test_ownership_consent_and_job_membership_are_checked_before_model(study):
    fixture, control = study
    owner = fixture.grant('B')
    state = fixture.onboard(owner)
    other = fixture.grant('B')
    for headers in ({}, other):
        response = fixture.client.post(endpoint(state), headers=headers, json={})
        assert response.status_code == 428
    assert fixture.client.post(endpoint(state, 'not-in-this-selection'), headers=owner, json={}).status_code == 404
    assert control.calls == []
    fixture.client.delete('/api/privacy/consent', headers=owner)
    assert fixture.client.post(endpoint(state), headers=owner, json={}).status_code == 428
    assert control.calls == []


@pytest.mark.parametrize('payload', [{'score': 100}, {'profile': {}}, [], None])
def test_endpoint_rejects_client_supplied_values(study, payload):
    fixture, control = study
    headers = fixture.grant('B')
    state = fixture.onboard(headers)
    response = fixture.client.post(endpoint(state), headers=headers, json=payload)
    assert response.status_code == 400
    assert control.calls == []


def test_model_failure_does_not_change_session_and_retry_is_possible(study):
    fixture, control = study
    headers = fixture.grant('C')
    state = fixture.onboard(headers)
    store = fixture.app.extensions['chat_store']
    before = store.get(state['session_id'])
    control.failure = LLMUnavailable('Simulierter API-Fehler')
    assert fixture.client.post(endpoint(state), headers=headers, json={}).status_code == 503
    assert store.get(state['session_id']) == before
    control.failure = None
    assert fixture.client.post(endpoint(state), headers=headers, json={}).status_code == 200
    assert len(control.calls) == 2


@pytest.mark.parametrize('extra', [{'score': 100}, {'components': {'technical_fit': 100}}, {'job_id': 'other'}])
def test_model_cannot_overwrite_scores_components_or_target(study, extra):
    fixture, control = study
    headers = fixture.grant('B')
    state = fixture.onboard(headers)
    store = fixture.app.extensions['chat_store']
    before = store.get(state['session_id'])
    control.payload.update(extra)
    response = fixture.client.post(endpoint(state), headers=headers, json={})
    assert response.status_code == 503
    assert store.get(state['session_id']) == before
    control.payload = copy.deepcopy(EXPLANATION)
    assert fixture.client.post(endpoint(state), headers=headers, json={}).status_code == 200


def test_concurrent_duplicate_requests_make_at_most_one_model_call(study):
    fixture, control = study
    headers = fixture.grant('B')
    state = fixture.onboard(headers)
    entered, release = threading.Event(), threading.Event()

    def wait_for_release():
        entered.set()
        assert release.wait(timeout=5), 'The test must release the simulated model call.'

    control.on_call = wait_for_release

    def first_request():
        with fixture.app.test_client() as client:
            return client.post(endpoint(state), headers=headers, json={})

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(first_request)
        try:
            assert entered.wait(timeout=5)
            duplicate = fixture.client.post(endpoint(state), headers=headers, json={})
            assert duplicate.status_code == 409
            assert duplicate.json['error']['code'] == 'explanation_in_progress'
            assert len(control.calls) == 1
        finally:
            release.set()
        assert pending.result(timeout=5).status_code == 200
    assert fixture.client.post(endpoint(state), headers=headers, json={}).status_code == 200
    assert len(control.calls) == 1


def test_explanations_remain_available_after_all_three_chat_turns(study):
    fixture, control = study
    headers = fixture.grant('C')
    state = fixture.onboard(headers)
    for _ in range(3):
        state = fixture.chat(headers, state).json
    assert state['chat_usage']['remaining'] == 0
    store = fixture.app.extensions['chat_store']
    before, _ = store.get(state['session_id'])
    response = fixture.client.post(endpoint(state), headers=headers, json={})
    assert response.status_code == 200
    after, _ = store.get(state['session_id'])
    assert invariant_state(after) == invariant_state(before)
    assert response.json['chat_usage'] == state['chat_usage']
    assert len(control.calls) == 1
    with fixture.app.extensions['survey_store'].connect() as db:
        assert db.execute("SELECT count(*) FROM track_events WHERE event_type='chat_turn'").fetchone()[0] == 3


def test_concurrent_session_update_is_preserved_instead_of_being_overwritten(study):
    fixture, control = study
    headers = fixture.grant('B')
    state = fixture.onboard(headers)
    store = fixture.app.extensions['chat_store']
    advanced = {}

    def concurrent_update():
        current, version = store.get(state['session_id'])
        current['assistant_message'] = 'Neuere, parallel gespeicherte Antwort.'
        store.update(state['session_id'], current, version)
        advanced['saved'] = store.get(state['session_id'])

    control.on_call = concurrent_update
    response = fixture.client.post(endpoint(state), headers=headers, json={})
    assert response.status_code == 409
    assert store.get(state['session_id']) == advanced['saved']
    assert not advanced['saved'][0]['jobs'][0]['match']['reasons']
    control.on_call = None
    assert fixture.client.post(endpoint(state), headers=headers, json={}).status_code == 200


def test_missing_component_assessment_is_rejected_without_model_call(study):
    fixture, control = study
    headers = fixture.grant('A')
    state = fixture.onboard(headers)
    store = fixture.app.extensions['chat_store']
    current, version = store.get(state['session_id'])
    current['jobs'][0]['match'].pop('components')
    store.update(state['session_id'], current, version)
    response = fixture.client.post(endpoint(state), headers=headers, json={})
    assert response.status_code == 409
    assert response.json['error']['code'] == 'assessment_missing'
    assert control.calls == []
