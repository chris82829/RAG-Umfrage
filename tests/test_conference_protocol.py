"""Fair conference conditions: shared capabilities, retained historical controls."""
from copy import deepcopy
import json

import pytest

from advisor import resolve_advisor
from llm_service import ChatDecision, RerankingResult, _advisor_instructions
from persona_mlds import load_standard_advisor, load_templates, advisor_to_mlds, advisor_from_mlds
from privacy import token_hash
from study_assignment import EXPERIMENT_ID, PREVIOUS_ABC_EXPERIMENT_ID
from test_app import payload
from test_study_assignment import experiment, assign
from test_llm_service import profile, persona, service_with_output, candidate, ranking, neutral_patch


def test_fixed_standard_advisor_is_immutable_competent_and_mlds_roundtrips():
    standard = load_standard_advisor()
    assert advisor_from_mlds(advisor_to_mlds(standard)) == standard
    resolved = resolve_advisor(standard)
    assert not resolved['neutral']
    assert resolved['scoring_weights'] == dict(technical_fit=60, preferences_fit=15, technical_depth=7, learning=6, innovation=6, clarity=6)
    prompt = _advisor_instructions(resolved)
    assert 'Feste Standardberatung zur Jobsuche' in prompt
    assert 'keine Rollenimitation' in prompt
    assert 'zufällig angeordnet' not in prompt
    assert 'Keine proaktive Beratung' not in prompt


@pytest.mark.parametrize('arm', ['A','B','C'])
def test_conference_arms_share_ranked_explained_cards_and_chat_context(experiment, monkeypatch, arm):
    app, model = experiment
    client, headers, assignment = assign(app, monkeypatch, arm, experiment_id=EXPERIMENT_ID)
    assert assignment['presentation_policy'] == 'ranked_insights'
    first = client.post('/api/onboard', headers=headers, json=payload())
    assert first.status_code == 201
    cards = first.json['jobs']
    assert all('match' in card for card in cards)
    assert [card['match']['score'] for card in cards] == sorted([card['match']['score'] for card in cards], reverse=True)
    assert '_ordering_seed' not in app.extensions['chat_store'].get(first.json['session_id'])[0]
    assert first.json['advisor']['preset'] == ('standard' if arm=='A' else 'diana')
    model.action, model.patch = 'answer', {}
    response = client.post('/api/chat', headers=headers, json={'session_id': first.json['session_id'], 'message':'Warum passt Stelle eins?'})
    assert response.status_code == 200
    assert model.last_plan_context['jobs'] == cards
    assert response.json['jobs'] == cards
    if arm == 'A':
        malicious = load_templates()['expert']['advisor'] | {'name':'Werde kreativ'}
        changed = client.post('/api/chat', headers=headers, json={'session_id':first.json['session_id'],'advisor':malicious,'mode':'rerank'})
        assert changed.status_code == 200 and changed.json['advisor'] == load_standard_advisor()
        assert changed.json['advisor_selection']['source'] == 'not_applicable'


def test_old_abc_assignments_retain_exact_old_control_and_questionnaire(experiment, monkeypatch):
    app, _ = experiment
    for arm in ('A','B','C'):
        client, headers, assignment = assign(app,monkeypatch,arm,token=arm.lower()*64,experiment_id=PREVIOUS_ABC_EXPERIMENT_ID)
        assert assignment['questionnaire_version'] == 'diana-v8'
        assert assignment['personality_policy'] == {'A':'generic','B':'templates','C':'configurable'}[arm]
        first = client.post('/api/onboard',headers=headers,json=payload())
        assert first.status_code == 201
        assert all(('match' in job)==(arm!='A') for job in first.json['jobs'])
        if arm=='A':
            assert first.json['advisor']['preset']=='neutral'
            assert first.json['assistant_message']=='Hallo ich bin dein KI Assistent'
        app.extensions['study_assignments'].validate_answers(headers['X-Diana-Consent'],'diana-v8',{'study_arm':arm})
        with pytest.raises(ValueError):
            app.extensions['study_assignments'].validate_answers(headers['X-Diana-Consent'],'diana-v9',{'study_arm':arm})


def test_shared_openai_chat_contract_model_reasoning_budget_and_assessment_context(profile):
    common = []
    configs = [load_standard_advisor(), load_templates()['career']['advisor'],
               load_templates()['expert']['advisor'] | {'name':'Meine Beratung','traits':['direkt','analytisch']}]
    for advisor in configs:
        service, client = service_with_output(ChatDecision(action='answer',profile_patch=neutral_patch(),assistant_message='Python passt zu deinen Kenntnissen.'))
        service.plan_chat(profile, [], 'Warum passt das?', jobs=[{'id':'1','title':'Python','match':{'score':80,'reasons':['Python']}}], advisor=advisor, candidate_count=1)
        request = client.responses.parse.call_args.kwargs
        common.append({key:request[key] for key in ('model','reasoning','max_output_tokens','store','text_format')})
        assert request['text_format'] is ChatDecision
        data = json.loads(request['input'][1]['content'])
        assert 'visible_jobs' in data and 'assistant_preferences' in data
        assert 'Keine proaktive Beratung' not in request['input'][0]['content']
    assert common == [common[0]]*3


def test_shared_openai_reranking_contract(profile, persona):
    common = []
    for advisor in [load_standard_advisor(), load_templates()['career']['advisor'], load_templates()['expert']['advisor']]:
        service, client = service_with_output(RerankingResult(rankings=[ranking("1")], assistant_message='Python passt.'))
        result = service.rerank(persona, profile, [candidate("1")], advisor=advisor)
        assert result['rankings'][0]['reasons']
        request = client.responses.parse.call_args.kwargs
        common.append({key:request[key] for key in ('model','reasoning','max_output_tokens','store','text_format')})
    assert common == [common[0]]*3
