"""Offline regression checks for the study-only three-message allowance."""
import json
import logging
import secrets
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from app import create_app
from llm_service import LLMUnavailable
from privacy import token_hash
from session_store import SessionConflict
from study_chat_limit import ChatMessageLimit, ChatReservationExpired
from study_metrics import metrics_snapshot


class FakeRetriever:
    def search(self, jobs, query, top_k=20):
        return [{'job': job, 'rrf_score': .03, 'bm25_rank': index + 1,
                 'semantic_rank': index + 1, 'bm25_score': 1, 'semantic_score': .8}
                for index, job in enumerate(jobs[:top_k])]


class FakeModel:
    def __init__(self):
        self.chat_calls = 0
        self.action = 'answer'
        self.fail = False
        self.fail_stream = False
        self.follow_up_flags = []
        self.ranking_follow_up_flags = []

    def generate_persona(self, profile):
        return dict(persona_prompt='Fachliche Anforderungen berücksichtigen.',
                    retrieval_query='Python Datenanalyse', opening_message='Hallo!')

    def rerank(self, persona, profile, candidates, **kwargs):
        self.ranking_follow_up_flags.append((kwargs.get('chat_context') or {}).get('follow_up_allowed'))
        return dict(rankings=[dict(job_id=item['job']['id'], score=90-index,
                                  reason='Fachkenntnisse passen.', matched_skills=['Python'], missing_skills=[])
                              for index, item in enumerate(candidates)],
                    assistant_message='Hier sind die Ergebnisse.')

    def plan_chat(self, *args, **kwargs):
        self.chat_calls += 1
        self.follow_up_flags.append(kwargs.get('follow_up_allowed'))
        if self.fail:
            raise LLMUnavailable('Offline-Testfehler')
        return dict(action=self.action, profile_patch={}, assistant_message='Die Python-Kenntnisse passen.')

    def plan_chat_steps(self, *args, **kwargs):
        result = self.plan_chat(*args, **{key: value for key, value in kwargs.items() if key != 'stream'})
        yield dict(data=result)
        if self.fail_stream:
            raise LLMUnavailable('Offline-Streamingfehler')
        return result


PROFILE = {'profile': {'query': 'Python Datenanalyse', 'skills': ['Python'], 'filters': {}}}


class SurveyChatLimitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        notice = root / 'privacy.json'
        notice.write_text(json.dumps(dict(approved=True, controller='Test', retention='Test',
                                         openai_processing='Test', technical_processing='Test')))
        self.model = FakeModel()
        self.app = create_app(dict(TESTING=True, PRIVACY_REQUIRED=True, OPENAI_API_KEY='',
                                   DATABASE_PATH=root / 'test.sqlite3', PRIVACY_SETTINGS_PATH=notice,
                                   SEED_DUMMY_DATA=True, REQUIRE_COMPLETE_INDEX=False),
                              retriever=FakeRetriever(), llm=self.model)
        self.client = self.app.test_client()
        self.app.logger.getChild('performance').setLevel(logging.CRITICAL)

    def grant(self, arm='A', standalone=False):
        headers = {'X-Diana-Consent': secrets.token_hex(32)}
        if standalone:
            headers['X-Diana-Test'] = arm
        notice = self.client.get('/api/privacy', headers=headers).json['notice']
        accepted = self.client.post('/api/privacy/consent', headers=headers,
                                    json=dict(token=headers['X-Diana-Consent'], version=notice['version'],
                                              purpose=f'test_{arm.lower()}' if standalone else 'study', accepted=True))
        self.assertEqual(accepted.status_code, 200)
        if not standalone:
            with patch('study_assignment.secrets.choice', return_value=arm):
                self.assertEqual(self.client.post('/api/study-assignment', headers=headers).json['arm'], arm)
        return headers

    def onboard(self, headers):
        response = self.client.post('/api/onboard', headers=headers, json=PROFILE)
        self.assertEqual(response.status_code, 201, response.json)
        return response.json

    def chat(self, headers, state, **changes):
        return self.client.post('/api/chat', headers=headers,
                                json=dict(session_id=state['session_id'], message='Warum passt das?', **changes))

    def test_each_study_arm_limits_successful_messages_before_model_call(self):
        for arm in ('A', 'B', 'C'):
            with self.subTest(arm=arm):
                headers = self.grant(arm)
                state = self.onboard(headers)
                self.assertEqual(state['chat_usage'], dict(limit=3, used=0, pending=0, remaining=3))
                for index in range(3):
                    response = self.chat(headers, state)
                    self.assertEqual(response.status_code, 200, response.json)
                    state = response.json
                    self.assertEqual(state['chat_usage'], dict(limit=3, used=index+1, pending=0, remaining=2-index))
                calls = self.model.chat_calls
                rejected = self.chat(headers, state)
                self.assertEqual(rejected.status_code, 409)
                self.assertEqual(rejected.json['error']['code'], 'chat_message_limit')
                self.assertEqual(rejected.json['error']['chat_usage']['remaining'], 0)
                self.assertEqual(self.model.chat_calls, calls)

    def test_usage_survives_session_deletion_new_search_and_app_restart(self):
        headers = self.grant()
        state = self.onboard(headers)
        for _ in range(3):
            state = self.chat(headers, state).json
        self.assertEqual(self.client.delete('/api/sessions/' + state['session_id'], headers=headers).status_code, 204)
        state = self.onboard(headers)
        self.assertEqual(state['chat_usage']['used'], 3)
        restarted = create_app(dict(self.app.config), retriever=FakeRetriever(), llm=self.model)
        restored = restarted.test_client().get('/api/sessions/' + state['session_id'], headers=headers)
        self.assertEqual(restored.json['chat_usage']['remaining'], 0)
        self.assertEqual(self.chat(headers, state).status_code, 409)

    def test_followups_respect_remaining_messages_across_planning_and_ranking(self):
        for arm in ('B', 'C'):
            with self.subTest(arm=arm):
                headers = self.grant(arm)
                state = self.onboard(headers)
                self.assertIs(self.model.ranking_follow_up_flags[-1], True)
                for index, action in enumerate(('answer', 'rerank', 'search')):
                    self.model.action = action
                    response = self.chat(headers, state)
                    self.assertEqual(response.status_code, 200, response.json)
                    state = response.json
                    self.assertIs(self.model.follow_up_flags[-1], index < 2)
                    if action != 'answer':
                        self.assertIs(self.model.ranking_follow_up_flags[-1], index < 2)
                # A new search must not invite an answer after the allowance was used.
                self.onboard(headers)
                self.assertIs(self.model.ranking_follow_up_flags[-1], False)

    def test_standalone_tests_keep_followups_after_three_messages(self):
        for arm in ('B', 'C'):
            headers = self.grant(arm, standalone=True)
            state = self.onboard(headers)
            self.model.action = 'rerank'
            for _ in range(4):
                response = self.chat(headers, state)
                self.assertEqual(response.status_code, 200, response.json)
                state = response.json
                self.assertIs(self.model.follow_up_flags[-1], True)
                self.assertIs(self.model.ranking_follow_up_flags[-1], True)

    def test_profile_and_search_or_rerank_without_message_do_not_consume_allowance(self):
        headers = self.grant()
        state = self.onboard(headers)
        for mode in ('rerank', 'search'):
            response = self.client.post('/api/chat', headers=headers, json=dict(session_id=state['session_id'], mode=mode))
            self.assertEqual(response.status_code, 200, response.json)
            state = response.json
            self.assertEqual(state['chat_usage']['used'], 0)
        response = self.client.post('/api/chat', headers=headers, json=dict(session_id=state['session_id'], **PROFILE))
        self.assertEqual(response.json['chat_usage']['remaining'], 3)
        self.assertEqual(self.model.chat_calls, 0)

    def test_messages_that_trigger_search_or_rerank_each_count_once(self):
        headers = self.grant()
        state = self.onboard(headers)
        for index, action in enumerate(('search', 'rerank', 'answer')):
            self.model.action = action
            state = self.chat(headers, state).json
            self.assertEqual(state['chat_usage']['used'], index + 1)
        self.assertEqual(self.chat(headers, state).status_code, 409)

    def test_failure_releases_reservation_and_success_remains_possible(self):
        headers = self.grant()
        state = self.onboard(headers)
        self.model.fail = True
        for _ in range(4):
            self.assertEqual(self.chat(headers, state).status_code, 503)
        restored = self.client.get('/api/sessions/' + state['session_id'], headers=headers).json
        self.assertEqual(restored['chat_usage'], dict(limit=3, used=0, pending=0, remaining=3))
        self.model.fail = False
        self.assertEqual(self.chat(headers, state).json['chat_usage']['used'], 1)

    def test_streaming_failure_and_disconnect_release_reservation(self):
        headers = self.grant()
        state = self.onboard(headers)
        streaming = {**headers, 'Accept': 'application/x-ndjson'}
        self.model.fail_stream = True
        response = self.chat(streaming, state)
        events = [json.loads(line) for line in response.data.splitlines()]
        self.assertEqual(events[0]['type'], 'assistant_text')
        self.assertEqual(events[-1]['type'], 'error')
        self.model.fail_stream = False
        response = self.client.post('/api/chat', headers=streaming,
                                    json=dict(session_id=state['session_id'], message='Noch ein Test'), buffered=False)
        self.assertIn(b'assistant_text', next(iter(response.response)))
        response.close()
        restored = self.client.get('/api/sessions/' + state['session_id'], headers=headers).json
        self.assertEqual(restored['chat_usage'], dict(limit=3, used=0, pending=0, remaining=3))
        final = self.chat(streaming, state)
        events = [json.loads(line) for line in final.data.splitlines()]
        self.assertEqual(events[-1]['data']['chat_usage']['used'], 1)

    def test_all_standalone_arms_allow_more_than_three_with_no_study_metrics(self):
        for arm in ('A', 'B', 'C'):
            with self.subTest(arm=arm):
                headers = self.grant(arm, standalone=True)
                state = self.onboard(headers)
                for index in range(5):
                    response = self.chat(headers, state)
                    self.assertEqual(response.status_code, 200, response.json)
                    state = response.json
                    self.assertEqual(state['chat_usage'], dict(limit=None, used=index+1, pending=0, remaining=None))
        with self.app.extensions['survey_store'].connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM study_operation_metrics').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM study_chat_reservations').fetchone()[0], 0)

    def test_test_header_cannot_bypass_study_consent_scope(self):
        headers = self.grant('A')
        state = self.onboard(headers)
        for _ in range(3):
            self.assertEqual(self.chat(headers, state).status_code, 200)
        calls = self.model.chat_calls
        for arm in ('A', 'B', 'C'):
            response = self.chat({**headers, 'X-Diana-Test': arm}, state)
            self.assertEqual(response.status_code, 428)
        test_headers = self.grant('A', standalone=True)
        self.assertEqual(self.chat(test_headers, state).status_code, 428)
        self.assertEqual(self.model.chat_calls, calls)

    def test_atomic_reservations_allow_only_three_concurrent_requests(self):
        headers = self.grant()
        digest = token_hash(headers['X-Diana-Consent'])
        limiter = self.app.extensions['chat_limit']
        barrier = threading.Barrier(8)

        def reserve():
            barrier.wait()
            try:
                with self.app.extensions['survey_store'].connect() as db:
                    return limiter.reserve(digest, db)
            except ChatMessageLimit:
                return None

        with ThreadPoolExecutor(max_workers=8) as pool:
            reservations = [item for item in pool.map(lambda _: reserve(), range(8)) if item]
        self.assertEqual(len(reservations), 3)
        state = self.onboard(headers)
        self.assertEqual(state['chat_usage'], dict(limit=3, used=0, pending=3, remaining=0))
        self.assertEqual(self.chat(headers, state).status_code, 409)
        self.assertEqual(self.model.chat_calls, 0)
        limiter.release(reservations[0])
        self.assertEqual(self.chat(headers, state).json['chat_usage'], dict(limit=3, used=1, pending=2, remaining=0))

    def test_stale_reservation_cannot_commit_or_consume_recovered_allowance(self):
        headers = self.grant()
        digest = token_hash(headers['X-Diana-Consent'])
        limiter = self.app.extensions['chat_limit']
        with self.app.extensions['survey_store'].connect() as db:
            old = limiter.reserve(digest, db)
            db.execute('UPDATE study_chat_reservations SET expires_at=0')
        with self.app.extensions['survey_store'].connect() as db:
            fresh = limiter.reserve(digest, db)
        with self.assertRaises(ChatReservationExpired):
            with self.app.extensions['survey_store'].connect() as db:
                limiter.finish(digest, old, db)
        with self.app.extensions['survey_store'].connect() as db:
            self.assertEqual(limiter.snapshot(digest, db), dict(limit=3, used=0, pending=1, remaining=2))
        limiter.release(fresh)

    def test_session_conflict_rolls_back_success_and_releases_lease(self):
        headers = self.grant()
        state = self.onboard(headers)
        store = self.app.extensions['chat_store']
        update = store.update

        def conflicting_update(session_id, new_state, version, before_save=None):
            def conflict_after_metrics(db, record_id):
                before_save(db, record_id)
                raise SessionConflict('Offline-Sitzungskonflikt')
            return update(session_id, new_state, version, before_save=conflict_after_metrics)

        with patch.object(store, 'update', side_effect=conflicting_update):
            self.assertEqual(self.chat(headers, state).status_code, 409)
        restored = self.client.get('/api/sessions/' + state['session_id'], headers=headers).json
        self.assertEqual(restored['chat_usage'], dict(limit=3, used=0, pending=0, remaining=3))
        self.assertEqual(self.chat(headers, state).json['chat_usage']['used'], 1)

    def test_production_memory_sessions_share_the_participant_allowance(self):
        self.app = create_app({**dict(self.app.config), 'PERSIST_CHAT_SESSIONS': False},
                              retriever=FakeRetriever(), llm=self.model)
        self.app.logger.getChild('performance').setLevel(logging.CRITICAL)
        self.client = self.app.test_client()
        headers = self.grant('C')
        first, second = self.onboard(headers), self.onboard(headers)
        for state in (first, second, first):
            self.assertEqual(self.chat(headers, state).status_code, 200)
        self.assertEqual(self.chat(headers, second).status_code, 409)
        self.assertEqual(self.client.get('/api/sessions/' + first['session_id'], headers=headers).json['chat_usage']['used'], 3)
        self.client.delete('/api/privacy/consent', headers=headers)

    def test_withdrawal_removes_pending_counts_and_does_not_store_text(self):
        headers = self.grant()
        state = self.onboard(headers)
        self.assertEqual(self.chat(headers, state).status_code, 200)
        digest = token_hash(headers['X-Diana-Consent'])
        with self.app.extensions['survey_store'].connect() as db:
            self.app.extensions['chat_limit'].reserve(digest, db)
            columns = [row[1] for row in db.execute('PRAGMA table_info(study_chat_reservations)')]
            self.assertEqual(columns, ['reservation_id', 'token_hash', 'expires_at'])
        self.assertEqual(self.client.delete('/api/privacy/consent', headers=headers).status_code, 200)
        with self.app.extensions['survey_store'].connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM study_chat_reservations').fetchone()[0], 0)
            self.assertEqual(metrics_snapshot(digest, db)['successful_chat_count'], None)

    def test_manifest_documents_study_limit_and_unlimited_tests(self):
        manifest = self.app.extensions['study_releases'].manifest
        self.assertEqual(manifest['max_user_chat_messages'], 3)
        self.assertIsNone(manifest['test_max_user_chat_messages'])
        self.assertIn('study_chat_limit.py', manifest['source_sha256'])


if __name__ == '__main__':
    unittest.main()
