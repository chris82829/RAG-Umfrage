"""Offline V12 telemetry checks: ownership, minimization, dedup and deletion."""
import json
import secrets
import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from werkzeug.security import generate_password_hash
from admin import register_admin

from flask import Flask, request, jsonify
from pydantic import ValidationError

from privacy import ConsentInput, ConsentRequired, PrivacyStore, token_hash
from session_store import EphemeralSessionStore
from study_metrics import StudyOperationMetrics, metrics_snapshot
from study_telemetry import StudyTelemetry, register_telemetry, telemetry_csv
from survey_store import SurveyStore


class StudyTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'study.sqlite3'
        self.privacy = PrivacyStore(self.path)
        self.surveys = SurveyStore(self.path)
        self.sessions = EphemeralSessionStore(self.path)
        self.metrics = StudyOperationMetrics(self.path)
        self.notice = dict(ready=True, configuration_complete=True, version='b'*64, purpose='study')
        self.token = secrets.token_hex(32)
        self.digest = token_hash(self.token)
        self.privacy.accept(ConsentInput(token=self.token, version=self.notice['version'], accepted=True), self.notice)
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.telemetry = register_telemetry(self.app, self.privacy, self.surveys, self.sessions,
            lambda: {**self.notice, 'purpose': f"test_{request.headers['X-Diana-Test'].lower()}"}
                    if request.headers.get('X-Diana-Test') else self.notice,
            lambda: request.headers.get('X-Diana-Consent', ''), lambda: request.headers.get('X-Diana-Test'))
        self.app.register_error_handler(ConsentRequired, lambda _error: (jsonify(error='consent'), 428))
        self.app.register_error_handler(ValidationError, lambda _error: (jsonify(error='invalid'), 400))
        self.client = self.app.test_client()
        self.headers = {'X-Diana-Consent': self.token}
        self.session_id = self.sessions.create({'jobs': [{'id': '123'}, {'id': '456'}]},
            before_save=lambda db, identifier: self.privacy.attach(self.token, self.notice, 'chat', identifier, db))
        self.addCleanup(lambda: self.sessions.delete(self.session_id))

    def event(self, kind='job_detail', **metadata):
        return dict(session_id=self.session_id, event_id=str(uuid.uuid4()), event_type=kind,
                    metadata=dict(job_id='123', rank=1, **metadata))

    def post(self, body=None, headers=None):
        return self.client.post('/api/track_event', json=body or self.event(), headers=headers or self.headers)

    def rows(self):
        with self.surveys.connect() as db:
            return db.execute('SELECT * FROM track_events ORDER BY id').fetchall()

    def test_migration_is_idempotent_and_works_on_empty_database(self):
        empty = Path(self.temp.name) / 'empty.sqlite3'
        StudyTelemetry(empty)
        StudyTelemetry(empty)
        with sqlite3.connect(empty) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM track_events').fetchone()[0], 0)

    def test_records_identifier_and_numbers_only_and_deduplicates(self):
        event = self.event('dwell_justification', duration_ms=5200)
        self.assertEqual(self.post(event).json, {'status': 'recorded'})
        self.assertEqual(self.post(event).json, {'status': 'duplicate'})
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0]['metadata']), {'job_id': '123', 'rank': 1, 'duration_ms': 5200})
        self.assertEqual(rows[0]['token_hash'], self.digest)
        self.assertTrue(rows[0]['timestamp'].endswith('Z'))
        self.assertNotIn(self.token, str(dict(rows[0])))

    def test_rejects_client_chat_turn_text_extra_fields_and_invalid_durations(self):
        events = [self.event('chat_turn'), self.event('dwell_justification'),
                  self.event('job_detail', duration_ms=1),
                  self.event('dwell_justification', duration_ms=60001),
                  self.event('dwell_justification', duration_ms=True),
                  self.event('job_detail', profile='do not store')]
        with_text = self.event(); with_text['message'] = 'do not store'
        events.append(with_text)
        for event in events:
            with self.subTest(event=event):
                self.assertEqual(self.post(event).status_code, 400)
        self.assertEqual(len(self.rows()), 0)

    def test_requires_current_consent_and_session_ownership(self):
        self.assertEqual(self.post(headers={'X-Diana-Consent': secrets.token_hex(32)}).status_code, 428)
        other = secrets.token_hex(32)
        self.privacy.accept(ConsentInput(token=other, version=self.notice['version'], accepted=True), self.notice)
        self.assertEqual(self.post(headers={'X-Diana-Consent': other}).status_code, 428)
        self.notice = {**self.notice, 'version': 'c'*64}
        self.assertEqual(self.post().status_code, 428)
        self.assertEqual(len(self.rows()), 0)

    def test_unknown_job_and_expired_session_do_not_create_events(self):
        event = self.event(); event['metadata']['job_id'] = 'not-a-result'
        self.assertEqual(self.post(event).status_code, 400)
        self.sessions.delete(self.session_id)
        self.assertEqual(self.post().status_code, 409)
        self.assertEqual(len(self.rows()), 0)

    def test_known_job_at_wrong_rank_is_rejected_until_actual_rank_matches(self):
        event = self.event()
        # The second result exists, but claiming the first position would
        # misattribute exposure after a rerank or from a stale browser view.
        event['metadata']['job_id'] = '456'
        response = self.post(event)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json['error']['code'], 'telemetry_ranking_changed')
        self.assertEqual(len(self.rows()), 0)
        event['metadata']['rank'] = 2
        self.assertEqual(self.post(event).json, {'status': 'recorded'})
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(json.loads(self.rows()[0]['metadata']), {'job_id': '456', 'rank': 2})

    def test_standalone_scope_does_not_create_study_events_or_bypass_consent(self):
        headers = {**self.headers, 'X-Diana-Test': 'A'}
        self.assertEqual(self.post(headers=headers).status_code, 428)
        token = secrets.token_hex(32)
        notice = {**self.notice, 'purpose': 'test_a'}
        self.privacy.accept(ConsentInput(token=token, version=notice['version'], accepted=True, purpose='test_a'), notice)
        self.assertEqual(self.post(headers={'X-Diana-Consent': token, 'X-Diana-Test': 'A'}).json,
                         {'status': 'ignored_test'})
        self.assertEqual(len(self.rows()), 0)

    def test_chat_turn_uses_success_metric_and_is_atomic_and_idempotent(self):
        with self.surveys.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self.metrics.record_operation(self.digest, 'search', True, 200, db)
            self.metrics.record_operation(self.digest, 'chat', False, 10, db)
            self.assertFalse(self.telemetry.record_chat_turn(self.digest, self.session_id, db))
            self.metrics.record_operation(self.digest, 'chat', True, 100, db)
            self.assertTrue(self.telemetry.record_chat_turn(self.digest, self.session_id, db))
            self.assertFalse(self.telemetry.record_chat_turn(self.digest, self.session_id, db))
        self.assertEqual(json.loads(self.rows()[0]['metadata']), {'successful_chat_count': 1})
        with self.surveys.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self.metrics.record_operation(self.digest, 'chat', True, 100, db)
            self.telemetry.record_chat_turn(self.digest, self.session_id, db)
            db.rollback()
        self.assertEqual(len(self.rows()), 1)
        with self.surveys.connect() as db:
            self.assertEqual(metrics_snapshot(self.digest, db)['successful_chat_count'], 1)

    def test_withdrawal_and_admin_deletion_remove_events_and_prevent_resurrection(self):
        self.post()
        receipt = self.privacy.receipt(self.token)
        self.privacy.delete_participant(receipt['participation_id'])
        self.assertEqual(len(self.rows()), 0)
        self.assertEqual(self.post().status_code, 428)
        with self.surveys.connect() as db:
            self.assertFalse(self.telemetry.record_chat_turn(self.digest, self.session_id, db))

    def test_export_obeys_participant_filter_and_omits_authentication_material(self):
        self.post(self.event('dwell_justification', duration_ms=3200))
        participation_id = self.privacy.receipt(self.token)['participation_id']
        with self.surveys.connect() as db:
            exported = telemetry_csv(db, {participation_id})
            empty = telemetry_csv(db, set())
        self.assertIn(participation_id, exported)
        self.assertIn('dwell_justification', exported)
        self.assertIn(';123;1;3200;', exported)
        self.assertNotIn(self.token, exported)
        self.assertNotIn(self.digest, exported)
        self.assertNotIn(participation_id, empty)
        self.assertEqual(len(empty.splitlines()), 1)

    def test_admin_export_requires_login_and_preserves_all_response_filters(self):
        self.app.config['ADMIN_PASSWORD_HASH'] = generate_password_hash('test-password', method='pbkdf2:sha256:1000')
        register_admin(self.app, self.surveys, self.privacy, SimpleNamespace(manifest={}),
                       self.sessions, self.notice, None)
        self.post()
        participant_id = self.privacy.receipt(self.token)['participation_id']
        filtered = Mock(return_value=[{'participation_id': participant_id}])
        self.app.extensions['admin_data'].filtered = filtered
        self.assertEqual(self.client.get('/api/admin/telemetry-export').status_code, 401)
        self.assertEqual(self.client.post('/api/admin/login', json={'password': 'test-password'}).status_code, 200)
        response = self.client.get('/api/admin/telemetry-export?version=diana-v12&status=in_progress&arm=C&q=needle')
        self.assertEqual(response.status_code, 200)
        filtered.assert_called_once_with('needle', 'diana-v12', 'in_progress', 'C', '')
        self.assertIn(participant_id, response.get_data(as_text=True))
        filtered.return_value = []
        response = self.client.get('/api/admin/telemetry-export?status=completed')
        self.assertNotIn(participant_id, response.get_data(as_text=True))

    def test_bulk_study_end_removes_events(self):
        self.post()
        self.privacy.end_study()
        self.assertEqual(len(self.rows()), 0)


