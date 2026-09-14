#!/usr/bin/env python3
"""Offline, prespecified C-versus-B analysis of the DIANA conference trial.

Read the admin Numiqo CSV (German or technical headers), select only
experiment diana-abc-v2 / questionnaire diana-v9, and include every valid
integer system_usefulness answer from 1 through 10, including partial responses.
The assigned arm determines the analysis; actual template/custom use never filters
participants. The export must include incomplete responses to implement this rule.

The primary estimate is mean(C) - mean(B), with a two-sided Welch t test and
95% Welch confidence interval. This treats the 10-point item as approximately
interval scaled and observations as independent. Hedges g uses the conventional
pooled sample SD and exact small-sample correction; its common-scale assumption
is additional to the unequal-variance Welch analysis. No composite scale is made.
For fewer than two valid observations in either arm, or zero variance in both
arms, inference is explicitly unavailable; no artificial p value is produced.

The JSON contains aggregates, input checksum and methods, never participant IDs
or free text. Only local files are read. Existing output files are never replaced.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import numpy
import scipy
from scipy import special, stats

EXPERIMENT = 'diana-abc-v2'
QUESTIONNAIRE = 'diana-v9'
PRIMARY_ITEM = 'system_usefulness'
ALIASES = {
    'participant': ('teilnahme_id', 'participation_id'),
    'experiment': ('experiment_id',),
    'version': ('fragebogen_version', 'survey_version'),
    'arm': ('studiengruppe', 'study_arm'),
    'primary': ('v9_system_nutzen', 'v9_system_usefulness'),
    'completion': ('teilnahme_status', 'response_status'),
}
MISSING = {'', 'not_used', 'not_assessable', 'not_specified'}


class AnalysisError(ValueError):
    """An input problem that can be reported without echoing participant data."""


def primary_value(cell):
    """Return (valid integer or None, missing/invalid classification)."""
    text = (cell or '').strip()
    if text in MISSING:
        return None, 'missing'
    if len(text) > 32:
        return None, 'invalid'
    try:
        value = Decimal(text.replace(',', '.'))
        if value.is_finite() and value == value.to_integral_value() and 1 <= value <= 10:
            return int(value), None
    except InvalidOperation:
        pass
    return None, 'invalid'


def describe(values):
    return {
        'n': len(values),
        'mean': statistics.mean(values) if values else None,
        'sample_sd': statistics.stdev(values) if len(values) >= 2 else None,
        'median': statistics.median(values) if values else None,
        'min': min(values) if values else None,
        'max': max(values) if values else None,
    }


def compare_groups(c_values, b_values):
    """Welch inference and pooled-SD Hedges g; degenerate data stay explicit."""
    result = dict(
        contrast='C minus B', status='insufficient_data',
        mean_difference=(statistics.mean(c_values) - statistics.mean(b_values)) if c_values and b_values else None,
        standard_error=None, welch_t=None, welch_df=None, p_two_sided=None,
        confidence_level=0.95, confidence_interval=None,
        hedges_g=None, pooled_sample_sd=None, hedges_correction=None,
    )
    if min(len(c_values), len(b_values)) < 2:
        result['reason'] = 'At least two valid primary answers per compared arm are required.'
        return result
    n_c, n_b = len(c_values), len(b_values)
    var_c, var_b = statistics.variance(c_values), statistics.variance(b_values)
    scaled_c, scaled_b = var_c / n_c, var_b / n_b
    se_squared = scaled_c + scaled_b
    if se_squared == 0:
        result.update(status='zero_variance', reason='Both arms have zero observed variance; t inference and standardized effect are undefined.')
        return result
    se = math.sqrt(se_squared)
    degrees = se_squared**2 / (scaled_c**2 / (n_c - 1) + scaled_b**2 / (n_b - 1))
    statistic = result['mean_difference'] / se
    critical = float(stats.t.ppf(0.975, degrees))
    pooled_df = n_c + n_b - 2
    pooled_sd = math.sqrt(((n_c - 1)*var_c + (n_b - 1)*var_b) / pooled_df)
    correction = math.exp(special.gammaln(pooled_df / 2) - 0.5*math.log(pooled_df / 2) - special.gammaln((pooled_df - 1) / 2))
    result.update(
        status='estimated', standard_error=se, welch_t=statistic, welch_df=degrees,
        p_two_sided=float(2 * stats.t.sf(abs(statistic), degrees)),
        confidence_interval=[result['mean_difference'] - critical*se, result['mean_difference'] + critical*se],
        hedges_g=correction * result['mean_difference'] / pooled_sd,
        pooled_sample_sd=pooled_sd, hedges_correction=correction,
    )
    return result


def analyze_csv(path):
    raw = Path(path).read_bytes()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError as failure:
        raise AnalysisError('The export must be a UTF-8 CSV file.') from failure
    first_line = text.splitlines()[0] if text.splitlines() else ''
    try:
        dialect = csv.Sniffer().sniff(first_line, delimiters=';,\t')
    except csv.Error as failure:
        raise AnalysisError('No usable CSV header found. Use the admin Numiqo CSV export.') from failure
    reader = csv.DictReader(io.StringIO(text, newline=''), dialect=dialect)
    headers = reader.fieldnames or []
    if len(headers) != len(set(headers)):
        raise AnalysisError('The CSV contains duplicate column names.')
    columns = {}
    for field, aliases in ALIASES.items():
        found = [alias for alias in aliases if alias in headers]
        if len(found) != 1:
            raise AnalysisError(f'Exactly one column is required for {field}: ' + ' or '.join(aliases))
        columns[field] = found[0]
    groups = {arm: dict(values=[], participants=0, missing=0, invalid=0, completion=Counter()) for arm in 'ABC'}
    seen = set()
    input_rows = excluded_rows = 0
    try:
        for row in reader:
            input_rows += 1
            if None in row or any(value is None for value in row.values()):
                raise AnalysisError(f'CSV row {reader.line_num} does not match its header.')
            if row[columns['experiment']].strip() != EXPERIMENT or row[columns['version']].strip() != QUESTIONNAIRE:
                excluded_rows += 1
                continue
            identifier = row[columns['participant']].strip()
            if not identifier:
                raise AnalysisError('A target-cohort row has no participation ID; deduplication cannot be verified.')
            if identifier in seen:
                raise AnalysisError('Duplicate participation IDs occur within the target cohort. Resolve them before analysis.')
            seen.add(identifier)
            arm = row[columns['arm']].strip()
            if arm not in groups:
                raise AnalysisError('A target-cohort row has no valid assigned arm A, B or C.')
            group = groups[arm]
            group['participants'] += 1
            status = row[columns['completion']].strip()
            group['completion'][status if status in ('completed', 'in_progress') else 'other_or_unspecified'] += 1
            value, reason = primary_value(row[columns['primary']])
            if value is not None:
                group['values'].append(value)
            else:
                group[reason] += 1
    except csv.Error as failure:
        raise AnalysisError('CSV parsing failed; check the delimiter and quotation marks.') from failure
    if not seen:
        raise AnalysisError(f'No eligible data: the file contains no {EXPERIMENT} / {QUESTIONNAIRE} rows.')
    return {
        'analysis': 'DIANA prespecified primary contrast',
        'experiment_id': EXPERIMENT, 'questionnaire_version': QUESTIONNAIRE,
        'primary_item': PRIMARY_ITEM,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'input_sha256': hashlib.sha256(raw).hexdigest(),
        'software': {'python': platform.python_version(), 'scipy': scipy.__version__, 'numpy': numpy.__version__},
        'cohort': {'input_rows': input_rows, 'eligible_rows': len(seen), 'excluded_experiment_or_version_rows': excluded_rows},
        'groups': {arm: {
            'participant_rows': group['participants'],
            'completion_status_counts': dict(group['completion']),
            'missing_primary': group['missing'],
            'invalid_primary': group['invalid'],
            'without_valid_primary': group['missing'] + group['invalid'],
            'primary': describe(group['values']),
        } for arm, group in groups.items()},
        'primary_comparison': compare_groups(groups['C']['values'], groups['B']['values']),
        'methods': {
            'included': 'All exported target-cohort participants with a valid integer primary answer 1–10, including in-progress responses; assigned groups, no filter on actual customization.',
            'test': 'Two-sided Welch independent-samples t test; alpha 0.05; 95% Welch confidence interval for mean(C) minus mean(B).',
            'effect_size': 'Hedges g = exact gamma small-sample correction times mean difference / pooled sample SD. This standardized measure assumes a meaningful common variance scale.',
            'assumptions': 'Independent participants; the 1–10 single item is treated as approximately interval scaled. No claim of a validated multi-item scale.',
            'missing': 'Missing and invalid primary values are excluded without imputation and counted separately by assigned arm.',
            'scope': 'Only rows present in this file are known. Export completed and incomplete responses together. Withdrawn, deleted, or unexported participants cannot be reconstructed from this file.',
        },
    }


def write_json(data, output=None):
    encoded = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if output is None:
        sys.stdout.write(encoded)
    else:
        with Path(output).open('x', encoding='utf-8') as target:
            target.write(encoded)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv_path', type=Path, help='Local Numiqo admin CSV, including incomplete responses')
    parser.add_argument('--output', type=Path, help='New JSON file (existing files are never replaced); default: stdout')
    args = parser.parse_args(argv)
    try:
        write_json(analyze_csv(args.csv_path), args.output)
    except (AnalysisError, OSError) as failure:
        parser.exit(2, f'Analysis not written: {failure}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
