import csv
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from common import CSV_FIELDS, audit_row, digest, load_source, score_bands, write_csv, write_json
from evaluate import (analyze, average_ranks, cohens_kappa, merge_blinded, ranking_metrics,
                      rating, read_ratings, spearman)
from example import FIXTURE_COMMIT, fixture_source, run_example
from sample import export, sample_pairs


class RelevanceWorkflowTest(unittest.TestCase):
    def test_sample_stratification_seed_and_missing_strata(self):
        source = fixture_source()
        selected, bands, _, quotas = sample_pairs(source["pairs"])
        self.assertEqual(40, len(selected))
        self.assertEqual(40, len({row["pair_id"] for row in selected}))
        self.assertEqual([13, 13, 14], sorted(Counter(row["condition"] for row in selected).values()))
        self.assertEqual(9, len(quotas))
        self.assertTrue(all(n in (4, 5) for n in quotas.values()))
        self.assertEqual(selected, sample_pairs(list(reversed(source["pairs"])))[0])
        for row in source["pairs"]:
            row["system_score"] = 70
        with self.assertRaisesRegex(ValueError, "Insufficient"):
            sample_pairs(source["pairs"])

    def test_provenance_rejects_old_and_implicit_synthetic_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            source = fixture_source()
            write_json(path, source)
            with self.assertRaisesRegex(ValueError, "Synthetic"):
                load_source(path, FIXTURE_COMMIT)
            with self.assertRaisesRegex(ValueError, "commit differs"):
                load_source(path, "old-commit", allow_synthetic=True)
            source["provenance"]["questionnaire_version"] = 11
            write_json(path, source)
            with self.assertRaisesRegex(ValueError, "V12"):
                load_source(path, FIXTURE_COMMIT, allow_synthetic=True)

    def test_blind_export_and_merge_preserve_missing_ratings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = fixture_source()
            path = root / "source.json"
            write_json(path, source)
            destination = root / "export"
            manifest = export(path, destination, FIXTURE_COMMIT, allow_synthetic=True)
            self.assertEqual(40, manifest["sample_size"])
            for rater in (1, 2):
                file = destination / f"rater{rater}.csv"
                with file.open(encoding="utf-8-sig", newline="") as handle:
                    reader = csv.DictReader(handle)
                    self.assertNotIn("system_score", reader.fieldnames)
                    self.assertNotIn("condition", reader.fieldnames)
                    items = list(reader)
                items[0]["relevance"] = "2"
                write_csv(file, ["blind_id", "profile_summary", "job_text", "relevance"], items)
            merged = merge_blinded(path, source, destination / "manifest.json", destination / "rater1.csv", destination / "rater2.csv")
            self.assertEqual(40, len(merged))
            self.assertEqual(2, sum(value is not None for item in merged.values() for value in item.values()))
            with self.assertRaisesRegex(ValueError, "Destination contains"):
                export(path, destination, FIXTURE_COMMIT, allow_synthetic=True)

    def test_statistical_known_values_ties_and_undefined(self):
        self.assertEqual([1.5, 1.5, 3.0], average_ranks([10, 10, 20]))
        self.assertAlmostEqual(1, spearman([1, 1, 3], [4, 4, 9])["value"])
        self.assertAlmostEqual(-1, spearman([1, 2, 3], [9, 4, 1])["value"])
        self.assertAlmostEqual(.5, cohens_kappa([0, 0, 1, 1], [0, 1, 1, 1])["value"])
        self.assertEqual("not_estimable", spearman([1, 1], [1, 2])["status"])
        self.assertEqual("not_estimable", cohens_kappa([1, 1], [1, 1])["status"])
        self.assertEqual("not_estimable", cohens_kappa([], [])["status"])
        with self.assertRaises(ValueError):
            rating("1.5", "rating")
        self.assertIsNone(rating("", "rating"))

    def test_rankings_need_complete_top10_pool_and_consensus(self):
        source = fixture_source()
        rows = source["pairs"]
        empty = ranking_metrics(rows, {})
        self.assertTrue(all(item["ndcg_status"] == "not_estimable" for item in empty["by_ranking"]))
        judgments = {row["pair_id"]: {"rater1_relevance": (20 - row["rank"]) // 5,
                                          "rater2_relevance": (20 - row["rank"]) // 5} for row in rows}
        full = ranking_metrics(rows, judgments)
        self.assertTrue(all(item["ndcg_at_10"] == 1 for item in full["by_ranking"]))
        self.assertTrue(all(item["precision_at_10"] == 1 for item in full["by_ranking"]))
        # One occurrence can establish a profile/job consensus across arms; remove all occurrences.
        sparse = {row["pair_id"]: judgments[row["pair_id"]] for row in rows if row["rank"] <= 10}
        top_only = ranking_metrics(rows, sparse)
        self.assertTrue(all(item["precision_status"] == "ok" and item["ndcg_status"] == "not_estimable"
                            for item in top_only["by_ranking"]))
        for item in judgments.values():
            item["rater1_relevance"], item["rater2_relevance"] = 0, 3
        disagree = ranking_metrics(rows, judgments)
        self.assertTrue(all(item["ndcg_at_10"] is None for item in disagree["by_ranking"]))

    def test_conflicting_labels_are_not_silently_averaged(self):
        source = fixture_source()
        judgments = {row["pair_id"]: {"consensus_relevance": 2} for row in source["pairs"]}
        judgments["fixture-q1-A-j1"]["consensus_relevance"] = 3
        result = ranking_metrics(source["pairs"], judgments)
        q1 = [item for item in result["by_ranking"] if item["query_id"] == "fixture-q1"]
        self.assertTrue(all(item["ndcg_status"] == "not_estimable" for item in q1))

    def test_ranking_order_matters_and_precision_uses_actual_top_ten(self):
        source = fixture_source()
        rows = source["pairs"]
        judgments = {row["pair_id"]: {"consensus_relevance": (20 - row["rank"]) // 5} for row in rows}
        for row in rows:
            if row["condition"] == "B":
                row["rank"] = 21 - row["rank"]
        results = ranking_metrics(rows, judgments)["by_ranking"]
        a = next(item for item in results if item["condition"] == "A")
        b = next(item for item in results if item["condition"] == "B")
        self.assertEqual(1, a["precision_at_10"])
        self.assertEqual(0, b["precision_at_10"])
        self.assertLess(b["ndcg_at_10"], a["ndcg_at_10"])

    def test_source_rejects_changed_profile_or_job_and_missing_ranks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            for field, value, message in (("profile_summary", "different need", "one fixed profile"),
                                          ("job_text", "different vacancy", "different job texts"),
                                          ("rank", 99, "gaps")):
                source = fixture_source()
                source["pairs"][20][field] = value
                write_json(path, source)
                with self.assertRaisesRegex(ValueError, message):
                    load_source(path, FIXTURE_COMMIT, allow_synthetic=True)

    def test_end_to_end_fixture_clearly_marked_and_no_fake_sparse_ndcg(self):
        with tempfile.TemporaryDirectory() as directory:
            run_example(directory)
            root = Path(directory)
            sparse = json.loads((root / "SYNTHETIC-sparse-report.json").read_text())
            self.assertEqual(40, sparse["jointly_rated_pairs"])
            self.assertEqual("synthetic_fixture", sparse["provenance"]["source_kind"])
            self.assertTrue(all(item["ndcg_at_10"] is None for item in sparse["ranking_metrics"]["by_ranking"]))
            full = json.loads((root / "SYNTHETIC-full-pool-report.json").read_text())
            self.assertTrue(all(item["ndcg_at_10"] == 1 for item in full["ranking_metrics"]["by_ranking"]))

    def test_invalid_metadata_and_rating_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixture_source()
            row = source["pairs"][0]
            bands, _ = score_bands(source["pairs"])
            path = Path(directory) / "ratings.csv"
            item = {**audit_row(row, bands[row["pair_id"]]), "rater1_relevance": 5}
            write_csv(path, CSV_FIELDS, [item])
            with self.assertRaisesRegex(ValueError, "from 0 to 3"):
                read_ratings(path, source["pairs"])
            item.update(rater1_relevance=2, system_score=5)
            write_csv(path, CSV_FIELDS, [item])
            with self.assertRaisesRegex(ValueError, "System score changed"):
                read_ratings(path, source["pairs"])


if __name__ == "__main__":
    unittest.main()
