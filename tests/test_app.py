from copy import deepcopy
import json
from pathlib import Path

import pytest

from app import MATCHING_POLICY_VERSION, PERSONA_CACHE_VERSION, create_app, merge_profile, persona_fingerprint
from llm_service import LLMUnavailable
from retrieval import EmbeddingUnavailable
from session_store import SessionConflict


class FakeRetriever:
    def __init__(self):
        self.calls = []

    def search(self, jobs, query, top_k=20):
        self.calls.append((deepcopy(jobs), query, top_k))
        return [{'job': job, 'rrf_score': 0.03, 'bm25_rank': i + 1,
                 'semantic_rank': i + 1, 'bm25_score': 1.0, 'semantic_score': 0.8}
                for i, job in enumerate(jobs[:top_k])]


class FakeLLM:
    def __init__(self):
        self.calls = []
        self.patch = {'filters': {'remote': ['remote']}}
        self.action = 'rerank'
        self.answer = 'Die Stellen passen wegen der angegebenen Python-Kenntnisse.'
        self.ranking_indices = None
        self.assessment_cache_output = None
        self.rerank_calls = []
        self.last_plan_context = None
        self.persona_profiles = []

    def generate_persona(self, profile):
        self.calls.append('persona')
        self.persona_profiles.append(deepcopy(profile))
        return {'persona_prompt': 'Suche skillbasierte Stellen.',
                'retrieval_query': 'Python Datenanalyse', 'opening_message': 'Los geht es.'}

    def rerank(self, persona, profile, candidates, **kwargs):
        self.calls.append('rerank')
        self.last_rerank_context = deepcopy(kwargs)
        self.last_rerank_candidates = deepcopy(candidates)
        self.rerank_calls.append(deepcopy({'persona': persona, 'profile': profile,
                                          'candidates': candidates, **kwargs}))
        selected = candidates[:20] if self.ranking_indices is None else [candidates[i] for i in self.ranking_indices]
        result = {'rankings': [{'job_id': x['job']['id'], 'score': 90 - i,
                               'reason': 'Python passt.', 'matched_skills': ['Python'],
                               'missing_skills': []} for i, x in enumerate(selected)],
                  'assistant_message': 'Diese Stellen passen zu deinen Fachkenntnissen.'}
        if self.assessment_cache_output is not None:
            result['assessment_cache'] = deepcopy(self.assessment_cache_output)
        return result

    def plan_chat(self, profile, history, message, *, jobs, advisor, mode, candidate_count):
        self.calls.append('plan')
        self.last_plan_context = deepcopy({'profile': profile, 'history': history,
                                           'message': message, 'jobs': jobs, 'advisor': advisor,
                                           'mode': mode, 'candidate_count': candidate_count})
        return {'action': self.action, 'profile_patch': deepcopy(self.patch),
                'assistant_message': self.answer}


@pytest.fixture
def setup(tmp_path):
    retriever, llm = FakeRetriever(), FakeLLM()
    app = create_app({'TESTING': True, 'DATABASE_PATH': str(tmp_path / 'test.sqlite3'),
                      'OPENAI_API_KEY': '', 'SEED_DUMMY_DATA': True, 'REQUIRE_COMPLETE_INDEX': False}, retriever=retriever, llm=llm)
    return app, app.test_client(), retriever, llm


def payload(**filters):
    return {'profile': {'query': 'Python Datenanalyse', 'skills': ['Python', 'SQL'],
                        'filters': filters}}


def test_health_reports_gpt54_without_reasoning_and_without_model_calls(setup):
    _, client, retriever, llm = setup
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['openai_model'] == 'gpt-5.4-2026-03-05'
    assert response.json['openai_reasoning_effort'] == 'none'
    assert retriever.calls == []
    assert llm.calls == []


def import_additional_jobs(app, tmp_path, count=25):
    template = json.loads((Path(__file__).resolve().parents[1] / 'dummy_jobs.json').read_text())[0]
    clones = []
    for index in range(count):
        job = deepcopy(template)
        job['jobId'] = 910000 + index
        job['angebotstitel'] = f'Werkstudent Python Teststelle {index}'
        clones.append(job)
    import_path = tmp_path / 'additional_jobs.json'
    import_path.write_text(json.dumps(clones))
    app.extensions['job_store'].import_json(import_path)


def test_filtering_precedes_retrieval_and_reranking(setup):
    app, client, retriever, llm = setup
    response = client.post('/api/search', json=payload(employment_types=['werkstudent']))
    assert response.status_code == 200
    data = response.get_json()
    assert data['jobs']
    assert all('werkstudent' in j['employment_types'] for j in retriever.calls[0][0])
    assert data['retrieval']['filtered_count'] == len(retriever.calls[0][0])
    assert all('search_text' not in j for j in data['jobs'])
    assert '_candidates' not in data
    assert data['candidate_pool'] == {'available': True, 'count': len(retriever.calls[0][0]), 'refresh_required': False}
    assert llm.calls == ['persona', 'rerank']
    assert retriever.calls[0][1].startswith('Python SQL\nPython Datenanalyse')


def test_zero_results_make_no_model_calls_and_do_not_relax_filters(setup):
    _, client, retriever, llm = setup
    response = client.post('/api/search', json=payload(employment_types=['ausbildung']))
    assert response.status_code == 200
    assert response.json['jobs'] == []
    assert response.json['profile']['filters']['employment_types'] == ['ausbildung']
    assert 'Stellenarten: Ausbildung' in response.json['assistant_message']
    assert not retriever.calls and not llm.calls


def test_onboarding_chat_persists_and_can_be_deleted(setup):
    app, client, _, llm = setup
    response = client.post('/api/onboard', json=payload(employment_types=['werkstudent']))
    assert response.status_code == 201
    session_id = response.json['session_id']
    initial = response.json
    response = client.post('/api/chat', json={'session_id': session_id, 'message': 'Nur vollständig remote.'})
    assert response.status_code == 200
    state = response.json
    assert state['profile']['filters']['employment_types'] == ['werkstudent']
    assert state['profile']['filters']['remote'] == ['remote']
    assert len(state['messages']) == 3
    assert llm.last_rerank_context['chat_context']['jobs'] == initial['jobs']
    assert llm.last_rerank_context['chat_context']['messages'] == initial['messages']
    assert state['chat_action'] == 'rerank'
    assert state['jobs'] == initial['jobs']  # Fake scores ignore preferences; no SQL exclusions.
    assert any(j['remote'] != 'remote' for j in state['jobs'])
    restarted = create_app(dict(app.config), retriever=FakeRetriever(), llm=FakeLLM())
    assert restarted.test_client().get(f'/api/sessions/{session_id}').json == state
    assert client.delete(f'/api/sessions/{session_id}').status_code == 204
    assert client.get(f'/api/sessions/{session_id}').status_code == 404


@pytest.mark.parametrize('body', [None, [], {}, {'profile': {}},
    payload(employment_types=['Befristet']), payload(max_hours=-1),
    {'profile': {'query': 'Python', 'unexpected': 'CV_PRIVATE_SENTINEL'}},
    {'profile': {'query': ' ', 'skills': [' ']}}])
def test_rejects_bad_inputs_without_reflecting_private_values(setup, body):
    _, client, retriever, llm = setup
    response = client.post('/api/search', data=__import__('json').dumps(body), content_type='application/json')
    assert response.status_code == 400
    assert 'CV_PRIVATE_SENTINEL' not in response.get_data(as_text=True)
    assert not llm.calls and not retriever.calls


def test_http_errors_are_json(setup):
    _, client, _, _ = setup
    assert client.post('/api/search', data='x').status_code == 415
    assert client.post('/api/search', data='{', content_type='application/json').status_code == 400
    assert client.get('/no-such-endpoint').is_json
    assert client.post('/api/search', data='x' * 140000, content_type='application/json').status_code == 413


def test_upstream_failure_does_not_create_chat(setup):
    app, client, _, llm = setup

    def fail(profile):
        raise LLMUnavailable('OpenAI ist vorübergehend nicht verfügbar.')

    llm.generate_persona = fail
    response = client.post('/api/onboard', json=payload())
    assert response.status_code == 503
    with app.extensions['chat_store'].connect() as db:
        assert db.execute('SELECT COUNT(*) FROM chat_sessions').fetchone()[0] == 0


def test_session_store_prevents_lost_updates(setup):
    app, _, _, _ = setup
    store = app.extensions['chat_store']
    session_id = store.create({'value': 1})
    state, version = store.get(session_id)
    store.update(session_id, {'value': 2}, version)
    with pytest.raises(SessionConflict):
        store.update(session_id, {'value': 3}, version)
    assert store.get(session_id)[0]['value'] == 2


def test_explicit_patch_semantics():
    from schemas import Profile
    before = Profile.model_validate(payload(employment_types=['werkstudent'], max_hours=20)['profile']).model_dump()
    after = merge_profile(before, {'skills': None, 'filters': {'locations': ['Berlin']}})
    assert after['filters']['max_hours'] == 20
    assert after['filters']['employment_types'] == ['werkstudent']
    assert after['skills'] == before['skills']
    assert before['filters']['locations'] == []
    after = merge_profile(after, {'filters': {'employment_types': [], 'clear_max_hours': True}})
    assert after['filters']['max_hours'] is None
    assert after['filters']['employment_types'] == []


def test_health_does_not_load_models(setup):
    _, client, retriever, llm = setup
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['jobs'] == 5
    assert response.json['openai_configured'] is False
    assert not llm.calls and not retriever.calls


@pytest.mark.parametrize('path', ['/', '/index.html', '/suche', '/mehr-erfahren'])
def test_spa_routes_serve_the_same_entry_on_direct_visit_and_refresh(setup, tmp_path, monkeypatch, path):
    _, client, retriever, llm = setup
    entry = '<!doctype html><html><body>SPA entry</body></html>'
    dist = tmp_path / 'web-dist'
    dist.mkdir()
    (dist / 'index.html').write_text(entry, encoding='utf-8')
    monkeypatch.setattr('app.BASE_DIR', tmp_path)

    for headers in ({}, {'Cache-Control': 'no-cache'}):
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        assert response.mimetype == 'text/html'
        assert response.get_data(as_text=True) == entry
    assert not llm.calls and not retriever.calls


def test_spa_routes_preserve_api_responses_and_missing_route_errors(setup):
    _, client, retriever, llm = setup
    health = client.get('/api/health')
    assert health.status_code == 200
    assert health.is_json
    assert health.json['status'] == 'ok'
    missing = client.get('/api/no-such-endpoint')
    assert missing.status_code == 404
    assert missing.is_json
    assert not llm.calls and not retriever.calls


