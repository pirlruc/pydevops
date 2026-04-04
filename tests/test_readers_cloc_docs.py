"""Tests for ``scripts.quality_gates.readers_cloc_docs``."""

from __future__ import annotations

from pathlib import Path

from scripts.quality_gates.readers_cloc_docs import pydoclint_issue_count


def test_pydoclint_issue_count_ignores_summary_lines(tmp_path: Path) -> None:
    """Summary lines mentioning 'errors' must not inflate the issue count."""
    p = tmp_path / "pydoclint.txt"
    p.write_text(
        "0 errors\nNo errors found.\nSummary: 0 errors in 3 files\n",
        encoding="utf-8",
    )
    assert pydoclint_issue_count(tmp_path) == 0


def test_pydoclint_issue_count_counts_flake8_style_violations(tmp_path: Path) -> None:
    """Violations use ``path:line:col: ERROR`` (flake8-style)."""
    p = tmp_path / "pydoclint.txt"
    p.write_text(
        "src/mod.py:10:1: ERROR Violation D100\n"
        "src/other.py:2:3: ERROR something else\n",
        encoding="utf-8",
    )
    assert pydoclint_issue_count(tmp_path) == 2


def test_pydoclint_issue_count_missing_file(tmp_path: Path) -> None:
    """No pydoclint.txt yields zero issues."""
    assert pydoclint_issue_count(tmp_path) == 0
