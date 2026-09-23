"""Prize-draw eligibility, separation, validation and protected administration."""
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

import test_study_progress_v12 as study_fixture
from raffle import NOTICE_VERSION, RaffleStore
from survey_store import SURVEY_VERSION


@pytest.fixture
def study():
    f=study_fixture.StudyProgressTests(); f.setUp()
    try:
        yield f
    finally:
        f.doCleanups()


def finish(f, arm='A'):
    headers=f.grant(arm)
    state=f.onboard(headers)
    for _ in range(3):
        state=f.chat(headers,state).json
    payload=dict(submission_id=headers['X-Diana-Consent'][:32], version=SURVEY_VERSION, **f.answers(SURVEY_VERSION,arm))
    assert f.client.post('/api/survey-responses',headers=headers,json=payload).status_code==201
    return headers


def entry(email='student@example.edu', **changes):
    return dict(email=email,accepted=True,notice_version=NOTICE_VERSION,**changes)


@pytest.mark.parametrize('arm',['A','B','C'])
def test_completed_study_only_and_separate_storage(study,arm):
    f=study; headers=finish(f,arm)
    assert f.client.get('/api/raffle',headers=headers).json['eligible'] is True
    response=f.client.post('/api/raffle',headers=headers,json=entry('Student+Test@Example.EDU'))
    assert response.status_code==200
    assert response.json=={'registered':True}
    status=f.client.get('/api/raffle',headers=headers).json
    assert status['registered'] and 'email' not in status
    store=f.app.extensions['raffle_store']
    with sqlite3.connect(store.email_path) as db:
        assert [r[1] for r in db.execute('PRAGMA table_info(raffle_entries)')]==['email','consent_version']
        assert db.execute('SELECT * FROM raffle_entries').fetchall()==[('student+test@example.edu',NOTICE_VERSION)]
        dump='\n'.join(db.iterdump())
        assert headers['X-Diana-Consent'] not in dump
        assert 'DIANA-' not in dump
        assert 'WITHOUT ROWID' in db.execute("SELECT sql FROM sqlite_master WHERE name='raffle_entries'").fetchone()[0]
    with sqlite3.connect(store.study_path) as db:
        assert 'student+test@example.edu' not in '\n'.join(db.iterdump())
        assert [r[1] for r in db.execute('PRAGMA table_info(raffle_claims)')]==['token_hash']
    assert store.email_path.stat().st_mode & 0o777 == 0o600


def test_no_completion_or_test_page_cannot_enter(study):
    f=study
    assert f.client.post('/api/raffle',json=entry()).status_code==428
    headers=f.grant()
    assert f.client.get('/api/raffle',headers=headers).json['eligible'] is False
    assert f.client.post('/api/raffle',headers=headers,json=entry()).status_code==428
    headers=f.grant('B',standalone=True)
    assert f.client.post('/api/raffle',headers=headers,json=entry()).status_code==428
    assert f.app.extensions['raffle_store'].summary()['count']==0


@pytest.mark.parametrize('value',['name','a@','a@localhost','a@@example.edu','a b@example.edu',
    'a\r\n@example.edu','.a@example.edu','a..b@example.edu','a@-example.edu','a@example..edu',
    'a@exa_mple.edu','a'*65+'@example.edu',None,[],123])
def test_backend_rejects_non_emails_without_echoing_input(study,value):
    f=study
    response=f.client.post('/api/raffle',json=entry(value))
    assert response.status_code==400
    assert 'email' not in response.json
    assert f.app.extensions['raffle_store'].summary()['count']==0


@pytest.mark.parametrize('changes',[{'accepted':False},{'accepted':1},{'notice_version':'old'},{'participant_id':'forbidden'}])
def test_consent_required_and_no_extra_identity_fields(study,changes):
    f=study; headers=finish(f)
    response=f.client.post('/api/raffle',headers=headers,json={**entry(),**changes})
    assert response.status_code==400
    assert not f.client.get('/api/raffle',headers=headers).json['registered']


