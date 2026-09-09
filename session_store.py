"""SQLite chat state survives Flask/Gunicorn restarts; writes use optimistic locking."""
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


class SessionConflict(RuntimeError):
    pass


class SessionStore:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY, state_json TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL)''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, state):
        session_id = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('INSERT INTO chat_sessions VALUES (?, ?, 1, ?)',
                       (session_id, json.dumps(state, ensure_ascii=False),
                        datetime.now(timezone.utc).isoformat()))
        return session_id

    def get(self, session_id):
        with self.connect() as db:
            row = db.execute('SELECT state_json, version FROM chat_sessions WHERE id=?',
                             (session_id,)).fetchone()
        return (json.loads(row[0]), row[1]) if row else None

    def update(self, session_id, state, version):
        with self.connect() as db:
            result = db.execute('''UPDATE chat_sessions SET state_json=?, version=version+1,
                updated_at=? WHERE id=? AND version=?''',
                (json.dumps(state, ensure_ascii=False), datetime.now(timezone.utc).isoformat(),
                 session_id, version))
            if result.rowcount != 1:
                raise SessionConflict('Der Chat wurde parallel geändert. Bitte neu laden.')

    def delete(self, session_id):
        with self.connect() as db:
            return db.execute('DELETE FROM chat_sessions WHERE id=?', (session_id,)).rowcount == 1
