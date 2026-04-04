"""Docstring coverage and pydoclint-derived gates."""

from __future__ import annotations

from typing import Any

from scripts.quality_gates.config import Thresholds

RowList = list[dict[str, Any]]


def gate_docstring_coverage(
    doc_cov: float | None,
    t: Thresholds,
    strictness_norm: str = "Medium",
) -> tuple[RowList, list[str]]:
    """Evaluate interrogate docstring coverage against tier thresholds."""
    if doc_cov is None:
        if strictness_norm == "High":
            row = {
                "gate": "Docstring coverage",
                "actual": "missing or unparseable interrogate.txt",
                "required": f">= {t.docstring_coverage_min:.1f}%",
                "ok": False,
            }
            return [row], ["docstring coverage"]
        return [], []
    ok = doc_cov >= t.docstring_coverage_min
    row = {
        "gate": "Docstring coverage",
        "actual": f"{doc_cov:.2f}%",
        "required": f">= {t.docstring_coverage_min:.1f}%",
        "ok": ok,
    }
    return [row], [] if ok else ["docstring coverage"]


def gate_docstring_issue_rate(
    cloc: float,
    pydoc_n: int,
    t: Thresholds,
) -> tuple[RowList, list[str]]:
    """Evaluate pydoclint issues per KLoC of comments."""
    if cloc <= 0:
        return [], []
    doc_per_k = (pydoc_n / cloc) * 1000.0
    ok = doc_per_k <= t.docstring_issues_per_kloc_cloc_max
    row = {
        "gate": "Docstring issue rate (per KLoC comments)",
        "actual": f"{doc_per_k:.2f}",
        "required": f"<= {t.docstring_issues_per_kloc_cloc_max:.1f}",
        "ok": ok,
    }
    return [row], [] if ok else ["docstring issue rate"]
