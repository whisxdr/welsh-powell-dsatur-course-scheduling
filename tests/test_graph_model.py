"""Tests for the shared graph model and coloring validation."""

from __future__ import annotations

import networkx as nx
import pytest

from graph_model import (
    ColoringResult,
    ConflictGraph,
    GraphModelError,
    validate_result,
)


def build(n: int, edges: list[tuple[int, int]]) -> ConflictGraph:
    return ConflictGraph.from_edges(n, edges)


# ----------------------------------------------------------------------
# Construction
# ----------------------------------------------------------------------
def test_construction_normalises_edges():
    graph = build(4, [(2, 3), (0, 1), (1, 0)])
    assert graph.n == 4
    assert graph.adjacency == ((1,), (0,), (3,), (2,))
    assert graph.m == 2
    assert graph.degrees == (1, 1, 1, 1)


def test_self_loops_rejected():
    with pytest.raises(GraphModelError):
        build(3, [(1, 1)])


def test_out_of_range_edge_rejected():
    with pytest.raises(GraphModelError):
        build(3, [(0, 5)])


def test_unsorted_adjacency_rejected():
    with pytest.raises(GraphModelError):
        ConflictGraph(3, ((2, 1), (0,), (0,)))


def test_asymmetric_adjacency_rejected():
    with pytest.raises(GraphModelError):
        ConflictGraph(2, ((1,), ()))


def test_networkx_round_trip():
    g = nx.Graph()
    g.add_edges_from([("a", "b"), ("b", "c"), ("c", "a")])
    graph = ConflictGraph.from_networkx(g)
    assert graph.n == 3
    assert graph.m == 3


# ----------------------------------------------------------------------
# Density
# ----------------------------------------------------------------------
def test_density_definition():
    assert build(1, []).density() == 0.0
    assert build(0, []).density() == 0.0
    assert build(4, []).density() == 0.0
    complete = build(5, [(i, j) for i in range(5) for j in range(i + 1, 5)])
    assert complete.m == 10
    assert complete.density() == pytest.approx(1.0)
    assert build(5, [(0, 1), (1, 2)]).density() == pytest.approx(2 * 2 / (5 * 4))


# ----------------------------------------------------------------------
# Coloring validation
# ----------------------------------------------------------------------
def test_check_coloring_accepts_valid():
    graph = build(3, [(0, 1), (1, 2)])
    graph.check_coloring([0, 1, 0])
    assert graph.is_valid_coloring([0, 1, 0])
    assert graph.count_conflicts([0, 1, 0]) == 0


def test_check_coloring_rejects_conflict():
    graph = build(3, [(0, 1), (1, 2)])
    assert not graph.is_valid_coloring([0, 0, 1])
    assert graph.count_conflicts([0, 0, 1]) == 1
    with pytest.raises(GraphModelError):
        graph.check_coloring([0, 0, 1])


def test_check_coloring_rejects_length_and_negative():
    graph = build(3, [])
    with pytest.raises(GraphModelError):
        graph.check_coloring([0, 1])
    with pytest.raises(GraphModelError):
        graph.check_coloring([0, -1, 2])


def test_colors_used_ignores_uncolored():
    assert ConflictGraph.colors_used((0, 1, 1, 2)) == 3
    assert ConflictGraph.colors_used(()) == 0
    assert ConflictGraph.colors_used((-1, -1)) == 0


def test_validate_result_detects_inconsistent_count():
    graph = build(3, [(0, 1)])
    bad = ColoringResult("x", (0, 1, 0), 3, 0.0)
    with pytest.raises(GraphModelError):
        validate_result(graph, bad)


def test_validate_result_detects_non_normalised_colors():
    graph = build(3, [(0, 1)])
    bad = ColoringResult("x", (0, 2, 2), 2, 0.0)
    with pytest.raises(GraphModelError):
        validate_result(graph, bad)
