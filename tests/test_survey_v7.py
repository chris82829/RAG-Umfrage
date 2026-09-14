"""A/B package outcomes and lossless exports of the historical B/C questionnaire."""
import csv
import io
import json
import zipfile
from copy import deepcopy

import pytest
from pydantic import ValidationError

from privacy import ConsentInput, token_hash
from survey_store import (
    SURVEY_DEFINITION, SURVEY_FIELDS, V6_SURVEY_DEFINITION, VERSIONED_FIELDS,
    SurveyDraftRequest, SurveyRequest, SurveySubmissionV6, SurveySubmissionV7,
    answer_status, field_visible,
)
from test_admin import admin_app, login


def versioned_payload(version='diana-v7', arm='A', submission_id='a' * 32):
    fields = VERSIONED_FIELDS[version]
    answers = {field['name']: 8 if field['kind'] == 'scale'
               else field['options'][0][0] if field['kind'] == 'choice'
               else '' if field.get('optional') else 'Softwareentwicklung'
               for field in fields}
    answers['study_arm'] = arm
    for field in fields:
        if not field_visible(field, answers):
            answers[field['name']] = None
    return dict(version=version, submission_id=submission_id, **answers)


def test_package_questions_are_only_required_and_answerable_in_b():
    assert SURVEY_DEFINITION['version'] == 'diana-v7'
    conditional = [field for field in SURVEY_FIELDS if field.get('visibleIf')]
    assert len(conditional) == 9
    assert {'score_usefulness', 'match_reasons_usefulness'} <= {field['name'] for field in conditional}
    for arm in ['A', 'B']:
        payload = versioned_payload(arm=arm)
        assert SurveyRequest.model_validate(payload).root == SurveySubmissionV7(**payload)
        for field in conditional:
            assert field['visibleIf'] == {'field': 'study_arm', 'equals': 'B'}
            assert answer_status(field, payload) == ('skipped' if arm == 'A' else 'answered')
            invalid = 8 if field['kind'] == 'scale' else 'yes'
            invalid = invalid if arm == 'A' else None
            with pytest.raises(ValidationError):
                SurveySubmissionV7(**(payload | {field['name']: invalid}))
    for name in ['search_ease', 'system_usefulness', 'chat_helpfulness', 'future_use']:
        assert not next(field for field in SURVEY_FIELDS if field['name'] == name).get('visibleIf')


def test_v7_drafts_keep_a_package_questions_empty_and_b_can_answer_them():
    draft = dict(submission_id='a'*32, version='diana-v7', revision=1,
                 answers={'study_arm': 'A', 'search_goal': 'P'})
    assert SurveyDraftRequest.model_validate(draft).root.answers.search_goal == 'P'
    with pytest.raises(ValidationError):
        SurveyDraftRequest.model_validate(draft | {'answers': {'study_arm': 'A', 'score_usefulness': 8}})
    assert SurveyDraftRequest.model_validate(draft | {'answers': {'study_arm': 'B', 'score_usefulness': 8}}).root.answers.score_usefulness == 8


def test_v6_archive_keeps_original_codes_and_questions_valid():
    field = next(field for field in V6_SURVEY_DEFINITION['demographics']['fields'] if field['name'] == 'study_arm')
    assert V6_SURVEY_DEFINITION['version'] == 'diana-v6'
    assert field['codes'] == {'B': 0, 'C': 1}
    for arm in ['B', 'C']:
        payload = versioned_payload('diana-v6', arm)
        assert SurveyRequest.model_validate(payload).root == SurveySubmissionV6(**payload)
        assert payload['score_usefulness'] == payload['match_reasons_usefulness'] == 8
        assert payload['personality_setup'] == (None if arm == 'B' else 8)


