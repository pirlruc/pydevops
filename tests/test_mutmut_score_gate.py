"""Tests for scripts.mutmut_score_gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import mutmut_score_gate as msg


def test_gate_passes_at_threshold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Score exactly at minimum passes."""
    p = tmp_path / 'stats.json'
    p.write_text(json.dumps({'killed': 85, 'survived': 15}), encoding='utf-8')
    monkeypatch.setenv('MUTMUT_CICD_STATS', str(p))
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '85')
    assert msg.main() == 0


def test_gate_fails_below_threshold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Score below minimum fails."""
    p = tmp_path / 'stats.json'
    p.write_text(json.dumps({'killed': 84, 'survived': 16}), encoding='utf-8')
    monkeypatch.setenv('MUTMUT_CICD_STATS', str(p))
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '85')
    assert msg.main() == 1


def test_gate_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('MUTMUT_CICD_STATS', str(tmp_path / 'nope.json'))
    assert msg.main() == 1


def test_gate_zero_denominator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / 'stats.json'
    p.write_text(json.dumps({'killed': 0, 'survived': 0}), encoding='utf-8')
    monkeypatch.setenv('MUTMUT_CICD_STATS', str(p))
    assert msg.main() == 1


def test_gate_invalid_min_score_not_a_number(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    p = tmp_path / 'stats.json'
    p.write_text(json.dumps({'killed': 90, 'survived': 10}), encoding='utf-8')
    monkeypatch.setenv('MUTMUT_CICD_STATS', str(p))
    monkeypatch.setenv('MUTMUT_MIN_SCORE', 'not-a-float')
    assert msg.main() == 1
    err = capsys.readouterr().err
    assert 'MUTMUT_MIN_SCORE must be a number' in err


def test_gate_min_score_out_of_range(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    p = tmp_path / 'stats.json'
    p.write_text(json.dumps({'killed': 90, 'survived': 10}), encoding='utf-8')
    monkeypatch.setenv('MUTMUT_CICD_STATS', str(p))
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '101')
    assert msg.main() == 1
    err = capsys.readouterr().err
    assert 'between 0 and 100' in err
