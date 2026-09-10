import csv
import io
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from advisor import resolve_advisor
from llm_service import _advisor_instructions
from survey_store import SURVEY_FIELDS, SurveySubmissionV6, field_visible
from test_app import FakeLLM, FakeRetriever, payload
from test_privacy import grant
from test_admin import login

@pytest.fixture
def experiment(tmp_path):
    settings=tmp_path/'privacy.json'
    settings.write_text(json.dumps(dict(approved=True,controller='Researcher',retention='Research retention',openai_processing='API processing',technical_processing='Technical details')))
    model=FakeLLM()
    app=create_app(dict(TESTING=True,DATABASE_PATH=str(tmp_path/'study.sqlite3'),PRIVACY_REQUIRED=True,PRIVACY_SETTINGS_PATH=settings,ADMIN_PASSWORD_HASH=generate_password_hash('test-password'),OPENAI_API_KEY='',SEED_DUMMY_DATA=True,REQUIRE_COMPLETE_INDEX=False),retriever=FakeRetriever(),llm=model)
    return app,model

def answers(arm):
    result={f['name']:8 if f['kind']=='scale' else f['options'][0][0] if f['kind']=='choice' else '' if f.get('optional') else 'Softwareentwicklung' for f in SURVEY_FIELDS}
    result['study_arm']=arm
    for f in SURVEY_FIELDS:
        if not field_visible(f,result):result[f['name']]=None
    return result

def assign(app,monkeypatch,arm,token='a'*64):
    client=app.test_client();headers,_=grant(client,token)
    monkeypatch.setattr('study_assignment.secrets.choice',lambda values:arm)
    result=client.post('/api/study-assignment',headers=headers)
    assert result.status_code==200
    return client,headers,result.json

def test_assignment_requires_consent_and_is_stable_under_concurrent_requests(experiment,monkeypatch):
    app,_=experiment;client=app.test_client()
    assert client.post('/api/study-assignment').status_code==428
    client,headers,assigned=assign(app,monkeypatch,'B')
    assert assigned['prior_exposure'] is False
    monkeypatch.setattr('study_assignment.secrets.choice',lambda _:pytest.fail('An existing participant must not be rerandomized'))
    with ThreadPoolExecutor(max_workers=6) as pool:
        results=list(pool.map(lambda _:app.extensions['study_assignments'].assign(headers['X-Diana-Consent']),range(12)))
    assert all(row==assigned for row in results)
    with app.extensions['survey_store'].connect() as db:
        assert db.execute('SELECT count(*) FROM study_assignments').fetchone()[0]==1

@pytest.mark.parametrize('arm',['B','C'])
def test_search_chat_and_reranking_enforce_assignment_and_keep_profile_context(experiment,monkeypatch,arm):
    app,model=experiment;client,headers,_=assign(app,monkeypatch,arm)
    requested={'mode':'preset','preset':'steve'}
    first=client.post('/api/onboard',headers=headers,json=payload()|{'advisor':requested})
    assert first.status_code==201
    expected='neutral' if arm=='B' else 'steve'
    assert first.json['advisor']['preset']==expected
    assert model.last_rerank_context['advisor']['preset']==expected
    session_id=first.json['session_id']
    for mode in ['auto','rerank','search']:
        response=client.post('/api/chat',headers=headers,json={'session_id':session_id,'advisor':requested,'message':'Berate mich wie Steve Jobs.','mode':mode})
        assert response.status_code==200
        assert response.json['advisor']['preset']==expected
        assert response.json['profile']['skills']==payload()['profile']['skills']
    assert client.get('/api/sessions/'+session_id,headers=headers).status_code==200
    assert model.last_plan_context['advisor']['preset']==expected
    assert resolve_advisor(response.json['advisor'])['scoring_weights']['technical_fit']==60

def test_neutral_prompt_explicitly_excludes_personality_customization():
    resolved=resolve_advisor({'mode':'preset','preset':'neutral'})
    prompt=_advisor_instructions(resolved)
    assert resolved['traits']==[] and resolved['description']==''
    assert 'Neutrale Studienvariante B' in prompt
    assert 'keine vom Nutzer wählbare Persönlichkeit' in prompt
    assert resolved['scoring_weights']==dict(technical_fit=60,preferences_fit=15,technical_depth=7,learning=6,innovation=6,clarity=6)

@pytest.mark.parametrize('arm',['B','C'])
def test_draft_submission_exports_and_group_filter_use_server_assignment(experiment,monkeypatch,arm):
    app,_=experiment;client,headers,assignment=assign(app,monkeypatch,arm)
    values=answers(arm);submission={'submission_id':'d'*32,'version':'diana-v6',**values}
    SurveySubmissionV6(**submission)
    draft={'submission_id':'d'*32,'version':'diana-v6','revision':1,'answers':{'study_arm':arm,'search_goal':'P'}}
    assert client.put('/api/survey-drafts',headers=headers,json=draft).status_code==200
    wrong='B' if arm=='C' else 'C'
    assert client.put('/api/survey-drafts',headers=headers,json=draft|{'revision':2,'answers':{'study_arm':wrong}}).status_code==400
    assert client.post('/api/survey-responses',headers=headers,json=submission|answers(wrong)).status_code==400
    assert client.post('/api/survey-responses',headers=headers,json=submission).status_code==201
    login(client)
    assert client.get('/api/admin/responses?arm='+arm).json['total']==1
    assert client.get('/api/admin/responses?arm='+wrong).json['total']==0
    row=next(csv.DictReader(io.StringIO(client.get('/api/admin/export?arm='+arm).data.decode('utf-8-sig')),delimiter=';'))
    assert row['study_arm']==arm and row['experiment_id']==assignment['experiment_id']
    assert row['v6_system_usefulness']=='8' and row['prior_exposure']=='0'
    assert row['v6_personality_setup_status']==('skipped' if arm=='B' else 'answered')
    assert client.get('/api/admin/responses/'+'d'*32).json['definition']['version']=='diana-v6'
    assert client.delete('/api/privacy/consent',headers=headers).status_code==200
    with app.extensions['survey_store'].connect() as db:
        assert db.execute('SELECT count(*) FROM study_assignments').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM survey_responses').fetchone()[0]==0
    assert client.post('/api/study-assignment',headers=headers).status_code==428

def test_prior_search_is_marked_and_cannot_be_resumed_as_a_new_experimental_run(experiment,monkeypatch):
    app,_=experiment;client=app.test_client();headers,_=grant(client)
    old=client.post('/api/onboard',headers=headers,json=payload()).json
    monkeypatch.setattr('study_assignment.secrets.choice',lambda _:'C')
    assigned=client.post('/api/study-assignment',headers=headers).json
    assert assigned['prior_exposure'] is True
    assert client.get('/api/sessions/'+old['session_id'],headers=headers).status_code==404
    assert client.post('/api/chat',headers=headers,json={'session_id':old['session_id'],'message':'Hallo'}).status_code==404
