"""Parse Semgrep SARIF for High-tier policy gates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.jsonutil import read_json


def _result_level(result: Any) -> str | None:
    """Return normalized SARIF result level, or None if missing or invalid."""
    if not isinstance(result, dict):
        return None
    level = result.get("level")
    return level.lower() if isinstance(level, str) else None


def _error_warning_delta_for_result(res: Any) -> tuple[int, int]:
    """Return (error_count, warning_count) contribution for one SARIF result."""
    lvl = _result_level(res)
    if lvl == "error":
        return 1, 0
    if lvl == "warning":
        return 0, 1
    return 0, 0


def _count_error_warning_in_results(results: list[Any]) -> tuple[int, int]:
    """Sum error- and warning-level counts in one results array."""
    n_error = 0
    n_warning = 0
    for res in results:
        de, dw = _error_warning_delta_for_result(res)
        n_error += de
        n_warning += dw
    return n_error, n_warning


def _accumulate_from_runs(runs: list[Any]) -> tuple[int, int]:
    """Sum counts across SARIF runs (skips malformed run nodes)."""
    n_error = 0
    n_warning = 0
    for run in runs:
        if not isinstance(run, dict):
            continue
        results = run.get("results")
        if not isinstance(results, list):
            continue
        de, dw = _count_error_warning_in_results(results)
        n_error += de
        n_warning += dw
    return n_error, n_warning


def semgrep_sarif_error_warning_counts(root: Path) -> tuple[int, int] | None:
    """
    Count SARIF result severities mapped to policy buckets.

    Semgrep maps rule severity to SARIF ``level``: error (blocking), warning, note.

    Returns (error_level_count, warning_level_count) summed across all runs, or None
    if the file is missing, invalid JSON, or not a SARIF object with a runs list.
    """
    data = read_json(root / "semgrep.sarif")
    if data is None or not isinstance(data, dict):
        return None
    runs = data.get("runs")
    if not isinstance(runs, list):
        return None
    return _accumulate_from_runs(runs)