def test_catalog_browsing_is_unranked_and_does_not_run_models(setup):
    _, client, retriever, llm = setup
    response = client.get('/api/jobs')
    assert response.status_code == 200
    assert response.json['total'] == 5
    assert response.json['ranked'] is False
    assert all('search_text' not in j and 'match' not in j for j in response.json['jobs'])
    assert not retriever.calls and not llm.calls


def test_pending_full_index_blocks_model_calls(setup):
    app, client, retriever, llm = setup
    app.config['REQUIRE_COMPLETE_INDEX'] = True
    status = client.get('/api/index-status')
    assert status.json['status'] == 'pending'
    assert status.json['total'] == 5
    response = client.post('/api/onboard', json=payload())
    assert response.status_code == 503
    assert not retriever.calls and not llm.calls


@pytest.mark.parametrize('failure', [False, True])
def test_warmup_only_unlocks_search_after_success(setup, failure):
    app, client, retriever, llm = setup
    app.config['REQUIRE_COMPLETE_INDEX'] = True

    def warmup(jobs, progress):
        progress(2, len(jobs))
        assert client.get('/api/index-status').json['completed'] == 2
        assert client.post('/api/onboard', json=payload()).status_code == 503
        if failure:
            raise RuntimeError('PRIVATE_MODEL_DETAIL')
        progress(len(jobs), len(jobs))

    retriever.warmup = warmup
    result = app.test_cli_runner().invoke(args=['warmup'])
    status = client.get('/api/index-status').json
    if failure:
        assert result.exit_code != 0
        assert status['status'] == 'failed' and status['completed'] == 2
        assert 'PRIVATE_MODEL_DETAIL' not in result.output
        assert client.post('/api/onboard', json=payload()).status_code == 503
        assert not retriever.calls and not llm.calls
    else:
        assert result.exit_code == 0
        assert status['status'] == 'ready' and status['completed'] == 5
        assert client.post('/api/onboard', json=payload()).status_code == 201


def test_web_routes_never_serve_credentials(setup):
    _, client, _, _ = setup
    for route in ['/.env', '/assets/../../.env', '/app.py', '/instance/jobs.sqlite3']:
        assert client.get(route).status_code == 404


def test_advisor_switch_preserves_profile_persona_query_and_persists(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json={**payload(), 'advisor': {'preset': 'steve'}}).json
    assert initial['advisor']['preset'] == 'steve'
    initial_query = retriever.calls[-1][1]
    llm.calls.clear()
    switched = client.post('/api/chat', json={'session_id': initial['session_id'],
                                             'advisor': {'preset': 'angela'}})
    assert switched.status_code == 200
    assert llm.calls == ['rerank']
    assert retriever.calls[-1][1] == initial_query
    assert switched.json['profile'] == initial['profile']
    assert switched.json['persona'] == initial['persona']
    assert switched.json['advisor']['preset'] == 'angela'
    assert 'advisor' not in switched.json['profile']
    assert len(switched.json['messages']) == len(initial['messages']) + 1
    assert client.get(f"/api/sessions/{initial['session_id']}").json == switched.json
    next_turn = client.post('/api/chat', json={'session_id': initial['session_id'], 'message': 'Nur remote.'})
    assert next_turn.json['advisor']['preset'] == 'angela'
    assert llm.last_rerank_context['advisor']['preset'] == 'angela'
    restarted = create_app(dict(app.config), retriever=FakeRetriever(), llm=FakeLLM())
    assert restarted.test_client().get(f"/api/sessions/{initial['session_id']}").json == next_turn.json


def test_message_advisor_names_preserve_history_after_switch_answers_and_noop(setup):
    app, client, retriever, llm = setup
    cache = {'fingerprint': 'PRIVATE_NAMED_MESSAGE_CACHE'}
    llm.assessment_cache_output = cache
    initial = client.post('/api/onboard', json={**payload(), 'advisor': {'preset': 'steve'}}).json
    session_id = initial['session_id']
    assert initial['messages'] == [{'role': 'assistant', 'content': initial['assistant_message'],
                                    'advisor_name': 'Steve-Jobs-KI'}]
    original_state = app.extensions['chat_store'].get(session_id)[0]
    llm.calls.clear()
    retriever.calls.clear()
    switched = client.post('/api/chat', json={'session_id': session_id, 'advisor': {'preset': 'angela'}})
    assert switched.status_code == 200 and switched.json['chat_action'] == 'rerank'
    assert llm.calls == ['rerank'] and not retriever.calls
    assert switched.json['messages'][:-1] == initial['messages']
    assert switched.json['messages'][-1]['advisor_name'] == 'Angela-Merkel-KI'
    assert llm.last_rerank_context['assessment_cache'] == cache

    llm.calls.clear()
    llm.action, llm.patch = 'answer', {}
    message = 'Welche fachlichen Anforderungen sind offen?'
    answered = client.post('/api/chat', json={'session_id': session_id, 'message': message})
    assert answered.status_code == 200 and answered.json['chat_action'] == 'answer'
    assert llm.calls == ['plan'] and not retriever.calls
    assert answered.json['messages'][:-2] == switched.json['messages']
    assert answered.json['messages'][-2] == {'role': 'user', 'content': message}
    assert answered.json['messages'][-1]['advisor_name'] == 'Angela-Merkel-KI'
    assert_recommendations_unchanged(switched.json, answered.json)

    llm.calls.clear()
    noop = client.post('/api/chat', json={'session_id': session_id, 'advisor': {'preset': 'angela'}})
    assert noop.status_code == 200 and noop.json['chat_action'] == 'answer'
    assert not llm.calls and not retriever.calls
    assert noop.json['messages'][:-1] == answered.json['messages']
    assert noop.json['messages'][-1]['advisor_name'] == 'Angela-Merkel-KI'
    assert_recommendations_unchanged(answered.json, noop.json)
    stored = app.extensions['chat_store'].get(session_id)[0]
    for key in ('_candidates', '_assessment_cache', '_persona_fingerprint'):
        assert stored[key] == original_state[key]
        assert key not in noop.json
    restarted = create_app(dict(app.config), retriever=FakeRetriever(), llm=FakeLLM())
    assert restarted.test_client().get(f'/api/sessions/{session_id}').json == noop.json


def test_legacy_message_dicts_are_not_backfilled_or_renamed(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json={**payload(), 'advisor': {'preset': 'steve'}}).json
    session_id = initial['session_id']
    sessions = app.extensions['chat_store']
    state, version = sessions.get(session_id)
    state['messages'][0].pop('advisor_name')
    state['messages'].append({'role': 'user', 'content': 'Eine frühere Frage.'})
    state['messages'].append({'role': 'assistant', 'content': 'Eine frühere Antwort.',
                              'advisor_name': 'Früherer-Anzeigename-KI'})
    legacy_messages = deepcopy(state['messages'])
    sessions.update(session_id, state, version)
    assert client.get(f'/api/sessions/{session_id}').json['messages'] == legacy_messages
    llm.calls.clear()
    retriever.calls.clear()
    llm.action, llm.patch = 'answer', {}
    response = client.post('/api/chat', json={'session_id': session_id, 'message': 'Was empfiehlst du jetzt?'})
    assert response.status_code == 200 and response.json['chat_action'] == 'answer'
    assert llm.calls == ['plan'] and not retriever.calls
    assert response.json['messages'][:-2] == legacy_messages
    assert 'advisor_name' not in response.json['messages'][-2]
    assert response.json['messages'][-1]['advisor_name'] == 'Steve-Jobs-KI'
    assert sessions.get(session_id)[0]['messages'] == response.json['messages']


def test_failed_advisor_switch_does_not_partially_commit(setup):
    _, client, _, llm = setup
    initial = client.post('/api/onboard', json=payload()).json

    def fail(*args, **kwargs):
        raise LLMUnavailable('KI vorübergehend nicht verfügbar.')

    llm.rerank = fail
    result = client.post('/api/chat', json={'session_id': initial['session_id'],
                                           'advisor': {'preset': 'guenther'}})
    assert result.status_code == 503
    assert client.get(f"/api/sessions/{initial['session_id']}").json == initial


def test_description_only_change_reranks_cached_jobs_and_persists_after_restart(setup, monkeypatch):
    app, client, retriever, llm = setup
    advisor = {'mode': 'custom', 'name': 'Meine Beratung', 'traits': ['analytisch'],
               'focus': 'ausgewogen', 'description': '  Erkläre Abwägungen sachlich.  '}
    initial = client.post('/api/onboard', json={**payload(), 'advisor': advisor}).json
    assert initial['advisor']['description'] == 'Erkläre Abwägungen sachlich.'
    session_id = initial['session_id']
    candidates = deepcopy(app.extensions['chat_store'].get(session_id)[0]['_candidates'])
    description = 'Stelle kurze, konkrete Rückfragen zu den Empfehlungen.'
    changed_advisor = {**initial['advisor'], 'description': f'\n{description}  '}
    llm.calls.clear()
    retriever.calls.clear()

    def unexpected_filter(*args, **kwargs):
        pytest.fail('Eine Persönlichkeitsbeschreibung darf keine SQL-Vorauswahl auslösen.')

    monkeypatch.setattr(app.extensions['job_store'], 'filter_jobs', unexpected_filter)
    response = client.post('/api/chat', json={'session_id': session_id, 'advisor': changed_advisor})
    assert response.status_code == 200
    assert response.json['chat_action'] == 'rerank'
    assert llm.calls == ['rerank'] and not retriever.calls
    assert response.json['advisor']['description'] == description
    assert llm.last_rerank_context['advisor']['description'] == description
    assert llm.last_rerank_candidates == candidates
    assert response.json['profile'] == initial['profile']
    assert response.json['persona'] == initial['persona']
    assert response.json['retrieval'] == initial['retrieval']
    assert response.json['candidate_pool'] == initial['candidate_pool']
    assert app.extensions['chat_store'].get(session_id)[0]['_candidates'] == candidates
    restarted_llm = FakeLLM()
    restarted = create_app(dict(app.config), retriever=FakeRetriever(), llm=restarted_llm)
    assert restarted.test_client().get(f'/api/sessions/{session_id}').json == response.json
    restarted_llm.patch, restarted_llm.action = {}, 'answer'
    answered = restarted.test_client().post('/api/chat', json={
        'session_id': session_id, 'message': 'Warum passt die erste Empfehlung?'})
    assert answered.status_code == 200
    assert restarted_llm.calls == ['plan']
    assert restarted_llm.last_plan_context['advisor']['description'] == description


