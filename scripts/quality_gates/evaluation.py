"""Collect gate rows and failure messages; ``evaluate`` also writes ``gates.json``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.quality_gates.config import (
    Thresholds,
    normalized_strictness_level,
    resolve_thresholds,
    scripts_only_package,
)
from scripts.quality_gates.gates_artifacts import enforce_high_artifact_presence
from scripts.quality_gates.gates_complexity import (
    gate_cyclomatic,
    gate_cyclomatic_avg,
    gate_duplication,
    gate_issues_per_kloc,
    gate_maintainability,
    gate_maintainability_avg,
)
from scripts.quality_gates.gates_coverage import (
    gate_coverage_branch,
    gate_coverage_line,
    gate_pylint,
    gate_pytest_exit,
)
from scripts.quality_gates.gates_docstrings import (
    gate_docstring_coverage,
    gate_docstring_issue_rate,
)
from scripts.quality_gates.gates_mypy import gate_mypy
from scripts.quality_gates.gates_security import (
    gate_bandit,
    gate_gitleaks,
    gate_semgrep,
    gate_vulnerabilities,
)
from scripts.quality_gates.readers_cloc_docs import (
    cloc_slocs_comments,
    interrogate_coverage,
    pydoclint_issue_count,
)
from scripts.quality_gates.readers_py_coverage import (
    load_coverage_totals,
    pylint_issue_count,
    pylint_score,
    pytest_exit_code,
)
from scripts.quality_gates.readers_radon import (
    radon_cc_avg,
    radon_cc_max,
    radon_mi_avg,
    radon_mi_min,
)
from scripts.quality_gates.readers_ruff_jscpd import jscpd_duplication_pct, ruff_issue_count


def _extend(
    rows: list[dict[str, Any]],
    failures: list[str],
    result: tuple[list[dict[str, Any]], list[str]],
) -> None:
    """Append one gate's rows and failure labels."""
    gate_rows, gate_failures = result
    rows.extend(gate_rows)
    failures.extend(gate_failures)


def _coverage_and_lint(
    root: Path,
    thresholds: Thresholds,
    strictness: str,
    scripts_only: bool,
    rows: list[dict[str, Any]],
    failures: list[str],
) -> None:
    """Coverage, pylint, and pytest rows. Scripts-only skips coverage."""
    if not scripts_only:
        _extend(rows, failures, enforce_high_artifact_presence(root, strictness))
        line_cov, branch_cov = load_coverage_totals(root)
        _extend(rows, failures, gate_coverage_line(line_cov, thresholds, strictness))
        _extend(rows, failures, gate_coverage_branch(branch_cov, thresholds, strictness))
    else:
        rows.append({
            'gate': 'Package mode',
            'actual': 'scripts',
            'required': 'skip install, mypy, and coverage floors',
            'ok': True,
        })
    _extend(rows, failures, gate_pylint(pylint_score(root), thresholds, strictness))
    if not scripts_only:
        _extend(rows, failures, gate_pytest_exit(pytest_exit_code(root), strictness))


def _complexity(
    root: Path,
    thresholds: Thresholds,
    strictness: str,
    rows: list[dict[str, Any]],
    failures: list[str],
) -> tuple[int, int]:
    """Complexity and duplication rows. Returns cloc sloc and comment counts."""
    _extend(rows, failures, gate_cyclomatic(radon_cc_max(root), thresholds, strictness))
    _extend(rows, failures, gate_cyclomatic_avg(radon_cc_avg(root), thresholds, strictness))
    _extend(rows, failures, gate_maintainability(radon_mi_min(root), thresholds, strictness))
    _extend(rows, failures, gate_maintainability_avg(radon_mi_avg(root), thresholds, strictness))
    _extend(rows, failures, gate_duplication(jscpd_duplication_pct(root), thresholds))
    sloc, comment_lines = cloc_slocs_comments(root)
    _extend(
        rows,
        failures,
        gate_issues_per_kloc(sloc, pylint_issue_count(root), ruff_issue_count(root), thresholds),
    )
    return sloc, comment_lines


def _docs_and_security(
    root: Path,
    thresholds: Thresholds,
    strictness: str,
    scripts_only: bool,
    sloc: int,
    comment_lines: int,
    rows: list[dict[str, Any]],
    failures: list[str],
) -> None:
    """Docs, types, and security rows."""
    if not scripts_only:
        _extend(rows, failures, gate_mypy(root, sloc, thresholds, strictness))
    _extend(
        rows,
        failures,
        gate_docstring_coverage(interrogate_coverage(root), thresholds, strictness),
    )
    _extend(
        rows,
        failures,
        gate_docstring_issue_rate(comment_lines, pydoclint_issue_count(root), thresholds),
    )
    _extend(rows, failures, gate_bandit(root, thresholds))
    _extend(rows, failures, gate_vulnerabilities(root, thresholds))
    _extend(rows, failures, gate_gitleaks(root))
    _extend(rows, failures, gate_semgrep(root, strictness))


def collect_gate_results(
    root: Path,
    strictness: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Run all gate checks and return (rows, failure labels)."""
    normalized = normalized_strictness_level(strictness)
    thresholds = resolve_thresholds(strictness)
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    scripts_only = scripts_only_package()
    _coverage_and_lint(root, thresholds, normalized, scripts_only, rows, failures)
    sloc, comment_lines = _complexity(root, thresholds, normalized, rows, failures)
    _docs_and_security(
        root,
        thresholds,
        normalized,
        scripts_only,
        sloc,
        comment_lines,
        rows,
        failures,
    )
    return rows, failures


def evaluate_semgrep_shield_only(root: Path, strictness: str) -> tuple[bool, list[dict[str, Any]]]:
    """Run only the Semgrep SARIF gate (High strictness); always pass for Low/Medium."""
    sn = normalized_strictness_level(strictness)
    rows, failures = gate_semgrep(root, sn)
    return len(failures) == 0, rows


def evaluate(root: Path, strictness: str) -> tuple[bool, list[dict[str, Any]]]:
    """Run all gates for ``strictness`` and write ``gates.json`` under ``root``."""
    rows, failures = collect_gate_results(root, strictness)
    passed = len(failures) == 0
    root.mkdir(parents=True, exist_ok=True)
    (root / 'gates.json').write_text(
        json.dumps({'passed': passed, 'failures': failures, 'rows': rows}, indent=2),
        encoding='utf-8',
    )
    return passed, rows
