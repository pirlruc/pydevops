"""Tests for ``scripts.quality_gates.jsonutil``."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.quality_gates.jsonutil import coerce_non_negative_float, read_json


def test_read_json_oserror_returns_none(tmp_path: Path) -> None:
    """I/O failures must not propagate (fail closed like invalid JSON)."""
    p = tmp_path / 'x.json'
    p.write_text('{}', encoding='utf-8')
    with patch.object(Path, 'read_text', side_effect=OSError('permission denied')):
        assert read_json(p) is None


def test_read_json_unicode_error_returns_none(tmp_path: Path) -> None:
    """Unicode decode failures from read must not propagate."""
    p = tmp_path / 'x.json'
    p.write_text('{}', encoding='utf-8')
    with patch.object(
        Path,
        'read_text',
        side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'reason'),
    ):
        assert read_json(p) is None


def test_coerce_non_negative_float() -> None:
    """JSON-like values map to non-negative floats; garbage → 0."""
    assert coerce_non_negative_float(None) == 0.0
    assert coerce_non_negative_float(True) == 0.0
    assert coerce_non_negative_float(False) == 0.0
    assert coerce_non_negative_float(42) == 42.0
    assert coerce_non_negative_float(3.5) == 3.5
    assert coerce_non_negative_float('12') == 12.0
    assert coerce_non_negative_float(' 3.25 ') == 3.25
    assert coerce_non_negative_float(-1) == 0.0
    assert coerce_non_negative_float('-2') == 0.0
    assert coerce_non_negative_float('x') == 0.0
    assert coerce_non_negative_float([]) == 0.0
    assert coerce_non_negative_float({}) == 0.0