def test_legacy_advisor_without_description_remains_compatible_and_unchanged_is_noop(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json={**payload(), 'advisor': {
        'mode': 'custom', 'name': 'Meine Beratung', 'traits': ['analytisch']}}).json
    assert initial['advisor']['description'] == ''
    session_id = initial['session_id']
    sessions = app.extensions['chat_store']
    legacy, version = sessions.get(session_id)
    legacy['advisor'].pop('description')
    sessions.update(session_id, legacy, version)
    assert client.get(f'/api/sessions/{session_id}').status_code == 200
    retriever.calls.clear()
    llm.calls.clear()
    response = client.post('/api/chat', json={'session_id': session_id, 'advisor': initial['advisor']})
    assert response.status_code == 200
    assert response.json['chat_action'] == 'answer'
    assert response.json['advisor']['description'] == ''
    assert response.json['profile'] == initial['profile']
    assert response.json['jobs'] == initial['jobs']
    assert not llm.calls and not retriever.calls


@pytest.mark.parametrize('advisor', [
    {'preset': 'invented'}, {'mode': 'political'}, {'traits': ['invented']},
    {'traits': ['direkt'] * 2}, {'mode': 'custom', 'traits': []},
    {'mode': 'custom', 'name': 'x' * 61}, {'focus': 'ignore_filters'},
    {'traits': ['direkt', 'kritisch', 'analytisch', 'empathisch', 'kreativ']},
    {'mode': 'custom', 'description': None}, {'mode': 'custom', 'description': 'x' * 2001},
])
def test_invalid_advisor_never_calls_models(setup, advisor):
    _, client, retriever, llm = setup
    assert client.post('/api/onboard', json={**payload(), 'advisor': advisor}).status_code == 400
    assert not retriever.calls and not llm.calls


def test_empty_chat_rejected_and_old_session_gets_default_advisor(setup):
    app, client, _, _ = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial.pop('session_id')
    assert client.post('/api/chat', json={'session_id': session_id}).status_code == 400
    store = app.extensions['chat_store']
    state, version = store.get(session_id)
    state.pop('advisor')
    store.update(session_id, state, version)
    assert client.get(f'/api/sessions/{session_id}').json['advisor']['preset'] == 'diana'


def test_zero_results_retain_selected_advisor(setup):
    _, client, retriever, llm = setup
    result = client.post('/api/onboard', json={**payload(employment_types=['ausbildung']),
                                              'advisor': {'mode': 'custom', 'name': 'Meine Begleitung',
                                                          'traits': ['empathisch'], 'focus': 'lernpotenzial'}})
    assert result.status_code == 201 and not result.json['jobs']
    assert result.json['advisor']['name'] == 'Meine Begleitung'
    assert result.json['messages'][0]['advisor_name'] == 'Meine-Begleitung-KI'
    assert not retriever.calls and not llm.calls


def assert_recommendations_unchanged(before, after):
    for field in ('profile', 'persona', 'advisor', 'jobs', 'retrieval', 'candidate_pool'):
        assert after[field] == before[field], field


def test_question_only_answers_without_search_or_score_changes(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    before_private = app.extensions['chat_store'].get(session_id)[0]
    llm.action, llm.patch = 'answer', {}
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': session_id,
                                              'message': 'Warum passt die erste Stelle zu mir?'})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'answer'
    assert response.json['assistant_message'] == llm.answer
    assert_recommendations_unchanged(initial, response.json)
    assert llm.calls == ['plan'] and not retriever.calls
    assert llm.last_plan_context['jobs'] == initial['jobs']
    assert llm.last_plan_context['history'] == initial['messages']
    assert llm.last_plan_context['profile'] == initial['profile']
    assert llm.last_plan_context['advisor'] == initial['advisor']
    assert llm.last_plan_context['mode'] == 'auto'
    assert llm.last_plan_context['candidate_count'] == 5
    saved = app.extensions['chat_store'].get(session_id)[0]
    assert saved['_candidates'] == before_private['_candidates']
    assert len(response.json['messages']) == len(initial['messages']) + 2
    assert client.get(f'/api/sessions/{session_id}').json == response.json


def test_soft_preference_change_only_reranks_even_if_planner_says_answer(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    pool = app.extensions['chat_store'].get(initial['session_id'])[0]['_candidates']
    llm.action = 'answer'
    llm.patch = {'preferences': ['Mentoring ist besonders wichtig']}
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                              'message': 'Gewichte Mentoring bitte höher.'})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'rerank'
    assert llm.calls == ['plan', 'rerank'] and not retriever.calls
    assert response.json['profile']['preferences'] == ['Mentoring ist besonders wichtig']
    assert response.json['persona'] == initial['persona']
    for field in ('query', 'skills', 'cv_text', 'filters'):
        assert response.json['profile'][field] == initial['profile'][field]
    assert llm.last_rerank_candidates == pool
    assert llm.last_rerank_context['chat_context']['scope'] == 'existing_candidates'
    assert llm.rerank_calls[-1]['profile'] == response.json['profile']
    assert app.extensions['chat_store'].get(initial['session_id'])[0]['_candidates'] == pool


def test_explicitly_planned_new_search_is_not_reduced_to_preference_rerank(setup):
    _, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    llm.action = 'search'
    llm.patch = {'preferences': ['Mehr Gestaltungsspielraum']}
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'auto',
                                              'message': 'Suche weitere Stellen mit mehr Gestaltungsspielraum.'})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'search'
    assert llm.calls == ['plan', 'persona', 'rerank'] and len(retriever.calls) == 1
    assert response.json['profile']['preferences'] == ['Mehr Gestaltungsspielraum']
    assert llm.last_rerank_context['chat_context']['scope'] == 'new_search'


def test_twenty_evaluated_cards_survive_restart_rerank_and_question_with_private_pool_and_cache(setup, tmp_path):
    app, client, retriever, llm = setup
    import_additional_jobs(app, tmp_path)
    cached = {'fingerprint': 'PRIVATE_TWENTY_ASSESSMENTS', 'assessments': []}
    llm.assessment_cache_output = cached
    onboarded = client.post('/api/onboard', json=payload())
    assert onboarded.status_code == 201
    initial = onboarded.json
    session_id = initial['session_id']
    saved = app.extensions['chat_store'].get(session_id)[0]
    pool = saved['_candidates']
    pool_ids = [item['job']['id'] for item in pool]
    assert initial['retrieval'] == {'filtered_count': 30, 'candidate_count': 20}
    assert initial['candidate_pool'] == {'available': True, 'count': 20, 'refresh_required': False}
    assert len(initial['jobs']) == len(pool) == 20
    assert [job['id'] for job in initial['jobs']] == pool_ids
    assert all(job['match']['reason'] == 'Python passt.' for job in initial['jobs'])
    assert saved['_assessment_cache'] == cached
    assert all('search_text' not in item['job'] and 'raw' not in item['job'] for item in pool)
    for public in (initial, client.get(f'/api/sessions/{session_id}').json):
        assert '_candidates' not in public
        assert '_assessment_cache' not in public
        assert 'PRIVATE_TWENTY_ASSESSMENTS' not in json.dumps(public)
        assert 'search_text' not in json.dumps(public)

    restarted_llm, restarted_retriever = FakeLLM(), FakeRetriever()
    restarted_llm.ranking_indices = list(reversed(range(20)))
    restarted_llm.assessment_cache_output = cached
    restarted = create_app(dict(app.config), retriever=restarted_retriever, llm=restarted_llm)
    restarted_client = restarted.test_client()
    assert restarted_client.get(f'/api/sessions/{session_id}').json == initial
    assert not restarted_llm.calls and not restarted_retriever.calls
    response = restarted_client.post('/api/chat', json={'session_id': session_id,
                                                       'advisor': {'preset': 'angela'}})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'rerank'
    assert restarted_llm.calls == ['rerank'] and not restarted_retriever.calls
    assert restarted_llm.last_rerank_candidates == pool
    assert restarted_llm.last_rerank_context['chat_context']['jobs'] == initial['jobs']
    assert restarted_llm.last_rerank_context['assessment_cache'] == cached
    assert [job['id'] for job in response.json['jobs']] == list(reversed(pool_ids))
    assert response.json['profile'] == initial['profile']
    assert response.json['persona'] == initial['persona']
    assert response.json['advisor']['preset'] == 'angela'
    assert response.json['candidate_pool'] == {'available': True, 'count': 20, 'refresh_required': False}
    assert '_candidates' not in response.json
    assert '_assessment_cache' not in response.json
    assert 'PRIVATE_TWENTY_ASSESSMENTS' not in json.dumps(response.json)
    assert restarted.extensions['chat_store'].get(session_id)[0]['_candidates'] == pool
    assert restarted_client.get(f'/api/sessions/{session_id}').json == response.json


    restarted_llm.calls.clear()
    restarted_llm.action, restarted_llm.patch = 'answer', {}
    answered = restarted_client.post('/api/chat', json={
        'session_id': session_id, 'message': f"Warum passt die zwanzigste Stelle (Job-ID {pool_ids[0]})?"})
    assert answered.status_code == 200
    assert answered.json['chat_action'] == 'answer'
    assert restarted_llm.calls == ['plan'] and not restarted_retriever.calls
    assert restarted_llm.last_plan_context['jobs'] == response.json['jobs']
    assert restarted_llm.last_plan_context['candidate_count'] == 20
    assert_recommendations_unchanged(response.json, answered.json)
    final_state = restarted.extensions['chat_store'].get(session_id)[0]
    assert final_state['_candidates'] == pool
    assert final_state['_assessment_cache'] == cached
    assert '_candidates' not in answered.json and '_assessment_cache' not in answered.json
    assert 'PRIVATE_TWENTY_ASSESSMENTS' not in json.dumps(answered.json)
    assert restarted_client.get(f'/api/sessions/{session_id}').json == answered.json