def test_retry_and_duplicate_email_are_idempotent(study):
    f=study; headers=finish(f)
    for email in ['Student@EXAMPLE.EDU','student@example.edu','different@example.edu']:
        assert f.client.post('/api/raffle',headers=headers,json=entry(email)).json=={'registered':True}
    second=finish(f,'B')
    assert f.client.post('/api/raffle',headers=second,json=entry('STUDENT@example.edu')).json=={'registered':True}
    store=f.app.extensions['raffle_store']
    assert store.summary()['count']==1
    with sqlite3.connect(store.study_path) as db:
        assert db.execute('SELECT COUNT(*) FROM raffle_claims').fetchone()[0]==2


def test_two_tabs_cannot_enter_two_addresses(study):
    f=study; headers=finish(f)
    def post(index):
        with f.app.test_client() as client:
            return client.post('/api/raffle',headers=headers,json=entry(f'name{index}@example.edu')).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(post,[1,2]))==[200,200]
    assert f.app.extensions['raffle_store'].summary()['count']==1


def test_entry_and_claim_roll_back_together(study):
    f=study; headers=finish(f);store=f.app.extensions['raffle_store']
    with sqlite3.connect(store.study_path) as db:
        db.execute("CREATE TRIGGER fail_claim BEFORE INSERT ON raffle_claims BEGIN SELECT RAISE(ABORT, 'test'); END")
    assert f.client.post('/api/raffle',headers=headers,json=entry()).status_code==500
    assert store.summary()['count']==0
    assert not f.client.get('/api/raffle',headers=headers).json['registered']


def test_withdrawal_does_not_link_or_delete_separate_email(study):
    f=study;headers=finish(f)
    f.client.post('/api/raffle',headers=headers,json=entry())
    f.app.extensions['privacy_store'].withdraw(headers['X-Diana-Consent'])
    assert f.client.get('/api/raffle',headers=headers).status_code==428
    assert f.app.extensions['raffle_store'].summary()['count']==1
    with sqlite3.connect(f.app.config['DATABASE_PATH']) as db:
        assert db.execute('SELECT COUNT(*) FROM raffle_claims').fetchone()[0]==0


def test_admin_export_close_and_delete_require_auth_and_csrf(study):
    f=study; headers=finish(f)
    f.client.post('/api/raffle',headers=headers,json=entry('+student@example.edu'))
    assert f.client.get('/api/admin/raffle/export').status_code==401
    f.app.config['ADMIN_PASSWORD_HASH']=generate_password_hash('test-only-password')
    login=f.client.post('/api/admin/login',json={'password':'test-only-password'})
    csrf={'X-CSRF-Token':login.json['csrf']}
    exported=f.client.get('/api/admin/raffle/export').text
    assert exported=='\ufeffemail\r\n\'+student@example.edu\r\n'
    assert '+student@example.edu' not in f.client.get('/api/admin/export?format=csv').text
    assert f.client.delete('/api/admin/raffle',json={'email':'+student@example.edu'}).status_code==403
    for invalid in [None,False,[],123]:
        assert f.client.delete('/api/admin/raffle',headers=csrf,json={'email':invalid}).status_code==400
        assert f.app.extensions['raffle_store'].summary()=={'count':1,'enabled':True}
    assert f.client.put('/api/admin/raffle',headers=csrf,json={'enabled':False}).status_code==200
    another=finish(f,'C')
    assert f.client.post('/api/raffle',headers=another,json=entry()).status_code==409
    assert f.client.delete('/api/admin/raffle',headers=csrf,json={'email':'+student@example.edu'}).json['count']==0
    f.client.put('/api/admin/raffle',headers=csrf,json={'enabled':True})
    assert f.client.post('/api/raffle',headers=another,json=entry()).status_code==200
    assert f.client.delete('/api/admin/raffle',headers=csrf,json={'confirmation':'wrong'}).status_code==400
    cleared=f.client.delete('/api/admin/raffle',headers=csrf,json={'confirmation':'ALLE GEWINNSPIELADRESSEN LÖSCHEN'})
    assert cleared.json=={'count':0,'enabled':False}
    with sqlite3.connect(f.app.config['DATABASE_PATH']) as db:
        assert db.execute('SELECT COUNT(*) FROM survey_responses').fetchone()[0]==2


def test_cannot_use_research_database_for_email(study):
    path=study.app.config['DATABASE_PATH']
    with pytest.raises(ValueError):RaffleStore(path,path)
