import csv
import io
import json
import sqlite3
import zipfile

import pytest

from survey_store import SurveyStore, SurveyRequest, SurveyDraftRequest, SurveyConflict
from test_admin import admin_app, login
from test_admin_analytics import question
from test_survey import payload, legacy_payload
from test_survey_v4 import v4_payload
from test_survey_v5 import v5_payload
from test_survey_v7 import versioned_payload, seed_record


def detail(client, sid='a' * 32):
    return client.get('/api/admin/responses/' + sid).json


def correction(row, **changes):
    return dict(edit_revision=row['edit_revision'], reason='Dokumentierte Rückmeldung', answers=row['answers'] | changes)


def seed(app, answers=None):
    app.extensions['survey_store'].save(SurveyRequest.model_validate(answers or versioned_payload()).root)


def test_corrections_require_admin_session_and_csrf(admin_app):
    seed(admin_app)
    client = admin_app.test_client()
    path = '/api/admin/responses/' + 'a' * 32
    assert client.put(path, json={}).status_code == 401
    login(client)
    row = detail(client)
    response = client.put(path, json=correction(row, system_usefulness=4))
    assert response.status_code == 403
    assert detail(client)['answers']['system_usefulness'] == 8
    assert response.headers['Cache-Control'] == 'no-store'


def test_saved_correction_is_audited_and_used_in_charts_and_all_exports(admin_app):
    seed_record(admin_app, 'diana-v7', 'A', 'a')
    store = admin_app.extensions['survey_store']
    with store.connect() as db:
        original_metadata = {table: [tuple(item) for item in db.execute('SELECT * FROM ' + table)]
                             for table in ['privacy_consents', 'privacy_links', 'study_assignments', 'survey_response_metadata']}
    client = admin_app.test_client(); headers = login(client); before = detail(client)
    result = client.put('/api/admin/responses/' + before['id'], headers=headers,
                        json=correction(before, system_usefulness=4, search_goal='Korrigiertes Suchvorhaben'))
    assert result.status_code == 200
    after = result.json
    assert after['answers']['system_usefulness'] == 4
    assert after['edit_revision'] != before['edit_revision']
    for key in ['id', 'participation_id', 'study_arm', 'experiment_id', 'assigned_at_utc', 'submitted_at_utc', 'survey_version', 'response_status']:
        assert after[key] == before[key]
    assert after['last_saved_at_utc'] == after['last_corrected_at_utc']
    assert after['correction_count'] == 1
    audit = after['corrections'][0]
    assert audit['before']['system_usefulness'] == 8 and audit['after']['system_usefulness'] == 4
    assert audit['reason'] == 'Dokumentierte Rückmeldung' and audit['actor'] == 'admin'
    assert {entry['field'] for entry in audit['changes']} == {'system_usefulness', 'search_goal'}
    with store.connect() as db:
        assert original_metadata == {table: [tuple(item) for item in db.execute('SELECT * FROM ' + table)] for table in original_metadata}
    charts = client.get('/api/admin/analytics?version=diana-v7').json
    assert question(charts, 'system_usefulness')['overall']['mean'] == 4
    exported = next(csv.DictReader(io.StringIO(client.get('/api/admin/export?columns=technical').data.decode('utf-8-sig')), delimiter=';'))
    assert exported['v7_system_usefulness'] == '4' and exported['correction_count'] == '1'
    cli_csv = io.StringIO(); store.export_csv(cli_csv)
    assert 'Korrigiertes Suchvorhaben' in cli_csv.getvalue()
    archive = zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?columns=technical&format=zip').data))
    history = json.loads(archive.read('answer_corrections.json'))
    assert history[0]['corrections'][0]['before']['system_usefulness'] == 8
    assert history[0]['participation_id'] == before['participation_id']
    assert 'answer_corrections.json' not in zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?columns=technical&format=zip&q=UNKNOWN').data)).namelist()


