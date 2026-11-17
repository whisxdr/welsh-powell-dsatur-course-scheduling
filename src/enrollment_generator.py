"""Simulated university course-enrolment scenarios (Experiment B).

The generator builds **synthetic** student-course enrolments and then derives a
conflict graph from shared enrolment.  Nothing here reproduces real institutional
records: every course name, cohort and enrolment is a simulation artefact.

Model
-----
1. ``n_courses`` courses are partitioned into ``n_semesters`` curriculum
   semesters.
2. Each course receives a popularity weight drawn from a Dirichlet
   distribution, so a few courses behave as high-demand "service" courses.
3. Each student belongs to a cohort that opens a window of ``window``
   consecutive semesters and enrols in ``k`` courses inside that window,
   with ``k`` drawn uniformly from ``[min_courses, max_courses]`` and courses
   sampled without replacement proportional to popularity.
4. Two courses are adjacent iff at least one student enrolled in both.

Step 4 is the definition used in the manuscript:
``E = {{u, v} : S_u ∩ S_v ≠ ∅}``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from graph_generator import instance_seed
from graph_model import ConflictGraph


@dataclass(frozen=True, slots=True)
class EnrollmentScenario:
    """Parameters of one synthetic curriculum."""

    name: str
    n_courses: int
    n_students: int
    n_semesters: int
    min_courses: int
    max_courses: int
    window: int = 3
    concentration: float = 0.8

    @property
    def label(self) -> str:
        return self.name


@dataclass(slots=True)
class EnrollmentInstance:
    """One generated instance plus its provenance."""

    scenario: EnrollmentScenario
    seed: int
    graph: ConflictGraph
    enrollments: list[list[int]] = field(default_factory=list)
    course_semester: list[int] = field(default_factory=list)
    n_edges: int = 0
    mean_courses_per_student: float = 0.0

    def metadata(self) -> dict[str, object]:
        return {
            "scenario": self.scenario.name,
            "n_courses": self.scenario.n_courses,
            "n_students": self.scenario.n_students,
            "n_semesters": self.scenario.n_semesters,
            "min_courses": self.scenario.min_courses,
            "max_courses": self.scenario.max_courses,
            "window": self.scenario.window,
            "concentration": self.scenario.concentration,
            "seed": self.seed,
            "n_edges": self.graph.m,
            "density": round(self.graph.density(), 6),
            "mean_degree": round(2.0 * self.graph.m / self.graph.n, 4) if self.graph.n else 0.0,
            "max_degree": self.graph.max_degree(),
            "isolated_courses": self.graph.isolated_vertices(),
            "mean_courses_per_student": round(self.mean_courses_per_student, 4),
        }


SCENARIOS: tuple[EnrollmentScenario, ...] = (
    EnrollmentScenario(
        name="small_program",
        n_courses=24,
        n_students=90,
        n_semesters=8,
        min_courses=4,
        max_courses=6,
        window=2,
    ),
    EnrollmentScenario(
        name="medium_program",
        n_courses=40,
        n_students=300,
        n_semesters=8,
        min_courses=5,
        max_courses=7,
        window=3,
    ),
    EnrollmentScenario(
        name="large_program",
        n_courses=60,
        n_students=900,
        n_semesters=8,
        min_courses=5,
        max_courses=8,
        window=4,
    ),
)

REPETITIONS_PER_SCENARIO = 30


def generate_enrollment_instance(scenario: EnrollmentScenario, seed: int) -> EnrollmentInstance:
    """Draw one synthetic enrolment table and derive its conflict graph."""
    rng = np.random.default_rng(seed)
    n_courses = scenario.n_courses
    n_semesters = scenario.n_semesters

    popularity = rng.dirichlet(np.full(n_courses, scenario.concentration))
    course_semester = [min(n_semesters - 1, i * n_semesters // n_courses) for i in range(n_courses)]
    semester_members: list[list[int]] = [[] for _ in range(n_semesters)]
    for course, semester in enumerate(course_semester):
        semester_members[semester].append(course)

    unique_pairs: set[tuple[int, int]] = set()
    enrollments: list[list[int]] = []
    total_courses_taken = 0

    for _ in range(scenario.n_students):
        start = int(rng.integers(0, max(1, n_semesters - scenario.window + 1)))
        window_courses = [
            c
            for s in range(start, min(n_semesters, start + scenario.window))
            for c in semester_members[s]
        ]
        if len(window_courses) < 2:
            continue
        k = int(rng.integers(scenario.min_courses, scenario.max_courses + 1))
        k = min(k, len(window_courses))
        weights = popularity[window_courses]
        weights = weights / weights.sum()
        chosen = rng.choice(len(window_courses), size=k, replace=False, p=weights)
        courses = sorted(window_courses[i] for i in chosen)
        enrollments.append(courses)
        total_courses_taken += len(courses)
        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                unique_pairs.add((courses[i], courses[j]))

    graph = ConflictGraph.from_edges(n_courses, unique_pairs)
    mean_courses = total_courses_taken / len(enrollments) if enrollments else 0.0
    return EnrollmentInstance(
        scenario=scenario,
        seed=seed,
        graph=graph,
        enrollments=enrollments,
        course_semester=course_semester,
        n_edges=graph.m,
        mean_courses_per_student=mean_courses,
    )


def generate_experiment_b(
    scenarios: tuple[EnrollmentScenario, ...] = SCENARIOS,
    repetitions: int = REPETITIONS_PER_SCENARIO,
) -> list[EnrollmentInstance]:
    """Materialise ``len(scenarios) x repetitions`` enrolment instances."""
    instances: list[EnrollmentInstance] = []
    for index, scenario in enumerate(scenarios):
        for rep in range(repetitions):
            seed = instance_seed(7_000_000 + index, scenario.n_courses, rep)
            instances.append(generate_enrollment_instance(scenario, seed))
    return instances
