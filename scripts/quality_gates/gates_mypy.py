"""Mypy metric gates (type coverage, imprecision, any-expression density)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.config import Thresholds
from scripts.quality_gates.readers_mypy import (
    mypy_any_exprs_totals,
    mypy_imprecision_pct,
)

RowList = list[dict[str, Any]]


def _skip_mypy_without_reports(
    strictness_norm: str,
    has_any_exprs_report: bool,
    has_imprecision: bool,
) -> bool:
    """True when Low/Medium should omit mypy gates (no usable reports)."""
    return strictness_norm != 'High' and not has_any_exprs_report and not has_imprecision


def _type_coverage_row(
    cov: float | None,
    t: Thresholds,
    strictness_norm: str,
) -> tuple[RowList, list[str]]:
    """Gate rows for any-exprs coverage percentage."""
    if cov is None:
        if strictness_norm == 'High':
            row = {
                'gate': 'Mypy type coverage (any-exprs)',
                'actual': 'missing or unparsable any-exprs report',
                'required': f'>= {t.mypy_type_coverage_min:.1f}%',
                'ok': False,
            }
            return [row], ['mypy type coverage']

        return [], []

    ok = cov >= t.mypy_type_coverage_min
    row = {
        'gate': 'Mypy type coverage (any-exprs)',
        'actual': f'{cov:.2f}%',
        'required': f'>= {t.mypy_type_coverage_min:.1f}%',
        'ok': ok,
    }
    return [row], [] if ok else ['mypy type coverage']


def _imprecision_row(
    imp: float | None,
    t: Thresholds,
    strictness_norm: str,
) -> tuple[RowList, list[str]]:
    """Gate rows for imprecise-line share from lineprecision."""
    if imp is None:
        if strictness_norm == 'High':
            row = {
                'gate': 'Mypy imprecision (lineprecision)',
                'actual': 'missing or unparsable lineprecision report',
                'required': f'< {t.mypy_imprecision_lt_pct:.1f}%',
                'ok': False,
            }
            return [row], ['mypy imprecision']

        return [], []

    ok = imp < t.mypy_imprecision_lt_pct
    row = {
        'gate': 'Mypy imprecision (lineprecision)',
        'actual': f'{imp:.2f}%',
        'required': f'< {t.mypy_imprecision_lt_pct:.1f}%',
        'ok': ok,
    }
    return [row], [] if ok else ['mypy imprecision']


def _any_density_row(
    anys: int | None,
    sloc: float,
    t: Thresholds,
    strictness_norm: str,
) -> tuple[RowList, list[str]]:
    """Gate rows for any-expressions per 1000 Python SLOC (cloc)."""
    if anys is None:
        if strictness_norm == 'High':
            row = {
                'gate': 'Mypy any-expression density',
                'actual': 'missing or unparsable any-exprs report',
                'required': f'< {t.mypy_any_per_kloc_lt:.1f} per 1K SLOC',
                'ok': False,
            }
            return [row], ['mypy any density']

        return [], []

    if sloc <= 0:
        row = {
            'gate': 'Mypy any-expression density',
            'actual': 'SLOC is 0 (cannot compute density)',
            'required': f'< {t.mypy_any_per_kloc_lt:.1f} per 1K SLOC',
            'ok': False,
        }
        return [row], ['mypy any density']

    density = (anys * 1000.0) / sloc
    ok = density < t.mypy_any_per_kloc_lt
    row = {
        'gate': 'Mypy any-expression density',
        'actual': f'{density:.3f} per 1K SLOC ({anys} any / {sloc:.0f} SLOC)',
        'required': f'< {t.mypy_any_per_kloc_lt:.1f} per 1K SLOC',
        'ok': ok,
    }
    return [row], [] if ok else ['mypy any density']


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

    if _skip_mypy_without_reports(strictness_norm, totals is not None, imp is not None):
        return [], []

    rows: RowList = []
    failures: list[str] = []

    r, f = _type_coverage_row(cov, t, strictness_norm)
    rows.extend(r)
    failures.extend(f)

    r, f = _imprecision_row(imp, t, strictness_norm)
    rows.extend(r)
    failures.extend(f)

    r, f = _any_density_row(anys, sloc, t, strictness_norm)
    rows.extend(r)
    failures.extend(f)

    return rows, failures
