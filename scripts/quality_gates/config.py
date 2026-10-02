"""Threshold definitions and High-tier required artifact list.

High-tier coverage / complexity / MI / docstring floors are loaded from
``docs/guardrails/python/profile.thresholds.yml`` (or the vendored
``scripts/python.profile.thresholds.yml``). Missing required keys fail closed
(CI-022). Low and Medium remain relative offsets below High.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

from scripts.org_thresholds import load_python_floors, require_python_floors


@dataclass(frozen=True)
class _Coverage:
    line_min: float
    branch_min: float


@dataclass(frozen=True)
class _Lint:
    pylint_score_min: float
    duplication_max_pct: float
    issues_per_kloc_slocs_max: float


@dataclass(frozen=True)
class _Complexity:
    cyclomatic_max: float
    cyclomatic_avg_max: float
    maintainability_index_min: float
    maintainability_index_avg_min: float


@dataclass(frozen=True)
class _Docs:
    coverage_min: float
    issues_per_kloc_cloc_max: float


@dataclass(frozen=True)
class _Types:
    coverage_min: float
    imprecision_lt_pct: float
    any_per_kloc_lt: float


@dataclass(frozen=True)
class _Security:
    vuln_high_max: int
    vuln_medium_max: int
    bandit_findings_max: int


@dataclass(frozen=True)
class Thresholds:
    """Numeric thresholds for one strictness tier.

    Fields are grouped so the dataclass stays under the pylint attribute cap.
    Callers still use the flat names.
    """

    coverage: _Coverage
    lint: _Lint
    complexity: _Complexity
    docs: _Docs
    types: _Types
    security: _Security

    @property
    def coverage_line_min(self) -> float:
        return self.coverage.line_min

    @property
    def coverage_branch_min(self) -> float:
        return self.coverage.branch_min

    @property
    def pylint_score_min(self) -> float:
        return self.lint.pylint_score_min

    @property
    def cyclomatic_max(self) -> float:
        return self.complexity.cyclomatic_max

    @property
    def cyclomatic_avg_max(self) -> float:
        return self.complexity.cyclomatic_avg_max

    @property
    def maintainability_index_min(self) -> float:
        return self.complexity.maintainability_index_min

    @property
    def maintainability_index_avg_min(self) -> float:
        return self.complexity.maintainability_index_avg_min

    @property
    def duplication_max_pct(self) -> float:
        return self.lint.duplication_max_pct

    @property
    def issues_per_kloc_slocs_max(self) -> float:
        return self.lint.issues_per_kloc_slocs_max

    @property
    def docstring_coverage_min(self) -> float:
        return self.docs.coverage_min

    @property
    def docstring_issues_per_kloc_cloc_max(self) -> float:
        return self.docs.issues_per_kloc_cloc_max

    @property
    def mypy_type_coverage_min(self) -> float:
        return self.types.coverage_min

    @property
    def mypy_imprecision_lt_pct(self) -> float:
        return self.types.imprecision_lt_pct

    @property
    def mypy_any_per_kloc_lt(self) -> float:
        return self.types.any_per_kloc_lt

    @property
    def vuln_high_max(self) -> int:
        return self.security.vuln_high_max

    @property
    def vuln_medium_max(self) -> int:
        return self.security.vuln_medium_max

    @property
    def bandit_findings_max(self) -> int:
        return self.security.bandit_findings_max


def _tier(values: dict[str, float | int]) -> Thresholds:
    """Build one tier from the flat names callers already use."""
    return Thresholds(
        coverage=_Coverage(values['coverage_line_min'], values['coverage_branch_min']),
        lint=_Lint(
            values['pylint_score_min'],
            values['duplication_max_pct'],
            values['issues_per_kloc_slocs_max'],
        ),
        complexity=_Complexity(
            values['cyclomatic_max'],
            values['cyclomatic_avg_max'],
            values['maintainability_index_min'],
            values['maintainability_index_avg_min'],
        ),
        docs=_Docs(
            values['docstring_coverage_min'],
            values['docstring_issues_per_kloc_cloc_max'],
        ),
        types=_Types(
            values['mypy_type_coverage_min'],
            values['mypy_imprecision_lt_pct'],
            values['mypy_any_per_kloc_lt'],
        ),
        security=_Security(
            int(values['vuln_high_max']),
            int(values['vuln_medium_max']),
            int(values['bandit_findings_max']),
        ),
    )


def _repo_root() -> Path:
    """pydevops repo root (parent of ``scripts/``)."""
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_org_python_floors() -> dict[str, float]:
    """Org floors from the pinned guardrails submodule or vendored copy."""
    return load_python_floors(_repo_root())


def _build_strictness() -> dict[str, Thresholds]:
    org = load_org_python_floors()
    high = _tier(dict(
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
    ))
    medium = _tier(dict(
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
    ))
    low = _tier(dict(
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
    ))
    return {'Low': low, 'Medium': medium, 'High': high}


STRICTNESS: dict[str, Thresholds] = _build_strictness()


def apply_consumer_floors(base: Thresholds, path: Path) -> Thresholds:
    """Replace coverage, complexity, MI, and docstring floors from a consumer file.

    A present file with a missing required key fails closed (CI-022).
    """
    floors = require_python_floors(path)
    return replace(
        base,
        coverage=replace(
            base.coverage,
            line_min=floors['statement_coverage'],
            branch_min=floors['branch_coverage'],
        ),
        complexity=replace(
            base.complexity,
            cyclomatic_max=floors['max_cyclomatic_complexity'],
            cyclomatic_avg_max=floors['avg_cyclomatic_complexity'],
            maintainability_index_min=floors['min_maintainability_index'],
            maintainability_index_avg_min=floors['avg_maintainability_index'],
        ),
        docs=replace(base.docs, coverage_min=floors['doc_coverage']),
    )


def resolve_thresholds(strictness: str, consumer_file: str | None = None) -> Thresholds:
    """Strictness tier, overlaid by the consumer profile when that file exists."""
    base = STRICTNESS[normalized_strictness_level(strictness)]
    raw = consumer_file if consumer_file is not None else os.environ.get('CONSUMER_THRESHOLDS', '')
    if not raw:
        return base
    path = Path(raw)
    if not path.is_file():
        return base
    return apply_consumer_floors(base, path)


def scripts_only_package() -> bool:
    """True when the caller has no installable app (PDO-PYPROJECT-001)."""
    return os.environ.get('PACKAGE_MODE', 'app') == 'scripts'


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
