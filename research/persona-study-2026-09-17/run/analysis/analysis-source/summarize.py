#!/usr/bin/env python3
"""Offline summary of the two-person A/B/C pilot. No network or model calls.

Usage:
    python summarize.py --run /absolute/path/to/run

Inputs: run/personas.json (the frozen six execution cases),
run/cases/{case_id}/T0..T3.json, run/judge-pools/{source_id}.json and
run/judgments/{source_id}.json. Missing snapshots are NA; existing snapshots
require a completely judged, matching common pool for their persona.

Judgment format (pool_sha256 hashes the exact pool file bytes):
    {"source_id": "P01", "pool_sha256": "<64 lowercase hexadecimal digits>",
     "assessor": "Codex", "judgments": [
       {"job_id": "<id>", "relevance": 2,
        "reason": "A concrete rationale.",
        "evidence": ["A specific quote or precise reference to the job text."]}]}

The rationale and evidence must be nonempty. evidence may alternatively be one
nonempty string. Grades are strict integers 0..3; true/false are not grades.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys
from typing import Any

from metrics import ndcg_at_k, precision_at_k, mrr_at_k

STUDY = Path(__file__).resolve().parent
ARMS = ('A', 'B', 'C')
TURNS = (0, 1, 2, 3)
METRICS = ('ndcg_10', 'ndcg_5', 'precision_5', 'rr_10')
LABELS = {'ndcg_10': 'nDCG@10', 'ndcg_5': 'nDCG@5',
          'precision_5': 'Precision@5', 'rr_10': 'RR@10'}
COMPARISONS = (('B', 'A'), ('C', 'A'), ('C', 'B'))


class ValidationError(ValueError):
    """An input violates the frozen evaluation design or data contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON object key: {key!r}')
        result[key] = value
    return result


def read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'),
                          object_pairs_hook=reject_duplicate_keys,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              ValidationError(f'Non-finite JSON value: {value}')))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f'Cannot read {path}: {error}') from error


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identifier(value: Any, where: str) -> str:
    require(type(value) in (str, int), f'{where}: job ID must be string or integer.')
    result = str(value)
    require(bool(result) and result == result.strip(), f'{where}: empty or padded ID.')
    return result


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def empty_metrics():
    return dict.fromkeys(METRICS)


def load_cases(run: Path, input_hashes: dict[str, str]):
    path = run / 'personas.json'
    data = read(path)
    input_hashes['personas.json'] = sha(path)
    cases = data.get('cases', data.get('personas')) if isinstance(data, dict) else data
    require(isinstance(cases, list) and len(cases) == 6,
            'The pilot requires six execution cases for two personas in A/B/C.')
    by_case = {}
    for row in cases:
        require(isinstance(row, dict), 'Execution case must be an object.')
        cid = row.get('case_id', row.get('id'))
        source = row.get('source_id')
        arm = row.get('assigned_arm')
        require(isinstance(cid, str) and re.fullmatch(r'[A-Za-z0-9_-]+', cid),
                'Invalid execution case ID.')
        require(isinstance(source, str) and re.fullmatch(r'[A-Za-z0-9_-]+', source),
                f'{cid}: invalid source ID.')
        require(arm in ARMS, f'{cid}: invalid arm.')
        require(row.get('fictional') is True or row.get('synthetic') is True,
                f'{cid}: not marked as synthetic.')
        require(cid not in by_case, f'Duplicate execution case {cid}.')
        require(isinstance(row.get('full_profile'), dict)
                and isinstance(row.get('full_information_need'), dict),
                f'{cid}: full reference profile/need missing.')
        by_case[cid] = {**row, 'case_id': cid}
    sources = sorted({row['source_id'] for row in by_case.values()})
    require(len(sources) == 2, 'Exactly two underlying personas are required.')
    for source in sources:
        group = [row for row in by_case.values() if row['source_id'] == source]
        require(len(group) == 3 and {row['assigned_arm'] for row in group} == set(ARMS),
                f'{source}: each arm must occur exactly once.')
        for field in ('initial_profile', 'full_profile', 'full_information_need',
                      'adaptive_message_stages'):
            require(field in group[0], f'{source}: missing frozen {field}.')
            require(all(row.get(field) == group[0][field] for row in group),
                    f'{source}: {field} differs across arms.')
    manifest_path = run / 'manifest.json'
    if manifest_path.exists():
        manifest = read(manifest_path)
        input_hashes['manifest.json'] = sha(manifest_path)
        expected = manifest.get('input_sha256', {}).get('personas.json')
        require(expected == input_hashes['personas.json'],
                'Frozen personas.json hash differs from manifest.json.')
        require(manifest.get('planned_personas') == 2
                and manifest.get('planned_sessions') == 6
                and manifest.get('planned_snapshots') == 24,
                'Manifest scope does not match this two-person pilot.')
    return by_case, sources


