import json
import csv
import io
import sqlite3
import time
from pathlib import Path

import pytest
from app import create_app
from privacy import ConsentInput, ConsentRequired, PrivacyStore, load_notice
from session_store import EphemeralSessionStore, SessionConflict
from test_survey import NoMatching, payload


@pytest.fixture
def privacy_app(tmp_path):
    settings = tmp_path / 'privacy.json'
    settings.write_text(json.dumps(dict(approved=True, controller='Test controller', retention='Test retention',
                                       openai_processing='Test processing', technical_processing='Test transport')))
    return create_app({'TESTING': True, 'DATABASE_PATH': str(tmp_path / 'data.sqlite3'),
                       'OPENAI_API_KEY': '', 'SEED_DUMMY_DATA': False,
                       'PRIVACY_REQUIRED': True, 'PERSIST_CHAT_SESSIONS': False,
                       'PRIVACY_SETTINGS_PATH': settings}, retriever=NoMatching(), llm=NoMatching())


def grant(client, token='a'*64):
    notice = client.get('/api/privacy').json['notice']
    response = client.post('/api/privacy/consent', json=dict(token=token, version=notice['version'], accepted=True))
    assert response.status_code == 200
    return {'X-Diana-Consent': token}, notice


def test_production_notice_stays_closed_until_required_operator_details_are_approved():
    assert load_notice(Path(__file__).parents[1] / 'privacy_settings.json')['ready'] is False


@pytest.mark.parametrize('path', ['/api/search', '/api/onboard', '/api/chat', '/api/survey-responses'])
def test_no_personal_data_or_model_calls_before_consent(privacy_app, path):
    client = privacy_app.test_client()
    assert client.post(path, json=payload()).status_code == 428
    with sqlite3.connect(privacy_app.config['DATABASE_PATH']) as db:
        assert db.execute('SELECT COUNT(*) FROM survey_responses').fetchone()[0] == 0


@pytest.mark.parametrize('accepted', [False, 1, 'true', None])
def test_only_explicit_boolean_acceptance_works(privacy_app, accepted):
    client=privacy_app.test_client()
    notice=client.get('/api/privacy').json['notice']
    assert client.post('/api/privacy/consent', json=dict(token='a'*64, version=notice['version'], accepted=accepted)).status_code in (400,428)
    assert client.get('/api/privacy', headers={'X-Diana-Consent':'a'*64}).json['active'] is False


def test_receipt_has_timestamp_and_exact_notice_without_raw_token_or_ip(privacy_app):
    client=privacy_app.test_client();headers,notice=grant(client)
    grant(client)
    assert client.get('/api/privacy',headers=headers).json['active'] is True
    with sqlite3.connect(privacy_app.config['DATABASE_PATH']) as db:
        rows=db.execute('SELECT * FROM privacy_consents').fetchall()
    assert len(rows)==1 and rows[0][0]!='a'*64
    assert json.loads(rows[0][2])==notice
    assert rows[0][3].endswith('+00:00') and rows[0][4] is None
    assert client.get('/api/privacy').headers['Cache-Control']=='no-store'
    assert client.get('/').headers['Referrer-Policy']=='no-referrer'


def test_withdrawal_deletes_only_owned_answers_and_ram_chat_and_blocks_recreation(privacy_app):
    client=privacy_app.test_client();headers,notice=grant(client)
    other,_=grant(client,'b'*64)
    assert client.post('/api/survey-responses',json=payload(),headers=headers).status_code==201
    assert client.post('/api/survey-responses',json=payload(submission_id='b'*32),headers=other).status_code==201
    store=privacy_app.extensions['privacy_store'];sessions=privacy_app.extensions['chat_store']
    sid=sessions.create({'cv':'private','messages':['private']},before_save=lambda db,sid:store.attach('a'*64,notice,'chat',sid,db))
    assert client.get('/api/sessions/'+sid,headers=other).status_code==428
    assert client.delete('/api/privacy/consent',headers=headers).json['withdrawn'] is True
    assert sessions.get(sid) is None
    assert client.delete('/api/privacy/consent',headers=headers).status_code==200
    assert client.post('/api/survey-responses',json=payload(),headers=headers).status_code==428
    assert client.post('/api/privacy/consent',json=dict(token='a'*64,version=notice['version'],accepted=True)).status_code==428
    with sqlite3.connect(privacy_app.config['DATABASE_PATH']) as db:
        assert db.execute('SELECT submission_id FROM survey_responses').fetchall()==[('b'*32,)]
    with pytest.raises(ConsentRequired):
        sessions.create({'cv':'late result'},before_save=lambda db,sid:store.attach('a'*64,notice,'chat',sid,db))
    assert len(sessions._states)==0


