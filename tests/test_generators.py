"""Tests for the reproducible graph and enrolment generators."""

from __future__ import annotations

import networkx as nx
import pytest

from enrollment_generator import (
    REPETITIONS_PER_SCENARIO,
    SCENARIOS,
    generate_enrollment_instance,
    generate_experiment_b,
)
from graph_generator import (
    erdos_renyi,
    experiment_a_configs,
    generate_experiment_a,
    instance_seed,
)


# ----------------------------------------------------------------------
# Erdős--Rényi generator
# ----------------------------------------------------------------------
def test_same_seed_gives_identical_graph():
    a = erdos_renyi(60, 0.35, 123456)
    b = erdos_renyi(60, 0.35, 123456)
    assert a.adjacency == b.adjacency


def test_different_seeds_give_different_graphs():
    a = erdos_renyi(60, 0.35, 1)
    b = erdos_renyi(60, 0.35, 2)
    assert a.adjacency != b.adjacency


def test_p_zero_gives_edgeless_graph():
    graph = erdos_renyi(30, 0.0, 7)
    assert graph.m == 0
    assert graph.max_degree() == 0


def test_p_one_gives_complete_graph():
    graph = erdos_renyi(25, 1.0, 7)
    assert graph.m == 25 * 24 // 2
    assert graph.density() == pytest.approx(1.0)


@pytest.mark.parametrize("p", [0.1, 0.3, 0.5, 0.7])
def test_observed_density_tracks_probability(p):
    densities = [erdos_renyi(200, p, seed).density() for seed in range(8)]
    mean = sum(densities) / len(densities)
    assert abs(mean - p) < 0.03


def test_generator_matches_networkx_statistics():
    graph = erdos_renyi(80, 0.5, instance_seed(80, 500, 4))
    reference = nx.gnp_random_graph(80, 0.5, seed=instance_seed(80, 500, 4))
    # The samplers differ, but both must produce graphs with the same order and
    # a comparable expected edge count.
    assert graph.n == reference.number_of_nodes()
    assert abs(graph.m - reference.number_of_edges()) < 0.25 * reference.number_of_edges()


def test_instance_seed_is_stable_and_distinct():
    first = instance_seed(20, 100, 0)
    second = instance_seed(20, 100, 0)
    third = instance_seed(20, 100, 1)
    assert first == second
    assert first != third
    assert 0 <= first < 2**31 - 1


def test_experiment_a_grid_size():
    configs = experiment_a_configs()
    assert len(configs) == 20
    assert [c.n for c in configs[:4]] == [20, 20, 20, 20]
    assert sum(c.repetitions for c in configs) == 600


def test_experiment_a_materialises_600_instances():
    instances = generate_experiment_a()
    assert len(instances) == 600
    digests = {tuple(graph.edges()) for _, _, graph in instances}
    assert len(digests) > 550  # essentially all instances are distinct


# ----------------------------------------------------------------------
# Enrolment generator
# ----------------------------------------------------------------------
def test_enrollment_generation_is_deterministic():
    scenario = SCENARIOS[0]
    a = generate_enrollment_instance(scenario, 424242)
    b = generate_enrollment_instance(scenario, 424242)
    assert a.graph.adjacency == b.graph.adjacency
    assert a.enrollments == b.enrollments


def test_edges_are_exactly_the_shared_enrollment_pairs():
    scenario = SCENARIOS[1]
    instance = generate_enrollment_instance(scenario, 98765)
    expected: set[tuple[int, int]] = set()
    for courses in instance.enrollments:
        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                expected.add((min(courses[i], courses[j]), max(courses[i], courses[j])))
    assert set(instance.graph.edges()) == expected


def test_no_edge_without_shared_student():
    scenario = SCENARIOS[2]
    instance = generate_enrollment_instance(scenario, 555)
    holders: dict[int, set[int]] = {}
    for student, courses in enumerate(instance.enrollments):
        for course in courses:
            holders.setdefault(course, set()).add(student)
    for u, v in instance.graph.edges():
        assert holders.get(u, set()) & holders.get(v, set())


def test_enrollment_instances_have_plausible_structure():
    instances = generate_experiment_b()
    assert len(instances) == len(SCENARIOS) * REPETITIONS_PER_SCENARIO == 90
    for instance in instances:
        assert instance.graph.n == instance.scenario.n_courses
        assert instance.graph.m > 0
        assert 0.0 < instance.graph.density() < 1.0
        assert instance.graph.isolated_vertices() >= 0
        assert instance.mean_courses_per_student >= instance.scenario.min_courses - 1e-9


def test_enrollment_density_increases_with_program_size():
    instances = generate_experiment_b()
    by_scenario: dict[str, list[float]] = {}
    for instance in instances:
        by_scenario.setdefault(instance.scenario.name, []).append(instance.graph.density())
    small = sum(by_scenario["small_program"]) / len(by_scenario["small_program"])
    large = sum(by_scenario["large_program"]) / len(by_scenario["large_program"])
    assert large > small
