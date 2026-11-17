"""Standard graph families used by the algorithm tests.

Construction uses NetworkX only to build topology; the coloring heuristics under
test never touch NetworkX.
"""

from __future__ import annotations

import networkx as nx

from graph_model import ConflictGraph


def empty() -> ConflictGraph:
    return ConflictGraph.from_edges(0, [])


def single() -> ConflictGraph:
    return ConflictGraph.from_edges(1, [])


def edgeless(n: int) -> ConflictGraph:
    return ConflictGraph.from_edges(n, [])


def complete(n: int) -> ConflictGraph:
    return ConflictGraph.from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n)])


def path(n: int) -> ConflictGraph:
    return ConflictGraph.from_edges(n, [(i, i + 1) for i in range(n - 1)])


def cycle(n: int) -> ConflictGraph:
    edges = [(i, (i + 1) % n) for i in range(n)]
    return ConflictGraph.from_edges(n, edges)


def star(leaves: int) -> ConflictGraph:
    return ConflictGraph.from_edges(leaves + 1, [(0, i) for i in range(1, leaves + 1)])


def complete_bipartite(left: int, right: int) -> ConflictGraph:
    edges = [(i, left + j) for i in range(left) for j in range(right)]
    return ConflictGraph.from_edges(left + right, edges)


def petersen() -> ConflictGraph:
    return ConflictGraph.from_networkx(nx.petersen_graph())


def grotzsch() -> ConflictGraph:
    """Grötzsch graph: the Mycielskian of C5 (11 vertices, triangle-free, chi = 4)."""
    return ConflictGraph.from_networkx(nx.mycielskian(nx.cycle_graph(5)))


def wheel(rim: int) -> ConflictGraph:
    return ConflictGraph.from_networkx(nx.wheel_graph(rim + 1))


def hypercube(dimension: int) -> ConflictGraph:
    return ConflictGraph.from_networkx(nx.hypercube_graph(dimension))


def grid(rows: int, cols: int) -> ConflictGraph:
    return ConflictGraph.from_networkx(nx.grid_2d_graph(rows, cols))


ALL_VALIDITY_CASES = {
    "empty": empty(),
    "single": single(),
    "edgeless5": edgeless(5),
    "complete6": complete(6),
    "path7": path(7),
    "cycle5": cycle(5),
    "cycle6": cycle(6),
    "cycle9": cycle(9),
    "star6": star(6),
    "k33": complete_bipartite(3, 3),
    "petersen": petersen(),
    "grotzsch": grotzsch(),
    "wheel6": wheel(6),
    "hypercube3": hypercube(3),
    "grid3x4": grid(3, 4),
}
