#!/usr/bin/env python3
"""A priori sample planning for the prespecified independent C-versus-B contrast.

For a two-sided equal-size two-sample t test, df = 2*n - 2 and noncentrality
= standardized mean difference d * sqrt(n/2). Power is the sum of the two
noncentral-t tail probabilities beyond the central-t alpha/2 cutoffs. The script
finds the smallest integer n per compared arm meeting 80% power at alpha=.05.
This normal/common-variance planning approximation is not a guarantee for the
bounded, ordinal single item or for the actual unequal-variance Welch analysis.
A is allocated the same planned n but is not a second primary comparison.

The 25% loss allowance is a planning assumption, not an observed dropout rate.
Total inflation and equal-per-arm rounded inflation are reported separately.
Simple randomization does not guarantee equal realized group sizes.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import sys

import numpy
import scipy
from scipy import stats


def two_sample_power(n, effect, alpha=0.05):
    if not isinstance(n, int) or n < 2:
        raise ValueError('n must be an integer of at least 2 per arm.')
    if not math.isfinite(effect) or effect <= 0 or not 0 < alpha < 1:
        raise ValueError('Effect must be positive and finite; alpha must be between 0 and 1.')
    df = 2*n - 2
    critical = stats.t.ppf(1-alpha/2, df)
    noncentrality = effect * math.sqrt(n/2)
    return float(stats.nct.sf(critical, df, noncentrality) + stats.nct.cdf(-critical, df, noncentrality))


def required_per_arm(effect, alpha=0.05, power=0.8):
    if not 0 < power < 1:
        raise ValueError('Target power must be between 0 and 1.')
    low, high = 2, 2
    while two_sample_power(high, effect, alpha) < power:
        high *= 2
        if high > 10_000_000:
            raise ValueError('Required sample size exceeds the supported planning range.')
    while low < high:
        middle = (low+high)//2
        if two_sample_power(middle, effect, alpha) >= power:
            high = middle
        else:
            low = middle+1
    return low


def plan():
    scenarios = []
    for effect in (0.3, 0.4, 0.5):
        n = required_per_arm(effect)
        total = 3*n
        starts_per_arm = math.ceil(n / 0.75)
        scenarios.append({
            'standardized_effect_d': effect,
            'valid_primary_answers_per_arm': n,
            'valid_primary_answers_total_abc': total,
            'achieved_power_at_n': two_sample_power(n, effect),
            'power_at_one_fewer_per_arm': two_sample_power(n-1, effect),
            'starts_total_abc_after_25_percent_loss_allowance': math.ceil(total/0.75),
            'equal_rounded_starts_per_arm': starts_per_arm,
            'equal_rounded_starts_total_abc': 3*starts_per_arm,
        })
    return {
        'experiment_id': 'diana-abc-v2', 'questionnaire_version': 'diana-v9',
        'primary_contrast': 'C minus B', 'primary_item': 'system_usefulness',
        'alpha_two_sided': 0.05, 'target_power': 0.8,
        'assumed_loss_fraction': 0.25,
        'software': {'python': platform.python_version(), 'scipy': scipy.__version__, 'numpy': numpy.__version__},
        'scenarios': scenarios,
        'notes': [
            'Counts refer to usable primary answers, including those in incomplete questionnaires, not necessarily complete surveys.',
            'Normal equal-variance two-sample t planning; realized power for the Welch test on the 1–10 item can differ.',
            'The standardized effect is assumed a priori and is not estimated from the current trial.',
            'All three arms receive the same planned valid-answer target; only C versus B is primary.',
            'Total 25% inflation is not always divisible by three; equal-per-arm integer rounding is reported separately.',
            'Simple random allocation and unequal missingness may require more starts to reach each arm target.',
            'This script does not recruit participants, enforce a stopping rule, or change the system.',
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, help='New JSON file; existing files are never replaced')
    args = parser.parse_args(argv)
    encoded = json.dumps(plan(), ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    try:
        if args.output:
            with args.output.open('x', encoding='utf-8') as target:
                target.write(encoded)
        else:
            sys.stdout.write(encoded)
    except OSError as failure:
        parser.exit(2, f'Plan not written: {failure}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
