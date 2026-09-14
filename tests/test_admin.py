import csv
import io
import json
import zipfile

import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from privacy import token_hash
from test_survey import NoMatching, payload, legacy_payload
from survey_store import SurveySubmission,LegacySurveySubmission


@pytest.fixture
def admin_app(tmp_path):
    app=create_app({'TESTING':True,'DATABASE_PATH':str(tmp_path/'data.sqlite3'),
                    'SEED_DUMMY_DATA':False,'OPENAI_API_KEY':'',
                    'ADMIN_PASSWORD_HASH':generate_password_hash('test-password',method='pbkdf2:sha256:1000')},retriever=NoMatching(),llm=NoMatching())
    return app


def login(client):
    response=client.post('/api/admin/login',json={'password':'test-password'})
    assert response.status_code==200
    return {'X-CSRF-Token':response.json['csrf']}


@pytest.mark.parametrize('path',['/api/admin/responses','/api/admin/responses/'+ 'a'*32,'/api/admin/export?columns=technical&format=csv','/api/admin/export?columns=technical&format=zip'])
def test_answers_and_exports_are_never_public(admin_app,path):
    admin_app.extensions['survey_store'].save(SurveySubmission(**payload()))
    response=admin_app.test_client().get(path)
    assert response.status_code==401
    assert 'Softwareentwicklung' not in response.get_data(as_text=True)
    assert response.headers['Cache-Control']=='no-store'


def test_login_cookie_csrf_logout_and_invalid_password(admin_app):
    client=admin_app.test_client()
    assert client.post('/api/admin/login',json={'password':'wrong'}).status_code==401
    response=client.post('/api/admin/login',json={'password':'test-password'})
    assert 'HttpOnly' in response.headers['Set-Cookie'] and 'SameSite=Strict' in response.headers['Set-Cookie']
    assert 'Path=/api/admin' in response.headers['Set-Cookie']
    assert client.get('/api/admin/session').json['authenticated'] is True
    assert client.post('/api/admin/logout').status_code==403
    assert client.post('/api/admin/logout',headers={'X-CSRF-Token':response.json['csrf']}).status_code==200
    assert client.get('/api/admin/responses').status_code==401


def test_login_limits_failed_attempts(admin_app):
    client=admin_app.test_client()
    for _ in range(5):assert client.post('/api/admin/login',json={'password':'wrong'}).status_code==401
    assert client.post('/api/admin/login',json={'password':'test-password'}).status_code==429


def test_no_default_password_and_cannot_use_participant_consent_as_admin(admin_app):
    admin_app.config['ADMIN_PASSWORD_HASH']=''
    client=admin_app.test_client()
    assert client.get('/api/admin/session').json['configured'] is False
    assert client.post('/api/admin/login',json={'password':'test-password'}).status_code==503
    assert client.get('/api/admin/responses',headers={'X-Diana-Consent':'a'*64}).status_code==401


def test_list_filters_details_and_delete_are_scoped(admin_app):
    store=admin_app.extensions['survey_store']
    store.save(SurveySubmission(**payload()));store.save(SurveySubmission(**payload(submission_id='b'*32)))
    client=admin_app.test_client();csrf=login(client)
    data=client.get('/api/admin/responses?q='+ 'a'*10).json
    assert data['total']==1 and 'answers' not in data['items'][0]
    assert data['items'][0]['openai_models']==[]
    row=client.get('/api/admin/responses/'+ 'a'*32).json
    assert row['answers']['chat_helpfulness']==8 and row['deletion_count']==1
    assert client.delete('/api/admin/responses/'+ 'a'*32,json={'confirm_id':'a'*32}).status_code==403
    assert client.delete('/api/admin/responses/'+ 'a'*32,json={'confirm_id':'b'*32},headers=csrf).status_code==409
    assert client.delete('/api/admin/responses/'+ 'a'*32,json={'confirm_id':'a'*32},headers=csrf).status_code==200
    assert client.get('/api/admin/responses').json['total']==1
    assert client.get('/api/admin/responses/'+ 'b'*32).status_code==200
    assert client.get('/api/admin/responses?page=-1').status_code==400
    assert client.get('/api/admin/responses?q=%27+OR+1=1').json['total']==0


