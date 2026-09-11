#!/usr/bin/env python3
"""Opt-in synthetic comparison of the real UI personality payloads.

Offline plan (no key read and no requests):
  NODE_BINARY=/path/to/node .venv/bin/python tools/evaluate_personality.py --output /tmp/plan.json
Live evaluation, only when explicitly requested:
  NODE_BINARY=/path/to/node .venv/bin/python tools/evaluate_personality.py --live --output /tmp/personality.json

One neutral bootstrap determines common evidence. A_neutral and four B personality
settings then use that same internal cache and the same follow-up question.
A exposes plain job cards; B exposes personality-specific scores and explanations.
Chat receives the public cards and greeting produced by the real application. This
is eleven logical model calls (SDK retries may add requests), at most two at once.
Mechanical checks do not assess style quality, factual validity, or study power.
No database, retrieval model, Flask application or participant session is created.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisor import AdvisorConfig, resolve_advisor
from app import public_state, welcome_message
from llm_service import MODEL, REASONING_EFFORT, OpenAIService, PersonaResult
from schemas import Profile

FIXTURE = Path(__file__).with_name("personality_fixture.json")
SOURCE_FILES = (
    "advisor.py", "app.py", "llm_service.py", "schemas.py",
    "frontend/advisor.js", "frontend/main.jsx", "frontend/score-visibility.js",
    "tools/evaluate_personality.py",
    "tools/personality_fixture.json",
)


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES}


def frontend_advisors():
    """Execute source exports, rather than maintaining a second set of templates."""
    source = """
      import { neutralAdvisor, advisorFromTemplate, validateAdvisor } from './frontend/advisor.js';
      const result = { A_neutral: neutralAdvisor };
      for (const name of ['steve', 'angela', 'guenther']) {
        result['B_' + name] = validateAdvisor(advisorFromTemplate(name));
      }
      process.stdout.write(JSON.stringify(result));
    """
    result = subprocess.run(
        [os.environ.get("NODE_BINARY", "node"), "--input-type=module", "-e", source],
        cwd=ROOT, capture_output=True, text=True, check=True, timeout=30,
    )
    return json.loads(result.stdout)


def neutral_patch(patch):
    """Check the full nested patch; clear_max_hours=False is the sole exception."""
    return patch == {
        "query": None, "skills": None, "preferences": None,
        "filters": {"employment_types": None, "locations": None, "remote": None,
                    "max_hours": None, "clear_max_hours": False},
    }


def text_metrics(value):
    return {"characters": len(value), "words": len(re.findall(r"\S+", value)),
            "question_marks": value.count("?")}


def result_cards(fixture, ranked):
    lookup = {item["job"]["id"]: item["job"] for item in fixture["candidates"]}
    return [{**deepcopy(lookup[item["job_id"]]), "match": deepcopy(item)}
            for item in ranked["rankings"]]


def evaluate_variant(label, advisor, fixture, common_cache, api_key):
    service = OpenAIService(api_key)
    started = time.perf_counter()
    ranked = service.rerank(
        deepcopy(fixture["persona"]), deepcopy(fixture["profile"]),
        deepcopy(fixture["candidates"]), advisor=deepcopy(advisor),
        assessment_cache=deepcopy(common_cache),
    )
    rerank_seconds = time.perf_counter() - started
    internal_cards = result_cards(fixture, ranked)
    resolved = resolve_advisor(advisor)
    state = {"jobs": internal_cards, "advisor": advisor,
             "assistant_message": ranked["assistant_message"]}
    # Both helpers are the application's real presentation boundary. A's internal
    # rerank text is deliberately absent from its displayed welcome message.
    greeting = welcome_message(state)
    public_cards = public_state(state)["jobs"]
    initially_visible = (public_cards if resolved["neutral"] else [
        card for card in public_cards if type(card.get("match", {}).get("score")) is int
        and 70 <= card["match"]["score"] <= 100
    ])
    started = time.perf_counter()
    chat = service.plan_chat(
        deepcopy(fixture["profile"]), [{"role": "assistant", "content": greeting}],
        fixture["chat_question"], jobs=deepcopy(public_cards), advisor=deepcopy(advisor),
        candidate_count=len(internal_cards), mode="auto",
    )
    chat_seconds = time.perf_counter() - started
    rankings = ranked["rankings"]
    checks = {
        "chat_answers_without_search": chat["action"] == "answer",
        "chat_profile_patch_unchanged": neutral_patch(chat["profile_patch"]),
        "common_components_preserved": ranked["assessment_cache"] == common_cache,
        "all_fixture_jobs_returned": sorted(item["job_id"] for item in rankings)
            == sorted(item["job"]["id"] for item in fixture["candidates"]),
        "internal_scores_within_1_100": all(type(item["score"]) is int and 1 <= item["score"] <= 100
                                   for item in rankings),
        "internal_reasons_within_contract": all(2 <= len(item["reasons"]) <= 3
            and all(0 < len(reason) <= 200 for reason in item["reasons"]) for item in rankings),
        "chat_within_600_characters": len(chat["assistant_message"]) <= 600,
        "internal_rerank_summary_within_600_characters": len(ranked["assistant_message"]) <= 600,
        "chat_at_most_one_question_mark": chat["assistant_message"].count("?") <= 1,
        "internal_rerank_summary_at_most_one_question_mark": ranked["assistant_message"].count("?") <= 1,
        "public_cards_match_arm": (
            all("match" not in card and "retrieval" not in card for card in public_cards)
            if resolved["neutral"] else all("match" in card for card in public_cards)),
        "basic_variant_initially_shows_all_cards": (
            not resolved["neutral"] or len(initially_visible) == len(public_cards)),
    }
    return {
        "label": label, "advisor_payload": advisor,
        "resolved_advisor": resolved,
        "internal_rerank": ranked,
        "public_presentation": {
            "greeting": greeting, "returned_cards": public_cards,
            "initially_visible_job_ids": [card["id"] for card in initially_visible],
            "scores_and_card_explanations_visible": not resolved["neutral"],
            "note": ("A displays every returned card without a score, prepared explanation or skill assessment."
                     if resolved["neutral"] else
                     "B initially displays scores of 70–100; other cards can be revealed. Only the first reason is initially expanded."),
        },
        "chat": chat,
        "counts": {"internally_evaluated": len(internal_cards),
                   "public_cards_returned": len(public_cards),
                   "initially_visible": len(initially_visible),
                   "initially_hidden": len(public_cards) - len(initially_visible)},
        "text_metrics": {"public_greeting": text_metrics(greeting),
                         "internal_rerank_summary": text_metrics(ranked["assistant_message"]),
                         "public_chat": text_metrics(chat["assistant_message"]),
                         "internal_first_reasons": {item["job_id"]: text_metrics(item["reasons"][0])
                                                    for item in rankings},
                         "initially_visible_first_reasons": {
                             card["id"]: text_metrics(card["match"]["reasons"][0])
                             for card in initially_visible if card.get("match", {}).get("reasons")}},
        "seconds": {"rerank": round(rerank_seconds, 3), "chat": round(chat_seconds, 3)},
        "mechanical_checks": checks,
        "mechanical_checks_passed": all(checks.values()),
    }


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="Explicitly permit eleven logical OpenAI calls with synthetic data.")
    parser.add_argument("--output", type=Path, default=Path("/tmp/diana-personality-evaluation.json"))
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output in {(ROOT / name).resolve() for name in SOURCE_FILES} or output.exists():
        parser.error("Choose a new output path; existing files and source files are never overwritten.")
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fixture["profile"] = Profile.model_validate(fixture["profile"]).model_dump(mode="json")
    PersonaResult.model_validate(fixture["persona"])
    advisors = frontend_advisors()
    advisors["B_custom"] = fixture["free_advisor"]
    for value in advisors.values():
        AdvisorConfig.model_validate(value)
    if any(advisors[label]["mode"] != "custom" for label in ("B_steve", "B_angela", "B_guenther")):
        raise ValueError("Expected current editable UI template payloads.")
    report = {
        "format_version": 2, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "prepared_offline", "live_requested": args.live,
        "model": MODEL, "reasoning_effort": REASONING_EFFORT, "response_store": False,
        "source_sha256": hashes(),
        "packages": {name: importlib.metadata.version(name) for name in ("openai", "pydantic")},
        "fixture": fixture, "advisor_payloads": advisors,
        "protocol": {
            "bootstrap": "Neutral evidence assessment; excluded from the style comparison.",
            "comparison": "A_neutral is the basic system; B_steve, B_angela, B_guenther and B_custom are four settings of the personalized package. All use an identical internal evidence cache and user question. Each chat receives its arm-specific public cards (the complete returned pool) and displayed greeting, as in the application.",
            "presentation": "A displays all returned cards without public scores or prepared card explanations. B initially shows cards at 70–100 points with scores and expandable explanations. Internal rerank text and assessments are recorded separately and must not be mistaken for what A participants see.",
            "planned_logical_calls": 11, "maximum_parallel_calls": 2,
            "note": "SDK retries may add requests. Generative outputs are not deterministic. This compares wording and mechanics, not end-to-end retrieval or treatment efficacy.",
        },
        "results": {}, "errors": {},
        "qualitative_review": "Not performed. Mechanical checks do not establish factual correctness or recognisable personality.",
    }
    write_report(output, report)
    if not args.live:
        print(f"Offline plan written: {output}. No credentials loaded; no API calls.")
        return 0
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        report["status"] = "blocked_missing_key"
        write_report(output, report)
        print("No configured OpenAI key. No API calls.", file=sys.stderr)
        return 2
    report["status"] = "running"
    write_report(output, report)
    try:
        started = time.perf_counter()
        bootstrap = OpenAIService(api_key).rerank(
            deepcopy(fixture["persona"]), deepcopy(fixture["profile"]),
            deepcopy(fixture["candidates"]), advisor=deepcopy(advisors["A_neutral"]),
        )
        report["bootstrap"] = {"result": bootstrap, "seconds": round(time.perf_counter() - started, 3)}
        common_cache = bootstrap["assessment_cache"]
        write_report(output, report)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(evaluate_variant, label, deepcopy(advisor), deepcopy(fixture),
                                   deepcopy(common_cache), api_key): label for label, advisor in advisors.items()}
            for future in as_completed(futures):
                label = futures[future]
                try:
                    report["results"][label] = future.result()
                except Exception as error:
                    # SDK/error strings can contain request headers or source text.
                    report["errors"][label] = {"exception_class": type(error).__name__}
                write_report(output, report)
        report["results"] = {label: report["results"][label] for label in advisors if label in report["results"]}
        report["status"] = "partial_failure" if report["errors"] else "completed"
    except Exception as error:
        report["errors"]["bootstrap"] = {"exception_class": type(error).__name__}
        report["status"] = "failed"
    report["source_sha256_after"] = hashes()
    report["sources_unchanged_during_run"] = report["source_sha256"] == report["source_sha256_after"]
    report["all_mechanical_checks_passed"] = (len(report["results"]) == len(advisors)
        and all(item["mechanical_checks_passed"] for item in report["results"].values()))
    write_report(output, report)
    print(f"Evaluation {report['status']}: {output}. Qualitative review remains necessary.")
    return 0 if report["status"] == "completed" and report["all_mechanical_checks_passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Evaluation stopped ({type(error).__name__}); no error details printed.", file=sys.stderr)
        raise SystemExit(2) from None
