"""High-tier required artifact presence checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.artifact_rules import first_missing_required_path, json_shape_error
from scripts.quality_gates.config import HIGH_REQUIRED_FILES, normalized_strictness_level
from scripts.quality_gates.jsonutil import read_json
from scripts.quality_gates.readers_cloc_docs import interrogate_coverage, pydoclint_txt_present
from scripts.quality_gates.readers_py_coverage import pylint_score

RowList = list[dict[str, Any]]

# High tier: these files may be size 0 when the tool legitimately produced no text (e.g. zero pydoclint hits).
_ALLOW_EMPTY_HIGH_ARTIFACTS: frozenset[str] = frozenset({"pydoclint.txt"})


SPECIAL_TEXT_CHECKS: dict[str, tuple[Any, str]] = {
    "pylint_score.txt": (pylint_score, "pylint_score.txt missing rated at X/10 line"),
    "interrogate.txt": (interrogate_coverage, "interrogate.txt missing parseable coverage line"),
    "pydoclint.txt": (pydoclint_txt_present, "pydoclint.txt missing"),
}


def _json_artifact_substance_check(path: Path, name: str) -> tuple[bool, str]:
    """Validate JSON artifact shape and required nested paths when configured."""
    data = read_json(path)
    if data is None:
        return False, f"{name} is missing or invalid JSON"
    shape_error = json_shape_error(data, name)
    if shape_error is not None:
        return False, shape_error
    required_path_error = first_missing_required_path(data, name)
    if required_path_error is not None:
        return False, required_path_error
    return True, ""


def high_artifact_substance_ok(root: Path, name: str) -> tuple[bool, str]:
    """Validate High-tier artifact content (not just non-empty file)."""
    path = root / name
    special = SPECIAL_TEXT_CHECKS.get(name)
    if special:
        reader, message = special
        return (True, "") if reader(root) is not None else (False, message)
    return _json_artifact_substance_check(path, name)


def high_artifact_gate_row(root: Path, name: str) -> tuple[RowList, bool]:
    """One artifact presence row and whether it is OK (including substance for High)."""
    path = root / name
    ok = path.is_file() and (path.stat().st_size > 0 or name in _ALLOW_EMPTY_HIGH_ARTIFACTS)
    actual = "present" if ok else "missing or empty"
    if ok:
        sub_ok, detail = high_artifact_substance_ok(root, name)
        if not sub_ok:
            ok = False
            actual = detail
    row = {
        "gate": f"Required artifact ({name})",
        "actual": actual,
        "required": "must exist for High",
        "ok": ok,
    }
    return [row], ok


def enforce_high_artifact_presence(
    root: Path,
    strictness: str,
) -> tuple[RowList, list[str]]:
    """Fail High runs if required tool outputs are missing (avoids silent skips)."""
    if normalized_strictness_level(strictness) != "High":
        return [], []
    rows: RowList = []
    failures: list[str] = []
    for name in HIGH_REQUIRED_FILES:
        row_list, ok = high_artifact_gate_row(root, name)
        rows.extend(row_list)
        if not ok:
            failures.append(f"missing artifact: {name}")
    return rows, failures
