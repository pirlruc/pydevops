"""Parse mypy report artifacts (lineprecision, any-exprs)."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.quality_gates.jsonutil import parse_float_or_none

# mypy --lineprecision-report: optional ``Total`` row (some versions omit it).
_RE_LINEPRECISION_TOTAL = re.compile(
    r'^\s*Total\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$',
    re.I,
)

# mypy --any-exprs-report: last line is ``Total ...`` with Anys, Exprs, Coverage%.
_RE_ANY_EXPRS_TOTAL = re.compile(
    r'^\s*Total\s+(\d+)\s+(\d+)\s+([\d.]+)%\s*$',
    re.I,
)


def _read_report_lines(path: Path) -> list[str]:
    """Return stripped text lines from a report file, or empty when missing."""
    if not path.is_file():
        return []

    return path.read_text(encoding='utf-8', errors='replace').splitlines()


def _skip_lineprecision_noise_line(line: str) -> bool:
    """Return True when a lineprecision line is header/separator noise."""
    return not line or line.startswith('-') or line.lower().startswith('name ')


def _lineprecision_seven_counts(parts: list[str]) -> tuple[int, int, int] | None:
    """Parse (lines, precise, imprecise) from seven whitespace-separated tokens."""
    if len(parts) != 7:
        return None

    try:
        return int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        return None


def _lineprecision_row_triplet(line: str) -> tuple[int, int, int] | None:
    """Parse one data row into (lines, precise, imprecise), or None."""
    if _skip_lineprecision_noise_line(line):
        return None

    return _lineprecision_seven_counts(line.split())


def _lineprecision_totals_from_total_line(lines: list[str]) -> tuple[int, int, int] | None:
    """Parse a trailing ``Total`` row from a lineprecision report, if present."""
    for raw in reversed(lines):
        m = _RE_LINEPRECISION_TOTAL.match(raw.strip())
        if not m:
            continue

        try:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
        except ValueError:
            return None

    return None


def _lineprecision_totals_from_rows(lines: list[str]) -> tuple[int, int, int] | None:
    """Sum module rows when mypy omits a ``Total`` line."""
    total_lines = 0
    precise = 0
    imprecise = 0
    saw_data = False

    for raw in lines:
        trip = _lineprecision_row_triplet(raw.strip())
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
    lines = _read_report_lines(root / 'mypy-reports' / 'lineprecision' / 'lineprecision.txt')
    if not lines:
        return None

    from_total = _lineprecision_totals_from_total_line(lines)
    if from_total is not None:
        return from_total

    return _lineprecision_totals_from_rows(lines)


def _any_exprs_totals_from_total_line(lines: list[str]) -> tuple[int, int, float] | None:
    """Parse a trailing ``Total`` row from an any-exprs report, if present."""
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


_RE_ANY_EXPRS_ROW = re.compile(r'^\s*(\S+)\s+(\d+)\s+(\d+)\s+([\d.]+)%\s*$')


def _any_exprs_row_counts(line: str) -> tuple[int, int] | None:
    """Parse (anys, exprs) from one any-exprs data row, or None."""
    m = _RE_ANY_EXPRS_ROW.match(line.strip())
    if not m or m.group(1).lower() == 'total':
        return None

    try:
        return int(m.group(2)), int(m.group(3))
    except ValueError:
        return None


def _any_exprs_row_pair(line: str) -> tuple[int, int] | None:
    """Return counts for a non-header any-exprs line, or None when skipped."""
    stripped = line.strip()
    if not stripped or stripped.startswith('-') or stripped.lower().startswith('name '):
        return None

    return _any_exprs_row_counts(stripped)


def _any_exprs_totals_from_rows(lines: list[str]) -> tuple[int, int, float] | None:
    """Sum module rows when mypy omits a ``Total`` line; recompute coverage from sums."""
    anys = 0
    exprs = 0
    saw_data = False

    for raw in lines:
        pair = _any_exprs_row_pair(raw)
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

    from_total = _any_exprs_totals_from_total_line(lines)
    if from_total is not None:
        return from_total

    return _any_exprs_totals_from_rows(lines)


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


def mypy_any_exprs_report_usable(root: Path) -> int | None:
    """Return 0 when any-exprs report is parseable (High-tier substance check)."""
    return 0 if mypy_any_exprs_totals(root) is not None else None
