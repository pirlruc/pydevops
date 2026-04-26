"""Quality-gates adapter for mypy lineprecision metrics."""

from __future__ import annotations

from pathlib import Path

from scripts.mypy_report_lineprecision import (
    mypy_imprecision_pct as _mypy_imprecision_pct,
    mypy_lineprecision_report_usable as _mypy_lineprecision_report_usable,
    mypy_lineprecision_totals as _mypy_lineprecision_totals,
)


def mypy_lineprecision_totals(root: Path) -> tuple[int, int, int] | None:
    """Return (lines, precise, imprecise) from lineprecision report, or None."""
    return _mypy_lineprecision_totals(root)


def mypy_imprecision_pct(root: Path) -> float | None:
    """Share of analyzed lines that are imprecise (0--100), or None if unavailable."""
    return _mypy_imprecision_pct(root)


def mypy_lineprecision_report_usable(root: Path) -> int | None:
    """Return 0 when lineprecision report is parseable (High-tier substance check)."""
    return _mypy_lineprecision_report_usable(root)
