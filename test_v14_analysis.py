"""Synthetic unit fixtures only: these tests are not observations from participants."""
import copy
import json
import math
import tempfile
from pathlib import Path
import unittest

import numpy as np
from scipy import stats

from research.v14.analyze import (CONSTRUCTS, analyze_rows, compare, holm,
                                 plan_metadata, power_plan, rating, reliability)
from research.v14.faithfulness import (analyze_annotations, cohens_kappa,
                                      sample_pairs)


def fixture_rows():
    rows = []
    for arm, offset in [('A', 0), ('B', 1), ('C', 2)]:
        for i in range(12):
            answers = {field: 1 + offset + ((i + j) % 4)
                       for fields in CONSTRUCTS.values() for j, field in enumerate(fields)}
            answers.update(perceived_character=1 + offset + i % 4,
                           previous_participation='yes' if i == 0 else 'no',
                           personality_customized='yes' if i % 2 else 'no')
            rows.append({'participation_id': f'{arm}{i}', 'survey_version': 'diana-v14',
                         'study_arm': arm, 'study_wave': 'main', 'answers': answers})
    return rows


class AnalysisTests(unittest.TestCase):
    def test_catalog_availability_is_separate_and_never_changes_constructs(self):
        rows = fixture_rows()
        before = analyze_rows(rows, include_inference=False)
        for row in rows:
            row['answers']['catalog_availability'] = 7
        after = analyze_rows(rows, include_inference=False)
        for name in CONSTRUCTS:
            self.assertEqual(before['descriptives'][name], after['descriptives'][name])
            self.assertEqual(before['reliability'][name], after['reliability'][name])
        self.assertNotIn('catalog_availability', after['reliability'])
        self.assertEqual(before['descriptives']['catalog_availability']['A']['n'], 0)
        self.assertEqual(after['descriptives']['catalog_availability']['A']['mean'], 7)

    def test_rating_does_not_impute_or_coerce_boolean_fraction_or_nonresponse(self):
        for value in (None, '', 'not_assessable', True, 0, 8, 1.5, 'nan'):
            self.assertIsNone(rating(value))
        self.assertEqual(rating('7'), 7)

    def test_primary_matches_independent_scipy_welch_and_direction(self):
        x, y = [3, 4, 7, 7, 6], [1, 2, 5, 2, 2, 3]
        actual = compare(x, y, bootstrap_samples=0)
        expected = stats.ttest_ind(x, y, equal_var=False)
        self.assertAlmostEqual(actual['p_value'], expected.pvalue, places=14)
        self.assertAlmostEqual(actual['statistic'], expected.statistic, places=14)
        ci = expected.confidence_interval()
        np.testing.assert_allclose(actual['difference_ci95'], [ci.low, ci.high])
        self.assertGreater(actual['hedges_g'], 0)

    def test_holm_keeps_family_of_three_even_with_missing_test(self):
        np.testing.assert_allclose(holm([.01, .04, .03]), [.03, .06, .06])
        self.assertEqual(holm([.01, None, .04]), [.03, None, .08])

    def test_main_only_complete_constructs_and_repeat_sensitivities(self):
        rows = fixture_rows()
        rows[0]['answers']['usefulness_ideal'] = 'not_assessable'
        rows[1]['response_status'] = 'incomplete'  # Still has a valid endpoint.
        old = copy.deepcopy(rows[2]); old.update(participation_id='old', survey_version='diana-v13')
        pretest = copy.deepcopy(rows[3]); pretest.update(participation_id='pretest', study_wave='pretest')
        report = analyze_rows(rows + [old, pretest])
        self.assertEqual(report['sample_flow']['included_main'], 36)
        self.assertEqual(report['sample_flow']['excluded_by_reason'], {'not_v14': 1, 'not_main_wave': 1})
        self.assertEqual(report['sample_flow']['missing_constructs']['usefulness'], 1)
        self.assertEqual(report['descriptives']['usefulness']['A']['n'], 11)
        self.assertEqual(report['sensitivity_without_repeat']['n'], 33)
        self.assertEqual(report['primary']['n_first'], 12)
        self.assertEqual(len(report['secondary']), 3)
        json.dumps(report, allow_nan=False)

    def test_requires_documented_exclusion_and_recovered_error_is_not_excluded(self):
        rows = fixture_rows()
        rows[0]['error_code'] = 'upstream_timeout'
        self.assertEqual(analyze_rows(rows, include_inference=False)['sample_flow']['included_main'], 36)
        rows[0]['technical_exclusion'] = 1
        with self.assertRaises(ValueError):
            analyze_rows(rows, include_inference=False)
        rows[0]['technical_exclusion_reason'] = 'Terminal failure before exposure; recorded prior to unblinding.'
        self.assertEqual(analyze_rows(rows, include_inference=False)['sample_flow']['included_main'], 35)

    def test_duplicate_ids_fail_instead_of_pseudoreplication(self):
        rows = fixture_rows()
        with self.assertRaises(ValueError):
            analyze_rows(rows + [rows[0]])

    def test_export_and_nested_answers_produce_same_means(self):
        nested = fixture_rows()
        flattened = [{**{k: v for k, v in row.items() if k != 'answers'},
                      **{'v14_' + k: str(v) for k, v in row['answers'].items()}} for row in nested]
        a = analyze_rows(nested, include_inference=False)
        b = analyze_rows(flattened, include_inference=False)
        self.assertEqual(a['descriptives'], b['descriptives'])

    def test_alpha_and_two_item_spearman_brown(self):
        rows = [{'answers': {'trust_fit': n, 'trust_credibility': n}} for n in range(1, 8)]
        result = reliability(rows, 'trust')
        self.assertAlmostEqual(result['alpha'], 1)
        self.assertAlmostEqual(result['spearman_brown'], 1)
        self.assertEqual(result['n'], 7)

    def test_small_samples_and_constant_arrays_return_json_null_not_nan(self):
        self.assertEqual(compare([4], [5])['status'], 'insufficient_data')
        self.assertEqual(compare([4, 4], [5, 5])['status'], 'zero_variance')
        json.dumps(analyze_rows([]), allow_nan=False)

    def test_versioned_plan_hash_and_invalid_freeze_are_detected(self):
        original = plan_metadata()
        self.assertEqual(original['status'], 'draft')
        self.assertEqual(len(original['sha256']), 64)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'plan.json'
            content = copy.deepcopy(original['contents'])
            content['status'] = 'frozen_before_main'
            path.write_text(json.dumps(content))
            with self.assertRaises(ValueError):
                plan_metadata(path)
            content.update(smallest_effect_of_interest_d=.35, expected_dropout_fraction=.2,
                           planned_valid_participants_per_arm=130, freeze_git_commit='a' * 40,
                           frozen_at_utc='2026-09-22T12:00:00Z',
                           main_recruitment_start_utc='2026-09-23T12:00:00Z',
                           main_recruitment_end_utc='2026-09-26T12:00:00Z')
            path.write_text(json.dumps(content))
            self.assertEqual(plan_metadata(path)['status'], 'frozen_before_main')
            content['main_recruitment_start_utc'] = '2026-09-21T12:00:00Z'
            path.write_text(json.dumps(content))
            with self.assertRaises(ValueError):
                plan_metadata(path)
        with self.assertRaises(ValueError):
            analyze_rows([], plan_status='frozen_before_main')

    def test_mixed_treatment_warning_and_unknown_metadata_remain_distinct(self):
        rows = fixture_rows()
        rows[0].update(system_prompt_policy='unprompted', system_prompt_revision=1,
                       system_prompt_base_sha256='a' * 64, study_release_ids=['release1'])
        rows[1].update(system_prompt_policy='unprompted', system_prompt_revision=2,
                       system_prompt_base_sha256='b' * 64, study_release_ids='release1|release2')
        report = analyze_rows(rows, include_inference=False)
        self.assertTrue(report['treatment_versions']['A']['mixed_prompt_versions'])
        self.assertTrue(report['treatment_versions']['A']['mixed_system_releases'])
        self.assertEqual(report['interpretation_status'], 'preliminary_mixed_treatments')
        self.assertEqual(report['treatment_versions']['B']['unknown_prompt_participants'], 12)
        rows[1].update(system_prompt_revision=1, system_prompt_base_sha256=None)
        report = analyze_rows(rows, include_inference=False)
        self.assertFalse(report['treatment_versions']['A']['mixed_prompt_versions'])

    def test_power_cross_check_statsmodels_when_available(self):
        power = power_plan()
        self.assertEqual(power['n_per_group_at_d_035'], 130)
        self.assertTrue(.348 < power['detectable_d_at_n_130'] < .350)
        try:
            from statsmodels.stats.power import TTestIndPower
        except ImportError:
            self.skipTest('Optional independent statsmodels check not installed')
        expected = TTestIndPower().solve_power(effect_size=.35, alpha=.05, power=.8, alternative='two-sided')
        self.assertAlmostEqual(power['n_per_group_continuous'], expected, places=5)


