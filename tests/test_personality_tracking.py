import json
import pytest
from persona_mlds import load_templates
from privacy import token_hash
from study_usage import usage_snapshot
from test_study_assignment import experiment, assign, answers
from test_app import payload
from test_admin import login

def config(key='career'):
    return load_templates()[key]['advisor']

def onboard(client,headers,advisor=None,selection=None):
    return client.post('/api/onboard',headers=headers,json={**payload(),'advisor':advisor or config(),
                       **({'advisor_selection':selection} if selection is not None else {})})

def usage(app,headers):
    with app.extensions['survey_store'].connect() as db:
        return usage_snapshot(token_hash(headers['X-Diana-Consent']),db)

@pytest.mark.parametrize('arm,selection,source',[
    ('A',{'source':'template','template_id':'career'},'not_applicable'),
    ('B',{'source':'template','template_id':'career'},'template'),
    ('B',{'source':'custom','template_id':None},'custom'),
    ('B',None,'unknown'),
])
def test_actual_applied_choice_is_saved_without_raw_personality_text(experiment,monkeypatch,arm,selection,source):
    app,model=experiment;client,headers,_=assign(app,monkeypatch,arm)
    result=onboard(client,headers,selection=selection)
    assert result.status_code==201
    assert result.json['advisor_selection']['source']==source
    observed=usage(app,headers)
    assert observed['initial_source']==observed['last_source']==source
    assert 'description' not in json.dumps(observed) and config()['description'] not in json.dumps(observed)
    if source=='unknown': assert observed['ever_custom'] is None

def test_invalid_template_claim_is_rejected_before_model_call(experiment,monkeypatch):
    app,model=experiment;client,headers,_=assign(app,monkeypatch,'B')
    result=onboard(client,headers,advisor=config()|{'name':'Changed'},selection={'source':'template','template_id':'career'})
    assert result.status_code==400 and not model.calls
    assert usage(app,headers)['capture_version']==0

def test_changes_track_only_applied_selection_and_final_snapshot_stays_frozen(experiment,monkeypatch):
    app,model=experiment;client,headers,_=assign(app,monkeypatch,'B')
    first=onboard(client,headers,selection={'source':'template','template_id':'career'}).json
    sid=first['session_id']
    custom=config()|{'name':'My own adviser','description':'Private content not to log'}
    changed=client.post('/api/chat',headers=headers,json={'session_id':sid,'mode':'rerank','advisor':custom,
        'advisor_selection':{'source':'custom','template_id':None}})
    assert changed.status_code==200
    assert usage(app,headers)['selection_change_count']==1
    model.action,model.patch='answer',{}
    assert client.post('/api/chat',headers=headers,json={'session_id':sid,'message':'Danke'}).status_code==200
    assert usage(app,headers)['selection_change_count']==1
    body={'submission_id':'d'*32,'version':'diana-v7',**answers('B')}
    assert client.post('/api/survey-responses',headers=headers,json=body).status_code==201
    before=usage(app,headers)
    client.post('/api/chat',headers=headers,json={'session_id':sid,'mode':'rerank','advisor':config('expert'),
        'advisor_selection':{'source':'template','template_id':'expert'}})
    login(client)
    row=client.get('/api/admin/responses/'+'d'*32).json
    assert row['personality_usage']==before
    assert row['personality_usage']['last_source']=='custom'

def test_failed_personality_application_keeps_previous_source(experiment,monkeypatch):
    app,_=experiment;client,headers,_=assign(app,monkeypatch,'B')
    first=onboard(client,headers,selection={'source':'template','template_id':'career'}).json
    sid=first['session_id'];state,version=app.extensions['chat_store'].get(sid)
    state.pop('_candidates',None);app.extensions['chat_store'].update(sid,state,version)
    response=client.post('/api/chat',headers=headers,json={'session_id':sid,'mode':'rerank','advisor':config('expert'),
        'advisor_selection':{'source':'template','template_id':'expert'}})
    assert response.status_code==200 and response.json['chat_action']=='answer'
    assert response.json['advisor_selection']['template_id']=='career'
    assert usage(app,headers)['selection_change_count']==0


def test_stateless_search_api_also_records_successful_study_use(experiment,monkeypatch):
    app,_=experiment;client,headers,_=assign(app,monkeypatch,'B')
    response=client.post('/api/search',headers=headers,json={**payload(),'advisor':config('expert'),
        'advisor_selection':{'source':'template','template_id':'expert'}})
    assert response.status_code==200
    assert usage(app,headers)['initial_template_id']=='expert'


def test_explicit_custom_choice_with_identical_values_is_kept_on_plain_answer(experiment,monkeypatch):
    app,model=experiment;client,headers,_=assign(app,monkeypatch,'B')
    first=onboard(client,headers,selection={'source':'template','template_id':'career'}).json
    model.action,model.patch='answer',{}
    response=client.post('/api/chat',headers=headers,json={'session_id':first['session_id'],
        'message':'Welche Fähigkeiten passen?', 'advisor':config(),
        'advisor_selection':{'source':'custom','template_id':None}})
    assert response.status_code==200 and response.json['chat_action']=='answer'
    assert response.json['advisor_selection']['source']=='custom'
    assert usage(app,headers)['last_source']=='custom'
    assert usage(app,headers)['selection_change_count']==1
