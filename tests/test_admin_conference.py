"""V9 reporting preserves historical comparisons and observes real denominators."""
import csv
import io
import json
import zipfile

from privacy import token_hash
from study_metrics import empty_metrics
from survey_store import SurveyDraftRequest, SurveyRequest
from test_admin import admin_app, login
from test_admin_analytics import question
from test_admin_corrections import correction
from test_survey_v7 import seed_record, versioned_payload


def csv_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig')),delimiter=';'))


def test_presentation_metadata_uses_assignment_when_old_and_new_cohorts_share_release(admin_app):
    releases=admin_app.extensions['study_releases']
    current=releases.manifest
    old_id='f'*64
    old_manifest={'openai_model':current['openai_model'], 'reasoning_effort':current['reasoning_effort'],
                  'neutral_presentation':'historical-presentation-v1'}
    cases=[('diana-v9','A','a',False),('diana-v9','B','b',False),('diana-v9','C','c',False),
           ('diana-v8','A','d',True),('diana-v8','B','e',False),('diana-v8','C','f',False),
           ('diana-v7','A','0',True),('diana-v7','B','1',False),
           ('diana-v6','B','2',True),('diana-v6','C','3',False)]
    store=admin_app.extensions['survey_store']
    for version,arm,identifier,_ in cases:
        seed_record(admin_app,version,arm,identifier)
    with store.connect() as db:
        db.execute('INSERT INTO study_releases VALUES (?,?,?)',
                   (old_id,'2026-09-10T12:00:00+00:00',json.dumps(old_manifest)))
        for _,_,identifier,_ in cases:
            db.execute('INSERT INTO survey_response_metadata VALUES (?,?)',
                       (identifier*32,json.dumps({'release_ids':[old_id,releases.release_id]})))
    client=admin_app.test_client();login(client)
    exported={(row['survey_version'],row['study_arm']):row
              for row in csv_rows(client.get('/api/admin/export?columns=technical').data)}
    for version,_,identifier,legacy_neutral in cases:
        row=client.get('/api/admin/responses/'+identifier*32).json
        expected=sorted([old_manifest['neutral_presentation'],current[
            'historical_neutral_presentation' if legacy_neutral else 'presentation_policy']])
        assert row['presentation_versions']==expected
        assert exported[(version,row['study_arm'])]['presentation_versions']=='|'.join(expected)
    assert releases.all()[old_id]==old_manifest


def test_current_release_does_not_infer_treatment_without_assignment(admin_app):
    seed_record(admin_app,'diana-v9','A','a')
    with admin_app.extensions['survey_store'].connect() as db:
        db.execute('DELETE FROM study_assignments WHERE token_hash=?',(token_hash('a'*64),))
        db.execute('INSERT INTO survey_response_metadata VALUES (?,?)',
                   ('a'*32,json.dumps({'release_ids':[admin_app.extensions['study_releases'].release_id]})))
    assert admin_app.extensions['admin_data'].records()[0]['presentation_versions']==['undocumented']


def test_v9_identical_outcomes_coded_and_v8_preserved(admin_app):
    for version,arm,sid in [('diana-v9','A','a'),('diana-v9','B','b'),('diana-v9','C','c'),('diana-v8','A','d')]:
        seed_record(admin_app,version,arm,sid)
    client=admin_app.test_client();headers=login(client)
    data=client.get('/api/admin/analytics?version=diana-v9').json
    assert data['cohorts'][0]['experiment_id']=='diana-abc-v2'
    assert data['cohorts'][0]['arms']=={'A':1,'B':1,'C':1}
    assert all(result['n']==1 for result in question(data,'score_usefulness')['groups'].values())
    assert question(client.get('/api/admin/analytics?version=diana-v8').json,'score_usefulness')['overall']['statuses']=={'skipped':1}
    row=client.get('/api/admin/responses/'+'a'*32).json
    assert row['definition']['version']=='diana-v9'
    changed=client.put('/api/admin/responses/'+row['id'],headers=headers,json=correction(row,score_usefulness=9))
    assert changed.status_code==200
    assert client.put('/api/admin/responses/'+row['id'],headers=headers,json=correction(changed.json,study_arm='C')).status_code==400
    rows=csv_rows(client.get('/api/admin/export?version=diana-v9').data)
    assert {row['v9_studiengruppe_originalcode'] for row in rows}=={'0','1','2'}
    assert all(row['v9_system_nutzen']=='8' for row in rows)
    assert all(row['v8_system_nutzen']=='' for row in rows)
    archive=zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?format=zip').data))
    book={field['variable']:field for field in json.loads(archive.read('codebook.json'))}
    assert book['v9_score_nutzen']['visible_if'] is None
    assert book['v9_jobportal_vorerfahrung']['original_codes']['0']=='never'
    assert book['suchen_dauer_gesamt_ms']['unit']=='ms'
    assert 'überlappen' in book['chatnachrichten_dauer_gesamt_ms']['notes']


