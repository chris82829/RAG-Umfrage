import csv
import io
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from app import create_app
from survey_store import (LegacySurveySubmission, LEGACY_SURVEY_DEFINITION as SURVEY_DEFINITION, LEGACY_SURVEY_FIELDS as SURVEY_FIELDS,
                          SurveyStore, SurveySubmission, SurveySubmissionV2, spreadsheet_text)

RATING_FIELDS = ('personality_clarity', 'personality_setup', 'personality_consistency',
                 'chat_helpfulness', 'search_refinement', 'explanation_helpfulness',
                 'search_ease', 'personality_value', 'future_use',
                 'score_usefulness', 'match_reasons_usefulness',
                 'personalized_chat_usefulness', 'personalized_search_usefulness')


class NoMatching:
    def __getattr__(self, name):
        raise AssertionError(f'The survey must not call retrieval or the LLM: {name}')


@pytest.fixture
def survey_app(tmp_path):
    return create_app({'TESTING': True, 'DATABASE_PATH': str(tmp_path / 'survey.sqlite3'),
                       'OPENAI_API_KEY': '', 'SEED_DUMMY_DATA': False},
                      retriever=NoMatching(), llm=NoMatching())


def payload(**changes):
    return {'submission_id': 'a' * 32, 'version': 'diana-v3',
            'age_group': '21_24', 'gender': 'not_specified', 'education': 'master',
            'study_field': 'Informatik', 'search_goal': 'Werkstudent; Softwareentwicklung.\nGern mit Python.',
            **dict.fromkeys(RATING_FIELDS, 8), **changes}


def legacy_payload(**changes):
    return {'submission_id': 'b' * 32, 'version': 'diana-v1', 'chat_helpfulness': 4,
            'added_value': 'some', 'future_preference': 'rather_yes', 'feedback': 'Gute Bedienung.', **changes}


def records(app):
    with app.extensions['survey_store'].connect() as db:
        return [dict(row) for row in db.execute('SELECT * FROM survey_responses')]


def test_questionnaire_definition_matches_the_validated_api_contract():
    assert SURVEY_DEFINITION['version'] == 'diana-v3'
    assert set(SurveySubmission.model_fields) - {'submission_id', 'version'} == {f['name'] for f in SURVEY_FIELDS}
    assert {f['name'] for f in SURVEY_FIELDS if f['kind'] == 'scale'} == set(RATING_FIELDS)
    for field in SURVEY_FIELDS:
        for value, _ in field.get('options', []):
            assert SurveySubmission(**payload(**{field['name']: value}))


def test_answers_are_persisted_without_chat_or_retrieval(survey_app):
    response = survey_app.test_client().post('/api/survey-responses', json=payload())
    assert response.status_code == 201
    assert response.json == {'saved': True}
    assert response.headers['Cache-Control'] == 'no-store'
    store = SurveyStore(survey_app.config['DATABASE_PATH'])
    with store.connect() as db:
        row = dict(db.execute('SELECT * FROM survey_responses').fetchone())
        assert db.execute('SELECT COUNT(*) FROM chat_sessions').fetchone()[0] == 0
    assert set(row) == {'submission_id', 'created_at', 'answers_json'}
    assert row['created_at'].endswith('+00:00')
    assert json.loads(row['answers_json']) == {k: v for k, v in payload().items() if k != 'submission_id'}


def test_retry_is_idempotent_and_preserves_timestamp(survey_app):
    client = survey_app.test_client()
    assert client.post('/api/survey-responses', json=payload()).status_code == 201
    before = records(survey_app)
    assert client.post('/api/survey-responses', json=payload()).status_code == 200
    assert records(survey_app) == before
    assert client.post('/api/survey-responses', json=payload(chat_helpfulness=1)).status_code == 409
    assert records(survey_app) == before


def test_concurrent_retry_inserts_only_once(survey_app):
    store = survey_app.extensions['survey_store']
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: store.save(SurveySubmission(**payload())), range(4)))
    assert results.count(True) == 1
    assert len(records(survey_app)) == 1


