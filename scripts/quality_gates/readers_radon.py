"""Parse radon cyclomatic complexity and maintainability index JSON."""

from __future__ import annotations

from pathlib import Path

from scripts.quality_gates.jsonutil import read_json
from scripts.radon_metrics import cc_avg, cc_max, mi_avg, mi_min


def radon_cc_max(root: Path) -> float | None:
    """Maximum cyclomatic complexity from radon cc -j output."""
    data = read_json(root / 'radon_cc.json')
    if not data or not isinstance(data, dict):
        return None
    return cc_max(data)


def radon_cc_avg(root: Path) -> float | None:
    """Average cyclomatic complexity across all blocks from radon cc -j."""
    data = read_json(root / 'radon_cc.json')
    if not data or not isinstance(data, dict):
        return None
    return cc_avg(data)


def radon_mi_min(root: Path) -> float | None:
    """Minimum maintainability index across files from radon mi -j."""
    data = read_json(root / 'radon_mi.json')
    if not data or not isinstance(data, dict):
        return None
    return mi_min(data)


def radon_mi_avg(root: Path) -> float | None:
    """Average maintainability index across files from radon mi -j."""
    data = read_json(root / 'radon_mi.json')
    if not data or not isinstance(data, dict):
        return None
    return mi_avg(data)
