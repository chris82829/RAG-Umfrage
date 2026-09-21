"""Offline formats and provenance checks for human relevance judgments (stdlib only)."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from datetime import datetime
from collections import defaultdict
from pathlib import Path

CONDITIONS = ("A", "B", "C")
BANDS = ("low", "medium", "high")
CSV_FIELDS = ["pair_id", "profile_summary", "job_text", "condition", "score_band",
              "system_score", "rater1_relevance", "rater2_relevance"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def spreadsheet_safe(value):
    """Keep researcher-controlled/user-provided text from becoming a spreadsheet formula."""
    value = "" if value is None else str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def write_csv(path, fields, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: spreadsheet_safe(row.get(field, "")) for field in fields})


def load_source(path, expected_commit, *, allow_synthetic=False):
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    if source.get("schema_version") != 1:
        raise ValueError("Source schema_version must be 1.")
    provenance = source.get("provenance", {})
    required = ("system_git_commit", "questionnaire_version", "scoring_version", "corpus_sha256",
                "captured_at", "source_kind", "model", "prompt_revision", "ranking_scope")
    for key in required:
        if not str(provenance.get(key, "")).strip():
            raise ValueError(f"Missing source provenance: {key}")
    if provenance["system_git_commit"] != expected_commit:
        raise ValueError("Source commit differs from --expected-system-commit; do not relabel historical results.")
    if int(provenance["questionnaire_version"]) != 12:
        raise ValueError("This workflow requires a separately captured V12 source; older pilots are not current data.")
    if provenance["source_kind"] == "synthetic_fixture":
        if not allow_synthetic:
            raise ValueError("Synthetic fixture: pass --allow-synthetic only to test the workflow, not for study evidence.")
    elif provenance["source_kind"] != "current_system_capture":
        raise ValueError("source_kind must be current_system_capture or synthetic_fixture.")
    elif not re.fullmatch(r"[0-9a-f]{40}", provenance["system_git_commit"]):
        raise ValueError("Real capture provenance requires the full 40-character Git commit hash.")
    if not re.fullmatch(r"[0-9a-f]{64}", provenance["corpus_sha256"]):
        raise ValueError("corpus_sha256 must be a SHA-256 digest.")
    try:
        captured = datetime.fromisoformat(provenance["captured_at"].replace("Z", "+00:00"))
        if captured.tzinfo is None:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("captured_at must be an ISO timestamp with time zone.") from None
    if provenance["ranking_scope"] != "captured_candidate_pool":
        raise ValueError("ranking_scope must be captured_candidate_pool; no claim of exhaustively judged corpus is supported.")
    rows = source.get("pairs", [])
    if not rows:
        raise ValueError("No current profile/job pairs available. Capture new results explicitly; do not reuse the historical pilot.")
    seen, identities, ranks, contexts, job_texts = set(), set(), set(), {}, {}
    for row in rows:
        for key in ("pair_id", "query_id", "job_id", "profile_summary", "job_text", "condition"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Every pair needs a nonempty string {key}.")
        if row["condition"] not in CONDITIONS:
            raise ValueError("condition must be A, B or C.")
        if row["pair_id"] in seen:
            raise ValueError(f"Duplicate pair_id: {row['pair_id']}")
        identity = row["query_id"], row["condition"], row["job_id"]
        if identity in identities:
            raise ValueError(f"Duplicate job in a ranking: {identity}")
        if type(row.get("rank")) is not int or row["rank"] < 1:
            raise ValueError("rank must be the original one-based integer rank.")
        rank_key = row["query_id"], row["condition"], row["rank"]
        if rank_key in ranks:
            raise ValueError(f"Duplicate rank: {rank_key}")
        score = row.get("system_score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 100:
            raise ValueError("system_score must be a finite number from 0 to 100.")
        if contexts.setdefault(row["query_id"], row["profile_summary"]) != row["profile_summary"]:
            raise ValueError("Each query_id must refer to exactly one fixed profile/need snapshot.")
        job_context = row["query_id"], row["job_id"]
        if job_texts.setdefault(job_context, row["job_text"]) != row["job_text"]:
            raise ValueError("A fixed query/job pair has different job texts across conditions; do not pool its judgments.")
        seen.add(row["pair_id"])
        identities.add(identity)
        ranks.add(rank_key)
    for key, group in group_rows(rows, ("query_id", "condition")).items():
        actual = sorted(row["rank"] for row in group)
        if actual != list(range(1, len(actual) + 1)):
            raise ValueError(f"Ranking {key} has gaps: include its full captured candidate list, not only selected pairs.")
    return source


def group_rows(rows, keys):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    return groups


def score_bands(rows):
    """Within-arm quantile thresholds. Identical scores stay together, never arbitrary tie splits."""
    result, thresholds = {}, {}
    for condition in CONDITIONS:
        group = [row for row in rows if row["condition"] == condition]
        if not group:
            raise ValueError(f"Missing condition {condition}.")
        scores = sorted(row["system_score"] for row in group)
        lower = scores[max(0, math.ceil(len(scores) / 3) - 1)]
        upper = scores[max(0, math.ceil(2 * len(scores) / 3) - 1)]
        thresholds[condition] = {"lower_inclusive": lower, "middle_inclusive": upper}
        for row in group:
            result[row["pair_id"]] = "low" if row["system_score"] <= lower else "medium" if row["system_score"] <= upper else "high"
    return result, thresholds


def audit_row(row, band):
    return {**{key: row[key] for key in ("pair_id", "profile_summary", "job_text", "condition", "system_score")},
            "score_band": band, "rater1_relevance": "", "rater2_relevance": ""}
