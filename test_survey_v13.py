"""V14 continuation of the V13 framework mapping, single active survey, seven-point data, and honest scale aggregation."""
import csv
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError
from admin_store import AdminSurveyData
from survey_analytics import analytics, construct_value
from survey_store import SURVEY_VERSION, SURVEY_FIELDS, SURVEY_DEFINITION, SurveyStore, SurveyRequest, SurveyDraftRequest, field_visible


def answers(arm='A'):
    values={'version':SURVEY_VERSION,'study_arm':arm}
    for field in SURVEY_FIELDS:
        name=field['name']
        if name=='study_arm':continue
        if not field_visible(field,values):values[name]=None
        elif field['kind']=='scale':values[name]=7
        elif field['kind']=='choice':values[name]=field['options'][0][0]
        else:values[name]='' if field.get('optional') else 'Data Science Werkstudent'
    return values


def record(values, identity='p1', arm='A'):
    return dict(id=identity,participation_id=identity,survey_version=SURVEY_VERSION,answers=values,
        submitted_at_utc='',study_release_ids=[],openai_models=[],reasoning_efforts=[],response_status='completed',
        last_saved_at_utc='',study_arm=arm,experiment_id='diana-abc-v7',assigned_at_utc='',prior_exposure=0,
        presentation_versions=['ranked_insights'])