def test_numiqo_export_is_rectangular_numeric_and_keeps_legacy_scale_separate(admin_app):
    store=admin_app.extensions['survey_store'];store.save(SurveySubmission(**payload(search_goal='Python; SQL\n"Data"',study_field='=1+1')))
    store.save(LegacySurveySubmission(**legacy_payload()))
    client=admin_app.test_client();login(client)
    response=client.get('/api/admin/export?columns=technical&format=csv')
    assert response.status_code==200 and response.data.startswith(b'\xef\xbb\xbf')
    rows=list(csv.DictReader(io.StringIO(response.data.decode('utf-8-sig')),delimiter=';'))
    current=next(row for row in rows if row['survey_version']=='diana-v3')
    legacy=next(row for row in rows if row['survey_version']=='diana-v1')
    assert current['chat_helpfulness']=='8' and current['v1_chat_helpfulness']==''
    assert legacy['chat_helpfulness']=='' and legacy['v1_chat_helpfulness']=='4'
    assert current['age_group']=='3' and current['gender']==''
    assert current['search_goal']=='Python; SQL\n"Data"' and current['study_field']=="'=1+1"
    assert current['openai_models']=='' and current['study_release_ids']==''
    assert None not in current
    assert len(list(csv.DictReader(io.StringIO(client.get('/api/admin/export?columns=technical&version=diana-v3').data.decode('utf-8-sig')),delimiter=';')))==1
    package=zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?columns=technical&format=zip').data))
    assert set(package.namelist())=={'diana_numiqo.csv','codebook.csv','codebook.json','study_manifest.json','spaltenzuordnung.csv','teilnahmefluss.csv','README.txt'}
    book=json.loads(package.read('codebook.json'))
    assert next(item for item in book if item['variable']=='score_usefulness')['endpoints']['low']=='Gar nicht nützlich'
    assert '4' not in next(item for item in book if item['variable']=='gender')['codes']
    manifest=json.loads(package.read('study_manifest.json'))
    assert manifest['observed_releases']=={}
    assert manifest['current_configuration']['openai_model']=='gpt-5.4-2026-03-05'
    assert manifest['current_configuration']['reasoning_effort']=='none'


def test_recorded_release_is_preserved_in_export_and_not_backfilled(admin_app):
    store=admin_app.extensions['survey_store'];releases=admin_app.extensions['study_releases']
    def capture(db, record_id):
        releases.mark_run(token_hash('a'*64),db)
        releases.capture_response(token_hash('a'*64),record_id,db,completed=True)
    store.save(SurveySubmission(**payload()),before_save=capture)
    rows=admin_app.extensions['admin_data'].records()
    assert rows[0]['openai_models']==['gpt-5.4-2026-03-05']
    assert rows[0]['study_release_ids']==[releases.release_id]
    assert 'cv' not in json.dumps(releases.manifest).lower()
    assert len(releases.manifest['job_data_sha256'])==64


def test_web_deletion_revokes_linked_participation_and_removes_metadata(admin_app):
    from privacy import ConsentInput
    privacy=admin_app.extensions['privacy_store'];store=admin_app.extensions['survey_store'];releases=admin_app.extensions['study_releases']
    notice={'ready':True,'version':'a'*64}
    privacy.accept(ConsentInput(token='c'*64,version='a'*64,accepted=True),notice)
    def link(db,record_id):
        privacy.attach('c'*64,notice,'survey',record_id,db)
        releases.mark_run(token_hash('c'*64),db)
        releases.capture_response(token_hash('c'*64),record_id,db)
    store.save(SurveySubmission(**payload()),before_save=link)
    participant=privacy.receipt('c'*64)['participation_id']
    client=admin_app.test_client();csrf=login(client)
    assert client.get('/api/admin/responses/'+ 'a'*32).json['participation_id']==participant
    response=client.delete('/api/admin/responses/'+ 'a'*32,json={'confirm_id':participant},headers=csrf)
    assert response.status_code==200
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM survey_response_metadata').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM study_runs').fetchone()[0]==0
        assert db.execute('SELECT withdrawn_at FROM privacy_consents').fetchone()[0]


