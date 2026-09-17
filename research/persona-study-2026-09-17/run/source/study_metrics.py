"""Consent-bound operation totals without input text or individual event records."""
import json
import sqlite3

METRICS_CAPTURE_VERSION = 1
OPERATION_KINDS = ('search', 'rerank', 'chat')


def empty_metrics():
    """Old/missing capture is unknown; zero only describes an observed period."""
    return dict(capture_version=0, **{key: None for kind in OPERATION_KINDS for key in
        (f'successful_{kind}_count', f'failed_{kind}_count', f'{kind}_duration_ms')})


def metrics_snapshot(digest, db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='study_operation_metrics'").fetchone():
        return empty_metrics()
    row = db.execute('SELECT metadata_json FROM study_operation_metrics WHERE token_hash=?', (digest,)).fetchone()
    return json.loads(row[0]) if row else empty_metrics()


class StudyOperationMetrics:
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute('''CREATE TABLE IF NOT EXISTS study_operation_metrics (
                token_hash TEXT PRIMARY KEY, metadata_json TEXT NOT NULL)''')
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='privacy_consents'").fetchone():
                db.executescript('''
                    CREATE TRIGGER IF NOT EXISTS privacy_revoke_operation_metrics
                    AFTER UPDATE OF withdrawn_at ON privacy_consents
                    WHEN NEW.withdrawn_at IS NOT NULL
                    BEGIN DELETE FROM study_operation_metrics WHERE token_hash=NEW.token_hash; END;
                    CREATE TRIGGER IF NOT EXISTS privacy_delete_operation_metrics
                    AFTER DELETE ON privacy_consents
                    BEGIN DELETE FROM study_operation_metrics WHERE token_hash=OLD.token_hash; END;
                ''')

    @staticmethod
    def snapshot(digest, db):
        return metrics_snapshot(digest, db)

    def record_operation(self, digest, kind, success, duration_ms, db):
        """Count a finished operation inside the caller's transaction.

        A chat that performs a search/rerank also counts as a chat operation when
        its own request finishes. Durations therefore overlap across kinds and
        must never be summed into a total study/session duration. Validation,
        permission and rate-limit rejections before work starts are not counted.
        No commit occurs here; rollback of the enclosing write also rolls back
        the metric. Every finished attempt is counted, including failed retries.
        """
        if kind not in OPERATION_KINDS or type(success) is not bool or type(duration_ms) is not int or duration_ms < 0:
            raise ValueError('Ungültige aggregierte Operationsmetrik.')
        if not db.in_transaction:
            db.execute('BEGIN IMMEDIATE')
        consent = db.execute('SELECT purpose, withdrawn_at FROM privacy_consents WHERE token_hash=?', (digest,)).fetchone()
        if not consent or consent[0] != 'study' or consent[1] is not None:
            return False
        metrics = metrics_snapshot(digest, db)
        if metrics['capture_version'] == 0:
            metrics = {key: 0 for key in empty_metrics()}
            metrics['capture_version'] = METRICS_CAPTURE_VERSION
        counter = f'{"successful" if success else "failed"}_{kind}_count'
        metrics[counter] += 1
        metrics[f'{kind}_duration_ms'] += duration_ms
        db.execute('''INSERT INTO study_operation_metrics VALUES (?, ?)
            ON CONFLICT(token_hash) DO UPDATE SET metadata_json=excluded.metadata_json''',
            (digest, json.dumps(metrics, sort_keys=True, separators=(',', ':'))))
        return True
