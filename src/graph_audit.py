"""Structural audit of every graph instance used in the study.

The audit answers a question the colour counts alone cannot: are the synthetic
graphs structurally comparable to the real registration graph, or do they differ
in ways that limit external validity?  Reported per instance: size, density,
degree statistics, connected components, clustering, and a clique lower bound.

NetworkX is used here for components, clustering and assortativity.  It is an
analysis dependency only; neither colouring heuristic calls it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from enrollment_generator import SCENARIOS, generate_enrollment_instance
from exact_coloring import greedy_clique
from graph_generator import erdos_renyi, instance_seed
from graph_model import ConflictGraph
from real_dataset import load_real_dataset


def audit_graph(graph: ConflictGraph) -> dict[str, float | int]:
    """Structural descriptors of one graph."""
    nx_graph = nx.Graph()
    nx_graph.add_nodes_from(range(graph.n))
    nx_graph.add_edges_from(graph.edges())

    components = sorted((len(c) for c in nx.connected_components(nx_graph)), reverse=True)
    degrees = np.array(graph.degrees, dtype=float)
    # Degree assortativity is undefined for regular graphs (zero variance);
    # report 0.0 there rather than propagating a NaN into the summary.
    with np.errstate(invalid="ignore", divide="ignore"):
        assortativity = float(nx.degree_assortativity_coefficient(nx_graph))
    if not np.isfinite(assortativity):
        assortativity = 0.0
    return {
        "n": graph.n,
        "m": graph.m,
        "density": round(graph.density(), 6),
        "mean_degree": round(float(degrees.mean()), 4) if graph.n else 0.0,
        "std_degree": round(float(degrees.std(ddof=0)), 4) if graph.n else 0.0,
        "max_degree": graph.max_degree(),
        "min_degree": int(degrees.min()) if graph.n else 0,
        "isolated_vertices": graph.isolated_vertices(),
        "components": len(components),
        "largest_component": components[0] if components else 0,
        "avg_clustering": round(float(nx.average_clustering(nx_graph)), 6),
        "transitivity": round(float(nx.transitivity(nx_graph)), 6),
        "assortativity": round(assortativity, 6),
        "clique_lower_bound": len(greedy_clique(graph)),
    }


def collect_instances() -> list[tuple[str, str, int, float, int, ConflictGraph]]:
    """Every instance as ``(experiment, block, n, p, seed, graph)``."""
    rows: list[tuple[str, str, int, float, int, ConflictGraph]] = []
    for n in (20, 40, 60, 80, 100):
        for p in (0.1, 0.3, 0.5, 0.7):
            for rep in range(30):
                seed = instance_seed(n, int(round(p * 1000)), rep)
                rows.append(("A", f"n{n}_p{p:.1f}", n, p, seed, erdos_renyi(n, p, seed)))
    for index, scenario in enumerate(SCENARIOS):
        for rep in range(30):
            seed = instance_seed(7_000_000 + index, scenario.n_courses, rep)
            instance = generate_enrollment_instance(scenario, seed)
            rows.append(("B", scenario.name, instance.graph.n, float("nan"), seed, instance.graph))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    args = parser.parse_args(argv)

    records = []
    for experiment, block, n, p, seed, graph in collect_instances():
        record = audit_graph(graph)
        record.update({"experiment": experiment, "block": block, "n": n, "p": p, "seed": seed})
        records.append(record)

    real = load_real_dataset()
    real_record = audit_graph(real.graph)
    real_record.update(
        {
            "experiment": "C",
            "block": "etp_registration",
            "n": real.graph.n,
            "p": float("nan"),
            "seed": -1,
        }
    )
    records.append(real_record)

    frame = pd.DataFrame(records)
    columns = [
        "experiment",
        "block",
        "n",
        "p",
        "seed",
        "m",
        "density",
        "mean_degree",
        "std_degree",
        "max_degree",
        "min_degree",
        "isolated_vertices",
        "components",
        "largest_component",
        "avg_clustering",
        "transitivity",
        "assortativity",
        "clique_lower_bound",
    ]
    frame = frame[columns]
    args.outdir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.outdir / "graph_audit.csv", index=False)

    summary = (
        frame.groupby(["experiment", "block"], dropna=False)
        .agg(
            instances=("n", "size"),
            n=("n", "mean"),
            m=("m", "mean"),
            density=("density", "mean"),
            mean_degree=("mean_degree", "mean"),
            max_degree=("max_degree", "mean"),
            components=("components", "mean"),
            avg_clustering=("avg_clustering", "mean"),
            transitivity=("transitivity", "mean"),
            assortativity=("assortativity", "mean"),
            clique_lower_bound=("clique_lower_bound", "mean"),
        )
        .reset_index()
        .round(4)
    )
    summary.to_csv(args.outdir / "graph_audit_summary.csv", index=False)

    real_meta = real.metadata()
    (args.outdir / "real_dataset.json").write_text(
        json.dumps(real_meta, indent=2), encoding="utf-8"
    )

    print(f"audited {len(frame)} instances")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
