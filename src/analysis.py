"""Paired statistical analysis of the benchmark results.

Design
------
The experiment is paired: both heuristics process exactly the same graph
instance, so every comparison is a within-instance pair.  The Wilcoxon
signed-rank test (distribution-free, paired) is used instead of an
independent-samples test, and bootstrap confidence intervals are reported for
the mean paired difference.

Multiplicity
------------
Two outcomes are **prespecified as primary**: the number of colours and the
runtime, both on the full paired sample.  Every subgroup analysis (by edge
probability, by graph size, by enrolment scenario) is **secondary and
exploratory**; within each family the p-values are adjusted with the Holm
step-down procedure and reported alongside the unadjusted values.

Unit of analysis
----------------
The unit is the graph instance, never the timing trial.  The seven repeated
timings per instance are reduced to a median *before* any test, so repeated
measurements cannot inflate the sample size (no pseudoreplication).

Assumptions stated in the manuscript:
* instances are independent draws from their generators;
* the paired differences are symmetrically distributed about their median
  (required by the signed-rank test);
* runtimes are summarised by the median of repeated timings, which reduces the
  influence of scheduler noise but does not remove it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20240517
ALPHA = 0.05


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjusted p-values, with monotonicity enforced."""
    if not pvalues:
        return {}
    ordered = sorted(pvalues.items(), key=lambda item: item[1])
    total = len(ordered)
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (key, value) in enumerate(ordered):
        candidate = min(1.0, (total - rank) * value)
        running = max(running, candidate)
        adjusted[key] = running
    return adjusted


def _rank_biserial(differences: np.ndarray) -> float:
    """Matched-pairs rank-biserial correlation as an effect size in [-1, 1]."""
    nonzero = differences[differences != 0]
    if nonzero.size == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(nonzero))
    positive = ranks[nonzero > 0].sum()
    negative = ranks[nonzero < 0].sum()
    total = positive + negative
    return float((positive - negative) / total) if total else 0.0


def _bootstrap_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    if values.size == 0:
        return (float("nan"), float("nan"))
    draws = rng.choice(values, size=(BOOTSTRAP_RESAMPLES, values.size), replace=True)
    means = draws.mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def paired_block(frame: pd.DataFrame, rng: np.random.Generator) -> dict[str, object]:
    """Summarise one paired block (colors and runtimes)."""
    color_diff = (frame["ds_colors"] - frame["wp_colors"]).to_numpy(dtype=float)
    time_diff = (frame["ds_time_median_s"] - frame["wp_time_median_s"]).to_numpy(dtype=float)

    block: dict[str, object] = {
        "instances": int(len(frame)),
        "wp_mean_colors": float(frame["wp_colors"].mean()),
        "ds_mean_colors": float(frame["ds_colors"].mean()),
        "mean_color_difference_ds_minus_wp": float(color_diff.mean()),
        "median_color_difference": float(np.median(color_diff)),
        "mean_reduction_pct": float(frame["reduction_pct"].mean()),
        "dsatur_wins": int((frame["winner"] == "dsatur").sum()),
        "ties": int((frame["winner"] == "tie").sum()),
        "wp_wins": int((frame["winner"] == "welsh_powell").sum()),
        "wp_median_runtime_ms": float(1000.0 * frame["wp_time_median_s"].median()),
        "ds_median_runtime_ms": float(1000.0 * frame["ds_time_median_s"].median()),
        "runtime_ratio_ds_over_wp": float(
            frame["ds_time_median_s"].median() / frame["wp_time_median_s"].median()
        ),
    }

    if np.any(color_diff != 0):
        result = stats.wilcoxon(
            frame["wp_colors"], frame["ds_colors"], zero_method="wilcox", alternative="two-sided"
        )
        block["colors_wilcoxon"] = {
            "statistic": float(result.statistic),
            "p_value": float(result.pvalue),
            "rank_biserial": _rank_biserial(color_diff),
        }
    else:
        block["colors_wilcoxon"] = {
            "statistic": 0.0,
            "p_value": 1.0,
            "rank_biserial": 0.0,
            "note": "all paired differences are zero",
        }

    if np.any(time_diff != 0):
        result = stats.wilcoxon(
            frame["wp_time_median_s"],
            frame["ds_time_median_s"],
            zero_method="wilcox",
            alternative="two-sided",
        )
        block["runtime_wilcoxon"] = {
            "statistic": float(result.statistic),
            "p_value": float(result.pvalue),
            "rank_biserial": _rank_biserial(time_diff),
        }
    else:
        block["runtime_wilcoxon"] = {
            "statistic": 0.0,
            "p_value": 1.0,
            "rank_biserial": 0.0,
            "note": "all paired differences are zero",
        }

    low, high = _bootstrap_ci(color_diff, rng)
    block["color_difference_bootstrap_95ci"] = [low, high]
    low_t, high_t = _bootstrap_ci(time_diff, rng)
    block["runtime_difference_bootstrap_95ci_s"] = [low_t, high_t]
    return block


def paired_analysis(frame: pd.DataFrame) -> dict[str, object]:
    """Full paired analysis: primary outcomes plus Holm-adjusted subgroups."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    out: dict[str, object] = {
        "design": "paired within-instance comparison",
        "test": "two-sided Wilcoxon signed-rank",
        "alpha": ALPHA,
        "primary_outcomes": ["colors", "runtime"],
        "secondary_status": "exploratory, Holm-adjusted within each family",
        "unit_of_analysis": "graph instance (timing repeats reduced to a median first)",
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "overall": paired_block(frame, rng),
    }

    experiment_a = frame[frame["experiment"] == "A"]
    by_p: dict[str, object] = {}
    for p, group in experiment_a.groupby("p"):
        by_p[f"{p:.1f}"] = paired_block(group, rng)
    out["by_probability"] = by_p

    experiment_b = frame[frame["experiment"] == "B"]
    by_scenario: dict[str, object] = {}
    for scenario, group in experiment_b.groupby("scenario"):
        by_scenario[str(scenario)] = paired_block(group, rng)
    out["by_scenario"] = by_scenario

    by_size: dict[str, object] = {}
    for n, group in experiment_a.groupby("n"):
        by_size[str(int(n))] = paired_block(group, rng)
    out["by_size"] = by_size

    # Holm adjustment within each secondary family (colours only; runtime is
    # reported descriptively for subgroups).
    for family in ("by_probability", "by_size", "by_scenario"):
        blocks: dict[str, dict] = out[family]  # type: ignore[assignment]
        raw = {key: block["colors_wilcoxon"]["p_value"] for key, block in blocks.items()}
        adjusted = holm_adjust(raw)
        for key, block in blocks.items():
            block["colors_wilcoxon"]["holm_adjusted_p"] = adjusted[key]
            block["colors_wilcoxon"]["significant_holm"] = adjusted[key] < ALPHA
    return out
