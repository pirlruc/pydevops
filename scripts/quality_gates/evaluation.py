"""Collect gate rows and failure messages; ``evaluate`` also writes ``gates.json``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.quality_gates.config import STRICTNESS, Thresholds, normalized_strictness_level
from scripts.quality_gates.gates_artifacts import enforce_high_artifact_presence
from scripts.quality_gates.gates_complexity import (
    gate_cyclomatic,
    gate_duplication,
    gate_issues_per_kloc,
    gate_maintainability,
)
from scripts.quality_gates.gates_coverage import (
    gate_coverage_branch,
    gate_coverage_line,
    gate_pylint,
)
from scripts.quality_gates.gates_docstrings import (
    gate_docstring_coverage,
    gate_docstring_issue_rate,
)
from scripts.quality_gates.gates_security import gate_gitleaks, gate_vulnerabilities
from scripts.quality_gates.readers_cloc_docs import (
    cloc_slocs_comments,
    interrogate_coverage,
    pydoclint_issue_count,
)
from scripts.quality_gates.readers_py_coverage import (
    load_coverage_totals,
    pylint_issue_count,
    pylint_score,
)
from scripts.quality_gates.readers_radon import radon_cc_max, radon_mi_min
from scripts.quality_gates.readers_ruff_jscpd import jscpd_duplication_pct, ruff_issue_count


def collect_gate_results(  # pylint: disable=too-many-locals
    root: Path, strictness: str
) -> tuple[list[dict[str, Any]], list[str]]:
    """Run all gate checks and return (rows, failure labels)."""
    sn = normalized_strictness_level(strictness)
    t: Thresholds = STRICTNESS[sn]
    rows: list[dict[str, Any]] = []
    failures: list[str] = []

    art_rows, art_fail = enforce_high_artifact_presence(root, sn)
    rows.extend(art_rows)
    failures.extend(art_fail)

    line_cov, branch_cov = load_coverage_totals(root)
    r, f = gate_coverage_line(line_cov, t, sn)
    rows.extend(r)
    failures.extend(f)
    r, f = gate_coverage_branch(branch_cov, t, sn)
    rows.extend(r)
    failures.extend(f)

    r, f = gate_pylint(pylint_score(root), t, sn)
    rows.extend(r)
    failures.extend(f)

    r, f = gate_cyclomatic(radon_cc_max(root), t, sn)
    rows.extend(r)
    failures.extend(f)

    r, f = gate_maintainability(radon_mi_min(root), t, sn)
    rows.extend(r)
    failures.extend(f)

    r, f = gate_duplication(jscpd_duplication_pct(root), t)
    rows.extend(r)
    failures.extend(f)

    sloc, cloc = cloc_slocs_comments(root)
    r, f = gate_issues_per_kloc(sloc, pylint_issue_count(root), ruff_issue_count(root), t)
    rows.extend(r)
    failures.extend(f)

    r, f = gate_docstring_coverage(interrogate_coverage(root), t, sn)
    rows.extend(r)
    failures.extend(f)

    r, f = gate_docstring_issue_rate(cloc, pydoclint_issue_count(root), t)
    rows.extend(r)
    failures.extend(f)

    r, f = gate_vulnerabilities(root, t)
    rows.extend(r)
    failures.extend(f)

    r, f = gate_gitleaks(root)
    rows.extend(r)
    failures.extend(f)

    return rows, failures


def evaluate(root: Path, strictness: str) -> tuple[bool, list[dict[str, Any]]]:
    """Run all gates for ``strictness`` and write ``gates.json`` under ``root``."""
    rows, failures = collect_gate_results(root, strictness)
    passed = len(failures) == 0
    root.mkdir(parents=True, exist_ok=True)
    (root / "gates.json").write_text(
        json.dumps({"passed": passed, "failures": failures, "rows": rows}, indent=2),
        encoding="utf-8",
    )
    return passed, rows
