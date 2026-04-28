"""Mypy metric gates (type coverage, imprecision, any-expression density)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.mypy_gate_rules import (
    any_density_row,
    imprecision_row,
    skip_mypy_without_reports,
    type_coverage_row,
)
from scripts.quality_gates.config import Thresholds
from scripts.quality_gates.readers_mypy import (
    mypy_any_exprs_totals,
    mypy_imprecision_pct,
)

RowList = list[dict[str, Any]]


def gate_mypy(
    root: Path,
    sloc: float,
    t: Thresholds,
    strictness_norm: str,
) -> tuple[RowList, list[str]]:
    """Evaluate mypy report gates; Low/Medium skip when reports are absent."""
    totals = mypy_any_exprs_totals(root)
    cov = totals[2] if totals is not None else None
    anys = totals[0] if totals is not None else None

    imp = mypy_imprecision_pct(root)

    if skip_mypy_without_reports(strictness_norm, totals is not None, imp is not None):
        return [], []

    rows: RowList = []
    failures: list[str] = []

    r, f = type_coverage_row(cov, t, strictness_norm)
    rows.extend(r)
    failures.extend(f)

    r, f = imprecision_row(imp, t, strictness_norm)
    rows.extend(r)
    failures.extend(f)

    r, f = any_density_row(anys, sloc, t, strictness_norm)
    rows.extend(r)
    failures.extend(f)

    return rows, failures