def load_snapshots(run, cases, input_hashes):
    records = []
    for cid, case in sorted(cases.items()):
        for turn in TURNS:
            record = {'case_id': cid, 'source_id': case['source_id'],
                      'name': case.get('name', case['source_id']),
                      'arm': case['assigned_arm'], 'turn': turn,
                      'snapshot': f'T{turn}', 'status': 'missing_snapshot',
                      'action': None, 'ranking_count': None,
                      'ranking': None, 'metrics': empty_metrics()}
            path = run / 'cases' / cid / f'T{turn}.json'
            if path.exists():
                data = read(path)
                input_hashes[path.relative_to(run).as_posix()] = sha(path)
                require(isinstance(data, dict), f'{path}: expected an object.')
                require(data.get('case_id') == cid
                        and data.get('source_id') == case['source_id']
                        and data.get('condition') == case['assigned_arm']
                        and type(data.get('turn')) is int and data['turn'] == turn,
                        f'{path}: snapshot identity does not match its case/filename.')
                ranking = data.get('ranking')
                require(isinstance(ranking, list) and len(ranking) <= 20,
                        f'{path}: ranking must contain at most twenty IDs.')
                ranking = [identifier(value, str(path)) for value in ranking]
                require(len(ranking) == len(set(ranking)), f'{path}: duplicate ranked ID.')
                if 'public_state' in data:
                    require(isinstance(data['public_state'], dict), f'{path}: invalid public state.')
                    jobs = data['public_state'].get('jobs')
                    require(isinstance(jobs, list), f'{path}: public jobs missing.')
                    require(all(isinstance(job, dict) for job in jobs), f'{path}: invalid public job object.')
                    actual = [identifier(job.get('id'), str(path)) for job in jobs]
                    require(ranking == actual, f'{path}: ranking differs from actual public jobs.')
                record.update(status='available', action=data.get('action'),
                              ranking_count=len(ranking), ranking=ranking)
            records.append(record)
    expected_dirs = set(cases)
    if (run / 'cases').exists():
        require(not any(path.is_dir() and path.name not in expected_dirs
                        for path in (run / 'cases').iterdir()),
                'Unexpected case directory; input contains unplanned execution cases.')
    return records


