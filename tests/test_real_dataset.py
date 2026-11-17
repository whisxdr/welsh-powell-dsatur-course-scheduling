"""Tests for the real-world dataset loader and the structural audit."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from graph_audit import audit_graph
from graph_model import ConflictGraph
from real_dataset import (
    DEFAULT_PATH,
    EXPECTED_SHA256,
    DatasetIntegrityError,
    load_real_dataset,
)

pytestmark = pytest.mark.skipif(
    not Path(DEFAULT_PATH).exists(),
    reason="real dataset not downloaded (see README)",
)


def test_dataset_loads_with_pinned_digest():
    dataset = load_real_dataset()
    assert dataset.sha256 == EXPECTED_SHA256
    assert dataset.n_students == 975
    assert dataset.n_courses == 156
    assert dataset.registrations == 3129


def test_conflict_graph_shape():
    dataset = load_real_dataset()
    graph = dataset.graph
    assert graph.n == 156
    assert graph.m == 1029
    assert graph.density() == pytest.approx(0.0851, abs=1e-4)
    assert graph.max_degree() == 60


def test_edges_are_symmetric_and_loop_free():
    graph = load_real_dataset().graph
    for u in range(graph.n):
        assert u not in graph.adjacency[u]
        for v in graph.adjacency[u]:
            assert u in graph.adjacency[v]


def test_tampered_file_is_rejected(tmp_path):
    target = tmp_path / "StudentSubjectUnique.csv"
    shutil.copyfile(DEFAULT_PATH, target)
    with target.open("a", encoding="utf-8") as handle:
        handle.write("\n0,0,0\n")
    with pytest.raises(DatasetIntegrityError):
        load_real_dataset(target)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_real_dataset(tmp_path / "absent.csv")


def test_audit_reports_expected_structure():
    graph = load_real_dataset().graph
    audit = audit_graph(graph)
    assert audit["n"] == 156
    assert audit["m"] == 1029
    assert audit["components"] == 2
    assert audit["largest_component"] == 155
    assert 0.6 < audit["avg_clustering"] < 0.7
    assert audit["clique_lower_bound"] >= 13


def test_audit_on_known_graph():
    graph = ConflictGraph.from_edges(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    audit = audit_graph(graph)
    assert audit["components"] == 1
    assert audit["avg_clustering"] == 0.0
    assert audit["clique_lower_bound"] == 2
