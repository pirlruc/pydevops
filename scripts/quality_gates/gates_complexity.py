"""Complexity, maintainability, duplication, and issue-density gates."""

from __future__ import annotations

from typing import Any

from scripts.quality_gates.config import Thresholds

RowList = list[dict[str, Any]]


def _missing_metric_row(gate: str, required: str, actual: str) -> dict[str, Any]:
    """Build a standardized failing row for missing metrics."""
    return {"gate": gate, "actual": actual, "required": required, "ok": False}


def gate_cyclomatic(
    cc: float | None,
    t: Thresholds,
    strictness_norm: str = "Medium",
) -> tuple[RowList, list[str]]:
    """Evaluate max cyclomatic complexity (High: max <= 5, strictly below 6)."""
    req = f"<= {t.cyclomatic_max:.0f}"
    if t.cyclomatic_max <= 5:
        req += ", target <= 4"
    label = "Cyclomatic complexity (max; High < 6)"
    if cc is None:
        if strictness_norm == "High":
            row = _missing_metric_row(label, req, "missing or unparseable radon_cc.json")
            return [row], ["cyclomatic complexity"]
        return [], []
    ok = cc <= t.cyclomatic_max
    row = {
        "gate": label,
        "actual": f"{cc:.1f}",
        "required": req,
        "ok": ok,
    }
    return [row], [] if ok else ["cyclomatic complexity"]


def gate_maintainability(
    mi: float | None,
    t: Thresholds,
    strictness_norm: str = "Medium",
) -> tuple[RowList, list[str]]:
    """Evaluate minimum MI across files (High targets >= 60)."""
    if mi is None:
        if strictness_norm == "High":
            row = _missing_metric_row(
                "Maintainability index (min; High targets >= 60)",
                f">= {t.maintainability_index_min:.1f}",
                "missing or unparseable radon_mi.json",
            )
            return [row], ["maintainability index"]
        return [], []
    ok = mi >= t.maintainability_index_min
    row = {
        "gate": "Maintainability index (min; High targets >= 60)",
        "actual": f"{mi:.1f}",
        "required": f">= {t.maintainability_index_min:.1f}",
        "ok": ok,
    }
    return [row], [] if ok else ["maintainability index"]


def gate_duplication(
    dup: float | None,
    t: Thresholds,
) -> tuple[RowList, list[str]]:
    """Evaluate jscpd duplication percentage."""
    if dup is None:
        row = {
            "gate": "Duplication (jscpd)",
            "actual": "(missing or invalid jscpd-report.json)",
            "required": f"<= {t.duplication_max_pct:.1f}%",
            "ok": False,
        }
        return [row], ["duplication"]
    ok = dup <= t.duplication_max_pct
    row = {
        "gate": "Duplication (jscpd)",
        "actual": f"{dup:.2f}%",
        "required": f"<= {t.duplication_max_pct:.1f}%",
        "ok": ok,
    }
    return [row], [] if ok else ["duplication"]


def gate_issues_per_kloc(
    sloc: float,
    pylint_n: int,
    ruff_n: int,
    t: Thresholds,
) -> tuple[RowList, list[str]]:
    """Evaluate combined Pylint+Ruff issues per KLoC (SLOC)."""
    if sloc <= 0:
        return [], []
    issues = pylint_n + ruff_n
    per_k = (issues / sloc) * 1000.0
    ok = per_k <= t.issues_per_kloc_slocs_max
    row = {
        "gate": "Code issues per KLoC (SLOC)",
        "actual": f"{per_k:.2f}",
        "required": f"<= {t.issues_per_kloc_slocs_max:.1f}",
        "ok": ok,
    }
    return [row], [] if ok else ["issues per KLoC (SLOC)"]
