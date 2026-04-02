"""Parse coverage.json and pylint artifacts."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.quality_gates.jsonutil import read_json


def load_coverage_totals(root: Path) -> tuple[float | None, float | None]:
    """Return (line_coverage_pct, branch_coverage_pct) from coverage.json totals."""
    data = read_json(root / "coverage.json")
    if not data or "totals" not in data:
        return None, None
    t = data["totals"]
    line = t.get("percent_covered")
    branches = t.get("percent_branches_covered")
    return (
        float(line) if line is not None else None,
        float(branches) if branches is not None else None,
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
