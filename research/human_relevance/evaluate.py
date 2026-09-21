#!/usr/bin/env python3
"""Offline agreement and relevance analysis; sparse samples never become fictitious rankings."""
from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

from common import (CONDITIONS, CSV_FIELDS, audit_row, digest, group_rows, load_source,
                    score_bands, spreadsheet_safe, write_csv, write_json)


def rating(value, column):
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    if text not in ("0", "1", "2", "3"):
        raise ValueError(f"{column}: expected an integer from 0 to 3 or an empty cell; got {text!r}.")
    return int(text)


def read_ratings(path, rows):
    known = {row["pair_id"]: row for row in rows}
    bands, _ = score_bands(rows)
    ratings = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not set(CSV_FIELDS).issubset(reader.fieldnames or []):
            raise ValueError("Ratings file must preserve the eight audit CSV columns; consensus_relevance is optional.")
        for item in reader:
            identifier = item["pair_id"]
            if identifier not in known or identifier in ratings:
                raise ValueError(f"Unknown or duplicate rated pair: {identifier}")
            expected = audit_row(known[identifier], bands[identifier])
            for field in ("profile_summary", "job_text", "condition", "score_band"):
                if item[field] != spreadsheet_safe(expected[field]):
                    raise ValueError(f"Source content changed for {identifier}/{field}; only edit rating columns.")
            if float(item["system_score"]) != float(expected["system_score"]):
                raise ValueError(f"System score changed for {identifier}.")
            ratings[identifier] = {key: rating(item.get(key), key) for key in
                                   ("rater1_relevance", "rater2_relevance", "consensus_relevance")}
    return ratings


def merge_blinded(source_path, source, manifest_path, rater1_path, rater2_path):
    import json
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("source_sha256") != digest(source_path):
        raise ValueError("Manifest source digest does not match source file.")
    known = {row["pair_id"]: row for row in source["pairs"]}
    merged, pair_sets = {}, []
    for index, path in enumerate((rater1_path, rater2_path), 1):
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not {"blind_id", "profile_summary", "job_text", "relevance"}.issubset(reader.fieldnames or []):
                raise ValueError("Blind rating files require blind_id, profile_summary, job_text, relevance.")
            items = list(reader)
        observed = [item["blind_id"] for item in items]
        if len(observed) != len(set(observed)):
            raise ValueError("Duplicate blind_id in a rating file.")
        matches = [mapping for name, mapping in manifest["blind_id_mapping"].items()
                   if name.endswith(f"rater{index}.csv") and set(mapping) == set(observed)]
        if len(matches) != 1:
            raise ValueError(f"Rater {index}: incomplete or wrong blind-ID set; preserve rows and leave missing ratings blank.")
        mapping = matches[0]
        pair_sets.append(set(mapping.values()))
        for item in items:
            identifier = mapping[item["blind_id"]]
            row = known[identifier]
            for field in ("profile_summary", "job_text"):
                if item[field] != spreadsheet_safe(row[field]):
                    raise ValueError(f"Rater {index}: source content changed for {identifier}/{field}.")
            merged.setdefault(identifier, {})[f"rater{index}_relevance"] = rating(item["relevance"], "relevance")
    if pair_sets[0] != pair_sets[1]:
        raise ValueError("Both raters must rate the same sampled pairs.")
    return merged


def average_ranks(values):
    ordered = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        average = (start + 1 + end) / 2
        for index in ordered[start:end]:
            ranks[index] = average
        start = end
    return ranks


def spearman(left, right):
    if len(left) < 2:
        return {"status": "not_estimable", "n": len(left), "value": None, "reason": "Fewer than two jointly rated pairs."}
    a, b = average_ranks(left), average_ranks(right)
    mean_a, mean_b = sum(a) / len(a), sum(b) / len(b)
    numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    denominator = math.sqrt(sum((x - mean_a) ** 2 for x in a) * sum((y - mean_b) ** 2 for y in b))
    if not denominator:
        return {"status": "not_estimable", "n": len(left), "value": None, "reason": "One variable is constant."}
    return {"status": "ok", "n": len(left), "value": max(-1.0, min(1.0, numerator / denominator))}


