"""Tests for ``scripts.quality_gates``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import quality_gates as qg


@pytest.fixture
def tmp_out(tmp_path: Path) -> Path:
    """Fresh output directory with minimal Low-tier artifacts."""
    d = tmp_path / "out"
    d.mkdir()
    (d / "coverage.json").write_text(
        json.dumps({"totals": {"percent_covered": 100.0, "percent_branches_covered": 100.0}}),
        encoding="utf-8",
    )
    (d / "pylint.json").write_text("[]", encoding="utf-8")
    (d / "pylint_score.txt").write_text("Your code has been rated at 10.00/10", encoding="utf-8")
    (d / "radon_cc.json").write_text(
        json.dumps({"mod.py": [{"type": "function", "complexity": 2}]}),
        encoding="utf-8",
    )
    (d / "radon_mi.json").write_text(json.dumps({"mod.py": {"mi": 80.0, "rank": "A"}}), encoding="utf-8")
    (d / "jscpd-report.json").write_text(
        json.dumps({"statistics": {"total": {"percentage": 0.0}}}),
        encoding="utf-8",
    )
    (d / "cloc.json").write_text(
        json.dumps({"Python": {"code": 100, "comment": 10}}),
        encoding="utf-8",
    )
    (d / "interrogate.txt").write_text("TOTAL COVERAGE: 100%\n", encoding="utf-8")
    (d / "pydoclint.txt").write_text("", encoding="utf-8")
    (d / "ruff.json").write_text("[]", encoding="utf-8")
    (d / "pip_audit.json").write_text("[]", encoding="utf-8")
    (d / "grype.json").write_text(json.dumps({"matches": []}), encoding="utf-8")
    (d / "gitleaks.json").write_text("[]", encoding="utf-8")
    (d / "bandit.json").write_text(json.dumps({"results": []}), encoding="utf-8")
    (d / "pytest_exit_code.txt").write_text("0\n", encoding="utf-8")
    return d


def test_evaluate_low_passes(tmp_out: Path) -> None:
    """Low strictness passes with generous thresholds."""
    passed, rows = qg.evaluate(tmp_out, "Low")
    assert passed
    assert any(r["gate"] == "Pylint score" for r in rows)


def test_high_fails_missing_artifact(tmp_out: Path) -> None:
    """High strictness fails when a required artifact is missing."""
    (tmp_out / "bandit.json").unlink()
    passed, rows = qg.evaluate(tmp_out, "High")
    assert not passed
    assert any("bandit.json" in r.get("gate", "") for r in rows)


def test_high_passes_with_full_artifacts(tmp_out: Path) -> None:
    """High strictness passes when artifacts meet stricter numeric gates."""
    (tmp_out / "bandit.json").write_text(json.dumps({"results": []}), encoding="utf-8")
    passed, _rows = qg.evaluate(tmp_out, "High")
    assert passed


def test_bandit_findings_fail_high(tmp_out: Path) -> None:
    """High tier allows zero Bandit findings; any result fails."""
    (tmp_out / "bandit.json").write_text(
        json.dumps({"results": [{"test_id": "B101"}]}),
        encoding="utf-8",
    )
    passed, rows = qg.evaluate(tmp_out, "High")
    assert not passed
    assert any(r.get("gate") == "Bandit (SAST)" for r in rows)


def test_bandit_findings_within_medium_cap_passes(tmp_out: Path) -> None:
    """Medium tier allows up to three Bandit findings."""
    (tmp_out / "bandit.json").write_text(
        json.dumps({"results": [{"i": 1}, {"i": 2}, {"i": 3}]}),
        encoding="utf-8",
    )
    passed, _ = qg.evaluate(tmp_out, "Medium")
    assert passed


def test_bandit_findings_exceed_medium_cap_fails(tmp_out: Path) -> None:
    """More than three Bandit findings fails Medium."""
    (tmp_out / "bandit.json").write_text(
        json.dumps({"results": [{"i": i} for i in range(4)]}),
        encoding="utf-8",
    )
    passed, _ = qg.evaluate(tmp_out, "Medium")
    assert not passed


def test_high_fails_missing_pytest_exit(tmp_out: Path) -> None:
    """High tier requires pytest_exit_code.txt from the test phase."""
    (tmp_out / "bandit.json").write_text(json.dumps({"results": []}), encoding="utf-8")
    (tmp_out / "pytest_exit_code.txt").unlink()
    passed, rows = qg.evaluate(tmp_out, "High")
    assert not passed
    assert any(r.get("gate") == "Pytest exit code" for r in rows)


def test_high_strictness_normalized_from_lowercase(tmp_out: Path) -> None:
    """STRICTNESS_LEVEL casing must not bypass High rules."""
    (tmp_out / "bandit.json").write_text(json.dumps({"results": []}), encoding="utf-8")
    assert qg.evaluate(tmp_out, "high")[0]
    assert qg.normalized_strictness_level("HIGH") == "High"


def test_pylint_gate_fails_low_score(tmp_out: Path) -> None:
    """Pylint below threshold fails."""
    (tmp_out / "pylint_score.txt").write_text("rated at 5.0/10", encoding="utf-8")
    passed, _rows = qg.evaluate(tmp_out, "Medium")
    assert not passed


def test_pytest_nonzero_exit_fails(tmp_out: Path) -> None:
    """Recorded pytest exit code non-zero fails the gate."""
    (tmp_out / "pytest_exit_code.txt").write_text("1\n", encoding="utf-8")
    passed, rows = qg.evaluate(tmp_out, "Low")
    assert not passed
    assert any(r.get("gate") == "Pytest exit code" for r in rows)


def test_grype_non_object_json_fails(tmp_out: Path) -> None:
    """Grype JSON root must be an object so counts are trustworthy."""
    (tmp_out / "grype.json").write_text("[]", encoding="utf-8")
    passed, rows = qg.evaluate(tmp_out, "Medium")
    assert not passed
    assert any("Grype report" in str(r.get("gate", "")) for r in rows)


def test_pip_audit_missing_fails(tmp_out: Path) -> None:
    """Missing pip_audit.json should fail via report-shape row, not pass as zero vulns."""
    (tmp_out / "pip_audit.json").unlink()
    passed, rows = qg.evaluate(tmp_out, "Medium")
    assert not passed
    assert any("pip-audit report" in str(r.get("gate", "")) for r in rows)


def test_cyclomatic_high_limit(tmp_out: Path) -> None:
    """High tier rejects complexity >= 6 (max allowed 5)."""
    (tmp_out / "radon_cc.json").write_text(
        json.dumps({"x.py": [{"type": "function", "complexity": 6}]}),
        encoding="utf-8",
    )
    passed, _rows = qg.evaluate(tmp_out, "High")
    assert not passed


def test_maintainability_high_limit(tmp_out: Path) -> None:
    """High tier requires minimum MI >= 60."""
    (tmp_out / "radon_mi.json").write_text(json.dumps({"x.py": {"mi": 45.0, "rank": "A"}}), encoding="utf-8")
    passed, _rows = qg.evaluate(tmp_out, "High")
    assert not passed


def test_license_gate_dedupes_multiple_patterns_per_package(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """One SBOM package matching several deny substrings yields one hit line, not several."""
    from scripts import license_gate

    sbom = tmp_path / "sbom.json"
    sbom.write_text(
        json.dumps({"packages": [{"name": "badlib", "licenseConcluded": "GPL-3.0-only"}]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("SPDX_SBOM_PATH", str(sbom))
    monkeypatch.setenv("LICENSE_DENY_LIST", json.dumps(["gpl", "gpl-3.0"]))
    assert license_gate.main() == 1
    err = capsys.readouterr().err
    assert err.count("badlib") == 1
    assert "gpl" in err and "gpl-3.0" in err


def test_license_gate_invalid_sbom_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Malformed SPDX JSON yields a distinct exit code."""
    from scripts import license_gate

    sbom = tmp_path / "sbom.json"
    sbom.write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv("SPDX_SBOM_PATH", str(sbom))
    monkeypatch.setenv("LICENSE_DENY_LIST", "[]")
    assert license_gate.main() == 3


