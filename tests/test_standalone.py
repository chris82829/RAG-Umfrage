"""Fixed test arms must never contaminate assignments or survey responses."""
import json
import sqlite3

import pytest

from app import create_app
from test_app import FakeLLM, FakeRetriever, payload


@pytest.fixture
def standalone(tmp_path):
    settings = tmp_path / 'privacy.json'
    settings.write_text(json.dumps(dict(approved=False, controller='Test controller', retention='Test retention',
                                       openai_processing='Test processing', technical_processing='Test transport')))
    llm = FakeLLM()
    app = create_app({'TESTING': True, 'DATABASE_PATH': str(tmp_path / 'data.sqlite3'),
                      'OPENAI_API_KEY': '', 'SEED_DUMMY_DATA': True, 'REQUIRE_COMPLETE_INDEX': False,
                      'PRIVACY_REQUIRED': True, 'PERSIST_CHAT_SESSIONS': False,
                      'PRIVACY_SETTINGS_PATH': settings}, retriever=FakeRetriever(), llm=llm)
    return app, app.test_client(), llm


def grant_test(client, arm):
    token = arm.lower() * 64
    headers = {'X-Diana-Test': arm, 'X-Diana-Consent': token}
    notice = client.get('/api/privacy', headers=headers).json['notice']
    response = client.post('/api/privacy/consent', headers=headers,
        json=dict(token=token, version=notice['version'], accepted=True, purpose=f'test_{arm.lower()}'))
    assert response.status_code == 200
    return headers


def test_direct_pages_are_served_and_independent_of_study_release(standalone):
    _, client, _ = standalone
    assert client.get('/api/privacy').json['notice']['ready'] is False
    for arm in ('A', 'B'):
        for suffix in ('', '/', '/datenschutz'):
            assert client.get(f'/test/{arm.lower()}{suffix}').status_code == 200
        headers = grant_test(client, arm)
        status = client.get('/api/privacy', headers=headers).json
        assert status['active'] is True and status['notice']['purpose'] == f'test_{arm.lower()}'
        assert 'keine Umfrageantwort' in status['notice']['consent_text']


def test_fixed_arms_isolate_sessions_and_never_create_study_data(standalone):
    app, client, llm = standalone
    a, b = grant_test(client, 'A'), grant_test(client, 'B')
    configured = {'mode':'custom','name':'Meine Beratung','traits':['analytisch'],'focus':'innovation'}
    first = client.post('/api/onboard', headers=a, json={**payload(), 'advisor':configured})
    assert first.status_code == 201
    assert first.json['advisor']['preset'] == 'neutral'
    second = client.post('/api/onboard', headers=b, json={**payload(), 'advisor':configured})
    assert second.status_code == 201
    assert second.json['advisor']['name'] == 'Meine Beratung'
    assert second.json['advisor_mlds']['personality'] == second.json['advisor']
    stored = app.extensions['chat_store'].get(second.json['session_id'])[0]
    assert stored['advisor_mlds']['format'] == 'DIANA-Personality-MLDS'
    sid = first.json['session_id']
    assert client.get('/api/sessions/'+sid, headers=b).status_code == 428
    assert client.get('/api/sessions/'+sid, headers={'X-Diana-Consent':a['X-Diana-Consent']}).status_code == 428
    assert client.get('/api/sessions/'+sid, headers={**a,'X-Diana-Test':'B'}).status_code == 428
    llm.action, llm.patch = 'answer', {}
    answer = client.post('/api/chat', headers=a, json={'session_id':sid,'message':'Warum passt Stelle eins?','advisor':configured})
    assert answer.status_code == 200 and answer.json['advisor']['preset'] == 'neutral'
    assert len(answer.json['messages']) == 3
    assert answer.json['advisor_mlds']['personality'] == answer.json['advisor']
    for headers in (a,b):
        for method,path in [('post','/api/study-assignment'),('post','/api/survey-responses'),('put','/api/survey-drafts'),('get','/api/survey-drafts/'+'c'*32)]:
            assert getattr(client,method)(path,headers=headers).status_code == 428
        assert client.post('/api/study-assignment',headers={'X-Diana-Consent':headers['X-Diana-Consent']}).status_code == 428
    with sqlite3.connect(app.config['DATABASE_PATH']) as db:
        for table in ('survey_responses','survey_drafts','study_assignments','study_runs','survey_response_metadata'):
            assert db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 0
        assert db.execute('SELECT purpose FROM privacy_consents ORDER BY purpose').fetchall() == [('test_a',),('test_b',)]


def test_test_consent_cannot_be_reused_across_purposes_and_withdrawal_is_scoped(standalone):
    _, client, _ = standalone
    a, b = grant_test(client,'A'), grant_test(client,'B')
    b_notice = client.get('/api/privacy',headers=b).json['notice']
    assert client.post('/api/privacy/consent',headers={'X-Diana-Test':'B'},json={
        'token':a['X-Diana-Consent'],'purpose':'test_b','accepted':True,'version':b_notice['version']}).status_code == 428
    assert client.post('/api/privacy/consent',headers={'X-Diana-Test':'B'},json={
        'token':'c'*64,'purpose':'study','accepted':True,'version':b_notice['version']}).status_code == 428
    assert client.delete('/api/privacy/consent',headers=a).status_code == 200
    assert client.post('/api/onboard',headers=a,json=payload()).status_code == 428
    assert client.get('/api/privacy',headers=b).json['active'] is True


def test_mlds_catalog_loads_reviewed_templates_without_model_calls(standalone):
    _, client, llm = standalone
    catalog = client.get('/api/persona-templates').json
    assert catalog['default'] == 'career'
    assert set(catalog['templates']) == {'career', 'expert'}
    for template in catalog['templates'].values():
        assert template['mlds']['personality'] == template['advisor']
        assert template['instructions'] == template['advisor']['description']
    assert llm.calls == []


def test_ending_study_keeps_independent_test_session_and_consent(standalone):
    app, client, _ = standalone
    headers = grant_test(client, 'B')
    sid = client.post('/api/onboard',headers=headers,json=payload()).json['session_id']
    result = app.test_cli_runner().invoke(args=['privacy-end-study', '--confirm'])
    assert result.exit_code == 0
    assert client.get('/api/privacy').json['study']['closed'] is True
    assert client.get('/api/privacy',headers=headers).json['active'] is True
    assert client.get('/api/sessions/'+sid,headers=headers).status_code == 200