def load_judgments(run, source, case, records, input_hashes):
    snapshots = [r for r in records if r['source_id'] == source and r['status'] == 'available']
    pool_path = run / 'judge-pools' / f'{source}.json'
    judgment_path = run / 'judgments' / f'{source}.json'
    if not snapshots and not pool_path.exists() and not judgment_path.exists():
        return {}, {'source_id': source, 'status': 'no_snapshots',
                    'pool_size': 0, 'available_snapshots': 0, 'expected_snapshots': 12}
    pool = read(pool_path)
    require(isinstance(pool, dict) and pool.get('source_id') == source,
            f'{pool_path}: source ID mismatch.')
    require(pool.get('synthetic') is True, f'{pool_path}: not a synthetic pool.')
    require(pool.get('reference_profile') == case['full_profile']
            and pool.get('reference_need') == case['full_information_need'],
            f'{pool_path}: reference differs from frozen persona.')
    require(pool.get('rubric') == case['evaluation_relevance_rules'],
            f'{pool_path}: rubric differs from frozen persona.')
    require(type(pool.get('complete_snapshots')) is int
            and pool['complete_snapshots'] == len(snapshots)
            and type(pool.get('expected_snapshots')) is int
            and pool['expected_snapshots'] == 12,
            f'{pool_path}: snapshot coverage metadata is stale or invalid.')
    jobs = pool.get('jobs')
    require(isinstance(jobs, list), f'{pool_path}: jobs must be a list.')
    require(all(isinstance(job, dict) and 'id' in job for job in jobs),
            f'{pool_path}: invalid job object.')
    pool_ids = [identifier(job['id'], str(pool_path)) for job in jobs]
    require(len(pool_ids) == len(set(pool_ids)), f'{pool_path}: duplicate job ID.')
    require(type(pool.get('candidate_count')) is int and pool['candidate_count'] == len(pool_ids),
            f'{pool_path}: candidate count differs from job list.')
    union = {job_id for snapshot in snapshots for job_id in snapshot['ranking']}
    require(set(pool_ids) == union, f'{pool_path}: pool is not the exact union of all saved rankings.')
    pool_hash = sha(pool_path)
    input_hashes[pool_path.relative_to(run).as_posix()] = pool_hash
    if not snapshots and not pool_ids and not judgment_path.exists():
        return {}, {'source_id': source, 'name': case.get('name', source),
                    'status': 'no_snapshots', 'pool_size': 0,
                    'available_snapshots': 0, 'expected_snapshots': 12,
                    'pool_sha256': pool_hash}
    data = read(judgment_path)
    require(isinstance(data, dict) and data.get('source_id') == source,
            f'{judgment_path}: source ID mismatch.')
    require(data.get('pool_sha256') == pool_hash,
            f'{judgment_path}: pool hash mismatch; judgments belong to another/stale pool.')
    require(data.get('assessor') == 'Codex', f'{judgment_path}: expected assessor Codex.')
    rows = data.get('judgments')
    require(isinstance(rows, list), f'{judgment_path}: judgments must be a list.')
    grades = {}
    for index, judgment in enumerate(rows):
        where = f'{judgment_path}, judgment {index + 1}'
        require(isinstance(judgment, dict), f'{where}: expected object.')
        job_id = identifier(judgment.get('job_id'), where)
        require(job_id not in grades, f'{where}: duplicate judgment for {job_id}.')
        grade = judgment.get('relevance')
        require(type(grade) is int and 0 <= grade <= 3, f'{where}: relevance must be integer 0..3.')
        require(nonempty_text(judgment.get('reason')), f'{where}: reason must be nonempty.')
        evidence = judgment.get('evidence')
        require(nonempty_text(evidence) or (isinstance(evidence, list) and bool(evidence)
                                          and all(nonempty_text(item) for item in evidence)),
                f'{where}: evidence must be nonempty text or a nonempty list of texts.')
        grades[job_id] = grade
    missing, extra = set(pool_ids) - grades.keys(), grades.keys() - set(pool_ids)
    require(not missing and not extra,
            f'{judgment_path}: incomplete pool coverage; missing={sorted(missing)}, extra={sorted(extra)}.')
    input_hashes[judgment_path.relative_to(run).as_posix()] = sha(judgment_path)
    return grades, {'source_id': source, 'name': case.get('name', source),
                    'status': 'fully_judged', 'pool_size': len(pool_ids),
                    'available_snapshots': len(snapshots), 'expected_snapshots': 12,
                    'pool_sha256': pool_hash,
                    'judgments_sha256': sha(judgment_path),
                    'grade_counts': {str(i): Counter(grades.values()).get(i, 0) for i in range(4)}}


