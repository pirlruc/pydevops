"""Vulnerability and secret-scanning gates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.config import Thresholds
from scripts.quality_gates.readers_grype_gitleaks import gitleaks_findings, grype_severities
from scripts.quality_gates.readers_pip import pip_audit_vulns

RowList = list[dict[str, Any]]


def gate_vulnerabilities(
    root: Path,
    t: Thresholds,
) -> tuple[RowList, list[str]]:
    """Evaluate pip-audit and Grype vulnerability aggregates."""
    pa_h, pa_m = pip_audit_vulns(root)
    gr_counts = grype_severities(root)
    failures: list[str] = []
    grype_rows: RowList = []
    if gr_counts is None:
        grype_rows.append(
            {
                "gate": "Grype report (JSON shape)",
                "actual": "JSON root is not an object (expected Grype object with matches[])",
                "required": "parseable object with matches[]",
                "ok": False,
            }
        )
        failures.append("grype report")
        gr_h, gr_m = 0, 0
    else:
        gr_h, gr_m = gr_counts
    # Sum counts so distinct findings from pip-audit vs Grype are not under-counted (conservative).
    high_v = pa_h + gr_h
    med_v = pa_m + gr_m
    ok_h = high_v <= t.vuln_high_max
    ok_m = med_v <= t.vuln_medium_max
    rows: RowList = [
        *grype_rows,
        {
            "gate": "Vulnerabilities (High)",
            "actual": str(high_v),
            "required": f"<= {t.vuln_high_max}",
            "ok": ok_h,
        },
        {
            "gate": "Vulnerabilities (Medium)",
            "actual": str(med_v),
            "required": f"<= {t.vuln_medium_max}",
            "ok": ok_m,
        },
    ]
    if not ok_h:
        failures.append("high vulnerabilities")
    if not ok_m:
        failures.append("medium vulnerabilities")
    return rows, failures


def gate_gitleaks(root: Path) -> tuple[RowList, list[str]]:
    """Fail on any Gitleaks finding."""
    leaks = gitleaks_findings(root)
    ok = leaks == 0
    row = {
        "gate": "Secret detection (Gitleaks)",
        "actual": str(leaks),
        "required": "0 findings",
        "ok": ok,
    }
    return [row], [] if ok else ["secrets detected"]
