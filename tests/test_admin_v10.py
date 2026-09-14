"""Short V10 questionnaire stays distinct from unchanged historical V9."""
import io
import json
import zipfile

from survey_store import SurveyDraftRequest
from test_admin import admin_app, login
from test_admin_analytics import question
from test_admin_conference import csv_rows
from test_admin_corrections import correction
from test_survey_v7 import seed_record

REMOVED={'search_ease','express_search_needs','adapt_search_ease','template_selection_ease','personality_setup'}


def fields(definition):
    return {field['name'] for group in [definition['demographics'],*definition['categories']] for field in group['fields']}


def test_v10_export_definition_charts_and_editing_keep_v9_intact(admin_app):
    for version,arm,sid in [('diana-v10','A','a'),('diana-v10','B','b'),('diana-v10','C','c'),('diana-v9','C','d')]:
        seed_record(admin_app,version,arm,sid)
    client=admin_app.test_client();headers=login(client)
    listing=client.get('/api/admin/responses?version=diana-v10').json
    assert listing['total']==3 and listing['definition']['version']=='diana-v10'
    data=client.get('/api/admin/analytics?version=diana-v10').json
    assert data['cohorts'][0]['experiment_id']=='diana-abc-v3'
    assert data['cohorts'][0]['arms']=={'A':1,'B':1,'C':1}
    assert all(item['n']==1 for item in question(data,'system_usefulness')['groups'].values())
    assert REMOVED.isdisjoint({q['name'] for cat in data['cohorts'][0]['categories'] for q in cat['questions']})
    assert question(client.get('/api/admin/analytics?version=diana-v9').json,'personality_setup')['overall']['n']==1
    current=client.get('/api/admin/responses/'+'a'*32).json
    legacy=client.get('/api/admin/responses/'+'d'*32).json
    assert REMOVED.isdisjoint(fields(current['definition']))
    assert REMOVED <= fields(legacy['definition'])
    assert legacy['definition']['version']=='diana-v9' and legacy['experiment_id']=='diana-abc-v2'
    updated=client.put('/api/admin/responses/'+legacy['id'],headers=headers,json=correction(legacy,personality_setup=4))
    assert updated.status_code==200 and updated.json['answers']['personality_setup']==4
    updated_current=client.put('/api/admin/responses/'+current['id'],headers=headers,json=correction(current,system_usefulness=9))
    assert updated_current.status_code==200
    assert client.put('/api/admin/responses/'+current['id'],headers=headers,json=correction(updated_current.json,study_arm='C')).status_code==400
    assert client.put('/api/admin/responses/'+current['id'],headers=headers,json=correction(updated_current.json,personality_setup=4)).status_code==400
    archive=zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?format=zip').data))
    rows=csv_rows(archive.read('diana_numiqo.csv'))
    v10=[row for row in rows if row['fragebogen_version']=='diana-v10']
    assert {row['v10_studiengruppe_originalcode'] for row in v10}=={'0','1','2'}
    assert {row['v10_system_nutzen'] for row in v10}=={'8','9'}
    assert all(row['v9_system_nutzen']=='' for row in v10)
    book={field['technical_variable']:field for field in json.loads(archive.read('codebook.json'))}
    assert all('v10_'+name not in book and 'v9_'+name in book for name in REMOVED)
    assert book['v10_system_usefulness']['variable']=='v10_system_nutzen'
    assert book['v10_chat_helpfulness']['variable']=='v10_chat_hilfe_suchwuensche'
    assert book['v10_study_arm']['original_codes']=={'0':'A','1':'B','2':'C'}
    assert 'diana-abc-v3' in archive.read('README.txt').decode()


def test_flow_reports_separate_v9_v10_valid_primary_counts_including_drafts(admin_app):
    seed_record(admin_app,'diana-v10','C','a');seed_record(admin_app,'diana-v9','C','b')
    store=admin_app.extensions['survey_store']
    with store.connect() as db:db.execute('DELETE FROM survey_responses WHERE submission_id=?',('a'*32,))
    store.save_draft(SurveyDraftRequest.model_validate(dict(version='diana-v10',submission_id='a'*32,revision=1,
        answers={'study_arm':'C','system_usefulness':5})).root)
    client=admin_app.test_client();login(client)
    response=client.get('/api/admin/analytics?version=diana-v10&status=in_progress')
    assert response.status_code==200 and question(response.json,'system_usefulness')['overall']['mean']==5
    archive=zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?format=zip&version=diana-v10&status=in_progress').data))
    flow={row['experiment_id']:row for row in csv_rows(archive.read('teilnahmefluss.csv'))}
    assert flow['diana-abc-v3']['primaerwert_v10_gueltig_anzahl']=='1'
    assert flow['diana-abc-v3']['primaerwert_v9_gueltig_anzahl']=='0'
    assert flow['diana-abc-v3']['abgeschlossen_anzahl']=='0'
    assert flow['diana-abc-v2']['primaerwert_v10_gueltig_anzahl']=='0'
    assert flow['diana-abc-v2']['primaerwert_v9_gueltig_anzahl']=='1'
    assert flow['diana-abc-v2']['abgeschlossen_anzahl']=='1'