def mean(values):
    present = [value for value in values if value is not None]
    return statistics.mean(present) if present else None


def difference(current, baseline):
    return None if current is None or baseline is None else current - baseline


def output_key(key):
    return 'mrr_10' if key == 'rr_10' else key


def aggregate(records, sources):
    indexed = {(r['source_id'], r['arm'], r['turn']): r for r in records}
    for r in records:
        baseline = indexed[(r['source_id'], r['arm'], 0)]
        r['delta_from_T0'] = {key: difference(r['metrics'][key], baseline['metrics'][key])
                              for key in METRICS}
    arm_means = []
    for arm in ARMS:
        for turn in TURNS:
            group = [indexed[(source, arm, turn)] for source in sources]
            row = {'arm': arm, 'turn': turn, 'snapshot': f'T{turn}',
                   'planned_personas': len(sources),
                   'available_snapshots': sum(r['status'] == 'available' for r in group),
                   'metrics': {}, 'n_by_metric': {}, 'source_ids_by_metric': {},
                   'mean_paired_delta_from_T0': {}, 'n_paired_T0_by_metric': {},
                   'paired_T0_source_ids_by_metric': {}}
            for key in METRICS:
                outkey = output_key(key)
                available = [r for r in group if r['metrics'][key] is not None]
                paired = [r for r in group if r['delta_from_T0'][key] is not None]
                row['metrics'][outkey] = mean([r['metrics'][key] for r in available])
                row['n_by_metric'][outkey] = len(available)
                row['source_ids_by_metric'][outkey] = [r['source_id'] for r in available]
                row['mean_paired_delta_from_T0'][outkey] = mean([r['delta_from_T0'][key] for r in paired])
                row['n_paired_T0_by_metric'][outkey] = len(paired)
                row['paired_T0_source_ids_by_metric'][outkey] = [r['source_id'] for r in paired]
            arm_means.append(row)
    comparisons = []
    for higher, baseline in COMPARISONS:
        for turn in TURNS:
            row = {'comparison': f'{higher}-{baseline}', 'arm': higher, 'reference_arm': baseline,
                   'turn': turn, 'snapshot': f'T{turn}', 'metrics': {}}
            for key in METRICS:
                current_pairs, change_pairs = [], []
                for source in sources:
                    left = indexed[(source, higher, turn)]
                    right = indexed[(source, baseline, turn)]
                    delta = difference(left['metrics'][key], right['metrics'][key])
                    if delta is not None:
                        current_pairs.append({'source_id': source, 'arm_value': left['metrics'][key],
                                              'reference_value': right['metrics'][key], 'difference': delta})
                    change_delta = difference(left['delta_from_T0'][key], right['delta_from_T0'][key])
                    if change_delta is not None:
                        change_pairs.append({'source_id': source,
                                             'arm_change': left['delta_from_T0'][key],
                                             'reference_change': right['delta_from_T0'][key],
                                             'difference': change_delta})
                row['metrics'][output_key(key)] = {
                    'mean_paired_difference': mean([p['difference'] for p in current_pairs]),
                    'n_pairs': len(current_pairs), 'pairs': current_pairs,
                    'mean_difference_of_T0_changes': mean([p['difference'] for p in change_pairs]),
                    'n_T0_change_pairs': len(change_pairs), 'T0_change_pairs': change_pairs}
            comparisons.append(row)
    return arm_means, comparisons


