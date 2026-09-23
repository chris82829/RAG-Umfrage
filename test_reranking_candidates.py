"""Regression: every candidate needs one assessment, including 20-job Nano calls."""
import copy
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from openai.lib._pydantic import to_strict_json_schema
from pydantic import ValidationError

from llm_service import (
    LLMUnavailable, MODEL, OpenAIService, _candidate_reranking_schema, _candidate_scoring_schema,
)
from advisor import score_from_components
from system_prompt_store import DEFAULT_SYSTEM_PROMPTS
from test_system_prompts import CapturingResponses, PROFILE


IDS = [str(851600 + index) for index in range(20)]
CANDIDATES = [{"job": {"id": job_id, "title": "Werkstudent Python",
                         "requirements": "Python", "tasks": "Daten auswerten"},
               "rrf_score": 0.1} for job_id in IDS]
ASSESSMENT = {"components": {"technical_fit": 80, "preferences_fit": 70,
                            "technical_depth": 65, "learning": 60,
                            "innovation": 55, "clarity": 75},
              "reasons": ["Python passt.", "Konkrete Datenaufgaben."],
              "matched_skills": ["Python"], "missing_skills": []}


def payload(ids=IDS, cached=False):
    assessments = {job_id: copy.deepcopy(ASSESSMENT) for job_id in ids}
    if cached:
        for item in assessments.values():
            item.pop("components")
    return {"rankings": assessments, "assistant_message": "Python passt. Was ist dir wichtig?"}


@pytest.mark.parametrize("cached", [False, True])
def test_api_schema_requires_each_actual_id_and_forbids_other_ids(cached):
    schema = _candidate_reranking_schema(IDS, cached=cached)
    strict = to_strict_json_schema(schema)
    ref = strict['properties']['rankings']['$ref'].split('/')[-1]
    fields = strict['$defs'][ref]
    assert set(fields['properties']) == set(fields['required']) == set(IDS)
    assert fields['additionalProperties'] is False
    assert schema.model_validate(payload(cached=cached)).rankings.model_dump(by_alias=True).keys() == set(IDS)
    incomplete = payload(cached=cached)
    incomplete['rankings'].pop(IDS[-1])
    with pytest.raises(ValidationError):
        schema.model_validate(incomplete)
    unknown = payload(cached=cached)
    unknown['rankings']['invented-id'] = unknown['rankings'].pop(IDS[-1])
    with pytest.raises(ValidationError):
        schema.model_validate(unknown)
    repeated_list = {"rankings": [{"job_id": IDS[0], **ASSESSMENT}] * 20,
                     "assistant_message": "Ungültige Auswahl."}
    with pytest.raises(ValidationError):
        schema.model_validate(repeated_list)


@pytest.mark.parametrize("policy", list(DEFAULT_SYSTEM_PROMPTS))
def test_twenty_candidates_return_in_public_list_and_cached_scores_stay_fixed(policy):
    responses = CapturingResponses()
    service = OpenAIService('', client=SimpleNamespace(responses=responses))
    args = dict(prompt_policy=policy, system_prompt=DEFAULT_SYSTEM_PROMPTS[policy])
    result = service.rerank({}, PROFILE, CANDIDATES, **args)
    assert [item['job_id'] for item in result['rankings']] == IDS  # stable ties
    assert len(result['assessment_cache']['components']) == 20
    assert [r['job_id'] for r in result['rankings'] if r['reasons']] == IDS[:5]
    assert all(r['reason'] == '' and r['matched_skills'] == [] and r['missing_skills'] == []
               for r in result['rankings'][5:])
    assert responses.calls[0]['model'] == MODEL
    assert responses.calls[0]['reasoning'] == {"effort": "none"}
    if policy == 'unprompted':
        assert [item['role'] for item in responses.calls[0]['input']] == ['user']
    again = service.rerank({}, PROFILE, CANDIDATES,
                           assessment_cache=result['assessment_cache'], **args)
    assert again['rankings'] == result['rankings']
    assert again['_scoring_metadata']['assessment_reused'] == (policy != 'unprompted')
    assert len(responses.calls) == (4 if policy == 'unprompted' else 3)


def test_job_ids_cannot_collide_with_pydantic_fields():
    ids = ['model_fields', 'model_dump', 'candidate_0', 'id.with/hyphen-1']
    schema = _candidate_reranking_schema(ids)
    assert set(schema.model_validate(payload(ids)).rankings.model_dump(by_alias=True)) == set(ids)


class StreamingResponses:
    def __init__(self, complete=True, explanations_complete=True):
        self.complete = complete
        self.explanations_complete = explanations_complete

    @contextmanager
    def stream(self, **options):
        request = json.loads(options['input'][-1]['content'])
        ids = [job['id'] for job in request.get('jobs', request.get('candidates', []))]
        is_scoring = 'Scoring' in options['text_format'].__name__
        if is_scoring:
            data = {'rankings': {job_id: copy.deepcopy(ASSESSMENT['components']) for job_id in ids}}
        else:
            data = payload(ids, cached=True)
        if (is_scoring and not self.complete) or (not is_scoring and not self.explanations_complete):
            data['rankings'].pop(ids[-1])
        text = json.dumps(data)
        # The preview includes the candidate map. Only a fully validated final
        # result can become public cards, with the original list contract.
        class Events:
            def __iter__(self):
                yield SimpleNamespace(type='response.output_text.delta', snapshot=text[:-5])
                yield SimpleNamespace(type='response.output_text.delta', snapshot=text)

            def get_final_response(self):
                return SimpleNamespace(status='completed', usage=None, output_parsed=data)
        yield Events()


