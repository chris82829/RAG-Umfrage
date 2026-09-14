"""New randomized ABC conditions are enforced independently of historical AB."""
from concurrent.futures import ThreadPoolExecutor

import pytest

from advisor import AdvisorConfig
from persona_mlds import load_templates
from privacy import token_hash
from study_assignment import EXPERIMENT_ID, AB_EXPERIMENT_ID, LEGACY_EXPERIMENT_ID
from test_app import payload
from test_privacy import grant
from test_study_assignment import experiment, assign
from test_standalone import standalone, grant_test


def new_assignment(app, monkeypatch, arm, token='a'*64):
    return assign(app, monkeypatch, arm, token=token, experiment_id=EXPERIMENT_ID)


@pytest.mark.parametrize('arm,policy', [('A','standard'),('B','templates'),('C','configurable')])
def test_fresh_assignment_has_three_equal_candidates_and_stays_stable(experiment, monkeypatch, arm, policy):
    app, _ = experiment
    client = app.test_client()
    headers, _ = grant(client)
    def choose(values):
        assert values == ('A', 'B', 'C')
        return arm
    monkeypatch.setattr('study_assignment.secrets.choice', choose)
    first = client.post('/api/study-assignment', headers=headers).json
    assert first['experiment_id'] == EXPERIMENT_ID
    assert first['arm'] == arm and first['personality_policy'] == policy
    assert first['questionnaire_version'] == 'diana-v10'
    monkeypatch.setattr('study_assignment.secrets.choice', lambda _: pytest.fail('Must not rerandomize'))
    with ThreadPoolExecutor(max_workers=6) as pool:
        repeated = list(pool.map(lambda _: app.extensions['study_assignments'].assign(headers['X-Diana-Consent']), range(15)))
    assert all(value == first for value in repeated)
    with app.extensions['survey_store'].connect() as db:
        assert db.execute('SELECT count(*) FROM study_assignments').fetchone()[0] == 1


@pytest.mark.parametrize('experiment_id,original_arm,expected_arm,version', [
    (AB_EXPERIMENT_ID,'B','B','diana-v7'), (LEGACY_EXPERIMENT_ID,'C','B','diana-v6')])
def test_existing_editable_b_retains_original_experiment_and_configuration(experiment, monkeypatch, experiment_id, original_arm, expected_arm, version):
    app, _ = experiment
    client, headers, _ = new_assignment(app, monkeypatch, 'B')
    with app.extensions['survey_store'].connect() as db:
        db.execute('UPDATE study_assignments SET experiment_id=?,arm=? WHERE token_hash=?', (experiment_id,original_arm,token_hash(headers['X-Diana-Consent'])))
        before = dict(db.execute('SELECT * FROM study_assignments').fetchone())
    assigned = client.post('/api/study-assignment', headers=headers).json
    assert assigned['arm'] == expected_arm and assigned['personality_policy'] == 'configurable'
    assert assigned['questionnaire_version'] == version
    custom = {'mode':'custom','name':'Meine Beratung','traits':['analytisch'],'focus':'innovation'}
    response = client.post('/api/onboard', headers=headers, json=payload() | {'advisor':custom,'advisor_selection':{'source':'custom','template_id':None}})
    assert response.status_code == 201
    assert response.json['advisor']['name'] == custom['name']
    with app.extensions['survey_store'].connect() as db:
        assert dict(db.execute('SELECT * FROM study_assignments').fetchone()) == before


@pytest.mark.parametrize('route', ['/api/search','/api/onboard'])
def test_new_b_accepts_only_exact_templates_and_never_calls_model_for_edits(experiment, monkeypatch, route):
    app, model = experiment
    client, headers, _ = new_assignment(app, monkeypatch, 'B')
    templates = load_templates()
    for key in ('career','expert'):
        advisor = templates[key]['advisor']
        first = client.post(route, headers=headers, json=payload() | {'advisor':advisor})
        assert first.status_code in (200,201)
        assert first.json['advisor'] == advisor
        assert first.json['advisor_selection'] == {'source':'template','template_id':key}
        for patch, selection in [
            ({'name':'Andere Person'}, {'source':'template','template_id':key}),
            ({'description':'Andere Anleitung'}, {'source':'template','template_id':key}),
            ({}, {'source':'custom','template_id':None}),
            ({}, {'source':'template','template_id':'expert' if key=='career' else 'career'}),
        ]:
            calls = list(model.calls)
            response = client.post(route, headers=headers, json=payload() | {'advisor':advisor | patch, 'advisor_selection':selection})
            assert response.status_code == 400
            assert model.calls == calls
    default = client.post(route, headers=headers, json=payload())
    assert default.json['advisor'] == templates['career']['advisor']
    assert default.json['advisor_selection']['template_id'] == 'career'


