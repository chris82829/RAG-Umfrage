"""Regression: every candidate needs one assessment, including 20-job Nano calls."""
import copy
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from openai.lib._pydantic import to_strict_json_schema
from pydantic import ValidationError

from llm_service import (
    LLMUnavailable, MODEL, OpenAIService, _candidate_reranking_schema,
)
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
    assert responses.calls[0]['model'] == MODEL
    assert responses.calls[0]['reasoning'] == {"effort": "none"}
    if policy == 'unprompted':
        assert [item['role'] for item in responses.calls[0]['input']] == ['user']
    again = service.rerank({}, PROFILE, CANDIDATES,
                           assessment_cache=result['assessment_cache'], **args)
    assert again['rankings'] == result['rankings']
    assert again['_scoring_metadata']['assessment_reused'] == (policy != 'unprompted')
    assert len(responses.calls) == 2  # no retry or follow-up completion calls


def test_job_ids_cannot_collide_with_pydantic_fields():
    ids = ['model_fields', 'model_dump', 'candidate_0', 'id.with/hyphen-1']
    schema = _candidate_reranking_schema(ids)
    assert set(schema.model_validate(payload(ids)).rankings.model_dump(by_alias=True)) == set(ids)


class StreamingResponses:
    def __init__(self, complete=True):
        self.complete = complete

    @contextmanager
    def stream(self, **options):
        data = payload()
        if not self.complete:
            data['rankings'].pop(IDS[-1])
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


def test_incomplete_stream_never_commits_a_partial_candidate_pool():
    service = OpenAIService('', client=SimpleNamespace(responses=StreamingResponses(False)))
    with pytest.raises(LLMUnavailable):
        list(service.rerank_steps({}, PROFILE, CANDIDATES, stream=True,
                                 prompt_policy='unprompted', system_prompt=''))


@pytest.mark.parametrize('count', [1, 7])
def test_pools_smaller_than_twenty_are_preserved(count):
    responses = CapturingResponses()
    service = OpenAIService('', client=SimpleNamespace(responses=responses))
    result = service.rerank({}, PROFILE, CANDIDATES[:count], prompt_policy='unprompted', system_prompt='')
    assert [item['job_id'] for item in result['rankings']] == IDS[:count]