def test_legacy_five_cards_expand_only_after_normal_rerank_without_automatic_migration(setup, tmp_path):
    app, client, retriever, llm = setup
    import_additional_jobs(app, tmp_path)
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    sessions = app.extensions['chat_store']
    legacy, version = sessions.get(session_id)
    legacy['jobs'] = legacy['jobs'][:5]
    for job in legacy['jobs']:
        job['match']['reason'] = 'Gespeicherte frühere Begründung.'
    sessions.update(session_id, legacy, version)
    pool = deepcopy(legacy['_candidates'])
    retriever.calls.clear()
    llm.calls.clear()

    restored = client.get(f'/api/sessions/{session_id}')
    assert restored.status_code == 200
    assert len(restored.json['jobs']) == 5
    assert restored.json['jobs'] == legacy['jobs']
    assert restored.json['candidate_pool']['count'] == 20
    assert not llm.calls and not retriever.calls
    llm.action, llm.patch = 'answer', {}
    answered = client.post('/api/chat', json={'session_id': session_id,
                                             'message': 'Erkläre mir die gespeicherten Empfehlungen.'})
    assert answered.status_code == 200
    assert answered.json['chat_action'] == 'answer'
    assert llm.calls == ['plan'] and not retriever.calls
    assert llm.last_plan_context['jobs'] == legacy['jobs']
    assert_recommendations_unchanged(restored.json, answered.json)
    assert sessions.get(session_id)[0]['_candidates'] == pool

    llm.calls.clear()
    reranked = client.post('/api/chat', json={'session_id': session_id, 'mode': 'rerank'})
    assert reranked.status_code == 200
    assert reranked.json['chat_action'] == 'rerank'
    assert llm.calls == ['rerank'] and not retriever.calls
    assert llm.last_rerank_candidates == pool
    assert len(reranked.json['jobs']) == 20
    assert {job['id'] for job in reranked.json['jobs']} == {item['job']['id'] for item in pool}
    assert all(job['match']['reason'] == 'Python passt.' for job in reranked.json['jobs'])
    assert reranked.json['profile'] == restored.json['profile']
    assert reranked.json['persona'] == restored.json['persona']
    assert '_candidates' not in reranked.json and '_assessment_cache' not in reranked.json
    assert sessions.get(session_id)[0]['_candidates'] == pool
    assert client.get(f'/api/sessions/{session_id}').json == reranked.json


def test_assessment_cache_stays_private_survives_answers_and_is_forwarded_after_restart(setup):
    app, client, _, llm = setup
    cached = {'fingerprint': 'PRIVATE_ASSESSMENT_SENTINEL', 'assessments': [{'job_id': 'example'}]}
    llm.assessment_cache_output = cached
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    assert llm.last_rerank_context['assessment_cache'] is None
    assert app.extensions['chat_store'].get(session_id)[0]['_assessment_cache'] == cached
    for public in (initial, client.get(f'/api/sessions/{session_id}').json):
        assert 'assessment_cache' not in public and '_assessment_cache' not in public
        assert 'PRIVATE_ASSESSMENT_SENTINEL' not in json.dumps(public)

    llm.action, llm.patch = 'answer', {}
    llm.calls.clear()
    answer = client.post('/api/chat', json={'session_id': session_id,
                                          'message': 'Warum passt diese Stelle?'}).json
    assert llm.calls == ['plan']
    assert_recommendations_unchanged(initial, answer)
    assert app.extensions['chat_store'].get(session_id)[0]['_assessment_cache'] == cached

    restarted_llm, restarted_retriever = FakeLLM(), FakeRetriever()
    refreshed = {'fingerprint': 'UPDATED_PRIVATE_ASSESSMENT_SENTINEL', 'assessments': []}
    restarted_llm.assessment_cache_output = refreshed
    restarted = create_app(dict(app.config), retriever=restarted_retriever, llm=restarted_llm)
    restarted_client = restarted.test_client()
    response = restarted_client.post('/api/chat', json={'session_id': session_id,
                                                        'advisor': {'preset': 'angela'}})
    assert response.status_code == 200
    assert restarted_llm.calls == ['rerank'] and not restarted_retriever.calls
    assert restarted_llm.last_rerank_context['assessment_cache'] == cached
    assert restarted.extensions['chat_store'].get(session_id)[0]['_assessment_cache'] == refreshed
    assert response.json['profile'] == initial['profile']
    assert response.json['candidate_pool'] == initial['candidate_pool']
    assert 'assessment_cache' not in response.json and '_assessment_cache' not in response.json
    assert 'PRIVATE_ASSESSMENT_SENTINEL' not in json.dumps(response.json)
    assert restarted_client.get(f'/api/sessions/{session_id}').json == response.json


@pytest.mark.parametrize('change', ['explicit_search', 'profile'])
def test_new_search_never_forwards_or_retains_the_previous_assessment_cache(setup, change):
    app, client, retriever, llm = setup
    llm.assessment_cache_output = {'fingerprint': 'PREVIOUS_ASSESSMENT_SENTINEL'}
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    llm.assessment_cache_output = None
    llm.calls.clear()
    retriever.calls.clear()
    body = {'session_id': session_id}
    if change == 'explicit_search':
        body['mode'] = 'search'
    else:
        body['profile'] = {**initial['profile'], 'skills': ['Python', 'SQL', 'Rust']}

    response = client.post('/api/chat', json=body)

    assert response.status_code == 200 and response.json['chat_action'] == 'search'
    assert llm.calls == (['rerank'] if change == 'explicit_search' else ['persona', 'rerank'])
    assert len(retriever.calls) == 1
    assert llm.last_rerank_context['assessment_cache'] is None
    assert '_assessment_cache' not in app.extensions['chat_store'].get(session_id)[0]
    assert 'PREVIOUS_ASSESSMENT_SENTINEL' not in json.dumps(response.json)


def test_existing_candidate_pool_without_assessment_cache_can_be_reranked(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    assert '_assessment_cache' not in app.extensions['chat_store'].get(session_id)[0]
    llm.assessment_cache_output = {'fingerprint': 'FIRST_ASSESSMENT_SENTINEL'}
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': session_id, 'mode': 'rerank'})

    assert response.status_code == 200 and response.json['chat_action'] == 'rerank'
    assert llm.last_rerank_context['assessment_cache'] is None
    assert not retriever.calls
    assert app.extensions['chat_store'].get(session_id)[0]['_assessment_cache'] == llm.assessment_cache_output
    assert 'FIRST_ASSESSMENT_SENTINEL' not in json.dumps(response.json)


def test_stateless_search_keeps_assessment_cache_out_of_public_response(setup):
    _, client, _, llm = setup
    llm.assessment_cache_output = {'fingerprint': 'STATELESS_PRIVATE_SENTINEL'}

    response = client.post('/api/search', json=payload())

    assert response.status_code == 200
    assert llm.last_rerank_context['assessment_cache'] is None
    assert 'assessment_cache' not in response.json and '_assessment_cache' not in response.json
    assert 'STATELESS_PRIVATE_SENTINEL' not in json.dumps(response.json)


@pytest.mark.parametrize('trigger', ['button', 'chat'])
@pytest.mark.parametrize('restart', [False, True])
def test_unchanged_profile_reuses_private_persona_but_searches_fresh_jobs_and_assessments(setup, tmp_path, trigger, restart):
    app, client, retriever, llm = setup
    llm.assessment_cache_output = {'fingerprint': 'OLD_PRIVATE_ASSESSMENTS'}
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    marker = app.extensions['chat_store'].get(session_id)[0]['_persona_fingerprint']
    assert marker == persona_fingerprint(initial['profile'])
    assert marker.startswith(PERSONA_CACHE_VERSION + ':')
    import_additional_jobs(app, tmp_path, count=1)
    if restart:
        retriever, llm = FakeRetriever(), FakeLLM()
        app = create_app(dict(app.config), retriever=retriever, llm=llm)
        client = app.test_client()
        assert client.get(f'/api/sessions/{session_id}').json == initial
    llm.calls.clear()
    retriever.calls.clear()
    llm.action, llm.patch, llm.assessment_cache_output = 'search', {}, None
    body = {'session_id': session_id, 'advisor': {'preset': 'steve'}}
    if trigger == 'button':
        body.update(mode='search', profile=deepcopy(initial['profile']))
    else:
        body.update(mode='auto', message='Suche nochmals nach neuen Stellen.')
    response = client.post('/api/chat', json=body)
    assert response.status_code == 200 and response.json['chat_action'] == 'search'
    assert llm.calls == (['rerank'] if trigger == 'button' else ['plan', 'rerank'])
    assert len(retriever.calls) == 1 and len(retriever.calls[0][0]) == 6
    assert response.json['retrieval']['filtered_count'] == 6 and len(response.json['jobs']) == 6
    assert response.json['persona'] == initial['persona']
    assert response.json['advisor']['preset'] == 'steve'
    assert llm.last_rerank_context['assessment_cache'] is None
    state = app.extensions['chat_store'].get(session_id)[0]
    assert state['_persona_fingerprint'] == marker and '_assessment_cache' not in state
    for public in (initial, response.json, client.get(f'/api/sessions/{session_id}').json):
        assert '_persona_fingerprint' not in public and marker not in json.dumps(public)


@pytest.mark.parametrize('field,value', [
    ('query', 'Forschung mit Python'), ('skills', ['Python', 'Rust']),
    ('cv_text', 'Erfahrung mit Datenanalyse.'), ('preferences', ['Klare Betreuung']),
    ('filters.employment_types', ['praktikum']), ('filters.locations', ['Berlin']),
    ('filters.remote', ['remote']), ('filters.max_hours', 20.0),
])
def test_full_search_invalidates_persona_for_every_changed_profile_field(setup, field, value):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    original_marker = app.extensions['chat_store'].get(session_id)[0]['_persona_fingerprint']
    profile = deepcopy(initial['profile'])
    if field.startswith('filters.'):
        profile['filters'][field.split('.')[1]] = value
    else:
        profile[field] = value
    llm.calls.clear()
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': session_id, 'mode': 'search', 'profile': profile})
    assert response.status_code == 200 and response.json['chat_action'] == 'search'
    assert llm.calls == ['persona', 'rerank'] and len(retriever.calls) == 1
    assert llm.persona_profiles[-1] == response.json['profile'] == profile
    new_marker = app.extensions['chat_store'].get(session_id)[0]['_persona_fingerprint']
    assert new_marker == persona_fingerprint(profile) and new_marker != original_marker
    assert '_persona_fingerprint' not in response.json


@pytest.mark.parametrize('invalid', ['missing_marker', 'null_marker', 'wrong_version', 'unversioned',
                                      'wrong_hash', 'missing_persona', 'null_persona', 'malformed_persona'])
def test_missing_or_invalid_persona_cache_regenerates_once(setup, invalid):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    sessions = app.extensions['chat_store']
    state, version = sessions.get(session_id)
    if invalid == 'missing_marker':
        state.pop('_persona_fingerprint')
    elif invalid == 'null_marker':
        state['_persona_fingerprint'] = None
    elif invalid == 'wrong_version':
        state['_persona_fingerprint'] = state['_persona_fingerprint'].replace(PERSONA_CACHE_VERSION, 'old-version')
    elif invalid == 'unversioned':
        state['_persona_fingerprint'] = state['_persona_fingerprint'].split(':')[1]
    elif invalid == 'wrong_hash':
        state['_persona_fingerprint'] = PERSONA_CACHE_VERSION + ':' + '0' * 64
    elif invalid == 'missing_persona':
        state.pop('persona')
    elif invalid == 'null_persona':
        state['persona'] = None
    else:
        state['persona'] = {**state['persona'], 'retrieval_query': ''}
    sessions.update(session_id, state, version)
    llm.calls.clear()
    retriever.calls.clear()
    first = client.post('/api/chat', json={'session_id': session_id, 'mode': 'search'})
    assert first.status_code == 200
    assert llm.calls == ['persona', 'rerank'] and len(retriever.calls) == 1
    assert sessions.get(session_id)[0]['_persona_fingerprint'] == persona_fingerprint(initial['profile'])
    llm.calls.clear()
    second = client.post('/api/chat', json={'session_id': session_id, 'mode': 'search'})
    assert second.status_code == 200 and llm.calls == ['rerank'] and len(retriever.calls) == 2


@pytest.mark.parametrize('field,value', [
    ('cv_text', 'Ein neuer Abschluss in Informatik.'), ('preferences', ['Lernen im Team']),
    ('filters.locations', ['Köln']), ('filters.remote', ['hybrid']), ('filters.max_hours', 18.0),
])
def test_soft_profile_rerank_preserves_original_persona_marker_until_later_search(setup, field, value):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    sessions = app.extensions['chat_store']
    marker = sessions.get(session_id)[0]['_persona_fingerprint']
    profile = deepcopy(initial['profile'])
    if field.startswith('filters.'):
        profile['filters'][field.split('.')[1]] = value
    else:
        profile[field] = value
    llm.calls.clear()
    retriever.calls.clear()
    reranked = client.post('/api/chat', json={'session_id': session_id, 'profile': profile})
    assert reranked.status_code == 200 and reranked.json['chat_action'] == 'rerank'
    assert llm.calls == ['rerank'] and not retriever.calls
    assert reranked.json['persona'] == initial['persona']
    assert sessions.get(session_id)[0]['_persona_fingerprint'] == marker != persona_fingerprint(profile)
    llm.calls.clear()
    refreshed = client.post('/api/chat', json={'session_id': session_id, 'mode': 'search'})
    assert refreshed.status_code == 200
    assert llm.calls == ['persona', 'rerank'] and len(retriever.calls) == 1
    assert llm.persona_profiles[-1] == profile
    assert sessions.get(session_id)[0]['_persona_fingerprint'] == persona_fingerprint(profile)


def test_persona_version_bump_invalidates_existing_marker(setup, monkeypatch):
    app, client, _, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    llm.calls.clear()
    monkeypatch.setattr('app.PERSONA_CACHE_VERSION', 'search-persona-next')
    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'search'})
    assert response.status_code == 200 and llm.calls == ['persona', 'rerank']
    assert app.extensions['chat_store'].get(initial['session_id'])[0]['_persona_fingerprint'].startswith('search-persona-next:')


