"""Tests for ``scripts.quality_gates.readers_cloc_docs``."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.quality_gates.readers_cloc_docs import cloc_slocs_comments, pydoclint_issue_count


def test_pydoclint_issue_count_ignores_summary_lines(tmp_path: Path) -> None:
    """Summary lines mentioning 'errors' must not inflate the issue count."""
    p = tmp_path / 'pydoclint.txt'
    p.write_text(
        '0 errors\nNo errors found.\nSummary: 0 errors in 3 files\n',
        encoding='utf-8',
    )
    assert pydoclint_issue_count(tmp_path) == 0


def test_pydoclint_issue_count_counts_flake8_style_violations(tmp_path: Path) -> None:
    """Violations use ``path:line:col: ERROR`` (flake8-style)."""
    p = tmp_path / 'pydoclint.txt'
    p.write_text(
        'src/mod.py:10:1: ERROR Violation D100\nsrc/other.py:2:3: ERROR something else\n',
        encoding='utf-8',
    )
    assert pydoclint_issue_count(tmp_path) == 2


def test_pydoclint_issue_count_missing_file(tmp_path: Path) -> None:
    """No pydoclint.txt yields zero issues."""
    assert pydoclint_issue_count(tmp_path) == 0


def test_cloc_slocs_comments_null_non_numeric(tmp_path: Path) -> None:
    """Malformed ``code`` / ``comment`` must not raise (null, lists → 0)."""
    (tmp_path / 'cloc.json').write_text(
        json.dumps({'Python': {'code': None, 'comment': [1, 2]}}),
        encoding='utf-8',
    )
    assert cloc_slocs_comments(tmp_path) == (0.0, 0.0)


def test_cloc_slocs_comments_unparsable_strings(tmp_path: Path) -> None:
    """Non-numeric strings for metrics yield zeros."""
    (tmp_path / 'cloc.json').write_text(
        json.dumps({'Python': {'code': 'nope', 'comment': ''}}),
        encoding='utf-8',
    )
    assert cloc_slocs_comments(tmp_path) == (0.0, 0.0)


def test_cloc_slocs_comments_string_numbers(tmp_path: Path) -> None:
    """Numeric strings from cloc are accepted."""
    (tmp_path / 'cloc.json').write_text(
        json.dumps({'Python': {'code': '100', 'comment': '10'}}),
        encoding='utf-8',
    )
    assert cloc_slocs_comments(tmp_path) == (100.0, 10.0)