def cohens_kappa(left, right):
    count = len(left)
    if not count:
        return {"status": "not_estimable", "n": 0, "value": None, "reason": "No jointly rated pairs."}
    observed = sum(x == y for x, y in zip(left, right)) / count
    a, b = Counter(left), Counter(right)
    expected = sum(a[grade] * b[grade] for grade in range(4)) / count ** 2
    if expected == 1:
        return {"status": "not_estimable", "n": count, "value": None, "observed_agreement": observed,
                "reason": "Both raters used one identical category; chance-corrected kappa is undefined."}
    return {"status": "ok", "n": count, "value": (observed - expected) / (1 - expected),
            "observed_agreement": observed, "expected_agreement": expected, "weighting": "unweighted"}


def consensus_for(item):
    if item.get("consensus_relevance") is not None:
        return item["consensus_relevance"]
    first, second = item.get("rater1_relevance"), item.get("rater2_relevance")
    return first if first is not None and first == second else None


def ranking_metrics(rows, judgments, threshold=2):
    # Ground truth belongs to a fixed profile/job pair, not to the recommending arm.
    labels, inconsistent = {}, set()
    for row in rows:
        value = consensus_for(judgments.get(row["pair_id"], {}))
        if value is None:
            continue
        key = row["query_id"], row["job_id"]
        if key in labels and labels[key] != value:
            inconsistent.add(key)
        labels[key] = value
    pools = {query: {row["job_id"] for row in group}
             for (query,), group in group_rows(rows, ("query_id",)).items()}
    results = []
    for (query, condition), group in sorted(group_rows(rows, ("query_id", "condition")).items()):
        ranking = sorted(group, key=lambda row: row["rank"])[:10]
        top_keys = [(query, row["job_id"]) for row in ranking]
        pool_keys = [(query, job) for job in pools[query]]
        missing_top = sum(key not in labels for key in top_keys)
        missing_pool = sum(key not in labels for key in pool_keys)
        conflict = sum(key in inconsistent for key in pool_keys)
        item = {"query_id": query, "condition": condition, "captured_pool_size": len(pool_keys),
                "missing_top10_consensus": missing_top, "missing_pool_consensus": missing_pool,
                "conflicting_profile_job_consensus": conflict, "precision_at_10": None, "ndcg_at_10": None}
        if conflict:
            item.update(precision_status="not_estimable", ndcg_status="not_estimable",
                        reason="Contradictory consensus for the same fixed profile/job across arms; adjudicate first.")
        elif len(ranking) < 10 or missing_top:
            item.update(precision_status="not_estimable", ndcg_status="not_estimable",
                        reason="A full ranked top ten with consensus judgments is required; unjudged is not irrelevant.")
        else:
            grades = [labels[key] for key in top_keys]
            item.update(precision_status="ok", precision_at_10=sum(grade >= threshold for grade in grades) / 10)
            if missing_pool:
                item.update(ndcg_status="not_estimable", reason="nDCG requires consensus for the full captured candidate pool to form IDCG.")
            else:
                ideal = sorted([labels[key] for key in pool_keys], reverse=True)[:10]
                dcg = lambda values: sum((2 ** grade - 1) / math.log2(rank + 2) for rank, grade in enumerate(values))
                denominator = dcg(ideal)
                if denominator:
                    item.update(ndcg_status="ok", ndcg_at_10=dcg(grades) / denominator)
                else:
                    item.update(ndcg_status="not_estimable", reason="No relevant candidates: IDCG is zero.")
        results.append(item)
    aggregate = {}
    for condition in CONDITIONS:
        eligible = [item for item in results if item["condition"] == condition]
        aggregate[condition] = {"rankings_in_source": len(eligible)}
        for name, status in (("ndcg_at_10", "ndcg_status"), ("precision_at_10", "precision_status")):
            values = [item[name] for item in eligible if item[status] == "ok"]
            aggregate[condition][name] = {"n_estimable_rankings": len(values), "mean": sum(values) / len(values) if values else None,
                                          "all_source_rankings_estimable": bool(eligible) and len(values) == len(eligible)}
    return {"basis": "Consensus over union of captured candidate lists per fixed query; not all corpus jobs.",
            "relevance_threshold": threshold, "dcg_gain": "2^relevance - 1", "by_ranking": results, "by_condition": aggregate}