def summarize(run: Path):
    run = run.resolve()
    input_hashes = {}
    cases, sources = load_cases(run, input_hashes)
    records = load_snapshots(run, cases, input_hashes)
    pools, qrels_by_source = [], {}
    for source in sources:
        case = next(c for c in cases.values() if c['source_id'] == source)
        qrels, information = load_judgments(run, source, case, records, input_hashes)
        pools.append(information)
        qrels_by_source[source] = qrels
    for r in records:
        if r['status'] != 'available':
            continue
        qrels = qrels_by_source[r['source_id']]
        r['metrics'] = {
            'ndcg_10': ndcg_at_k(r['ranking'], qrels, 10),
            'ndcg_5': ndcg_at_k(r['ranking'], qrels, 5),
            'precision_5': precision_at_k(r['ranking'], qrels, 5),
            'rr_10': mrr_at_k(r['ranking'], qrels, 10),
        }
    means, comparisons = aggregate(records, sources)
    available = sum(r['status'] == 'available' for r in records)
    return {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'design': {'synthetic': True, 'planned_personas': 2, 'source_ids': sources,
                   'planned_sessions': 6, 'planned_snapshots': 24,
                   'available_snapshots': available, 'missing_snapshots': 24 - available,
                   'complete': available == 24, 'arms': list(ARMS), 'turns': list(TURNS),
                   'additional_model_or_network_calls': 0},
        'definitions': {
            'ndcg': 'Gain 2^grade-1; log2(rank+1) discount; ideal ranking from the persona-specific common pool across all arms and turns.',
            'binary_relevance': 'Grades 2 and 3 count as relevant.',
            'precision_5': 'Relevant among first five divided by five, also for short result lists.',
            'rr_10': 'Single-person reciprocal rank of first relevant item among first ten; zero if none; NA if no judgment universe.',
            'mrr_10': 'Equal-weight mean of available individual RR@10 values at a fixed arm/turn; n is shown.',
            'missing': 'Missing snapshots and undefined metrics are null/NA, never fabricated zeroes.',
            'delta': 'Within-person change from the same arm at T0; aggregate only complete pairs.',
            'arm_differences': 'Contemporaneous within-person paired arm differences; change differences require all four relevant values.',
        },
        'limitations': [
            'Two deliberately constructed synthetic personas; repeated snapshots are not independent participants.',
            'One stochastic session per persona/arm; descriptive only, without significance tests, confidence intervals or general causal claims.',
            'Codex-created profiles and judgments; no independent human gold standard.',
            'Pool-relative nDCG, not an ideal ranking established over all 8,537 jobs.',
            'These are ranking metrics, not measures of chat quality, usability, participant satisfaction or real-world employment outcomes.',
            'Additional facts disclosed during chat can improve ranking; changes are not attributable to personality alone.',
        ],
        'pools': pools, 'per_persona_arm_turn': records,
        'arm_turn_means': means, 'paired_arm_differences': comparisons,
        'provenance': {'input_sha256': input_hashes,
                       'analysis_source_sha256': {'summarize.py': sha(Path(__file__)),
                                                  'metrics.py': sha(STUDY / 'metrics.py')}},
    }


def fmt(value, *, signed=False):
    if value is None:
        return 'NA'
    if abs(value) < 0.000000000001:
        value = 0.0
    return f'{value:+.3f}' if signed else f'{value:.3f}'


def cell(value, n, *, signed=False):
    return f'{fmt(value, signed=signed)} (n={n})'


