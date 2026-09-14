import csv
import io
import json
import zipfile

import pytest
from pydantic import ValidationError
from survey_store import V4_SURVEY_DEFINITION as SURVEY_DEFINITION, V4_SURVEY_FIELDS as SURVEY_FIELDS, SurveySubmissionV4, SurveySubmission, field_visible
from test_survey import survey_app, payload, records
from test_admin import admin_app, login


def v4_payload(**changes):
    values = {field['name']: (8 if field['kind']=='scale' else field['options'][0][0] if field['kind']=='choice' else '' if field.get('optional') else 'Werkstudent Data Science') for field in SURVEY_FIELDS}
    return dict(submission_id='c'*32, version='diana-v4', **values) | changes


def test_definition_and_api_agree_on_all_answers_and_optional_fields():
    assert SURVEY_DEFINITION['version']=='diana-v4'
    assert set(SurveySubmissionV4.model_fields)-{'version','submission_id'}=={f['name'] for f in SURVEY_FIELDS}
    for field in SURVEY_FIELDS:
        for value,_ in field.get('options',[])+field.get('nonresponse',[]):
            data=v4_payload(**{field['name']:value})
            for other in SURVEY_FIELDS:
                if not field_visible(other,data):data[other['name']]=None
            assert SurveySubmissionV4(**data)
    data=v4_payload();del data['feedback'];del data['study_field']
    assert SurveySubmissionV4(**data).feedback==''


@pytest.mark.parametrize('field',[f['name'] for f in SURVEY_FIELDS if not f.get('optional')])
def test_every_visible_question_requires_an_answer(field):
    data=v4_payload();del data[field]
    with pytest.raises(ValidationError):SurveySubmissionV4(**data)


@pytest.mark.parametrize('bad',[0,11,True,False,'8',8.5,None,'unknown'])
def test_ratings_are_strict_and_missing_reasons_are_explicit(bad):
    with pytest.raises(ValidationError):SurveySubmissionV4(**v4_payload(score_usefulness=bad))


def test_conditional_questions_cannot_be_forged_or_required_when_skipped(survey_app):
    client=survey_app.test_client()
    data=v4_payload(chat_used='no')
    assert client.post('/api/survey-responses',json=data).status_code==400
    for field in SURVEY_FIELDS:
        if not field_visible(field,data):data.pop(field['name'])
    assert client.post('/api/survey-responses',json=data).status_code==201
    assert client.post('/api/survey-responses',json=data).status_code==200
    saved=json.loads(records(survey_app)[0]['answers_json'])
    for name in ['chat_helpfulness','search_refinement','personalized_chat_usefulness']:assert saved[name] is None
    assert saved['chat_used']=='no'
    assert client.post('/api/survey-responses',json=data|{'chat_used':'yes'}).status_code==400


def test_v4_admin_export_codes_missing_and_previous_versions_remain_separate(admin_app):
    store=admin_app.extensions['survey_store']
    store.save(SurveySubmission(**payload()))
    values=v4_payload(chat_used='no', personality_customized='no', chat_helpfulness=None,
        search_refinement=None,personalized_chat_usefulness=None,score_usefulness='not_used',
        match_reasons_usefulness='not_assessable',future_use='3',feedback='=1+1')
    store.save(SurveySubmissionV4(**values))
    client=admin_app.test_client();login(client)
    data=client.get('/api/admin/responses?version=diana-v4').json
    assert data['total']==1
    detail=client.get('/api/admin/responses/'+'c'*32).json
    assert detail['definition']['version']=='diana-v4'
    assert client.get('/api/admin/responses/'+'a'*32).json['definition']['version']=='diana-v3'
    package=zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?columns=technical&format=zip').data))
    rows=list(csv.DictReader(io.StringIO(package.read('diana_numiqo.csv').decode('utf-8-sig')),delimiter=';'))
    new=next(row for row in rows if row['survey_version']=='diana-v4')
    old=next(row for row in rows if row['survey_version']=='diana-v3')
    assert new['v4_chat_used']=='0' and new['v4_chat_used_status']=='answered'
    assert new['v4_personality_customized']=='0'
    assert new['v4_score_usefulness']=='' and new['v4_score_usefulness_status']=='not_used'
    assert new['v4_match_reasons_usefulness']=='' and new['v4_match_reasons_usefulness_status']=='not_assessable'
    assert new['v4_chat_helpfulness']=='' and new['v4_chat_helpfulness_status']=='skipped'
    assert new['v4_future_use']=='3' and new['v4_future_use_status']=='answered'
    assert new['v4_feedback']=="'=1+1"
    assert new['chat_helpfulness']=='' and old['chat_helpfulness']=='8'
    assert old['v4_chat_helpfulness']=='' and old['v4_chat_helpfulness_status']=='not_asked'
    book={field['variable']:field for field in json.loads(package.read('codebook.json'))}
    assert set(new)==set(book) and None not in new
    assert book['v4_chat_used']['codes']=={'1':'Ja','0':'Nein'}
    assert book['v4_future_use']['codes']['3']=='Unentschieden'
    assert book['v4_personalized_chat_usefulness']['visible_if']=={'field':'chat_used','equals':'yes'}
    assert book['v4_personality_setup']['level']=='ordinal'
    assert book['v4_personality_customized']['level']=='nominal'


def test_v4_readable_export_handles_null_and_nonresponse_without_mislabeling(survey_app):
    data=v4_payload(score_usefulness='not_used',feedback='@TEST')
    survey_app.extensions['survey_store'].save(SurveySubmissionV4(**data))
    stream=io.StringIO();survey_app.extensions['survey_store'].export_csv(stream)
    row=next(csv.DictReader(io.StringIO(stream.getvalue()),delimiter=';'))
    assert row['v4_score_nutzen_antwortstatus']=='not_used'
    assert row['v4_verbesserungsvorschlaege_freitext']=="'@TEST"
