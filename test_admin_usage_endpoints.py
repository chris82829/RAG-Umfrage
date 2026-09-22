"""Protected usage analysis and the requested complete study-data reset, offline."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from werkzeug.security import generate_password_hash

from admin import register_admin


class AdminUsageEndpointTests(unittest.TestCase):
    def setUp(self):
        from test_study_telemetry import StudyTelemetryTests
        self.fixture=StudyTelemetryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f=self.fixture
        f.app.config['ADMIN_PASSWORD_HASH']=generate_password_hash('test-password',method='pbkdf2:sha256:1000')
        register_admin(f.app,f.surveys,f.privacy,SimpleNamespace(manifest={}),f.sessions,f.notice,None)
        self.participant=f.privacy.receipt(f.token)['participation_id']
        self.filtered=Mock(return_value=[dict(id='answer1',participation_id=self.participant,study_arm='C',response_status='in_progress')])
        f.app.extensions['admin_data'].filtered=self.filtered

    def test_usage_analysis_and_csv_are_protected_filtered_and_use_same_aggregate(self):
        f=self.fixture
        for path in ('usage-analytics','usage-export'):
            self.assertEqual(f.client.get('/api/admin/'+path).status_code,401)
        self.assertEqual(f.post(f.event('dwell_justification',duration_ms=2500)).status_code,200)
        self.assertEqual(f.client.post('/api/admin/login',json={'password':'test-password'}).status_code,200)
        query='?status=in_progress&arm=C&q=needle'
        result=f.client.get('/api/admin/usage-analytics'+query)
        self.assertEqual(result.status_code,200)
        self.filtered.assert_called_with('needle','diana-v14','in_progress','C','','')
        self.assertEqual(result.json['participants'][0]['dwell_seconds'],2.5)
        exported=f.client.get('/api/admin/usage-export'+query)
        self.assertEqual(exported.status_code,200)
        self.assertIn('text/csv',exported.content_type)
        self.assertIn('diana_nutzungsverhalten.csv',exported.headers['Content-Disposition'])
        self.assertIn(self.participant,exported.get_data(as_text=True))
        self.assertIn(';2.5;',exported.get_data(as_text=True))
        self.filtered.return_value=[]
        self.assertEqual(f.client.get('/api/admin/usage-analytics'+query).json['summary']['participant_count'],0)
        self.assertNotIn(self.participant,f.client.get('/api/admin/usage-export'+query).get_data(as_text=True))
        self.assertEqual(f.client.get('/api/admin/usage-analytics?arm=D').status_code,400)

    def test_bulk_delete_removes_orphan_events_and_reservations_and_blocks_old_tokens(self):
        from test_survey_chat_limit import SurveyChatLimitTests
        fixture=SurveyChatLimitTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        headers=fixture.grant();state=fixture.onboard(headers);fixture.chat(headers,state)
        store=fixture.app.extensions['admin_data']
        with store.surveys.connect() as db:
            before_jobs=db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
            db.execute("INSERT INTO track_events(token_hash,session_id,event_id,event_type,metadata) VALUES('orphan','unused','orphan-event','job_detail','{}')")
            db.execute("INSERT INTO study_chat_reservations VALUES('orphan-reservation','orphan',0)")
        store.delete_all(store.deletion_preview()['fingerprint'])
        with store.surveys.connect() as db:
            for table in ('survey_responses','survey_drafts','survey_answer_corrections','study_assignments','study_operation_metrics','track_events','study_chat_reservations'):
                self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],0,table)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],before_jobs)
        self.assertEqual(fixture.client.post('/api/study-assignment',headers=headers).status_code,428)

if __name__=='__main__':unittest.main()
