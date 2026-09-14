"""A/B/C allocation and lossless migration of the original B/C experiment."""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Lock

import pytest

from privacy import token_hash
from study_assignment import EXPERIMENT_ID, LEGACY_EXPERIMENT_ID, StudyAssignments


class Database:
    def __init__(self, path):
        self.path = path
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS privacy_links (token_hash TEXT, kind TEXT)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()


class Consent:
    @staticmethod
    def require(token, notice, db):
        if not token:
            raise ValueError('Consent required')
        return token_hash(token)


@pytest.fixture
def database(tmp_path):
    return Database(tmp_path / 'study.sqlite3')


def legacy_database(database):
    rows = [
        (token_hash('b' * 64), LEGACY_EXPERIMENT_ID, 'B', '2026-09-08T10:00:00+00:00', 0),
        (token_hash('c' * 64), LEGACY_EXPERIMENT_ID, 'C', '2026-09-08T11:00:00+00:00', 1),
    ]
    with database.connect() as db:
        db.execute('''CREATE TABLE study_assignments (
            token_hash TEXT PRIMARY KEY, experiment_id TEXT NOT NULL,
            arm TEXT NOT NULL CHECK(arm IN ('B','C')), assigned_at TEXT NOT NULL,
            prior_exposure INTEGER NOT NULL DEFAULT 0)''')
        db.executemany('INSERT INTO study_assignments VALUES (?, ?, ?, ?, ?)', rows)
    return rows


def test_migration_preserves_legacy_rows_and_runs_once_under_concurrent_startup(database, monkeypatch):
    original = legacy_database(database)
    monkeypatch.setattr('study_assignment.secrets.choice', lambda _: pytest.fail('Existing assignments must never be randomized again'))
    with ThreadPoolExecutor(max_workers=6) as pool:
        services = list(pool.map(lambda _: StudyAssignments(database, Consent(), {}), range(12)))
    for service in services:
        for token, old, current in [('b' * 64, original[0], 'A'), ('c' * 64, original[1], 'B')]:
            assert service.get(token) == service.assign(token) == {
                'experiment_id': LEGACY_EXPERIMENT_ID, 'arm': current,
                'assigned_at': old[3], 'prior_exposure': bool(old[4]),
                'personality_policy':'generic' if current=='A' else 'configurable',
                'questionnaire_version':'diana-v6','questionnaire_arm':old[2],
                'presentation_policy':'legacy_neutral' if current=='A' else 'ranked_insights',
            }
    with database.connect() as db:
        assert [tuple(row) for row in db.execute('SELECT * FROM study_assignments ORDER BY assigned_at')] == original
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='study_assignments_ab_migration'").fetchone()
        db.execute('INSERT INTO study_assignments VALUES (?, ?, ?, ?, ?)',
                   ('new', EXPERIMENT_ID, 'A', '2026-09-10', 0))


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
@pytest.mark.parametrize('migrate', [False, True])
def test_new_allocation_stores_current_arm_and_experiment(database, monkeypatch, arm, migrate):
    if migrate:
        legacy_database(database)
    service = StudyAssignments(database, Consent(), {})
    def choice(options):
        assert options == ('A', 'B', 'C')
        return arm
    monkeypatch.setattr('study_assignment.secrets.choice', choice)
    result = service.assign('a' * 64)
    assert result['arm'] == arm and result['experiment_id'] == EXPERIMENT_ID == 'diana-abc-v2'
    assert result['prior_exposure'] is False
    with database.connect() as db:
        row = db.execute('SELECT * FROM study_assignments WHERE token_hash=?', (token_hash('a' * 64),)).fetchone()
        assert row['arm'] == arm and row['assigned_at'] == result['assigned_at']


def test_concurrent_first_assignment_draws_exactly_once(database, monkeypatch):
    service = StudyAssignments(database, Consent(), {})
    calls, lock = [], Lock()
    def choice(options):
        with lock:
            calls.append(options)
        return 'A'
    monkeypatch.setattr('study_assignment.secrets.choice', choice)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: service.assign('a' * 64), range(20)))
    assert results == [results[0]] * 20
    assert calls == [('A', 'B', 'C')]
    with database.connect() as db:
        assert db.execute('SELECT count(*) FROM study_assignments').fetchone()[0] == 1