class SurveyV13Tests(unittest.TestCase):
    def test_framework_sources_counts_and_scale_are_consistent_for_all_arms(self):
        self.assertEqual(SURVEY_VERSION,'diana-v14')
        scales=[f for f in SURVEY_FIELDS if f['kind']=='scale']
        self.assertEqual(len(scales),20)
        self.assertEqual(sum(f['framework'] in ('ResQue','CRS-Que') for f in scales),14)
        self.assertEqual(sum(f['framework']=='DIANA' for f in scales),4)
        for f in scales:
            self.assertEqual(f['scale']['max'],7)
            self.assertEqual(len(f['scale']['labels']),7)
            self.assertIn('source_item',f)
            self.assertEqual(f['nonresponse'],[['not_assessable','Kann ich nicht beurteilen']])
        for arm,count in [('A',26),('B',26),('C',26)]:
            self.assertEqual(sum(not f.get('retired') and not f.get('systemProvided') and field_visible(f,{'study_arm':arm}) for f in SURVEY_FIELDS),count)
            SurveyRequest.model_validate(dict(submission_id='a'*32,**answers(arm)))

    def test_availability_control_has_schema_export_and_no_construct_membership(self):
        field = next(f for f in SURVEY_FIELDS if f['name']=='catalog_availability')
        self.assertEqual(field['item_type'], 'control_variable')
        self.assertTrue(all(field['name'] not in c['items'] for c in SURVEY_DEFINITION['constructs']))
        book = {r['technical_variable']:r for r in object.__new__(AdminSurveyData).codebook()}
        self.assertEqual(book['v14_catalog_availability']['item_type'], 'control_variable')
        with tempfile.TemporaryDirectory() as directory:
            store = SurveyStore(Path(directory)/'test.db')
            with store.connect() as db:
                self.assertIn('v14_catalog_availability', {r[1] for r in db.execute('pragma table_xinfo(survey_responses)')})
            values=answers('C')
            values['catalog_availability']=3
            store.save(SurveyRequest.model_validate(dict(submission_id='c'*32,**values)).root)
            with store.connect() as db:
                self.assertEqual(db.execute('select v14_catalog_availability from survey_responses').fetchone()[0],3)

    def test_existing_wording_preserved_new_items_order_and_trust_two_items(self):
        old=json.loads(Path(__file__).with_name('survey_definition_v13.json').read_text())
        current={f['name']:f for f in SURVEY_FIELDS}
        for group in [old['demographics'],*old['categories']]:
            for field in group['fields']:
                self.assertEqual(current[field['name']]['kind'],field['kind'])
                self.assertEqual(current[field['name']]['construct'],field['construct'])
        names=[f['name'] for f in SURVEY_FIELDS]
        self.assertTrue(current['previous_participation']['retired'])
        self.assertTrue(current['personality_customized']['retired'])
        self.assertTrue(current['personality_customized']['optional'])
        self.assertTrue(all('DIANA' not in f['title'] for f in SURVEY_FIELDS if not f.get('retired')))
        self.assertEqual(current['intention_reuse']['title'],'So ein System werde ich bei einer weiteren Jobsuche wieder nutzen.')
        self.assertEqual(names[names.index('usefulness_suggestions')+1:names.index('usefulness_suggestions')+3],['trust_fit','trust_credibility'])
        self.assertEqual(names[names.index('dialogue_attentiveness')+1],'perceived_character')
        trust=next(c for c in SURVEY_DEFINITION['constructs'] if c['id']=='trust')
        self.assertEqual(construct_value({'trust_fit':2,'trust_credibility':6},trust),4)
        self.assertIsNone(construct_value({'trust_fit':2,'trust_credibility':'not_assessable'},trust))
        book={r['technical_variable']:r for r in object.__new__(AdminSurveyData).codebook()}
        self.assertEqual(book['v14_trust_fit']['item_type'],'multi_item')
        self.assertEqual(book['v14_perceived_character']['item_type'],'single_item')
        self.assertEqual(book['v14_trust_mean']['items'],['trust_fit','trust_credibility'])

    def test_all_item_bounds_and_c_only_item_are_enforced(self):
        for field in (f for f in SURVEY_FIELDS if f['kind']=='scale'):
            for value in (0,8,10,True,2.5):
                with self.subTest(field=field['name'],value=value),self.assertRaises(ValidationError):
                    SurveyRequest.model_validate(dict(submission_id='a'*32,**{**answers(),field['name']:value}))
            SurveyRequest.model_validate(dict(submission_id='a'*32,**{**answers(),field['name']:'not_assessable'}))
        with self.assertRaises(ValidationError):
            SurveyRequest.model_validate(dict(submission_id='a'*32,**{**answers(),'personality_customized':'yes'}))

    def test_sql_columns_idempotence_nulls_and_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            store=SurveyStore(Path(directory)/'test.db');SurveyStore(store.path)
            draft=SurveyDraftRequest.model_validate(dict(submission_id='a'*32,version=SURVEY_VERSION,revision=1,
                answers=dict(study_arm='A',usefulness_ideal=5,control_preferences='not_assessable'))).root
            store.save_draft(draft)
            with store.connect() as db:
                names={r[1] for r in db.execute('PRAGMA table_xinfo(survey_drafts)')}
                self.assertTrue(all('v14_'+f['name'] in names for f in SURVEY_FIELDS if f['kind']=='scale'))
                row=db.execute('SELECT * FROM survey_drafts').fetchone()
                self.assertEqual(row['v14_usefulness_ideal'],5);self.assertIsNone(row['v14_control_preferences'])
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute("UPDATE survey_drafts SET answers_json=json_set(answers_json,'$.usefulness_ideal',8)")
            submitted=SurveyRequest.model_validate(dict(submission_id='b'*32,**answers())).root
            store.save(submitted)
            self.assertEqual(store.get_draft('b'*32),dict(completed=True,version=SURVEY_VERSION))
            stream=io.StringIO();store.export_csv(stream)
            self.assertIn('v14_nutzen_mittelwert',stream.getvalue())
            self.assertNotIn('v12_',stream.getvalue())

    def test_construct_means_and_group_counts_use_complete_cases_without_imputation(self):
        construct=SURVEY_DEFINITION['constructs'][0]
        good={**answers(),**dict(zip(construct['items'],(1,4,7)))}
        self.assertEqual(construct_value(good,construct),4)
        missing={**good,construct['items'][0]:'not_assessable'}
        self.assertIsNone(construct_value(missing,construct))
        data=analytics([record(good),record(missing,'p2','B')],SURVEY_VERSION)
        result=data['cohorts'][0]['constructs'][0]
        self.assertEqual(result['overall'],dict(total=2,n=1,missing=1,mean=4,median=4))
        self.assertEqual(result['groups']['B']['n'],0)
        self.assertIsNone(result['groups']['B']['mean'])
        self.assertNotIn('grand_total',data)
        fields={q['name']:q for c in data['cohorts'][0]['categories'] for q in c['questions']}
        self.assertEqual(fields['control_preferences']['framework'],'CRS-Que')
        self.assertTrue(fields['study_effort']['reverse'])

    def test_current_csv_and_codebook_have_no_historical_columns_and_record_sources(self):
        admin=object.__new__(AdminSurveyData)
        book={r['technical_variable']:r for r in admin.codebook()}
        self.assertIn('v14_usefulness_mean',book)
        self.assertEqual(book['v14_control_preferences']['framework'],'CRS-Que')
        self.assertIn('10.1145/',book['v14_control_preferences']['source_url'])
        self.assertTrue(all(item['versions']==[SURVEY_VERSION] for item in book.values()))
        self.assertFalse(any(k.startswith(('v1_','v11_','v12_')) for k in book))
        payload=admin.csv_data([record(answers())],columns='technical').decode('utf-8-sig')
        rows=list(csv.DictReader(io.StringIO(payload),delimiter=';'))
        self.assertEqual(rows[0]['v14_usefulness_mean'],'7')
        self.assertEqual(rows[0]['v14_personality_customized_status'],'skipped')
        self.assertNotIn('v12_',payload)
        values=answers();values['usefulness_ideal']='not_assessable'
        payload=admin.csv_data([record(values)]).decode('utf-8-sig')
        row=next(csv.DictReader(io.StringIO(payload),delimiter=';'))
        self.assertEqual(row['v14_nutzen_mittelwert'],'')

    def test_retired_http_submissions_and_old_version_filters_are_rejected(self):
        from test_survey_chat_limit import SurveyChatLimitTests
        from werkzeug.security import generate_password_hash
        fixture=SurveyChatLimitTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        headers=fixture.grant()
        for version in ('diana-v1','diana-v11','diana-v12'):
            self.assertEqual(fixture.client.post('/api/survey-responses',headers=headers,json={'version':version}).status_code,409)
            self.assertEqual(fixture.client.put('/api/survey-drafts',headers=headers,json={'version':version}).status_code,409)
        fixture.app.config['ADMIN_PASSWORD_HASH']=generate_password_hash('test',method='pbkdf2:sha256:1000')
        self.assertEqual(fixture.client.post('/api/admin/login',json={'password':'test'}).status_code,200)
        for suffix in ('?version=diana-v12','?version='):
            self.assertEqual(fixture.client.get('/api/admin/analytics'+suffix).status_code,400)
        self.assertEqual(fixture.client.get('/api/admin/analytics').status_code,200)
        with fixture.app.extensions['admin_data'].surveys.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM survey_responses').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM survey_drafts').fetchone()[0],0)

if __name__=='__main__':unittest.main()
