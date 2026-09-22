"""Pre-specified V14 contrasts; no API calls and no mutation of study data.

CLI expects the admin's TECHNICAL CSV export. Results remain preliminary until
an analysis plan and recruitment window have been frozen before the main wave.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import optimize, special, stats

ANALYSIS_VERSION = 'diana-v14-analysis-1'
CONSTRUCTS = {
    'usefulness': ('usefulness_ideal', 'usefulness_find_easy', 'usefulness_suggestions'),
    'control': ('control_preferences', 'control_recommendations', 'control_adjustment'),
    'transparency': ('transparency_why', 'transparency_assessment', 'transparency_fit'),
    'trust': ('trust_fit', 'trust_credibility'),
}
SINGLES = ('dialogue_understanding', 'dialogue_response_quality', 'dialogue_attentiveness',
           'overall_satisfaction', 'intention_reuse', 'study_effort', 'study_style_control',
           'perceived_character')
ARMS = ('A', 'B', 'C')


def plan_metadata(path=None):
    """Read the versioned plan; validate configured dates without claiming external registration."""
    path = Path(path) if path else Path(__file__).with_name('analysis_plan.json')
    raw = path.read_bytes()
    content = json.loads(raw)
    status = content.get('status')
    if status not in ('draft', 'frozen_before_main'):
        raise ValueError('Analysis plan status must be draft or frozen_before_main.')
    if content.get('questionnaire_version') != 'diana-v14' or content.get('analysis_version') != ANALYSIS_VERSION:
        raise ValueError('Analysis plan does not match this questionnaire/analysis version.')
    if content.get('alpha') != .05 or content.get('power') != .8:
        raise ValueError('This analysis implementation is specified for alpha=.05 and power=.8.')
    dates = {}
    for field in ('frozen_at_utc', 'main_recruitment_start_utc', 'main_recruitment_end_utc'):
        value = content.get(field)
        if value is not None:
            try:
                date = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (AttributeError, ValueError) as error:
                raise ValueError(f'Invalid analysis plan date: {field}') from error
            if date.tzinfo is None or date.utcoffset().total_seconds() != 0:
                raise ValueError(f'{field} must have an explicit UTC offset.')
            dates[field] = date
    effect = content.get('smallest_effect_of_interest_d')
    dropout = content.get('expected_dropout_fraction')
    planned = content.get('planned_valid_participants_per_arm')
    if effect is not None and (isinstance(effect, bool) or not isinstance(effect, (int, float)) or not math.isfinite(effect) or effect <= 0):
        raise ValueError('SESOI must be a positive finite number or null.')
    if dropout is not None and (isinstance(dropout, bool) or not isinstance(dropout, (int, float)) or not 0 <= dropout < 1):
        raise ValueError('Expected dropout fraction must be in [0, 1) or null.')
    if planned is not None and (type(planned) is not int or planned < 2):
        raise ValueError('Planned valid participants per arm must be an integer >= 2 or null.')
    commit = content.get('freeze_git_commit')
    if commit is not None and (not isinstance(commit, str) or len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit)):
        raise ValueError('freeze_git_commit must be a full lowercase Git SHA-1 or null.')
    if status == 'frozen_before_main':
        if len(dates) != 3 or None in (effect, dropout, planned, commit):
            raise ValueError('A frozen plan needs SESOI, dropout reserve, sample target, three dates and a Git commit.')
        if not dates['frozen_at_utc'] < dates['main_recruitment_start_utc'] < dates['main_recruitment_end_utc']:
            raise ValueError('Freeze must precede recruitment, and recruitment must end after its start.')
    primary = content.get('primary', {})
    secondary = content.get('secondary_holm_family', [])
    if (primary.get('construct'), primary.get('first'), primary.get('second')) != ('usefulness', 'C', 'B'):
        raise ValueError('Plan primary contrast differs from the implemented analysis.')
    if [(x.get('construct'), x.get('first'), x.get('second')) for x in secondary] != [
        ('control', 'C', 'B'), ('transparency', 'C', 'B'), ('usefulness', 'B', 'A')]:
        raise ValueError('Plan secondary family differs from the implemented analysis.')
    return {'status': status, 'sha256': hashlib.sha256(raw).hexdigest(), 'contents': content,
            'provenance_note': 'Configured plan state; Git chronology/external registration not independently verified.'}


def _tokens(value):
    if value is None or value == '':
        return []
    values = value if isinstance(value, (list, tuple, set)) else str(value).split('|')
    return sorted({str(v).strip() for v in values if v is not None and str(v).strip()})


def treatment_versions(rows):
    """Report heterogeneity and unknown exposure without inventing historical metadata."""
    arms = {}
    for arm in ARMS:
        group = [r for r in rows if r['study_arm'] == arm]
        prompt_versions, releases = set(), set()
        policies, revisions, hashes = set(), set(), set()
        unknown_prompt = unknown_release = multi_release_participants = 0
        for row in group:
            policy, revision, digest = (row.get(k) for k in ('system_prompt_policy', 'system_prompt_revision', 'system_prompt_base_sha256'))
            if revision in (None, '') or not digest or not policy:
                unknown_prompt += 1
            if policy:
                policies.add(str(policy))
            if revision not in (None, ''):
                revisions.add(str(revision))
            if digest:
                hashes.add(str(digest))
            if revision not in (None, '') or digest:
                prompt_versions.add(f'{policy or "unknown"}:{revision if revision not in (None, "") else "unknown"}:{digest or "unknown"}')
            used = _tokens(row.get('study_release_ids'))
            releases.update(used)
            unknown_release += not bool(used)
            multi_release_participants += len(used) > 1
        arms[arm] = {'prompt_versions': sorted(prompt_versions), 'study_release_ids': sorted(releases),
                     'unknown_prompt_participants': unknown_prompt, 'unknown_release_participants': unknown_release,
                     'multiple_release_participants': multi_release_participants,
                     'mixed_prompt_versions': any(len(values) > 1 for values in (policies, revisions, hashes)), 'mixed_system_releases': len(releases) > 1}
    return arms


def answer(row, name):
    nested = row.get('answers') or {}
    return nested.get(name, row.get('v14_' + name, row.get(name)))


def rating(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number.is_integer() and 1 <= number <= 7 else None


def _safe(value):
    return float(value) if value is not None and math.isfinite(float(value)) else None


def _meta(row, name):
    return row.get(name, (row.get('study_context') or {}).get(name))


def complete_items(row, construct):
    values = [rating(answer(row, field)) for field in CONSTRUCTS[construct]]
    return values if all(value is not None for value in values) else None


def values_for(rows, field):
    if field in CONSTRUCTS:
        return np.asarray([np.mean(values) for row in rows
                           if (values := complete_items(row, field)) is not None], dtype=float)
    return np.asarray([value for row in rows if (value := rating(answer(row, field))) is not None], dtype=float)


def describe(values):
    values = np.asarray(values, dtype=float)
    return {'n': len(values), 'mean': _safe(np.mean(values)) if len(values) else None,
            'sd': _safe(np.std(values, ddof=1)) if len(values) > 1 else None,
            'median': _safe(np.median(values)) if len(values) else None}


def _hedges(first, second, axis=None):
    n1, n2 = first.shape[-1], second.shape[-1]
    df = n1 + n2 - 2
    pooled = ((n1 - 1) * np.var(first, axis=axis, ddof=1) +
              (n2 - 1) * np.var(second, axis=axis, ddof=1)) / df
    correction = math.exp(special.gammaln(df / 2) - .5 * math.log(df / 2) - special.gammaln((df - 1) / 2))
    with np.errstate(divide='ignore', invalid='ignore'):
        return correction * (np.mean(first, axis=axis) - np.mean(second, axis=axis)) / np.sqrt(pooled)


def compare(first, second, *, comparison_id='', construct='', contrast='', bootstrap_samples=5000):
    first, second = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    d1, d2 = describe(first), describe(second)
    out = {'id': comparison_id, 'construct': construct, 'contrast': contrast,
           'n_first': d1['n'], 'n_second': d2['n'], 'mean_first': d1['mean'], 'mean_second': d2['mean'],
           'sd_first': d1['sd'], 'sd_second': d2['sd'], 'difference': None, 'difference_ci95': None,
           'statistic': None, 'df': None, 'p_value': None, 'hedges_g': None, 'hedges_g_ci95': None,
           'mann_whitney_p': None, 'levene_p_diagnostic_only': None, 'status': 'insufficient_data',
           'method': 'two-sided Welch t-test; no variance-test-based selection',
           'g_ci_method': 'independent-group percentile bootstrap, deterministic seed, 5000 replicates'}
    if min(len(first), len(second)) < 2:
        return out
    out['difference'] = float(np.mean(first) - np.mean(second))
    a, b = np.var(first, ddof=1) / len(first), np.var(second, ddof=1) / len(second)
    if a + b <= 0:
        out['status'] = 'zero_variance'
        return out
    df = (a + b) ** 2 / (a * a / (len(first) - 1) + b * b / (len(second) - 1))
    se = math.sqrt(a + b)
    half = stats.t.ppf(.975, df) * se
    statistic = out['difference'] / se
    out.update(status='ok', statistic=_safe(statistic), df=_safe(df),
               p_value=_safe(2 * stats.t.sf(abs(statistic), df)),
               difference_ci95=[float(out['difference'] - half), float(out['difference'] + half)],
               hedges_g=_safe(_hedges(first, second)))
    if bootstrap_samples and out['hedges_g'] is not None:
        seed = int(hashlib.sha256((comparison_id + ':' + construct + ':' + contrast).encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        samples = _hedges(rng.choice(first, (bootstrap_samples, len(first))),
                          rng.choice(second, (bootstrap_samples, len(second))), axis=1)
        valid = samples[np.isfinite(samples)]
        # Do not conceal degenerate bootstrap draws in very small/discrete samples.
        out['g_ci_valid_replicates'] = len(valid)
        out['g_ci_replicates'] = bootstrap_samples
        out['g_ci_method'] = f'independent-group percentile bootstrap, deterministic seed, {bootstrap_samples} replicates'
        if len(valid) >= .99 * bootstrap_samples:
            out['hedges_g_ci95'] = [float(x) for x in np.quantile(valid, [.025, .975])]
        else:
            out['g_ci_warning'] = 'Over 1% zero-variance bootstrap draws; interval not reported.'
    out['mann_whitney_p'] = _safe(stats.mannwhitneyu(first, second, alternative='two-sided', method='asymptotic').pvalue)
    # Levene is diagnostic only; Welch is used regardless of this value.
    deviations = [np.abs(x - np.median(x)) for x in (first, second)]
    if any(np.var(x) > 0 for x in deviations):
        out['levene_p_diagnostic_only'] = _safe(stats.levene(first, second, center='median').pvalue)
    return out


def holm(p_values):
    """Keep the prespecified family size even if one test is not estimable."""
    adjusted = [None] * len(p_values)
    ordered = sorted((float(p), i) for i, p in enumerate(p_values) if p is not None)
    prior = 0.0
    for rank, (p, index) in enumerate(ordered):
        prior = max(prior, (len(p_values) - rank) * p)
        adjusted[index] = min(1.0, prior)
    return adjusted


def reliability(rows, construct):
    items = [values for row in rows if (values := complete_items(row, construct)) is not None]
    out = {'n': len(items), 'items': len(CONSTRUCTS[construct]), 'alpha': None,
           'status': 'insufficient_data', 'interpretation': 'Reliability does not establish construct validity.'}
    if len(items) < 2:
        return out
    matrix = np.asarray(items, dtype=float)
    total_variance = np.var(matrix.sum(axis=1), ddof=1)
    k = matrix.shape[1]
    if total_variance <= 0:
        out['status'] = 'zero_total_variance'
        return out
    out['alpha'] = _safe(k / (k - 1) * (1 - np.var(matrix, axis=0, ddof=1).sum() / total_variance))
    out['status'] = 'ok'
    out['below_point_seven'] = out['alpha'] < .7
    if k == 2:
        if all(np.var(matrix[:, i]) > 0 for i in range(k)):
            r = _safe(np.corrcoef(matrix.T)[0, 1])
            out['inter_item_correlation'] = r
            out['spearman_brown'] = _safe(2 * r / (1 + r)) if r > -1 else None
        out['interpretation'] = 'Adapted two-item trust pair; alpha and Spearman–Brown are descriptive, not a validation.'
    return out


def power_plan():
    """Balanced independent t-test planning benchmark, not exact unequal-variance Welch power."""
    def power(d, n):
        df = 2 * n - 2
        critical = stats.t.ppf(.975, df)
        ncp = d * math.sqrt(n / 2)
        return float(stats.nct.sf(critical, df, ncp) + stats.nct.cdf(-critical, df, ncp))
    target_n = optimize.brentq(lambda n: power(.35, n) - .8, 3, 1000)
    detectable = optimize.brentq(lambda d: power(d, 130) - .8, .001, 1)
    return {'alpha': .05, 'power': .8, 'alternative': 'two-sided', 'example_effect_d': .35,
            'n_per_group_at_d_035': math.ceil(target_n), 'n_per_group_continuous': target_n,
            'total_three_groups_at_d_035': 3 * math.ceil(target_n),
            'detectable_d_at_n_130': detectable, 'power_at_d_035_n_130': power(.35, 130),
            'method': 'noncentral t; balanced equal-variance planning benchmark, equivalent to statsmodels TTestIndPower; not exact Welch power',
            'planning_status': 'example only: SESOI, dropout reserve and recruitment dates not yet fixed'}


def _comparison(rows, construct, first, second, id):
    return compare(values_for([r for r in rows if r['study_arm'] == first], construct),
                   values_for([r for r in rows if r['study_arm'] == second], construct),
                   comparison_id=id, construct=construct, contrast=f'{first} - {second}')


def _hypotheses(rows):
    primary = _comparison(rows, 'usefulness', 'C', 'B', 'H1')
    secondary = [_comparison(rows, 'control', 'C', 'B', 'S1'),
                 _comparison(rows, 'transparency', 'C', 'B', 'S2'),
                 _comparison(rows, 'usefulness', 'B', 'A', 'S3')]
    secondary[2]['interpretation'] = 'Package comparison; does not isolate personality.'
    for result, adjusted in zip(secondary, holm([r['p_value'] for r in secondary])):
        result['p_holm'] = adjusted
        result['multiplicity_family'] = 'S1, S2, S3 only (3 tests)'
    return primary, secondary


def analyze_rows(rows, operations=None, *, plan_status=None, include_inference=True):
    plan = plan_metadata()
    if plan_status is not None and plan_status != plan['status']:
        raise ValueError('plan_status override contradicts the versioned analysis_plan.json.')
    plan_status = plan['status']
    rows = list(rows)
    ids = [str(r.get('participation_id', r.get('id'))) for r in rows if r.get('participation_id', r.get('id'))]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate participation_id: merge exports without double-counting before analysis.')
    excluded, included = Counter(), []
    for original in rows:
        row = dict(original)
        version = row.get('survey_version', row.get('version'))
        arm = row.get('study_arm', answer(row, 'study_arm'))
        if version != 'diana-v14':
            excluded['not_v14'] += 1
        elif _meta(row, 'study_wave') != 'main':
            excluded['not_main_wave'] += 1
        elif arm not in ARMS:
            excluded['missing_or_invalid_arm'] += 1
        elif row.get('technical_exclusion') in (True, 1, '1', 'true', 'yes'):
            if not str(row.get('technical_exclusion_reason', '')).strip():
                raise ValueError('A technical exclusion needs a documented technical_exclusion_reason.')
            excluded['documented_terminal_technical_failure'] += 1
        else:
            row['study_arm'] = arm
            included.append(row)
    flow = {'input_total': len(rows), 'included_main': len(included), 'excluded_by_reason': dict(excluded),
            'arms': {arm: sum(r['study_arm'] == arm for r in included) for arm in ARMS},
            'missing_constructs': {name: sum(complete_items(r, name) is None for r in included) for name in CONSTRUCTS}}
    out = {'analysis_version': ANALYSIS_VERSION, 'plan_status': plan_status,
           'status': 'analyzed' if include_inference else 'descriptive_only', 'sample_flow': flow,
           'warnings': ['Incomplete questionnaires contribute whenever all endpoint items are valid.',
                        'Recovered operation errors never automatically exclude a participant.',
                        'A null manipulation test does not prove equivalence or absence of perception.',
                        'No subgroup causal claim: self-reported customization is self-selected.'],
           'power': power_plan(), 'descriptives': {}, 'reliability': {}}
    out['analysis_plan'] = plan
    out['analysis_plan_sha256'] = plan['sha256']
    out['treatment_versions'] = treatment_versions(included)
    out['interpretation_status'] = 'preliminary_exploratory' if plan_status != 'frozen_before_main' else 'configured_frozen_plan'
    if any(v['mixed_prompt_versions'] or v['mixed_system_releases'] for v in out['treatment_versions'].values()):
        out['warnings'].append('Mixed prompt revisions or system releases within arms: pooled findings are preliminary; inspect treatment_versions and report release-specific sensitivity, not a homogeneous confirmatory treatment.')
        out['interpretation_status'] = 'preliminary_mixed_treatments'
    if any(v['unknown_prompt_participants'] or v['unknown_release_participants'] for v in out['treatment_versions'].values()):
        out['warnings'].append('Some treatment-version metadata are unknown; version homogeneity cannot be verified or retroactively assumed.')
    if plan_status != 'frozen_before_main':
        out['warnings'].insert(0, 'Draft analysis plan: all findings are preliminary/exploratory, not preregistered confirmatory evidence.')
    for field in (*CONSTRUCTS, *SINGLES):
        out['descriptives'][field] = {arm: describe(values_for([r for r in included if r['study_arm'] == arm], field)) for arm in ARMS}
    for name in CONSTRUCTS:
        out['reliability'][name] = reliability(included, name)
        out['reliability'][name]['by_arm'] = {arm: reliability([r for r in included if r['study_arm'] == arm], name) for arm in ARMS}
    out['metadata'] = {name: dict(Counter(str(_meta(r, name) or 'missing') for r in included))
                       for name in ('viewport_class', 'recruitment_batch', 'furthest_step_reached')}
    if operations is not None:
        ids_set = {str(r.get('participation_id', r.get('id'))) for r in included}
        operations = [o for o in operations if str(o.get('participation_id', o.get('consent_id'))) in ids_set]
        out['operation_errors'] = dict(Counter(f"{o.get('error_stage', 'unknown')}:{o['error_code']}" for o in operations if o.get('error_code')))
    if not include_inference:
        return out
    out['primary'], out['secondary'] = _hypotheses(included)
    out['exploratory'] = [_comparison(included, 'usefulness', 'C', 'A', 'E1')]
    c_rows = [r for r in included if r['study_arm'] == 'C']
    customized = lambda r: answer(r, 'personality_customized') in ('yes', 1, '1')
    uncustomized = lambda r: answer(r, 'personality_customized') in ('no', 0, '0')
    out['exploratory'].append(compare(values_for([r for r in c_rows if customized(r)], 'usefulness'),
                                      values_for([r for r in c_rows if uncustomized(r)], 'usefulness'),
                                      comparison_id='E2', construct='usefulness', contrast='C customized - C unchanged (self-report)'))
    groups = [values_for([r for r in included if r['study_arm'] == arm], 'perceived_character') for arm in ARMS]
    manipulation = {'groups': out['descriptives']['perceived_character'], 'h': None, 'p_value': None,
                    'status': 'insufficient_data', 'method': 'Kruskal–Wallis, asymptotic tie-corrected; ordinal single item',
                    'interpretation': 'Expected A < B and A < C; descriptive pattern and uncertainty do not gate H1.'}
    if all(len(g) >= 5 for g in groups):
        if len(set(np.concatenate(groups))) > 1:
            result = stats.kruskal(*groups)
            manipulation.update(h=_safe(result.statistic), p_value=_safe(result.pvalue), status='ok')
        else:
            manipulation['status'] = 'all_identical'
    out['manipulation'] = manipulation
    no_repeat = [r for r in included if answer(r, 'previous_participation') not in ('yes', 1, '1')]
    first_time_only = [r for r in included if answer(r, 'previous_participation') in ('no', 0, '0')]
    for key, subset in [('sensitivity_without_repeat', no_repeat), ('sensitivity_first_time_only', first_time_only)]:
        primary, secondary = _hypotheses(subset)
        out[key] = {'n': len(subset), 'primary': primary, 'secondary': secondary,
                    'interpretation': 'Sensitivity only, not another confirmatory family or replacement for H1.'}
    return out


def markdown_report(result):
    lines = ['# DIANA V14 – statistische Auswertung', '',
             f"Analysestand: `{result['analysis_version']}` · Planstatus: `{result['plan_status']}`",
             f"Plan-SHA-256: `{result['analysis_plan_sha256']}`", '']
    lines += ['- ' + warning for warning in result['warnings']]
    lines += ['', '## Stichprobe', '', '```json', json.dumps(result['sample_flow'], ensure_ascii=False, indent=2), '```', '',
              '## Vorab festgelegte Vergleiche', '',
              '| Test | Vergleich | n | M (SD) | Differenz [95%-KI] | Hedges g [95%-KI] | p | Holm-p |',
              '| --- | --- | --- | --- | --- | --- | --- | --- |']
    def fmt(value):
        if value is None:
            return 'nicht schätzbar'
        if isinstance(value, list):
            return '[' + ', '.join(fmt(v) for v in value) + ']'
        return f'{value:.6g}' if isinstance(value, (float, int)) else str(value)
    for r in [result.get('primary')] + result.get('secondary', []) + result.get('exploratory', []):
        if r:
            lines.append(f"| {r['id']} / {r['construct']} | {r['contrast']} | {r['n_first']} / {r['n_second']} | {fmt(r['mean_first'])} ({fmt(r['sd_first'])}) / {fmt(r['mean_second'])} ({fmt(r['sd_second'])}) | {fmt(r['difference'])} {fmt(r['difference_ci95'])} | {fmt(r['hedges_g'])} {fmt(r['hedges_g_ci95'])} | {fmt(r['p_value'])} | {fmt(r.get('p_holm'))} |")
    lines += ['', 'Alle Tests zweiseitig. CIs für g: unabhängiger Perzentil-Bootstrap; bei kleinen Stichproben vorsichtig interpretieren.',
              'Mann–Whitney-Sensitivität, Einzelitem-Deskriptivwerte, Reliabilität je Gruppe, Manipulationscheck und Wiederholungssensitivität stehen vollständig in der JSON-Datei.', '',
              '## Reliabilität', '', '| Konstrukt | vollständige Fälle | α |', '| --- | --- | --- |']
    lines += [f"| {name} | {r['n']} | {fmt(r['alpha'])} |" for name, r in result['reliability'].items()]
    lines += ['', '## Manipulationscheck', '', '```json', json.dumps(result.get('manipulation'), ensure_ascii=False, indent=2), '```', '',
              '## Fallzahlbeispiel, noch keine festgelegte Zielgröße', '', '```json', json.dumps(result['power'], ensure_ascii=False, indent=2), '```', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path, help='Technical admin CSV export, questionnaire V14')
    parser.add_argument('--output', type=Path, required=True, help='Output filename without extension')
    parser.add_argument('--operations', type=Path, help='Optional raw operation CSV for error descriptions')
    args = parser.parse_args()
    def read(path):
        with path.open(encoding='utf-8-sig', newline='') as f:
            return list(csv.DictReader(f, delimiter=';'))
    result = analyze_rows(read(args.csv), read(args.operations) if args.operations else None)
    result['input_sha256'] = hashlib.sha256(args.csv.read_bytes()).hexdigest()
    result['source_file'] = args.csv.name
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix('.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    args.output.with_suffix('.md').write_text(markdown_report(result), encoding='utf-8')
    print(f"Written {args.output.with_suffix('.json')} and {args.output.with_suffix('.md')}")


if __name__ == '__main__':
    main()