def test_license_gate_hits(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """license_gate returns 1 when a denied license matches."""
    from scripts import license_gate

    sbom = tmp_path / "sbom.json"
    sbom.write_text(
        json.dumps(
            {
                "packages": [
                    {"name": "bad", "licenseConcluded": "GPL-3.0-only"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SPDX_SBOM_PATH", str(sbom))
    monkeypatch.setenv("LICENSE_DENY_LIST", '["gpl-3.0"]')
    assert license_gate.main() == 1


def test_vulnerabilities_fail_high(tmp_out: Path) -> None:
    """High-severity vulns fail when above tier limit."""
    (tmp_out / "pip_audit.json").write_text(
        json.dumps([{"vulns": [{"id": "h1", "severity": "HIGH", "description": ""}]}]),
        encoding="utf-8",
    )
    passed, _ = qg.evaluate(tmp_out, "Medium")
    assert not passed


def test_vulnerabilities_sum_pip_audit_and_grype(tmp_out: Path) -> None:
    """pip-audit and Grype highs are summed (not max) for a conservative gate."""
    (tmp_out / "pip_audit.json").write_text(
        json.dumps([{"vulns": [{"id": "h1", "severity": "HIGH", "description": ""}]}]),
        encoding="utf-8",
    )
    (tmp_out / "grype.json").write_text(
        json.dumps({"matches": [{"vulnerability": {"severity": "High"}}]}),
        encoding="utf-8",
    )
    passed, rows = qg.evaluate(tmp_out, "Medium")
    assert not passed
    high_row = next(r for r in rows if r.get("gate") == "Vulnerabilities (High)")
    assert high_row["actual"] == "2"


def test_vulnerabilities_fail_medium(tmp_out: Path) -> None:
    """Too many medium vulnerabilities fails Medium tier."""
    vulns = [{"id": f"m{i}", "severity": "medium", "description": ""} for i in range(15)]
    (tmp_out / "pip_audit.json").write_text(json.dumps([{"vulns": vulns}]), encoding="utf-8")
    passed, _ = qg.evaluate(tmp_out, "Medium")
    assert not passed


def test_high_fails_when_cloc_missing_python_section(tmp_out: Path) -> None:
    """High-tier substance check rejects empty cloc.json."""
    (tmp_out / "cloc.json").write_text("{}", encoding="utf-8")
    (tmp_out / "bandit.json").write_text(json.dumps({"results": []}), encoding="utf-8")
    passed, rows = qg.evaluate(tmp_out, "High")
    assert not passed
    assert any("cloc.json" in str(r.get("gate", "")) for r in rows)


def test_pr_comment_malformed_gates_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """PR comment script tolerates invalid gates.json."""
    from scripts import pr_comment_markdown

    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / "gates.json").write_text("{", encoding="utf-8")
    assert pr_comment_markdown.main() == 0
    assert "could not be parsed as JSON" in capsys.readouterr().out


def test_consolidate_malformed_gates_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Consolidation tolerates invalid gates.json and still writes the report."""
    from scripts import consolidate_artifacts

    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / "gates.json").write_text("{", encoding="utf-8")
    assert consolidate_artifacts.main() == 0
    body = (tmp_path / "quality_report.md").read_text(encoding="utf-8")
    assert "not valid JSON" in body
    assert "FAILED" in body


def test_main_cli_exit_code(tmp_out: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main() respects STRICTNESS_LEVEL and QUALITY_OUTPUT_DIR."""
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(tmp_out))
    monkeypatch.setenv("STRICTNESS_LEVEL", "Low")
    assert qg.main() == 0


def test_duplication_gate_fails_when_jscpd_report_missing(tmp_out: Path) -> None:
    """Missing or unreadable jscpd-report.json must not skip the duplication gate."""
    (tmp_out / "jscpd-report.json").unlink()
    passed, rows = qg.evaluate(tmp_out, "Low")
    assert not passed
    assert any(r.get("gate") == "Duplication (jscpd)" and r.get("ok") is False for r in rows)
