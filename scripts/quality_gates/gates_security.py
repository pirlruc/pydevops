"""Vulnerability and secret-scanning gates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.config import Thresholds
from scripts.quality_gates.readers_bandit import bandit_finding_count
from scripts.quality_gates.readers_grype_gitleaks import gitleaks_findings, grype_severities
from scripts.quality_gates.readers_pip import pip_audit_vulns
from scripts.quality_gates.readers_semgrep import semgrep_sarif_error_warning_counts

RowList = list[dict[str, Any]]


def gate_bandit(root: Path, t: Thresholds) -> tuple[RowList, list[str]]:
    """Evaluate Bandit result count against tier-specific caps (PY-SEC-002)."""
    n = bandit_finding_count(root)
    if n is None:
        row = {
            'gate': 'Bandit (SAST)',
            'actual': 'missing or invalid bandit.json',
            'required': 'parseable JSON object with results[]',
            'ok': False,
        }
        return [row], ['bandit report']

    ok = n <= t.bandit_findings_max
    row = {
        'gate': 'Bandit (SAST)',
        'actual': str(n),
        'required': f'<= {t.bandit_findings_max}',
        'ok': ok,
    }
    return [row], [] if ok else ['bandit findings']


def gate_vulnerabilities(
    root: Path,
    t: Thresholds,
) -> tuple[RowList, list[str]]:
    """Evaluate pip-audit and Grype vulnerability aggregates (PY-SEC-004)."""
    pa_counts = pip_audit_vulns(root)
    gr_counts = grype_severities(root)
    failures: list[str] = []
    report_rows: RowList = []
    if pa_counts is None:
        report_rows.append(
            {
                'gate': 'pip-audit report (JSON shape)',
                'actual': 'missing or invalid pip_audit.json',
                'required': 'parseable JSON array',
                'ok': False,
            },
        )
        failures.append('pip-audit report')
        pa_h, pa_m = 0, 0
    else:
        pa_h, pa_m = pa_counts

    if gr_counts is None:
        report_rows.append(
            {
                'gate': 'Grype report (JSON shape)',
                'actual': 'missing/invalid grype.json or non-object root',
                'required': 'parseable object with matches[]',
                'ok': False,
            },
        )
        failures.append('grype report')
        gr_h, gr_m = 0, 0
    else:
        gr_h, gr_m = gr_counts
    # Sum counts so distinct findings from pip-audit vs Grype are not under-counted (conservative).
    high_v = pa_h + gr_h
    med_v = pa_m + gr_m
    ok_h = high_v <= t.vuln_high_max
    ok_m = med_v <= t.vuln_medium_max
    rows: RowList = [
        *report_rows,
        {
            'gate': 'Vulnerabilities (High)',
            'actual': str(high_v),
            'required': f'<= {t.vuln_high_max}',
            'ok': ok_h,
        },
        {
            'gate': 'Vulnerabilities (Medium)',
            'actual': str(med_v),
            'required': f'<= {t.vuln_medium_max}',
            'ok': ok_m,
        },
    ]
    if not ok_h:
        failures.append('high vulnerabilities')

    if not ok_m:
        failures.append('medium vulnerabilities')

    return rows, failures


def gate_semgrep(root: Path, strictness_norm: str) -> tuple[RowList, list[str]]:
    """Medium and High: Semgrep SARIF error=0, warning<=5 (PY-SEC-002)."""
    if strictness_norm == 'Low':
        return [], []

    counts = semgrep_sarif_error_warning_counts(root)
    if counts is None:
        row = {
            'gate': 'Semgrep (SARIF)',
            'actual': 'missing or invalid semgrep.sarif',
            'required': '0 error-level, <= 5 warning-level results',
            'ok': False,
        }
        return [row], ['semgrep report']

    n_err, n_warn = counts
    ok_err = n_err == 0
    ok_warn = n_warn <= 5
    rows: RowList = [
        {
            'gate': 'Semgrep (error-level)',
            'actual': str(n_err),
            'required': '0',
            'ok': ok_err,
        },
        {
            'gate': 'Semgrep (warning-level)',
            'actual': str(n_warn),
            'required': '<= 5',
            'ok': ok_warn,
        },
    ]
    failures: list[str] = []
    if not ok_err:
        failures.append('semgrep error-level findings')

    if not ok_warn:
        failures.append('semgrep warning-level findings')

    return rows, failures


def gate_gitleaks(root: Path) -> tuple[RowList, list[str]]:
    """Fail on any Gitleaks finding (PY-SEC-003)."""
    leaks = gitleaks_findings(root)
    ok = leaks == 0
    row = {
        'gate': 'Secret detection (Gitleaks)',
        'actual': str(leaks),
        'required': '0 findings',
        'ok': ok,
    }
    return [row], [] if ok else ['secrets detected']
