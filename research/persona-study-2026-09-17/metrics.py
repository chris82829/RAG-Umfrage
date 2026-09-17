"""Offline retrieval metrics with explicit judgment and sampling assumptions.

No production dependencies or API calls. Relevance grades are numeric 0..3;
binary relevance defaults to grade >= 2. Unknown documents raise by default:
pass ``unjudged='zero'`` only when the evaluation protocol explicitly permits
that convention. This is not a substitute for comprehensive recall judgments.

Rankings are document IDs, highest rank first, without duplicates. Precision@k
uses k slots, so an incomplete result list does not inflate precision. nDCG uses
exponential gain (2**grade - 1) and log2(rank + 1) discount. Undefined metrics
are None, never NaN. A grade-1-only query has valid nDCG, zero precision/RR and
undefined recall because it has no grade >= 2 positive. Known nonempty all-zero
qrels likewise yield zero precision/RR; wholly empty qrels yield None to mark
that no judgment universe is available (including empty hard-filter controls).
Bootstrap units are profiles;
repeated runs within each profile are averaged before sampling profiles.
"""
from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping, Sequence
import math
import random
import statistics
from typing import Any

DocumentId = Hashable


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f'{name} must be a finite number, not a boolean.')
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f'{name} must be a finite number.') from error
    if not math.isfinite(numeric):
        raise ValueError(f'{name} must be a finite number.')
    return numeric


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f'{name} must be a positive integer.')
    return value


def _unique_ranking(ranking: Sequence[DocumentId]) -> list[DocumentId]:
    items = list(ranking)
    if len(items) != len(set(items)):
        raise ValueError('A ranking must not contain duplicate document IDs.')
    return items


def _judgments(qrels: Mapping[DocumentId, float]) -> dict[DocumentId, float]:
    values = {identifier: _finite(grade, 'Relevance grade') for identifier, grade in qrels.items()}
    if any(not 0 <= grade <= 3 for grade in values.values()):
        raise ValueError('Relevance grades must be between 0 and 3.')
    return values


def _inputs(ranking, qrels, k, unjudged):
    _positive_integer(k, 'k')
    if unjudged not in ('error', 'zero'):
        raise ValueError("unjudged must be 'error' or 'zero'.")
    documents = _unique_ranking(ranking)[:k]
    judgments = _judgments(qrels)
    if unjudged == 'error' and any(identifier not in judgments for identifier in documents):
        raise ValueError('The evaluated ranking contains unjudged documents; extend qrels or explicitly choose a policy.')
    return documents, judgments


def _threshold(value):
    threshold = _finite(value, 'Relevance threshold')
    if not 0 < threshold <= 3:
        raise ValueError('Relevance threshold must be greater than 0 and at most 3.')
    return threshold


def ndcg_at_k(ranking: Sequence[DocumentId], qrels: Mapping[DocumentId, float], k: int,
              *, unjudged: str = 'error') -> float | None:
    """Graded nDCG, relative to the best k documents in *all supplied* qrels."""
    documents, judgments = _inputs(ranking, qrels, k, unjudged)

    def dcg(grades):
        return sum((2.0 ** grade - 1.0) / math.log2(rank + 2) for rank, grade in enumerate(grades))

    ideal = dcg(sorted(judgments.values(), reverse=True)[:k])
    if not ideal:
        return None
    return dcg(judgments.get(identifier, 0.0) for identifier in documents) / ideal


def precision_at_k(ranking: Sequence[DocumentId], qrels: Mapping[DocumentId, float], k: int,
                   *, relevant_threshold: float = 2, unjudged: str = 'error') -> float | None:
    """Hits/k, including 0 for judged negative queries; None for empty qrels."""
    documents, judgments = _inputs(ranking, qrels, k, unjudged)
    threshold = _threshold(relevant_threshold)
    if not judgments:
        return None
    return sum(judgments.get(identifier, 0.0) >= threshold for identifier in documents) / k


def recall_at_k(ranking: Sequence[DocumentId], qrels: Mapping[DocumentId, float], k: int,
                *, relevant_threshold: float = 2, unjudged: str = 'error') -> float | None:
    """Recall among supplied judgments, not necessarily corpus-wide true recall."""
    documents, judgments = _inputs(ranking, qrels, k, unjudged)
    threshold = _threshold(relevant_threshold)
    positives = sum(grade >= threshold for grade in judgments.values())
    if not positives:
        return None
    return sum(judgments.get(identifier, 0.0) >= threshold for identifier in documents) / positives


def mrr_at_k(ranking: Sequence[DocumentId], qrels: Mapping[DocumentId, float], k: int,
             *, relevant_threshold: float = 2, unjudged: str = 'error') -> float | None:
    """Single-query RR (0 if no hit), averaged for MRR; None for empty qrels."""
    documents, judgments = _inputs(ranking, qrels, k, unjudged)
    threshold = _threshold(relevant_threshold)
    if not judgments:
        return None
    return next((1.0 / rank for rank, identifier in enumerate(documents, 1)
                 if judgments.get(identifier, 0.0) >= threshold), 0.0)

