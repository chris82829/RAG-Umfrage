import json
from pathlib import Path
import sqlite3

import pytest

from persona_mlds import load_neutral_advisor, load_templates
from privacy import ConsentInput, PrivacyStore, load_notice, token_hash
from study_release import StudyReleases
from study_usage import StudyPersonalityUsage, empty_usage, normalize_selection, usage_snapshot
from survey_store import SurveyStore
from test_access import test_notice as standalone_notice


@pytest.fixture
def usage_store(tmp_path):
    path = tmp_path / 'usage.sqlite3'
    privacy = PrivacyStore(path)
    settings = tmp_path / 'privacy.json'
    settings.write_text(json.dumps(dict(approved=True, controller='Test', retention='Test',
                                       openai_processing='Test', technical_processing='Test')))
    notice = load_notice(settings)
    usage = StudyPersonalityUsage(path)
    surveys = SurveyStore(path)
    releases = StudyReleases(path, Path(__file__).parents[1], [])

    def consent(letter='a', purpose='study'):
        active_notice = standalone_notice(notice, purpose[-1].upper()) if purpose != 'study' else notice
        token = letter * 64
        privacy.accept(ConsentInput(token=token, version=active_notice['version'], accepted=True, purpose=purpose), active_notice)
        return token_hash(token)

    return path, privacy, usage, surveys, releases, consent


def apply(fixture, selection, digest=None):
    path, _privacy, usage, _surveys, _releases, consent = fixture
    digest = digest or consent()
    with sqlite3.connect(path) as db:
        result = usage.mark_applied(digest, selection, db)
        return result, usage_snapshot(digest, db)


def test_selection_matches_reviewed_mlds_and_modified_template_must_be_custom():
    career = load_templates()['career']['advisor']
    selected = dict(source='template', template_id='career')
    assert normalize_selection(career, selected) == selected
    assert normalize_selection(career, dict(source='custom', template_id=None))['source'] == 'custom'
    assert normalize_selection(career)['source'] == 'unknown'
    with pytest.raises(ValueError, match='verändert'):
        normalize_selection({**career, 'name': 'Individuell'}, selected)
    with pytest.raises(ValueError, match='verändert'):
        normalize_selection(load_templates()['expert']['advisor'], selected)
    with pytest.raises(ValueError):
        normalize_selection(career, dict(source='custom', template_id='career'))


def test_neutral_effective_advisor_is_not_applicable_regardless_of_requested_selection():
    result = normalize_selection(load_neutral_advisor(), dict(source='template', template_id='expert'))
    assert result == dict(source='not_applicable', template_id=None)


def test_usage_tracks_applied_selection_changes_without_logging_every_chat(usage_store):
    career = dict(source='template', template_id='career')
    custom = dict(source='custom', template_id=None)
    expert = dict(source='template', template_id='expert')
    changed, first = apply(usage_store, career)
    assert changed and first['initial_source'] == 'template' and first['initial_template_id'] == 'career'
    assert first['ever_template'] is True and first['ever_custom'] is False
    assert first['selection_change_count'] == 0
    assert first['first_applied_at_utc'].endswith('+00:00')
    changed, duplicate = apply(usage_store, career)
    assert not changed and duplicate == first
    _, second = apply(usage_store, custom)
    assert second['initial_template_id'] == 'career' and second['last_source'] == 'custom'
    assert second['ever_custom'] is True and second['ever_template'] is True
    _, third = apply(usage_store, expert)
    assert third['last_template_id'] == 'expert' and third['selection_change_count'] == 2
    assert third['first_applied_at_utc'] == first['first_applied_at_utc']


def test_no_record_created_for_standalone_tests_missing_consent_or_withdrawal(usage_store):
    path, privacy, usage, _surveys, _releases, consent = usage_store
    for letter, purpose in [('a', 'test_a'), ('b', 'test_b')]:
        digest = consent(letter, purpose)
        assert apply(usage_store, dict(source='custom', template_id=None), digest)[0] is False
    with sqlite3.connect(path) as db:
        assert usage.mark_applied('missing', dict(source='unknown', template_id=None), db) is False
        assert db.execute('SELECT COUNT(*) FROM study_personality_usage').fetchone()[0] == 0
    digest = consent('c')
    privacy.withdraw('c' * 64)
    assert apply(usage_store, dict(source='custom', template_id=None), digest)[0] is False


def test_metadata_contains_only_fixed_codes_and_times(usage_store):
    _, record = apply(usage_store, dict(source='custom', template_id=None))
    assert set(record) == set(empty_usage())
    assert not any(word in record for word in ['name', 'description', 'traits', 'profile', 'messages'])
    with pytest.raises(ValueError):
        apply(usage_store, dict(source='custom', template_id=None, description='private'))


