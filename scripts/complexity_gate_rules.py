"""Shared row-building logic for cyclomatic and maintainability gates."""

from __future__ import annotations

from typing import Any

RowList = list[dict[str, Any]]


def missing_metric_row(gate: str, required: str, actual: str) -> dict[str, Any]:
    """Build a standardized failing row for missing metrics."""
    return {'gate': gate, 'actual': actual, 'required': required, 'ok': False}


def max_cc_gate(
    cc: float | None,
    limit: float,
    strictness_norm: str,
) -> tuple[RowList, list[str]]:
    """Evaluate max cyclomatic complexity."""
    req = f'<= {limit:.0f}'
    label = 'Cyclomatic complexity (max)'
    if cc is None:
        if strictness_norm == 'High':
            return (
                [missing_metric_row(label, req, 'missing or unparsable radon_cc.json')],
                ['cyclomatic complexity'],
            )
        return [], []
    ok = cc <= limit
    row = {'gate': label, 'actual': f'{cc:.1f}', 'required': req, 'ok': ok}
    return [row], [] if ok else ['cyclomatic complexity']


def avg_cc_gate(
    cc_avg: float | None,
    limit: float,
    strictness_norm: str,
) -> tuple[RowList, list[str]]:
    """Evaluate average cyclomatic complexity."""
    req = f'<= {limit:.0f}'
    label = 'Cyclomatic complexity (avg)'
    if cc_avg is None:
        if strictness_norm == 'High':
            return (
                [missing_metric_row(label, req, 'missing or unparsable radon_cc.json')],
                ['cyclomatic complexity avg'],
            )
        return [], []
    ok = cc_avg <= limit
    row = {'gate': label, 'actual': f'{cc_avg:.2f}', 'required': req, 'ok': ok}
    return [row], [] if ok else ['cyclomatic complexity avg']


def min_mi_gate(
    mi: float | None,
    floor: float,
    strictness_norm: str,
) -> tuple[RowList, list[str]]:
    """Evaluate minimum MI across files."""
    req = f'>= {floor:.1f}'
    label = 'Maintainability index (min)'
    if mi is None:
        if strictness_norm == 'High':
            return (
                [missing_metric_row(label, req, 'missing or unparsable radon_mi.json')],
                ['maintainability index'],
            )
        return [], []
    ok = mi >= floor
    row = {'gate': label, 'actual': f'{mi:.1f}', 'required': req, 'ok': ok}
    return [row], [] if ok else ['maintainability index']


def avg_mi_gate(
    mi_avg: float | None,
    floor: float,
    strictness_norm: str,
) -> tuple[RowList, list[str]]:
    """Evaluate average MI across files."""
    req = f'>= {floor:.1f}'
    label = 'Maintainability index (avg)'
    if mi_avg is None:
        if strictness_norm == 'High':
            return (
                [missing_metric_row(label, req, 'missing or unparsable radon_mi.json')],
                ['maintainability index avg'],
            )
        return [], []
    ok = mi_avg >= floor
    row = {'gate': label, 'actual': f'{mi_avg:.2f}', 'required': req, 'ok': ok}
    return [row], [] if ok else ['maintainability index avg']