def test_b_chat_rejects_edit_before_llm_but_allows_switch_between_templates(experiment, monkeypatch):
    app, model = experiment
    client, headers, _ = new_assignment(app, monkeypatch, 'B')
    initial = client.post('/api/onboard', headers=headers, json=payload()).json
    sid = initial['session_id']
    expert = load_templates()['expert']['advisor']
    calls = list(model.calls)
    rejected = client.post('/api/chat', headers=headers, json={'session_id':sid,'message':'Bitte prüfen','advisor':expert | {'focus':'innovation'}})
    assert rejected.status_code == 400 and model.calls == calls
    result = client.post('/api/chat', headers=headers, json={'session_id':sid,'advisor':expert,'mode':'rerank'})
    assert result.status_code == 200 and result.json['advisor'] == expert
    assert result.json['advisor_selection'] == {'source':'template','template_id':'expert'}
    restored = client.get('/api/sessions/'+sid, headers=headers)
    assert restored.status_code == 200
    # A session created by the former direct B page must not inherit new B.
    sessions = app.extensions['chat_store']
    old, version = sessions.get(sid)
    old.pop('_personality_policy')
    sessions.update(sid, old, version)
    assert client.get('/api/sessions/'+sid, headers=headers).status_code == 404
    assert client.post('/api/chat', headers=headers,json={'session_id':sid,'message':'Hallo'}).status_code == 404


def test_c_keeps_custom_and_template_selection_provenance(experiment, monkeypatch):
    app, _ = experiment
    client, headers, _ = new_assignment(app, monkeypatch, 'C')
    career = load_templates()['career']['advisor']
    response = client.post('/api/onboard', headers=headers, json=payload() | {'advisor':career,'advisor_selection':{'source':'custom','template_id':None}})
    assert response.status_code == 201
    assert response.json['advisor_selection']['source'] == 'custom'
    result = client.post('/api/chat',headers=headers,json={'session_id':response.json['session_id'],'advisor':career,'advisor_selection':{'source':'template','template_id':'career'},'mode':'rerank'})
    assert result.status_code == 200 and result.json['advisor_selection']['source'] == 'template'
    with app.extensions['survey_store'].connect() as db:
        import json
        usage = json.loads(db.execute('SELECT metadata_json FROM study_personality_usage').fetchone()[0])
        assert usage['initial_source'] == 'custom' and usage['last_source'] == 'template'
        assert usage['selection_change_count'] == 1


def test_questionnaire_version_cannot_mix_new_and_historical_assignments(experiment, monkeypatch):
    app, _ = experiment
    _, headers, _ = new_assignment(app, monkeypatch, 'C')
    assignments = app.extensions['study_assignments']
    token = headers['X-Diana-Consent']
    assignments.validate_answers(token, 'diana-v10', {'study_arm':'C'})
    for version in ('diana-v3','diana-v6','diana-v7','diana-v8','diana-v9'):
        with pytest.raises(ValueError): assignments.validate_answers(token, version, {'study_arm':'C'})
    with pytest.raises(ValueError): assignments.validate_answers(token,'diana-v10',{'study_arm':'B'})


def test_c_test_page_isolated_from_b_and_study_data(standalone):
    app, client, model = standalone
    b, c = grant_test(client,'B'), grant_test(client,'C')
    assert client.get('/test/c').status_code == 200
    config = AdvisorConfig(mode='custom',name='Eigenes',traits=['kritisch']).model_dump()
    assert client.post('/api/onboard',headers=b,json=payload()|{'advisor':config}).status_code == 400
    response = client.post('/api/onboard',headers=c,json=payload()|{'advisor':config,'advisor_selection':{'source':'custom','template_id':None}})
    assert response.status_code == 201
    assert client.get('/api/sessions/'+response.json['session_id'],headers=b).status_code == 428
    with app.extensions['survey_store'].connect() as db:
        for table in ('study_assignments','study_runs','study_personality_usage','survey_response_metadata','survey_responses','survey_drafts'):
            assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == 0
