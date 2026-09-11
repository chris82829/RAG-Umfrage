"""Server-assigned A/B experiment, preserving historical B/C allocations."""
import secrets
from datetime import datetime, timezone

from privacy import token_hash
from advisor import AdvisorConfig

EXPERIMENT_ID = 'diana-ab-v2'
LEGACY_EXPERIMENT_ID = 'diana-bc-v1'
LEGACY_TO_CURRENT_ARM = {'B': 'A', 'C': 'B'}
CURRENT_TO_LEGACY_ARM = {current: legacy for legacy, current in LEGACY_TO_CURRENT_ARM.items()}
NEUTRAL_ADVISOR = dict(mode='preset', preset='neutral', name='DIANA', traits=[], focus='ausgewogen', description='')


class StudyAssignments:
    def __init__(self, surveys, privacy, notice):
        self.surveys, self.privacy, self.notice = surveys, privacy, notice
        with surveys.connect() as db:
            # Serialize startup migrations as well as allocations. Old rows retain
            # their original experiment, group code and allocation timestamp.
            db.execute('BEGIN IMMEDIATE')
            db.execute('''CREATE TABLE IF NOT EXISTS study_assignments (
                token_hash TEXT PRIMARY KEY, experiment_id TEXT NOT NULL,
                arm TEXT NOT NULL CHECK(arm IN ('A','B','C')), assigned_at TEXT NOT NULL,
                prior_exposure INTEGER NOT NULL DEFAULT 0)''')
            schema = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='study_assignments'").fetchone()['sql']
            if "'A'" not in schema.upper():
                # SQLite cannot alter CHECK constraints in place. Rebuild within
                # this transaction so concurrent workers never see a partial table.
                db.execute('''CREATE TABLE study_assignments_ab_migration (
                    token_hash TEXT PRIMARY KEY, experiment_id TEXT NOT NULL,
                    arm TEXT NOT NULL CHECK(arm IN ('A','B','C')), assigned_at TEXT NOT NULL,
                    prior_exposure INTEGER NOT NULL DEFAULT 0)''')
                db.execute('''INSERT INTO study_assignments_ab_migration
                    (token_hash, experiment_id, arm, assigned_at, prior_exposure)
                    SELECT token_hash, experiment_id, arm, assigned_at, prior_exposure
                    FROM study_assignments''')
                db.execute('DROP TABLE study_assignments')
                db.execute('ALTER TABLE study_assignments_ab_migration RENAME TO study_assignments')

    @staticmethod
    def public(row):
        if not row:
            return None
        arm = row['arm']
        if row['experiment_id'] == LEGACY_EXPERIMENT_ID:
            arm = LEGACY_TO_CURRENT_ARM[arm]
        return dict(experiment_id=row['experiment_id'], arm=arm, assigned_at=row['assigned_at'],
                    prior_exposure=bool(row['prior_exposure']))

    def get(self, token):
        if not token:
            return None
        with self.surveys.connect() as db:
            row = db.execute('SELECT * FROM study_assignments WHERE token_hash=?', (token_hash(token),)).fetchone()
            return self.public(row)

    def assign(self, token):
        with self.surveys.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            digest = self.privacy.require(token, self.notice, db)
            old = db.execute('SELECT * FROM study_assignments WHERE token_hash=?', (digest,)).fetchone()
            if old:
                return self.public(old)
            prior = bool(db.execute("SELECT 1 FROM privacy_links WHERE token_hash=? AND kind='chat' LIMIT 1", (digest,)).fetchone())
            db.execute('INSERT INTO study_assignments VALUES (?, ?, ?, ?, ?)',
                       (digest, EXPERIMENT_ID, secrets.choice(('A', 'B')), datetime.now(timezone.utc).isoformat(), int(prior)))
            return self.public(db.execute('SELECT * FROM study_assignments WHERE token_hash=?', (digest,)).fetchone())

    def advisor(self, token, requested):
        assigned = self.get(token)
        if assigned and assigned['arm'] == 'A':
            return dict(NEUTRAL_ADVISOR)
        if (assigned and assigned['arm'] == 'B'
                and requested.get('mode', 'preset') == 'preset'
                and requested.get('preset') == 'neutral'):
            # A stale or modified client must never turn a B participant into A.
            return AdvisorConfig().model_dump()
        return requested

    def validate_answers(self, token, version, answers):
        if version not in ('diana-v6', 'diana-v7'):
            return
        assigned = self.get(token)
        expected_arm = assigned['arm'] if assigned else None
        if version == 'diana-v6':
            expected_arm = CURRENT_TO_LEGACY_ARM.get(expected_arm)
        if not assigned or answers.get('study_arm') != expected_arm:
            raise ValueError('Die Studienzuordnung fehlt oder stimmt nicht überein. Bitte lade die Umfrage neu.')