def markdown(report):
    d = report['design']
    lines = ['# Deskriptive Rankingauswertung: zwei fiktive Personen in A/B/C', '',
             f"**{d['available_snapshots']} von 24 Messpunkten vorhanden.** Zwei synthetische Personen, "
             'je eine Sitzung in A, B und C. Pro Sitzung initiale Suche und drei Nachrichten. '
             'Die 24 geplanten Messpunkte sind keine 24 unabhängigen Teilnehmer.', '',
             'nDCG ist relativ zum gemeinsamen bewerteten Stellenpool der jeweiligen Person. '
             'Relevanz 2 und 3 zählt für Precision/RR als relevant. Pro Person wird RR@10 '
             'berichtet; der Mittelwert über Personen heißt MRR@10. **NA** bedeutet '
             'fehlender Messpunkt oder undefinierte Kennzahl. Alle Änderungen beziehen sich '
             'auf die gleiche Person und Variante bei T0. Es wurden keine zusätzlichen '
             'Modellaufrufe für diese Berechnung ausgeführt.', '',
             '## Bewertungspools', '',
             '| Person | Bewertete Stellen | Vorhandene Messpunkte | Relevanz 0 / 1 / 2 / 3 |',
             '|---|---:|---:|---|']
    for pool in report['pools']:
        counts = pool.get('grade_counts', {})
        grades = ' / '.join(str(counts.get(str(i), 0)) for i in range(4))
        lines.append(f"| {pool['source_id']} · {pool.get('name', '')} | {pool['pool_size']} | "
                     f"{pool['available_snapshots']}/12 | {grades} |")
    for source in d['source_ids']:
        rows = [r for r in report['per_persona_arm_turn'] if r['source_id'] == source]
        lines += ['', f"## {source} · {rows[0]['name']}", '',
                  'Je Zelle: Kennzahl **(Änderung gegenüber T0)**.', '',
                  '| Variante | Zeitpunkt | Stellen | nDCG@10 (ΔT0) | nDCG@5 (ΔT0) | Precision@5 (ΔT0) | RR@10 (ΔT0) |',
                  '|---|---|---:|---:|---:|---:|---:|']
        for row in rows:
            values = [f"{fmt(row['metrics'][k])} ({fmt(row['delta_from_T0'][k], signed=True)})" for k in METRICS]
            lines.append(f"| {row['arm']} | {row['snapshot']} | "
                         f"{row['ranking_count'] if row['ranking_count'] is not None else 'NA'} | "
                         + ' | '.join(values) + ' |')
    lines += ['', '## Mittelwerte je Variante und Zeitpunkt', '',
              'Die Fallzahl steht je Kennzahl dabei. Ein Mittelwert mit n=1 ist kein '
              'vollständiger Mittelwert über beide geplanten Personen.', '',
              '| Variante | Zeitpunkt | nDCG@10 | nDCG@5 | Precision@5 | MRR@10 |',
              '|---|---|---:|---:|---:|---:|']
    for row in report['arm_turn_means']:
        cells = [cell(row['metrics'][output_key(k)], row['n_by_metric'][output_key(k)]) for k in METRICS]
        lines.append(f"| {row['arm']} | {row['snapshot']} | " + ' | '.join(cells) + ' |')
    lines += ['', '## Mittlere gepaarte Veränderung gegenüber T0', '',
              'Nur Personen mit definiertem Ausgangs- und Folgewert derselben Variante gehen ein.', '',
              '| Variante | Zeitpunkt | Δ nDCG@10 | Δ nDCG@5 | Δ Precision@5 | Δ MRR@10 |',
              '|---|---|---:|---:|---:|---:|']
    for row in report['arm_turn_means']:
        if row['turn'] == 0:
            continue
        cells = [cell(row['mean_paired_delta_from_T0'][output_key(k)],
                      row['n_paired_T0_by_metric'][output_key(k)], signed=True) for k in METRICS]
        lines.append(f"| {row['arm']} | {row['snapshot']} | " + ' | '.join(cells) + ' |')
    lines += ['', '## Gepaarte Unterschiede zwischen Varianten', '',
              'B−A, C−A und C−B verwenden je Zeitpunkt dieselben Personen auf beiden Seiten. '
              'Positive Werte sprechen in diesem konkreten Vergleich für die zuerst genannte '
              'Variante. Dies sind deskriptive Unterschiede, keine Signifikanznachweise.', '',
              '| Vergleich | Zeitpunkt | Δ nDCG@10 | Δ nDCG@5 | Δ Precision@5 | Δ MRR@10 |',
              '|---|---|---:|---:|---:|---:|']
    for row in report['paired_arm_differences']:
        cells = [cell(row['metrics'][output_key(k)]['mean_paired_difference'],
                      row['metrics'][output_key(k)]['n_pairs'], signed=True) for k in METRICS]
        lines.append(f"| {row['comparison']} | {row['snapshot']} | " + ' | '.join(cells) + ' |')
    lines += ['', '## Unterschied der Veränderungen seit T0', '',
              'Verglichen wird (Variante X bei Tn − X bei T0) minus '
              '(Variante Y bei Tn − Y bei T0). Pro Person müssen alle vier Werte vorliegen.', '',
              '| Vergleich | Zeitpunkt | ΔΔ nDCG@10 | ΔΔ nDCG@5 | ΔΔ Precision@5 | ΔΔ MRR@10 |',
              '|---|---|---:|---:|---:|---:|']
    for row in report['paired_arm_differences']:
        if row['turn'] == 0:
            continue
        cells = [cell(row['metrics'][output_key(k)]['mean_difference_of_T0_changes'],
                      row['metrics'][output_key(k)]['n_T0_change_pairs'], signed=True) for k in METRICS]
        lines.append(f"| {row['comparison']} | {row['snapshot']} | " + ' | '.join(cells) + ' |')
    missing = [f"{r['case_id']}/{r['snapshot']}" for r in report['per_persona_arm_turn']
               if r['status'] != 'available']
    lines += ['', '## Fehlende Messpunkte', '',
              ', '.join(missing) if missing else 'Keine fehlenden Messpunkte.', '',
              '## Aussagegrenzen', '',
              '- Zwei konstruierte synthetische Personen; keine repräsentative Nutzerstichprobe.',
              '- Ein stochastischer Lauf je Person/Variante; keine Signifikanztests oder Konfidenzintervalle.',
              '- Codex erstellt Nutzerprofile und Relevanzurteile; keine unabhängige menschliche Referenz.',
              '- Die ideale Rangfolge stammt aus dem gepoolten Ergebnisbestand, nicht aus einer vollständigen Bewertung aller 8.537 Stellen.',
              '- Zusätzliche Informationen im Gespräch können Änderungen erklären. Ein Persönlichkeitseffekt ist damit nicht isoliert nachgewiesen.',
              '- Rankingmetriken messen keine Chatqualität, Bedienbarkeit, Zufriedenheit oder tatsächliche Einstellungschancen.', '',
              '## Nachvollziehbarkeit', '',
              'Der JSON-Bericht enthält alle Eingabeprüfsummen, vollständige Einzelwerte, '
              'verwendete Personenpaare, Fallzahlen und die Definitionen. Vor der Berechnung '
              'wurden Bewertungsabdeckung, IDs, Relevanzgrade, Dopplungen, Poolhash und '
              'Übereinstimmung des Pools mit den gespeicherten Rangfolgen geprüft.', '']
    return '\n'.join(lines)