def test_persona_cache_is_session_local_and_phase_logs_contain_only_timings(setup, caplog):
    app, client, _, llm = setup
    body = payload()
    body['profile']['cv_text'] = 'PRIVATE_CV_SENTINEL'
    first = client.post('/api/onboard', json=body).json
    second = client.post('/api/onboard', json=body).json
    assert llm.calls == ['persona', 'rerank', 'persona', 'rerank']
    refreshed = client.post('/api/chat', json={'session_id': first['session_id'], 'mode': 'search'})
    assert refreshed.status_code == 200
    assert llm.calls == ['persona', 'rerank', 'persona', 'rerank', 'rerank']
    events = [json.loads(record.message) for record in caplog.records
              if record.name == app.logger.name + '.performance']
    assert {event['phase'] for event in events} == {'prefilter', 'persona', 'retrieval', 'rerank'}
    assert [event['cache_hit'] for event in events if event['phase'] == 'persona'] == [False, False, True]
    for event in events:
        assert set(event) <= {'event', 'phase', 'elapsed_ms', 'status', 'cache_hit'}
        assert event['event'] == 'matching_phase' and event['status'] == 'ok'
        assert isinstance(event['elapsed_ms'], (int, float)) and event['elapsed_ms'] >= 0
    assert 'PRIVATE_CV_SENTINEL' not in caplog.text
    assert first['session_id'] not in caplog.text and second['session_id'] not in caplog.text


@pytest.mark.parametrize('patch', [
    {'filters': {'employment_types': ['praktikum']}},
    {'query': 'Frontend-Entwicklung mit TypeScript'},
    {'skills': ['Python', 'SQL', 'TypeScript']},
])
@pytest.mark.parametrize('classification', ['answer', 'rerank'])
def test_changed_core_input_forces_search_despite_planner_classification(setup, patch, classification):
    _, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    llm.action, llm.patch = classification, patch
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                              'message': 'Bitte meine Suchkriterien aktualisieren.'})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'search'
    assert llm.calls == ['plan', 'persona', 'rerank'] and len(retriever.calls) == 1
    assert response.json['profile'] == merge_profile(initial['profile'], patch)
    assert llm.last_rerank_context['chat_context']['scope'] == 'new_search'
    if 'filters' in patch:
        assert all('praktikum' in job['employment_types'] for job in retriever.calls[0][0])


@pytest.mark.parametrize('field,value', [
    ('query', 'NLP-Forschungspraktikum'), ('skills', ['PyTorch', 'Python']),
    ('filters', {'employment_types': ['praktikum'], 'remote': [], 'locations': [], 'max_hours': None}),
])
def test_full_profile_edit_without_message_runs_search_without_planner(setup, field, value):
    _, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    updated_profile = deepcopy(initial['profile'])
    updated_profile[field] = value
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                              'profile': updated_profile})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'search'
    assert response.json['profile'] == updated_profile
    assert llm.calls == ['persona', 'rerank'] and len(retriever.calls) == 1
    assert len(response.json['messages']) == len(initial['messages']) + 1
    assert llm.last_plan_context is None


@pytest.mark.parametrize('submitted', ['profile', 'advisor'])
def test_unchanged_form_submission_avoids_all_model_calls(setup, submitted):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    pool = app.extensions['chat_store'].get(initial['session_id'])[0]['_candidates']
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                              submitted: initial[submitted]})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'answer'
    assert_recommendations_unchanged(initial, response.json)
    assert not llm.calls and not retriever.calls
    assert app.extensions['chat_store'].get(initial['session_id'])[0]['_candidates'] == pool


@pytest.mark.parametrize('patch,planned_action', [
    ({'filters': {'employment_types': ['praktikum']}}, 'rerank'),
    ({}, 'search'),
])
def test_explicit_rerank_refuses_new_search_and_preserves_results(setup, patch, planned_action):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    pool = app.extensions['chat_store'].get(initial['session_id'])[0]['_candidates']
    llm.action, llm.patch = planned_action, patch
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'rerank',
                                              'message': 'Suche andere passende Stellen.'})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'answer'
    assert 'neue Suche' in response.json['assistant_message']
    assert_recommendations_unchanged(initial, response.json)
    assert llm.calls == ['plan'] and not retriever.calls
    assert llm.last_plan_context['mode'] == 'rerank'
    assert app.extensions['chat_store'].get(initial['session_id'])[0]['_candidates'] == pool


def test_rerank_mode_also_refuses_changed_full_profile_without_calling_llm(setup):
    _, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    changed_profile = deepcopy(initial['profile'])
    changed_profile['filters']['employment_types'] = ['praktikum']
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                              'mode': 'rerank', 'profile': changed_profile})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'answer'
    assert_recommendations_unchanged(initial, response.json)
    assert not llm.calls and not retriever.calls


def test_explicit_new_search_with_empty_message_rebuilds_selection(setup):
    _, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                              'mode': 'search', 'message': ''})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'search'
    assert response.json['profile'] == initial['profile']
    assert llm.calls == ['rerank'] and len(retriever.calls) == 1
    assert llm.last_plan_context is None
    assert response.json['candidate_pool'] == {'available': True, 'count': 5, 'refresh_required': False}


def test_legacy_session_cannot_rerank_but_can_answer_without_retrieval(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    sessions = app.extensions['chat_store']
    legacy, version = sessions.get(session_id)
    legacy.pop('_candidates')
    sessions.update(session_id, legacy, version)
    baseline = client.get(f'/api/sessions/{session_id}').json
    assert baseline['candidate_pool'] == {'available': False, 'count': 0, 'refresh_required': False}
    llm.calls.clear()
    retriever.calls.clear()

    refused = client.post('/api/chat', json={'session_id': session_id, 'mode': 'rerank'})

    assert refused.status_code == 200
    assert refused.json['chat_action'] == 'answer'
    assert 'älteren Chat' in refused.json['assistant_message']
    assert 'Neue Suche' in refused.json['assistant_message']
    assert_recommendations_unchanged(baseline, refused.json)
    assert '_candidates' not in sessions.get(session_id)[0]
    assert not llm.calls and not retriever.calls

    llm.action, llm.patch = 'answer', {}
    answered = client.post('/api/chat', json={'session_id': session_id,
                                              'message': 'Welche Skills verlangt die erste Stelle?'})
    assert answered.status_code == 200
    assert answered.json['assistant_message'] == llm.answer
    assert_recommendations_unchanged(baseline, answered.json)
    assert llm.calls == ['plan'] and not retriever.calls
    assert llm.last_plan_context['candidate_count'] == 0
    assert llm.last_plan_context['jobs'] == initial['jobs']


def test_empty_candidate_pool_never_calls_reranker(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload(employment_types=['ausbildung'])).json
    assert initial['candidate_pool'] == {'available': True, 'count': 0, 'refresh_required': False}

    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'rerank',
                                              'advisor': {'preset': 'steve'}})

    assert response.status_code == 200
    assert response.json['chat_action'] == 'answer'
    assert 'keine Jobs vorhanden' in response.json['assistant_message']
    assert_recommendations_unchanged(initial, response.json)
    assert response.json['messages'][-1]['advisor_name'] == 'DIANA-KI'
    assert not llm.calls and not retriever.calls
    assert app.extensions['chat_store'].get(initial['session_id'])[0]['_candidates'] == []


