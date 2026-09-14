"""ABC questionnaire: comparable shared outcomes and version-safe resumption."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from survey_store import (V8_SURVEY_DEFINITION as SURVEY_DEFINITION, V8_SURVEY_FIELDS as SURVEY_FIELDS, V7_SURVEY_DEFINITION,
                          SurveyRequest, SurveyDraftRequest, field_visible, answer_status)


def payload(arm):
    answers = {field['name']: 8 if field['kind'] == 'scale'
               else field['options'][0][0] if field['kind'] == 'choice'
               else '' if field.get('optional') else 'Softwareentwicklung'
               for field in SURVEY_FIELDS}
    answers['study_arm'] = arm
    for field in SURVEY_FIELDS:
        if not field_visible(field, answers):
            answers[field['name']] = None
    return dict(version='diana-v8', submission_id='a' * 32, **answers)


def test_v7_questionnaire_is_unchanged_archive_and_v8_has_three_groups():
    assert SURVEY_DEFINITION['version'] == 'diana-v8'
    assert V7_SURVEY_DEFINITION == json.loads(Path('survey_definition.json').read_text())
    assert V7_SURVEY_DEFINITION['version'] == 'diana-v7'
    assert SURVEY_DEFINITION['demographics']['fields'][0]['codes'] == {'A': 0, 'B': 1, 'C': 2}
    fields = {field['name']: field for field in SURVEY_FIELDS}
    common = ['search_ease', 'express_search_needs', 'adapt_search_ease', 'search_effort',
              'system_usefulness', 'future_use', 'chat_helpfulness', 'search_refinement']
    for name in common:
        assert not fields[name].get('visibleIf')
    for name in ['score_usefulness', 'match_reasons_usefulness', 'personality_consistency',
                 'personalized_chat_usefulness', 'personalized_search_usefulness']:
        assert fields[name]['visibleIf'] == {'field': 'study_arm', 'in': ['B', 'C']}
    assert fields['template_selection_ease']['visibleIf']['equals'] == 'B'
    assert fields['personality_customized']['visibleIf']['equals'] == 'C'
    assert fields['personality_setup']['visibleIf']['equals'] == 'C'


@pytest.mark.parametrize('arm', ['A', 'B', 'C'])
def test_final_and_draft_enforce_arm_specific_questions(arm):
    body = payload(arm)
    assert SurveyRequest.model_validate(body).root.model_dump() == body
    answers = {name: value for name, value in body.items() if name not in ('version', 'submission_id')}
    assert SurveyDraftRequest.model_validate(dict(version='diana-v8', submission_id='a'*32,
                                                 revision=1, answers=answers))
    for field in SURVEY_FIELDS:
        if not field.get('visibleIf'):
            continue
        visible = field_visible(field, body)
        invalid = None if visible else (8 if field['kind'] == 'scale' else 'yes')
        with pytest.raises(ValidationError):
            SurveyRequest.model_validate(body | {field['name']: invalid})
        assert answer_status(field, body) == ('answered' if visible else 'skipped')


def test_nonuse_is_explicit_and_never_becomes_a_low_score():
    b, c = payload('B'), payload('C')
    assert SurveyRequest.model_validate(b | {'template_selection_ease': 'not_used'})
    assert SurveyRequest.model_validate(c | {'personality_setup': 'not_used', 'personality_customized': 'no'})
    for arm in ['B', 'C']:
        for name in ['score_usefulness', 'match_reasons_usefulness', 'personalized_chat_usefulness', 'personalized_search_usefulness']:
            for value in ['not_used', 'not_assessable']:
                assert SurveyRequest.model_validate(payload(arm) | {name: value})
