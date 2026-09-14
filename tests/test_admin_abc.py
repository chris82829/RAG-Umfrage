"""Current A/B/C and historical A/B remain distinct in administration."""
import csv
import io
import json
import zipfile

import pytest

from test_admin import admin_app, login
from test_admin_analytics import question
from test_admin_corrections import correction
from test_survey_v7 import seed_record, versioned_payload
from survey_store import SurveyDraftRequest


def read_rows(raw):
    return list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';'))


def test_v8_filter_chart_export_and_codebook_keep_three_groups_and_history(admin_app):
    for version, arm, sid in [('diana-v8','A','a'),('diana-v8','B','b'),('diana-v8','C','c'),
                              ('diana-v7','B','d'),('diana-v6','C','e')]:
        seed_record(admin_app, version, arm, sid)
    client=admin_app.test_client();login(client)
    assert client.get('/api/admin/responses?arm=C').json['total']==1
    assert client.get('/api/admin/responses?version=diana-v8').json['total']==3
    result=client.get('/api/admin/analytics?version=diana-v8').json
    assert result['cohorts'][0]['experiment_id']=='diana-abc-v1'
    assert result['cohorts'][0]['arms']=={'A':1,'B':1,'C':1}
    assert question(result,'system_usefulness')['overall']['n']==3
    score=question(result,'score_usefulness')
    assert score['groups']['A']['statuses']=={'skipped':1}
    assert score['groups']['B']['n']==score['groups']['C']['n']==1
    setup=question(result,'personality_setup')
    assert setup['groups']['B']['statuses']=={'skipped':1} and setup['groups']['C']['n']==1
    template=question(result,'template_selection_ease')
    assert template['groups']['B']['n']==1 and template['groups']['C']['statuses']=={'skipped':1}
    rows=read_rows(client.get('/api/admin/export').data)
    current={row['studiengruppe']:row for row in rows if row['fragebogen_version']=='diana-v8'}
    assert {arm:row['v8_studiengruppe_originalcode'] for arm,row in current.items()}=={'A':'0','B':'1','C':'2'}
    assert current['B']['v8_ki_vorlagenauswahl_einfachheit']=='8'
    assert current['B']['v8_ki_einrichten_einfachheit_antwortstatus']=='skipped'
    assert current['C']['v8_ki_einrichten_einfachheit']=='8'
    assert current['C']['v8_ki_vorlagenauswahl_einfachheit_antwortstatus']=='skipped'
    historical=[row for row in rows if row['fragebogen_version']!='diana-v8']
    assert all(row['studiengruppe']=='B' and row['v8_studiengruppe_originalcode']=='' for row in historical)
    assert {row['experiment_id'] for row in historical}=={'diana-ab-v1','diana-bc-v1'}
    archive=zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?format=zip').data))
    book={field['variable']:field for field in json.loads(archive.read('codebook.json'))}
    assert book['v8_studiengruppe_originalcode']['original_codes']=={'0':'A','1':'B','2':'C'}
    assert book['v6_studiengruppe_originalcode']['original_codes']=={'0':'B','1':'C'}
    assert book['v7_studiengruppe_originalcode']['original_codes']=={'0':'A','1':'B'}
    assert book['v8_score_nutzen']['visible_if_export']=={'field':'v8_studiengruppe_originalcode','in':['B','C']}
    assert 'Historisches B' in book['studiengruppe']['notes']
    assert 'diana-abc-v1' in archive.read('README.txt').decode()


@pytest.mark.parametrize('arm',['A','B','C'])
def test_v8_answers_edit_without_reassigning_or_changing_version(admin_app,arm):
    seed_record(admin_app,'diana-v8',arm,'a')
    client=admin_app.test_client();headers=login(client);path='/api/admin/responses/'+'a'*32
    row=client.get(path).json
    assert row['definition']['version']=='diana-v8' and row['study_arm']==arm
    result=client.put(path,headers=headers,json=correction(row,system_usefulness=3))
    assert result.status_code==200
    assert result.json['answers']['system_usefulness']==3
    assert result.json['experiment_id']=='diana-abc-v1'
    changed_arm='B' if arm=='C' else 'C'
    rejected=client.put(path,headers=headers,json=correction(result.json,study_arm=changed_arm))
    assert rejected.status_code==400
    assert client.get(path).json['study_arm']==arm


def test_v8_incomplete_c_answers_available_in_charts_and_download(admin_app):
    store=admin_app.extensions['survey_store']
    store.save_draft(SurveyDraftRequest.model_validate(dict(version='diana-v8',submission_id='a'*32,
        revision=1,answers={'study_arm':'C','system_usefulness':4})).root)
    client=admin_app.test_client();login(client)
    query='version=diana-v8&arm=C&status=in_progress'
    result=client.get('/api/admin/analytics?'+query)
    assert result.status_code==200 and result.json['in_progress']==1
    assert question(result.json,'system_usefulness')['groups']['C']['mean']==4
    row=read_rows(client.get('/api/admin/export?'+query).data)[0]
    assert row['v8_system_nutzen']=='4' and row['teilnahme_status']=='in_progress'
