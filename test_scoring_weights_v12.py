"""Offline proof that every treatment uses the same deterministic score rule."""
import unittest
from advisor import AdvisorConfig, SCORING_WEIGHTS, resolve_advisor, score_from_components
from study_assignment import advisor_for_policy

class SharedScoringWeightsTests(unittest.TestCase):
    def test_identical_weights_and_score_in_all_arms(self):
        components = dict(technical_fit=83, preferences_fit=70, technical_depth=95,
                          learning=15, innovation=40, clarity=60)
        values = []
        for arm, policy in [('A','unprompted'),('B','career_fixed'),('C','custom_career')]:
            with self.subTest(arm=arm):
                advisor = advisor_for_policy(AdvisorConfig().model_dump(), policy)
                self.assertEqual(resolve_advisor(advisor)['scoring_weights'], SCORING_WEIGHTS)
                values.append(score_from_components(components, advisor))
        self.assertEqual(len(set(values)), 1)
        self.assertEqual(SCORING_WEIGHTS, dict(technical_fit=60, preferences_fit=15,
                         technical_depth=7, learning=6, innovation=6, clarity=6))

    def test_custom_focus_and_caller_mutation_cannot_override_weights(self):
        for focus in ('ausgewogen','fachliche_tiefe','lernpotenzial','innovation'):
            config = AdvisorConfig(mode='custom', focus=focus).model_dump()
            weights = resolve_advisor(config)['scoring_weights']
            self.assertEqual(weights, SCORING_WEIGHTS)
            weights['learning'] = 100
            self.assertEqual(resolve_advisor(config)['scoring_weights']['learning'], 6)

if __name__ == '__main__':
    unittest.main()
