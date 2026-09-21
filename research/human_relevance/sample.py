#!/usr/bin/env python3
"""Export 40 auditable, stratified pairs without requesting models or touching a study DB."""
from __future__ import annotations

import argparse
import hashlib
import random
from collections import Counter
from pathlib import Path

from common import BANDS, CONDITIONS, CSV_FIELDS, audit_row, digest, load_source, score_bands, write_csv, write_json


def sample_pairs(rows, count=40, seed=20260921):
    if count < 9:
        raise ValueError("At least nine pairs are required to cover all nine strata.")
    bands, thresholds = score_bands(rows)
    rng = random.Random(seed)
    arm_order = list(CONDITIONS)
    rng.shuffle(arm_order)
    quotas = {}
    for index, arm in enumerate(arm_order):
        target = count // 3 + (index < count % 3)
        band_order = list(BANDS)
        rng.shuffle(band_order)
        for band_index, band in enumerate(band_order):
            quotas[arm, band] = target // 3 + (band_index < target % 3)
    available = Counter((row["condition"], bands[row["pair_id"]]) for row in rows)
    shortages = {f"{arm}/{band}": {"needed": quota, "available": available[arm, band]}
                 for (arm, band), quota in quotas.items() if available[arm, band] < quota}
    if shortages:
        raise ValueError(f"Insufficient distinct pairs in score strata: {shortages}. Acquire more current cases; do not split tied scores or fabricate rows.")
    selected = []
    for (arm, band), quota in sorted(quotas.items()):
        pool = sorted([row for row in rows if row["condition"] == arm and bands[row["pair_id"]] == band], key=lambda row: row["pair_id"])
        selected.extend(rng.sample(pool, quota))
    rng.shuffle(selected)
    return selected, bands, thresholds, {f"{arm}/{band}": value for (arm, band), value in sorted(quotas.items())}


def export(source_path, destination, expected_commit, *, count=40, seed=20260921,
           allow_synthetic=False, export_pool=False):
    source = load_source(source_path, expected_commit, allow_synthetic=allow_synthetic)
    rows = source["pairs"]
    selected, bands, thresholds, quotas = sample_pairs(rows, count, seed)
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    # Refuse accidental replacement of completed human judgments.
    names = ["sample.csv", "rater1.csv", "rater2.csv", "manifest.json"]
    if export_pool:
        names += ["pool.csv", "pool-rater1.csv", "pool-rater2.csv"]
    if any((out / name).exists() for name in names):
        raise ValueError("Destination contains exported files. Use a new directory to preserve existing ratings.")
    audit_rows = [audit_row(row, bands[row["pair_id"]]) for row in selected]
    write_csv(out / "sample.csv", CSV_FIELDS, audit_rows)
    blinding = {}
    for suffix, collection in (("", selected), ("pool-", rows)):
        if suffix and not export_pool:
            continue
        if suffix:
            write_csv(out / "pool.csv", CSV_FIELDS, [audit_row(row, bands[row["pair_id"]]) for row in rows])
        for rater in (1, 2):
            order = sorted(collection, key=lambda row: row["pair_id"])
            random.Random(f"{seed}:{suffix}:{rater}").shuffle(order)
            blind_rows, mapping = [], {}
            for row in order:
                token = hashlib.sha256(f"{seed}:{suffix}:{rater}:{row['pair_id']}".encode()).hexdigest()[:16]
                mapping[token] = row["pair_id"]
                blind_rows.append({"blind_id": token, "profile_summary": row["profile_summary"],
                                   "job_text": row["job_text"], "relevance": ""})
            filename = f"{suffix}rater{rater}.csv"
            write_csv(out / filename, ["blind_id", "profile_summary", "job_text", "relevance"], blind_rows)
            blinding[filename] = mapping
    manifest = {
        "schema_version": 1, "source_file": str(Path(source_path).resolve()), "source_sha256": digest(source_path),
        "provenance": source["provenance"], "sample_size": len(selected), "seed": seed,
        "stratum_quotas": quotas, "within_condition_score_thresholds": thresholds,
        "sample_pair_ids": [row["pair_id"] for row in selected], "blind_id_mapping": blinding,
        "files_sha256": {name: digest(out / name) for name in names if name != "manifest.json"},
        "rating_scale": {"0": "nicht passend", "1": "eingeschränkt passend", "2": "passend", "3": "sehr passend"},
        "warnings": ["Metadata assertions document provenance; they cannot certify it independently.",
                     "Forty stratified judgments describe the sample, not unbiased overall corpus quality.",
                     "A sparse stratified sample does not establish nDCG@10 or Precision@10.",
                     "Keep manifest and audit CSV from raters: they expose conditions and scores."],
    }
    write_json(out / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--expected-system-commit", required=True)
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260921)
    parser.add_argument("--allow-synthetic", action="store_true")
    parser.add_argument("--export-pool", action="store_true", help="Also export the entire captured pool for separately adjudicated ranking metrics.")
    args = parser.parse_args()
    try:
        result = export(args.source, args.out, args.expected_system_commit, count=args.count,
                        seed=args.seed, allow_synthetic=args.allow_synthetic, export_pool=args.export_pool)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Exported {result['sample_size']} pairs; source_kind={result['provenance']['source_kind']}; no model calls.")


if __name__ == "__main__":
    main()
