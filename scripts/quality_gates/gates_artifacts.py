"""High-tier required artifact presence checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.config import HIGH_REQUIRED_FILES, normalized_strictness_level
from scripts.quality_gates.jsonutil import read_json
from scripts.quality_gates.readers_cloc_docs import interrogate_coverage
from scripts.quality_gates.readers_py_coverage import pylint_score

RowList = list[dict[str, Any]]


def high_artifact_substance_ok(root: Path, name: str) -> tuple[bool, str]:
    """Validate High-tier artifact content (not just non-empty file)."""
    path = root / name
    if name == "pylint_score.txt":
        if pylint_score(root) is None:
            return False, "pylint_score.txt missing rated at X/10 line"
        return True, ""
    if name == "interrogate.txt":
        if interrogate_coverage(root) is None:
            return False, "interrogate.txt missing parseable coverage line"
        return True, ""

    data = read_json(path)
    if data is None:
        return False, f"{name} is missing or invalid JSON"

    if name == "cloc.json":
        if not isinstance(data, dict) or "Python" not in data:
            return False, "cloc.json missing Python stats"
    elif name == "coverage.json":
        if not isinstance(data, dict) or "totals" not in data:
            return False, "coverage.json missing totals"
        if data["totals"].get("percent_covered") is None:
            return False, "coverage.json missing percent_covered"
    elif name == "pylint.json":
        if not isinstance(data, list):
            return False, "pylint.json must be a JSON array"
    elif name == "ruff.json":
        if not isinstance(data, (list, dict)):
            return False, "ruff.json must be array or object"
    elif name == "gitleaks.json":
        if not isinstance(data, list):
            return False, "gitleaks.json must be a JSON array"
    elif name == "bandit.json":
        if not isinstance(data, dict) or "results" not in data:
            return False, "bandit.json missing results"
    elif name in ("radon_cc.json", "radon_mi.json"):
        if not isinstance(data, dict):
            return False, f"{name} must be a JSON object"
    return True, ""


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
