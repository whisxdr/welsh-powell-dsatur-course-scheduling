"""Tests for the greedy DSATUR heuristic."""

from __future__ import annotations

import pytest

import graph_families as families
from dsatur import dsatur, dsatur_reference
from graph_generator import erdos_renyi, instance_seed
from graph_model import ConflictGraph, validate_result


# ----------------------------------------------------------------------
# Determinism and tie-breaking
# ----------------------------------------------------------------------
def test_run_is_deterministic():
    graph = erdos_renyi(40, 0.3, instance_seed(40, 300, 0))
    first = dsatur(graph)
    second = dsatur(graph)
    assert first.colors == second.colors
    assert first.order == second.order


def test_tie_break_uses_degree_then_identifier():
    # Triangle 0-1-2 plus triangle 2-3-4.  Vertex 2 has degree 4, all others 2.
    graph = ConflictGraph.from_edges(5, [(0, 1), (0, 2), (1, 2), (2, 3), (2, 4), (3, 4)])
    result = dsatur(graph)
    # Hand-derived expectation:
    #   2 (max degree) -> color 0
    #   0 (saturation 1, degree 2, smallest id) -> color 1
    #   1 (saturation 2) -> color 2
    #   3 (saturation 1, degree 2) -> color 1
    #   4 (saturation 2) -> color 2
    assert result.order == (2, 0, 1, 3, 4)
    assert result.colors == (1, 2, 0, 1, 2)
    assert result.num_colors == 3


def test_edgeless_graph_selection_order_is_ascending():
    result = dsatur(families.edgeless(6))
    assert result.order == (0, 1, 2, 3, 4, 5)
    assert result.num_colors == 1


# ----------------------------------------------------------------------
# Heap implementation versus linear-scan reference
# ----------------------------------------------------------------------
@pytest.mark.parametrize("n", [10, 25, 60, 100])
@pytest.mark.parametrize("p", [0.05, 0.3, 0.6, 0.9])
def test_heap_matches_reference(n, p):
    graph = erdos_renyi(n, p, instance_seed(n, int(p * 1000), 3))
    fast = dsatur(graph)
    slow = dsatur_reference(graph)
    assert fast.colors == slow.colors
    assert fast.num_colors == slow.num_colors
    assert fast.order == slow.order


@pytest.mark.parametrize("name", sorted(families.ALL_VALIDITY_CASES))
def test_heap_matches_reference_on_families(name):
    graph = families.ALL_VALIDITY_CASES[name]
    fast = dsatur(graph)
    slow = dsatur_reference(graph)
    assert fast.colors == slow.colors
    assert fast.order == slow.order


# ----------------------------------------------------------------------
# Validity
# ----------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(families.ALL_VALIDITY_CASES))
def test_produces_valid_coloring(name):
    graph = families.ALL_VALIDITY_CASES[name]
    result = dsatur(graph)
    validate_result(graph, result)
    assert graph.count_conflicts(result.colors) == 0


@pytest.mark.parametrize("seed", range(20))
def test_valid_on_random_graphs(seed):
    graph = erdos_renyi(50, 0.2 + 0.03 * seed, instance_seed(50, seed, 13))
    result = dsatur(graph)
    validate_result(graph, result)
    assert result.num_colors <= graph.max_degree() + 1


# ----------------------------------------------------------------------
# Known color counts
# ----------------------------------------------------------------------
def test_empty_graph_uses_no_colors():
    result = dsatur(families.empty())
    assert result.colors == ()
    assert result.num_colors == 0


def test_single_vertex_uses_one_color():
    assert dsatur(families.single()).num_colors == 1


def test_edgeless_graph_uses_one_color():
    assert dsatur(families.edgeless(9)).num_colors == 1


@pytest.mark.parametrize("n", [2, 3, 5, 8])
def test_complete_graph_uses_n_colors(n):
    graph = families.complete(n)
    result = dsatur(graph)
    validate_result(graph, result)
    assert result.num_colors == n


@pytest.mark.parametrize("n", [3, 5, 7, 9])
def test_odd_cycles_use_three_colors(n):
    assert dsatur(families.cycle(n)).num_colors == 3


@pytest.mark.parametrize("n", [4, 6, 8, 10])
def test_even_cycles_use_two_colors(n):
    assert dsatur(families.cycle(n)).num_colors == 2


@pytest.mark.parametrize("leaves", [1, 3, 6])
def test_star_uses_two_colors(leaves):
    assert dsatur(families.star(leaves)).num_colors == 2


@pytest.mark.parametrize(("left", "right"), [(2, 3), (3, 3), (4, 5)])
def test_complete_bipartite_uses_two_colors(left, right):
    assert dsatur(families.complete_bipartite(left, right)).num_colors == 2


def test_petersen_uses_three_colors():
    assert dsatur(families.petersen()).num_colors == 3


def test_grotzsch_needs_at_least_four_colors():
    graph = families.grotzsch()
    result = dsatur(graph)
    validate_result(graph, result)
    assert result.num_colors >= 4


@pytest.mark.parametrize("name", ["hypercube3", "grid3x4", "k33"])
def test_bipartite_graphs_are_validly_colored(name):
    # Greedy heuristics have no two-colour guarantee on arbitrary bipartite
    # graphs, so only validity and the trivial lower bound are asserted here.
    graph = families.ALL_VALIDITY_CASES[name]
    result = dsatur(graph)
    validate_result(graph, result)
    assert 2 <= result.num_colors <= graph.max_degree() + 1
