"""Scale changes remain separate from historical measurements and autosave safely."""
import csv
import io

import pytest
from pydantic import ValidationError
from survey_store import SURVEY_FIELDS, SurveySubmissionV5
from test_survey import survey_app
from test_admin import admin_app, login
from test_survey_v4 import v4_payload


def v5_payload(**changes):
    answers = {f['name']: 8 if f['kind']=='scale' else f['options'][0][0] if f['kind']=='choice' else '' if f.get('optional') else 'Data Science' for f in SURVEY_FIELDS}
    return dict(submission_id='e'*32,version='diana-v5',**answers) | changes


def test_all_ratings_use_ten_points_and_chat_self_report_is_removed():
    ratings=[f for f in SURVEY_FIELDS if f['kind']=='scale']
    assert len(ratings)==13
    assert 'chat_used' not in SurveySubmissionV5.model_fields
    assert not any('visibleIf' in f for f in SURVEY_FIELDS)
    for field in ratings:
        for value in [1,10,*[code for code,_ in field.get('nonresponse',[])]]:
            SurveySubmissionV5(**v5_payload(**{field['name']:value}))
        for value in [0,11,'4',True,5.5]:
            with pytest.raises(ValidationError):
                SurveySubmissionV5(**v5_payload(**{field['name']:value}))
    with pytest.raises(ValidationError):
        SurveySubmissionV5(**v5_payload(chat_used='yes'))


def test_new_scale_autosaves_and_completes_without_chat_question(survey_app):
    client=survey_app.test_client(); full=v5_payload()
    draft=dict(submission_id=full['submission_id'],version='diana-v5',revision=1,answers={'personality_setup':10})
    assert client.put('/api/survey-drafts',json=draft).status_code==200
    assert client.get('/api/survey-drafts/'+full['submission_id']).json['draft']['answers']['personality_setup']==10
    assert client.put('/api/survey-drafts',json=draft|{'revision':2,'answers':{'personality_setup':'4'}}).status_code==400
    assert client.post('/api/survey-responses',json=full).status_code==201
    assert client.put('/api/survey-drafts',json=draft|{'revision':3}).json['completed'] is True


def test_v4_and_v5_exports_keep_distinct_scales_and_codebooks(admin_app):
    client=admin_app.test_client()
    assert client.post('/api/survey-responses',json=v4_payload(personality_setup='4')).status_code==201
    assert client.post('/api/survey-responses',json=v5_payload(personality_setup=10)).status_code==201
    login(client)
    assert client.get('/api/admin/responses?version=diana-v5').json['total']==1
    rows=list(csv.DictReader(io.StringIO(client.get('/api/admin/export').data.decode('utf-8-sig')),delimiter=';'))
    old=next(row for row in rows if row['survey_version']=='diana-v4')
    new=next(row for row in rows if row['survey_version']=='diana-v5')
    assert old['v4_personality_setup']=='4' and old['v5_personality_setup']==''
    assert new['v5_personality_setup']=='10' and new['v4_personality_setup']==''
    assert new['v4_chat_used_status']=='not_asked' and 'v5_chat_used' not in new
    assert client.get('/api/admin/responses/'+'c'*32).json['definition']['version']=='diana-v4'
    assert client.get('/api/admin/responses/'+'e'*32).json['definition']['version']=='diana-v5'
