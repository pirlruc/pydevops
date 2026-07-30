"""Tests for Radon metric helpers outside the gated package."""

from __future__ import annotations

from scripts.radon_metrics import (
    as_complexity,
    cc_avg,
    cc_max,
    collect_mi_values,
    max_cc_in_block_list,
    mi_avg,
    mi_min,
    mi_value_from_entry,
)


def test_as_complexity_variants() -> None:
    """Complexity accepts int/float/str and rejects other shapes."""
    assert as_complexity({'complexity': 3}) == 3.0
    assert as_complexity({'complexity': '4.5'}) == 4.5
    assert as_complexity({'complexity': 'x'}) is None
    assert as_complexity('nope') is None
    assert as_complexity({'complexity': True}) is None


def test_max_cc_in_block_list() -> None:
    """Block-list max reports presence and largest complexity."""
    assert max_cc_in_block_list('bad') == (0.0, False)
    assert max_cc_in_block_list([]) == (0.0, False)
    assert max_cc_in_block_list([{'complexity': 2}, {'complexity': 5}]) == (5.0, True)


def test_cc_max_and_avg() -> None:
    """CC aggregations across files."""
    data = {
        'a.py': [{'complexity': 2}, {'complexity': 4}],
        'b.py': 'skip',
        'c.py': [{'complexity': 6}],
    }
    assert cc_max(data) == 6.0
    assert cc_avg(data) == 4.0
    assert cc_max({'x.py': []}) is None
    assert cc_avg({'x.py': []}) is None


def test_mi_parsing_and_aggregates() -> None:
    """MI entry shapes and min/avg reductions."""
    assert mi_value_from_entry({'mi': 42.5}) == 42.5
    assert mi_value_from_entry(50) == 50.0
    assert mi_value_from_entry('33.0') == 33.0
    assert mi_value_from_entry({'rank': 'A'}) is None
    assert mi_value_from_entry(None) is None
    data = {'a.py': {'mi': 40}, 'b.py': {'mi': 60}, 'c.py': 'bad'}
    assert collect_mi_values(data) == [40.0, 60.0]
    assert mi_min(data) == 40.0
    assert mi_avg(data) == 50.0
    assert mi_min({}) is None
    assert mi_avg({}) is None
