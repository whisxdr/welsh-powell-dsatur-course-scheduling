"""Reproducible synthetic graph generators.

Experiment A uses the Erdős--Rényi ``G(n, p)`` model.  The sampler draws one
uniform variate per unordered vertex pair from a NumPy ``PCG64`` generator, so
an instance is fully determined by ``(n, p, seed)`` and is bit-reproducible on
any platform with the same NumPy major version.

Reference for the model:
P. Erdős and A. Rényi, "On the evolution of random graphs," *Publications of
the Mathematical Institute of the Hungarian Academy of Sciences*, vol. 5,
pp. 17--61, 1960.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from graph_model import ConflictGraph


@dataclass(frozen=True, slots=True)
class RandomGraphConfig:
    """One cell of the ``|V| x p`` experimental grid."""

    n: int
    p: float
    repetitions: int

    @property
    def label(self) -> str:
        return f"n{self.n}_p{self.p:.1f}"


def instance_seed(*components: int) -> int:
    """Derive a stable 63-bit seed from integer components via ``SeedSequence``."""
    state = np.random.SeedSequence(list(components)).generate_state(1, dtype=np.uint32)
    return int(state[0]) % (2**31 - 1)


def erdos_renyi(n: int, p: float, seed: int) -> ConflictGraph:
    """Sample an undirected ``G(n, p)`` graph.

    Each of the ``n(n-1)/2`` unordered pairs is present independently with
    probability ``p``.  Edges are drawn in lexicographic order from a single
    uniform stream, which keeps the procedure deterministic.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must lie in [0, 1]")
    rng = np.random.default_rng(seed)
    rows, cols = np.triu_indices(n, k=1)
    draws = rng.random(rows.size)
    keep = draws < p
    edges = list(zip(rows[keep].tolist(), cols[keep].tolist(), strict=True))
    return ConflictGraph.from_edges(n, edges)


def experiment_a_configs(
    sizes: tuple[int, ...] = (20, 40, 60, 80, 100),
    probabilities: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7),
    repetitions: int = 30,
) -> list[RandomGraphConfig]:
    """The 5 x 4 grid of Experiment A, with 30 paired repetitions per cell."""
    return [
        RandomGraphConfig(n=n, p=p, repetitions=repetitions) for n in sizes for p in probabilities
    ]


def generate_experiment_a(
    configs: list[RandomGraphConfig] | None = None,
) -> list[tuple[RandomGraphConfig, int, ConflictGraph]]:
    """Materialise every Experiment A instance as ``(config, seed, graph)``."""
    configs = experiment_a_configs() if configs is None else configs
    out: list[tuple[RandomGraphConfig, int, ConflictGraph]] = []
    for config in configs:
        for rep in range(config.repetitions):
            seed = instance_seed(config.n, int(round(config.p * 1000)), rep)
            out.append((config, seed, erdos_renyi(config.n, config.p, seed)))
    return out
