"""Offline checks for current and historical study-version boundaries."""
import unittest

from advisor import AdvisorConfig, FOCUS_PRIORITIES, resolve_advisor
from persona_mlds import load_templates
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
        self.assertEqual(EXPERIMENT_ID, "diana-abc-v7")
        self.assertEqual(
            [personality_policy(EXPERIMENT_ID, arm) for arm in "ABC"],
            ["unprompted", "career_fixed", "custom_career"],
        )
        self.assertEqual(
            [personality_policy(PREVIOUS_CONFERENCE_EXPERIMENT_ID, arm) for arm in "ABC"],
            ["standard", "templates", "configurable"],
        )

    def test_current_questionnaire_does_not_relabel_v10(self):
        self.assertEqual(SURVEY_VERSION, "diana-v14")
        self.assertEqual(SURVEY_DEFINITION["version"], "diana-v14")
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
        self.assertEqual(normalized["focus"], "ausgewogen")

        custom = AdvisorConfig(
            mode="custom", preset="angela", name="Meine Beratung",
            traits=["kritisch"], focus="fachliche_tiefe",
        ).model_dump()
        normalized = advisor_for_policy(custom, "custom_career")
        self.assertEqual(normalized["mode"], "custom")
        self.assertEqual(normalized["preset"], "diana")
        self.assertEqual(normalized["name"], "Meine Beratung")
        self.assertEqual(normalized["focus"], "ausgewogen")

    def test_c_uses_balanced_weights_for_every_starting_configuration(self):
        career = load_templates()["career"]["advisor"]
        starting_configs = [AdvisorConfig().model_dump(), career]
        starting_configs.extend(
            AdvisorConfig(mode="preset", preset=preset).model_dump()
            for preset in ("neutral", "standard", "steve", "angela", "guenther")
        )
        expected = {**career, "focus": "ausgewogen"}
        for requested in starting_configs:
            with self.subTest(requested=requested["preset"], focus=requested["focus"]):
                normalized = advisor_for_policy(requested, "custom_career")
                self.assertEqual(normalized, expected)
                self.assertEqual(resolve_advisor(normalized)["scoring_weights"], {
                    "technical_fit": 60, "preferences_fit": 15,
                    "technical_depth": 7, "learning": 6, "innovation": 6, "clarity": 6,
                })

    def test_c_preserves_custom_personality_but_normalizes_cached_focus(self):
        for focus in FOCUS_PRIORITIES:
            with self.subTest(focus=focus):
                requested = AdvisorConfig(
                    mode="custom", preset="angela", name="Meine Beratung",
                    description="Bitte antworte direkt in kurzen Absätzen.",
                    traits=["direkt", "kritisch"], focus=focus,
                ).model_dump()
                normalized = advisor_for_policy(requested, "custom_career")
                self.assertEqual(normalized, {
                    **requested, "preset": "diana", "focus": "ausgewogen",
                })
                self.assertEqual(requested["focus"], focus)
                self.assertEqual(resolve_advisor(normalized)["scoring_weights"], {
                    "technical_fit": 60, "preferences_fit": 15,
                    "technical_depth": 7, "learning": 6, "innovation": 6, "clarity": 6,
                })

    def test_b_and_historical_policies_keep_their_original_focus(self):
        career = load_templates()["career"]["advisor"]
        self.assertEqual(career["focus"], "lernpotenzial")
        for policy in ("career_fixed", "templates"):
            with self.subTest(policy=policy):
                self.assertEqual(advisor_for_policy(career, policy), career)
                self.assertEqual(advisor_for_policy(AdvisorConfig().model_dump(), policy), career)
        for focus in FOCUS_PRIORITIES:
            with self.subTest(policy="configurable", focus=focus):
                requested = AdvisorConfig(mode="custom", focus=focus).model_dump()
                self.assertEqual(advisor_for_policy(requested, "configurable"), requested)

    def test_c_self_report_refers_to_real_change(self):
        question = next(
            field["title"]
            for category in SURVEY_DEFINITION["categories"]
            for field in category["fields"]
            if field["name"] == "personality_customized"
        )
        self.assertIn("selbst verändert", question)


if __name__ == "__main__":
    unittest.main()