@pytest.mark.parametrize('changes', [
    {'submission_id': 'short'}, {'submission_id': 'A' * 32}, {'submission_id': "' OR 1=1"},
    {'version': 'future-version'}, {'chat_helpfulness': 0}, {'chat_helpfulness': 11},
    {'chat_helpfulness': True}, {'chat_helpfulness': '4'}, {'chat_helpfulness': 4.5},
    {'age_group': 'unknown'}, {'gender': ''}, {'education': None},
    {'study_field': 'x' * 161}, {'search_goal': 'x' * 1001}, {'search_goal': '   '},
    {'search_goal': None}, {'profile': {'query': 'Private information'}}, {'session_id': 'secret'},
    {'feedback': 'Removed v1 field'},
])
def test_invalid_input_is_rejected_without_echoing_answers(survey_app, changes):
    response = survey_app.test_client().post('/api/survey-responses', json=payload(**changes))
    assert response.status_code == 400
    assert response.json['error']['code'] == 'validation_error'
    assert 'Private information' not in response.get_data(as_text=True)
    assert records(survey_app) == []


@pytest.mark.parametrize('field', ['submission_id', 'version', 'age_group', 'gender', 'education', 'search_goal', *RATING_FIELDS])
def test_required_fields(survey_app, field):
    data = payload()
    del data[field]
    assert survey_app.test_client().post('/api/survey-responses', json=data).status_code == 400


@pytest.mark.parametrize('field', RATING_FIELDS)
def test_every_rating_accepts_one_and_ten_but_rejects_eleven(survey_app, field):
    client = survey_app.test_client()
    for value, token in [(1, 'c' * 32), (10, 'd' * 32)]:
        assert client.post('/api/survey-responses', json=payload(**{field: value, 'submission_id': token})).status_code == 201
    assert client.post('/api/survey-responses', json=payload(**{field: 11})).status_code == 400


def test_demographics_allow_no_disclosure_and_field_is_optional(survey_app):
    data = payload(age_group='not_specified', gender='not_specified', education='not_specified')
    del data['study_field']
    assert survey_app.test_client().post('/api/survey-responses', json=data).status_code == 201
    assert json.loads(records(survey_app)[0]['answers_json'])['study_field'] == ''


def test_distinct_participants_are_saved_even_with_identical_answers(survey_app):
    client = survey_app.test_client()
    for token in ['a' * 32, 'b' * 32]:
        assert client.post('/api/survey-responses', json=payload(submission_id=token)).status_code == 201
    assert len(records(survey_app)) == 2


def test_malformed_requests_and_no_public_export(survey_app):
    client = survey_app.test_client()
    assert client.post('/api/survey-responses', data='text').status_code == 415
    assert client.post('/api/survey-responses', data='{', content_type='application/json').status_code == 400
    assert client.get('/api/survey-responses').status_code == 405
    assert client.get('/api/survey-responses/export').status_code == 404


def test_server_cli_exports_labels_unicode_newlines_and_no_overwrite(survey_app, tmp_path):
    client = survey_app.test_client()
    assert client.post('/api/survey-responses', json=payload()).status_code == 201
    output = tmp_path / 'umfrage.csv'
    runner = survey_app.test_cli_runner()
    result = runner.invoke(args=['survey-export', '--output', str(output)])
    assert result.exit_code == 0, result.output
    assert '1 Umfrageantworten exportiert' in result.output
    raw = output.read_bytes()
    assert raw.startswith(b'\xef\xbb\xbf')
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';'))
    assert len(rows) == 2 and len(rows[0]) == 111
    assert rows[1][3:8] == ['21–24 Jahre', 'Keine Angabe', 'Masterstudium', 'Informatik', payload()['search_goal']]
    assert rows[1][8:21] == ['8'] * 13
    assert rows[1][21:25] == [''] * 4
    assert '(1–10)' in rows[0][8]
    assert runner.invoke(args=['survey-export', '--output', str(output)]).exit_code != 0
    assert output.read_bytes() == raw


