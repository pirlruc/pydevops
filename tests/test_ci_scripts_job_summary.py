"""Tests for scripts.ci_scripts_job_summary."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts import ci_scripts_job_summary
from scripts.ci_scripts_job_summary import (
    build_summary,
    _interrogate_pct,
    _log_tail_fence,
    _pylint_rating,
    _pytest_coverage_line,
    _pytest_tests_line,
    _radon_cc_summary,
    _radon_mi_summary,
    _read,
)


@pytest.fixture
def summary_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "_ci_summary"
    d.mkdir()
    return d


def _write_ci_summary_fixture(d: Path) -> None:
    (d / "pytest.txt").write_text(
        "================================ tests coverage ================================\n"
        "TOTAL                                              100      5    95%\n"
        "145 passed in 0.41s\n",
        encoding="utf-8",
    )
    (d / "pylint.txt").write_text("Your code has been rated at 9.80/10\n", encoding="utf-8")
    (d / "interrogate.txt").write_text(
        "RESULT: PASSED (minimum: 95.0%, actual: 100.0%)\n",
        encoding="utf-8",
    )
    (d / "radon_cc.txt").write_text(
        "Overall max CC (across files)                      3.0  (limit ≤ 5.0)\n",
        encoding="utf-8",
    )
    (d / "radon_mi.txt").write_text(
        "Minimum MI (worst file)                            55.00  (must be > 40.0)\n",
        encoding="utf-8",
    )


def test_build_summary_pytest_coverage(summary_dir: Path) -> None:
    _write_ci_summary_fixture(summary_dir)
    md = build_summary()
    assert "## Scripts quality (CI)" in md
    assert "145 passed" in md
    assert "**95%**" in md


def test_build_summary_pylint_interrogate_radon(summary_dir: Path) -> None:
    _write_ci_summary_fixture(summary_dir)
    md = build_summary()
    assert "9.80" in md
    assert "100.0%" in md
    assert "Overall max CC" in md
    assert "Minimum MI" in md


def test_build_summary_empty_logs_use_placeholders(summary_dir: Path) -> None:
    md = build_summary()
    assert "## Scripts quality (CI)" in md
    assert "(empty)" in md
    assert "—" in md


def test_read_missing_file_is_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_ci_summary").mkdir()
    assert _read("nope.txt") == ""


def test_pytest_tests_line_empty() -> None:
    assert _pytest_tests_line("") == "—"


def test_pytest_coverage_line_missing_total() -> None:
    assert _pytest_coverage_line("no total line") == "—"


def test_pylint_rating_missing() -> None:
    assert _pylint_rating("no rating") == "—"


def test_interrogate_pct_missing() -> None:
    assert _interrogate_pct("no percent here") == "—"


def test_radon_cc_summary_missing() -> None:
    assert _radon_cc_summary("no cc line") == "—"


def test_radon_mi_summary_missing() -> None:
    assert _radon_mi_summary("no mi line") == "—"


def test_log_tail_fence_empty() -> None:
    assert _log_tail_fence("   \n", 5) == "(empty)"


def test_main_prints_summary(
    summary_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["ci_scripts_job_summary.py"])
    assert ci_scripts_job_summary.main() == 0
    out = capsys.readouterr().out
    assert "## Scripts quality (CI)" in out


def test_script___main___guard(summary_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    monkeypatch.chdir(summary_dir.parent)
    path = Path(ci_scripts_job_summary.__file__).resolve()
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(path), run_name="__main__")
    assert exc_info.value.code == 0
