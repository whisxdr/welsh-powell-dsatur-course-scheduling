"""Tests for the benchmark driver and the paired analysis."""

from __future__ import annotations

import pandas as pd
import pytest

from analysis import paired_analysis
from benchmark import (
    environment_info,
    measure_instance,
    summarise_colors,
    summarise_density_effect,
    summarise_runtime,
    summarise_win_tie_loss,
)
from graph_generator import erdos_renyi, instance_seed


@pytest.fixture(scope="module")
def sample_frame() -> pd.DataFrame:
    rows = []
    for n in (20, 40):
        for p in (0.1, 0.5):
            for rep in range(3):
                graph = erdos_renyi(n, p, instance_seed(n, int(p * 1000), rep))
                record = measure_instance(graph, repeats=3)
                record.update(
                    {
                        "experiment": "A",
                        "scenario": f"n{n}_p{p:.1f}",
                        "p": p,
                        "seed": rep,
                        "generation_s": 0.0,
                        "digest": "x",
                    }
                )
                rows.append(record)
    return pd.DataFrame(rows)


def test_measure_instance_reports_zero_conflicts(sample_frame):
    assert (sample_frame["wp_conflicts"] == 0).all()
    assert (sample_frame["ds_conflicts"] == 0).all()


def test_measure_instance_records_positive_times(sample_frame):
    assert (sample_frame["wp_time_median_s"] > 0).all()
    assert (sample_frame["ds_time_median_s"] > 0).all()
    assert (sample_frame["repeats"] == 3).all()


def test_reduction_and_winner_are_consistent(sample_frame):
    for row in sample_frame.itertuples():
        expected = 100.0 * (row.wp_colors - row.ds_colors) / row.wp_colors
        assert row.reduction_pct == pytest.approx(expected)
        if row.ds_colors < row.wp_colors:
            assert row.winner == "dsatur"
        elif row.ds_colors > row.wp_colors:
            assert row.winner == "welsh_powell"
        else:
            assert row.winner == "tie"


def test_summaries_have_expected_shape(sample_frame):
    colors = summarise_colors(sample_frame)
    runtime = summarise_runtime(sample_frame)
    wtl = summarise_win_tie_loss(sample_frame)
    density = summarise_density_effect(sample_frame)

    assert {"experiment", "scenario", "n", "wp_mean", "ds_mean"} <= set(colors.columns)
    assert {"wp_median_ms", "ds_median_ms"} <= set(runtime.columns)
    assert {"dsatur_wins", "ties", "wp_wins", "instances"} <= set(wtl.columns)
    assert {"density_bin", "wp_mean_colors", "ds_mean_colors"} <= set(density.columns)
    assert (wtl["instances"] == wtl[["dsatur_wins", "ties", "wp_wins"]].sum(axis=1)).all()


def test_paired_analysis_structure(sample_frame):
    stats = paired_analysis(sample_frame)
    assert stats["design"] == "paired within-instance comparison"
    assert "overall" in stats
    assert "by_probability" in stats
    overall = stats["overall"]
    assert overall["instances"] == len(sample_frame)
    assert 0.0 <= overall["colors_wilcoxon"]["p_value"] <= 1.0
    low, high = overall["color_difference_bootstrap_95ci"]
    assert low <= high


def test_environment_info_reports_real_versions():
    info = environment_info()
    assert info["python_version"]
    assert info["numpy_version"]
    assert info["system"]
