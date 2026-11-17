"""Core graph model shared by both coloring heuristics.

The model is deliberately independent of NetworkX so that the two heuristics
operate on exactly the same immutable input representation.  NetworkX is used
only for independent cross-validation in the test suite.

Vertices are the integers ``0 .. n-1``.  Colors are the integers
``0 .. k-1``; a color of ``-1`` means "not yet colored".
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass


class GraphModelError(ValueError):
    """Raised when a graph or a coloring violates the model invariants."""


@dataclass(frozen=True, slots=True)
class ConflictGraph:
    """Undirected simple graph on ``n`` vertices.

    Attributes
    ----------
    n:
        Number of vertices.
    adjacency:
        ``adjacency[v]`` is the ascending tuple of neighbours of ``v``.
    """

    n: int
    adjacency: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        if self.n < 0:
            raise GraphModelError("n must be non-negative")
        if len(self.adjacency) != self.n:
            raise GraphModelError("len(adjacency) must equal n")
        for v, neighbours in enumerate(self.adjacency):
            if len(set(neighbours)) != len(neighbours):
                raise GraphModelError(f"duplicate neighbour at vertex {v}")
            if tuple(sorted(neighbours)) != tuple(neighbours):
                raise GraphModelError(f"neighbours of vertex {v} must be sorted")
            for u in neighbours:
                if u == v:
                    raise GraphModelError(f"self-loop at vertex {v}")
                if not 0 <= u < self.n:
                    raise GraphModelError(f"neighbour {u} of vertex {v} out of range")
                if v not in self.adjacency[u]:
                    raise GraphModelError(f"asymmetric edge ({v}, {u})")

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------
    @classmethod
    def from_edges(cls, n: int, edges: Iterable[tuple[int, int]]) -> ConflictGraph:
        """Build a graph from an undirected edge list (duplicates tolerated)."""
        if n < 0:
            raise GraphModelError("n must be non-negative")
        buckets: list[set[int]] = [set() for _ in range(n)]
        for u, v in edges:
            if not (0 <= u < n and 0 <= v < n):
                raise GraphModelError(f"edge ({u}, {v}) out of range for n={n}")
            if u == v:
                raise GraphModelError(f"self-loop at vertex {u}")
            buckets[u].add(v)
            buckets[v].add(u)
        return cls(n, tuple(tuple(sorted(b)) for b in buckets))

    @classmethod
    def from_networkx(cls, graph: object) -> ConflictGraph:
        """Convert a ``networkx.Graph`` into the research representation."""
        nodes = list(graph.nodes())  # type: ignore[attr-defined]
        index = {node: i for i, node in enumerate(nodes)}
        edges = [(index[u], index[v]) for u, v in graph.edges()]  # type: ignore[attr-defined]
        return cls.from_edges(len(nodes), edges)

    # ------------------------------------------------------------------
    # Basic queries
    # ------------------------------------------------------------------
    def degree(self, v: int) -> int:
        return len(self.adjacency[v])

    def neighbours(self, v: int) -> tuple[int, ...]:
        return self.adjacency[v]

    @property
    def m(self) -> int:
        """Number of edges."""
        return sum(len(a) for a in self.adjacency) // 2

    @property
    def degrees(self) -> tuple[int, ...]:
        return tuple(len(a) for a in self.adjacency)

    def edges(self) -> list[tuple[int, int]]:
        return [(u, v) for u in range(self.n) for v in self.adjacency[u] if u < v]

    def density(self) -> float:
        """Graph density ``2|E| / (|V|(|V|-1))``; ``0.0`` for ``|V| < 2``."""
        if self.n < 2:
            return 0.0
        return 2.0 * self.m / (self.n * (self.n - 1))

    def max_degree(self) -> int:
        return max((len(a) for a in self.adjacency), default=0)

    def isolated_vertices(self) -> int:
        return sum(1 for a in self.adjacency if not a)

    # ------------------------------------------------------------------
    # Coloring validation
    # ------------------------------------------------------------------
    def check_coloring(self, colors: Sequence[int]) -> None:
        """Raise :class:`GraphModelError` unless ``colors`` is a valid coloring."""
        if len(colors) != self.n:
            raise GraphModelError(f"expected {self.n} colors, got {len(colors)}")
        for v, c in enumerate(colors):
            if not isinstance(c, int) or c < 0:
                raise GraphModelError(f"vertex {v} has invalid color {c!r}")
        for u in range(self.n):
            cu = colors[u]
            for v in self.adjacency[u]:
                if u < v and colors[v] == cu:
                    raise GraphModelError(f"conflict on edge ({u}, {v}): both color {cu}")

    def is_valid_coloring(self, colors: Sequence[int]) -> bool:
        try:
            self.check_coloring(colors)
        except GraphModelError:
            return False
        return True

    def count_conflicts(self, colors: Sequence[int]) -> int:
        """Number of monochromatic edges ``C(c)``."""
        return sum(
            1 for u in range(self.n) for v in self.adjacency[u] if u < v and colors[u] == colors[v]
        )

    @staticmethod
    def colors_used(colors: Sequence[int]) -> int:
        """Number of distinct colors actually used (``0`` for an empty graph)."""
        used = {c for c in colors if c >= 0}
        return len(used)


@dataclass(frozen=True, slots=True)
class ColoringResult:
    """Outcome of one heuristic run on one graph instance."""

    algorithm: str
    colors: tuple[int, ...]
    num_colors: int
    elapsed_seconds: float
    order: tuple[int, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "algorithm": self.algorithm,
            "num_colors": self.num_colors,
            "elapsed_seconds": self.elapsed_seconds,
            "colors": list(self.colors),
            "order": list(self.order),
        }


def validate_result(graph: ConflictGraph, result: ColoringResult) -> None:
    """Check that a result is a valid coloring whose color count is consistent."""
    graph.check_coloring(result.colors)
    used = graph.colors_used(result.colors)
    if used != result.num_colors:
        raise GraphModelError(
            f"{result.algorithm}: reported {result.num_colors} colors but used {used}"
        )
    if result.num_colors > 0 and max(result.colors) != result.num_colors - 1:
        raise GraphModelError(f"{result.algorithm}: colors are not normalized to 0..k-1")
