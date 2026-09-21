"""Offline checks for current and historical study-version boundaries."""
import unittest

from advisor import AdvisorConfig
from study_assignment import (
    EXPERIMENT_ID,
    PREVIOUS_CONFERENCE_EXPERIMENT_ID,
    PersonalityPolicyError,
    advisor_for_policy,
    personality_policy,
)
from survey_store import SURVEY_DEFINITION, SURVEY_VERSION, V10_SURVEY_DEFINITION


class StudyVersioningTests(unittest.TestCase):
    def test_current_and_previous_policy_names_stay_distinct(self):
        self.assertEqual(EXPERIMENT_ID, "diana-abc-v4")
        self.assertEqual(
            [personality_policy(EXPERIMENT_ID, arm) for arm in "ABC"],
            ["unprompted", "career_fixed", "custom_career"],
        )
        self.assertEqual(
            [personality_policy(PREVIOUS_CONFERENCE_EXPERIMENT_ID, arm) for arm in "ABC"],
            ["standard", "templates", "configurable"],
        )

    def test_current_questionnaire_does_not_relabel_v10(self):
        self.assertEqual(SURVEY_VERSION, "diana-v11")
        self.assertEqual(SURVEY_DEFINITION["version"], "diana-v11")
        self.assertEqual(V10_SURVEY_DEFINITION["version"], "diana-v10")
        arm = next(
            field
            for field in SURVEY_DEFINITION["demographics"]["fields"]
            if field["name"] == "study_arm"
        )
        self.assertEqual(
            [label for _, label in arm["options"]],
            [
                "A – Basissystem ohne KI-Suchpersönlichkeit",
                "B – Fester Top-Berufsberater",
                "C – Selbst gestaltete KI-Suchpersönlichkeit auf Berufsberater-Basis",
            ],
        )

    def test_b_is_fixed_and_c_accepts_custom_configuration(self):
        default = AdvisorConfig().model_dump()
        self.assertEqual(advisor_for_policy(default, "career_fixed")["name"], "Top-Berufsberater")
        custom = {
            "mode": "custom",
            "preset": "diana",
            "name": "Eigene KI",
            "description": "Direkt und sorgfältig.",
            "traits": ["direkt"],
            "focus": "ausgewogen",
        }
        with self.assertRaises(PersonalityPolicyError):
            advisor_for_policy(custom, "career_fixed")
        self.assertEqual(advisor_for_policy(custom, "custom_career"), custom)

    def test_c_normalizes_removed_legacy_presets_and_canonicalizes_custom_config(self):
        legacy = AdvisorConfig(
            mode="preset", preset="steve", name="Steve-Jobs-KI",
            traits=["kreativ", "direkt"], focus="innovation",
        ).model_dump()
        normalized = advisor_for_policy(legacy, "custom_career")
        self.assertEqual(normalized["mode"], "custom")
        self.assertEqual(normalized["preset"], "diana")
        self.assertEqual(normalized["name"], "Top-Berufsberater")

        custom = AdvisorConfig(
            mode="custom", preset="angela", name="Meine Beratung",
            traits=["kritisch"], focus="fachliche_tiefe",
        ).model_dump()
        normalized = advisor_for_policy(custom, "custom_career")
        self.assertEqual(normalized["mode"], "custom")
        self.assertEqual(normalized["preset"], "diana")
        self.assertEqual(normalized["name"], "Meine Beratung")

    def test_c_self_report_refers_to_real_change(self):
        question = next(
            field["title"]
            for category in SURVEY_DEFINITION["categories"]
            for field in category["fields"]
            if field["name"] == "personality_customized"
        )
        self.assertIn("tatsächlich verändert", question)


if __name__ == "__main__":
    unittest.main()
