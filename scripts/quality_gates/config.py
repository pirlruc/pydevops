"""Threshold definitions and High-tier required artifact list.

High-tier coverage / complexity / MI / docstring floors are loaded from
``docs/guardrails/python/profile.thresholds.yml`` (or the vendored
``scripts/python.profile.thresholds.yml``). Missing required keys fail closed
(CI-022). Low and Medium remain relative offsets below High.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from scripts.org_thresholds import load_python_floors


@dataclass(frozen=True)
class Thresholds:  # pylint: disable=too-many-instance-attributes
    """Numeric thresholds for one strictness tier."""

    coverage_line_min: float
    coverage_branch_min: float
    pylint_score_min: float
    cyclomatic_max: float
    cyclomatic_avg_max: float
    maintainability_index_min: float
    maintainability_index_avg_min: float
    duplication_max_pct: float
    issues_per_kloc_slocs_max: float
    docstring_coverage_min: float
    docstring_issues_per_kloc_cloc_max: float
    mypy_type_coverage_min: float
    mypy_imprecision_lt_pct: float
    mypy_any_per_kloc_lt: float
    vuln_high_max: int
    vuln_medium_max: int
    bandit_findings_max: int


def _repo_root() -> Path:
    """pydevops repo root (parent of ``scripts/``)."""
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_org_python_floors() -> dict[str, float]:
    """Org floors from the pinned guardrails submodule or vendored copy."""
    return load_python_floors(_repo_root())


def _build_strictness() -> dict[str, Thresholds]:
    org = load_org_python_floors()
    high = Thresholds(
        coverage_line_min=org['statement_coverage'],
        coverage_branch_min=org['branch_coverage'],
        pylint_score_min=9.5,
        cyclomatic_max=org['max_cyclomatic_complexity'],
        cyclomatic_avg_max=org['avg_cyclomatic_complexity'],
        maintainability_index_min=org['min_maintainability_index'],
        maintainability_index_avg_min=org['avg_maintainability_index'],
        duplication_max_pct=5.0,
        issues_per_kloc_slocs_max=5.0,
        docstring_coverage_min=org['doc_coverage'],
        docstring_issues_per_kloc_cloc_max=2.0,
        mypy_type_coverage_min=95.0,
        mypy_imprecision_lt_pct=1.0,
        mypy_any_per_kloc_lt=1.0,
        vuln_high_max=0,
        vuln_medium_max=5,
        bandit_findings_max=0,
    )
    medium = Thresholds(
        coverage_line_min=85.0,
        coverage_branch_min=80.0,
        pylint_score_min=8.0,
        cyclomatic_max=10,
        cyclomatic_avg_max=7,
        maintainability_index_min=20.0,
        maintainability_index_avg_min=40.0,
        duplication_max_pct=15.0,
        issues_per_kloc_slocs_max=15.0,
        docstring_coverage_min=85.0,
        docstring_issues_per_kloc_cloc_max=5.0,
        mypy_type_coverage_min=90.0,
        mypy_imprecision_lt_pct=2.0,
        mypy_any_per_kloc_lt=2.0,
        vuln_high_max=0,
        vuln_medium_max=10,
        bandit_findings_max=3,
    )
    low = Thresholds(
        coverage_line_min=70.0,
        coverage_branch_min=65.0,
        pylint_score_min=7.0,
        cyclomatic_max=15,
        cyclomatic_avg_max=10,
        maintainability_index_min=10.0,
        maintainability_index_avg_min=25.0,
        duplication_max_pct=25.0,
        issues_per_kloc_slocs_max=25.0,
        docstring_coverage_min=70.0,
        docstring_issues_per_kloc_cloc_max=8.0,
        mypy_type_coverage_min=85.0,
        mypy_imprecision_lt_pct=5.0,
        mypy_any_per_kloc_lt=5.0,
        vuln_high_max=2,
        vuln_medium_max=25,
        bandit_findings_max=15,
    )
    return {'Low': low, 'Medium': medium, 'High': high}


STRICTNESS: dict[str, Thresholds] = _build_strictness()


def normalized_strictness_level(raw: str) -> str:
    """Return ``Low`` | ``Medium`` | ``High`` (case-insensitive); unknown values map to Medium."""
    key = raw.strip().title()
    return key if key in STRICTNESS else 'Medium'


# When STRICTNESS_LEVEL=High, these artifacts must exist (non-empty files) so gates are not skipped.
HIGH_REQUIRED_FILES: tuple[str, ...] = (
    'coverage.json',
    'pylint.json',
    'pylint_score.txt',
    'radon_cc.json',
    'radon_mi.json',
    'interrogate.txt',
    'pydoclint.txt',
    'ruff.json',
    'gitleaks.json',
    'semgrep.sarif',
    'bandit.json',
    'pip_audit.json',
    'grype.json',
    'cloc.json',
    'mypy-reports/lineprecision/lineprecision.txt',
    'mypy-reports/anyexprs/any-exprs.txt',
)
