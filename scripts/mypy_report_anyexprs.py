"""Parse mypy any-exprs report artifacts."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.quality_gates.jsonutil import parse_float_or_none

_RE_ANY_EXPRS_TOTAL = re.compile(r'^\s*Total\s+(\d+)\s+(\d+)\s+([\d.]+)%\s*$', re.I)
_RE_ANY_EXPRS_ROW = re.compile(r'^\s*(\S+)\s+(\d+)\s+(\d+)\s+([\d.]+)%\s*$')


def _read_report_lines(path: Path) -> list[str]:
    """Return report lines, or an empty list when file is missing."""
    if not path.is_file():
        return []
    return path.read_text(encoding='utf-8', errors='replace').splitlines()


def _totals_from_total_line(lines: list[str]) -> tuple[int, int, float] | None:
    """Parse the trailing Total row when present."""
    for raw in reversed(lines):
        m = _RE_ANY_EXPRS_TOTAL.match(raw.strip())
        if not m:
            continue
        try:
            anys = int(m.group(1))
            exprs = int(m.group(2))
        except ValueError:
            return None
        cov = parse_float_or_none(m.group(3))
        if cov is None:
            return None
        return anys, exprs, cov
    return None


def _row_counts(line: str) -> tuple[int, int] | None:
    """Parse one module row into (any_count, expr_count)."""
    m = _RE_ANY_EXPRS_ROW.match(line.strip())
    if not m or m.group(1).lower() == 'total':
        return None
    try:
        return int(m.group(2)), int(m.group(3))
    except ValueError:
        return None


def _row_pair(line: str) -> tuple[int, int] | None:
    """Skip headers/separators and parse one any-exprs data row."""
    stripped = line.strip()
    if not stripped or stripped.startswith('-') or stripped.lower().startswith('name '):
        return None
    return _row_counts(stripped)


def _totals_from_rows(lines: list[str]) -> tuple[int, int, float] | None:
    """Aggregate rows and recompute coverage when Total row is absent."""
    anys = 0
    exprs = 0
    saw_data = False
    for raw in lines:
        pair = _row_pair(raw)
        if pair is None:
            continue
        a_part, e_part = pair
        anys += a_part
        exprs += e_part
        saw_data = True
    if not saw_data or exprs <= 0:
        return None
    cov = 100.0 * float(exprs - anys) / float(exprs)
    return anys, exprs, cov


def mypy_any_exprs_totals(root: Path) -> tuple[int, int, float] | None:
    """Return (anys, exprs, coverage_pct) from any-exprs report, or None."""
    lines = _read_report_lines(root / 'mypy-reports' / 'anyexprs' / 'any-exprs.txt')
    if not lines:
        return None
    from_total = _totals_from_total_line(lines)
    if from_total is not None:
        return from_total
    return _totals_from_rows(lines)


def mypy_any_exprs_report_usable(root: Path) -> int | None:
    """Return 0 when any-exprs report is parseable (High-tier substance check)."""
    return 0 if mypy_any_exprs_totals(root) is not None else None
