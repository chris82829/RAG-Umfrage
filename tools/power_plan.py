#!/usr/bin/env python3
"""Reproduce the DIANA planning sensitivity for 200 evaluable participants.

Run from the project directory: .venv/bin/python tools/power_plan.py
Requires SciPy, already present in the project's scientific Python environment.
No study data or network services are read or changed.
"""

import json
import math

import scipy
from scipy.optimize import brentq
from scipy.stats import nct, t


def two_sample_power(d: float, n_a: int, n_b: int, alpha: float = 0.05) -> float:
    """Two-sided, independent equal-variance t-test under a normal alternative.

    d is the population mean difference divided by the common population SD.
    This is a planning model, not a guarantee for ordinal or selected survey data.
    """
    if n_a < 2 or n_b < 2 or not 0 < alpha < 1 or not math.isfinite(d):
        raise ValueError("Use at least two observations per arm and 0 < alpha < 1.")
    df = n_a + n_b - 2
    critical = t.ppf(1 - alpha / 2, df)
    noncentrality = d / math.sqrt(1 / n_a + 1 / n_b)
    result = float(nct.sf(critical, df, noncentrality) + nct.cdf(-critical, df, noncentrality))
    if not math.isfinite(result):
        raise ArithmeticError("The noncentral t calculation was not finite.")
    return result


def main() -> None:
    n_a = n_b = 100
    alpha = 0.05
    # A bounded interval avoids unnecessarily extreme noncentralities.
    detectable = {
        str(target): brentq(
            lambda d: two_sample_power(d, n_a, n_b, alpha) - target,
            0.0001,
            0.9,
        )
        for target in (0.8, 0.9)
    }
    result = {
        "method": "Two-sided independent equal-variance t-test; noncentral t power",
        "scipy_version": scipy.__version__,
        "n_a": n_a,
        "n_b": n_b,
        "n_total_evaluable": n_a + n_b,
        "alpha": alpha,
        "power_by_cohens_d": {
            str(d): two_sample_power(d, n_a, n_b, alpha) for d in (0.2, 0.3, 0.4, 0.5)
        },
        "detectable_cohens_d_by_target_power": detectable,
        "assumed_loss_fraction": 0.2,
        "planned_starts_under_loss_assumption": math.ceil((n_a + n_b) / (1 - 0.2)),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
