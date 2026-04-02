"""Tests for ``scripts.pr_comment_markdown``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.pr_comment_markdown import main as pr_main


def test_pr_comment_empty_gates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Without gates.json, emit placeholder Markdown."""
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(tmp_path))
    # capsys not imported - use monkeypatch on print? main uses print
    import io
    import sys

    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    assert pr_main() == 0
    assert "gates output" in buf.getvalue().lower() or "quality" in buf.getvalue().lower()


def test_pr_comment_with_gates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With gates.json, table includes gate rows."""
    (tmp_path / "gates.json").write_text(
        json.dumps(
            {
                "passed": True,
                "rows": [{"gate": "Test", "actual": "1", "required": "0", "ok": True}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(tmp_path))
    import io
    import sys

    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    assert pr_main() == 0
    out = buf.getvalue()
    assert "Test" in out
    assert "PASS" in out


def test_pr_comment_failed_overall(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """FAILED shown when passed is false."""
    (tmp_path / "gates.json").write_text(
        json.dumps({"passed": False, "rows": []}),
        encoding="utf-8",
    )
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(tmp_path))
    import io
    import sys

    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    assert pr_main() == 0
    assert "FAILED" in buf.getvalue()
