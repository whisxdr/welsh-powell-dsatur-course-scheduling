"""Publication-quality figures for the IEEE manuscript.

Usage
-----
    python src/visualization.py --results results --figures paper/figures

All figures are written as vector PDF (for LaTeX) plus a 300 dpi PNG preview.
Colors follow the Okabe--Ito color-blind-safe palette.  Every label is in
Indonesian to match the manuscript.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import networkx as nx
import numpy as np
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from dsatur import dsatur  # noqa: E402
from illustrative_example import example_graph  # noqa: E402
from welsh_powell import welsh_powell  # noqa: E402

WP_COLOR = "#0072B2"
DS_COLOR = "#D55E00"
SLOT_COLORS = ("#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#F0E442")
WP_LABEL = "Welsh\u2013Powell"
DS_LABEL = "DSATUR"
SCENARIO_LABELS = {
    "small_program": "program\nkecil",
    "medium_program": "program\nmenengah",
    "large_program": "program\nbesar",
}


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "legend.fontsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.linewidth": 0.6,
            "grid.linewidth": 0.4,
            "lines.linewidth": 1.1,
            "lines.markersize": 3.2,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.01,
        }
    )


def save(fig: plt.Figure, outdir: Path, name: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    fig.savefig(outdir / f"{name}.pdf")
    fig.savefig(outdir / f"{name}.png", dpi=300)
    plt.close(fig)


# ----------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------
def figure_example(outdir: Path) -> None:
    """Conflict graph, Welsh--Powell coloring and DSATUR coloring of the example."""
    graph = example_graph()
    wp = welsh_powell(graph)
    ds = dsatur(graph)

    nx_graph = nx.Graph()
    nx_graph.add_nodes_from(range(graph.n))
    nx_graph.add_edges_from(graph.edges())
    positions = nx.spring_layout(nx_graph, seed=11, k=1.1, iterations=400)

    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.05))
    titles = (
        "(a) Graf konflik",
        f"(b) {WP_LABEL}: {wp.num_colors} slot",
        f"(c) {DS_LABEL}: {ds.num_colors} slot",
    )
    colorings = (None, wp.colors, ds.colors)

    for axis, title, coloring in zip(axes, titles, colorings, strict=True):
        node_colors = (
            ["#DDDDDD"] * graph.n
            if coloring is None
            else [SLOT_COLORS[c % len(SLOT_COLORS)] for c in coloring]
        )
        nx.draw_networkx_edges(nx_graph, positions, ax=axis, width=0.7, edge_color="#555555")
        nx.draw_networkx_nodes(
            nx_graph,
            positions,
            ax=axis,
            node_size=190,
            node_color=node_colors,
            edgecolors="#222222",
            linewidths=0.7,
        )
        nx.draw_networkx_labels(
            nx_graph,
            positions,
            ax=axis,
            labels={v: f"C{v + 1}" for v in range(graph.n)},
            font_size=6,
            font_family="serif",
        )
        axis.set_title(title, pad=3)
        axis.margins(0.10)
        axis.axis("off")

    save(fig, outdir, "fig_example")


def figure_size_effects(frame: pd.DataFrame, outdir: Path) -> None:
    """Colors (top row) and run time (bottom row) against graph size, per p."""
    experiment_a = frame[frame["experiment"] == "A"].copy()
    experiment_a["wp_ms"] = 1000.0 * experiment_a["wp_time_median_s"]
    experiment_a["ds_ms"] = 1000.0 * experiment_a["ds_time_median_s"]
    probabilities = sorted(experiment_a["p"].dropna().unique())

    fig, axes = plt.subplots(2, 4, figsize=(7.1, 2.15), sharex=True)
    for column, probability in enumerate(probabilities):
        subset = experiment_a[experiment_a["p"] == probability]
        colors = subset.groupby("n")[["wp_colors", "ds_colors"]].mean()
        times = subset.groupby("n")[["wp_ms", "ds_ms"]].median()

        top = axes[0, column]
        top.plot(colors.index, colors["wp_colors"], "o-", color=WP_COLOR, label=WP_LABEL)
        top.plot(colors.index, colors["ds_colors"], "s-", color=DS_COLOR, label=DS_LABEL)
        top.set_title(f"$p = {probability:.1f}$", pad=2)
        top.grid(True, alpha=0.3)

        bottom = axes[1, column]
        bottom.plot(times.index, times["wp_ms"], "o-", color=WP_COLOR)
        bottom.plot(times.index, times["ds_ms"], "s-", color=DS_COLOR)
        bottom.set_yscale("log")
        bottom.grid(True, alpha=0.3, which="both")
        bottom.set_xlabel("$|V|$")

    axes[0, 0].set_ylabel("Rata-rata warna")
    axes[1, 0].set_ylabel("Waktu median (ms)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.05))
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save(fig, outdir, "fig_size_effects")


def figure_density_effect(frame: pd.DataFrame, outdir: Path) -> None:
    """Effect of observed density, restricted to Experiment A.

    Experiment B is reported separately because its curricula occupy a narrow,
    structurally different density range; pooling the two would confound the
    density effect with the generator.
    """
    working = frame[frame["experiment"] == "A"].copy()
    working["bin"] = pd.qcut(working["density"], q=8, duplicates="drop")

    def sem(series: pd.Series) -> float:
        return float(series.std(ddof=1) / np.sqrt(len(series))) if len(series) > 1 else 0.0

    grouped = working.groupby("bin", observed=True).agg(
        density=("density", "mean"),
        wp=("wp_colors", "mean"),
        wp_sem=("wp_colors", sem),
        ds=("ds_colors", "mean"),
        ds_sem=("ds_colors", sem),
        reduction=("reduction_pct", "mean"),
        reduction_sem=("reduction_pct", sem),
        count=("wp_colors", "size"),
    )

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.2))
    axes[0].errorbar(
        grouped["density"],
        grouped["wp"],
        yerr=1.96 * grouped["wp_sem"],
        fmt="o-",
        color=WP_COLOR,
        capsize=2,
        label=WP_LABEL,
    )
    axes[0].errorbar(
        grouped["density"],
        grouped["ds"],
        yerr=1.96 * grouped["ds_sem"],
        fmt="s-",
        color=DS_COLOR,
        capsize=2,
        label=DS_LABEL,
    )
    axes[0].set_xlabel("Kepadatan teramati $d(G)$")
    axes[0].set_ylabel("Rata-rata warna")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].errorbar(
        grouped["density"],
        grouped["reduction"],
        yerr=1.96 * grouped["reduction_sem"],
        fmt="D-",
        color="#009E73",
        capsize=2,
    )
    axes[1].axhline(0.0, color="#555555", linewidth=0.7, linestyle="--")
    axes[1].set_xlabel("Kepadatan teramati $d(G)$")
    axes[1].set_ylabel("Rata-rata $R_k$ (\\%)")
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    save(fig, outdir, "fig_density_effect")


def figure_outcomes(frame: pd.DataFrame, outdir: Path) -> None:
    """Win/tie/loss shares and the Experiment B colour counts in one row."""
    experiment_a = frame[frame["experiment"] == "A"]
    probabilities = sorted(experiment_a["p"].dropna().unique())
    experiment_b = frame[frame["experiment"] == "B"]
    scenarios = [
        s
        for s in ("small_program", "medium_program", "large_program")
        if s in set(experiment_b["scenario"])
    ]

    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.3))
    for axis, groups, labels, xlabel in (
        (
            axes[0],
            [experiment_a[experiment_a["p"] == p] for p in probabilities],
            [f"{p:.1f}" for p in probabilities],
            "Probabilitas sisi $p$",
        ),
        (
            axes[1],
            [experiment_b[experiment_b["scenario"] == s] for s in scenarios],
            [SCENARIO_LABELS[s] for s in scenarios],
            "Skenario Eksperimen B",
        ),
    ):
        counts = np.array(
            [
                [
                    (group["winner"] == "welsh_powell").sum(),
                    (group["winner"] == "tie").sum(),
                    (group["winner"] == "dsatur").sum(),
                ]
                for group in groups
            ],
            dtype=float,
        )
        shares = 100.0 * counts / counts.sum(axis=1, keepdims=True)
        positions = np.arange(len(groups))
        bottom = np.zeros(len(groups))
        for column, color, label in (
            (0, WP_COLOR, "WP menang"),
            (1, "#BBBBBB", "Seri"),
            (2, DS_COLOR, "DSATUR menang"),
        ):
            axis.bar(
                positions, shares[:, column], bottom=bottom, color=color, label=label, width=0.65
            )
            bottom += shares[:, column]
        axis.set_xticks(positions, labels, fontsize=6.5)
        axis.set_xlabel(xlabel)
        axis.set_ylim(0, 100)
        axis.grid(True, axis="y", alpha=0.3)
    axes[0].set_ylabel("Proporsi instans (\\%)")

    grouped = (
        experiment_b.groupby("scenario")[["wp_colors", "ds_colors", "density"]]
        .mean()
        .loc[scenarios]
    )
    positions = np.arange(len(scenarios))
    width = 0.36
    axes[2].bar(positions - width / 2, grouped["wp_colors"], width, color=WP_COLOR)
    axes[2].bar(positions + width / 2, grouped["ds_colors"], width, color=DS_COLOR)
    axes[2].set_xticks(
        positions,
        [
            f"{SCENARIO_LABELS[s]}\n$d={density:.2f}$"
            for s, density in zip(scenarios, grouped["density"], strict=True)
        ],
        fontsize=6.5,
    )
    axes[2].set_ylabel("Rata-rata warna")
    axes[2].set_xlabel("Skenario Eksperimen B")
    axes[2].grid(True, axis="y", alpha=0.3)
    axes[2].set_ylim(0, max(grouped["wp_colors"].max(), grouped["ds_colors"].max()) * 1.2)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.06))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, outdir, "fig_outcomes")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--figures", type=Path, default=Path("paper/figures"))
    args = parser.parse_args(argv)

    style()
    frame = pd.read_csv(args.results / "raw_results.csv")

    figure_example(args.figures)
    figure_size_effects(frame, args.figures)
    figure_density_effect(frame, args.figures)
    figure_outcomes(frame, args.figures)
    print(f"figures written to {args.figures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
