#!/usr/bin/env python3
"""Run a fully SYNTHETIC offline demonstration; these are not real jobs, runs or human ratings."""
from __future__ import annotations

import argparse
from pathlib import Path

from common import CSV_FIELDS, audit_row, digest, score_bands, write_csv, write_json
from evaluate import analyze, read_ratings
from sample import export

FIXTURE_COMMIT = "SYNTHETIC-FIXTURE-NOT-A-SYSTEM-RUN"


def fixture_source():
    rows = []
    for query in range(1, 4):
        for condition in ("A", "B", "C"):
            for rank in range(1, 21):
                rows.append({"pair_id": f"fixture-q{query}-{condition}-j{rank}",
                             "query_id": f"fixture-q{query}", "job_id": f"fictional-job-{rank}",
                             "profile_summary": f"SYNTHETIC SOFTWARE TEST: fictional profile {query}, no participant data.",
                             "job_text": f"SYNTHETIC SOFTWARE TEST: fictional job {rank}; not an actual vacancy.",
                             "condition": condition, "rank": rank, "system_score": 100 - rank * 4})
    return {"schema_version": 1, "provenance": {
        "system_git_commit": FIXTURE_COMMIT, "questionnaire_version": 12,
        "scoring_version": "synthetic-not-scored", "corpus_sha256": "0" * 64,
        "captured_at": "2026-09-21T00:00:00Z", "source_kind": "synthetic_fixture",
        "model": "none-no-api", "prompt_revision": "none", "ranking_scope": "captured_candidate_pool",
    }, "pairs": rows}


def run_example(out):
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Use an empty directory for the synthetic demo.")
    out.mkdir(parents=True, exist_ok=True)
    source = fixture_source()
    source_path = out / "synthetic-source.json"
    write_json(source_path, source)
    manifest = export(source_path, out / "sample", FIXTURE_COMMIT, allow_synthetic=True, export_pool=True)
    bands, _ = score_bands(source["pairs"])
    for label, identifiers in (("sparse", set(manifest["sample_pair_ids"])),
                               ("full-pool", {row["pair_id"] for row in source["pairs"]})):
        rows = []
        for row in source["pairs"]:
            if row["pair_id"] not in identifiers:
                continue
            grade = (20 - row["rank"]) // 5
            rows.append({**audit_row(row, bands[row["pair_id"]]), "rater1_relevance": grade,
                         "rater2_relevance": grade, "consensus_relevance": grade})
        rating_path = out / f"SYNTHETIC-{label}-ratings.csv"
        write_csv(rating_path, CSV_FIELDS + ["consensus_relevance"], rows)
        judgments = read_ratings(rating_path, source["pairs"])
        report = analyze(source, judgments, digest(source_path), {"synthetic_demo": digest(rating_path)})
        report["WARNING"] = "SYNTHETIC SOFTWARE TEST ONLY: no actual system run, no human raters, no research evidence."
        write_json(out / f"SYNTHETIC-{label}-report.json", report)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        run_example(args.out)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print("SYNTHETIC demonstration completed. No models, real participants, human ratings or research findings.")


if __name__ == "__main__":
    main()