def analyze(source, judgments, source_sha256, ratings_sha256=None):
    rows = source["pairs"]
    jointly = [(row, judgments[row["pair_id"]]) for row in rows if row["pair_id"] in judgments
               and all(judgments[row["pair_id"]].get(key) is not None for key in ("rater1_relevance", "rater2_relevance"))]
    a = [item["rater1_relevance"] for _, item in jointly]
    b = [item["rater2_relevance"] for _, item in jointly]
    correlations = {}
    for condition in ("all", *CONDITIONS):
        subset = [(row, item) for row, item in jointly if condition == "all" or row["condition"] == condition]
        correlations[condition] = spearman([row["system_score"] for row, _ in subset],
                                          [(item["rater1_relevance"] + item["rater2_relevance"]) / 2 for _, item in subset])
    return {
        "schema_version": 1, "provenance": source["provenance"], "source_sha256": source_sha256,
        "ratings_sha256": ratings_sha256, "source_pairs": len(rows), "submitted_rows": len(judgments),
        "jointly_rated_pairs": len(jointly),
        "distinct_fixed_profile_job_pairs_rated": len({(row["query_id"], row["job_id"]) for row, _ in jointly}),
        "cohens_kappa": cohens_kappa(a, b), "spearman_system_vs_mean_human": correlations,
        "ranking_metrics": ranking_metrics(rows, judgments),
        "interpretation": [
            "This is a descriptive stratified sample, not a representative estimate of corpus-wide quality.",
            "Related pairs/queries and repeated profile/job pairs are not independent participants; no p-values are generated.",
            "Only joint ratings enter agreement/correlation. Missing ratings are never imputed as zero.",
            "Equal ratings count as consensus. Disagreements require a separately entered consensus_relevance; their mean is not consensus.",
            "Ranking means cover estimable lists only; inspect missing-list counts before comparing conditions.",
            "Synthetic fixtures validate software only and are never human study findings.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--expected-system-commit", required=True)
    parser.add_argument("--ratings", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--rater1", type=Path)
    parser.add_argument("--rater2", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--allow-synthetic", action="store_true")
    args = parser.parse_args()
    try:
        source = load_source(args.source, args.expected_system_commit, allow_synthetic=args.allow_synthetic)
        blind_args = (args.manifest, args.rater1, args.rater2)
        if args.ratings and any(blind_args):
            raise ValueError("Choose either --ratings or --manifest with both blinded rater files.")
        if args.ratings:
            judgments = read_ratings(args.ratings, source["pairs"])
            hashes = {"audit": digest(args.ratings)}
        elif all(blind_args):
            judgments = merge_blinded(args.source, source, *blind_args)
            hashes = {"rater1": digest(args.rater1), "rater2": digest(args.rater2), "manifest": digest(args.manifest)}
        else:
            raise ValueError("Supply --ratings or all of --manifest, --rater1 and --rater2.")
        result = analyze(source, judgments, digest(args.source), hashes)
        merged_path = args.out.with_suffix(".ratings.csv")
        if args.out.exists() or (not args.ratings and merged_path.exists()):
            raise ValueError("Report already exists; choose a new output path to preserve analysis history.")
        write_json(args.out, result)
        if not args.ratings:
            bands, _ = score_bands(source["pairs"])
            merged = [{**audit_row(row, bands[row["pair_id"]]), **judgments[row["pair_id"]], "consensus_relevance": ""}
                      for row in source["pairs"] if row["pair_id"] in judgments]
            write_csv(merged_path, CSV_FIELDS + ["consensus_relevance"], merged)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Analyzed {result['jointly_rated_pairs']} jointly rated pairs. Missing ranking judgments are reported, not invented.")


if __name__ == "__main__":
    main()
