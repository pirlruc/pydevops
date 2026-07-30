"""Tests for complexity / maintainability gate row builders."""

from __future__ import annotations

from scripts.complexity_gate_rules import avg_cc_gate, avg_mi_gate, max_cc_gate, min_mi_gate


def test_max_cc_gate_high_missing() -> None:
    """High fails closed when CC is missing; Medium skips."""
    rows, fails = max_cc_gate(None, 8.0, 'High')
    assert rows[0]['ok'] is False
    assert fails == ['cyclomatic complexity']
    assert max_cc_gate(None, 8.0, 'Medium') == ([], [])


def test_max_cc_gate_pass_fail() -> None:
    """Max CC compares against the limit."""
    rows, fails = max_cc_gate(5.0, 8.0, 'High')
    assert rows[0]['ok'] is True
    assert fails == []
    rows, fails = max_cc_gate(9.0, 8.0, 'High')
    assert rows[0]['ok'] is False
    assert fails


def test_avg_cc_and_mi_gates() -> None:
    """Average and min MI gates cover pass, fail, and High-missing."""
    rows, fails = avg_cc_gate(4.0, 5.0, 'High')
    assert rows[0]['ok'] is True
    assert fails == []
    rows, fails = avg_cc_gate(None, 5.0, 'High')
    assert rows[0]['ok'] is False
    assert fails == ['cyclomatic complexity avg']
    assert avg_cc_gate(None, 5.0, 'Medium') == ([], [])
    rows, fails = avg_cc_gate(6.0, 5.0, 'High')
    assert rows[0]['ok'] is False

    rows, fails = min_mi_gate(45.0, 40.0, 'High')
    assert rows[0]['ok'] is True
    rows, fails = min_mi_gate(30.0, 40.0, 'High')
    assert rows[0]['ok'] is False
    rows, fails = min_mi_gate(None, 40.0, 'Medium')
    assert rows == []

    rows, fails = avg_mi_gate(55.0, 60.0, 'High')
    assert rows[0]['ok'] is False
    assert fails == ['maintainability index avg']
    rows, fails = avg_mi_gate(None, 60.0, 'High')
    assert fails == ['maintainability index avg']
    assert avg_mi_gate(None, 60.0, 'Medium') == ([], [])
    rows, fails = avg_mi_gate(65.0, 60.0, 'High')
    assert rows[0]['ok'] is True
