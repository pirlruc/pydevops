"""Tests for ``scripts.quality_gates.jsonutil``."""

from __future__ import annotations

from scripts.quality_gates.jsonutil import coerce_non_negative_float


def test_coerce_non_negative_float() -> None:
    """JSON-like values map to non-negative floats; garbage → 0."""
    assert coerce_non_negative_float(None) == 0.0
    assert coerce_non_negative_float(True) == 0.0
    assert coerce_non_negative_float(False) == 0.0
    assert coerce_non_negative_float(42) == 42.0
    assert coerce_non_negative_float(3.5) == 3.5
    assert coerce_non_negative_float("12") == 12.0
    assert coerce_non_negative_float(" 3.25 ") == 3.25
    assert coerce_non_negative_float(-1) == 0.0
    assert coerce_non_negative_float("-2") == 0.0
    assert coerce_non_negative_float("x") == 0.0
    assert coerce_non_negative_float([]) == 0.0
    assert coerce_non_negative_float({}) == 0.0
