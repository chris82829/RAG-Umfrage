"""Optional prize draw: email-only database, no join key to research answers."""
import csv
import io
import os
import re
import sqlite3
from pathlib import Path

from flask import jsonify, request
from pydantic import Field, ValidationError, field_validator
from typing import Literal

from privacy import ConsentRequired
from schemas import APIModel
from survey_store import spreadsheet_text

NOTICE_VERSION = 'diana-raffle-v1'
NOTICE_TEXT = ('Die Teilnahme am Gewinnspiel ist freiwillig. Deine E-Mail-Adresse wird ausschließlich '
               'zur Durchführung des Gewinnspiels und zur Gewinnbenachrichtigung verwendet. Sie wird '
               'in einer eigenen Datenbank ohne Teilnahme-ID, Studiengruppe, Umfrageantworten oder '
               'Anmeldezeitpunkt gespeichert und nicht an die KI übermittelt. Nach Abschluss des '
               'Gewinnspiels werden die Adressen gelöscht. Für einen Widerruf oder die Löschung '
               'deiner Gewinnspieladresse schreibe von dieser Adresse an '
               'christoph.scharnagl@th-nuernberg.de. Die Löschung deiner Umfrageantworten löscht '
               'die getrennt gespeicherte Gewinnspieladresse nicht automatisch.')


def normalize_email(value):
    if not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('Bitte gib eine gültige E-Mail-Adresse ein.')
    value = value.strip()
    if len(value) > 254 or value.count('@') != 1:
        raise ValueError('Bitte gib eine gültige E-Mail-Adresse ein.')
    local, domain = value.rsplit('@', 1)
    if (not re.fullmatch(r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]{1,64}", local)
            or local.startswith('.') or local.endswith('.') or '..' in local):
        raise ValueError('Bitte gib eine gültige E-Mail-Adresse ein.')
    try:
        domain = domain.encode('idna').decode('ascii').lower()
    except UnicodeError:
        raise ValueError('Bitte gib eine gültige E-Mail-Adresse ein.') from None
    labels = domain.split('.')
    if (len(labels) < 2 or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', part) for part in labels)
            or not re.fullmatch(r'(?:[a-z]{2,63}|xn--[a-z0-9-]{2,59})', labels[-1])):
        raise ValueError('Bitte gib eine gültige E-Mail-Adresse ein.')
    normalized = local.lower() + '@' + domain
    if len(normalized) > 254:
        raise ValueError('Bitte gib eine gültige E-Mail-Adresse ein.')
    return normalized


class RaffleEntry(APIModel):
    email: str = Field(max_length=254)
    accepted: bool
    notice_version: Literal['diana-raffle-v1']

    @field_validator('email', mode='before')
    @classmethod
    def email_address(cls, value):
        return normalize_email(value)

    @field_validator('accepted')
    @classmethod
    def consent(cls, value):
        if value is not True:
            raise ValueError('Die Einwilligung fehlt.')
        return value


