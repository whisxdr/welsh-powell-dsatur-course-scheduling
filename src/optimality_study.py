"""Exact optimality gaps on the subset of instances where chi(G) is provable.

Only instances whose chromatic number can be certified by the branch-and-bound
search are included.  For every other instance the manuscript reports bounds,
never a gap, because a gap against an unknown optimum would be meaningless.

Coverage is chosen empirically: cells are included when the exact search
finishes reliably within the time limit.  Dense graphs with |V| >= 80 remain
out of reach and are reported as unproven rather than guessed.

    python src/optimality_study.py            # full study (~7 min)
    python src/optimality_study.py --quick    # |V| in {20, 40} only

Writes ``results/optimality.csv`` (per instance) and ``results/optimality.json``
(summary by block).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from dsatur import dsatur
from enrollment_generator import SCENARIOS, generate_enrollment_instance
from exact_coloring import exact_chromatic
from graph_generator import erdos_renyi, instance_seed
from welsh_powell import welsh_powell

#: (|V|, p) cells of Experiment A that the exact search can certify.
EXACT_CELLS: tuple[tuple[int, float], ...] = (
    (20, 0.1),
    (20, 0.3),
    (20, 0.5),
    (20, 0.7),
    (40, 0.1),
    (40, 0.3),
    (40, 0.5),
    (40, 0.7),
    (60, 0.1),
    (60, 0.3),
    (60, 0.5),
    (80, 0.1),
)
QUICK_CELLS: tuple[tuple[int, float], ...] = tuple(cell for cell in EXACT_CELLS if cell[0] <= 40)
TIME_LIMIT_S = 60.0


def instances(cells: tuple[tuple[int, float], ...]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for n, p in cells:
        for rep in range(30):
            seed = instance_seed(n, int(round(p * 1000)), rep)
            rows.append(
                {
                    "experiment": "A",
                    "block": f"n{n}_p{p:.1f}",
                    "n": n,
                    "p": p,
                    "seed": seed,
                    "graph": erdos_renyi(n, p, seed),
                }
            )
    for index, scenario in enumerate(SCENARIOS):
        for rep in range(30):
            seed = instance_seed(7_000_000 + index, scenario.n_courses, rep)
            instance = generate_enrollment_instance(scenario, seed)
            rows.append(
                {
                    "experiment": "B",
                    "block": scenario.name,
                    "n": instance.graph.n,
                    "p": float("nan"),
                    "seed": seed,
                    "graph": instance.graph,
                }
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    parser.add_argument("--time-limit", type=float, default=TIME_LIMIT_S)
    parser.add_argument("--quick", action="store_true", help="only |V| in {20, 40}")
    args = parser.parse_args(argv)

    cells = QUICK_CELLS if args.quick else EXACT_CELLS
    started = time.perf_counter()
    records: list[dict[str, object]] = []
    for item in instances(cells):
        graph = item["graph"]
        wp = welsh_powell(graph)
        ds = dsatur(graph)
        exact = exact_chromatic(graph, time_limit_s=args.time_limit)
        record = {
            "experiment": item["experiment"],
            "block": item["block"],
            "n": item["n"],
            "p": item["p"],
            "seed": item["seed"],
            "k_wp": wp.num_colors,
            "k_ds": ds.num_colors,
            "chi": exact.chromatic_number,
            "proven": exact.proven,
            "lower_bound": exact.lower_bound,
            "upper_bound": exact.upper_bound,
            "nodes": exact.nodes,
            "exact_seconds": exact.elapsed_seconds,
        }
        if exact.proven and exact.chromatic_number:
            chi = exact.chromatic_number
            record["gap_wp_pct"] = 100.0 * (wp.num_colors - chi) / chi
            record["gap_ds_pct"] = 100.0 * (ds.num_colors - chi) / chi
            record["wp_optimal"] = wp.num_colors == chi
            record["ds_optimal"] = ds.num_colors == chi
        else:
            record["gap_wp_pct"] = float("nan")
            record["gap_ds_pct"] = float("nan")
            record["wp_optimal"] = None
            record["ds_optimal"] = None
        records.append(record)

    frame = pd.DataFrame(records)
    args.outdir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.outdir / "optimality.csv", index=False)

    proven = frame[frame["proven"]]
    summary = (
        proven.groupby(["experiment", "block"], dropna=False)
        .agg(
            instances=("chi", "size"),
            mean_chi=("chi", "mean"),
            mean_gap_wp=("gap_wp_pct", "mean"),
            mean_gap_ds=("gap_ds_pct", "mean"),
            max_gap_wp=("gap_wp_pct", "max"),
            max_gap_ds=("gap_ds_pct", "max"),
            wp_optimal_share=("wp_optimal", "mean"),
            ds_optimal_share=("ds_optimal", "mean"),
        )
        .reset_index()
        .round(4)
    )
    summary.to_csv(args.outdir / "optimality_summary.csv", index=False)

    attempted = frame.groupby(["experiment", "block"], dropna=False).size().rename("attempted")
    summary = summary.merge(attempted.reset_index(), on=["experiment", "block"], how="left")

    overall = {
        "instances_attempted": int(len(frame)),
        "instances_proven": int(len(proven)),
        "share_proven": round(len(proven) / len(frame), 4) if len(frame) else 0.0,
        "share_of_benchmark": round(len(proven) / 690, 4),
        "mean_gap_wp_pct": round(float(proven["gap_wp_pct"].mean()), 4),
        "mean_gap_ds_pct": round(float(proven["gap_ds_pct"].mean()), 4),
        "max_gap_wp_pct": round(float(proven["gap_wp_pct"].max()), 4),
        "max_gap_ds_pct": round(float(proven["gap_ds_pct"].max()), 4),
        "wp_optimal_share": round(float(proven["wp_optimal"].mean()), 4),
        "ds_optimal_share": round(float(proven["ds_optimal"].mean()), 4),
        "time_limit_s": args.time_limit,
        "exact_cells": [f"n{n}_p{p:.1f}" for n, p in cells],
        "wall_clock_seconds": round(time.perf_counter() - started, 1),
    }
    payload = {
        "overall": overall,
        "by_block": summary.to_dict(orient="records"),
    }
    (args.outdir / "optimality.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(overall, indent=2))
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
