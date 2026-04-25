"""Parse radon cyclomatic complexity and maintainability index JSON."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.jsonutil import parse_float_or_none, read_json


def _as_complexity(v: Any) -> float | None:
    """Return a block complexity value as float, or ``None`` when absent."""
    if not isinstance(v, dict):
        return None

    raw = v.get('complexity')
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)

    if isinstance(raw, str):
        return parse_float_or_none(raw)

    return None


def max_cc_in_block_list(blocks: Any) -> tuple[float, bool]:
    """Largest ``complexity`` in a radon cc block list, and whether any block had it."""
    if not isinstance(blocks, list):
        return 0.0, False

    present = [value for block in blocks if (value := _as_complexity(block)) is not None]
    if not present:
        return 0.0, False

    return max(present), True


def _file_cc_maxima(data: dict[str, Any]) -> list[float]:
    """Collect per-file max CC values from Radon's JSON output."""
    out: list[float] = []
    for blocks in data.values():
        local_max, found = max_cc_in_block_list(blocks)
        if found:
            out.append(local_max)

    return out


def radon_cc_max(root: Path) -> float | None:
    """Maximum cyclomatic complexity from radon cc -j output."""
    data = read_json(root / 'radon_cc.json')
    if not data or not isinstance(data, dict):
        return None

    maxima = _file_cc_maxima(data)
    return max(maxima) if maxima else None


def _mi_from_dict_entry(v: dict) -> float | None:
    """``mi`` field from a Radon MI object node."""
    if 'mi' not in v:
        return None

    return parse_float_or_none(str(v['mi']))


def mi_value_from_entry(v: Any) -> float | None:
    """Parse a single radon mi file entry to a float MI, or None."""
    if isinstance(v, dict):
        return _mi_from_dict_entry(v)

    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)

    if isinstance(v, str):
        return parse_float_or_none(v)

    return None


def collect_mi_values(data: dict[str, Any]) -> list[float]:
    """Gather numeric MI values from a radon mi -j mapping."""
    out: list[float] = []
    for v in data.values():
        m = mi_value_from_entry(v)
        if m is not None:
            out.append(m)

    return out


def radon_mi_min(root: Path) -> float | None:
    """Minimum maintainability index across files from radon mi -j."""
    data = read_json(root / 'radon_mi.json')
    if not data or not isinstance(data, dict):
        return None

    values = collect_mi_values(data)
    return min(values) if values else None