@pytest.mark.parametrize('action', ['answer', 'rerank'])
def test_pending_index_does_not_block_answers_or_cached_reranking(setup, action):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    app.config['REQUIRE_COMPLETE_INDEX'] = True
    assert client.get('/api/index-status').json['status'] == 'pending'
    llm.action, llm.patch = action, {}
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                              'message': 'Bitte erläutere die Auswahl.'})

    assert response.status_code == 200
    assert response.json['chat_action'] == action
    assert llm.calls == (['plan'] if action == 'answer' else ['plan', 'rerank'])
    assert not retriever.calls
    assert response.json['profile'] == initial['profile']
    assert response.json['persona'] == initial['persona']
    assert response.json['candidate_pool'] == initial['candidate_pool']


def test_pending_index_still_blocks_new_search_and_keeps_existing_session(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    before = app.extensions['chat_store'].get(initial['session_id'])
    app.config['REQUIRE_COMPLETE_INDEX'] = True
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'search'})

    assert response.status_code == 503
    assert response.json['error']['code'] == 'llm_unavailable'
    assert not llm.calls and not retriever.calls
    assert app.extensions['chat_store'].get(initial['session_id']) == before
    assert client.get(f"/api/sessions/{initial['session_id']}").json == initial


def test_failed_preference_rerank_does_not_commit_profile_messages_or_pool(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    before = app.extensions['chat_store'].get(session_id)
    llm.action, llm.patch = 'rerank', {'preferences': ['Mehr Mentoring']}
    retriever.calls.clear()

    def fail(*args, **kwargs):
        raise LLMUnavailable('Reranking nicht verfügbar.')

    llm.rerank = fail
    response = client.post('/api/chat', json={'session_id': session_id,
                                              'message': 'Gewichte Mentoring höher.'})

    assert response.status_code == 503
    assert not retriever.calls
    assert app.extensions['chat_store'].get(session_id) == before
    assert client.get(f'/api/sessions/{session_id}').json == initial


@pytest.mark.parametrize('stage', ['persona', 'retrieval', 'rerank'])
def test_failed_profile_search_leaves_persisted_session_untouched(setup, stage):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    before = app.extensions['chat_store'].get(session_id)
    changed_profile = deepcopy(initial['profile'])
    changed_profile['skills'] = ['Python', 'SQL', 'PyTorch']

    def fail(*args, **kwargs):
        if stage == 'retrieval':
            raise EmbeddingUnavailable('E5 unavailable')
        raise LLMUnavailable('KI nicht verfügbar.')

    if stage == 'persona':
        llm.generate_persona = fail
    elif stage == 'retrieval':
        retriever.search = fail
    else:
        llm.rerank = fail
    response = client.post('/api/chat', json={'session_id': session_id, 'profile': changed_profile})

    assert response.status_code == 503
    assert app.extensions['chat_store'].get(session_id) == before
    assert client.get(f'/api/sessions/{session_id}').json == initial


@pytest.mark.parametrize('changes', [
    {'mode': 'invented'}, {'message': 'Frage', 'profile': payload()['profile']},
    {'profile': {'query': 'Python', 'filters': {'remote': ['sometimes']}}},
])
def test_invalid_dispatch_request_never_calls_models_or_changes_session(setup, changes):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    session_id = initial['session_id']
    before = app.extensions['chat_store'].get(session_id)
    llm.calls.clear()
    retriever.calls.clear()

    response = client.post('/api/chat', json={'session_id': session_id, **changes})

    assert response.status_code == 400
    assert not llm.calls and not retriever.calls
    assert app.extensions['chat_store'].get(session_id) == before


def test_location_whitespace_changes_do_not_search_or_drop_jobs(setup):
    app, client, retriever, llm = setup
    location = next(job['location'] for job in app.extensions['job_store'].filter_jobs({})
                    if ' ' in job['location'])
    initial = client.post('/api/onboard', json=payload(locations=[location])).json
    assert initial['jobs']
    updated = deepcopy(initial['profile'])
    updated['filters']['locations'] = [location.replace(' ', '  ', 1)]
    assert app.extensions['job_store'].filter_jobs(updated['filters'])
    llm.calls.clear()
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'profile': updated})
    assert response.status_code == 200
    assert response.json['chat_action'] == 'answer'
    assert response.json['jobs'] == initial['jobs']
    assert response.json['candidate_pool'] == initial['candidate_pool']
    # Whitespace alone changes no search or assessment evidence.
    assert not retriever.calls and not llm.calls


def test_location_remote_hours_and_cv_reach_llm_without_excluding_jobs(setup):
    app, client, retriever, llm = setup
    requested = payload(employment_types=['werkstudent'], locations=['AtlantisImpossible'],
                        remote=['remote'], max_hours=1)
    requested['profile']['cv_text'] = 'Synthetischer Lebenslauf ohne Angaben zur Datenanalyse.'
    response = client.post('/api/search', json=requested)
    expected = app.extensions['job_store'].filter_jobs({'employment_types': ['werkstudent']})
    assert response.status_code == 200
    assert {job['id'] for job in retriever.calls[0][0]} == {job['id'] for job in expected}
    assert response.json['retrieval']['filtered_count'] == 3
    assert any(job['remote'] != 'remote' for job in retriever.calls[0][0])
    assert any(job['hours_max'] > 1 for job in retriever.calls[0][0])
    assessed_profile = llm.rerank_calls[-1]['profile']
    assert assessed_profile['filters'] == requested['profile']['filters']
    assert assessed_profile['cv_text'] == requested['profile']['cv_text']
    assert response.json['candidate_pool']['refresh_required'] is False
    assert '_matching_policy_version' not in response.json


@pytest.mark.parametrize('mode', ['auto', 'rerank'])
@pytest.mark.parametrize('field,value', [
    ('locations', ['München']), ('remote', ['remote']), ('max_hours', 15.0),
    ('cv_text', 'Python-Projekt und SQL-Kenntnisse aus dem Studium.'),
])
def test_soft_profile_edit_reranks_same_pool_without_retrieval(setup, mode, field, value):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    pool = app.extensions['chat_store'].get(initial['session_id'])[0]['_candidates']
    changed = deepcopy(initial['profile'])
    (changed if field == 'cv_text' else changed['filters'])[field] = value
    llm.calls.clear()
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                             'profile': changed, 'mode': mode})
    assert response.status_code == 200 and response.json['chat_action'] == 'rerank'
    assert response.json['profile'] == changed
    assert response.json['persona'] == initial['persona']
    assert llm.calls == ['rerank'] and not retriever.calls
    assert llm.last_rerank_candidates == pool
    assert llm.rerank_calls[-1]['profile'] == changed


@pytest.mark.parametrize('patch', [
    {'filters': {'locations': ['Berlin']}}, {'filters': {'remote': ['hybrid']}},
    {'filters': {'max_hours': 15}}, {'filters': {'clear_max_hours': True}},
])
@pytest.mark.parametrize('classification', ['answer', 'rerank'])
def test_soft_chat_patch_reranks_even_if_planner_says_answer(setup, patch, classification):
    _, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload(max_hours=20)).json
    llm.action, llm.patch = classification, patch
    llm.calls.clear()
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                             'message': 'Bitte meinen Wunsch aktualisieren.'})
    assert response.status_code == 200 and response.json['chat_action'] == 'rerank'
    assert response.json['profile'] == merge_profile(initial['profile'], patch)
    assert llm.calls == ['plan', 'rerank'] and not retriever.calls
    assert llm.rerank_calls[-1]['profile'] == response.json['profile']


def old_restricted_session(app, client):
    initial = client.post('/api/onboard', json=payload(remote=['remote'])).json
    sessions = app.extensions['chat_store']
    state, version = sessions.get(initial['session_id'])
    state.pop('_matching_policy_version')
    state.pop('_persona_fingerprint')
    state['_candidates'] = state['_candidates'][:1]
    state['jobs'] = state['jobs'][:1]
    state['retrieval'] = {'filtered_count': 1, 'candidate_count': 1}
    sessions.update(initial['session_id'], state, version)
    return client.get(f"/api/sessions/{initial['session_id']}").json


def test_old_restricted_pool_is_flagged_and_plain_questions_preserve_it(setup):
    _, client, retriever, llm = setup
    initial = old_restricted_session(setup[0], client)
    assert initial['candidate_pool']['refresh_required'] is True
    llm.action, llm.patch = 'answer', {}
    llm.calls.clear()
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                             'message': 'Warum passt diese Stelle?'})
    assert response.json['chat_action'] == 'answer'
    assert_recommendations_unchanged(initial, response.json)
    assert llm.calls == ['plan'] and not retriever.calls


def test_old_restricted_pool_refuses_explicit_rerank_without_partial_changes(setup):
    app, client, retriever, llm = setup
    initial = old_restricted_session(app, client)
    llm.calls.clear()
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                             'mode': 'rerank', 'advisor': {'preset': 'angela'}})
    assert response.json['chat_action'] == 'answer'
    assert 'einmal „Neue Suche“' in response.json['assistant_message']
    assert_recommendations_unchanged(initial, response.json)
    assert not retriever.calls and not llm.calls


def test_old_restricted_pool_refreshes_once_on_actual_automatic_matching_request(setup):
    app, client, retriever, llm = setup
    initial = old_restricted_session(app, client)
    llm.calls.clear()
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': initial['session_id'],
                                             'advisor': {'preset': 'angela'}})
    assert response.status_code == 200 and response.json['chat_action'] == 'search'
    assert response.json['profile'] == initial['profile']
    assert response.json['candidate_pool'] == {'available': True, 'count': 5, 'refresh_required': False}
    assert llm.calls == ['persona', 'rerank'] and len(retriever.calls) == 1
    assert llm.last_rerank_context['assessment_cache'] is None
    state = app.extensions['chat_store'].get(initial['session_id'])[0]
    assert state['_matching_policy_version'] == MATCHING_POLICY_VERSION
    llm.calls.clear()
    retriever.calls.clear()
    reranked = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'rerank'})
    assert reranked.json['chat_action'] == 'rerank'
    assert llm.calls == ['rerank'] and not retriever.calls


def test_old_pool_without_soft_constraints_needs_no_refresh(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    store = app.extensions['chat_store']
    state, version = store.get(initial['session_id'])
    state.pop('_matching_policy_version')
    store.update(initial['session_id'], state, version)
    llm.calls.clear()
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'rerank'})
    assert response.json['chat_action'] == 'rerank'
    assert response.json['candidate_pool']['refresh_required'] is False
    assert llm.calls == ['rerank'] and not retriever.calls


STREAM_HEADERS = {'Accept': 'application/x-ndjson'}


def stream_events(response):
    assert response.mimetype == 'application/x-ndjson'
    return [json.loads(line) for line in response.get_data(as_text=True).splitlines()]


