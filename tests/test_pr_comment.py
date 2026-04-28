"""Tests for ``scripts.pr_comment_markdown``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.pr_comment_markdown import main as pr_main


def test_pr_comment_empty_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without gates.json, emit placeholder Markdown."""
    monkeypatch.setenv('QUALITY_OUTPUT_DIR', str(tmp_path))
    assert pr_main() == 0
    out = capsys.readouterr().out
    assert 'gates output' in out.lower() or 'quality' in out.lower()


def test_pr_comment_with_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With gates.json, table includes gate rows."""
    (tmp_path / 'gates.json').write_text(
        json.dumps(
            {
                'passed': True,
                'rows': [{'gate': 'Test', 'actual': '1', 'required': '0', 'ok': True}],
            },
        ),
        encoding='utf-8',
    )
    monkeypatch.setenv('QUALITY_OUTPUT_DIR', str(tmp_path))
    assert pr_main() == 0
    out = capsys.readouterr().out
    assert 'Test' in out
    assert 'PASS' in out


def test_pr_comment_failed_overall(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """FAILED shown when passed is false."""
    (tmp_path / 'gates.json').write_text(
        json.dumps({'passed': False, 'rows': []}),
        encoding='utf-8',
    )
    monkeypatch.setenv('QUALITY_OUTPUT_DIR', str(tmp_path))
    assert pr_main() == 0
    assert 'FAILED' in capsys.readouterr().out


def test_pr_comment_missing_passed_defaults_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing ``passed`` is treated conservatively as failed."""
    (tmp_path / 'gates.json').write_text(
        json.dumps({'rows': [{'gate': 'X', 'actual': '1', 'required': '1', 'ok': True}]}),
        encoding='utf-8',
    )
    monkeypatch.setenv('QUALITY_OUTPUT_DIR', str(tmp_path))
    assert pr_main() == 0
    assert 'FAILED' in capsys.readouterr().out


def test_pr_comment_table_cells_sanitize_pipe_and_newlines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pipe and newline in cell values must not break GFM table columns."""
    (tmp_path / 'gates.json').write_text(
        json.dumps(
            {
                'passed': True,
                'rows': [
                    {
                        'gate': 'a|b',
                        'actual': 'c\nd',
                        'required': 'ok',
                        'ok': True,
                    },
                ],
            },
        ),
        encoding='utf-8',
    )
    monkeypatch.setenv('QUALITY_OUTPUT_DIR', str(tmp_path))
    assert pr_main() == 0
    out = capsys.readouterr().out
    assert '\u00a6' in out
    assert 'c d' in out


def test_pr_comment_coerces_malformed_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Non-list ``rows`` does not crash; overall summary is failed."""
    (tmp_path / 'gates.json').write_text(
        json.dumps({'passed': True, 'rows': 'bad'}),
        encoding='utf-8',
    )
    monkeypatch.setenv('QUALITY_OUTPUT_DIR', str(tmp_path))
    assert pr_main() == 0
    assert 'FAILED' in capsys.readouterr().out
