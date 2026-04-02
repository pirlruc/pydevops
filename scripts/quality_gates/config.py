"""Threshold definitions and High-tier required artifact list."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Thresholds:  # pylint: disable=too-many-instance-attributes
    """Numeric thresholds for one strictness tier."""

    coverage_line_min: float
    coverage_branch_min: float
    pylint_score_min: float
    cyclomatic_max: float
    maintainability_index_min: float
    duplication_max_pct: float
    issues_per_kloc_slocs_max: float
    docstring_coverage_min: float
    docstring_issues_per_kloc_cloc_max: float
    vuln_high_max: int
    vuln_medium_max: int


STRICTNESS: dict[str, Thresholds] = {
    "Low": Thresholds(
        coverage_line_min=70.0,
        coverage_branch_min=65.0,
        pylint_score_min=7.0,
        cyclomatic_max=15,
        maintainability_index_min=10.0,
        duplication_max_pct=25.0,
        issues_per_kloc_slocs_max=25.0,
        docstring_coverage_min=70.0,
        docstring_issues_per_kloc_cloc_max=8.0,
        vuln_high_max=2,
        vuln_medium_max=25,
    ),
    "Medium": Thresholds(
        coverage_line_min=85.0,
        coverage_branch_min=80.0,
        pylint_score_min=8.0,
        cyclomatic_max=10,
        maintainability_index_min=20.0,
        duplication_max_pct=15.0,
        issues_per_kloc_slocs_max=15.0,
        docstring_coverage_min=85.0,
        docstring_issues_per_kloc_cloc_max=5.0,
        vuln_high_max=0,
        vuln_medium_max=10,
    ),
    "High": Thresholds(
        coverage_line_min=95.0,
        coverage_branch_min=95.0,
        pylint_score_min=9.0,
        cyclomatic_max=5,
        maintainability_index_min=60.0,
        duplication_max_pct=5.0,
        issues_per_kloc_slocs_max=5.0,
        docstring_coverage_min=95.0,
        docstring_issues_per_kloc_cloc_max=2.0,
        vuln_high_max=0,
        vuln_medium_max=5,
    ),
}


def normalized_strictness_level(raw: str) -> str:
    """Return ``Low`` | ``Medium`` | ``High`` (case-insensitive); unknown values map to Medium."""
    key = raw.strip().title()
    return key if key in STRICTNESS else "Medium"


# When STRICTNESS_LEVEL=High, these artifacts must exist (non-empty files) so gates are not skipped.
HIGH_REQUIRED_FILES: tuple[str, ...] = (
    "coverage.json",
    "pylint.json",
    "pylint_score.txt",
    "radon_cc.json",
    "radon_mi.json",
    "interrogate.txt",
    "ruff.json",
    "gitleaks.json",
    "bandit.json",
    "cloc.json",
)
