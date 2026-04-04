"""Parse cloc, interrogate, and pydoclint outputs."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.quality_gates.jsonutil import coerce_non_negative_float, parse_float_or_none, read_json


def cloc_slocs_comments(root: Path) -> tuple[float, float]:
    """Return (Python code lines, Python comment lines) from cloc.json."""
    data = read_json(root / "cloc.json")
    if not isinstance(data, dict):
        return 0.0, 0.0
    py = data.get("Python")
    if not isinstance(py, dict):
        return 0.0, 0.0
    return (
        coerce_non_negative_float(py.get("code")),
        coerce_non_negative_float(py.get("comment")),
    )


def interrogate_coverage(root: Path) -> float | None:
    """Parse docstring coverage percentage from interrogate stdout capture."""
    p = root / "interrogate.txt"
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"TOTAL COVERAGE:\s*([\d.]+)%", text)
    if m:
        return parse_float_or_none(m.group(1))
    m = re.search(r"([\d.]+)%\s*covered", text, re.I)
    return parse_float_or_none(m.group(1)) if m else None


# pydoclint emits flake8-style lines: ``path:line:col: ERROR ...`` (col may be omitted in some versions).
_RE_PYDOCLINT_VIOLATION = re.compile(r":\d+:\s*(?:\d+:\s*)?ERROR\s+", re.I)


def pydoclint_issue_count(root: Path) -> int:
    """Count pydoclint violation lines (flake8-style ``...:line: ERROR``), not summary text."""
    p = root / "pydoclint.txt"
    if not p.is_file():
        return 0
    n = 0
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if _RE_PYDOCLINT_VIOLATION.search(line):
            n += 1
    return n