class HumanFaithfulnessTests(unittest.TestCase):
    def fixtures(self):
        return [{'pair_id': f'{arm}{i}', 'study_arm': arm, 'job_id': str(i),
                 'profile': 'Synthetic Python learner', 'job_text': 'Python required.',
                 'explanation': 'Python matches the profile.'} for arm in 'ABC' for i in range(30)]

    def test_sample_is_balanced_blinded_deterministic_and_unrated(self):
        annotations, mapping = sample_pairs(self.fixtures(), 40)
        self.assertEqual(len(annotations), 40)
        self.assertEqual(sorted(sum(r['study_arm'] == arm for r in mapping) for arm in 'ABC'), [13, 13, 14])
        self.assertEqual((annotations, mapping), sample_pairs(self.fixtures(), 40))
        self.assertTrue(all(r['rater_1'] == r['rater_2'] == '' and 'study_arm' not in r for r in annotations))
        self.assertEqual(analyze_annotations(annotations, mapping)['missing_paired_ratings'], 40)

    def test_known_kappa_and_no_fake_perfect_agreement(self):
        pairs = [(0, 0), (1, 1), (2, 2), (0, 1)]
        result = cohens_kappa(pairs)
        self.assertAlmostEqual(result['kappa'], 7 / 11)
        self.assertIsNone(cohens_kappa([(2, 2), (2, 2)])['kappa'])
        annotations, mapping = sample_pairs(self.fixtures(), 60)
        for i, row in enumerate(annotations):
            row['rater_1'] = str(i % 3); row['rater_2'] = str(i % 3)
        result = analyze_annotations(annotations, mapping)
        self.assertEqual(result['reliability']['kappa'], 1)
        self.assertEqual(result['missing_paired_ratings'], 0)
        self.assertTrue(all(value['n_pairs'] == 20 for value in result['by_arm'].values()))

    def test_no_imputation_or_replacement_if_source_is_too_small(self):
        with self.assertRaises(ValueError):
            sample_pairs(self.fixtures()[:20], 40)
        with self.assertRaises(ValueError):
            sample_pairs(self.fixtures(), 39)
        annotations, mapping = sample_pairs(self.fixtures(), 40)
        annotations[0]['rater_1'] = 'yes'
        with self.assertRaises(ValueError):
            analyze_annotations(annotations, mapping)


if __name__ == '__main__':
    unittest.main()
