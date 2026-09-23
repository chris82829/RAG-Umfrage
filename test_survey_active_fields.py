"""The browser submits active questionnaire items, never removed questions."""
import json
import sqlite3

import pytest
from pydantic import ValidationError

import test_study_progress_v12 as study_fixture
from survey_store import SURVEY_DEFINITION, SURVEY_VERSION, SurveyRequest


def browser_payload(arm):
    # Match frontend/survey.js: demographics + categories, excluding retiredFields.
    payload = dict(submission_id=arm.lower() * 32, version=SURVEY_VERSION, study_arm=arm)
    for group in [SURVEY_DEFINITION['demographics'], *SURVEY_DEFINITION['categories']]:
        for field in group['fields']:
            if field['name'] == 'study_arm':
                continue
            payload[field['name']] = (4 if field['kind'] == 'scale' else
                                      field['options'][0][0] if field['kind'] == 'choice' else
                                      '' if field.get('optional') else 'Studentische Python-Stelle')
    return payload


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
def test_actual_browser_payload_finishes_and_does_not_fabricate_retired_answers(arm):
    f = study_fixture.StudyProgressTests()
    f.setUp()
    try:
        headers = f.grant(arm)
        state = f.onboard(headers)
        for _ in range(3):
            state = f.chat(headers, state).json
        payload = browser_payload(arm)
        assert 'personality_customized' not in payload
        assert 'previous_participation' not in payload
        response = f.client.post('/api/survey-responses', headers=headers, json=payload)
        assert response.status_code == 201, response.json
        assert response.json == {'saved': True}
        assert f.client.get('/api/survey-drafts/' + payload['submission_id'], headers=headers).json == {
            'draft': {'completed': True, 'version': SURVEY_VERSION}}
        with sqlite3.connect(f.app.config['DATABASE_PATH']) as db:
            rows = db.execute('SELECT answers_json FROM survey_responses').fetchall()
        assert len(rows) == 1
        saved = json.loads(rows[0][0])
        assert saved['study_arm'] == arm
        assert saved.get('personality_customized') is None
        assert saved.get('previous_participation') is None
        assert saved['usefulness_ideal'] == 4
    finally:
        f.doCleanups()


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
def test_missing_active_answer_is_still_rejected(arm):
    payload = browser_payload(arm)
    del payload['usefulness_ideal']
    with pytest.raises(ValidationError):
        SurveyRequest.model_validate(payload)
