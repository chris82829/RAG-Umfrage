import csv
import io
import json
import sqlite3

import pytest
from survey_store import SurveyDraft, SurveySubmissionV4, SURVEY_FIELDS
from privacy import ConsentInput, ConsentRequired
from test_survey import survey_app
from test_survey_v4 import v4_payload
from test_privacy import privacy_app, grant
from test_admin import admin_app, login


def draft(**changes):
    return dict(submission_id='c'*32,version='diana-v4',revision=1,answers={'age_group':'21_24'},waiting_answered=['age_group']) | changes


def test_each_answer_upserts_one_draft_with_idempotent_retries_and_stale_protection(survey_app):
    client=survey_app.test_client()
    assert client.put('/api/survey-drafts',json=draft()).json=={'saved':True,'completed':False,'revision':1}
    first=client.get('/api/survey-drafts/'+'c'*32).json['draft']
    assert client.put('/api/survey-drafts',json=draft()).status_code==200
    second=draft(revision=2,answers={'age_group':'21_24','gender':'not_specified'})
    assert client.put('/api/survey-drafts',json=second).status_code==200
    assert client.put('/api/survey-drafts',json=draft()).status_code==409
    assert client.put('/api/survey-drafts',json=second|{'answers':{'age_group':'40_plus'}}).status_code==409
    with survey_app.extensions['survey_store'].connect() as db:
        assert db.execute('SELECT count(*) FROM survey_responses').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM survey_drafts').fetchone()[0]==1
    restored=client.get('/api/survey-drafts/'+'c'*32).json['draft']
    assert restored['revision']==2 and restored['answers']['gender']=='not_specified'
    assert first['answers']['age_group']==restored['answers']['age_group']


@pytest.mark.parametrize('changes',[
    {'revision':True},{'revision':0},{'version':'diana-v3'},{'submission_id':'invalid'},
    {'answers':{'score_usefulness':11}},{'answers':{'score_usefulness':True}},
    {'answers':{'age_group':'invalid'}},{'answers':{'profile':{'cv':'private'}}},
    {'answers':{'feedback':'x'*4001}},{'waiting_answered':['unknown']},
    {'answers':{'chat_used':'no','chat_helpfulness':5}},
])
def test_invalid_partial_inputs_are_rejected(survey_app,changes):
    response=survey_app.test_client().put('/api/survey-drafts',json=draft(**changes))
    assert response.status_code==400
    assert 'private' not in response.get_data(as_text=True)


def test_short_text_drafts_and_clearing_an_answer_are_preserved(survey_app):
    client=survey_app.test_client()
    assert client.put('/api/survey-drafts',json=draft(answers={'search_goal':'P'})).status_code==200
    assert client.put('/api/survey-drafts',json=draft(revision=2,answers={'search_goal':''})).status_code==200
    assert client.get('/api/survey-drafts/'+'c'*32).json['draft']['answers']['search_goal']==''


def test_final_submission_promotes_draft_and_late_autosaves_cannot_recreate_it(survey_app):
    client=survey_app.test_client()
    client.put('/api/survey-drafts',json=draft())
    assert client.post('/api/survey-responses',json=v4_payload()).status_code==201
    assert client.put('/api/survey-drafts',json=draft(revision=2)).json['completed'] is True
    assert client.get('/api/survey-drafts/'+'c'*32).json['draft']=={'completed':True}
    assert client.post('/api/survey-responses',json=v4_payload()).status_code==200
    with survey_app.extensions['survey_store'].connect() as db:
        assert db.execute('SELECT count(*) FROM survey_drafts').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM survey_responses').fetchone()[0]==1


def test_consent_ownership_withdrawal_and_no_recreation_of_partial_answers(privacy_app):
    client=privacy_app.test_client()
    assert client.put('/api/survey-drafts',json=draft()).status_code==428
    headers,_=grant(client);other,_=grant(client,'b'*64)
    assert client.put('/api/survey-drafts',json=draft(),headers=headers).status_code==200
    assert client.get('/api/survey-drafts/'+'c'*32,headers=other).json=={'draft':None}
    assert client.put('/api/survey-drafts',json=draft(revision=2),headers=other).status_code==428
    assert client.delete('/api/privacy/consent',headers=headers).status_code==200
    assert client.put('/api/survey-drafts',json=draft(revision=3),headers=headers).status_code==428
    with sqlite3.connect(privacy_app.config['DATABASE_PATH']) as db:
        assert db.execute('SELECT count(*) FROM survey_drafts').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM survey_response_metadata').fetchone()[0]==0


def test_admin_lists_exports_filters_and_deletes_partial_answers(admin_app):
    client=admin_app.test_client();client.put('/api/survey-drafts',json=draft())
    client.post('/api/survey-responses',json=v4_payload(submission_id='d'*32))
    csrf=login(client)
    items=client.get('/api/admin/responses').json['items'];assert len(items)==2
    assert {item['response_status'] for item in items}=={'completed','in_progress'}
    assert client.get('/api/admin/responses?status=in_progress').json['total']==1
    assert client.get('/api/admin/responses?status=completed').json['total']==1
    assert client.get('/api/admin/responses?status=invalid').status_code==400
    response=client.get('/api/admin/export?status=in_progress')
    row=next(csv.DictReader(io.StringIO(response.data.decode('utf-8-sig')),delimiter=';'))
    assert row['response_status']=='in_progress' and row['submitted_at_utc']=='' and row['last_saved_at_utc']
    assert row['v4_age_group']=='3' and row['v4_gender']==''
    assert row['v4_gender_status']=='unanswered' and row['v4_chat_helpfulness_status']=='unanswered'
    assert client.delete('/api/admin/responses/'+'c'*32,json={'confirm_id':'c'*32},headers=csrf).status_code==200
    assert client.get('/api/admin/responses').json['total']==1


def test_new_notice_can_be_explicitly_accepted_without_losing_id_or_old_receipt(privacy_app):
    client=privacy_app.test_client();headers,notice=grant(client)
    before=client.get('/api/privacy',headers=headers).json['receipt']['participation_id']
    store=privacy_app.extensions['privacy_store'];changed={**notice,'version':'e'*64}
    with pytest.raises(ConsentRequired):store.require('a'*64,changed)
    store.accept(ConsentInput(token='a'*64,version='e'*64,accepted=True),changed)
    assert store.receipt('a'*64)['participation_id']==before
    with sqlite3.connect(privacy_app.config['DATABASE_PATH']) as db:
        old=json.loads(db.execute('SELECT notice_json FROM privacy_consent_history').fetchone()[0])
    assert old['version']==notice['version']
    store.withdraw('a'*64)
    with pytest.raises(ConsentRequired):store.accept(ConsentInput(token='a'*64,version='e'*64,accepted=True),changed)
