from copy import deepcopy
import pytest
from test_admin import admin_app, login
from test_survey_v7 import versioned_payload
from survey_store import SurveySubmissionV7
from survey_analytics import analytics


def record(arm='B', value=8, version='diana-v7', status='completed', experiment='diana-ab-v1', sid='a'):
    answers=versioned_payload(version,arm)
    answers['system_usefulness']=value
    return dict(id=sid,participation_id=sid,answers=answers,study_arm=arm,
                survey_version=version,response_status=status,experiment_id=experiment)


def question(data,name,cohort=0):
    return next(q for group in data['cohorts'][cohort]['categories'] for q in group['questions'] if q['name']==name)


def test_valid_denominators_missing_answers_and_ordinal_statistics():
    rows=[record('A',2,sid='a'),record('B',8,sid='b'),record('B','not_assessable',sid='c'),record('B',None,status='in_progress',sid='d')]
    data=analytics(rows,'diana-v7')
    q=question(data,'system_usefulness')
    assert data['total']==4 and data['completed']==3 and data['in_progress']==1
    assert q['overall']['mean']==5 and q['overall']['median']==5 and q['overall']['n']==2
    assert q['groups']['B']['n']==1 and q['groups']['B']['distribution'][7]['percent']==100
    assert q['overall']['statuses']=={'answered':2,'not_assessable':1,'unanswered':1}
    score=question(data,'score_usefulness')
    assert score['groups']['A']['n']==0 and score['groups']['A']['mean'] is None
    assert score['groups']['A']['statuses']=={'skipped':1}
    assert question(data,'search_effort')['reverse']


def test_versions_experiments_and_historical_branching_stay_separate():
    old=record('B',4,'diana-v6',experiment='diana-bc-v1')
    old['study_arm']='A'  # admin mapping; original answers remain B
    data=analytics([old],'diana-v6')
    assert question(data,'personality_setup')['groups']['A']['statuses']=={'skipped':1}
    rows=[record(experiment='old'),record(experiment='new')]
    assert len(analytics(rows,'diana-v7')['cohorts'])==2
    assert analytics(rows,'')['cohorts']==[]
    assert question(analytics([],'diana-v7'),'system_usefulness')['overall']['mean'] is None


def test_status_selection_matches_charts_csv_and_zip_with_partial_answers(admin_app):
    import csv
    import io
    import zipfile
    from survey_store import SurveyDraftV7
    store=admin_app.extensions['survey_store']
    store.save(SurveySubmissionV7(**versioned_payload()))
    for sid,value in [('b',2),('c',None)]:
        store.save_draft(SurveyDraftV7(submission_id=sid*32,version='diana-v7',revision=1,
            answers={'study_arm':'A','system_usefulness':value}))
    client=admin_app.test_client();login(client)
    for status,count,mean,valid in [('completed',1,8,1),('',3,5,2),('in_progress',2,2,1)]:
        query='version=diana-v7&status='+status
        data=client.get('/api/admin/analytics?'+query).json
        assert data['total']==count
        summary=question(data,'system_usefulness')['overall']
        assert summary['mean']==mean and summary['n']==valid
        raw=client.get('/api/admin/export?format=csv&'+query).data
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'))
        assert len(rows)==count
        assert sum(row['v7_system_usefulness']!='' for row in rows)==valid
        if status:assert all(row['response_status']==status for row in rows)
        package=zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?format=zip&'+query).data))
        assert package.read('diana_numiqo.csv')==raw


def test_freetext_limited_and_zero_choice_is_not_missing():
    rows=[record(sid=str(i)) for i in range(60)]
    for row in rows:
        row['answers']['feedback']='<script>alert(1)</script>'
        row['answers']['search_refinement']='no'
    data=analytics(rows,'diana-v7')
    q=question(data,'feedback')['overall']
    assert q['n']==60 and len(q['texts'])==50 and q['remaining_texts']==10
    assert question(data,'search_refinement')['overall']['distribution'][1]['count']==60


