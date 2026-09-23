"""Independent V14 integration checks: actual HTTP, SQLite and offline model fake."""
import csv
import hashlib
import io
import json
import secrets
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from werkzeug.security import generate_password_hash
from survey_store import SURVEY_VERSION, SURVEY_FIELDS, field_visible
from system_prompt_store import SystemPromptStore, DEFAULT_SYSTEM_PROMPTS


def complete_answers(arm, rating=5):
    values=dict(version=SURVEY_VERSION,study_arm=arm)
    for field in SURVEY_FIELDS:
        name=field['name']
        if name=='study_arm':continue
        if not field_visible(field,values):values[name]=None
        elif field['kind']=='scale':values[name]=rating
        elif field['kind']=='choice':values[name]='no' if name in ('previous_participation','personality_customized') else field['options'][0][0]
        else:values[name]='' if field.get('optional') else 'Werkstudent Data Science'
    return values


def csv_rows(content):
    text=content.decode('utf-8-sig') if isinstance(content,bytes) else content.lstrip('\ufeff')
    return list(csv.DictReader(io.StringIO(text),delimiter=';'))


class V14AdminIntegrationTests(unittest.TestCase):
    def setUp(self):
        from test_survey_chat_limit import SurveyChatLimitTests
        self.fx=SurveyChatLimitTests();self.fx.setUp();self.addCleanup(self.fx.doCleanups)
        self.app=self.fx.app;self.client=self.fx.client
        self.app.config['ADMIN_PASSWORD_HASH']=generate_password_hash('integration-password',method='pbkdf2:sha256:1000')
        self.db_path=self.app.config['DATABASE_PATH']
        self.headers={}

    def login(self):
        result=self.client.post('/api/admin/login',json={'password':'integration-password'})
        self.assertEqual(result.status_code,200,result.json)
        self.headers={'X-CSRF-Token':result.json['csrf']}

    def phase(self,wave='main'):
        config=self.client.get('/api/admin/study-context').json
        result=self.client.put('/api/admin/study-context',headers=self.headers,
            json=dict(study_wave=wave,recruitment_batch='2026-10-05T08:00:00Z' if wave=='main' else None,revision=config['revision']))
        self.assertEqual(result.status_code,200,result.json)
        return result.json

    def participant(self,arm,rating=5,completed=True):
        headers=self.fx.grant(arm)
        state=self.fx.onboard(headers)
        for _ in range(3):state=self.fx.chat(headers,state).json
        identifier=secrets.token_hex(16)
        if completed:
            result=self.client.post('/api/survey-responses',headers=headers,
                json=dict(submission_id=identifier,**complete_answers(arm,rating)))
        else:
            result=self.client.put('/api/survey-drafts',headers=headers,
                json=dict(submission_id=identifier,version=SURVEY_VERSION,revision=1,
                answers=dict(study_arm=arm,previous_participation='no',usefulness_ideal=rating,
                    usefulness_find_easy=rating,usefulness_suggestions=rating)))
        self.assertIn(result.status_code,(200,201),result.json)
        receipt=self.app.extensions['privacy_store'].receipt(headers['X-Diana-Consent'])
        return identifier,receipt['participation_id'],headers

    def test_admin_configuration_authentication_csrf_and_frozen_cohorts(self):
        for endpoint in ('study-context','study-metadata','study-metadata-export','study-analysis'):
            self.assertEqual(self.client.get('/api/admin/'+endpoint).status_code,401)
        self.login()
        initial=self.client.get('/api/admin/study-context').json
        pretest=self.fx.grant('A')
        self.assertEqual(self.client.put('/api/admin/study-context',json={**initial,'study_wave':'main'}).status_code,403)
        config=self.phase()
        self.assertEqual(config['revision'],initial['revision']+1)
        self.assertEqual(self.client.get('/api/study-context',headers=pretest).json['study_context']['study_wave'],'pretest')
        self.assertEqual(self.client.put('/api/admin/study-context',headers=self.headers,json=initial).status_code,409)
        main=self.fx.grant('B')
        self.assertEqual(self.client.get('/api/study-context',headers=main).json['study_context']['study_wave'],'main')
        report=self.client.get('/api/admin/study-metadata?study_wave=main').json
        self.assertEqual(report['participant_count'],1)
        self.assertEqual(report['step_counts']['consent'],1)
        self.assertEqual(self.client.get('/api/admin/responses?study_wave=main').json['total'],0)
        archive=zipfile.ZipFile(io.BytesIO(self.client.get('/api/admin/study-metadata-export?study_wave=main').data))
        exported=json.loads(archive.read('study_metadata.json'))
        self.assertEqual(exported['participant_count'],1)
        self.assertIn('operation_events.csv',archive.namelist())
        self.assertIn('scoring_calls.csv',archive.namelist())

    def test_csv_zip_codebook_and_completed_snapshot_obey_wave(self):
        self.login()
        _,pretest_id,_=self.participant('A',rating=1)
        self.phase()
        response_id,main_id,main_headers=self.participant('C',rating=6)
        extra=self.fx.grant('B')
        extra_id=self.app.extensions['privacy_store'].receipt(extra['X-Diana-Consent'])['participation_id']
        response=self.client.get('/api/admin/export?format=csv&columns=technical&study_wave=main')
        self.assertEqual(response.status_code,200,response.json)
        rows=csv_rows(response.data)
        self.assertEqual([row['participation_id'] for row in rows],[main_id])
        self.assertEqual(rows[0]['study_wave'],'main')
        self.assertEqual(rows[0]['v14_trust_fit'],'6')
        self.assertEqual(rows[0]['v14_perceived_character'],'6')
        self.assertEqual(rows[0]['v14_previous_participation'],'0')
        self.assertEqual(rows[0]['v14_personality_customized'],'0')
        self.assertEqual(rows[0]['furthest_step_reached'],'questionnaire_completed')
        self.assertNotIn('v13_',response.get_data(as_text=True))
        self.client.put('/api/study-context',headers=main_headers,json={'viewport_class':'mobile'})
        records=self.app.extensions['admin_data'].records()
        saved=next(row for row in records if row['id']==response_id)
        self.assertIsNone(saved['viewport_class'], 'Completed response context must retain the value at submission.')
        archive=zipfile.ZipFile(io.BytesIO(self.client.get('/api/admin/export?format=zip&study_wave=main').data))
        contexts=csv_rows(archive.read('studienkontext_alle_einwilligungen.csv'))
        self.assertEqual({row['participation_id'] for row in contexts},{main_id,extra_id})
        self.assertNotIn(pretest_id,archive.read('analysis_input.csv').decode())
        book=json.loads(archive.read('codebook.json'))
        indexed={item['technical_variable']:item for item in book}
        self.assertTrue(all(item['versions']==['diana-v14'] for item in book))
        self.assertEqual(indexed['v14_trust_mean']['item_type'],'multi_item_score')
        self.assertEqual(indexed['v14_perceived_character']['item_type'],'single_item')
        self.assertEqual(indexed['v14_trust_mean']['items'],['trust_fit','trust_credibility'])
        self.assertIn('study_wave',indexed)
        with sqlite3.connect(self.db_path) as db:
            stored=json.loads(db.execute('SELECT metadata_json FROM survey_response_metadata WHERE submission_id=?',(response_id,)).fetchone()[0])
            self.assertEqual(stored['study_context']['furthest_step_reached'],'questionnaire_completed')
            self.assertTrue(stored['personality_usage_frozen'])
            stored_ratings=db.execute('SELECT v14_usefulness_ideal,usefulness_ideal,v14_trust_fit FROM survey_responses WHERE submission_id=?',(response_id,)).fetchone()
            self.assertEqual(stored_ratings,(6,None,6), 'V14 generated columns must not leak values into V13 columns.')

    def test_online_analysis_matches_technical_csv_and_includes_valid_partial_endpoint(self):
        from research.v14.analyze import analyze_rows
        self.login()
        self.participant('A',rating=1)
        self.phase()
        self.participant('B',rating=2)
        self.participant('B',rating=4,completed=False)
        self.participant('C',rating=5)
        self.participant('C',rating=7)
        online=self.client.get('/api/admin/study-analysis?arm=A&study_wave=pretest')
        self.assertEqual(online.status_code,200,online.json)
        exported=self.client.get('/api/admin/export?format=csv&columns=technical')
        self.assertEqual(exported.status_code,200,exported.json)
        technical=csv_rows(exported.data)
        offline=analyze_rows(technical)
        self.assertEqual(online.json['sample_flow']['included_main'],4)
        self.assertEqual(online.json['primary']['n_second'],2)
        self.assertEqual(online.json['primary'],offline['primary'])
        self.assertEqual(online.json['sensitivity_first_time_only']['n'],4)
        self.assertEqual(online.json['plan_status'],'draft')


