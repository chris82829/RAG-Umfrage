import unittest

from admin_store import AdminSurveyData
from survey_analytics import analytics


def row(arm, policy, revision, sha256, value):
    return {
        "id": f"{arm}-{revision}-{sha256[:2]}",
        "participation_id": f"DIANA-{arm}-{revision}-{sha256[:2]}",
        "survey_version": "diana-v11",
        "response_status": "completed",
        "study_arm": arm,
        "experiment_id": "diana-abc-v4",
        "presentation_versions": ["ranked_insights"],
        "system_prompt_policy": policy,
        "system_prompt_revision": revision,
        "system_prompt_base_sha256": sha256,
        "answers": {"system_usefulness": value},
    }


class AdminPromptAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.a1 = row("A", "unprompted", 1, "a" * 64, 4)
        self.a2 = row("A", "unprompted", 2, "b" * 64, 8)
        self.b1 = row("B", "career_fixed", 1, "c" * 64, 7)
        self.rows = [self.a1, self.a2, self.b1]

    def test_prompt_options_are_exact_aggregates_without_prompt_text(self):
        options = AdminSurveyData.prompt_versions(self.rows)
        self.assertEqual(len(options), 3)
        self.assertEqual(options[0]["arms"], ["A"])
        self.assertEqual(options[0]["count"], 1)
        self.assertEqual(
            options[0]["value"],
            f"unprompted:1:{'a' * 64}",
        )
        self.assertNotIn("text", options[0])

    def test_exact_prompt_filter_selects_only_that_snapshot(self):
        selected = f"unprompted:2:{'b' * 64}"
        store = object.__new__(AdminSurveyData)
        store.records = lambda: self.rows
        self.assertEqual(store.filtered(prompt=selected), [self.a2])

    def test_analytics_separates_multiple_revisions_within_one_arm(self):
        result = analytics(self.rows, "diana-v11")
        cohort = result["cohorts"][0]
        self.assertEqual(cohort["mixed_prompt_arms"], ["A"])
        self.assertEqual(len(cohort["series"]), 3)
        question = next(
            question
            for category in cohort["categories"]
            for question in category["questions"]
            if question["name"] == "system_usefulness"
        )
        self.assertEqual(len(question["groups"]), 3)
        self.assertEqual(sorted(group["n"] for group in question["groups"].values()), [1, 1, 1])


if __name__ == "__main__":
    unittest.main()
