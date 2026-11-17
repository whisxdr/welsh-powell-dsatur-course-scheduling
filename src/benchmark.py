"""Paired benchmark driver for Experiment A and Experiment B.

Usage
-----
    python src/benchmark.py                 # full study (690 instances)
    python src/benchmark.py --quick         # smoke test on a reduced grid
    python src/benchmark.py --repeats 9     # more timing repetitions

Outputs (under ``results/`` unless ``--outdir`` is given)
--------------------------------------------------------
``raw_results.csv``        one row per (instance, algorithm)
``instance_summary.csv``   one row per instance with both algorithms side by side
``summary_colors.csv``     descriptive statistics of color counts
``summary_runtime.csv``    descriptive statistics of runtimes
``win_tie_loss.csv``       win/tie/loss frequencies
``density_effect.csv``     color counts binned by observed density
``statistics.json``        paired hypothesis tests and bootstrap intervals
``environment.json``       hardware, OS and dependency versions actually observed
``run_manifest.json``      configuration of the run and integrity hashes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics as pystats
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from dsatur import dsatur
from enrollment_generator import (
    REPETITIONS_PER_SCENARIO,
    SCENARIOS,
    generate_enrollment_instance,
)
from graph_generator import (
    RandomGraphConfig,
    erdos_renyi,
    experiment_a_configs,
    instance_seed,
)
from graph_model import ConflictGraph, validate_result
from welsh_powell import welsh_powell

ALGORITHMS = ("welsh_powell", "dsatur")


# ----------------------------------------------------------------------
# Environment capture
# ----------------------------------------------------------------------
def environment_info() -> dict[str, object]:
    """Record only values that are actually observable in this process."""
    import matplotlib
    import networkx
    import scipy

    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor_identifier": os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "cpu_count_logical": os.cpu_count(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "networkx_version": networkx.__version__,
        "scipy_version": scipy.__version__,
        "matplotlib_version": matplotlib.__version__,
        "timer": "time.perf_counter (monotonic, nanosecond resolution)",
    }


def graph_digest(graph: ConflictGraph) -> str:
    """SHA-256 over the canonical edge list, for reproducibility checks."""
    payload = ";".join(f"{u}-{v}" for u, v in graph.edges()).encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:16]


# ----------------------------------------------------------------------
# Single-instance measurement
# ----------------------------------------------------------------------
def measure_instance(
    graph: ConflictGraph, repeats: int, timer=time.perf_counter
) -> dict[str, object]:
    """Run both heuristics on the same graph and return paired measurements."""
    wp_times: list[float] = []
    ds_times: list[float] = []
    wp_result = None
    ds_result = None
    for _ in range(repeats):
        wp_result = welsh_powell(graph, timer)
        wp_times.append(wp_result.elapsed_seconds)
        ds_result = dsatur(graph, timer)
        ds_times.append(ds_result.elapsed_seconds)

    assert wp_result is not None
    assert ds_result is not None
    validate_result(graph, wp_result)
    validate_result(graph, ds_result)

    wp_median = pystats.median(wp_times)
    ds_median = pystats.median(ds_times)
    reduction = (
        100.0 * (wp_result.num_colors - ds_result.num_colors) / wp_result.num_colors
        if wp_result.num_colors
        else 0.0
    )
    if ds_result.num_colors < wp_result.num_colors:
        winner = "dsatur"
    elif ds_result.num_colors > wp_result.num_colors:
        winner = "welsh_powell"
    else:
        winner = "tie"

    return {
        "n": graph.n,
        "m": graph.m,
        "density": graph.density(),
        "max_degree": graph.max_degree(),
        "isolated_vertices": graph.isolated_vertices(),
        "wp_colors": wp_result.num_colors,
        "ds_colors": ds_result.num_colors,
        "wp_time_median_s": wp_median,
        "ds_time_median_s": ds_median,
        "wp_time_min_s": min(wp_times),
        "ds_time_min_s": min(ds_times),
        "wp_time_mean_s": pystats.fmean(wp_times),
        "ds_time_mean_s": pystats.fmean(ds_times),
        "wp_conflicts": graph.count_conflicts(wp_result.colors),
        "ds_conflicts": graph.count_conflicts(ds_result.colors),
        "reduction_pct": reduction,
        "winner": winner,
        "repeats": repeats,
    }


# ----------------------------------------------------------------------
# Experiment drivers
# ----------------------------------------------------------------------
def run_experiment_a(
    configs: list[RandomGraphConfig], repeats: int
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    instances: list[dict[str, object]] = []
    for config in configs:
        for rep in range(config.repetitions):
            seed = instance_seed(config.n, int(round(config.p * 1000)), rep)
            t0 = time.perf_counter()
            graph = erdos_renyi(config.n, config.p, seed)
            generation_s = time.perf_counter() - t0
            record = measure_instance(graph, repeats)
            record.update(
                {
                    "experiment": "A",
                    "scenario": config.label,
                    "n": config.n,
                    "p": config.p,
                    "seed": seed,
                    "generation_s": generation_s,
                    "digest": graph_digest(graph),
                }
            )
            rows.append(record)
            instances.append(
                {
                    "experiment": "A",
                    "scenario": config.label,
                    "n": config.n,
                    "p": config.p,
                    "seed": seed,
                    "m": graph.m,
                    "density": round(graph.density(), 6),
                    "digest": record["digest"],
                }
            )
    return rows, instances


def run_experiment_b(
    scenarios: tuple, repetitions: int, repeats: int
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    instances: list[dict[str, object]] = []
    for index, scenario in enumerate(scenarios):
        for rep in range(repetitions):
            seed = instance_seed(7_000_000 + index, scenario.n_courses, rep)
            t0 = time.perf_counter()
            instance = generate_enrollment_instance(scenario, seed)
            generation_s = time.perf_counter() - t0
            record = measure_instance(instance.graph, repeats)
            record.update(
                {
                    "experiment": "B",
                    "scenario": instance.scenario.name,
                    "n": instance.graph.n,
                    "p": float("nan"),
                    "seed": instance.seed,
                    "generation_s": generation_s,
                    "digest": graph_digest(instance.graph),
                }
            )
            rows.append(record)
            meta = instance.metadata()
            meta["experiment"] = "B"
            meta["n"] = instance.graph.n
            meta["digest"] = record["digest"]
            instances.append(meta)
    return rows, instances


# ----------------------------------------------------------------------
# Summaries
# ----------------------------------------------------------------------
def summarise_colors(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby(["experiment", "scenario", "n"], dropna=False)
    out = grouped.agg(
        instances=("wp_colors", "size"),
        wp_mean=("wp_colors", "mean"),
        wp_std=("wp_colors", "std"),
        wp_min=("wp_colors", "min"),
        wp_max=("wp_colors", "max"),
        ds_mean=("ds_colors", "mean"),
        ds_std=("ds_colors", "std"),
        ds_min=("ds_colors", "min"),
        ds_max=("ds_colors", "max"),
        mean_density=("density", "mean"),
        mean_reduction_pct=("reduction_pct", "mean"),
    ).reset_index()
    return out.round(4)


def summarise_runtime(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby(["experiment", "scenario", "n"], dropna=False)
    out = grouped.agg(
        instances=("wp_time_median_s", "size"),
        wp_median_ms=("wp_time_median_s", lambda s: 1000.0 * s.median()),
        ds_median_ms=("ds_time_median_s", lambda s: 1000.0 * s.median()),
        wp_mean_ms=("wp_time_median_s", lambda s: 1000.0 * s.mean()),
        ds_mean_ms=("ds_time_median_s", lambda s: 1000.0 * s.mean()),
        wp_p95_ms=("wp_time_median_s", lambda s: 1000.0 * s.quantile(0.95)),
        ds_p95_ms=("ds_time_median_s", lambda s: 1000.0 * s.quantile(0.95)),
    ).reset_index()
    return out.round(4)


def summarise_win_tie_loss(frame: pd.DataFrame) -> pd.DataFrame:
    counts = (
        frame.groupby(["experiment", "scenario", "winner"], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for column in ("dsatur", "tie", "welsh_powell"):
        if column not in counts:
            counts[column] = 0
    counts = counts.rename(
        columns={"dsatur": "dsatur_wins", "tie": "ties", "welsh_powell": "wp_wins"}
    )
    counts["instances"] = counts[["dsatur_wins", "ties", "wp_wins"]].sum(axis=1)
    return counts[["experiment", "scenario", "instances", "dsatur_wins", "ties", "wp_wins"]]


def summarise_density_effect(frame: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    working = frame.copy()
    working["density_bin"] = pd.cut(working["density"], bins=bins, include_lowest=True)
    out = (
        working.groupby("density_bin", observed=True)
        .agg(
            instances=("wp_colors", "size"),
            mean_density=("density", "mean"),
            wp_mean_colors=("wp_colors", "mean"),
            ds_mean_colors=("ds_colors", "mean"),
            mean_reduction_pct=("reduction_pct", "mean"),
        )
        .reset_index()
    )
    out["density_bin"] = out["density_bin"].astype(str)
    return out.round(4)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def warm_up() -> None:
    """Touch NumPy and both heuristics once so first-call overhead is excluded."""
    warm = erdos_renyi(16, 0.4, 12345)
    welsh_powell(warm)
    dsatur(warm)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=7, help="timing repetitions per algorithm")
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    parser.add_argument("--datadir", type=Path, default=Path("data"))
    parser.add_argument("--quick", action="store_true", help="reduced grid for smoke testing")
    args = parser.parse_args(argv)
    warm_up()

    if args.quick:
        configs = experiment_a_configs(sizes=(20, 40), probabilities=(0.1, 0.5), repetitions=3)
        b_repetitions = 2
    else:
        configs = experiment_a_configs()
        b_repetitions = REPETITIONS_PER_SCENARIO

    args.outdir.mkdir(parents=True, exist_ok=True)
    args.datadir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    rows_a, meta_a = run_experiment_a(configs, args.repeats)
    rows_b, meta_b = run_experiment_b(SCENARIOS, b_repetitions, args.repeats)
    elapsed = time.perf_counter() - started

    frame = pd.DataFrame(rows_a + rows_b)
    frame.to_csv(args.outdir / "raw_results.csv", index=False)

    instance_frame = pd.DataFrame(meta_a + meta_b)
    instance_frame.to_csv(args.datadir / "instances_metadata.csv", index=False)

    summarise_colors(frame).to_csv(args.outdir / "summary_colors.csv", index=False)
    summarise_runtime(frame).to_csv(args.outdir / "summary_runtime.csv", index=False)
    summarise_win_tie_loss(frame).to_csv(args.outdir / "win_tie_loss.csv", index=False)
    summarise_density_effect(frame).to_csv(args.outdir / "density_effect.csv", index=False)

    from analysis import paired_analysis

    stats = paired_analysis(frame)
    (args.outdir / "statistics.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")

    environment = environment_info()
    (args.outdir / "environment.json").write_text(
        json.dumps(environment, indent=2), encoding="utf-8"
    )

    manifest = {
        "experiment_a_configs": [asdict(c) for c in configs],
        "experiment_b_scenarios": [asdict(s) for s in SCENARIOS],
        "experiment_b_repetitions": b_repetitions,
        "timing_repeats": args.repeats,
        "instances_total": int(len(frame)),
        "algorithm_instance_comparisons": int(len(frame) * len(ALGORITHMS)),
        "wall_clock_seconds": round(elapsed, 3),
        "quick_mode": bool(args.quick),
        "python": sys.version,
    }
    (args.outdir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"instances: {len(frame)}")
    print(f"algorithm-instance comparisons: {len(frame) * len(ALGORITHMS)}")
    print(f"wall clock: {elapsed:.2f} s")
    print(frame["winner"].value_counts().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