def seed_record(app, version, arm, identifier):
    store = app.extensions['survey_store']
    privacy = app.extensions['privacy_store']
    token = identifier * 64
    notice = {'ready': True, 'version': 'a' * 64}
    privacy.accept(ConsentInput(token=token, version=notice['version'], accepted=True), notice)
    experiment = 'diana-bc-v1' if version == 'diana-v6' else 'diana-ab-v1'
    with store.connect() as db:
        db.execute('INSERT INTO study_assignments VALUES (?, ?, ?, ?, ?)',
                   (token_hash(token), experiment, arm, '2026-09-10T12:00:00+00:00', 0))
    def link(db, record_id):
        privacy.attach(token, notice, 'survey', record_id, db)
    store.save(SurveyRequest.model_validate(versioned_payload(version, arm, identifier*32)).root, before_save=link)


def test_admin_and_exports_use_ab_labels_without_rewriting_legacy_answers(admin_app):
    cases = [('diana-v6', 'B', 'a'), ('diana-v6', 'C', 'b'),
             ('diana-v7', 'A', 'c'), ('diana-v7', 'B', 'd')]
    for args in cases:
        seed_record(admin_app, *args)
    store = admin_app.extensions['survey_store']
    with store.connect() as db:
        before = [tuple(row) for row in db.execute('SELECT * FROM survey_responses ORDER BY submission_id')]
    archive_before = deepcopy(V6_SURVEY_DEFINITION)
    client = admin_app.test_client()
    login(client)
    for arm, ids in [('A', {'a'*32, 'c'*32}), ('B', {'b'*32, 'd'*32})]:
        listing = client.get('/api/admin/responses?arm=' + arm).json
        assert listing['total'] == 2
        assert {item['id'] for item in listing['items']} == ids
    assert client.get('/api/admin/responses?arm=C').status_code == 400
    assert client.get('/api/admin/responses?version=diana-v7').json['total'] == 2
    legacy = client.get('/api/admin/responses/' + 'a'*32).json
    assert legacy['study_arm'] == 'A' and legacy['answers']['study_arm'] == 'B'
    choice = next(field for field in legacy['definition']['demographics']['fields'] if field['name'] == 'study_arm')
    assert dict(choice['options'])['B'].startswith('A – ')
    assert legacy['definition']['version'] == 'diana-v6'
    assert client.get('/api/admin/responses/'+'d'*32).json['definition']['version'] == 'diana-v7'
    assert V6_SURVEY_DEFINITION == archive_before

    rows = {row['participation_id']: row for row in csv.DictReader(
        io.StringIO(client.get('/api/admin/export?columns=technical').data.decode('utf-8-sig')), delimiter=';')}
    by_case = {(row['survey_version'], row['study_arm']): row for row in rows.values()}
    assert len(by_case) == 4
    for (version, arm), row in by_case.items():
        prefix = version[6:] + '_'
        assert row[prefix + 'study_arm'] == ('0' if arm == 'A' else '1')
        assert row[prefix + 'system_usefulness'] == '8'
        assert row[prefix + 'score_usefulness_status'] == ('skipped' if (version, arm) == ('diana-v7', 'A') else 'answered')
        assert row[prefix + 'personality_setup_status'] == ('skipped' if arm == 'A' else 'answered')
        assert row['experiment_id'] == ('diana-bc-v1' if version == 'diana-v6' else 'diana-ab-v1')
        assert None not in row
    package = zipfile.ZipFile(io.BytesIO(client.get('/api/admin/export?columns=technical&format=zip').data))
    book = {field['variable']: field for field in json.loads(package.read('codebook.json'))}
    assert book['v6_study_arm']['original_codes'] == {'0': 'B', '1': 'C'}
    assert book['v7_study_arm']['original_codes'] == {'0': 'A', '1': 'B'}
    assert set(book['study_arm']['codes']) == {'A', 'B'}
    assert 'diana-v6' in book['study_arm']['notes']
    assert book['v7_score_usefulness']['visible_if'] == {'field': 'study_arm', 'equals': 'B'}
    csvbook = next(csv.DictReader(io.StringIO(package.read('codebook.csv').decode('utf-8-sig')), delimiter=';'))
    assert 'original_codes' in csvbook and 'notes' in csvbook
    with store.connect() as db:
        assert [tuple(row) for row in db.execute('SELECT * FROM survey_responses ORDER BY submission_id')] == before
