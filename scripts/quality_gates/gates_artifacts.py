"""High-tier required artifact presence checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.config import HIGH_REQUIRED_FILES, normalized_strictness_level
from scripts.quality_gates.jsonutil import read_json
from scripts.quality_gates.readers_cloc_docs import interrogate_coverage
from scripts.quality_gates.readers_py_coverage import pylint_score

RowList = list[dict[str, Any]]


SPECIAL_TEXT_CHECKS: dict[str, tuple[Any, str]] = {
    "pylint_score.txt": (pylint_score, "pylint_score.txt missing rated at X/10 line"),
    "interrogate.txt": (interrogate_coverage, "interrogate.txt missing parseable coverage line"),
}

JSON_SHAPES: dict[str, tuple[type[Any] | tuple[type[Any], ...], str]] = {
    "cloc.json": (dict, "cloc.json must be a JSON object"),
    "coverage.json": (dict, "coverage.json must be a JSON object"),
    "pylint.json": (list, "pylint.json must be a JSON array"),
    "ruff.json": ((list, dict), "ruff.json must be array or object"),
    "gitleaks.json": (list, "gitleaks.json must be a JSON array"),
    "bandit.json": (dict, "bandit.json must be a JSON object"),
    "pip_audit.json": (list, "pip_audit.json must be a JSON array"),
    "grype.json": (dict, "grype.json must be a JSON object"),
    "radon_cc.json": (dict, "radon_cc.json must be a JSON object"),
    "radon_mi.json": (dict, "radon_mi.json must be a JSON object"),
}

JSON_REQUIRED_PATHS: dict[str, list[tuple[tuple[str, ...], str]]] = {
    "bandit.json": [(("results",), "bandit.json missing results")],
    "cloc.json": [(("Python",), "cloc.json missing Python stats")],
    "coverage.json": [
        (("totals",), "coverage.json missing totals"),
        (("totals", "percent_covered"), "coverage.json missing percent_covered"),
    ],
}


def _json_path_present(data: Any, path: tuple[str, ...]) -> bool:
    """Return whether a nested key-path exists and ends in a non-None value."""
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return False
        cur = cur[key]
    return cur is not None


def _json_artifact_substance_check(path: Path, name: str) -> tuple[bool, str]:
    """Validate JSON artifact shape and required nested paths when configured."""
    data = read_json(path)
    if data is None:
        return False, f"{name} is missing or invalid JSON"
    expected = JSON_SHAPES.get(name)
    if expected and not isinstance(data, expected[0]):
        return False, expected[1]
    for req_path, message in JSON_REQUIRED_PATHS.get(name, []):
        if not _json_path_present(data, req_path):
            return False, message
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
    ok = path.is_file() and path.stat().st_size > 0
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