@pytest.mark.parametrize('changes', [
    {'system_usefulness': 0}, {'system_usefulness': 11}, {'system_usefulness': True},
    {'system_usefulness': '8'}, {'system_usefulness': None}, {'study_arm': 'B'},
    {'score_usefulness': 5}, {'age_group': 'invalid'}, {'search_goal': 'x'},
    {'feedback': 'x' * 4001}, {'submission_id': 'b' * 32}, {'version': 'diana-v6'},
])
def test_invalid_values_skipped_questions_and_immutable_fields_are_rejected(admin_app, changes):
    seed(admin_app)
    client = admin_app.test_client(); headers = login(client); before = detail(client)
    assert client.put('/api/admin/responses/' + before['id'], headers=headers, json=correction(before, **changes)).status_code == 400
    assert detail(client)['answers'] == before['answers']
    assert detail(client)['correction_count'] == 0


@pytest.mark.parametrize('change', [lambda data: data | {'reason': ''}, lambda data: data | {'reason': '  '},
    lambda data: data | {'reason': 'x' * 1001}, lambda data: data | {'edit_revision': 'invalid'},
    lambda data: data | {'participation_id': 'changed'}, lambda data: data | {'answers': {'system_usefulness': 3}}])
def test_correction_request_is_strict(admin_app, change):
    seed(admin_app)
    client = admin_app.test_client(); headers = login(client); row = detail(client)
    assert client.put('/api/admin/responses/' + row['id'], headers=headers, json=change(correction(row))).status_code == 400


def test_stale_admin_updates_conflict_and_unchanged_save_creates_no_audit(admin_app):
    seed(admin_app)
    client = admin_app.test_client(); headers = login(client); row = detail(client)
    path = '/api/admin/responses/' + row['id']
    unchanged = client.put(path, headers=headers, json=correction(row)).json
    assert unchanged['correction_count'] == 0 and unchanged['edit_revision'] == row['edit_revision']
    assert client.put(path, headers=headers, json=correction(row, system_usefulness=3)).status_code == 200
    assert client.put(path, headers=headers, json=correction(row, system_usefulness=2)).status_code == 409
    current = detail(client)
    assert client.put(path, headers=headers, json=correction(current, system_usefulness=8)).status_code == 200
    reverted = detail(client)
    assert reverted['correction_count'] == 2 and reverted['edit_revision'] != row['edit_revision']
    assert client.put(path, headers=headers, json=correction(row, system_usefulness=2)).status_code == 409


@pytest.mark.parametrize('answers,field,value', [
    (legacy_payload(submission_id='a'*32), 'chat_helpfulness', 5),
    ({**{key:value for key,value in payload().items() if not key.endswith('_usefulness')}, 'version':'diana-v2'}, 'chat_helpfulness', 10),
    (payload(), 'chat_helpfulness', 10),
    (v4_payload(submission_id='a'*32), 'chat_helpfulness', 10),
    (v5_payload(submission_id='a'*32), 'chat_helpfulness', 10),
    (versioned_payload('diana-v6', 'B'), 'score_usefulness', 10),
    (versioned_payload('diana-v7', 'B'), 'score_usefulness', 10),
])
def test_historical_versions_keep_their_original_schema(admin_app, answers, field, value):
    seed(admin_app, answers)
    client=admin_app.test_client(); headers=login(client); row=detail(client)
    assert client.put('/api/admin/responses/' + row['id'], headers=headers, json=correction(row, **{field:value})).status_code == 200
    assert detail(client)['survey_version'] == answers['version']
    assert detail(client)['answers'].get('study_arm') == answers.get('study_arm')
    if answers['version'] == 'diana-v2':
        assert 'score_usefulness' not in {field['name'] for group in [row['definition']['demographics'], *row['definition']['categories']] for field in group['fields']}


def test_legacy_five_point_scale_cannot_be_changed_to_ten(admin_app):
    seed(admin_app, legacy_payload(submission_id='a'*32))
    client=admin_app.test_client(); headers=login(client); row=detail(client)
    assert client.put('/api/admin/responses/' + row['id'], headers=headers, json=correction(row, chat_helpfulness=8)).status_code == 400


