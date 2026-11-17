"""Verify that every headline number in the manuscript matches the frozen results.

This is the final integrity gate.  It reads **only** ``results/frozen/<version>/``
— never freshly generated measurements — so a later benchmark run cannot silently
change what the manuscript is checked against.  The frozen manifest is verified
first; a digest mismatch aborts the check.

    python src/verify_claims.py
    python src/verify_claims.py --version v1
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from dsatur import dsatur
from freeze_results import verify as verify_frozen
from illustrative_example import ENROLMENTS, N_COURSES, example_graph
from welsh_powell import welsh_powell

ROOT = Path(__file__).resolve().parents[1]


def fmt_p(value: float) -> str:
    """Same formatting rule as ``make_tables.fmt_p``."""
    if value >= 0.001:
        return f"{value:.3f}"
    exponent = int(f"{value:e}".split("e")[1])
    mantissa = value / 10**exponent
    return f"${mantissa:.1f}\\times10^{{{exponent}}}$"


def collected_test_count() -> int:
    """Number of tests pytest would collect, read from a real collection run."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    match = re.search(r"(\d+)\s+tests?\s+collected", proc.stdout)
    if match:
        return int(match.group(1))
    per_file = re.findall(r"^tests[/\\].*:\s*(\d+)\s*$", proc.stdout, flags=re.MULTILINE)
    if per_file:
        return sum(int(count) for count in per_file)
    raise RuntimeError(f"could not parse pytest collection output:\n{proc.stdout[-500:]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v2")
    args = parser.parse_args(argv)

    frozen = ROOT / "results" / "frozen" / args.version
    manifest = verify_frozen(ROOT / "results", args.version)

    frame = pd.read_csv(frozen / "raw_results.csv")
    key = json.loads((frozen / "key_numbers.json").read_text(encoding="utf-8"))
    optimality = json.loads((frozen / "optimality.json").read_text(encoding="utf-8"))
    tex = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    # Whitespace-insensitive view so a phrase split across source lines still matches.
    tex_flat = re.sub(r"\s+", " ", tex)

    opt_blocks = {(row["experiment"], row["block"]): row for row in optimality["by_block"]}

    def gap(experiment: str, block: str, field: str) -> str:
        return f"{opt_blocks[(experiment, block)][field]:.2f}"

    experiment_a = frame[frame["experiment"] == "A"]
    corner = experiment_a[(experiment_a["n"] == 100) & (experiment_a["p"] == 0.7)]
    corner_wp_ms = 1000.0 * corner["wp_time_median_s"].median()
    corner_ds_ms = 1000.0 * corner["ds_time_median_s"].median()
    ratios = list(key["runtime_ratio_by_p"].values())

    graph = example_graph()
    wp = welsh_powell(graph)
    ds = dsatur(graph)
    triangle = all(v in graph.adjacency[u] for u, v in ((4, 5), (5, 6), (4, 6)))

    opt = key["optimality"]
    real = key["real_case"]
    audit = key["audit"]

    claims: list[tuple[str, str, str]] = [
        ("instances total", "690", str(key["instances_total"])),
        ("instances experiment A", "600", str(key["instances_experiment_a"])),
        ("instances experiment B", "90", str(key["instances_experiment_b"])),
        ("paired comparisons", "690", str(key["instances_total"])),
        (
            "primary executions",
            "1.380",
            f"{key['algorithm_instance_comparisons']:,}".replace(",", "."),
        ),
        ("mean colors WP", "11.89", f"{key['overall_wp_mean_colors']:.2f}"),
        ("mean colors DSATUR", "11.10", f"{key['overall_ds_mean_colors']:.2f}"),
        ("mean reduction", "7.17", f"{key['overall_mean_reduction_pct']:.2f}"),
        ("DSATUR wins", "390", str(key["overall_dsatur_wins"])),
        ("ties", "285", str(key["overall_ties"])),
        ("WP wins", "15", str(key["overall_wp_wins"])),
        ("runtime ratio", "3.09", f"{key['overall_runtime_ratio']:.2f}"),
        ("colors p-value", "4.2\\times10^{-66}", fmt_p(key["overall_colors_p"]).strip("$")),
        ("effect size", "-0.95", f"{key['overall_colors_effect']:.2f}"),
        ("ci low", "-0.86", f"{key['overall_color_ci'][0]:.2f}"),
        ("ci high", "-0.73", f"{key['overall_color_ci'][1]:.2f}"),
        ("runtime p-value", "1.2\\times10^{-114}", fmt_p(key["overall_runtime_p"]).strip("$")),
        ("runtime effect", "r=1.00", f"r={key['overall_runtime_effect']:.2f}"),
        ("experiment B ties", "83", str(key["experiment_b_ties"])),
        ("reduction n=20", "5.23", f"{key['reduction_by_n']['20']:.2f}"),
        ("reduction n=60", "10.34", f"{key['reduction_by_n']['60']:.2f}"),
        ("reduction n=100", "8.61", f"{key['reduction_by_n']['100']:.2f}"),
        ("reduction p=0.1", "11.14", f"{key['reduction_by_p']['0.1']:.2f}"),
        ("reduction p=0.3", "8.19", f"{key['reduction_by_p']['0.3']:.2f}"),
        ("reduction p=0.5", "8.04", f"{key['reduction_by_p']['0.5']:.2f}"),
        ("reduction p=0.7", "5.49", f"{key['reduction_by_p']['0.7']:.2f}"),
        ("reduction small program", "0.00", f"{key['reduction_by_scenario']['small_program']:.2f}"),
        (
            "reduction medium program",
            "0.48",
            f"{key['reduction_by_scenario']['medium_program']:.2f}",
        ),
        ("reduction large program", "0.11", f"{key['reduction_by_scenario']['large_program']:.2f}"),
        ("p small program", "1.000", f"{key['p_by_scenario']['small_program']:.3f}"),
        ("p medium program", "0.157", f"{key['p_by_scenario']['medium_program']:.3f}"),
        ("p large program", "0.655", f"{key['p_by_scenario']['large_program']:.3f}"),
        ("holm medium program", "0.472", f"{key['holm_p_by_scenario']['medium_program']:.3f}"),
        ("corner runtime DSATUR", "5.59", f"{corner_ds_ms:.2f}"),
        ("corner runtime WP", "1.83", f"{corner_wp_ms:.2f}"),
        ("min runtime ratio", "2.92", f"{min(ratios):.2f}"),
        ("max runtime ratio", "3.13", f"{max(ratios):.2f}"),
        ("max colors WP", "30", str(key["max_wp_colors"])),
        ("max colors DSATUR", "29", str(key["max_ds_colors"])),
        ("total conflicts", "nol konflik", "nol konflik" if key["total_conflicts"] == 0 else "X"),
        ("example courses", "tujuh mata kuliah", "tujuh mata kuliah" if N_COURSES == 7 else "X"),
        ("example students", "lima mahasiswa", "lima mahasiswa" if len(ENROLMENTS) == 5 else "X"),
        ("example edges", "sembilan sisi", "sembilan sisi" if graph.m == 9 else "X"),
        ("example WP colors", "empat slot", "empat slot" if wp.num_colors == 4 else "X"),
        ("example DSATUR colors", "tiga slot", "tiga slot" if ds.num_colors == 3 else "X"),
        ("example triangle", "segitiga", "segitiga" if triangle else "X"),
        # Exact optimality study
        ("optimality attempted", "450", str(opt["instances_attempted"])),
        ("optimality proven", "447", str(opt["instances_proven"])),
        ("optimality share", "99.3", f"{100.0 * opt['share_proven']:.1f}"),
        ("optimality benchmark share", "64.8", f"{100.0 * opt['share_of_benchmark']:.1f}"),
        ("optimality unproven", "243", str(opt["instances_without_proof"])),
        ("gap WP", "15.75", f"{opt['mean_gap_wp_pct']:.2f}"),
        ("gap DSATUR", "7.06", f"{opt['mean_gap_ds_pct']:.2f}"),
        ("DS optimal share", "61.3", f"{100.0 * opt['ds_optimal_share']:.1f}"),
        ("WP optimal share", "38.7", f"{100.0 * opt['wp_optimal_share']:.1f}"),
        ("gap n20 DS low", "1.11", gap("A", "n20_p0.1", "mean_gap_ds")),
        ("gap n20 DS high", "4.17", gap("A", "n20_p0.3", "mean_gap_ds")),
        ("gap n40 DS low", "7.50", gap("A", "n40_p0.1", "mean_gap_ds")),
        ("gap n40 DS high", "14.58", gap("A", "n40_p0.5", "mean_gap_ds")),
        ("gap n40 WP low", "17.75", gap("A", "n40_p0.7", "mean_gap_wp")),
        ("gap n40 WP high", "25.19", gap("A", "n40_p0.5", "mean_gap_wp")),
        ("gap n60 DS low", "15.91", gap("A", "n60_p0.5", "mean_gap_ds")),
        ("gap n60 DS high", "17.14", gap("A", "n60_p0.3", "mean_gap_ds")),
        ("gap B low", "0.00", gap("B", "small_program", "mean_gap_wp")),
        ("gap B high", "0.78", gap("B", "medium_program", "mean_gap_wp")),
        # Real-world case study
        ("real courses", "156", str(real["n_courses"])),
        ("real students", "975", str(real["n_students"])),
        ("real edges", "1.029", f"{real['n_edges']:,}".replace(",", ".")),
        ("real density", "0.085", f"{real['density']:.3f}"),
        ("real clustering", "0.649", f"{real['avg_clustering']:.3f}"),
        ("real WP colors", "13", str(real["k_wp"])),
        ("real DSATUR colors", "13", str(real["k_ds"])),
        ("real clique", "13", str(real["clique_lower_bound"])),
        ("real runtime ratio", "3.75", f"{real['runtime_ratio']:.2f}"),
        # Structural audit
        ("clustering experiment A", "0.397", f"{audit['clustering_experiment_a']:.3f}"),
        ("clustering experiment B", "0.776", f"{audit['clustering_experiment_b']:.3f}"),
    ]

    failures: list[str] = []
    for label, needle, computed in claims:
        if needle != computed:
            failures.append(f"{label}: manuscript says {needle!r}, frozen data gives {computed!r}")
        elif needle not in tex_flat:
            failures.append(f"{label}: {needle!r} not found in paper/main.tex")

    tests = collected_test_count()
    match = re.search(r"(\d+)\s+uji otomatis", tex)
    if not match:
        failures.append("test count: sentence about the automated tests not found")
    elif int(match.group(1)) != tests:
        failures.append(f"test count: manuscript says {match.group(1)}, pytest collects {tests}")

    print(
        f"frozen snapshot {args.version}: {len(manifest['files'])} artefacts, "
        f"checked {len(claims) + 1} claims"
    )
    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("all claims match the frozen benchmark dataset")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
