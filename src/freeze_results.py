"""Freeze the benchmark artefacts that the manuscript cites.

Runtime measurements drift between runs, so the manuscript must be tied to one
immutable snapshot rather than to whatever ``results/`` currently holds.  This
script copies the cited artefacts into ``results/frozen/<version>/`` and writes a
manifest of SHA-256 digests.  ``verify_claims.py`` reads only from the frozen
snapshot and refuses to run if a digest does not match.

    python src/freeze_results.py --version v1
    python src/freeze_results.py --verify --version v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

FROZEN_FILES = (
    "raw_results.csv",
    "statistics.json",
    "key_numbers.json",
    "environment.json",
    "run_manifest.json",
    "optimality.csv",
    "optimality.json",
    "optimality_summary.csv",
    "real_case_study.json",
    "graph_audit.csv",
    "graph_audit_summary.csv",
    "real_dataset.json",
)

MANIFEST_NAME = "FROZEN_MANIFEST.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(results: Path, version: str, force: bool = False) -> dict[str, object]:
    target = results / "frozen" / version
    manifest_path = target / MANIFEST_NAME
    if manifest_path.exists() and not force:
        raise FileExistsError(
            f"frozen snapshot {version} already exists at {target}. "
            "Use --force to overwrite it, or choose a new --version."
        )
    target.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, object]] = {}
    for name in FROZEN_FILES:
        source = results / name
        if not source.exists():
            raise FileNotFoundError(f"cannot freeze missing artefact: {source}")
        shutil.copy2(source, target / name)
        files[name] = {"sha256": sha256(target / name), "bytes": (target / name).stat().st_size}
    manifest = {
        "version": version,
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "note": (
            "Immutable snapshot of the artefacts cited by paper/main.tex. "
            "verify_claims.py reads only this directory."
        ),
        "files": files,
    }
    (target / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def verify(results: Path, version: str) -> dict[str, object]:
    target = results / "frozen" / version
    manifest_path = target / MANIFEST_NAME
    if not manifest_path.exists():
        raise FileNotFoundError(f"no frozen manifest at {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems: list[str] = []
    for name, record in manifest["files"].items():
        path = target / name
        if not path.exists():
            problems.append(f"{name}: missing")
        elif sha256(path) != record["sha256"]:
            problems.append(f"{name}: digest mismatch")
    if problems:
        raise RuntimeError("frozen snapshot is corrupt:\n  " + "\n  ".join(problems))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--version", default="v1")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--force", action="store_true", help="overwrite an existing snapshot")
    args = parser.parse_args(argv)

    if args.verify:
        manifest = verify(args.results, args.version)
        print(f"frozen snapshot {args.version} verified: {len(manifest['files'])} files")
        return 0

    manifest = freeze(args.results, args.version, force=args.force)
    print(f"frozen {len(manifest['files'])} artefacts into results/frozen/{args.version}")
    for name, record in manifest["files"].items():
        print(f"  {name:28s} {record['sha256'][:16]}  {record['bytes']:>8} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