def test_partial_corrections_keep_status_and_detect_participant_writes(admin_app):
    store = admin_app.extensions['survey_store']
    draft = SurveyDraftRequest.model_validate(dict(submission_id='a'*32, version='diana-v7', revision=1,
                                                  answers={'study_arm':'A','search_goal':'P'}, waiting_answered=['search_goal'])).root
    store.save_draft(draft)
    client=admin_app.test_client(); headers=login(client); row=detail(client)
    path='/api/admin/responses/' + row['id']
    saved=client.put(path, headers=headers, json=correction(row, system_usefulness=2)).json
    assert saved['response_status']=='in_progress' and saved['submitted_at_utc']==''
    restored=store.get_draft('a'*32)
    assert restored['revision']==2 and restored['waiting_answered']==['search_goal']
    assert restored['answers']['search_goal']=='P' and restored['answers']['gender'] is None
    with pytest.raises(SurveyConflict): store.save_draft(draft)
    newer=draft.model_copy(update={'revision':3})
    store.save_draft(newer)
    assert client.put(path, headers=headers, json=correction(saved, system_usefulness=1)).status_code==409
    store.save(SurveyRequest.model_validate(versioned_payload()).root)
    assert detail(client)['correction_count']==1  # draft promotion preserves history
    assert client.put(path, headers=headers, json=correction(saved, system_usefulness=1)).status_code==409


@pytest.mark.parametrize('linked', [False, True])
def test_answer_deletion_removes_correction_history(admin_app, linked):
    if linked: seed_record(admin_app, 'diana-v7', 'A', 'a')
    else: seed(admin_app)
    client=admin_app.test_client(); headers=login(client); row=detail(client)
    client.put('/api/admin/responses/' + row['id'], headers=headers, json=correction(row, system_usefulness=4))
    assert client.delete('/api/admin/responses/' + row['id'], headers=headers, json={'confirm_id':row['participation_id']}).status_code==200
    with admin_app.extensions['survey_store'].connect() as db:
        assert db.execute('SELECT COUNT(*) FROM survey_answer_corrections').fetchone()[0]==0


def test_migration_is_additive_and_repeatable(tmp_path):
    path=str(tmp_path/'historical.sqlite3')
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE survey_responses (submission_id TEXT PRIMARY KEY,created_at TEXT NOT NULL,answers_json TEXT NOT NULL)')
        db.execute('INSERT INTO survey_responses VALUES (?,?,?)',('old','2026-01-01','{"version":"diana-v1"}'))
    SurveyStore(path); SurveyStore(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT * FROM survey_responses').fetchall()==[('old','2026-01-01','{"version":"diana-v1"}')]
        assert db.execute('SELECT COUNT(*) FROM survey_answer_corrections').fetchone()[0]==0


def test_bulk_study_deletion_preserves_standalone_test_consents_and_sessions(admin_app):
    from privacy import ConsentInput, token_hash
    privacy=admin_app.extensions['privacy_store']; store=admin_app.extensions['survey_store']
    sessions=admin_app.extensions['chat_store']; data=admin_app.extensions['admin_data']
    study_notice={'ready':True,'version':'a'*64}
    test_notice={'ready':True,'configuration_complete':True,'version':'b'*64,'purpose':'test_a'}
    privacy.accept(ConsentInput(token='a'*64,version='a'*64,accepted=True),study_notice)
    privacy.accept(ConsentInput(token='b'*64,version='b'*64,accepted=True,purpose='test_a'),test_notice)
    study_chat=sessions.create({'mode':'study'},before_save=lambda db,sid:privacy.attach('a'*64,study_notice,'chat',sid,db))
    test_chat=sessions.create({'mode':'test'},before_save=lambda db,sid:privacy.attach('b'*64,test_notice,'chat',sid,db))
    with store.connect() as db:
        db.execute('INSERT INTO privacy_consent_history VALUES (?,?,?,?)',(token_hash('b'*64),'old-test-version','{}','2026-09-14'))
    preview=data.deletion_preview()
    assert preview['active_consents']==1
    data.delete_all(preview['fingerprint'])
    assert sessions.get(study_chat) is None and sessions.get(test_chat) is not None
    with store.connect() as db:
        assert db.execute('SELECT withdrawn_at FROM privacy_consents WHERE token_hash=?',(token_hash('b'*64),)).fetchone()[0] is None
        assert db.execute('SELECT COUNT(*) FROM privacy_consent_history WHERE token_hash=?',(token_hash('b'*64),)).fetchone()[0]==1
        assert db.execute('SELECT COUNT(*) FROM privacy_links WHERE record_id=?',(test_chat,)).fetchone()[0]==1