def test_streamed_onboarding_emits_phase_before_models_and_commits_before_result(setup):
    app, client, retriever, llm = setup
    response = client.post('/api/onboard', json=payload(), headers=STREAM_HEADERS, buffered=False)
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['X-Accel-Buffering'] == 'no'
    iterator = iter(response.response)
    try:
        assert json.loads(next(iterator)) == {'type': 'phase', 'phase': 'search'}
        assert not llm.calls and not retriever.calls
        with app.extensions['chat_store'].connect() as db:
            assert db.execute('SELECT COUNT(*) FROM chat_sessions').fetchone()[0] == 0
        remaining = [json.loads(line) for line in iterator]
    finally:
        response.close()
    assert [event['stage'] for event in remaining[:-1]] == ['loaded', 'profiling', 'retrieval', 'ranking', 'finalizing']
    assert remaining[-1]['type'] == 'result'
    result = remaining[-1]['data']
    assert result['chat_action'] == 'search'
    assert llm.calls == ['persona', 'rerank'] and len(retriever.calls) == 1
    assert '_candidates' not in result and '_assessment_cache' not in result
    assert client.get(f"/api/sessions/{result['session_id']}").json == result


@pytest.mark.parametrize('patch,classification', [
    ({}, 'search'),
    ({'skills': ['Python', 'PyTorch']}, 'answer'),
    ({'filters': {'employment_types': ['praktikum']}}, 'rerank'),
])
def test_auto_chat_search_phase_follows_final_dispatch_but_precedes_matching(setup, patch, classification):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    before = app.extensions['chat_store'].get(initial['session_id'])
    llm.patch, llm.action = patch, classification
    llm.calls.clear()
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'auto',
                                              'message': 'Bitte aktualisiere meine Suche.'},
                           headers=STREAM_HEADERS, buffered=False)
    iterator = iter(response.response)
    try:
        assert json.loads(next(iterator)) == {'type': 'phase', 'phase': 'search'}
        assert llm.calls == ['plan'] and not retriever.calls
        assert app.extensions['chat_store'].get(initial['session_id']) == before
        remaining = [json.loads(line) for line in iterator]
    finally:
        response.close()
    assert [event['stage'] for event in remaining[:-1]] == ['loaded', 'profiling', 'retrieval', 'ranking', 'finalizing']
    assert remaining[-1]['type'] == 'result'
    assert remaining[-1]['data']['chat_action'] == 'search'
    assert llm.calls == (['plan', 'persona', 'rerank'] if patch else ['plan', 'rerank'])
    assert len(retriever.calls) == 1
    assert client.get(f"/api/sessions/{initial['session_id']}").json == remaining[-1]['data']


@pytest.mark.parametrize('mode,classification,patch,expected_action', [
    ('auto', 'answer', {}, 'answer'),
    ('auto', 'rerank', {'preferences': ['Mentoring']}, 'rerank'),
    ('rerank', 'rerank', {'filters': {'remote': ['remote']}}, 'rerank'),
    ('rerank', 'search', {}, 'answer'),
    ('rerank', 'search', {'filters': {'employment_types': ['praktikum']}}, 'answer'),
])
def test_streamed_answers_reranks_and_refused_reranks_never_signal_search(setup, mode, classification, patch, expected_action):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    llm.patch, llm.action = patch, classification
    llm.calls.clear()
    retriever.calls.clear()
    events = stream_events(client.post('/api/chat', json={'session_id': initial['session_id'],
                                                         'message': 'Bitte prüfe meine Auswahl.', 'mode': mode},
                                       headers=STREAM_HEADERS))
    assert [event['type'] for event in events] == ['result']
    assert events[0]['data']['chat_action'] == expected_action
    assert not retriever.calls and 'persona' not in llm.calls
    if expected_action == 'answer':
        assert_recommendations_unchanged(initial, events[0]['data'])
    assert client.get(f"/api/sessions/{initial['session_id']}").json == events[0]['data']


def test_streamed_legacy_migration_signals_search_only_after_refusal_checks(setup):
    app, client, retriever, llm = setup
    initial = old_restricted_session(app, client)
    llm.calls.clear()
    retriever.calls.clear()
    refused = stream_events(client.post('/api/chat', json={'session_id': initial['session_id'],
                                                          'mode': 'rerank', 'advisor': {'preset': 'angela'}},
                                        headers=STREAM_HEADERS))
    assert [event['type'] for event in refused] == ['result']
    assert refused[0]['data']['chat_action'] == 'answer'
    assert not llm.calls and not retriever.calls
    refreshed = stream_events(client.post('/api/chat', json={'session_id': initial['session_id'],
                                                            'advisor': {'preset': 'angela'}},
                                          headers=STREAM_HEADERS))
    assert [event['type'] for event in refreshed] == ['phase'] + ['search_progress'] * 5 + ['result']
    assert refreshed[0]['phase'] == 'search'
    assert refreshed[-1]['data']['candidate_pool']['refresh_required'] is False
    assert llm.calls == ['persona', 'rerank'] and len(retriever.calls) == 1


@pytest.mark.parametrize('failure', ['llm', 'embedding', 'unexpected'])
def test_errors_after_search_phase_are_terminal_safe_events_without_partial_session(setup, failure):
    app, client, retriever, llm = setup

    def fail(*args, **kwargs):
        if failure == 'embedding':
            raise EmbeddingUnavailable('PRIVATE_BACKEND_SENTINEL')
        if failure == 'unexpected':
            raise RuntimeError('PRIVATE_BACKEND_SENTINEL')
        raise LLMUnavailable('KI vorübergehend nicht verfügbar.')

    if failure == 'embedding':
        retriever.search = fail
    else:
        llm.generate_persona = fail
    response = client.post('/api/onboard', json=payload(), headers=STREAM_HEADERS)
    events = stream_events(response)
    assert response.status_code == 200  # Stream headers precede downstream failure.
    assert events[-1]['type'] == 'error'
    expected_stages = ['loaded', 'profiling', 'retrieval'] if failure == 'embedding' else ['loaded', 'profiling']
    assert [event['stage'] for event in events[1:-1]] == expected_stages
    assert events[0] == {'type': 'phase', 'phase': 'search'}
    assert events[-1]['status'] == (500 if failure == 'unexpected' else 503)
    assert isinstance(events[-1]['error']['message'], str)
    assert 'PRIVATE_BACKEND_SENTINEL' not in response.get_data(as_text=True)
    with app.extensions['chat_store'].connect() as db:
        assert db.execute('SELECT COUNT(*) FROM chat_sessions').fetchone()[0] == 0


def test_streamed_rerank_failure_never_emits_search_and_preserves_existing_session(setup):
    app, client, _, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    before = app.extensions['chat_store'].get(initial['session_id'])

    def fail(*args, **kwargs):
        raise LLMUnavailable('Neubewertung nicht verfügbar.')

    llm.rerank = fail
    events = stream_events(client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'rerank'},
                                       headers=STREAM_HEADERS))
    assert [event['type'] for event in events] == ['error']
    assert events[0]['status'] == 503
    assert app.extensions['chat_store'].get(initial['session_id']) == before


def test_streaming_preserves_real_optimistic_lock_conflict_after_search_phase(setup):
    app, client, _, _ = setup
    initial = client.post('/api/onboard', json=payload()).json
    sessions = app.extensions['chat_store']
    state, version = sessions.get(initial['session_id'])
    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'search'},
                           headers=STREAM_HEADERS, buffered=False)
    iterator = iter(response.response)
    try:
        assert json.loads(next(iterator)) == {'type': 'phase', 'phase': 'search'}
        concurrent = deepcopy(state)
        concurrent['messages'].append({'role': 'assistant', 'content': 'Parallel gespeicherte Antwort.',
                                       'advisor_name': 'DIANA-KI'})
        sessions.update(initial['session_id'], concurrent, version)
        remaining = [json.loads(line) for line in iterator]
    finally:
        response.close()
    assert [event['type'] for event in remaining] == ['search_progress'] * 5 + ['error']
    assert remaining[-1]['status'] == 409
    assert remaining[-1]['error']['code'] == 'session_conflict'
    assert sessions.get(initial['session_id']) == (concurrent, version + 1)


def test_presearch_blockers_and_empty_results_do_not_signal_an_expensive_search(setup):
    app, client, retriever, llm = setup
    empty = stream_events(client.post('/api/onboard', json=payload(employment_types=['ausbildung']),
                                      headers=STREAM_HEADERS))
    assert [event['type'] for event in empty] == ['result']
    assert empty[0]['data']['jobs'] == []
    app.config['REQUIRE_COMPLETE_INDEX'] = True
    blocked = stream_events(client.post('/api/onboard', json=payload(), headers=STREAM_HEADERS))
    assert [event['type'] for event in blocked] == ['error']
    assert blocked[0]['status'] == 503
    assert not llm.calls and not retriever.calls


@pytest.mark.parametrize('endpoint,body,status', [
    ('/api/onboard', {'profile': {}}, 400),
    ('/api/chat', {'session_id': 'x' * 43, 'message': 'Frage'}, 404),
])
def test_preflight_errors_follow_ndjson_protocol_with_http_status(setup, endpoint, body, status):
    _, client, retriever, llm = setup
    response = client.post(endpoint, json=body, headers=STREAM_HEADERS)
    events = stream_events(response)
    assert response.status_code == status
    assert [event['type'] for event in events] == ['error']
    assert events[0]['status'] == status and events[0]['error']['message']
    assert not llm.calls and not retriever.calls


def test_streamed_invalid_content_type_malformed_json_and_oversized_input_are_errors(setup):
    _, client, retriever, llm = setup
    for data, content_type, status in [('x', 'text/plain', 415), ('{', 'application/json', 400),
                                        ('x' * 140000, 'application/json', 413)]:
        response = client.post('/api/onboard', data=data, content_type=content_type, headers=STREAM_HEADERS)
        events = stream_events(response)
        assert response.status_code == status
        assert [event['type'] for event in events] == ['error']
        assert events[0]['status'] == status
    assert not llm.calls and not retriever.calls


def test_planner_failure_is_reported_before_any_search_phase(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    before = app.extensions['chat_store'].get(initial['session_id'])
    retriever.calls.clear()

    def fail(*args, **kwargs):
        raise LLMUnavailable('Aktionsplanung nicht verfügbar.')

    llm.plan_chat = fail
    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'message': 'Suche erneut.'},
                           headers=STREAM_HEADERS)
    events = stream_events(response)
    assert response.status_code == 503
    assert [event['type'] for event in events] == ['error']
    assert events[0]['status'] == 503
    assert not retriever.calls
    assert app.extensions['chat_store'].get(initial['session_id']) == before


