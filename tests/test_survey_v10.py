"""Shortened questions are a separate cohort, never a rewrite of V9 answers."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from privacy import token_hash
from study_assignment import EXPERIMENT_ID, PREVIOUS_FAIR_EXPERIMENT_ID
from survey_store import (SURVEY_DEFINITION, SURVEY_FIELDS, V9_SURVEY_DEFINITION,
                          V9_SURVEY_FIELDS, SurveyRequest, SurveyDraftRequest,
                          SurveySubmissionV10, SurveyStore, field_visible)
from test_study_assignment import experiment, assign
from test_survey_v7 import versioned_payload


REMOVED = {'search_ease', 'express_search_needs', 'adapt_search_ease',
           'template_selection_ease', 'personality_setup'}


def test_v10_removes_only_five_items_and_preserves_all_other_wording():
    old = deepcopy(V9_SURVEY_DEFINITION)
    assert old['version'] == 'diana-v9'
    assert REMOVED <= {field['name'] for field in V9_SURVEY_FIELDS}
    old['version'] = 'diana-v10'
    for group in [old['demographics'], *old['categories']]:
        group['fields'] = [field for field in group['fields'] if field['name'] not in REMOVED]
    assert SURVEY_DEFINITION == old
    assert not REMOVED & set(SurveySubmissionV10.model_fields)
    assert next(field for field in SURVEY_FIELDS if field['name'] == 'system_usefulness') == next(
        field for field in V9_SURVEY_FIELDS if field['name'] == 'system_usefulness')


@pytest.mark.parametrize('arm,count', [('A', 15), ('B', 20), ('C', 21)])
def test_visible_question_count_and_primary_requirement(arm, count):
    visible = [field for field in SURVEY_FIELDS
               if not field.get('systemProvided') and field_visible(field, {'study_arm': arm})]
    assert len(visible) == count
    assert [field['name'] for field in visible if field.get('optional')] == ['study_field', 'feedback']
    body = versioned_payload('diana-v10', arm)
    assert SurveyRequest.model_validate(body).root.model_dump() == body
    for name in REMOVED:
        with pytest.raises(ValidationError):
            SurveyRequest.model_validate(body | {name: 8})
    with pytest.raises(ValidationError):
        SurveyRequest.model_validate({name: value for name, value in body.items() if name != 'system_usefulness'})


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
def test_v9_final_and_partial_answers_stay_valid_and_unchanged(tmp_path, arm):
    old = versioned_payload('diana-v9', arm)
    submission = SurveyRequest.model_validate(old).root
    assert submission.model_dump() == old
    store = SurveyStore(tmp_path / 'answers.sqlite3')
    answers = {name: value for name, value in old.items() if name not in ('version', 'submission_id')}
    draft = SurveyDraftRequest.model_validate(dict(
        version='diana-v9', submission_id=old['submission_id'], revision=1,
        answers=answers, waiting_answered=['age_group'])).root
    store.save_draft(draft)
    restored = store.get_draft(old['submission_id'])
    assert restored['version'] == 'diana-v9' and restored['answers'] == answers
    assert restored['waiting_answered'] == ['age_group']
    assert REMOVED <= set(restored['answers'])
    store.save(submission)
    assert store.save(submission) is False
    assert store.get_draft(old['submission_id']) == {'completed': True}


@pytest.mark.parametrize('arm,policy', [('A', 'standard'), ('B', 'templates'), ('C', 'configurable')])
def test_v9_assignments_restore_without_changing_treatment_or_accepting_v10(experiment, monkeypatch, arm, policy):
    app, model = experiment
    client, headers, old = assign(app, monkeypatch, arm, experiment_id=PREVIOUS_FAIR_EXPERIMENT_ID)
    assert old['experiment_id'] == 'diana-abc-v2'
    assert old['questionnaire_version'] == 'diana-v9'
    assert old['personality_policy'] == policy and old['presentation_policy'] == 'ranked_insights'
    draft = dict(version='diana-v9', submission_id='a'*32, revision=1,
                 answers={'study_arm': arm, 'search_ease': 7, 'express_search_needs': 8})
    assert client.put('/api/survey-drafts', headers=headers, json=draft).status_code == 200
    before = client.get('/api/survey-drafts/'+'a'*32, headers=headers).json
    monkeypatch.setattr('study_assignment.secrets.choice', lambda _: pytest.fail('Must retain original assignment'))
    assert client.post('/api/study-assignment', headers=headers).json == old
    wrong = dict(draft, version='diana-v10', revision=2, answers={'study_arm': arm})
    assert client.put('/api/survey-drafts', headers=headers, json=wrong).status_code == 400
    assert client.get('/api/survey-drafts/'+'a'*32, headers=headers).json == before
    with app.extensions['survey_store'].connect() as db:
        row = db.execute('SELECT * FROM study_assignments WHERE token_hash=?',
                         (token_hash(headers['X-Diana-Consent']),)).fetchone()
        assert row['experiment_id'] == PREVIOUS_FAIR_EXPERIMENT_ID and row['assigned_at'] == old['assigned_at']
    assert model.calls == []


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
def test_new_short_drafts_require_new_assignment_and_only_factual_waiting_answers(experiment, monkeypatch, arm):
    app, model = experiment
    client, headers, assignment = assign(app, monkeypatch, arm, experiment_id=EXPERIMENT_ID)
    assert assignment['experiment_id'] == 'diana-abc-v3' and assignment['questionnaire_version'] == 'diana-v10'
    draft = dict(version='diana-v10', submission_id='b'*32, revision=1,
                 answers={'study_arm': arm, 'search_goal': 'Data Science'}, waiting_answered=['search_goal'])
    assert client.put('/api/survey-drafts', headers=headers, json=draft).status_code == 200
    assert client.get('/api/survey-drafts/'+'b'*32, headers=headers).json['draft']['version'] == 'diana-v10'
    assert client.put('/api/survey-drafts', headers=headers, json=draft | {'version': 'diana-v9'}).status_code == 400
    for name in ['personality_setup', 'template_selection_ease', 'personality_customized']:
        with pytest.raises(ValidationError, match='Sachangaben'):
            SurveyDraftRequest.model_validate(draft | {'waiting_answered': [name]})
    assert model.calls == []
