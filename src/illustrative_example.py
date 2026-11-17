"""The small worked example used in the manuscript.

Seven courses and five students, deliberately small enough that the reader can
verify every edge and both colorings by hand.  The conflict graph has nine
edges, contains the triangle {C5, C6, C7} (so the chromatic number is at least
three) and DSATUR colours it with exactly three slots, while Welsh--Powell
needs four.

The example is illustrative only: it is not part of the benchmark, and it was
selected to expose the difference between the two orderings, not to estimate
their relative performance.
"""

from __future__ import annotations

from graph_model import ConflictGraph

#: ``enrolments[i]`` is the set of (0-based) course indices taken by student i+1.
ENROLMENTS: tuple[tuple[int, ...], ...] = (
    (0, 3),
    (1, 2),
    (0, 4, 5),
    (1, 5, 6),
    (4, 6),
)

N_COURSES = 7


def example_graph() -> ConflictGraph:
    """Derive the conflict graph induced by the enrolled-student sets."""
    pairs: set[tuple[int, int]] = set()
    for courses in ENROLMENTS:
        ordered = sorted(courses)
        for i, u in enumerate(ordered):
            for v in ordered[i + 1 :]:
                pairs.add((u, v))
    return ConflictGraph.from_edges(N_COURSES, pairs)


def example_table() -> list[tuple[str, list[str]]]:
    """Human-readable enrolment table, with 1-based course labels."""
    return [
        (f"S{index}", [f"C{course + 1}" for course in courses])
        for index, courses in enumerate(ENROLMENTS, start=1)
    ]
