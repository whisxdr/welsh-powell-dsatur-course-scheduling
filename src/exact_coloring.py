"""Exact chromatic number by branch and bound, for small instances only.

The two heuristics under study carry no optimality guarantee.  To measure how
far they are from the true optimum on instances where the optimum is knowable,
this module computes the chromatic number exactly with a DSATUR-ordered
branch-and-bound search (the classical exact form of Brélaz's algorithm).

The search is deliberately bounded: it stops after a wall-clock limit or a node
limit and reports ``proven = False`` rather than guessing.  Callers must treat
an unproven result as "unknown", never as an optimum.

Bounds used
-----------
* Upper bound: the greedy DSATUR coloring of the same graph.
* Lower bound: the size of a clique found by a greedy common-neighbour search.
  Any clique is a valid lower bound because ``omega(G) <= chi(G)``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from dsatur import dsatur
from graph_model import ConflictGraph
from welsh_powell import welsh_powell


@dataclass(frozen=True, slots=True)
class ExactResult:
    """Outcome of an exact chromatic-number attempt."""

    chromatic_number: int | None
    proven: bool
    lower_bound: int
    upper_bound: int
    nodes: int
    elapsed_seconds: float
    timed_out: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "chromatic_number": self.chromatic_number,
            "proven": self.proven,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "nodes": self.nodes,
            "elapsed_seconds": self.elapsed_seconds,
            "timed_out": self.timed_out,
        }


def greedy_clique(graph: ConflictGraph) -> tuple[int, ...]:
    """Greedy clique: a valid lower bound on ``omega(G)`` and hence on ``chi(G)``."""
    best: tuple[int, ...] = ()
    adjacency = [set(a) for a in graph.adjacency]
    for start in range(graph.n):
        clique = [start]
        candidates = set(adjacency[start])
        while candidates:
            pivot = max(
                candidates,
                key=lambda u: (len(candidates & adjacency[u]), -u),
            )
            clique.append(pivot)
            candidates &= adjacency[pivot]
        if len(clique) > len(best):
            best = tuple(clique)
    return best


def exact_chromatic(
    graph: ConflictGraph,
    time_limit_s: float = 30.0,
    node_limit: int = 2_000_000,
) -> ExactResult:
    """Compute ``chi(G)`` exactly, or report that the search was cut short."""
    start = time.perf_counter()
    n = graph.n
    if n == 0:
        return ExactResult(0, True, 0, 0, 0, time.perf_counter() - start, False)

    # Upper bound: the better of the two heuristics under study.  Using the
    # best available colouring is standard practice and can certify an instance
    # immediately when it matches the clique bound.
    wp = welsh_powell(graph)
    ds = dsatur(graph)
    if wp.num_colors <= ds.num_colors:
        best = wp.num_colors
        best_colors = list(wp.colors)
    else:
        best = ds.num_colors
        best_colors = list(ds.colors)
    lower = len(greedy_clique(graph))

    if lower >= best:
        return ExactResult(best, True, lower, best, 0, time.perf_counter() - start, False)

    degrees = graph.degrees
    colors = [-1] * n
    saturation = [0] * n
    neighbour_colors = [0] * n
    nodes = 0
    timed_out = False

    def select_vertex() -> int:
        chosen = -1
        best_key = (-1, -1, 0)
        for v in range(n):
            if colors[v] == -1:
                key = (saturation[v], degrees[v], -v)
                if key > best_key:
                    best_key = key
                    chosen = v
        return chosen

    def search(used: int) -> None:
        nonlocal best, best_colors, nodes, timed_out
        if timed_out:
            return
        nodes += 1
        if nodes % 2048 == 0 and time.perf_counter() - start > time_limit_s:
            timed_out = True
            return
        if nodes > node_limit:
            timed_out = True
            return

        vertex = select_vertex()
        if vertex < 0:
            if used < best:
                best = used
                best_colors = colors.copy()
            return
        if used >= best:
            return

        forbidden = neighbour_colors[vertex]
        # At the root only color 0 is tried: this removes colour-permutation
        # symmetry without losing any solution.
        limit = 0 if used == 0 else min(used, best - 1)
        for color in range(limit + 1):
            if (forbidden >> color) & 1:
                continue
            colors[vertex] = color
            bit = 1 << color
            changed: list[int] = []
            for u in graph.adjacency[vertex]:
                if colors[u] == -1 and not neighbour_colors[u] & bit:
                    neighbour_colors[u] |= bit
                    saturation[u] += 1
                    changed.append(u)
            search(max(used, color + 1))
            for u in changed:
                neighbour_colors[u] &= ~bit
                saturation[u] -= 1
            colors[vertex] = -1
            if timed_out:
                return

    search(0)
    elapsed = time.perf_counter() - start

    if timed_out:
        return ExactResult(None, False, lower, best, nodes, elapsed, True)

    # The search exhausted the space, so `best` is the true chromatic number.
    graph.check_coloring(best_colors)
    return ExactResult(best, True, lower, best, nodes, elapsed, False)
