"""Server-assigned B/C experiment, fixed per consent identity and stored separately from chat."""
import secrets
from datetime import datetime, timezone

from privacy import token_hash

EXPERIMENT_ID = 'diana-bc-v1'
NEUTRAL_ADVISOR = dict(mode='preset', preset='neutral', name='DIANA', traits=[], focus='ausgewogen', description='')


class StudyAssignments:
    def __init__(self, surveys, privacy, notice):
        self.surveys, self.privacy, self.notice = surveys, privacy, notice
        with surveys.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS study_assignments (
                token_hash TEXT PRIMARY KEY, experiment_id TEXT NOT NULL,
                arm TEXT NOT NULL CHECK(arm IN ('B','C')), assigned_at TEXT NOT NULL,
                prior_exposure INTEGER NOT NULL DEFAULT 0)''')

    @staticmethod
    def public(row):
        return dict(experiment_id=row['experiment_id'], arm=row['arm'], assigned_at=row['assigned_at'],
                    prior_exposure=bool(row['prior_exposure'])) if row else None

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
                       (digest, EXPERIMENT_ID, secrets.choice(('B', 'C')), datetime.now(timezone.utc).isoformat(), int(prior)))
            return self.public(db.execute('SELECT * FROM study_assignments WHERE token_hash=?', (digest,)).fetchone())

    def advisor(self, token, requested):
        assigned = self.get(token)
        return dict(NEUTRAL_ADVISOR) if assigned and assigned['arm']=='B' else requested

    def validate_answers(self, token, version, answers):
        if version != 'diana-v6':
            return
        assigned = self.get(token)
        if not assigned or answers.get('study_arm') != assigned['arm']:
            raise ValueError('Die Studienzuordnung fehlt oder stimmt nicht überein. Bitte lade die Umfrage neu.')
