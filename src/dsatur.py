"""Greedy DSATUR saturation-degree coloring heuristic.

Reference
---------
D. Brélaz, "New methods to color the vertices of a graph," *Communications of
the ACM*, vol. 22, no. 4, pp. 251--256, 1979.  doi:10.1145/359094.359101

This module implements the *greedy* DSATUR construction only.  It is a
heuristic and carries no optimality guarantee; the exact branch-and-bound
DSATUR of Brélaz is outside the scope of this study.

Two implementations are provided and are required to agree exactly:

``dsatur``
    Production implementation.  A lazy binary heap over the key
    ``(-saturation, -degree, vertex)`` yields an amortised
    ``O((n + m) log n)`` running time.

``dsatur_reference``
    Straightforward ``O(n^2 + m)`` linear-scan selection, used only to validate
    the heap implementation in the test suite.

Both use the same deterministic tie-breaking rule: highest saturation degree,
then highest (static) degree, then smallest vertex identifier.
"""

from __future__ import annotations

import heapq
import time
from collections.abc import Callable

from graph_model import ColoringResult, ConflictGraph

Timer = Callable[[], float]


def _first_free_color(forbidden_mask: int) -> int:
    """Smallest non-negative color whose bit is not set in ``forbidden_mask``."""
    color = 0
    while (forbidden_mask >> color) & 1:
        color += 1
    return color


def dsatur(graph: ConflictGraph, timer: Timer = time.perf_counter) -> ColoringResult:
    """Greedy DSATUR with a lazy heap and deterministic tie-breaking."""
    start = timer()
    n = graph.n
    colors = [-1] * n
    saturation = [0] * n
    neighbour_colors = [0] * n  # bit mask of colors present in the neighbourhood
    degrees = graph.degrees

    # key = (-saturation, -degree, vertex): smallest key wins, so the popped
    # vertex has maximum saturation, then maximum degree, then minimum id.
    heap = [(-0, -degrees[v], v) for v in range(n)]
    heapq.heapify(heap)
    selection_order: list[int] = []

    while heap:
        neg_sat, _neg_deg, v = heapq.heappop(heap)
        if colors[v] != -1:
            continue  # stale entry: vertex already colored
        if -neg_sat != saturation[v]:
            continue  # stale entry: records an outdated saturation degree
        selection_order.append(v)
        color = _first_free_color(neighbour_colors[v])
        colors[v] = color
        bit = 1 << color
        for u in graph.adjacency[v]:
            if colors[u] == -1 and not neighbour_colors[u] & bit:
                neighbour_colors[u] |= bit
                saturation[u] += 1
                heapq.heappush(heap, (-saturation[u], -degrees[u], u))

    elapsed = timer() - start
    k = max(colors) + 1 if n else 0
    return ColoringResult("dsatur", tuple(colors), k, elapsed, tuple(selection_order))


def dsatur_reference(graph: ConflictGraph, timer: Timer = time.perf_counter) -> ColoringResult:
    """Literal O(n^2 + m) DSATUR: rescan all uncolored vertices at each step."""
    start = timer()
    n = graph.n
    colors = [-1] * n
    saturation = [0] * n
    neighbour_colors = [0] * n
    degrees = graph.degrees
    selection_order: list[int] = []

    for _ in range(n):
        best = -1
        best_key = (-1, -1, 0)
        for v in range(n):
            if colors[v] != -1:
                continue
            key = (saturation[v], degrees[v], -v)
            if key > best_key:
                best_key = key
                best = v
        if best < 0:
            break
        selection_order.append(best)
        color = _first_free_color(neighbour_colors[best])
        colors[best] = color
        bit = 1 << color
        for u in graph.adjacency[best]:
            if colors[u] == -1 and not neighbour_colors[u] & bit:
                neighbour_colors[u] |= bit
                saturation[u] += 1

    elapsed = timer() - start
    k = max(colors) + 1 if n else 0
    return ColoringResult("dsatur_reference", tuple(colors), k, elapsed, tuple(selection_order))
