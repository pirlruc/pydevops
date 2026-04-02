"""Parse cloc, interrogate, and pydoclint outputs."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.quality_gates.jsonutil import read_json


def cloc_slocs_comments(root: Path) -> tuple[float, float]:
    """Return (Python code lines, Python comment lines) from cloc.json."""
    data = read_json(root / "cloc.json")
    if not data or "Python" not in data:
        return 0.0, 0.0
    py = data["Python"]
    return float(py.get("code", 0)), float(py.get("comment", 0))


def interrogate_coverage(root: Path) -> float | None:
    """Parse docstring coverage percentage from interrogate stdout capture."""
    p = root / "interrogate.txt"
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"TOTAL COVERAGE:\s*([\d.]+)%", text)
    if m:
        return float(m.group(1))
    m = re.search(r"([\d.]+)%\s*covered", text, re.I)
    return float(m.group(1)) if m else None


def pydoclint_issue_count(root: Path) -> int:
    """Heuristic count of pydoclint error lines in captured output."""
    p = root / "pydoclint.txt"
    if not p.is_file():
        return 0
    return sum(
        1
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
        if "ERROR" in line or "error" in line.lower()
    )
