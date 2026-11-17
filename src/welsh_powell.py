"""Welsh--Powell sequential coloring heuristic.

Reference
---------
D. J. A. Welsh and M. B. Powell, "An upper bound for the chromatic number of a
graph and its application to timetabling problems," *The Computer Journal*,
vol. 10, no. 1, pp. 85--86, 1967.  doi:10.1093/comjnl/10.1.85

Two formulations are provided:

``welsh_powell``
    The efficient greedy formulation: visit vertices in non-increasing degree
    order and give each vertex the smallest color not used by an already
    colored neighbour.  Runs in ``O(n + m)`` time with a bit-mask of forbidden
    colors.

``welsh_powell_class_scan``
    A literal transcription of the 1967 color-class construction: repeatedly
    open a new color class, seed it with the first uncolored vertex in the
    ordering, then sweep the remaining uncolored vertices in the same ordering
    and add every vertex that is non-adjacent to the class.  Runs in
    ``O(n(n + m))`` time.

The two formulations are provably equivalent (see ``tests/test_welsh_powell.py``
for the executable check): a vertex receives the smallest color index whose
class contains none of its neighbours, which is exactly the smallest color not
used by an earlier neighbour.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from graph_model import ColoringResult, ConflictGraph

Timer = Callable[[], float]


def welsh_powell_order(graph: ConflictGraph) -> tuple[int, ...]:
    """Vertices sorted by non-increasing degree, ties broken by ascending id."""
    return tuple(sorted(range(graph.n), key=lambda v: (-graph.degree(v), v)))


def welsh_powell(graph: ConflictGraph, timer: Timer = time.perf_counter) -> ColoringResult:
    """Greedy coloring in Welsh--Powell (descending degree) order."""
    start = timer()
    order = welsh_powell_order(graph)
    colors = [-1] * graph.n
    for v in order:
        forbidden = 0
        for u in graph.adjacency[v]:
            c = colors[u]
            if c >= 0:
                forbidden |= 1 << c
        color = 0
        while (forbidden >> color) & 1:
            color += 1
        colors[v] = color
    elapsed = timer() - start
    k = max(colors) + 1 if graph.n else 0
    return ColoringResult("welsh_powell", tuple(colors), k, elapsed, order)


def welsh_powell_class_scan(
    graph: ConflictGraph, timer: Timer = time.perf_counter
) -> ColoringResult:
    """Literal color-class construction of the original 1967 algorithm."""
    start = timer()
    order = welsh_powell_order(graph)
    colors = [-1] * graph.n
    color = 0
    for seed in order:
        if colors[seed] != -1:
            continue
        colors[seed] = color
        for v in order:
            if colors[v] != -1:
                continue
            if all(colors[u] != color for u in graph.adjacency[v]):
                colors[v] = color
        color += 1
    elapsed = timer() - start
    k = max(colors) + 1 if graph.n else 0
    return ColoringResult("welsh_powell_class_scan", tuple(colors), k, elapsed, order)
