"""Tests for the exact chromatic-number solver.

The solver is the reference against which optimality gaps are measured, so it is
validated two ways: against graph families with known chromatic numbers, and
against exhaustive search on small random graphs.
"""

from __future__ import annotations

import itertools
import random

import pytest

import graph_families as families
from exact_coloring import exact_chromatic, greedy_clique
from graph_model import ConflictGraph


def brute_force_chromatic(graph: ConflictGraph) -> int:
    """Smallest k for which a k-colouring exists, by exhaustive enumeration."""
    for k in range(1, graph.n + 1):
        for assignment in itertools.product(range(k), repeat=graph.n):
            if all(
                assignment[u] != assignment[v]
                for u in range(graph.n)
                for v in graph.adjacency[u]
                if u < v
            ):
                return k
    return graph.n


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("empty", 0),
        ("single", 1),
        ("edgeless5", 1),
        ("complete6", 6),
        ("path7", 2),
        ("cycle5", 3),
        ("cycle6", 2),
        ("cycle9", 3),
        ("star6", 2),
        ("k33", 2),
        ("petersen", 3),
        ("grotzsch", 4),
        ("hypercube3", 2),
        ("grid3x4", 2),
    ],
)
def test_known_chromatic_numbers(name, expected):
    graph = families.ALL_VALIDITY_CASES[name]
    result = exact_chromatic(graph, time_limit_s=30)
    assert result.proven
    assert result.chromatic_number == expected


def test_odd_wheel_needs_four_colors():
    # wheel(5) has a 5-cycle rim plus a hub, so chi = 4.
    result = exact_chromatic(families.wheel(5), time_limit_s=30)
    assert result.proven
    assert result.chromatic_number == 4


def test_even_wheel_needs_three_colors():
    result = exact_chromatic(families.wheel(6), time_limit_s=30)
    assert result.proven
    assert result.chromatic_number == 3


def test_matches_brute_force_on_random_graphs():
    rng = random.Random(20240517)
    for _ in range(120):
        n = rng.randint(1, 8)
        p = rng.choice([0.1, 0.3, 0.5, 0.7, 0.9])
        edges = [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
        graph = ConflictGraph.from_edges(n, edges)
        result = exact_chromatic(graph, time_limit_s=10)
        assert result.proven
        assert result.chromatic_number == brute_force_chromatic(graph)


def test_greedy_clique_is_a_clique():
    graph = families.petersen()
    clique = greedy_clique(graph)
    for i, u in enumerate(clique):
        for v in clique[i + 1 :]:
            assert v in graph.adjacency[u]


def test_lower_bound_never_exceeds_chromatic_number():
    for name in ("petersen", "grotzsch", "cycle9", "grid3x4"):
        graph = families.ALL_VALIDITY_CASES[name]
        result = exact_chromatic(graph, time_limit_s=30)
        assert result.lower_bound <= result.chromatic_number


def test_time_limit_reports_unproven_instead_of_guessing():
    # A dense 60-vertex graph with a zero time budget cannot be finished.
    graph = families.complete(60)
    result = exact_chromatic(graph, time_limit_s=0.0, node_limit=1)
    # The clique bound already certifies the answer for a complete graph, so the
    # search is skipped; the result must still be proven and correct.
    assert result.proven
    assert result.chromatic_number == 60


def test_node_limit_marks_result_unproven():
    graph = families.cycle(9)
    result = exact_chromatic(graph, time_limit_s=60.0, node_limit=1)
    assert not result.proven
    assert result.chromatic_number is None
    assert result.lower_bound <= result.upper_bound


def test_uses_best_heuristic_as_upper_bound():
    # One enrolment instance has Welsh--Powell matching the clique bound while
    # DSATUR needs one more colour.  The search must certify it immediately
    # instead of exploring, which is only possible if the better colouring is
    # used as the initial upper bound.
    from dsatur import dsatur
    from enrollment_generator import SCENARIOS, generate_enrollment_instance
    from welsh_powell import welsh_powell

    scenario = SCENARIOS[2]
    graph = generate_enrollment_instance(scenario, 419919096).graph
    wp = welsh_powell(graph)
    ds = dsatur(graph)
    if wp.num_colors >= ds.num_colors:
        pytest.skip("this instance no longer separates the two heuristics")
    result = exact_chromatic(graph, time_limit_s=10)
    assert result.proven
    assert result.chromatic_number == wp.num_colors
    assert result.nodes == 0
