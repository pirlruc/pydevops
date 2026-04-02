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


def test_pylint_gate_fails_low_score(tmp_out: Path) -> None:
    """Pylint below threshold fails."""
    (tmp_out / "pylint_score.txt").write_text("rated at 5.0/10", encoding="utf-8")
    passed, _rows = qg.evaluate(tmp_out, "Medium")
    assert not passed


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


def test_vulnerabilities_fail_medium(tmp_out: Path) -> None:
    """Too many medium vulnerabilities fails Medium tier."""
    vulns = [{"id": f"m{i}", "severity": "medium", "description": ""} for i in range(15)]
    (tmp_out / "pip_audit.json").write_text(json.dumps([{"vulns": vulns}]), encoding="utf-8")
    passed, _ = qg.evaluate(tmp_out, "Medium")
    assert not passed


def test_main_cli_exit_code(tmp_out: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main() respects STRICTNESS_LEVEL and QUALITY_OUTPUT_DIR."""
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(tmp_out))
    monkeypatch.setenv("STRICTNESS_LEVEL", "Low")
    assert qg.main() == 0