def test_usage_does_not_commit_a_failed_session_transaction(usage_store):
    path, _privacy, usage, _surveys, _releases, consent = usage_store
    digest = consent()
    with pytest.raises(RuntimeError):
        with sqlite3.connect(path) as db:
            db.execute('BEGIN IMMEDIATE')
            usage.mark_applied(digest, dict(source='custom', template_id=None), db)
            raise RuntimeError('Session conflict')
    with sqlite3.connect(path) as db:
        assert usage_snapshot(digest, db) == empty_usage()


def test_draft_snapshot_updates_but_completed_snapshot_is_frozen(usage_store):
    path, _privacy, _usage, _surveys, releases, consent = usage_store
    digest = consent()
    apply(usage_store, dict(source='template', template_id='career'), digest)
    with sqlite3.connect(path) as db:
        releases.mark_run(digest, db)
        releases.capture_response(digest, 'response', db)
    apply(usage_store, dict(source='custom', template_id=None), digest)
    with sqlite3.connect(path) as db:
        releases.capture_response(digest, 'response', db, completed=True)
        frozen = db.execute('SELECT metadata_json FROM survey_response_metadata').fetchone()[0]
        assert json.loads(frozen)['personality_usage']['last_source'] == 'custom'
        assert json.loads(frozen)['personality_usage_frozen'] is True
    apply(usage_store, dict(source='template', template_id='expert'), digest)
    with sqlite3.connect(path) as db:
        releases.capture_response(digest, 'response', db, completed=True)
        assert db.execute('SELECT metadata_json FROM survey_response_metadata').fetchone()[0] == frozen
        assert usage_snapshot(digest, db)['last_template_id'] == 'expert'


def test_historical_completed_answers_are_not_backfilled_from_later_usage(usage_store):
    path, _privacy, _usage, _surveys, releases, consent = usage_store
    digest = consent()
    apply(usage_store, dict(source='template', template_id='career'), digest)
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO survey_responses VALUES ('legacy', 'yesterday', '{}')")
        db.execute("INSERT INTO survey_response_metadata VALUES ('legacy', ?)", (json.dumps({'release_ids': ['historical']}),))
        releases.capture_response(digest, 'legacy', db, completed=True)
        assert json.loads(db.execute("SELECT metadata_json FROM survey_response_metadata WHERE submission_id='legacy'").fetchone()[0]) == {'release_ids': ['historical']}


def test_missing_metadata_is_unknown_even_when_neutral_or_default_template_is_available(usage_store):
    path = usage_store[0]
    with sqlite3.connect(path) as db:
        value = usage_snapshot('never_used', db)
    assert value['capture_version'] == 0 and value['initial_source'] == 'unknown'
    assert value['ever_template'] is None and value['selection_change_count'] is None


def test_unknown_usage_does_not_claim_absence_of_customization(usage_store):
    _, first = apply(usage_store, dict(source='unknown', template_id=None))
    assert first['ever_custom'] is None and first['ever_template'] is None
    _, career = apply(usage_store, dict(source='template', template_id='career'))
    assert career['ever_template'] is True and career['ever_custom'] is None
    _, again_unknown = apply(usage_store, dict(source='unknown', template_id=None))
    assert again_unknown['ever_template'] is True and again_unknown['ever_custom'] is None
    _, custom = apply(usage_store, dict(source='custom', template_id=None))
    assert custom['ever_template'] is True and custom['ever_custom'] is True
    assert custom['selection_change_count'] == 3


def test_unknown_later_keeps_positive_evidence_but_invalidates_negative_flag(usage_store):
    apply(usage_store, dict(source='template', template_id='career'))
    _, unknown = apply(usage_store, dict(source='unknown', template_id=None))
    assert unknown['ever_template'] is True and unknown['ever_custom'] is None


def test_withdrawal_removes_only_owned_usage_and_frozen_snapshot(usage_store):
    path, privacy, _usage, _surveys, releases, consent = usage_store
    for letter in ('a', 'b'):
        digest = consent(letter)
        apply(usage_store, dict(source='custom', template_id=None), digest)
        with sqlite3.connect(path) as db:
            db.execute('INSERT INTO privacy_links VALUES (?, ?, ?)', ('survey', letter, digest))
            releases.capture_response(digest, letter, db, completed=True)
    privacy.withdraw('a' * 64)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT token_hash FROM study_personality_usage').fetchall() == [(token_hash('b' * 64),)]
        assert db.execute('SELECT submission_id FROM survey_response_metadata').fetchall() == [('b',)]


@pytest.mark.parametrize('operation', ['end_study', 'bulk_revoke', 'delete_consent'])
def test_all_lifecycle_deletions_remove_usage(usage_store, operation):
    path, privacy, _usage, _surveys, _releases, _consent = usage_store
    apply(usage_store, dict(source='custom', template_id=None))
    if operation == 'end_study':
        privacy.end_study()
    else:
        with sqlite3.connect(path) as db:
            db.execute("UPDATE privacy_consents SET withdrawn_at='now'" if operation == 'bulk_revoke' else 'DELETE FROM privacy_consents')
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM study_personality_usage').fetchone()[0] == 0
