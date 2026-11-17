"""Run the whole reproducible pipeline in order.

    python run_all.py                 # everything, then freeze and verify
    python run_all.py --skip-benchmark  # reuse existing results, re-freeze

The LaTeX build is separate because it needs a TeX installation; see README.md.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(label: str, command: list[str]) -> None:
    print(f"\n=== {label} ===")
    print("$ " + " ".join(command))
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(f"step failed: {label} (exit {result.returncode})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-benchmark", action="store_true")
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--version", default="v2")
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="re-freeze the snapshot after the run (requires --force if it exists)",
    )
    parser.add_argument("--force", action="store_true", help="overwrite the frozen snapshot")
    args = parser.parse_args()

    python = sys.executable
    run("unit tests", [python, "-m", "pytest"])
    run("lint", [python, "-m", "ruff", "check", "src", "tests"])
    if not args.skip_benchmark:
        run("benchmark", [python, "src/benchmark.py", "--repeats", str(args.repeats)])
    run("structural audit", [python, "src/graph_audit.py"])
    run("exact optimality study", [python, "src/optimality_study.py"])
    run("real-world case study", [python, "src/real_case_study.py"])
    run("tables", [python, "src/make_tables.py"])
    run("figures", [python, "src/visualization.py"])
    if args.freeze:
        command = [python, "src/freeze_results.py", "--version", args.version]
        if args.force:
            command.append("--force")
        run("freeze results", command)
    run("claim verification", [python, "src/verify_claims.py", "--version", args.version])
    print("\nAll pipeline steps completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
