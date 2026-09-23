"""Grounded B/C references across the planner, new searches and saved chat turns."""
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
import test_survey_chat_limit as fixtures
from chat_text import format_chat_answer, assistant_chat_message, chat_instructions, JOB_REFERENCE_INSTRUCTIONS
from chat_completion import conclude_custom_chat
from llm_service import OpenAIService
from test_system_prompts import PROFILE, neutral_patch

JOBS=[{'id':'17','title':'Werkstudent im Bereich Data Management (m/w/d)','company':'MEAG'},
      {'id':'18','title':'Data Analyst','company':'Firma A'},
      {'id':'19','title':'Data Analyst','company':'Firma B'}]


def test_explicit_shortened_and_escaped_titles_are_grounded_without_company_link():
    text=r'Andere Option: [Data Management bei MEAG]\(job:17). Data Analyst und [Andere Option](job:19). [Erfunden](job:999).'
    result=format_chat_answer(text,JOBS)
    assert '[Werkstudent im Bereich Data Management](job:17)' in result
    assert 'Data Analyst und [Data Analyst](job:19)' in result
    assert 'Erfunden.' in result and 'job:999' not in result
    assert '[MEAG]' not in result
    assert format_chat_answer(result,JOBS)==result


def test_legacy_title_fallback_is_unambiguous_and_company_remains_plain():
    text='Werkstudent Data Management bei MEAG ist eine Alternative. Data Analyst auch.'
    result=format_chat_answer(text,JOBS)
    assert result=='[Werkstudent im Bereich Data Management](job:17) bei MEAG ist eine Alternative. Data Analyst auch.'
    assert 'job:' not in format_chat_answer('Data Analysts sind gefragt. MEAG.',JOBS)


def test_c_third_reply_keeps_valid_links_and_complete_sentences():
    value=conclude_custom_chat('Alternative: [Data Management](job:17).\n\nWillst du diese Stelle?',JOBS)
    assert '(job:17)' in value and '?' not in value
    assert 'Alternative:' in value


@pytest.mark.parametrize('policy',['career_fixed','custom_career'])
def test_stream_and_final_planner_resolve_short_labels_using_provided_ids(policy):
    payload={'action':'answer','profile_patch':neutral_patch(),'assistant_message':'Eine andere Stelle: [Kurz](job:17).'}
    class Responses:
        @contextmanager
        def stream(self,**options):
            assert JOB_REFERENCE_INSTRUCTIONS in options['input'][0]['content']
            class Events:
                def __iter__(self):yield SimpleNamespace(type='response.output_text.delta',snapshot=json.dumps(payload))
                def get_final_response(self):return SimpleNamespace(status='completed',usage=None,output_parsed=payload)
            yield Events()
    service=OpenAIService('',client=SimpleNamespace(responses=Responses()))
    steps=service.plan_chat_steps(PROFILE,[],'Andere Stelle bitte',jobs=JOBS,stream=True,prompt_policy=policy,system_prompt='Berate anhand der übergebenen Stellen.')
    preview=next(steps)['data']['assistant_message']
    with pytest.raises(StopIteration) as final:next(steps)
    assert preview==final.value.value['assistant_message']
    assert '[Werkstudent im Bereich Data Management](job:17)' in preview


@pytest.mark.parametrize('arm',['A','B','C'])
def test_route_keeps_references_when_new_search_replaces_results(monkeypatch,arm):
    fixture=fixtures.SurveyChatLimitTests(methodName='runTest');fixture.setUp()
    try:
        retrieval=fixtures.FakeRetriever.search
        selected=0
        def search(self,jobs,query,top_k=20):return retrieval(self,jobs[selected:selected+1],query,top_k)
        monkeypatch.setattr(fixtures.FakeRetriever,'search',search)
        rank=fixture.model.rerank
        def rank_link(persona,profile,candidates,**kwargs):
            result=rank(persona,profile,candidates,**kwargs)
            result['assistant_message']=f'- [Andere Stelle](job:{candidates[0]["job"]["id"]}): Die Aufgaben passen.'
            return result
        monkeypatch.setattr(fixture.model,'rerank',rank_link)
        headers=fixture.grant(arm)
        first=fixture.onboard(headers)
        first_id=first['jobs'][0]['id']
        fixture.model.action='search';selected=1
        second=fixture.chat(headers,first).json
        new_id=second['jobs'][0]['id']
        assert first_id!=new_id
        if arm=='A':
            assert all('job_references' not in m for m in second['messages'])
        else:
            assert second['messages'][0]['job_references'][0]['id']==first_id
            assert second['messages'][-1]['job_references'][0]['id']==new_id
            assert f'(job:{new_id})' in second['messages'][-1]['content']
            assert 'match' not in second['messages'][-1]['job_references'][0]
            restored=fixture.client.get('/api/sessions/'+second['session_id'],headers=headers).json
            assert restored['messages']==second['messages']
    finally:fixture.doCleanups()

@pytest.mark.parametrize('marker',['Job-ID 813447','Job ID: 813447','Stellen-ID: 813447','Anzeigen-ID 813447','Kennung 813447','ID 813447'])
def test_bc_never_displays_identifier_annotations(marker):
    jobs=[{'id':'813447','title':'Werkstudent Data Engineering','company':'Test AG'}]
    value=format_chat_answer(f'- [Stelle](job:813447) ({marker}): Passt mit 85/100 Punkten bei 20 Stunden.',jobs)
    assert value=='- [Werkstudent Data Engineering](job:813447): Passt mit 85/100 Punkten bei 20 Stunden.'
    assert marker not in value


def test_bare_known_ids_become_titles_but_salary_scores_and_hours_remain():
    jobs=[{'id':'813447','title':'Data Engineer'}, {'id':'100000','title':'Data Analyst'}]
    value=format_chat_answer('813447 passt, #100000 ist eine Alternative. 100000 Euro, 85/100 Punkte und 20 Stunden.',jobs)
    assert value=='[Data Engineer](job:813447) passt, [Data Analyst](job:100000) ist eine Alternative. 100000 Euro, 85/100 Punkte und 20 Stunden.'


def test_unknown_labelled_id_is_removed_without_inventing_link():
    assert format_chat_answer('Data Engineer (Job-ID: 999999) passt.',JOBS)=='Data Engineer passt.'


def test_numeric_unknown_link_label_is_not_a_visible_id():
    assert format_chat_answer('Prüfe [999999](job:999999).',JOBS)=='Prüfe diese Stelle.'


def test_known_id_at_sentence_end_is_linked_without_changing_decimal_amounts():
    jobs=[{'id':'813447','title':'Data Engineer'}]
    assert format_chat_answer('Alternative: 813447. 813447,50 Euro.',jobs) == 'Alternative: [Data Engineer](job:813447). 813447,50 Euro.'
