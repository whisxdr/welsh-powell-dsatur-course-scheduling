"""Tests for the frozen-results mechanism and the Holm adjustment."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis import holm_adjust
from freeze_results import FROZEN_FILES, freeze, verify


def test_holm_matches_worked_example():
    # Holm step-down on p = (0.01, 0.02, 0.03, 0.04) with m = 4:
    # raw adjusted = (0.04, 0.06, 0.06, 0.04); enforcing monotonicity gives
    # (0.04, 0.06, 0.06, 0.06).
    adjusted = holm_adjust({"a": 0.01, "b": 0.02, "c": 0.03, "d": 0.04})
    assert adjusted["a"] == pytest.approx(0.04)
    assert adjusted["b"] == pytest.approx(0.06)
    assert adjusted["c"] == pytest.approx(0.06)
    assert adjusted["d"] == pytest.approx(0.06)


def test_holm_is_monotone_and_bounded():
    adjusted = holm_adjust({"a": 0.001, "b": 0.2, "c": 0.9})
    values = [adjusted[key] for key in ("a", "b", "c")]
    assert all(0.0 <= value <= 1.0 for value in values)
    assert values[0] <= values[1] <= values[2]


def test_holm_never_decreases_a_p_value():
    raw = {"a": 0.5, "b": 0.5}
    adjusted = holm_adjust(raw)
    assert all(adjusted[key] >= raw[key] for key in raw)


def test_holm_handles_empty_input():
    assert holm_adjust({}) == {}


def test_freeze_and_verify_roundtrip(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    for name in FROZEN_FILES:
        (results / name).write_text(f"content of {name}", encoding="utf-8")

    manifest = freeze(results, "vtest")
    assert set(manifest["files"]) == set(FROZEN_FILES)
    assert (results / "frozen" / "vtest" / "FROZEN_MANIFEST.json").exists()

    verified = verify(results, "vtest")
    assert verified["version"] == "vtest"


def test_verify_detects_tampering(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    for name in FROZEN_FILES:
        (results / name).write_text(f"content of {name}", encoding="utf-8")
    freeze(results, "vtest")

    target = results / "frozen" / "vtest" / FROZEN_FILES[0]
    target.write_text("tampered", encoding="utf-8")
    with pytest.raises(RuntimeError, match="digest mismatch"):
        verify(results, "vtest")


def test_freeze_refuses_missing_artefact(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    with pytest.raises(FileNotFoundError):
        freeze(results, "vtest")


def test_freeze_refuses_to_overwrite_without_force(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    for name in FROZEN_FILES:
        (results / name).write_text(f"content of {name}", encoding="utf-8")
    freeze(results, "vtest")
    with pytest.raises(FileExistsError):
        freeze(results, "vtest")
    # An explicit force is allowed.
    assert freeze(results, "vtest", force=True)["version"] == "vtest"


def test_frozen_snapshot_in_repository_is_intact():
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "results" / "frozen" / "v1" / "FROZEN_MANIFEST.json"
    if not manifest_path.exists():
        pytest.skip("no frozen snapshot in this checkout")
    manifest = verify(root / "results", "v1")
    assert manifest["version"] == "v1"
    assert len(manifest["files"]) == len(FROZEN_FILES)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["files"] == manifest["files"]
