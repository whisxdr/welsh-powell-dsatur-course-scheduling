"""Case study on the one real-world registration instance.

A single instance cannot support a hypothesis test, so this script reports
descriptive measurements only: colour counts, runtimes, and certified bounds on
the chromatic number.  The bounds are stated as bounds; no optimality claim is
made unless the clique lower bound meets the best colour count.

    python src/real_case_study.py
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from dsatur import dsatur
from exact_coloring import greedy_clique
from graph_audit import audit_graph
from graph_model import validate_result
from real_dataset import load_real_dataset
from welsh_powell import welsh_powell

REPEATS = 7


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    parser.add_argument("--repeats", type=int, default=REPEATS)
    args = parser.parse_args(argv)

    dataset = load_real_dataset()
    graph = dataset.graph

    wp_times: list[float] = []
    ds_times: list[float] = []
    wp = ds = None
    for _ in range(args.repeats):
        wp = welsh_powell(graph)
        wp_times.append(wp.elapsed_seconds)
        ds = dsatur(graph)
        ds_times.append(ds.elapsed_seconds)

    assert wp is not None
    assert ds is not None
    validate_result(graph, wp)
    validate_result(graph, ds)

    clique = greedy_clique(graph)
    lower = len(clique)
    upper = min(wp.num_colors, ds.num_colors)

    payload = {
        "dataset": dataset.metadata(),
        "structure": audit_graph(graph),
        "k_wp": wp.num_colors,
        "k_ds": ds.num_colors,
        "wp_time_median_ms": round(1000.0 * statistics.median(wp_times), 4),
        "ds_time_median_ms": round(1000.0 * statistics.median(ds_times), 4),
        "runtime_ratio_ds_over_wp": round(
            statistics.median(ds_times) / statistics.median(wp_times), 4
        ),
        "conflicts_wp": graph.count_conflicts(wp.colors),
        "conflicts_ds": graph.count_conflicts(ds.colors),
        "clique_lower_bound": lower,
        "chromatic_interval": [lower, upper],
        "chromatic_number_proven": lower == upper,
        "repeats": args.repeats,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "real_case_study.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
