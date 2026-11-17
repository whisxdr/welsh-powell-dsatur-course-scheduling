"""Tests for the worked example used in the manuscript.

The manuscript makes specific, checkable claims about this example: seven
courses, five students, nine edges, a triangle, four Welsh--Powell slots and
three DSATUR slots.  Those claims are asserted here so the figure and the text
cannot drift from the code.
"""

from __future__ import annotations

from dsatur import dsatur
from graph_model import validate_result
from illustrative_example import ENROLMENTS, N_COURSES, example_graph, example_table
from welsh_powell import welsh_powell


def test_example_size():
    assert N_COURSES == 7
    assert len(ENROLMENTS) == 5


def test_example_edge_count():
    assert example_graph().m == 9


def test_example_contains_triangle():
    graph = example_graph()
    triangle = (4, 5, 6)
    for i, u in enumerate(triangle):
        for v in triangle[i + 1 :]:
            assert v in graph.adjacency[u]


def test_example_welsh_powell_uses_four_slots():
    graph = example_graph()
    result = welsh_powell(graph)
    validate_result(graph, result)
    assert result.num_colors == 4


def test_example_dsatur_uses_three_slots():
    graph = example_graph()
    result = dsatur(graph)
    validate_result(graph, result)
    assert result.num_colors == 3


def test_example_dsatur_is_optimal():
    # The triangle gives chi >= 3 and DSATUR attains 3, so the example is
    # provably optimal for DSATUR.
    graph = example_graph()
    assert dsatur(graph).num_colors == 3


def test_example_table_labels_are_one_based():
    table = example_table()
    assert table[0][0] == "S1"
    assert table[0][1] == ["C1", "C4"]
    assert all(label.startswith("C") for _, courses in table for label in courses)