def test_old_forms_remain_submittable_and_export_separately_without_rescaling(survey_app):
    client = survey_app.test_client()
    assert client.post('/api/survey-responses', json=legacy_payload()).status_code == 201
    assert client.post('/api/survey-responses', json=legacy_payload()).status_code == 200
    assert client.post('/api/survey-responses', json=legacy_payload(chat_helpfulness=10)).status_code == 400
    assert client.post('/api/survey-responses', json=payload()).status_code == 201
    stream = io.StringIO()
    survey_app.extensions['survey_store'].export_csv(stream)
    rows = list(csv.reader(io.StringIO(stream.getvalue()), delimiter=';'))
    assert all(header.startswith('V1: ') for header in rows[0][21:25])
    assert rows[1][2] == 'diana-v1' and rows[1][3:21] == [''] * 18
    assert rows[1][21:25] == ['4', 'Etwas Mehrwert', 'Eher ja', 'Gute Bedienung.']
    assert rows[2][2] == 'diana-v3' and rows[2][8:21] == ['8'] * 13


@pytest.mark.parametrize('text', ['=HYPERLINK("test")', '+1', '-1', '@SUM(A1)', '\t=1', ' \n@SUM(A1)'])
def test_csv_formula_escaping(text):
    assert spreadsheet_text(text) == "'" + text


def test_export_escapes_all_user_text_and_empty_export_has_headers(survey_app):
    store = survey_app.extensions['survey_store']
    empty = io.StringIO()
    assert store.export_csv(empty) == 0
    assert len(list(csv.reader(io.StringIO(empty.getvalue()), delimiter=';'))) == 1
    store.save(SurveySubmission(**payload(study_field='=1+1', search_goal='@SUM(A1)')))
    store.save(LegacySurveySubmission(**legacy_payload(feedback='=1+1')))
    stream = io.StringIO()
    assert store.export_csv(stream) == 2
    rows = list(csv.reader(io.StringIO(stream.getvalue()), delimiter=';'))
    assert rows[1][6:8] == ["'=1+1", "'@SUM(A1)"]
    assert rows[2][24] == "'=1+1"
    assert spreadsheet_text('Sehr gut – danke!') == 'Sehr gut – danke!'


@pytest.mark.parametrize('path', ['/', '/index.html', '/umfrage', '/umfrage/'])
def test_survey_page_serves_same_spa_entry(survey_app, tmp_path, monkeypatch, path):
    import app as app_module
    dist = tmp_path / 'web-dist'
    dist.mkdir()
    (dist / 'index.html').write_text('<html>DIANA survey entry</html>')
    monkeypatch.setattr(app_module, 'BASE_DIR', tmp_path)
    response = survey_app.test_client().get(path)
    assert response.status_code == 200
    assert response.get_data(as_text=True) == '<html>DIANA survey entry</html>'


def test_v2_forms_and_retries_still_work_and_new_usefulness_columns_remain_empty(survey_app):
    old = {key: value for key, value in payload(version='diana-v2').items()
           if key in SurveySubmissionV2.model_fields}
    client = survey_app.test_client()
    assert client.post('/api/survey-responses', json=old).status_code == 201
    assert client.post('/api/survey-responses', json=old).status_code == 200
    stream = io.StringIO()
    survey_app.extensions['survey_store'].export_csv(stream)
    rows = list(csv.reader(io.StringIO(stream.getvalue()), delimiter=';'))
    assert rows[1][2] == 'diana-v2'
    for index, field in enumerate(SURVEY_FIELDS, start=3):
        if field['name'].endswith('_usefulness'):
            assert rows[1][index] == ''
        elif field['kind'] == 'scale':
            assert rows[1][index] == '8'
    assert len(records(survey_app)) == 1