def test_withdrawn_or_foreign_consent_cannot_overwrite_an_existing_submission(privacy_app):
    client=privacy_app.test_client();headers,_=grant(client);other,_=grant(client,'b'*64)
    assert client.post('/api/survey-responses',json=payload(),headers=headers).status_code==201
    assert client.post('/api/survey-responses',json=payload(),headers=other).status_code==428
    assert client.post('/api/survey-responses',json=payload(),headers=headers).status_code==200


def test_ram_only_sessions_expire_and_deleted_sessions_cannot_be_updated(tmp_path):
    store=EphemeralSessionStore(tmp_path/'ram.sqlite3',ttl=.03)
    sid=store.create({'cv':'private'});assert store.get(sid)[0]['cv']=='private'
    with sqlite3.connect(tmp_path/'ram.sqlite3') as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()==[]
    deadline=time.monotonic()+1
    while store.get(sid) and time.monotonic()<deadline:time.sleep(.01)
    assert store.get(sid) is None
    with pytest.raises(SessionConflict):store.update(sid,{'cv':'late'},1)


def test_end_study_requires_confirmation_and_prevents_new_participation(privacy_app):
    client=privacy_app.test_client();headers,notice=grant(client)
    assert client.post('/api/survey-responses',json=payload(),headers=headers).status_code==201
    runner=privacy_app.test_cli_runner()
    assert runner.invoke(args=['privacy-end-study']).exit_code!=0
    assert runner.invoke(args=['privacy-end-study','--confirm']).exit_code==0
    assert client.get('/api/privacy',headers=headers).json['notice']['ready'] is False
    assert client.post('/api/privacy/consent',json=dict(token='c'*64,version=notice['version'],accepted=True)).status_code==428
    with sqlite3.connect(privacy_app.config['DATABASE_PATH']) as db:
        assert db.execute('SELECT COUNT(*) FROM survey_responses').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM privacy_consents').fetchone()[0]==0


def test_participation_id_is_stable_separate_from_token_and_enables_targeted_admin_deletion(privacy_app):
    client=privacy_app.test_client();headers,_=grant(client)
    receipt=client.get('/api/privacy',headers=headers).json['receipt']
    participant_id=receipt['participation_id']
    assert participant_id.startswith('DIANA-') and len(participant_id)==42
    assert 'a'*64 not in str(receipt)
    grant(client)
    assert client.get('/api/privacy',headers=headers).json['receipt']==receipt
    assert client.get('/api/privacy',headers={'X-Diana-Consent':participant_id}).json['active'] is False
    other,_=grant(client,'b'*64)
    assert client.post('/api/survey-responses',json=payload(),headers=headers).status_code==201
    assert client.post('/api/survey-responses',json=payload(submission_id='b'*32),headers=other).status_code==201
    exported=io.StringIO()
    privacy_app.extensions['survey_store'].export_csv(exported)
    rows=list(csv.reader(io.StringIO(exported.getvalue()),delimiter=';'))
    assert rows[1][0]==participant_id
    runner=privacy_app.test_cli_runner()
    command=['privacy-delete','--participation-id',participant_id]
    assert runner.invoke(args=command).exit_code==0
    assert client.get('/api/privacy',headers=headers).json['active'] is True
    assert runner.invoke(args=command+['--confirm']).exit_code==0
    assert client.get('/api/privacy',headers=headers).json['active'] is False
    assert client.get('/api/privacy',headers=other).json['active'] is True
    with sqlite3.connect(privacy_app.config['DATABASE_PATH']) as db:
        assert db.execute('SELECT submission_id FROM survey_responses').fetchall()==[('b'*32,)]
    assert runner.invoke(args=['privacy-delete','--participation-id',"' OR 1=1",'--confirm']).exit_code!=0


def test_admin_revocation_blocks_late_updates_in_another_web_process(privacy_app):
    client=privacy_app.test_client();_,notice=grant(client)
    privacy=privacy_app.extensions['privacy_store'];sessions=privacy_app.extensions['chat_store']
    guard=lambda db,sid:privacy.attach('a'*64,notice,'chat',sid,db)
    sid=sessions.create({'message':'before'},before_save=guard)
    # A separate admin process has no access to the worker's RAM store.
    admin=PrivacyStore(privacy_app.config['DATABASE_PATH'])
    admin.delete_participant(privacy.receipt('a'*64)['participation_id'])
    with pytest.raises(ConsentRequired):
        sessions.update(sid,{'message':'late response'},1,before_save=guard)
    assert sessions.get(sid)[0]=={'message':'before'}
    sessions.delete(sid)
