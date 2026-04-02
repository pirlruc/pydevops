"""Evaluate quality gate thresholds from CI tool outputs (strictness: Low | Medium | High)."""

from __future__ import annotations

from scripts.quality_gates.config import HIGH_REQUIRED_FILES, STRICTNESS, Thresholds, normalized_strictness_level
from scripts.quality_gates.evaluation import evaluate
from scripts.quality_gates.engine import main
from scripts.quality_gates.jsonutil import parse_float_or_none as _parse_float_or_none
from scripts.quality_gates.jsonutil import read_json as _read_json
from scripts.quality_gates.readers_cloc_docs import interrogate_coverage as _interrogate_coverage
from scripts.quality_gates.readers_py_coverage import pylint_issue_count as _pylint_issue_count
from scripts.quality_gates.readers_py_coverage import pylint_score as _pylint_score
from scripts.quality_gates.readers_grype_gitleaks import gitleaks_findings as _gitleaks_findings
from scripts.quality_gates.readers_grype_gitleaks import grype_severities as _grype_severities
from scripts.quality_gates.readers_pip import pip_audit_vulns as _pip_audit_vulns
from scripts.quality_gates.readers_radon import radon_cc_max as _radon_cc_max
from scripts.quality_gates.readers_radon import radon_mi_min as _radon_mi_min
from scripts.quality_gates.readers_ruff_jscpd import ruff_issue_count as _ruff_issue_count

__all__ = [
    "HIGH_REQUIRED_FILES",
    "STRICTNESS",
    "Thresholds",
    "normalized_strictness_level",
    "evaluate",
    "main",
    "_gitleaks_findings",
    "_grype_severities",
    "_interrogate_coverage",
    "_parse_float_or_none",
    "_pip_audit_vulns",
    "_pylint_issue_count",
    "_pylint_score",
    "_radon_cc_max",
    "_radon_mi_min",
    "_read_json",
    "_ruff_issue_count",
]
