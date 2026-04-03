"""Tests for ``scripts.consolidate_artifacts``."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts.consolidate_artifacts import main as consolidate_main


def test_consolidate_writes_report_and_zip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """consolidate_artifacts creates quality_report.md and quality_bundle.zip."""
    out = tmp_path / "qo"
    out.mkdir()
    (out / "gates.json").write_text(
        json.dumps({"passed": True, "failures": [], "rows": []}),
        encoding="utf-8",
    )
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(out))
    assert consolidate_main() == 0
    assert (out / "quality_report.md").is_file()
    assert (out / "quality_bundle.zip").is_file()
    with zipfile.ZipFile(out / "quality_bundle.zip") as zf:
        names = zf.namelist()
        assert any("quality_report.md" in n for n in names)


def test_consolidate_empty_gates_table(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing gates.json still writes report with empty table."""
    out = tmp_path / "q2"
    out.mkdir()
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(out))
    assert consolidate_main() == 0
    text = (out / "quality_report.md").read_text(encoding="utf-8")
    assert "PASSED" in text or "FAILED" in text


def test_consolidate_with_gate_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-empty gate rows exercise Markdown table loop."""
    out = tmp_path / "q4"
    out.mkdir()
    rows = [{"gate": "G", "actual": "1", "required": "0", "ok": True}]
    (out / "gates.json").write_text(
        json.dumps({"passed": True, "failures": [], "rows": rows}),
        encoding="utf-8",
    )
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(out))
    assert consolidate_main() == 0
    assert "| G |" in (out / "quality_report.md").read_text(encoding="utf-8")


def test_consolidate_missing_passed_defaults_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing ``passed`` in gates payload is rendered as FAILED."""
    out = tmp_path / "q6"
    out.mkdir()
    (out / "gates.json").write_text(
        json.dumps({"rows": [{"gate": "G", "actual": "1", "required": "1", "ok": True}]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(out))
    assert consolidate_main() == 0
    text = (out / "quality_report.md").read_text(encoding="utf-8")
    assert "FAILED" in text


def test_consolidate_gates_json_array_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid JSON array is not a gates object — report shows failed overall, empty safe rows."""
    out = tmp_path / "q5"
    out.mkdir()
    (out / "gates.json").write_text("[]", encoding="utf-8")
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(out))
    assert consolidate_main() == 0
    text = (out / "quality_report.md").read_text(encoding="utf-8")
    assert "FAILED" in text


def test_consolidate_summary_snippet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """summary_*.txt files appear in report body."""
    out = tmp_path / "q3"
    out.mkdir()
    (out / "gates.json").write_text('{"passed": true, "rows": []}', encoding="utf-8")
    (out / "summary_tool.txt").write_text("hello log", encoding="utf-8")
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(out))
    assert consolidate_main() == 0
    assert "hello log" in (out / "quality_report.md").read_text(encoding="utf-8")
