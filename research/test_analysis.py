"""Synthetic-only regression checks for the offline analysis and planning scripts.

Run separately from application tests:
python -m unittest discover -s research -p 'test_analysis.py' -v
"""
import contextlib
import csv
import io
import json
import math
from pathlib import Path
import tempfile
import unittest

try:
    from analyze_primary import AnalysisError, analyze_csv, compare_groups, main, primary_value, write_json
    from plan_sample_size import plan, required_per_arm, two_sample_power
except ModuleNotFoundError as failure:
    if failure.name in ('scipy', 'numpy'):
        raise unittest.SkipTest('Install research/requirements.txt in a separate environment to run offline research tests.') from failure
    raise

GERMAN = ['teilnahme_id', 'experiment_id', 'fragebogen_version', 'studiengruppe',
          'v10_system_nutzen', 'teilnahme_status', 'ki_letzte_verwendung', 'feedback']
TECHNICAL = ['participation_id', 'experiment_id', 'survey_version', 'study_arm',
             'v10_system_usefulness', 'response_status', 'personality_last_source', 'feedback']


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'synthetic.csv'

    def export(self, rows, headers=GERMAN, delimiter=';'):
        with self.path.open('w', encoding='utf-8-sig', newline='') as target:
            writer = csv.writer(target, delimiter=delimiter)
            writer.writerow(headers)
            writer.writerows(rows)
        return self.path

    def row(self, identifier, arm, value, status='completed', source='template', version='diana-v10', experiment='diana-abc-v3'):
        return [identifier, experiment, version, arm, value, status, source, 'PRIVATE FAKE FREETEXT: never echo me']

    def test_cohort_is_exact_and_partial_answers_and_templates_are_included(self):
        rows = [self.row('synthetic-b1', 'B', 1), self.row('synthetic-b2', 'B', 2, 'in_progress'),
                self.row('synthetic-b3', 'B', 3), self.row('synthetic-c1', 'C', 3, source='custom'),
                self.row('synthetic-c2', 'C', 4, 'in_progress', 'template'), self.row('synthetic-c3', 'C', 5),
                self.row('synthetic-a1', 'A', 6), self.row('synthetic-c4', 'C', '', 'in_progress'),
                self.row('synthetic-b4', 'B', 'not_assessable'), self.row('synthetic-b5', 'B', '11'),
                self.row('synthetic-c5', 'C', '4.5'), self.row('synthetic-old1', 'C', 10, version='diana-v8'),
                self.row('synthetic-old2', 'B', 10, experiment='diana-abc-v1')]
        result = analyze_csv(self.export(rows))
        self.assertEqual(result['cohort'], {'input_rows': 13, 'eligible_rows': 11, 'excluded_experiment_or_version_rows': 2})
        self.assertEqual(result['groups']['B']['primary']['n'], 3)
        self.assertEqual(result['groups']['C']['primary']['n'], 3)
        self.assertEqual(result['groups']['A']['primary']['n'], 1)
        self.assertEqual(result['groups']['B']['missing_primary'], 1)
        self.assertEqual(result['groups']['C']['missing_primary'], 1)
        self.assertEqual(result['groups']['B']['invalid_primary'], 1)
        self.assertEqual(result['groups']['C']['invalid_primary'], 1)
        self.assertEqual(result['groups']['B']['completion_status_counts']['in_progress'], 1)
        self.assertEqual(result['primary_comparison']['mean_difference'], 2)
        encoded = json.dumps(result)
        for forbidden in ['synthetic-', 'PRIVATE FAKE', 'never echo me', 'customized_count']:
            self.assertNotIn(forbidden, encoded)
        # Technical/comma exports give the same estimates and counts.
        other = analyze_csv(self.export(rows, TECHNICAL, ','))
        self.assertEqual(other['primary_comparison'], result['primary_comparison'])
        self.assertEqual(other['groups'], result['groups'])

    def test_v9_requires_explicit_cohort_and_is_never_pooled_with_v10(self):
        headers = GERMAN + ['v9_system_nutzen']
        rows = [self.row('same-b', 'B', 2) + [''], self.row('new-b', 'B', 4) + [''],
                self.row('same-c', 'C', 6) + [''], self.row('new-c', 'C', 8) + [''],
                self.row('same-b', 'B', '', version='diana-v9', experiment='diana-abc-v2') + [7],
                self.row('old-b', 'B', '', version='diana-v9', experiment='diana-abc-v2') + [9],
                self.row('same-c', 'C', '', version='diana-v9', experiment='diana-abc-v2') + [1],
                self.row('old-c', 'C', '', version='diana-v9', experiment='diana-abc-v2') + [3]]
        path = self.export(rows, headers)
        latest = analyze_csv(path)
        historical = analyze_csv(path, 'v9')
        self.assertEqual(latest['selected_cohort'], 'v10')
        self.assertEqual(latest['experiment_id'], 'diana-abc-v3')
        self.assertEqual(latest['questionnaire_version'], 'diana-v10')
        self.assertEqual(latest['primary_comparison']['mean_difference'], 4)
        self.assertEqual(historical['selected_cohort'], 'v9')
        self.assertEqual(historical['experiment_id'], 'diana-abc-v2')
        self.assertEqual(historical['questionnaire_version'], 'diana-v9')
        self.assertEqual(historical['primary_comparison']['mean_difference'], -6)
        for result in (latest, historical):
            self.assertEqual(result['cohort']['eligible_rows'], 4)
            self.assertEqual(result['cohort']['excluded_experiment_or_version_rows'], 4)
        with self.assertRaisesRegex(AnalysisError, 'pooling is not supported'):
            analyze_csv(path, 'all')
        with self.assertRaisesRegex(AnalysisError, 'No eligible data'):
            analyze_csv(self.export(rows[4:], headers))

    def test_historical_technical_csv_uses_only_v9_primary_column(self):
        headers = [name.replace('v10_', 'v9_') for name in TECHNICAL]
        rows = [self.row('old-b', 'B', 8, version='diana-v9', experiment='diana-abc-v2'),
                self.row('old-c', 'C', 9, version='diana-v9', experiment='diana-abc-v2')]
        result = analyze_csv(self.export(rows, headers), 'v9')
        self.assertEqual(result['primary_comparison']['mean_difference'], 1)
        self.assertEqual(result['groups']['B']['primary']['n'], 1)
        self.assertEqual(result['groups']['C']['primary']['n'], 1)

    def test_welch_and_small_sample_corrected_g_match_known_values(self):
        result = compare_groups([3, 4, 5], [1, 2, 3])
        self.assertEqual(result['status'], 'estimated')
        self.assertAlmostEqual(result['welch_df'], 4)
        self.assertAlmostEqual(result['welch_t'], math.sqrt(6))
        self.assertAlmostEqual(result['p_two_sided'], 0.07048399691021993)
        self.assertAlmostEqual(result['pooled_sample_sd'], 1)
        self.assertAlmostEqual(result['hedges_g'], 2*math.sqrt(2/math.pi))
        self.assertLess(result['confidence_interval'][0], 0)
        self.assertAlmostEqual(sum(result['confidence_interval'])/2, 2)
        reverse = compare_groups([1, 2, 3], [3, 4, 5])
        self.assertEqual(reverse['mean_difference'], -2)
        self.assertAlmostEqual(reverse['p_two_sided'], result['p_two_sided'])
        self.assertAlmostEqual(reverse['hedges_g'], -result['hedges_g'])

    def test_unequal_variances_use_welch_degrees_of_freedom(self):
        result = compare_groups([8, 8, 8, 8], [1, 2, 4])
        self.assertEqual(result['status'], 'estimated')
        self.assertAlmostEqual(result['welch_df'], 2)
        self.assertTrue(math.isfinite(result['hedges_g']))
        self.assertTrue(0 <= result['p_two_sided'] <= 1)

    def test_insufficient_and_constant_samples_never_invent_p_values(self):
        for c, b, status in [([], [], 'insufficient_data'), ([8], [3, 4], 'insufficient_data'),
                             ([4, 4], [4, 4], 'zero_variance'), ([8, 8], [3, 3], 'zero_variance')]:
            with self.subTest(c=c, b=b):
                result = compare_groups(c, b)
                self.assertEqual(result['status'], status)
                self.assertIsNone(result['p_two_sided'])
                self.assertIsNone(result['confidence_interval'])
                self.assertIsNone(result['hedges_g'])
                json.dumps(result, allow_nan=False)

    def test_primary_parser_accepts_only_integer_values_within_one_to_ten(self):
        for raw, expected in [('1', 1), ('10', 10), (' 8 ', 8), ('8.0', 8), ('8,0', 8)]:
            self.assertEqual(primary_value(raw), (expected, None))
        for raw in ['0', '11', '-1', '3.5', 'NaN', 'Infinity', '=8', 'yes', '1'*100]:
            self.assertEqual(primary_value(raw), (None, 'invalid'))
        for raw in ['', 'not_assessable', 'not_used', 'not_specified']:
            self.assertEqual(primary_value(raw), (None, 'missing'))

    def test_duplicate_target_ids_fail_even_if_one_primary_is_missing(self):
        with self.assertRaisesRegex(AnalysisError, 'Duplicate participation'):
            analyze_csv(self.export([self.row('fake-same', 'B', 8), self.row('fake-same', 'C', '')]))
        result = analyze_csv(self.export([self.row('fake-same', 'B', 8), self.row('fake-same', 'B', 8, version='diana-v8')]))
        self.assertEqual(result['cohort']['eligible_rows'], 1)

    def test_missing_id_invalid_arm_wrong_version_and_bad_headers_fail_clearly(self):
        for rows, message in [([self.row('', 'B', 8)], 'no participation ID'),
                              ([self.row('fake', 'D', 8)], 'valid assigned arm'),
                              ([self.row('fake', 'B', 8, version='diana-v8')], 'No eligible data')]:
            with self.subTest(message=message), self.assertRaisesRegex(AnalysisError, message):
                analyze_csv(self.export(rows))
        with self.assertRaisesRegex(AnalysisError, 'Exactly one column'):
            analyze_csv(self.export([], GERMAN[:-3]))
        with self.assertRaisesRegex(AnalysisError, 'duplicate column'):
            analyze_csv(self.export([], GERMAN + ['experiment_id']))

    def test_no_eligible_cli_writes_no_output_and_reports_no_rows(self):
        output = Path(self.folder.name) / 'result.json'
        self.export([self.row('fake', 'B', 8, version='diana-v8')])
        error = io.StringIO()
        with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as exit:
            main([str(self.path), '--output', str(output)])
        self.assertEqual(exit.exception.code, 2)
        self.assertIn('No eligible data', error.getvalue())
        self.assertNotIn('fake', error.getvalue())
        self.assertFalse(output.exists())

    def test_output_never_overwrites_existing_file(self):
        output = Path(self.folder.name) / 'result.json'
        write_json({'safe': True}, output)
        original = output.read_bytes()
        with self.assertRaises(FileExistsError):
            write_json({'different': True}, output)
        self.assertEqual(output.read_bytes(), original)


class PlanningTests(unittest.TestCase):
    def test_requested_scenarios_and_integer_minima(self):
        result = plan()
        self.assertEqual([row['valid_primary_answers_per_arm'] for row in result['scenarios']], [176, 100, 64])
        self.assertEqual([row['valid_primary_answers_total_abc'] for row in result['scenarios']], [528, 300, 192])
        self.assertEqual([row['starts_total_abc_after_25_percent_loss_allowance'] for row in result['scenarios']], [704, 400, 256])
        self.assertEqual([row['equal_rounded_starts_total_abc'] for row in result['scenarios']], [705, 402, 258])
        for row in result['scenarios']:
            self.assertGreaterEqual(row['achieved_power_at_n'], .8)
            self.assertLess(row['power_at_one_fewer_per_arm'], .8)

    def test_planning_rejects_invalid_assumptions(self):
        for value in [0, -1, math.inf, math.nan]:
            with self.assertRaises(ValueError):
                required_per_arm(value)
        with self.assertRaises(ValueError):
            required_per_arm(.5, power=1)
        with self.assertRaises(ValueError):
            two_sample_power(1, .5)


if __name__ == '__main__':
    unittest.main()