@pytest.mark.parametrize('accept', [None, 'application/json', '*/*', 'application/x-ndjson;q=0'])
def test_json_clients_keep_existing_status_and_payload_without_explicit_stream_opt_in(setup, accept):
    _, client, _, _ = setup
    response = client.post('/api/onboard', json=payload(), headers={'Accept': accept} if accept else {})
    assert response.status_code == 201
    assert response.is_json
    assert response.json['session_id'] and response.json['chat_action'] == 'search'
    assert 'type' not in response.json


def test_stream_opt_in_does_not_change_other_endpoints(setup):
    _, client, _, _ = setup
    response = client.post('/api/search', json=payload(), headers=STREAM_HEADERS)
    assert response.status_code == 200 and response.is_json
    assert 'type' not in response.json
    assert client.get('/api/health', headers=STREAM_HEADERS).is_json


def test_closing_stream_after_phase_does_not_start_models_or_create_session(setup):
    app, client, retriever, llm = setup
    response = client.post('/api/onboard', json=payload(), headers=STREAM_HEADERS, buffered=False)
    assert json.loads(next(iter(response.response))) == {'type': 'phase', 'phase': 'search'}
    response.close()
    assert not llm.calls and not retriever.calls
    with app.extensions['chat_store'].connect() as db:
        assert db.execute('SELECT COUNT(*) FROM chat_sessions').fetchone()[0] == 0


def install_chat_stream(llm, *, fail=False):
    def steps(*args, **kwargs):
        assert kwargs.pop('stream') is True
        decision = llm.plan_chat(*args, **kwargs)
        for text in ['Python', decision['assistant_message']]:
            yield {'type': 'assistant_preview', 'data': {**decision, 'assistant_message': text}}
        if fail:
            raise LLMUnavailable('Die Verbindung zur KI wurde unterbrochen.')
        return decision
    llm.plan_chat_steps = steps


def test_chat_text_arrives_before_commit_and_final_message_is_saved_once(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    before = app.extensions['chat_store'].get(initial['session_id'])
    llm.patch, llm.action = {}, 'answer'
    install_chat_stream(llm)
    retriever.calls.clear()
    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'message': 'Warum?'},
                           headers=STREAM_HEADERS, buffered=False)
    iterator = iter(response.response)
    try:
        assert json.loads(next(iterator)) == {'type': 'assistant_text', 'text': 'Python'}
        assert app.extensions['chat_store'].get(initial['session_id']) == before
        remaining = [json.loads(event) for event in iterator]
    finally:
        response.close()
    assert [event['type'] for event in remaining] == ['assistant_text', 'result']
    final = remaining[-1]['data']
    assert len(final['messages']) == len(initial['messages']) + 2
    assert final['messages'][-1]['content'] == llm.answer
    assert_recommendations_unchanged(initial, final)
    assert not retriever.calls


@pytest.mark.parametrize('failure', ['disconnect', 'upstream', 'conflict'])
def test_partial_answer_never_commits_on_failure(setup, failure):
    app, client, _, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    store = app.extensions['chat_store']
    before = store.get(initial['session_id'])
    llm.patch, llm.action = {}, 'answer'
    install_chat_stream(llm, fail=failure == 'upstream')
    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'message': 'Warum?'},
                           headers=STREAM_HEADERS, buffered=False)
    iterator = iter(response.response)
    assert json.loads(next(iterator))['type'] == 'assistant_text'
    if failure == 'disconnect':
        response.close()
        assert store.get(initial['session_id']) == before
        return
    if failure == 'conflict':
        state, version = before
        store.update(initial['session_id'], {**state, 'assistant_message': 'Parallel gespeichert.'}, version)
        before = store.get(initial['session_id'])
    events = [json.loads(event) for event in iterator]
    response.close()
    assert events[-1]['type'] == 'error'
    assert events[-1]['status'] == (409 if failure == 'conflict' else 503)
    assert not any(event['type'] == 'result' for event in events)
    assert store.get(initial['session_id']) == before


@pytest.mark.parametrize('action,patch,mode', [
    ('rerank', {}, 'auto'), ('search', {}, 'auto'),
    ('answer', {'skills': ['Rust']}, 'auto'),
    ('answer', {'preferences': ['Mentoring']}, 'auto'),
    ('answer', {}, 'rerank'), ('answer', {}, 'search'),
])
def test_chat_dispatch_does_not_stream_a_planner_answer_that_will_be_replaced(setup, action, patch, mode):
    _, client, _, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    llm.patch, llm.action = patch, action
    install_chat_stream(llm)
    events = stream_events(client.post('/api/chat', json={'session_id': initial['session_id'],
                            'message': 'Bitte anpassen.', 'mode': mode}, headers=STREAM_HEADERS))
    assert not any(event['type'] == 'assistant_text' for event in events)
    assert events[-1]['type'] == 'result'
    assert events[-1]['data']['chat_action'] in {'search', 'rerank'}


def test_rerank_text_streams_without_search_popup_or_candidate_changes(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload()).json
    before = app.extensions['chat_store'].get(initial['session_id'])
    retriever.calls.clear()
    def steps(*args, **kwargs):
        assert kwargs.pop('stream') is True
        result = llm.rerank(*args, **kwargs)
        yield {'type': 'assistant_preview', 'data': {**result, 'assistant_message': 'Diese Stellen'}}
        return result
    llm.rerank_steps = steps
    response = client.post('/api/chat', json={'session_id': initial['session_id'], 'mode': 'rerank'},
                           headers=STREAM_HEADERS, buffered=False)
    iterator = iter(response.response)
    assert json.loads(next(iterator)) == {'type': 'assistant_text', 'text': 'Diese Stellen'}
    assert app.extensions['chat_store'].get(initial['session_id']) == before
    events = [json.loads(event) for event in iterator]
    response.close()
    assert [event['type'] for event in events] == ['result']
    assert events[-1]['data']['candidate_pool'] == initial['candidate_pool']
    assert not retriever.calls


@pytest.mark.parametrize('scores,expected', [
    ([95, 85, 70], ['3 Stellen gefunden und bewertet', 'links in der Ergebnisübersicht']),
    ([80, 70, 69], ['3 Stellen gefunden und bewertet', 'Links siehst du 2;', 'übrigen']),
    ([70, 69, 35], ['3 Stellen gefunden und bewertet', 'Links siehst du 1;', 'übrigen']),
    ([69, 40, 1], ['3 Stellen gefunden und bewertet', 'keine 70 Punkte', 'trotzdem einblenden']),
    ([70], ['Eine Stelle gefunden und bewertet', 'links in der Ergebnisübersicht']),
    ([69], ['Eine Stelle gefunden und bewertet', 'trotzdem einblenden']),
    ([], ['keine Stellen zur gewählten Stellenart', 'Suche gemeinsam anpassen']),
])
def test_welcome_counts_actual_cards_and_respects_hidden_results(scores, expected):
    from app import welcome_message
    explanation = 'Python ist belegt; Betreuung bleibt noch zu klären.'
    result = {'jobs': [{'match': {'score': score}} for score in scores],
              'assistant_message': explanation}
    before = deepcopy(result)
    message = welcome_message(result)
    assert message.startswith('Hallo! ')
    assert 'Rückfragen' in message
    assert all(fragment in message for fragment in expected)
    assert message.split('\n\n')[1] == explanation
    assert len(message.split('\n\n')[0].split()) <= 25
    assert result == before


def test_welcome_is_saved_once_at_onboarding_and_followup_keeps_normal_answer(setup):
    app, client, retriever, llm = setup
    initial = client.post('/api/onboard', json=payload(), headers=STREAM_HEADERS)
    data = stream_events(initial)[-1]['data']
    greeting = data['assistant_message']
    assert greeting.startswith('Hallo! ')
    assert f"{len(data['jobs'])} Stellen gefunden und bewertet" in greeting
    assert 'links' in greeting and 'Rückfragen' in greeting
    assert data['messages'][0]['content'] == greeting
    assert client.get(f"/api/sessions/{data['session_id']}").json['messages'][0]['content'] == greeting
    assert llm.calls == ['persona', 'rerank']
    retriever.calls.clear()
    llm.patch, llm.action = {}, 'answer'
    reply = client.post('/api/chat', json={'session_id': data['session_id'], 'message': 'Warum passt die erste Stelle?'}).json
    assert reply['assistant_message'] == llm.answer
    assert reply['messages'][0]['content'] == greeting
    assert not retriever.calls


def test_neutral_public_cards_and_greeting_have_no_assessment_without_changing_private_state():
    from app import public_state, welcome_message
    state = {'advisor': {'preset': 'neutral'}, 'jobs': [
        {'id': 'low', 'title': 'Python', 'match': {'score': 30, 'reasons': ['Bewertung']}, 'retrieval': {'rrf_score': .02}},
        {'id': 'high', 'title': 'SQL', 'match': {'score': 90, 'reasons': ['Bewertung']}}],
        'assistant_message': 'Nicht für die neutrale Suchansprache bestimmt.'}
    before = deepcopy(state)
    public = public_state(state)
    assert public['jobs'] == [{'id': 'low', 'title': 'Python'}, {'id': 'high', 'title': 'SQL'}]
    greeting = welcome_message(state)
    assert greeting == 'Hallo ich bin dein KI Assistent'
    assert state['assistant_message'] not in greeting
    assert all(word not in greeting for word in ['Score', 'Punkte', 'Bewertung'])
    assert state == before


def test_progress_counts_and_phases_follow_actual_work(setup):
    app, client, retriever, llm = setup
    response = client.post('/api/onboard', json=payload(), headers=STREAM_HEADERS, buffered=False)
    iterator = iter(response.response)
    try:
        assert json.loads(next(iterator))['type'] == 'phase'
        loaded = json.loads(next(iterator))
        assert loaded['stage'] == 'loaded' and loaded['job_count'] > 0
        assert json.loads(next(iterator))['stage'] == 'profiling'
        assert llm.calls == []
        assert json.loads(next(iterator))['stage'] == 'retrieval'
        assert llm.calls == ['persona'] and retriever.calls == []
        ranking = json.loads(next(iterator))
        assert ranking['stage'] == 'ranking'
        assert ranking['candidate_count'] == min(loaded['job_count'], 20)
        assert len(retriever.calls) == 1 and llm.calls == ['persona']
        assert json.loads(next(iterator))['stage'] == 'finalizing'
        assert llm.calls == ['persona', 'rerank']
        result = json.loads(next(iterator))
        assert result['type'] == 'result'
        assert result['data']['retrieval']['candidate_count'] == ranking['candidate_count']
    finally:
        response.close()
