"""Conference study measures the same outcomes after use in all three arms."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from survey_store import (SURVEY_DEFINITION, SURVEY_FIELDS, V8_SURVEY_DEFINITION,
                          SurveyRequest, SurveyDraftRequest, field_visible)


def payload(arm):
    answers = {field['name']: 8 if field['kind'] == 'scale'
               else field['options'][0][0] if field['kind'] == 'choice'
               else '' if field.get('optional') else 'Softwareentwicklung'
               for field in SURVEY_FIELDS}
    answers['study_arm'] = arm
    for field in SURVEY_FIELDS:
        if not field_visible(field, answers):
            answers[field['name']] = None
    return dict(version='diana-v9', submission_id='a' * 32, **answers)


def test_current_outcomes_and_scores_are_identical_for_abc_without_rewriting_v8():
    assert SURVEY_DEFINITION['version'] == 'diana-v9'
    fields = {field['name']: field for field in SURVEY_FIELDS}
    for name in ['search_ease', 'express_search_needs', 'adapt_search_ease', 'search_effort',
                 'system_usefulness', 'future_use', 'chat_helpfulness', 'search_refinement',
                 'score_usefulness', 'match_reasons_usefulness']:
        assert not fields[name].get('visibleIf')
        old = next(field for group in V8_SURVEY_DEFINITION['categories'] for field in group['fields'] if field['name'] == name)
        unchanged = deepcopy(old)
        unchanged.pop('visibleIf', None)
        assert fields[name] == unchanged
    primary = fields['system_usefulness']
    assert primary['kind'] == 'scale'
    assert primary['title'] == 'Wie hilfreich war das System für die Durchführung deiner Suche?'
    assert fields['personality_customized']['visibleIf'] == {'field': 'study_arm', 'equals': 'C'}
    old_score = next(field for group in V8_SURVEY_DEFINITION['categories'] for field in group['fields'] if field['name'] == 'score_usefulness')
    assert old_score['visibleIf'] == {'field': 'study_arm', 'in': ['B', 'C']}


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
def test_complete_abc_responses_require_same_primary_and_score_answers(arm):
    body = payload(arm)
    assert SurveyRequest.model_validate(body).root.model_dump() == body
    for name in ['system_usefulness', 'score_usefulness', 'match_reasons_usefulness']:
        with pytest.raises(ValidationError):
            SurveyRequest.model_validate(body | {name: None})
        assert SurveyRequest.model_validate(body | {name: 'not_assessable'})
    if arm == 'A':
        assert body['personality_customized'] is body['personality_setup'] is body['template_selection_ease'] is None


def test_prior_experience_is_factual_and_allows_nondisclosure():
    fields = [field for field in SURVEY_FIELDS if field.get('beforeSystem')]
    assert [field['name'] for field in fields] == ['job_portal_experience', 'ai_chat_experience']
    for field in fields:
        assert field['kind'] == 'choice' and field['level'] == 'ordinal'
        assert field['codes'] == {'never': 0, 'occasionally': 1, 'weekly': 2, 'daily': 3}
        for value in ['never', 'occasionally', 'weekly', 'daily', 'not_specified']:
            assert SurveyRequest.model_validate(payload('C') | {field['name']: value})


def test_waiting_marker_accepts_facts_and_rejects_any_evaluation():
    base = dict(version='diana-v9', submission_id='a'*32, revision=1,
                answers={'study_arm': 'C', 'job_portal_experience': 'never', 'ai_chat_experience': 'daily'})
    assert SurveyDraftRequest.model_validate(base | {'waiting_answered': ['job_portal_experience', 'ai_chat_experience']})
    for name in ['personality_customized', 'personality_setup', 'template_selection_ease']:
        with pytest.raises(ValidationError, match='Sachangaben'):
            SurveyDraftRequest.model_validate(base | {'waiting_answered': [name]})