def test_analytics_protected_all_pages_filters_and_deletion(admin_app):
    client=admin_app.test_client()
    assert client.get('/api/admin/analytics?version=diana-v7').status_code==401
    store=admin_app.extensions['survey_store']
    for i in range(30):
        store.save(SurveySubmissionV7(**versioned_payload(submission_id=f'{i:032x}')))
    csrf=login(client)
    result=client.get('/api/admin/analytics?version=diana-v7&status=completed')
    assert result.status_code==200 and result.headers['Cache-Control']=='no-store'
    assert question(result.json,'system_usefulness')['overall']['n']==30
    assert client.get('/api/admin/analytics?version=bad').status_code==400
    assert client.get('/api/admin/analytics?version=diana-v7&arm=B').json['total']==0
    sid=f'{0:032x}'
    assert client.delete('/api/admin/responses/'+sid,json={'confirm_id':sid},headers=csrf).status_code==200
    assert client.get('/api/admin/analytics?version=diana-v7').json['total']==29


def test_bulk_deletion_requires_auth_csrf_confirmation_and_fresh_snapshot(admin_app):
    client=admin_app.test_client()
    assert client.get('/api/admin/deletion-preview').status_code==401
    assert client.delete('/api/admin/responses').status_code==401
    csrf=login(client)
    store=admin_app.extensions['survey_store']
    store.save(SurveySubmissionV7(**versioned_payload()))
    preview=client.get('/api/admin/deletion-preview').json
    body=dict(confirmation='ALLE TEILNAHMEN LÖSCHEN',fingerprint=preview['fingerprint'])
    assert client.delete('/api/admin/responses',json=body).status_code==403
    assert client.delete('/api/admin/responses',json=body|{'confirmation':'yes'},headers=csrf).status_code==400
    store.save(SurveySubmissionV7(**versioned_payload(submission_id='b'*32)))
    assert client.delete('/api/admin/responses',json=body,headers=csrf).status_code==409
    assert client.get('/api/admin/responses').json['total']==2
    body['fingerprint']=client.get('/api/admin/deletion-preview').json['fingerprint']
    assert client.delete('/api/admin/responses',json=body,headers=csrf).status_code==200
    assert client.get('/api/admin/responses').json['total']==0
    assert question(client.get('/api/admin/analytics?version=diana-v7').json,'system_usefulness')['overall']['n']==0


def test_bulk_revokes_old_identities_without_closing_study(admin_app):
    from privacy import ConsentInput, ConsentRequired, token_hash
    privacy=admin_app.extensions['privacy_store'];store=admin_app.extensions['survey_store']
    notice={'ready':True,'version':'a'*64}
    privacy.accept(ConsentInput(token='c'*64,version='a'*64,accepted=True),notice)
    def link(db,record_id):
        privacy.attach('c'*64,notice,'survey',record_id,db)
        admin_app.extensions['study_releases'].mark_run(token_hash('c'*64),db)
        admin_app.extensions['study_releases'].capture_response(token_hash('c'*64),record_id,db)
    store.save(SurveySubmissionV7(**versioned_payload()),before_save=link)
    data=admin_app.extensions['admin_data']
    snapshot=data.deletion_preview()
    assert snapshot['active_consents']==1
    data.delete_all(snapshot['fingerprint'])
    assert not privacy.closed()
    with store.connect() as db:
        for table in ['survey_responses','survey_drafts','privacy_links','privacy_consent_history','survey_response_metadata','study_runs','study_assignments']:
            assert db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]==0
        assert db.execute('SELECT withdrawn_at FROM privacy_consents').fetchone()[0]
        with pytest.raises(ConsentRequired):privacy.attach('c'*64,notice,'survey','late',db)
    privacy.accept(ConsentInput(token='d'*64,version='a'*64,accepted=True),notice)
    assert data.deletion_preview()['active_consents']==1


def test_v1_five_point_scale_and_v2_questions_are_preserved():
    row=record(version='diana-v7');row['survey_version']='diana-v1'
    row['answers']={'chat_helpfulness':4,'added_value':'same','future_preference':'undecided','feedback':''}
    data=analytics([row],'diana-v1')
    q=question(data,'chat_helpfulness')
    assert len(q['overall']['distribution'])==5 and q['scale']['max']==5
    assert q['overall']['mean']==4
    q=analytics([],'diana-v2')['cohorts'][0]['categories']
    assert not any(item['name']=='score_usefulness' for cat in q for item in cat['questions'])
