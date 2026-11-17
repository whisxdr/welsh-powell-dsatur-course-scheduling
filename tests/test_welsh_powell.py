"""Tests for the Welsh--Powell heuristic."""

from __future__ import annotations

import pytest

import graph_families as families
from graph_generator import erdos_renyi, instance_seed
from graph_model import validate_result
from welsh_powell import welsh_powell, welsh_powell_class_scan, welsh_powell_order


# ----------------------------------------------------------------------
# Ordering and determinism
# ----------------------------------------------------------------------
def test_order_is_descending_degree_with_id_tiebreak():
    graph = families.star(5)  # center 0 has degree 5, leaves 1..5 have degree 1
    assert welsh_powell_order(graph) == (0, 1, 2, 3, 4, 5)


def test_order_ties_broken_by_ascending_id():
    graph = families.cycle(6)  # all degrees equal
    assert welsh_powell_order(graph) == (0, 1, 2, 3, 4, 5)


def test_run_is_deterministic():
    graph = erdos_renyi(40, 0.3, instance_seed(40, 300, 0))
    first = welsh_powell(graph)
    second = welsh_powell(graph)
    assert first.colors == second.colors
    assert first.num_colors == second.num_colors


# ----------------------------------------------------------------------
# Equivalence of the two formulations
# ----------------------------------------------------------------------
@pytest.mark.parametrize("n", [10, 25, 60, 100])
@pytest.mark.parametrize("p", [0.05, 0.3, 0.6, 0.9])
def test_greedy_matches_class_scan(n, p):
    graph = erdos_renyi(n, p, instance_seed(n, int(p * 1000), 7))
    greedy = welsh_powell(graph)
    scan = welsh_powell_class_scan(graph)
    assert greedy.colors == scan.colors
    assert greedy.num_colors == scan.num_colors


@pytest.mark.parametrize("name", sorted(families.ALL_VALIDITY_CASES))
def test_greedy_matches_class_scan_on_families(name):
    graph = families.ALL_VALIDITY_CASES[name]
    assert welsh_powell(graph).colors == welsh_powell_class_scan(graph).colors


# ----------------------------------------------------------------------
# Validity
# ----------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(families.ALL_VALIDITY_CASES))
def test_produces_valid_coloring(name):
    graph = families.ALL_VALIDITY_CASES[name]
    result = welsh_powell(graph)
    validate_result(graph, result)
    assert graph.count_conflicts(result.colors) == 0


@pytest.mark.parametrize("seed", range(20))
def test_valid_on_random_graphs(seed):
    graph = erdos_renyi(50, 0.2 + 0.03 * seed, instance_seed(50, seed, 11))
    result = welsh_powell(graph)
    validate_result(graph, result)
    assert result.num_colors <= graph.max_degree() + 1


# ----------------------------------------------------------------------
# Known color counts
# ----------------------------------------------------------------------
def test_empty_graph_uses_no_colors():
    result = welsh_powell(families.empty())
    assert result.colors == ()
    assert result.num_colors == 0


def test_single_vertex_uses_one_color():
    result = welsh_powell(families.single())
    assert result.num_colors == 1


def test_edgeless_graph_uses_one_color():
    assert welsh_powell(families.edgeless(9)).num_colors == 1


@pytest.mark.parametrize("n", [2, 3, 5, 8])
def test_complete_graph_uses_n_colors(n):
    graph = families.complete(n)
    result = welsh_powell(graph)
    validate_result(graph, result)
    assert result.num_colors == n


@pytest.mark.parametrize("n", [3, 5, 7, 9])
def test_odd_cycles_use_three_colors(n):
    assert welsh_powell(families.cycle(n)).num_colors == 3


@pytest.mark.parametrize("n", [4, 6, 8, 10])
def test_even_cycles_use_two_colors(n):
    assert welsh_powell(families.cycle(n)).num_colors == 2


@pytest.mark.parametrize("leaves", [1, 3, 6])
def test_star_uses_two_colors(leaves):
    assert welsh_powell(families.star(leaves)).num_colors == 2


@pytest.mark.parametrize(("left", "right"), [(2, 3), (3, 3), (4, 5)])
def test_complete_bipartite_uses_two_colors(left, right):
    assert welsh_powell(families.complete_bipartite(left, right)).num_colors == 2


def test_petersen_uses_three_colors():
    assert welsh_powell(families.petersen()).num_colors == 3


def test_grotzsch_needs_at_least_four_colors():
    graph = families.grotzsch()
    result = welsh_powell(graph)
    validate_result(graph, result)
    # The Grötzsch graph is triangle-free with chromatic number 4, so no valid
    # coloring can use fewer than four colors.
    assert result.num_colors >= 4
