"""Separate, offline human annotation of evidence faithfulness (not ranking relevance).

No web/API calls, study database reads, or model-generated rater judgements.
Input must already be a consented research or synthetic JSONL dataset.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

SOURCE_FIELDS = ('pair_id', 'study_arm', 'profile', 'job_id', 'job_text', 'explanation')
ANNOTATION_FIELDS = ('annotation_id', 'profile', 'job_text', 'explanation', 'rater_1', 'rater_2', 'comment_1', 'comment_2')
MAPPING_FIELDS = ('annotation_id', 'pair_id', 'study_arm', 'job_id')


def sample_pairs(rows, count=60, seed=20260922):
    if not 40 <= count <= 80:
        raise ValueError('Human validation sample must contain 40–80 pairs.')
    if len({r.get('pair_id') for r in rows}) != len(rows):
        raise ValueError('pair_id must be unique.')
    groups = {arm: [] for arm in 'ABC'}
    for row in rows:
        if any(not str(row.get(key, '')).strip() for key in SOURCE_FIELDS):
            raise ValueError('Every row needs pair_id, study_arm, profile, job_id, job_text and explanation.')
        if row['study_arm'] not in groups:
            raise ValueError('study_arm must be A, B or C.')
        groups[row['study_arm']].append(row)
    rng = random.Random(seed)
    remainder_arms = rng.sample(list('ABC'), count % 3)
    chosen = []
    for arm in 'ABC':
        n = count // 3 + (arm in remainder_arms)
        if len(groups[arm]) < n:
            raise ValueError(f'Need at least {n} distinct pairs for {arm}; never fill by duplication.')
        chosen += rng.sample(sorted(groups[arm], key=lambda r: str(r['pair_id'])), n)
    rng.shuffle(chosen)
    annotations, mapping = [], []
    for index, row in enumerate(chosen, 1):
        annotation_id = f'F{index:03d}'
        annotations.append({'annotation_id': annotation_id, **{k: row[k] for k in ('profile', 'job_text', 'explanation')},
                            'rater_1': '', 'rater_2': '', 'comment_1': '', 'comment_2': ''})
        mapping.append({'annotation_id': annotation_id, **{k: row[k] for k in ('pair_id', 'study_arm', 'job_id')}})
    return annotations, mapping


def _rating(value):
    if value in (None, ''):
        return None
    if isinstance(value, bool) or str(value).strip() not in ('0', '1', '2'):
        raise ValueError('Human ratings must be 0 (not supported), 1 (partly), 2 (fully supported), or blank.')
    return int(value)


def cohens_kappa(pairs):
    n = len(pairs)
    if not n:
        return {'n': 0, 'kappa': None, 'observed_agreement': None, 'expected_agreement': None, 'status': 'no_paired_ratings'}
    left, right = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    observed = sum(a == b for a, b in pairs) / n
    expected = sum(left[k] * right[k] for k in (0, 1, 2)) / n ** 2
    return {'n': n, 'kappa': (observed - expected) / (1 - expected) if expected < 1 else None,
            'observed_agreement': observed, 'expected_agreement': expected,
            'status': 'ok' if expected < 1 else 'undefined_single_category', 'weighting': 'unweighted'}


def analyze_annotations(annotations, mapping):
    assignments = {r['annotation_id']: r for r in mapping}
    if len(assignments) != len(mapping) or len({r['annotation_id'] for r in annotations}) != len(annotations):
        raise ValueError('annotation_id must be unique in annotations and mapping.')
    if set(assignments) != {r['annotation_id'] for r in annotations}:
        raise ValueError('Annotations and mapping must contain exactly the same IDs.')
    pairs, by_arm = [], {arm: [] for arm in 'ABC'}
    missing = 0
    for row in annotations:
        arm = assignments[row['annotation_id']]['study_arm']
        if arm not in by_arm:
            raise ValueError('Invalid study arm in mapping.')
        a, b = _rating(row.get('rater_1')), _rating(row.get('rater_2'))
        if a is None or b is None:
            missing += 1
        else:
            pairs.append((a, b)); by_arm[arm].append((a, b))
    result = {'endpoint': 'explanation_evidence_faithfulness', 'total_sampled': len(annotations),
              'missing_paired_ratings': missing, 'reliability': cohens_kappa(pairs), 'by_arm': {},
              'limitations': ['Faithfulness is not usefulness, ranking relevance or causal effectiveness.',
                              'Two ratings of one pair are not two independent observations.',
                              'Arm masking reduces expectation bias but wording can reveal the arm.']}
    for arm, values in by_arm.items():
        result['by_arm'][arm] = {'n_pairs': len(values),
                                 'rater_1_counts': dict(Counter(a for a, _ in values)),
                                 'rater_2_counts': dict(Counter(b for _, b in values)),
                                 'both_fully_supported': sum(a == b == 2 for a, b in values),
                                 'disagreements': sum(a != b for a, b in values),
                                 'reliability': cohens_kappa(values)}
    return result


def _write_csv(path, fields, rows):
    # Prevent spreadsheet formula execution; preserve exact text as far as possible.
    def safe(value):
        text = str(value)
        return "'" + text if text.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else text
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter=';')
        writer.writeheader()
        writer.writerows({k: safe(row.get(k, '')) for k in fields} for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    sample = commands.add_parser('sample')
    sample.add_argument('input', type=Path)
    sample.add_argument('--dataset-kind', choices=['synthetic', 'consented_research'], required=True)
    sample.add_argument('--count', type=int, default=60)
    sample.add_argument('--seed', type=int, default=20260922)
    sample.add_argument('--output-dir', type=Path, required=True)
    analysis = commands.add_parser('analyze')
    analysis.add_argument('annotations', type=Path)
    analysis.add_argument('mapping', type=Path)
    analysis.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'sample':
        rows = [json.loads(line) for line in args.input.read_text(encoding='utf-8').splitlines() if line.strip()]
        annotations, mapping = sample_pairs(rows, args.count, args.seed)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        _write_csv(args.output_dir / 'annotations.csv', ANNOTATION_FIELDS, annotations)
        _write_csv(args.output_dir / 'arm_mapping_private.csv', MAPPING_FIELDS, mapping)
        provenance = {'dataset_kind': args.dataset_kind, 'source_sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
                      'seed': args.seed, 'sample_size': args.count, 'source_pairs': len(rows),
                      'sampling': 'random without replacement within arms, equal quotas ±1, blinded shuffled output',
                      'arm_counts': dict(Counter(r['study_arm'] for r in mapping)),
                      'warning': 'Empty rater fields: this output is not completed human validation.'}
        (args.output_dir / 'sampling.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Prepared {len(annotations)} unrated pairs in {args.output_dir}')
    else:
        def read(path):
            with path.open(encoding='utf-8-sig', newline='') as stream:
                return list(csv.DictReader(stream, delimiter=';'))
        result = analyze_annotations(read(args.annotations), read(args.mapping))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        print(f'Written {args.output}')


if __name__ == '__main__':
    main()