def test_streaming_twenty_candidates_keeps_previews_and_list_contract():
    service = OpenAIService('', client=SimpleNamespace(responses=StreamingResponses()))
    steps = service.rerank_steps({}, PROFILE, CANDIDATES, stream=True,
                                  prompt_policy='unprompted', system_prompt='')
    previews = []
    while True:
        try:
            previews.append(next(steps))
        except StopIteration as done:
            result = done.value
            break
    assert previews and all(item['type'] == 'assistant_preview' for item in previews)
    assert len(result['rankings']) == 20
    assert {item['job_id'] for item in result['rankings']} == set(IDS)
    assert sum(bool(item['reasons']) for item in result['rankings']) == 5


def test_incomplete_stream_never_commits_a_partial_candidate_pool():
    service = OpenAIService('', client=SimpleNamespace(responses=StreamingResponses(False)))
    with pytest.raises(LLMUnavailable):
        list(service.rerank_steps({}, PROFILE, CANDIDATES, stream=True,
                                 prompt_policy='unprompted', system_prompt=''))


@pytest.mark.parametrize('count', [0, 1, 5, 7, 20])
def test_pools_smaller_than_twenty_are_preserved(count):
    responses = CapturingResponses()
    service = OpenAIService('', client=SimpleNamespace(responses=responses))
    result = service.rerank({}, PROFILE, CANDIDATES[:count], prompt_policy='unprompted', system_prompt='')
    assert [item['job_id'] for item in result['rankings']] == IDS[:count]
    assert sum(bool(item['reasons']) for item in result['rankings']) == min(count, 5)
    assert len(responses.calls) == (2 if count else 0)


def test_score_schema_requires_all_twenty_without_prose():
    schema = _candidate_scoring_schema(IDS)
    strict = to_strict_json_schema(schema)
    assert set(strict['properties']) == {'rankings'}
    ref = strict['properties']['rankings']['$ref'].split('/')[-1]
    assert set(strict['$defs'][ref]['required']) == set(IDS)
    scores = {job_id: ASSESSMENT['components'] for job_id in IDS}
    schema.model_validate({'rankings': scores})
    with pytest.raises(ValidationError):
        schema.model_validate({'rankings': {job_id: values for job_id, values in scores.items() if job_id != IDS[-1]}})


@pytest.mark.parametrize('policy', list(DEFAULT_SYSTEM_PROMPTS))
def test_explanations_follow_server_scores_not_retrieval_order_or_model_key_order(policy):
    class DifferentScores(CapturingResponses):
        def parse(self, **options):
            result = super().parse(**options)
            if 'Scoring' in options['text_format'].__name__:
                data = result.output_parsed.model_dump(by_alias=True)
                for index, job_id in enumerate(IDS):
                    data['rankings'][job_id] = {key: 30 + index for key in ASSESSMENT['components']}
                data['rankings'] = dict(reversed(list(data['rankings'].items())))
                result.output_parsed = options['text_format'].model_validate(data)
            return result
    responses = DifferentScores()
    service = OpenAIService('', client=SimpleNamespace(responses=responses))
    result = service.rerank({}, PROFILE, CANDIDATES, prompt_policy=policy,
                            system_prompt=DEFAULT_SYSTEM_PROMPTS[policy])
    expected_ids = list(reversed(IDS))
    assert [r['job_id'] for r in result['rankings']] == expected_ids
    assert [r['job_id'] for r in result['rankings'] if r['reasons']] == expected_ids[:5]
    assert all(r['score'] == score_from_components(r['components']) for r in result['rankings'])
    explanation_call = responses.calls[-1]
    request = json.loads(explanation_call['input'][-1]['content'])
    assert request['selected_job_ids'] == expected_ids[:5]
    assert request['requested_count'] == 5 and request['evaluated_candidate_count'] == 20
    assert [j['id'] for j in request.get('jobs', request.get('candidates', []))] == expected_ids[:5]
    explanation_schema = explanation_call['text_format']
    invalid = payload(expected_ids[:5], cached=True)
    invalid['rankings'][expected_ids[0]]['components'] = ASSESSMENT['components']
    with pytest.raises(ValidationError):
        explanation_schema.model_validate(invalid)  # prose cannot overwrite scores


def test_failed_explanations_do_not_commit_partially_scored_cards():
    service = OpenAIService('', client=SimpleNamespace(responses=StreamingResponses(explanations_complete=False)))
    with pytest.raises(LLMUnavailable):
        list(service.rerank_steps({}, PROFILE, CANDIDATES, stream=True,
                                 prompt_policy='unprompted', system_prompt=''))


@pytest.mark.parametrize('policy', ['career_fixed', 'custom_career'])
def test_explanation_context_has_no_dangling_job_detail_references(policy):
    responses = CapturingResponses()
    service = OpenAIService('', client=SimpleNamespace(responses=responses))
    service.rerank({}, PROFILE, CANDIDATES, prompt_policy=policy,
                   system_prompt=DEFAULT_SYSTEM_PROMPTS[policy],
                   chat_context={'jobs': CANDIDATES})
    request = json.loads(responses.calls[-1]['input'][-1]['content'])
    candidate_ids = {job['id'] for job in request['candidates']}
    previous = request['conversation_context']['previous_jobs']
    assert len(previous) == 20
    for job in previous:
        if 'details_from_candidate_id' in job:
            assert job['details_from_candidate_id'] in candidate_ids
        else:
            assert job['title'] == 'Werkstudent Python'
