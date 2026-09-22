"""Offline V14 enrollment, monotonic progress, diagnostics and privacy checks."""
import csv
import io
import json
import secrets
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from privacy import ConsentInput, ConsentRequired, PrivacyStore, token_hash
from study_context import (StudyContext, context_snapshot, participant_contexts,
                           dropout_summary, metadata_analysis, context_csv, scoring_csv)
from study_metrics import StudyOperationMetrics, operation_diagnostics, operation_events_csv, metrics_snapshot


class ContextStoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name)/'test.db'
        self.privacy = PrivacyStore(self.path)
        self.context = StudyContext(self.path)
        self.metrics = StudyOperationMetrics(self.path)
        self.notice = dict(ready=True,configuration_complete=True,version='b'*64,purpose='study')
        self.token = secrets.token_hex(32)
        self.digest = token_hash(self.token)
        self.privacy.accept(ConsentInput(token=self.token,version=self.notice['version'],accepted=True),self.notice)

    def enroll(self, digest=None):
        with sqlite3.connect(self.path) as db:
            return self.context.enroll(digest or self.digest,db,experiment_id='diana-abc-v7',questionnaire_version='diana-v14')

    def test_configuration_is_versioned_optimistic_and_frozen_at_enrollment(self):
        first = self.enroll()
        self.assertEqual(first['study_wave'],'pretest')
        self.assertIsNone(first['recruitment_batch'])
        updated = self.context.configure('main','2026-10-01T09:00:00+02:00',1)
        self.assertEqual(updated,dict(revision=2,study_wave='main',recruitment_batch='2026-10-01T07:00:00Z'))
        self.assertEqual(self.enroll(),first)
        with self.assertRaises(ValueError): self.context.configure('pretest',None,1)
        with self.assertRaises(ValueError): self.context.configure('main',None,2)
        with self.assertRaises(ValueError): self.context.configure('main','2026-10-01T09:00:00',2)
        with self.assertRaises(ValueError): self.context.configure('main','free text with personal data',2)
        token = secrets.token_hex(32)
        self.privacy.accept(ConsentInput(token=token,version=self.notice['version'],accepted=True),self.notice)
        self.assertEqual(self.enroll(token_hash(token))['study_wave'],'main')
        StudyContext(self.path)
        self.assertEqual(self.context.config(),updated)

    def test_no_retrofit_and_monotonic_progress_with_initial_last_viewport(self):
        with sqlite3.connect(self.path) as db:
            self.assertEqual(context_snapshot(self.digest,db),{})
            self.assertEqual(self.context.viewport(self.digest,'mobile',db),{})
            self.assertEqual(self.context.advance(self.digest,'chat',db),{})
        self.enroll()
        with sqlite3.connect(self.path) as db:
            self.context.viewport(self.digest,'mobile',db)
            self.context.viewport(self.digest,'desktop',db)
            self.context.advance(self.digest,'chat',db)
            self.context.advance(self.digest,'profile',db)
            saved=context_snapshot(self.digest,db)
            self.assertEqual(saved['viewport_class'],'mobile')
            self.assertEqual(saved['viewport_class_last'],'desktop')
            self.assertEqual(saved['furthest_step_reached'],'chat')
            with self.assertRaises(ValueError):self.context.advance(self.digest,'made up',db)
            with self.assertRaises(ValueError):self.context.viewport(self.digest,'iPhone full identity',db)

    def test_scoring_call_evidence_and_safe_error_codes_export_and_recovery(self):
        self.enroll()
        evidence=dict(applied_weights=[60,15,7,6,6,6],scoring_version='fixed-balanced-v4',assessment_reused=False)
        with sqlite3.connect(self.path) as db:
            self.context.record_scoring(self.digest,evidence,'operation1',db)
            self.context.record_scoring(self.digest,{**evidence,'assessment_reused':True},'operation2',db)
            with self.assertRaises(ValueError):self.context.record_scoring(self.digest,{**evidence,'applied_weights':[99]},'operation3',db)
            self.metrics.record_operation(self.digest,'chat',False,45,db,error_code='private free text',error_stage='raw prompt')
            failed=operation_diagnostics(self.digest,db)
            self.assertEqual(failed['unrecovered_operation_kinds'],['chat'])
            self.assertEqual(failed['last_error_code'],'internal_error')
            self.assertEqual(failed['last_error_stage'],'unknown')
            self.metrics.record_operation(self.digest,'chat',True,200,db)
            recovered=operation_diagnostics(self.digest,db)
            self.assertEqual(recovered['unrecovered_operation_kinds'],[])
            self.assertTrue(recovered['last_operation_success'])
            self.assertEqual(metrics_snapshot(self.digest,db)['successful_chat_count'],1)
            report=metadata_analysis(db,version='diana-v14')
            self.assertEqual(report['scoring']['call_count'],2)
            self.assertEqual(report['scoring']['weight_vectors'],[dict(applied_weights=[60,15,7,6,6,6],count=2)])
            self.assertEqual(report['errors'],[dict(error_code='internal_error',error_stage='unknown',count=1)])
            for content in (scoring_csv(db),operation_events_csv(db),context_csv(db)):
                self.assertNotIn(self.digest,content)
                self.assertNotIn(self.token,content)
                self.assertNotIn('private free text',content)
            self.assertEqual(len(scoring_csv(db,[]).splitlines()),1)
            self.assertEqual(len(operation_events_csv(db,[]).splitlines()),1)

    def test_dropout_denominator_includes_consent_only_and_excludes_other_waves(self):
        self.enroll()
        with sqlite3.connect(self.path) as db:
            self.assertEqual(dropout_summary(db,version='diana-v14')['enrolled_count'],1)
            self.assertEqual(dropout_summary(db,version='diana-v14')['furthest_steps']['consent'],1)
            self.assertEqual(dropout_summary(db,version='diana-v13')['enrolled_count'],0)
            self.assertEqual(participant_contexts(db,wave='main'),[])
            self.assertEqual(len(list(csv.DictReader(io.StringIO(context_csv(db).lstrip('\ufeff')),delimiter=';'))),1)

    def test_test_consent_excluded_and_withdrawal_deletes_all_new_observations(self):
        test_token=secrets.token_hex(32)
        self.privacy.accept(ConsentInput(token=test_token,version=self.notice['version'],accepted=True,purpose='test_a'),{**self.notice,'purpose':'test_a'})
        with self.assertRaises(ConsentRequired):self.enroll(token_hash(test_token))
        self.enroll()
        with sqlite3.connect(self.path) as db:
            self.context.record_scoring(self.digest,dict(applied_weights=[60,15,7,6,6,6],scoring_version='v4',assessment_reused=False),'op1',db)
            self.metrics.record_operation(self.digest,'search',True,55,db)
        self.privacy.withdraw(self.token)
        with sqlite3.connect(self.path) as db:
            for table in ('study_participant_context','study_scoring_calls','study_operation_events'):
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],0)
            self.assertFalse(self.metrics.record_operation(self.digest,'chat',True,1,db))
            with self.assertRaises(ConsentRequired):self.context.enroll(self.digest,db,experiment_id='v7',questionnaire_version='v14')


