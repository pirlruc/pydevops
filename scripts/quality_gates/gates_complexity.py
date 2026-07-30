"""Complexity, maintainability, duplication, and issue-density gates."""

from __future__ import annotations

from typing import Any

from scripts.complexity_gate_rules import avg_cc_gate, avg_mi_gate, max_cc_gate, min_mi_gate
from scripts.quality_gates.config import Thresholds

RowList = list[dict[str, Any]]


def gate_cyclomatic(
    cc: float | None,
    t: Thresholds,
    strictness_norm: str = 'Medium',
) -> tuple[RowList, list[str]]:
    """Evaluate max cyclomatic complexity."""
    return max_cc_gate(cc, t.cyclomatic_max, strictness_norm)


def gate_cyclomatic_avg(
    cc_avg: float | None,
    t: Thresholds,
    strictness_norm: str = 'Medium',
) -> tuple[RowList, list[str]]:
    """Evaluate average cyclomatic complexity."""
    return avg_cc_gate(cc_avg, t.cyclomatic_avg_max, strictness_norm)


def gate_maintainability(
    mi: float | None,
    t: Thresholds,
    strictness_norm: str = 'Medium',
) -> tuple[RowList, list[str]]:
    """Evaluate minimum MI across files."""
    return min_mi_gate(mi, t.maintainability_index_min, strictness_norm)


def gate_maintainability_avg(
    mi_avg: float | None,
    t: Thresholds,
    strictness_norm: str = 'Medium',
) -> tuple[RowList, list[str]]:
    """Evaluate average MI across files."""
    return avg_mi_gate(mi_avg, t.maintainability_index_avg_min, strictness_norm)


def gate_duplication(
    dup: float | None,
    t: Thresholds,
) -> tuple[RowList, list[str]]:
    """Evaluate jscpd duplication percentage."""
    if dup is None:
        row = {
            'gate': 'Duplication (jscpd)',
            'actual': '(missing or invalid jscpd-report.json)',
            'required': f'<= {t.duplication_max_pct:.1f}%',
            'ok': False,
        }
        return [row], ['duplication']

    ok = dup <= t.duplication_max_pct
    row = {
        'gate': 'Duplication (jscpd)',
        'actual': f'{dup:.2f}%',
        'required': f'<= {t.duplication_max_pct:.1f}%',
        'ok': ok,
    }
    return [row], [] if ok else ['duplication']


def gate_issues_per_kloc(
    sloc: float,
    pylint_n: int,
    ruff_n: int,
    t: Thresholds,
) -> tuple[RowList, list[str]]:
    """Evaluate combined Pylint+Ruff issues per KLoC (SLOC)."""
    if sloc <= 0:
        return [], []

    issues = pylint_n + ruff_n
    per_k = (issues / sloc) * 1000.0
    ok = per_k <= t.issues_per_kloc_slocs_max
    row = {
        'gate': 'Code issues per KLoC (SLOC)',
        'actual': f'{per_k:.2f}',
        'required': f'<= {t.issues_per_kloc_slocs_max:.1f}',
        'ok': ok,
    }
    return [row], [] if ok else ['issues per KLoC (SLOC)']