def test_admin_can_release_pause_and_resume_without_losing_answers(admin_app):
    admin_app.config['PRIVACY_REQUIRED'] = True
    client = admin_app.test_client()
    assert client.get('/api/admin/study-status').status_code == 401
    assert client.put('/api/admin/study-status', json={'enabled': True}).status_code == 401
    csrf = login(client)
    assert client.get('/api/admin/study-status').json['enabled'] is False
    assert client.put('/api/admin/study-status', json={'enabled': True}).status_code == 403
    for invalid in [{'enabled': 'true'}, {'enabled': 1}, {}, {'enabled': True, 'extra': True}]:
        assert client.put('/api/admin/study-status', json=invalid, headers=csrf).status_code == 400
    enabled = client.put('/api/admin/study-status', json={'enabled': True}, headers=csrf)
    assert enabled.status_code == 200 and enabled.json['enabled'] and enabled.json['updated_at']
    notice = client.get('/api/privacy').json['notice']
    assert notice['ready'] is True
    token = 'd'*64
    assert client.post('/api/privacy/consent', json={'token': token, 'version': notice['version'], 'accepted': True}).status_code == 200
    consent = {'X-Diana-Consent': token}
    assert client.post('/api/survey-responses', json=payload(), headers=consent).status_code == 201
    store = admin_app.extensions['survey_store']
    with store.connect() as db:
        assert json.loads(db.execute('SELECT notice_json FROM privacy_consents').fetchone()[0]) == notice
    assert client.put('/api/admin/study-status', json={'enabled': False}, headers=csrf).json['enabled'] is False
    assert client.get('/api/privacy').json['notice']['ready'] is False
    for path in ['/api/search', '/api/onboard', '/api/chat', '/api/survey-responses']:
        assert client.post(path, json=payload(), headers=consent).status_code == 428
    assert client.get('/api/admin/responses').json['total'] == 1
    assert client.post('/api/privacy/consent', json={'token': 'e'*64, 'version': notice['version'], 'accepted': True}).status_code == 428
    # A store in another process observes persistent state immediately.
    from privacy import PrivacyStore, ConsentRequired
    other = PrivacyStore(admin_app.config['DATABASE_PATH'])
    assert other.study_status(notice)['enabled'] is False
    with store.connect() as db, pytest.raises(ConsentRequired):
        other.attach(token, notice, 'survey', 'late-result', db)
    assert client.put('/api/admin/study-status', json={'enabled': True}, headers=csrf).json['enabled'] is True
    assert other.study_status(notice)['enabled'] is True
    status = client.get('/api/privacy', headers=consent).json
    assert status['active'] and status['notice']['version'] == notice['version']
    assert client.post('/api/survey-responses', json=payload(), headers=consent).status_code == 200
    # Withdrawal still works while paused.
    client.put('/api/admin/study-status', json={'enabled': False}, headers=csrf)
    assert client.delete('/api/privacy/consent', headers=consent).status_code == 200


def test_ended_study_cannot_be_reopened_in_admin(admin_app):
    client = admin_app.test_client(); csrf = login(client)
    assert admin_app.test_cli_runner().invoke(args=['privacy-end-study', '--confirm']).exit_code == 0
    state = client.get('/api/admin/study-status').json
    assert state['closed'] and not state['can_enable']
    assert client.put('/api/admin/study-status', json={'enabled': True}, headers=csrf).status_code == 409
    assert client.get('/api/privacy').json['notice']['ready'] is False
