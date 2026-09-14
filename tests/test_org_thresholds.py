"""Tests for org threshold YAML loading outside the gated package."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.org_thresholds import (
    ThresholdError,
    default_python_floors,
    load_ci_thresholds,
    load_python_floors,
    parse_threshold_yaml,
    self_ci_max_cyclomatic,
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


def test_load_python_floors_missing_file_loud_fallback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Absent YAML warns on stderr and returns baked-in defaults."""
    floors = load_python_floors(tmp_path)
    assert floors == default_python_floors()
    err = capsys.readouterr().err
    assert 'CI-022' in err
    assert 'baked-in High floors' in err


def test_load_python_floors_missing_file_fail_closed(tmp_path: Path) -> None:
    """Absent YAML raises when the no-checkout fallback is disabled."""
    with pytest.raises(ThresholdError, match='CI-022'):
        load_python_floors(tmp_path, allow_missing_checkout=False)


def test_load_python_floors_missing_key_fail_closed(tmp_path: Path) -> None:
    """Present YAML missing a required key fails closed."""
    py_dir = tmp_path / 'docs' / 'guardrails' / 'python'
    py_dir.mkdir(parents=True)
    (py_dir / 'profile.thresholds.yml').write_text(
        'statement_coverage: 95\n',
        encoding='utf-8',
    )
    with pytest.raises(ThresholdError, match='missing threshold key'):
        load_python_floors(tmp_path)


def test_load_python_floors_reads_yaml(tmp_path: Path) -> None:
    """Present YAML supplies required keys including lint_exception_max_days."""
    py_dir = tmp_path / 'docs' / 'guardrails' / 'python'
    py_dir.mkdir(parents=True)
    (py_dir / 'profile.thresholds.yml').write_text(
        'statement_coverage: 95\n'
        'branch_coverage: 95\n'
        'doc_coverage: 90\n'
        'max_cyclomatic_complexity: 7\n'
        'avg_cyclomatic_complexity: 5\n'
        'min_maintainability_index: 40\n'
        'avg_maintainability_index: 55\n'
        'lint_exception_max_days: 14\n',
        encoding='utf-8',
    )
    floors = load_python_floors(tmp_path)
    assert floors['max_cyclomatic_complexity'] == 7.0
    assert floors['avg_maintainability_index'] == 55.0
    assert floors['doc_coverage'] == 90.0
    assert floors['lint_exception_max_days'] == 14.0


def test_load_python_floors_prefers_submodule_over_vendor(tmp_path: Path) -> None:
    """Guardrails submodule wins over the vendored scripts/ copy."""
    py_dir = tmp_path / 'docs' / 'guardrails' / 'python'
    py_dir.mkdir(parents=True)
    body = (
        'statement_coverage: 95\n'
        'branch_coverage: 95\n'
        'doc_coverage: 95\n'
        'max_cyclomatic_complexity: 8\n'
        'avg_cyclomatic_complexity: 5\n'
        'min_maintainability_index: 40\n'
        'avg_maintainability_index: 60\n'
    )
    (py_dir / 'profile.thresholds.yml').write_text(
        body.replace('max_cyclomatic_complexity: 8', 'max_cyclomatic_complexity: 3'),
        encoding='utf-8',
    )
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    (scripts / 'python.profile.thresholds.yml').write_text(body, encoding='utf-8')
    floors = load_python_floors(tmp_path)
    assert floors['max_cyclomatic_complexity'] == 3.0


def test_self_ci_max_cyclomatic_stricter_than_high() -> None:
    """Maintainer CI CC 5 is min(org, 5); no deviation for being stricter."""
    floors = default_python_floors()
    assert floors['max_cyclomatic_complexity'] == 8.0
    assert self_ci_max_cyclomatic(floors) == 5.0


def test_load_ci_thresholds_fail_closed_missing_key(tmp_path: Path) -> None:
    """CI pack missing a required key fails closed."""
    ci_dir = tmp_path / 'docs' / 'guardrails' / 'ci'
    ci_dir.mkdir(parents=True)
    (ci_dir / 'profile.thresholds.yml').write_text(
        'ci_image_max_age_days: 30\n',
        encoding='utf-8',
    )
    with pytest.raises(ThresholdError, match='missing threshold key'):
        load_ci_thresholds(tmp_path)


def test_load_ci_thresholds_missing_file_loud_fallback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Absent CI pack warns and returns empty mapping."""
    loaded = load_ci_thresholds(tmp_path)
    assert loaded == {}
    assert 'CI-022' in capsys.readouterr().err


def test_load_ci_thresholds_missing_file_fail_closed(tmp_path: Path) -> None:
    """Absent CI pack raises when fallback is disabled."""
    with pytest.raises(ThresholdError, match='CI-022'):
        load_ci_thresholds(tmp_path, allow_missing_checkout=False)


def test_load_ci_thresholds_reads_pack(tmp_path: Path) -> None:
    """CI pack loads CI-027 / CI-003 / CI-029 keys."""
    ci_dir = tmp_path / 'docs' / 'guardrails' / 'ci'
    ci_dir.mkdir(parents=True)
    (ci_dir / 'profile.thresholds.yml').write_text(
        'ci_image_max_age_days: 30\n'
        'ci_job_timeout_minutes_max: 60\n'
        'security_rescan_interval_days: 30\n',
        encoding='utf-8',
    )
    loaded = load_ci_thresholds(tmp_path)
    assert loaded['ci_job_timeout_minutes_max'] == 60.0