class AppTelemetryIntegrationTests(unittest.TestCase):
    def test_committed_chat_emits_one_turn_errors_and_standalone_emit_none(self):
        # Reuse the app's existing fully offline fixtures, not a second fake
        # implementation of successful chat counting.
        from test_survey_chat_limit import SurveyChatLimitTests
        fixture = SurveyChatLimitTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        headers = fixture.grant('A')
        state = fixture.onboard(headers)
        db_path = fixture.app.config['DATABASE_PATH']

        def chat_events():
            with sqlite3.connect(db_path) as db:
                return db.execute("SELECT session_id, metadata FROM track_events WHERE event_type='chat_turn'").fetchall()

        self.assertEqual(chat_events(), [])
        response = fixture.chat(headers, state)
        self.assertEqual(response.status_code, 200)
        state = response.json
        self.assertEqual(chat_events(), [(state['session_id'], '{"successful_chat_count":1}')])
        # A profile rerank is successful work, but not an authored user turn.
        response = fixture.client.post('/api/chat', headers=headers,
            json=dict(session_id=state['session_id'], mode='rerank'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(chat_events()), 1)
        fixture.model.fail = True
        response = fixture.chat(headers, state)
        self.assertGreaterEqual(response.status_code, 400)
        self.assertEqual(len(chat_events()), 1)
        fixture.model.fail = False
        response = fixture.chat(headers, state)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(chat_events()), 2)
        self.assertEqual(json.loads(chat_events()[1][1]), {'successful_chat_count': 2})
        other_headers = fixture.grant('A', standalone=True)
        standalone = fixture.onboard(other_headers)
        self.assertEqual(fixture.chat(other_headers, standalone).status_code, 200)
        self.assertEqual(len(chat_events()), 2)

        # The real application route accepts only the caller's displayed jobs.
        job_id = state['jobs'][0]['id']
        event = dict(event_type='job_detail', event_id=str(uuid.uuid4()),
                     session_id=state['session_id'], metadata={'job_id': job_id, 'rank': 1})
        response = fixture.client.post('/api/track_event', headers=headers, json=event)
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(fixture.client.delete('/api/privacy/consent', headers=headers).status_code, 200)
        self.assertEqual(chat_events(), [])
        with sqlite3.connect(db_path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM track_events').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