class V14PromptIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.path=Path(temporary.name)/'prompts.db'
        self.store=SystemPromptStore(self.path)

    def test_obsolete_b_weight_sentence_repair_is_narrow_versioned_and_preserves_snapshots(self):
        old='15 %, technical_depth 3 %, learning 17 %, innovation 3 %, clarity 2 %.'
        new='15 %, technical_depth 7 %, learning 6 %, innovation 6 %, clarity 6 %.'
        text=DEFAULT_SYSTEM_PROMPTS['career_fixed'].replace(new,old)+'\nBewahre meinen individuell ergänzten Satz.'
        self.assertIn(old,text)
        digest=hashlib.sha256(text.encode()).hexdigest()
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE system_prompts SET text=?,sha256=?,revision=8 WHERE policy='career_fixed'",(text,digest))
        frozen=self.store.participant_snapshot('a'*64,'diana-abc-v6','career_fixed')
        before=self.store.get()['revision']
        repaired=SystemPromptStore(self.path)
        current=repaired.snapshot('career_fixed')
        self.assertEqual(current['revision'],9)
        self.assertEqual(current['text'],text.replace(old,new))
        self.assertEqual(repaired.get()['revision'],before+1)
        self.assertEqual(repaired.participant_snapshot('a'*64,'diana-abc-v6','career_fixed'),frozen)
        self.assertEqual(SystemPromptStore(self.path).get()['revision'],before+1)

    def test_admin_prompt_validation_rejects_conflicting_explicit_weights_in_all_arms(self):
        for policy in ('unprompted','career_fixed','custom_career'):
            current=self.store.get()
            values={name:item['text'] for name,item in current['prompts'].items()}
            values[policy]+='\ntechnical_fit 99 %'
            with self.subTest(policy=policy),self.assertRaises(ValueError):
                self.store.update(current['revision'],values)

    def test_real_scoring_layer_returns_identical_applied_weights_for_all_arms(self):
        from advisor import SCORING_WEIGHTS,SCORING_VERSION
        from llm_service import OpenAIService
        from test_system_prompts import CapturingResponses,PROFILE,CANDIDATES
        responses=CapturingResponses()
        model=OpenAIService('',client=SimpleNamespace(responses=responses))
        scores=[]
        for policy in ('unprompted','career_fixed','custom_career'):
            result=model.rerank({},PROFILE,CANDIDATES,prompt_policy=policy,system_prompt=self.store.snapshot(policy))
            self.assertEqual(result['_scoring_metadata'],dict(applied_weights=list(SCORING_WEIGHTS.values()),scoring_version=SCORING_VERSION,assessment_reused=False))
            scores.append(result['rankings'][0]['score'])
        self.assertEqual(len(set(scores)),1)
        self.assertEqual(len(responses.calls),6)


if __name__=='__main__':unittest.main()
