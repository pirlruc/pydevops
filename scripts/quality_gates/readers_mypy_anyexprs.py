"""Quality-gates adapter for mypy any-exprs metrics."""

from __future__ import annotations

from pathlib import Path

from scripts.mypy_report_anyexprs import (
    mypy_any_exprs_report_usable as _mypy_any_exprs_report_usable,
    mypy_any_exprs_totals as _mypy_any_exprs_totals,
)


def mypy_any_exprs_totals(root: Path) -> tuple[int, int, float] | None:
    """Return (anys, exprs, coverage_pct) from any-exprs report, or None."""
    return _mypy_any_exprs_totals(root)


def mypy_any_exprs_report_usable(root: Path) -> int | None:
    """Return 0 when any-exprs report is parseable (High-tier substance check)."""
    return _mypy_any_exprs_report_usable(root)
