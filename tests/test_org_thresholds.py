"""Tests for org threshold YAML loading outside the gated package."""

from __future__ import annotations

from pathlib import Path

from scripts.org_thresholds import (
    default_python_floors,
    load_python_floors,
    parse_threshold_yaml,
)


def test_parse_threshold_yaml_ignores_comments_and_junk() -> None:
    """Parser keeps numeric keys and skips non-numeric / blank lines."""
    text = (
        '# header\n'
        'statement_coverage: 95  # PY-TEST-002\n'
        'bad: not-a-number\n'
        '\n'
        'avg_cyclomatic_complexity: 5.0\n'
        'orphan\n'
    )
    parsed = parse_threshold_yaml(text)
    assert parsed == {
        'statement_coverage': 95.0,
        'avg_cyclomatic_complexity': 5.0,
    }


def test_load_python_floors_missing_file(tmp_path: Path) -> None:
    """Absent YAML returns baked-in defaults."""
    floors = load_python_floors(tmp_path)
    assert floors == default_python_floors()


def test_load_python_floors_merges_yaml(tmp_path: Path) -> None:
    """Present YAML overlays matching keys onto defaults."""
    py_dir = tmp_path / 'docs' / 'guardrails' / 'python'
    py_dir.mkdir(parents=True)
    (py_dir / 'profile.thresholds.yml').write_text(
        'max_cyclomatic_complexity: 7\n'
        'avg_maintainability_index: 55\n'
        'ignored_extra: 1\n',
        encoding='utf-8',
    )
    floors = load_python_floors(tmp_path)
    assert floors['max_cyclomatic_complexity'] == 7.0
    assert floors['avg_maintainability_index'] == 55.0
    assert floors['statement_coverage'] == 95.0
