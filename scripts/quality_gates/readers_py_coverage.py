"""Parse coverage.json and pylint artifacts."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.quality_gates.jsonutil import parse_float_or_none, read_json


def load_coverage_totals(root: Path) -> tuple[float | None, float | None]:
    """Return (line_coverage_pct, branch_coverage_pct) from coverage.json totals."""
    data = read_json(root / "coverage.json")
    if not isinstance(data, dict):
        return None, None
    totals = data.get("totals")
    if not isinstance(totals, dict):
        return None, None
    line = totals.get("percent_covered")
    branches = totals.get("percent_branches_covered")
    return (
        parse_float_or_none(str(line)) if line is not None else None,
        parse_float_or_none(str(branches)) if branches is not None else None,
    )


def pylint_score(root: Path) -> float | None:
    """Parse Pylint /10 score from pylint_score.txt (JSON list alone has no score)."""
    score_path = root / "pylint_score.txt"
    if not score_path.is_file():
        return None
    text = score_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"rated at ([\d.]+)/10", text)
    return float(m.group(1)) if m else None


def pylint_issue_count(root: Path) -> int:
    """Count Pylint messages from pylint.json."""
    data = read_json(root / "pylint.json")
    if not data or not isinstance(data, list):
        return 0
    return len(data)


def pytest_exit_code(root: Path) -> int | None:
    """Read integer ``pytest_exit_code.txt`` from the quality output dir, if present and valid."""
    path = root / "pytest_exit_code.txt"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    try:
        return int(text)
    except ValueError:
        return None