class RaffleStore:
    def __init__(self, study_path, email_path):
        self.study_path = Path(study_path).resolve()
        self.email_path = Path(email_path).resolve()
        if self.email_path == self.study_path:
            raise ValueError('Gewinnspiel und Umfrage benötigen getrennte Datenbanken.')
        self.email_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.email_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(descriptor)
        os.chmod(self.email_path, 0o600)
        with sqlite3.connect(self.email_path) as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS raffle_entries (
                    email TEXT PRIMARY KEY, consent_version TEXT NOT NULL
                ) WITHOUT ROWID;
                CREATE TABLE IF NOT EXISTS raffle_settings (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL
                ) WITHOUT ROWID;
                INSERT OR IGNORE INTO raffle_settings VALUES ('enabled', 'true');
            ''')
        with sqlite3.connect(self.study_path) as db:
            # Only eligibility consumption, never an email, raffle ID or timestamp.
            db.executescript('''
                CREATE TABLE IF NOT EXISTS raffle_claims (token_hash TEXT PRIMARY KEY) WITHOUT ROWID;
                CREATE TRIGGER IF NOT EXISTS privacy_delete_raffle_claim
                AFTER DELETE ON privacy_consents
                BEGIN DELETE FROM raffle_claims WHERE token_hash=OLD.token_hash; END;
                CREATE TRIGGER IF NOT EXISTS privacy_revoke_raffle_claim
                AFTER UPDATE OF withdrawn_at ON privacy_consents WHEN NEW.withdrawn_at IS NOT NULL
                BEGIN DELETE FROM raffle_claims WHERE token_hash=OLD.token_hash; END;
            ''')

    @staticmethod
    def eligible(digest, db):
        return bool(db.execute('''SELECT 1 FROM privacy_links l JOIN survey_responses r
            ON r.submission_id=l.record_id WHERE l.kind='survey' AND l.token_hash=? LIMIT 1''', (digest,)).fetchone())

    def enabled(self):
        with sqlite3.connect(self.email_path) as db:
            return db.execute("SELECT value FROM raffle_settings WHERE key='enabled'").fetchone()[0] == 'true'

    def status(self, token, privacy, notice):
        with sqlite3.connect(self.study_path) as db:
            digest = privacy.require(token, notice, db)
            if notice.get('purpose', 'study') != 'study':
                raise ConsentRequired()
            return dict(eligible=self.eligible(digest, db),
                        registered=bool(db.execute('SELECT 1 FROM raffle_claims WHERE token_hash=?', (digest,)).fetchone()),
                        enabled=self.enabled(), notice_version=NOTICE_VERSION, notice_text=NOTICE_TEXT)

    def enter(self, token, body, privacy, notice):
        # Both files use rollback journals. ATTACH + one transaction makes an
        # entry and its consumed eligibility atomic, including concurrent tabs.
        with sqlite3.connect(self.study_path, timeout=30) as db:
            db.execute('ATTACH DATABASE ? AS raffle', (str(self.email_path),))
            db.execute('BEGIN IMMEDIATE')
            digest = privacy.require(token, notice, db)
            if notice.get('purpose', 'study') != 'study' or not self.eligible(digest, db):
                raise ConsentRequired()
            if db.execute('SELECT 1 FROM raffle_claims WHERE token_hash=?', (digest,)).fetchone():
                return
            if db.execute("SELECT value FROM raffle.raffle_settings WHERE key='enabled'").fetchone()[0] != 'true':
                raise ValueError('Die Anmeldung zum Gewinnspiel ist geschlossen.')
            db.execute('INSERT OR IGNORE INTO raffle.raffle_entries VALUES (?, ?)', (body.email, NOTICE_VERSION))
            db.execute('INSERT INTO raffle_claims VALUES (?)', (digest,))

    def summary(self):
        with sqlite3.connect(self.email_path) as db:
            return dict(count=db.execute('SELECT COUNT(*) FROM raffle_entries').fetchone()[0],
                        enabled=db.execute("SELECT value FROM raffle_settings WHERE key='enabled'").fetchone()[0]=='true')

    def configure(self, enabled):
        with sqlite3.connect(self.email_path) as db:
            db.execute("UPDATE raffle_settings SET value=? WHERE key='enabled'", ('true' if enabled else 'false',))
        return self.summary()

    def export(self):
        out=io.StringIO(); writer=csv.writer(out, delimiter=';'); writer.writerow(['email'])
        with sqlite3.connect(self.email_path) as db:
            for (email,) in db.execute('SELECT email FROM raffle_entries ORDER BY email'):
                writer.writerow([spreadsheet_text(email)])
        return '\ufeff'+out.getvalue()

    def delete(self, email=None):
        with sqlite3.connect(self.email_path) as db:
            db.execute('PRAGMA secure_delete=ON')
            if email is None:
                db.execute("UPDATE raffle_settings SET value='false' WHERE key='enabled'")
                db.execute('DELETE FROM raffle_entries')
            else:
                db.execute('DELETE FROM raffle_entries WHERE email=?', (normalize_email(email),))
        return self.summary()


def register_raffle(app, store, privacy, notice, consent_token, test_arm):
    @app.get('/api/raffle')
    def raffle_status():
        if test_arm():
            raise ConsentRequired()
        return jsonify(store.status(consent_token(), privacy, notice))

    @app.post('/api/raffle')
    def raffle_enter():
        if test_arm():
            raise ConsentRequired()
        try:
            body=RaffleEntry.model_validate(request.get_json(silent=True))
        except ValidationError:
            # Never return/log validation input: it contains the email address.
            return jsonify(error={'message':'Bitte gib eine gültige E-Mail-Adresse ein und bestätige die Gewinnspielhinweise.'}),400
        try:
            store.enter(consent_token(),body,privacy,notice)
        except ValueError:
            return jsonify(error={'message':'Die Anmeldung zum Gewinnspiel ist geschlossen.'}),409
        return jsonify(registered=True)