class ContextHTTPTests(unittest.TestCase):
    def setUp(self):
        from test_survey_chat_limit import SurveyChatLimitTests
        self.fx=SurveyChatLimitTests()
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.client=self.fx.client

    def context(self, headers):
        response=self.client.get('/api/study-context',headers=headers)
        self.assertEqual(response.status_code,200)
        return response.json['study_context']

    def test_enrollment_validates_viewport_and_server_controls_each_phase(self):
        from survey_store import SURVEY_VERSION
        from test_survey_v13 import answers
        headers=self.fx.grant('C')
        self.assertEqual(self.context(headers)['furthest_step_reached'],'consent')
        self.assertEqual(self.context(headers)['study_wave'],'pretest')
        self.assertEqual(self.client.put('/api/study-context',headers=headers,json={'viewport_class':'mobile'}).status_code,200)
        self.assertEqual(self.client.put('/api/study-context',headers=headers,json={'viewport_class':'mobile','furthest_step_reached':'questionnaire_completed'}).status_code,400)
        self.assertEqual(self.client.put('/api/study-context',headers=headers,json={'viewport_class':'iPhone'}).status_code,400)
        self.assertEqual(self.client.post('/api/proceed_to_survey',headers=headers).status_code,403)
        self.assertEqual(self.context(headers)['furthest_step_reached'],'consent')
        state=self.fx.onboard(headers)
        self.assertEqual(self.context(headers)['furthest_step_reached'],'first_search')
        state=self.fx.chat(headers,state).json
        self.assertEqual(self.context(headers)['furthest_step_reached'],'chat')
        self.assertEqual(self.client.post('/api/proceed_to_survey',headers=headers).status_code,403)
        for _ in range(2):state=self.fx.chat(headers,state).json
        self.assertEqual(self.client.post('/api/proceed_to_survey',headers=headers).status_code,200)
        self.assertEqual(self.context(headers)['furthest_step_reached'],'questionnaire_started')
        response=self.client.post('/api/survey-responses',headers=headers,json=dict(submission_id='f'*32,**answers('C')))
        self.assertIn(response.status_code,(200,201),response.json)
        self.assertEqual(self.context(headers)['furthest_step_reached'],'questionnaire_completed')
        with sqlite3.connect(self.fx.app.config['DATABASE_PATH']) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM track_events WHERE event_type='chat_turn'").fetchone()[0],3)
            self.assertEqual(metrics_snapshot(token_hash(headers['X-Diana-Consent']),db)['successful_chat_count'],3)

    def test_scoring_metadata_errors_retries_and_test_exclusion(self):
        headers=self.fx.grant('B')
        original=self.fx.model.rerank
        def with_evidence(*args,**kwargs):
            return {**original(*args,**kwargs),'_scoring_metadata':dict(applied_weights=[60,15,7,6,6,6],scoring_version='test',assessment_reused=False)}
        with patch.object(self.fx.model,'rerank',side_effect=with_evidence):
            state=self.fx.onboard(headers)
            test_headers=self.fx.grant('B',standalone=True)
            self.fx.onboard(test_headers)
        self.fx.model.fail=True
        self.assertEqual(self.fx.chat(headers,state).status_code,503)
        self.fx.model.fail=False
        self.assertEqual(self.fx.chat(headers,state).status_code,200)
        with sqlite3.connect(self.fx.app.config['DATABASE_PATH']) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM study_scoring_calls').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT error_code,error_stage FROM study_operation_events WHERE success=0').fetchone(),('llm_unavailable','chat_plan'))
            self.assertEqual(operation_diagnostics(token_hash(headers['X-Diana-Consent']),db)['unrecovered_operation_kinds'],[])
            self.assertEqual(len(participant_contexts(db)),1)
        self.assertEqual(self.context(test_headers),{})


if __name__=='__main__':unittest.main()
