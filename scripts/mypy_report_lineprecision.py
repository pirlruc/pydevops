"""Parse mypy lineprecision report artifacts."""

from __future__ import annotations

import re
from pathlib import Path

_RE_LINEPRECISION_TOTAL = re.compile(
    r"^\s*Total\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$",
    re.I,
)


def _read_report_lines(path: Path) -> list[str]:
    """Return report lines, or an empty list when file is missing."""
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _skip_noise_line(line: str) -> bool:
    """True when line is header/separator noise."""
    return not line or line.startswith("-") or line.lower().startswith("name ")


def _counts_from_seven_tokens(parts: list[str]) -> tuple[int, int, int] | None:
    """Parse one lineprecision row into (lines, precise, imprecise)."""
    if len(parts) != 7:
        return None
    try:
        return int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        return None


def _row_triplet(line: str) -> tuple[int, int, int] | None:
    """Return parsed metrics for one non-noise lineprecision row."""
    if _skip_noise_line(line):
        return None
    return _counts_from_seven_tokens(line.split())


def _totals_from_total_line(lines: list[str]) -> tuple[int, int, int] | None:
    """Parse metrics from trailing Total row when available."""
    for raw in reversed(lines):
        m = _RE_LINEPRECISION_TOTAL.match(raw.strip())
        if not m:
            continue
        try:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
        except ValueError:
            return None
    return None


def _totals_from_rows(lines: list[str]) -> tuple[int, int, int] | None:
    """Aggregate metrics from per-module rows when Total row is absent."""
    total_lines = 0
    precise = 0
    imprecise = 0
    saw_data = False
    for raw in lines:
        trip = _row_triplet(raw.strip())
        if trip is None:
            continue
        ln, pr, imp = trip
        total_lines += ln
        precise += pr
        imprecise += imp
        saw_data = True
    if not saw_data or total_lines <= 0:
        return None
    return total_lines, precise, imprecise


def mypy_lineprecision_totals(root: Path) -> tuple[int, int, int] | None:
    """Return (lines, precise, imprecise) from lineprecision report, or None."""
    lines = _read_report_lines(root / "mypy-reports" / "lineprecision" / "lineprecision.txt")
    if not lines:
        return None
    from_total = _totals_from_total_line(lines)
    if from_total is not None:
        return from_total
    return _totals_from_rows(lines)


def mypy_imprecision_pct(root: Path) -> float | None:
    """Share of analyzed lines that are imprecise (0--100), or None if unavailable."""
    totals = mypy_lineprecision_totals(root)
    if totals is None:
        return None
    lines, _precise, imprecise = totals
    if lines <= 0:
        return None
    return 100.0 * float(imprecise) / float(lines)


def mypy_lineprecision_report_usable(root: Path) -> int | None:
    """Return 0 when lineprecision report is parseable (High-tier substance check)."""
    return 0 if mypy_lineprecision_totals(root) is not None else None
