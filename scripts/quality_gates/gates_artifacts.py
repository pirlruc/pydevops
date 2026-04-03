"""High-tier required artifact presence checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.config import HIGH_REQUIRED_FILES, normalized_strictness_level
from scripts.quality_gates.jsonutil import read_json
from scripts.quality_gates.readers_cloc_docs import interrogate_coverage
from scripts.quality_gates.readers_py_coverage import pylint_score

RowList = list[dict[str, Any]]


def _json_validator_list(data: Any, name: str) -> tuple[bool, str]:
    if not isinstance(data, list):
        return False, f"{name} must be a JSON array"
    return True, ""


def _json_validator_ruff(data: Any, _name: str) -> tuple[bool, str]:
    if not isinstance(data, (list, dict)):
        return False, "ruff.json must be array or object"
    return True, ""


def _json_validator_dict(data: Any, name: str) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, f"{name} must be a JSON object"
    return True, ""


def _json_validator_bandit(data: Any, _name: str) -> tuple[bool, str]:
    if not isinstance(data, dict) or "results" not in data:
        return False, "bandit.json missing results"
    return True, ""


def _json_validator_cloc(data: Any, _name: str) -> tuple[bool, str]:
    if not isinstance(data, dict) or "Python" not in data:
        return False, "cloc.json missing Python stats"
    return True, ""


def _json_validator_coverage(data: Any, _name: str) -> tuple[bool, str]:
    if not isinstance(data, dict) or "totals" not in data:
        return False, "coverage.json missing totals"
    if data["totals"].get("percent_covered") is None:
        return False, "coverage.json missing percent_covered"
    return True, ""


JSON_VALIDATORS: dict[str, Any] = {
    "cloc.json": _json_validator_cloc,
    "coverage.json": _json_validator_coverage,
    "pylint.json": _json_validator_list,
    "ruff.json": _json_validator_ruff,
    "gitleaks.json": _json_validator_list,
    "bandit.json": _json_validator_bandit,
    "pip_audit.json": _json_validator_list,
    "grype.json": _json_validator_dict,
    "radon_cc.json": _json_validator_dict,
    "radon_mi.json": _json_validator_dict,
}


def high_artifact_substance_ok(root: Path, name: str) -> tuple[bool, str]:
    """Validate High-tier artifact content (not just non-empty file)."""
    path = root / name
    ok = True
    detail = ""
    if name == "pylint_score.txt":
        if pylint_score(root) is None:
            ok = False
            detail = "pylint_score.txt missing rated at X/10 line"
    elif name == "interrogate.txt":
        if interrogate_coverage(root) is None:
            ok = False
            detail = "interrogate.txt missing parseable coverage line"
    else:
        data = read_json(path)
        if data is None:
            ok = False
            detail = f"{name} is missing or invalid JSON"
        else:
            validator = JSON_VALIDATORS.get(name)
            if validator is not None:
                ok, detail = validator(data, name)

    return ok, detail


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
