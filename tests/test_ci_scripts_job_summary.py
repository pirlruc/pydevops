"""Tests for scripts.ci_scripts_job_summary."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts import ci_scripts_job_summary
from scripts.ci_scripts_job_summary import (
    build_summary,
    _interrogate_actual_pct,
    _log_tail_fence,
    _passed_failed_from_summary_line,
    _pylint_rating_value,
    _pytest_coverage_pct,
    _pytest_counts_phrase,
    _pytest_successful_failed,
    _radon_cc_for_summary,
    _radon_mi_for_summary,
    _read,
)


@pytest.fixture
def summary_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    d = tmp_path / '_ci_summary'
    d.mkdir()
    return d


def _write_ci_summary_fixture(d: Path) -> None:
    (d / 'pytest.txt').write_text(
        '================================ tests coverage ================================\n'
        'TOTAL                                              100      5    95%\n'
        '145 passed in 0.41s\n',
        encoding='utf-8',
    )
    (d / 'pylint.txt').write_text('Your code has been rated at 9.80/10\n', encoding='utf-8')
    (d / 'interrogate.txt').write_text(
        'RESULT: PASSED (minimum: 95.0%, actual: 100.0%)\n',
        encoding='utf-8',
    )
    (d / 'radon_cc.txt').write_text(
        'Overall max CC (across files)                      3.0  (limit ≤ 5.0)\n',
        encoding='utf-8',
    )
    (d / 'radon_mi.txt').write_text(
        'Minimum MI (worst file)                            55.00  (must be > 40.0)\n',
        encoding='utf-8',
    )


def _row_starting_with(md: str, prefix: str) -> str:
    for line in md.splitlines():
        if line.strip().startswith(prefix):
            return line

    return ''


def test_build_summary_tests_row(summary_dir: Path) -> None:
    _write_ci_summary_fixture(summary_dir)
    md = build_summary()
    row = _row_starting_with(md, '| **Tests** |')
    assert '**145** successful' in row and '**0** failed' in row
    assert '0.41s' not in row


def test_build_summary_coverage_row(summary_dir: Path) -> None:
    _write_ci_summary_fixture(summary_dir)
    md = build_summary()
    row = _row_starting_with(md, '| **Code Coverage** |')
    assert '**95%** line coverage' in row
    assert 'pytest-cov TOTAL' not in row
    assert '≥95% required' in row


def test_build_summary_has_header(summary_dir: Path) -> None:
    _write_ci_summary_fixture(summary_dir)
    md = build_summary()
    assert '## Scripts quality (CI)' in md
    assert '| Analysis | Result |' in md


def test_build_summary_table_analysis_headers(summary_dir: Path) -> None:
    _write_ci_summary_fixture(summary_dir)
    md = build_summary()
    prefixes = (
        '| **Tests** |',
        '| **Code Coverage** |',
        '| **Documentation Coverage** |',
        '| **Cyclomatic Complexity** |',
        '| **Maintainability Index** |',
    )
    for p in prefixes:
        assert _row_starting_with(md, p), f'missing row {p}'


def test_build_summary_code_quality_and_docstrings(summary_dir: Path) -> None:
    _write_ci_summary_fixture(summary_dir)
    md = build_summary()
    assert '9.80' in _row_starting_with(md, '| **Code Quality** |')
    assert '100.0%' in md


def test_build_summary_radon_threshold_phrases(summary_dir: Path) -> None:
    _write_ci_summary_fixture(summary_dir)
    md = build_summary()
    assert '≤5.0 required' in _row_starting_with(md, '| **Cyclomatic Complexity** |')
    assert '≥40.0 required' in _row_starting_with(md, '| **Maintainability Index** |')


def test_pytest_counts_with_failures() -> None:
    log = '2 failed, 143 passed in 1.23s\n'
    assert _pytest_counts_phrase(log) == '**143** successful, **2** failed'
    assert '1.23s' not in _pytest_counts_phrase(log)


def test_passed_failed_from_summary_line() -> None:
    assert _passed_failed_from_summary_line('2 failed, 143 passed in 1s') == (143, 2)
    assert _passed_failed_from_summary_line('145 passed in 0.41s') == (145, 0)


def test_build_summary_empty_logs_use_placeholders(summary_dir: Path) -> None:
    md = build_summary()
    assert '## Scripts quality (CI)' in md
    assert '(empty)' in md
    assert '—' in md


def test_read_missing_file_is_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / '_ci_summary').mkdir()
    assert _read('nope.txt') == ''


def test_pytest_counts_phrase_empty() -> None:
    assert _pytest_counts_phrase('') == '—'


def test_pytest_successful_failed_empty() -> None:
    assert _pytest_successful_failed('') is None


def test_pytest_coverage_pct_missing() -> None:
    assert _pytest_coverage_pct('no total line') == ''


def test_pylint_rating_value_missing() -> None:
    assert _pylint_rating_value('no rating') == ''


def test_interrogate_actual_pct_missing() -> None:
    assert _interrogate_actual_pct('no percent here') == ''


def test_radon_cc_for_summary_missing() -> None:
    assert _radon_cc_for_summary('no cc line') == '—'


def test_radon_mi_for_summary_missing() -> None:
    assert _radon_mi_for_summary('no mi line') == '—'


def test_log_tail_fence_empty() -> None:
    assert _log_tail_fence('   \n', 5) == '(empty)'


def test_main_prints_summary(
    summary_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, 'argv', ['ci_scripts_job_summary.py'])
    assert ci_scripts_job_summary.main() == 0
    out = capsys.readouterr().out
    assert '## Scripts quality (CI)' in out


def test_script___main___guard(summary_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    monkeypatch.chdir(summary_dir.parent)
    path = Path(ci_scripts_job_summary.__file__).resolve()
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(path), run_name='__main__')

    assert exc_info.value.code == 0