def test_failed_schema_migration_rolls_back_without_losing_legacy_data(database, monkeypatch):
    original = legacy_database(database)
    connect = database.connect

    class FailingConnection:
        def __init__(self, db):
            self.db = db

        def execute(self, sql, *args):
            if sql.startswith('ALTER TABLE study_assignments_ab_migration'):
                raise sqlite3.OperationalError('Simulated failure after old table removal')
            return self.db.execute(sql, *args)

    @contextmanager
    def failing_connect():
        with connect() as db:
            yield FailingConnection(db)

    monkeypatch.setattr(database, 'connect', failing_connect)
    with pytest.raises(sqlite3.OperationalError, match='Simulated failure'):
        StudyAssignments(database, Consent(), {})
    with connect() as db:
        assert [tuple(row) for row in db.execute('SELECT * FROM study_assignments ORDER BY assigned_at')] == original
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='study_assignments_ab_migration'").fetchone()
    monkeypatch.setattr(database, 'connect', connect)
    assert StudyAssignments(database, Consent(), {}).get('b' * 64)['arm'] == 'A'


def test_many_participants_retries_and_independent_workers_keep_one_assignment(database, monkeypatch):
    calls=[]
    def draw(options):
        assert options==('A','B','C')
        calls.append(1)
        return options[len(calls)%3]
    monkeypatch.setattr('study_assignment.secrets.choice',draw)
    workers=[StudyAssignments(database,Consent(),{}) for _ in range(6)]
    tokens=[f'{i:064x}' for i in range(100)]
    requests=[(workers[i%6],token) for i,token in enumerate(tokens*4)]
    with ThreadPoolExecutor(max_workers=12) as pool:
        results=list(pool.map(lambda item:(item[1],item[0].assign(item[1])),requests))
    assert len(calls)==100
    stable={}
    for token,row in results:
        assert stable.setdefault(token,row)==row
    restarted=StudyAssignments(database,Consent(),{})
    monkeypatch.setattr('study_assignment.secrets.choice',lambda _:pytest.fail('No new draw after restart'))
    for token,row in stable.items():assert restarted.assign(token)==row
    with database.connect() as db:
        assert db.execute('SELECT count(*) FROM study_assignments').fetchone()[0]==100


@pytest.mark.parametrize('legacy_arm,current_arm', [('B', 'A'), ('C', 'B')])
def test_old_participant_accepts_each_questionnaire_own_code(database, legacy_arm, current_arm):
    legacy_database(database)
    service = StudyAssignments(database, Consent(), {})
    token = legacy_arm.lower() * 64
    service.validate_answers(token, 'diana-v6', {'study_arm': legacy_arm})
    service.validate_answers(token, 'diana-v7', {'study_arm': current_arm})
    for version, wrong in [('diana-v6', 'C' if legacy_arm == 'B' else 'B'),
                           ('diana-v7', 'B' if current_arm == 'A' else 'A')]:
        with pytest.raises(ValueError, match='Studienzuordnung'):
            service.validate_answers(token, version, {'study_arm': wrong})


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
def test_new_participant_validation_and_neutral_override(database, monkeypatch, arm):
    from persona_mlds import load_templates
    service = StudyAssignments(database, Consent(), {})
    monkeypatch.setattr('study_assignment.secrets.choice', lambda _: arm)
    token = 'a' * 64
    service.assign(token)
    service.validate_answers(token, 'diana-v9', {'study_arm': arm})
    for version in ('diana-v6','diana-v7','diana-v8'):
        with pytest.raises(ValueError, match='Studienzuordnung'):
            service.validate_answers(token, version, {'study_arm': arm})
    requested = load_templates()['career']['advisor']
    actual = service.advisor(token, requested)
    assert actual['preset'] == 'standard' if arm=='A' else actual==requested
    for code in [None, '', *[code for code in ('A','B','C') if code != arm]]:
        with pytest.raises(ValueError, match='Studienzuordnung'):
            service.validate_answers(token, 'diana-v9', {'study_arm': code})


def test_legacy_neutral_mapping_and_missing_assignment(database):
    legacy_database(database)
    service = StudyAssignments(database, Consent(), {})
    requested = {'preset': 'steve'}
    assert service.advisor('b' * 64, requested)['preset'] == 'neutral'
    assert service.advisor('c' * 64, requested) == requested
    assert service.get(None) is None
    assert service.get('a' * 64) is None
    for version in ['diana-v6', 'diana-v7']:
        with pytest.raises(ValueError, match='Studienzuordnung'):
            service.validate_answers('a' * 64, version, {'study_arm': 'A'})
    service.validate_answers('a' * 64, 'diana-v5', {})


def test_allocation_preserves_prior_exposure_and_requires_consent(database, monkeypatch):
    service = StudyAssignments(database, Consent(), {})
    monkeypatch.setattr('study_assignment.secrets.choice', lambda _: 'B')
    with database.connect() as db:
        db.execute('INSERT INTO privacy_links VALUES (?, ?)', (token_hash('a' * 64), 'chat'))
    assert service.assign('a' * 64)['prior_exposure'] is True
    with pytest.raises(ValueError, match='Consent required'):
        service.assign(None)
    with database.connect() as db:
        assert db.execute('SELECT count(*) FROM study_assignments').fetchone()[0] == 1
