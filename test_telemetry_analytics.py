"""Offline analytics regression tests: correct units, coverage and consent scope."""
import csv
import io
import json
import sqlite3
import unittest
from pathlib import Path

from telemetry_analytics import telemetry_analysis, telemetry_participant_csv


class TelemetryAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE privacy_consents (token_hash TEXT, participation_id TEXT, purpose TEXT, withdrawn_at TEXT)')
        self.db.execute('CREATE TABLE study_operation_metrics (token_hash TEXT, metadata_json TEXT)')
        self.db.executescript((Path(__file__).parent / 'migrations/012_study_telemetry.sql').read_text())
        self.rows = []
        for identifier, arm in (('one', 'A'), ('two', 'B'), ('three', 'C')):
            self.db.execute('INSERT INTO privacy_consents VALUES (?,?,?,NULL)', (identifier+'-secret', identifier, 'study'))
            self.rows.append(dict(id=identifier+'-response', participation_id=identifier, study_arm=arm,
                                  response_status='completed', consent_linked=True,
                                  operation_metrics={'capture_version': 1, 'successful_chat_count': 99}))
        self.next_id = 0

    def event(self, participant='one', kind='dwell_justification', job='42', session='s1', **metadata):
        self.next_id += 1
        self.db.execute('INSERT INTO track_events (token_hash,session_id,event_id,event_type,metadata) VALUES (?,?,?,?,?)',
                        (participant+'-secret',session,str(self.next_id),kind,json.dumps(dict(job_id=job, rank=1, **metadata))))

    def metrics(self, participant, count):
        self.db.execute('INSERT INTO study_operation_metrics VALUES (?,?)',
                        (participant+'-secret',json.dumps(dict(capture_version=1,successful_chat_count=count))))

    def test_sum_seconds_per_job_across_flushes_sessions_and_ranks(self):
        self.event(duration_ms=15000)
        self.event(duration_ms=2500, session='s2')
        self.event(kind='job_expand')
        self.event(kind='job_detail', job='43')
        analysis = telemetry_analysis(self.db, self.rows)
        first = next(row for row in analysis['participants'] if row['participation_id']=='one')
        self.assertEqual(first['dwell_seconds'],17.5)
        self.assertEqual(first['viewed_job_count'],2)
        self.assertEqual(first['job_expand_count'],1)
        self.assertEqual(first['job_detail_count'],1)
        self.assertEqual(first['jobs'][0]['session_count'],2)
        self.assertEqual(first['jobs'][0]['dwell_seconds'],17.5)
        self.assertIsNone(first['jobs'][1]['dwell_seconds'])
        self.assertEqual(first['response_id'], 'one-response')
        self.assertEqual(analysis['events']['dwell_justification'],2)

    def test_unknown_is_not_zero_and_means_exclude_unknown(self):
        self.event(duration_ms=0)
        self.event(participant='two', duration_ms=4000)
        self.metrics('one',0)
        analysis = telemetry_analysis(self.db,self.rows)
        self.assertEqual(analysis['summary']['metrics']['dwell_seconds'],
                         dict(n=2,mean=2,median=2,total=4,min=0,max=4))
        self.assertEqual(analysis['summary']['metrics']['successful_chat_count']['n'],1)
        self.assertEqual(analysis['summary']['metrics']['successful_chat_count']['mean'],0)
        third=next(row for row in analysis['participants'] if row['participation_id']=='three')
        for field in ('dwell_seconds','viewed_job_count','job_expand_count','job_detail_count','successful_chat_count'):
            self.assertIsNone(third[field])
        self.assertEqual(analysis['coverage']['without_client_events'],1)

    def test_chat_count_reads_authoritative_counter_never_event_or_response_snapshot(self):
        self.metrics('one',3)
        self.event(kind='chat_turn', successful_chat_count=1)
        self.event(kind='chat_turn', successful_chat_count=1)
        self.event(kind='chat_turn', successful_chat_count=45)
        analysis=telemetry_analysis(self.db,self.rows)
        first=next(row for row in analysis['participants'] if row['participation_id']=='one')
        self.assertEqual(first['successful_chat_count'],3)
        self.assertEqual(analysis['summary']['metrics']['successful_chat_count']['total'],3)
        self.assertEqual(first['event_count'],3)
        self.assertIsNone(first['job_expand_count'])
        self.assertIsNone(first['viewed_job_count'])

    def test_filters_revoked_deleted_and_non_study_even_if_rows_are_stale(self):
        self.event()
        self.event(participant='two')
        self.event(participant='three')
        self.db.execute("UPDATE privacy_consents SET withdrawn_at='now' WHERE participation_id='one'")
        self.db.execute("DELETE FROM privacy_consents WHERE participation_id='two'")
        self.db.execute("UPDATE privacy_consents SET purpose='test_c' WHERE participation_id='three'")
        analysis=telemetry_analysis(self.db,self.rows)
        self.assertEqual(analysis['participants'],[])
        self.assertEqual(analysis['summary']['event_count'],0)
        self.assertIsNone(analysis['summary']['metrics']['dwell_seconds']['mean'])

    def test_filtered_rows_and_duplicates_do_not_cross_contaminate(self):
        self.event(duration_ms=1000)
        self.event(participant='two',duration_ms=2000)
        analysis=telemetry_analysis(self.db,[self.rows[0],self.rows[0]])
        self.assertEqual(analysis['summary']['participant_count'],1)
        self.assertEqual(analysis['summary']['event_count'],1)
        self.assertEqual(analysis['groups'][0]['participant_count'],1)
        self.assertEqual(analysis['groups'][1]['participant_count'],0)
        self.assertEqual(telemetry_analysis(self.db,[])['summary']['participant_count'],0)
        self.assertNotIn('-secret',json.dumps(analysis))

    def test_csv_is_one_row_per_participant_with_units_and_blank_unknown(self):
        self.event(duration_ms=1234)
        analysis=telemetry_analysis(self.db,self.rows)
        output=telemetry_participant_csv(analysis)
        parsed=list(csv.DictReader(io.StringIO(output.lstrip('\ufeff')),delimiter=';'))
        self.assertEqual(len(parsed),3)
        first=next(row for row in parsed if row['teilnahme_id']=='one')
        self.assertEqual(first['begruendung_sichtbare_zeit_summe_sekunden'],'1.234')
        self.assertEqual(first['erfolgreiche_chatnachrichten_anzahl'],'')
        self.assertEqual(first['begruendungen_aufgeklappt_anzahl'],'0')
        self.assertNotIn('secret',output)
        self.assertNotIn('operation_metrics',output)

    def test_missing_tables_return_empty_coverage_without_failure(self):
        with sqlite3.connect(':memory:') as db:
            analysis=telemetry_analysis(db,self.rows)
            self.assertEqual(analysis['summary']['participant_count'],0)
            self.assertEqual(analysis['coverage']['with_events'],0)

    def test_malformed_legacy_metadata_does_not_crash_or_invent_duration(self):
        self.event(duration_ms=500)
        self.db.execute("UPDATE track_events SET metadata='invalid-json'")
        self.db.execute('INSERT INTO study_operation_metrics VALUES (?,?)',('one-secret','invalid-json'))
        analysis=telemetry_analysis(self.db,self.rows)
        first=next(row for row in analysis['participants'] if row['participation_id']=='one')
        self.assertIsNone(first['dwell_seconds'])
        self.assertIsNone(first['successful_chat_count'])
        self.assertEqual(first['jobs'],[])


if __name__ == '__main__':
    unittest.main()
