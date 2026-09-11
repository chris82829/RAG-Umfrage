from copy import deepcopy
from app import neutral_card_order, NEUTRAL_PRESENTATION_VERSION
from test_app import setup, payload
from test_llm_service import profile, service_with_output, chat_decision, candidate
from llm_service import _GENERIC_CHAT_INSTRUCTIONS
import json


def test_random_order_is_reproducible_score_independent_and_lossless():
    cards=[{'id':str(i),'match':{'score':100-i}} for i in range(20)]
    before=deepcopy(cards)
    shuffled,seed=neutral_card_order(cards,'fixed-test-seed')
    assert cards==before
    assert sorted(x['id'] for x in shuffled)==sorted(x['id'] for x in cards)
    assert shuffled!=cards
    changed=[dict(x,match={'score':1}) for x in reversed(cards)]
    assert [x['id'] for x in neutral_card_order(changed,seed)[0]]==[x['id'] for x in shuffled]
    assert neutral_card_order(cards,'another-seed')[0]!=shuffled
    _,new_seed=neutral_card_order(cards)
    assert new_seed and new_seed!=seed


def test_neutral_random_order_survives_reload_answer_and_rerank(setup):
    app,client,retriever,llm=setup
    neutral=payload()|{'advisor':{'mode':'preset','preset':'neutral'}}
    initial=client.post('/api/onboard',json=neutral).json
    sid=initial['session_id'];ids=[x['id'] for x in initial['jobs']]
    saved,version=app.extensions['chat_store'].get(sid)
    seed=saved['_ordering_seed']
    assert saved['_presentation_version']==NEUTRAL_PRESENTATION_VERSION
    assert '_ordering_seed' not in initial
    assert initial['assistant_message'] == 'Hallo ich bin dein KI Assistent'
    assert [x['id'] for x in client.get('/api/sessions/'+sid).json['jobs']]==ids
    llm.action='answer';llm.patch={}
    answer=client.post('/api/chat',json={'session_id':sid,'message':'Was ist die zweite Stelle?'}).json
    assert [x['id'] for x in answer['jobs']]==ids
    assert [x['id'] for x in llm.last_plan_context['jobs']]==ids
    llm.ranking_indices=list(reversed(range(len(ids))))
    reranked=client.post('/api/chat',json={'session_id':sid,'mode':'rerank'}).json
    assert [x['id'] for x in reranked['jobs']]==ids
    assert app.extensions['chat_store'].get(sid)[0]['_ordering_seed']==seed
    assert 'zufällig' in reranked['assistant_message']
    fresh=client.post('/api/onboard',json=neutral).json
    assert app.extensions['chat_store'].get(fresh['session_id'])[0]['_ordering_seed']!=seed


def test_personalized_order_still_comes_from_reranker(setup):
    _,client,_,llm=setup
    llm.ranking_indices=[4,3,2,1,0]
    result=client.post('/api/onboard',json=payload()).json
    assert [x['match']['score'] for x in result['jobs']]==[90,89,88,87,86]
    assert '_ordering_seed' not in result


def test_old_neutral_sessions_require_a_new_search(setup):
    app,client,_,_=setup
    initial=client.post('/api/onboard',json=payload()|{'advisor':{'preset':'neutral'}}).json
    sid=initial['session_id'];store=app.extensions['chat_store']
    state,version=store.get(sid);state.pop('_presentation_version')
    store.update(sid,state,version)
    assert client.get('/api/sessions/'+sid).status_code==404
    response=client.post('/api/chat',json={'session_id':sid,'message':'Hallo'})
    assert response.status_code==404 and 'neu' in response.json['error']['message']


def test_actual_neutral_chat_system_message_has_no_job_role_or_domain_rules(profile):
    service,client=service_with_output(chat_decision())
    job=candidate('one')['job'];job['match']={'score':90,'reasons':['Begründung']}
    service.plan_chat(profile,[],'Was steht im ersten Eintrag?',jobs=[job],advisor={'preset':'neutral'})
    messages=client.responses.parse.call_args.kwargs['input']
    assert messages[0]['content']==_GENERIC_CHAT_INSTRUCTIONS
    for forbidden in ['Jobsuche','Stellenberatung','Stellenanzeigen','scoring_weights','technical_fit','STUDIENVARIANTE','assistant_preferences']:
        assert forbidden not in messages[0]['content']
    data=json.loads(messages[1]['content'])
    assert 'assistant_preferences' not in data and 'context_entries' in data
    assert 'previous_score' not in data['context_entries'][0]
    assert messages[0]['content'] == 'Du bist ein allgemeiner KI-Assistent.'
    assert sum(message['role']=='system' for message in messages)==1


def test_dashboard_keeps_old_and_new_presentations_separate():
    from test_admin_analytics import record
    from survey_analytics import analytics
    old=record();new=record()
    old['presentation_versions']=['undocumented']
    new['presentation_versions']=[NEUTRAL_PRESENTATION_VERSION]
    data=analytics([old,new],'diana-v7')
    assert len(data['cohorts'])==2
    assert all(cohort['total']==1 for cohort in data['cohorts'])


def test_general_chat_accepts_long_answers_and_omits_output_cap(profile):
    from llm_service import GenericChatDecision
    result=chat_decision();result['assistant_message']=('Eine sachliche Antwort. '*500).strip()
    service,client=service_with_output(result)
    actual=service.plan_chat(profile,[],'Erkläre es.',jobs=[],advisor={'preset':'neutral'})
    assert actual['assistant_message']==result['assistant_message']
    options=client.responses.parse.call_args.kwargs
    assert 'max_output_tokens' not in options
    assert options['text_format'] is GenericChatDecision
    assert 'maxLength' not in GenericChatDecision.model_json_schema()['properties']['assistant_message']
    for forbidden in ['600','kurz','knapp','Wörter','Sätzen']:
        assert forbidden not in options['input'][0]['content']
