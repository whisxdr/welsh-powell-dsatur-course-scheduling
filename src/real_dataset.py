"""Loader for the one real-world instance used in the study.

Source
------
P. C. Le, "Dataset for ETP," Zenodo, 2025. doi:10.5281/zenodo.17129990.
Licence: CC BY 4.0.  The archive contains anonymised student-subject
registration records released for examination timetabling research.

What is used here
-----------------
``StudentSubjectUnique.csv`` is a binary student x subject matrix (975 students,
156 subjects) with duplicate registrations removed.  Two subjects are adjacent
when at least one student registered for both, which is exactly the conflict
definition of the manuscript.  No student identifier, name, grade, or any other
personal attribute is read: only the incidence matrix is used.

What this dataset is not
------------------------
It is a single institution's examination-registration snapshot, not a course
timetable.  It carries no lecturer, room, or time-slot information, so it cannot
support lecturer-conflict edges or a full timetabling evaluation.  It is used to
test external validity of the colour-count comparison, nothing more.

Integrity
---------
The SHA-256 of the source file is pinned below.  ``load_real_dataset`` refuses to
proceed if the file on disk differs, so a silently modified dataset cannot enter
the results.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from graph_model import ConflictGraph

SOURCE_DOI = "10.5281/zenodo.17129990"
SOURCE_LICENSE = "CC BY 4.0"
SOURCE_CITATION = 'P. C. Le, "Dataset for ETP," Zenodo, 2025, doi:10.5281/zenodo.17129990.'
EXPECTED_SHA256 = "b1833dc0f3112c254658033dd6cc3f6b858c4ea78a5fd1b163efd7c5fecba829"
DEFAULT_PATH = Path("data/external/StudentSubjectUnique.csv")


class DatasetIntegrityError(RuntimeError):
    """Raised when the on-disk dataset does not match the pinned digest."""


@dataclass(frozen=True, slots=True)
class RealDataset:
    """The real instance plus provenance."""

    name: str
    graph: ConflictGraph
    n_students: int
    n_courses: int
    registrations: int
    sha256: str
    source_doi: str = SOURCE_DOI
    license: str = SOURCE_LICENSE

    def metadata(self) -> dict[str, object]:
        return {
            "name": self.name,
            "n_students": self.n_students,
            "n_courses": self.n_courses,
            "registrations": self.registrations,
            "n_edges": self.graph.m,
            "density": round(self.graph.density(), 6),
            "max_degree": self.graph.max_degree(),
            "isolated_courses": self.graph.isolated_vertices(),
            "sha256": self.sha256,
            "source_doi": self.source_doi,
            "license": self.license,
        }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_real_dataset(path: Path | str = DEFAULT_PATH) -> RealDataset:
    """Read the incidence matrix and derive the conflict graph."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Download StudentSubjectUnique.csv from "
            f"https://doi.org/{SOURCE_DOI} (licence {SOURCE_LICENSE})."
        )
    digest = _sha256(path)
    if digest != EXPECTED_SHA256:
        raise DatasetIntegrityError(
            f"{path} has SHA-256 {digest}, expected {EXPECTED_SHA256}. "
            "Refusing to use a dataset that differs from the pinned version."
        )

    matrix = np.loadtxt(path, delimiter=",", dtype=np.int8)
    if matrix.ndim != 2:
        raise ValueError("expected a two-dimensional incidence matrix")
    if not np.isin(matrix, (0, 1)).all():
        raise ValueError("incidence matrix must be binary")

    n_students, n_courses = matrix.shape
    # Co-registration counts: C[i, j] = number of students taking both i and j.
    counts = matrix.T.astype(np.int32) @ matrix.astype(np.int32)
    np.fill_diagonal(counts, 0)
    edges = [(int(u), int(v)) for u, v in np.argwhere(np.triu(counts, 1) > 0)]
    graph = ConflictGraph.from_edges(n_courses, edges)

    return RealDataset(
        name="etp_registration",
        graph=graph,
        n_students=int(n_students),
        n_courses=int(n_courses),
        registrations=int(matrix.sum()),
        sha256=digest,
    )
