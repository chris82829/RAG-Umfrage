"""Persist totals only for actual operations and freeze completed response metrics."""
import json

from llm_service import LLMUnavailable
from privacy import token_hash
from study_metrics import metrics_snapshot
from study_assignment import EXPERIMENT_ID
from test_study_assignment import experiment, assign
from test_app import payload, STREAM_HEADERS, stream_events
from test_standalone import standalone, grant_test


def metrics(app, headers):
    with app.extensions['survey_store'].connect() as db:
        return metrics_snapshot(token_hash(headers['X-Diana-Consent']), db)


def test_successful_search_chat_and_actual_rerank_are_counted(experiment, monkeypatch):
    app, model = experiment
    client, headers, _ = assign(app,monkeypatch,'A',experiment_id=EXPERIMENT_ID)
    first = client.post('/api/onboard', headers=headers,json=payload()).json
    assert metrics(app,headers)['successful_search_count']==1
    model.action, model.patch='answer',{}
    assert client.post('/api/chat',headers=headers,json={'session_id':first['session_id'],'message':'Warum passt die Stelle?'}).status_code==200
    model.action='rerank'
    assert client.post('/api/chat',headers=headers,json={'session_id':first['session_id'],'message':'Bitte neu bewerten'}).status_code==200
    model.action='search'
    assert client.post('/api/chat',headers=headers,json={'session_id':first['session_id'],'message':'Suche erneut'}).status_code==200
    result=metrics(app,headers)
    assert result['successful_search_count']==2
    assert result['successful_rerank_count']==1
    assert result['successful_chat_count']==3
    assert result['failed_chat_count']==0
    assert all(type(result[key]) is int and result[key]>=0 for key in result if key.endswith('_duration_ms'))
    assert 'Warum passt' not in json.dumps(result)


def test_failed_planning_does_not_claim_search_and_failed_search_counts_both(experiment, monkeypatch):
    app,model=experiment;client,headers,_=assign(app,monkeypatch,'A',experiment_id=EXPERIMENT_ID)
    first=client.post('/api/onboard',headers=headers,json=payload()).json
    def fail(*args,**kwargs): raise LLMUnavailable('Testfehler')
    with monkeypatch.context() as patch:
        patch.setattr(model,'plan_chat',fail)
        response=client.post('/api/chat',headers=headers,json={'session_id':first['session_id'],'message':'Test'})
        assert response.status_code==503
    result=metrics(app,headers)
    assert result['failed_chat_count']==1 and result['failed_search_count']==0
    model.action,model.patch='search',{}
    with monkeypatch.context() as patch:
        patch.setattr(model,'rerank',fail)
        response=client.post('/api/chat',headers=headers|STREAM_HEADERS,json={'session_id':first['session_id'],'message':'Neue Suche'})
        assert stream_events(response)[-1]['type']=='error'
    result=metrics(app,headers)
    assert result['failed_chat_count']==2 and result['failed_search_count']==1


def test_onboarding_failure_and_validation_failure_have_distinct_totals(experiment, monkeypatch):
    app,model=experiment;client,headers,_=assign(app,monkeypatch,'B',experiment_id=EXPERIMENT_ID)
    bad={'mode':'custom','name':'Manipuliert','traits':['direkt'],'focus':'innovation'}
    assert client.post('/api/onboard',headers=headers,json=payload()|{'advisor':bad}).status_code==400
    assert metrics(app,headers)['capture_version']==0
    def fail(*args,**kwargs): raise LLMUnavailable('Testfehler')
    monkeypatch.setattr(model,'generate_persona',fail)
    assert client.post('/api/onboard',headers=headers,json=payload()).status_code==503
    result=metrics(app,headers)
    assert result['failed_search_count']==1 and result['failed_chat_count']==0


def test_completion_snapshot_freezes_and_withdrawal_deletes(experiment,monkeypatch):
    from survey_store import SURVEY_FIELDS, field_visible
    app,model=experiment;client,headers,_=assign(app,monkeypatch,'A',experiment_id=EXPERIMENT_ID)
    first=client.post('/api/onboard',headers=headers,json=payload()).json
    values={f['name']:8 if f['kind']=='scale' else f['options'][0][0] if f['kind']=='choice' else '' if f.get('optional') else 'Softwareentwicklung' for f in SURVEY_FIELDS}
    values['study_arm']='A'
    for field in SURVEY_FIELDS:
        if not field_visible(field,values): values[field['name']]=None
    before=metrics(app,headers)
    response=client.post('/api/survey-responses',headers=headers,json={'submission_id':'d'*32,'version':'diana-v9',**values})
    assert response.status_code==201, response.json
    model.action,model.patch='answer',{}
    assert client.post('/api/chat',headers=headers,json={'session_id':first['session_id'],'message':'Danke'}).status_code==200
    with app.extensions['survey_store'].connect() as db:
        saved=json.loads(db.execute('SELECT metadata_json FROM survey_response_metadata').fetchone()[0])
        assert saved['operation_metrics']==before
    assert metrics(app,headers)['successful_chat_count']==1
    assert client.delete('/api/privacy/consent',headers=headers).status_code==200
    with app.extensions['survey_store'].connect() as db:
        assert db.execute('SELECT count(*) FROM study_operation_metrics').fetchone()[0]==0


def test_direct_tests_never_capture_operation_totals(standalone):
    app,client,model=standalone
    for arm in ('A','B','C'):
        headers=grant_test(client,arm)
        first=client.post('/api/onboard',headers=headers,json=payload()).json
        model.action,model.patch='answer',{}
        client.post('/api/chat',headers=headers,json={'session_id':first['session_id'],'message':'Danke'})
    with app.extensions['survey_store'].connect() as db:
        assert db.execute('SELECT count(*) FROM study_operation_metrics').fetchone()[0]==0
