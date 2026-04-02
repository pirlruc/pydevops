"""Parse radon cyclomatic complexity and maintainability index JSON."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.jsonutil import parse_float_or_none, read_json


def max_cc_in_block_list(blocks: Any) -> float:
    """Largest ``complexity`` value in a radon cc block list."""
    if not isinstance(blocks, list):
        return 0.0
    best = 0.0
    for b in blocks:
        if isinstance(b, dict) and "complexity" in b:
            best = max(best, float(b["complexity"]))
    return best


def radon_cc_max(root: Path) -> float | None:
    """Maximum cyclomatic complexity from radon cc -j output."""
    data = read_json(root / "radon_cc.json")
    if not data or not isinstance(data, dict):
        return None
    max_cc = max((max_cc_in_block_list(blocks) for blocks in data.values()), default=0.0)
    return max_cc if max_cc else None


def mi_value_from_entry(v: Any) -> float | None:
    """Parse a single radon mi file entry to a float MI, or None."""
    if isinstance(v, dict) and "mi" in v:
        return float(v["mi"])
    if isinstance(v, (int, float)):
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
    data = read_json(root / "radon_mi.json")
    if not data or not isinstance(data, dict):
        return None
    values = collect_mi_values(data)
    return min(values) if values else None
