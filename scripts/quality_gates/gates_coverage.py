"""Coverage and Pylint score gates."""

from __future__ import annotations

from typing import Any

from scripts.quality_gates.config import Thresholds

RowList = list[dict[str, Any]]


def gate_coverage_line(
    line_cov: float | None,
    t: Thresholds,
    strictness_norm: str = "Medium",
) -> tuple[RowList, list[str]]:
    """Evaluate line coverage gate."""
    if line_cov is None:
        if strictness_norm == "High":
            row = {
                "gate": "Coverage (line)",
                "actual": "missing or unparseable coverage.json",
                "required": f">= {t.coverage_line_min:.1f}%",
                "ok": False,
            }
            return [row], ["line coverage"]
        return [], []
    ok = line_cov >= t.coverage_line_min
    row = {
        "gate": "Coverage (line)",
        "actual": f"{line_cov:.2f}%",
        "required": f">= {t.coverage_line_min:.1f}%",
        "ok": ok,
    }
    return [row], [] if ok else ["line coverage"]


def gate_coverage_branch(
    branch_cov: float | None,
    t: Thresholds,
    strictness_norm: str = "Medium",
) -> tuple[RowList, list[str]]:
    """Evaluate branch coverage gate."""
    if branch_cov is None:
        if strictness_norm == "High":
            row = {
                "gate": "Coverage (branch)",
                "actual": "missing or unparseable coverage.json",
                "required": f">= {t.coverage_branch_min:.1f}%",
                "ok": False,
            }
            return [row], ["branch coverage"]
        return [], []
    ok = branch_cov >= t.coverage_branch_min
    row = {
        "gate": "Coverage (branch)",
        "actual": f"{branch_cov:.2f}%",
        "required": f">= {t.coverage_branch_min:.1f}%",
        "ok": ok,
    }
    return [row], [] if ok else ["branch coverage"]


def gate_pylint(
    score: float | None,
    t: Thresholds,
    strictness_norm: str = "Medium",
) -> tuple[RowList, list[str]]:
    """Evaluate Pylint score gate (minimum /10)."""
    if score is None:
        if strictness_norm == "High":
            row = {
                "gate": "Pylint score",
                "actual": "missing or unparseable pylint_score.txt",
                "required": f">= {t.pylint_score_min:.1f}",
                "ok": False,
            }
            return [row], ["pylint score"]
        return [], []
    ok = score >= t.pylint_score_min
    row = {
        "gate": "Pylint score",
        "actual": f"{score:.2f}/10",
        "required": f">= {t.pylint_score_min:.1f}",
        "ok": ok,
    }
    return [row], [] if ok else ["pylint score"]
