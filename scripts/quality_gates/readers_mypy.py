"""Compatibility facade for mypy report readers."""

from __future__ import annotations

from scripts.quality_gates.readers_mypy_anyexprs import (
    mypy_any_exprs_report_usable,
    mypy_any_exprs_totals,
)
from scripts.quality_gates.readers_mypy_lineprecision import (
    mypy_imprecision_pct,
    mypy_lineprecision_report_usable,
    mypy_lineprecision_totals,
)

__all__ = [
    "mypy_any_exprs_report_usable",
    "mypy_any_exprs_totals",
    "mypy_imprecision_pct",
    "mypy_lineprecision_report_usable",
    "mypy_lineprecision_totals",
]