def write_outputs(report, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    (out / 'report.md').write_text(markdown(report), encoding='utf-8')
    archive = out / 'analysis-source'
    archive.mkdir(exist_ok=True)
    for name in ('summarize.py', 'metrics.py'):
        (archive / name).write_bytes((STUDY / name).read_bytes())
    files = [out / 'report.json', out / 'report.md', archive / 'summarize.py', archive / 'metrics.py']
    (out / 'artifact-sha256.json').write_text(json.dumps(
        {path.relative_to(out).as_posix(): sha(path) for path in files}, indent=2) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--run', type=Path, default=STUDY / 'run')
    parser.add_argument('--out', type=Path, help='Defaults to <run>/analysis.')
    parser.add_argument('--check-only', action='store_true', help='Validate and calculate in memory; write no files.')
    args = parser.parse_args(argv)
    try:
        report = summarize(args.run)
        if not args.check_only:
            out = args.out or args.run / 'analysis'
            write_outputs(report, out)
            print(f'Written {out / "report.md"} and report.json')
        print(f"Validated {len(report['pools'])} persona pools; "
              f"{report['design']['available_snapshots']}/24 snapshots. No API calls.")
    except (ValidationError, ValueError, KeyError, TypeError) as error:
        print(f'Evaluation input rejected: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