def test_operation_export_keeps_frozen_completion_and_missing_history(admin_app):
    seed_record(admin_app,'diana-v9','C','a');seed_record(admin_app,'diana-v8','B','b')
    metrics=admin_app.extensions['operation_metrics']
    store=admin_app.extensions['survey_store'];digest=token_hash('a'*64)
    with store.connect() as db:
        metrics.record_operation(digest,'search',True,200,db)
        frozen=metrics.snapshot(digest,db)
        db.execute('INSERT INTO survey_response_metadata VALUES (?,?)',('a'*32,json.dumps({'release_ids':[],'operation_metrics':frozen})))
        metrics.record_operation(digest,'search',False,300,db)
    client=admin_app.test_client();login(client)
    rows={row['fragebogen_version']:row for row in csv_rows(client.get('/api/admin/export').data)}
    assert rows['diana-v9']['suchen_erfolgreich_anzahl']=='1'
    assert rows['diana-v9']['suchen_fehlgeschlagen_anzahl']=='0'
    assert rows['diana-v9']['suchen_dauer_gesamt_ms']=='200'
    assert rows['diana-v8']['nutzung_erfassungsversion']=='0'
    assert rows['diana-v8']['suchen_erfolgreich_anzahl']==''
    assert client.get('/api/admin/responses/'+'a'*32).json['operation_metrics']==frozen
    client.delete('/api/admin/responses/'+'a'*32,json={'confirm_id':client.get('/api/admin/responses/'+'a'*32).json['participation_id']},headers=login(client))
    with store.connect() as db:assert metrics.snapshot(digest,db)==empty_metrics()


def test_unfiltered_flow_counts_starts_and_partial_primary_without_duplicating_people(admin_app):
    for version,arm,sid in [('diana-v9','A','a'),('diana-v9','B','b'),('diana-v9','C','c'),('diana-v8','B','d')]:
        seed_record(admin_app,version,arm,sid)
    store=admin_app.extensions['survey_store']
    with store.connect() as db:
        db.execute('DELETE FROM survey_responses WHERE submission_id IN (?,?)',('a'*32,'c'*32))
    store.save_draft(SurveyDraftRequest.model_validate(dict(submission_id='c'*32,version='diana-v9',revision=1,
        answers={'study_arm':'C','system_usefulness':5})).root)
    privacy=admin_app.extensions['privacy_store']
    store.save(SurveyRequest.model_validate(versioned_payload('diana-v9','B','e'*32)).root,
        before_save=lambda db,sid:privacy.attach('b'*64,{'ready':True,'version':'a'*64},'survey',sid,db))
    client=admin_app.test_client();login(client)
    archive=zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?format=zip&version=diana-v9&arm=B&status=completed').data))
    assert len(csv_rows(archive.read('diana_numiqo.csv')))==2
    flow=csv_rows(archive.read('teilnahmefluss.csv'))
    assert len(flow)==4
    current={row['studiengruppe']:row for row in flow if row['experiment_id']=='diana-abc-v2'}
    assert current['A']['zugeteilt_anzahl']=='1' and current['A']['antworten_gespeichert_anzahl']=='0'
    assert current['B']['abgeschlossen_anzahl']=='1'
    assert current['C']['abgeschlossen_anzahl']=='0' and current['C']['primaerwert_v9_gueltig_anzahl']=='1'
    assert all(row['umfang']=='ungefilterter_aktiver_studienbestand' for row in flow)
    assert 'unabhängig von den Auswahlfiltern' in archive.read('README.txt').decode()
    admin_app.extensions['privacy_store'].withdraw('a'*64)
    assert len(admin_app.extensions['admin_data'].participation_flow())==3
