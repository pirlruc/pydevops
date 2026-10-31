"""Parse pip-audit JSON output."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.jsonutil import read_json


def pip_tuple_row_vulns(row: list[Any] | tuple[Any, ...]) -> list[Any]:
    """Vulnerabilities from a ``[name, version, vulns]`` pip-audit row."""
    if len(row) < 3:
        return []

    inner = row[2]
    return list(inner) if isinstance(inner, (list, tuple)) else []


def pip_dict_row_vulns(row: dict[str, Any]) -> list[Any]:
    """Vulnerabilities from a dict-shaped pip-audit row."""
    raw = row.get('vulns')
    if raw is None:
        raw = row.get('vulnerabilities')

    if isinstance(raw, (list, tuple)):
        return list(raw)

    return []


def pip_row_vulnerabilities(row: Any) -> list[Any]:
    """Extract vulnerability list from one pip-audit JSON row (tuple or dict shape)."""
    if isinstance(row, (list, tuple)):
        return pip_tuple_row_vulns(row)

    if isinstance(row, dict):
        return pip_dict_row_vulns(row)

    return []


def bump_pip_severity(v: dict, highs: int, mediums: int) -> tuple[int, int]:
    """Increment high/medium counts for one pip-audit vulnerability object."""
    id_ = str(v.get('id', ''))
    desc = str(v.get('description', '')).lower()
    sev = str(v.get('severity', '')).lower()
    if sev in ('high', 'critical') or 'critical' in desc:
        return highs + 1, mediums

    if sev == 'medium':
        return highs, mediums + 1

    if id_:
        return highs, mediums + 1

    return highs, mediums


def accumulate_pip_vulns(vulns: Any, highs: int, mediums: int) -> tuple[int, int]:
    """Apply pip-audit vulnerability objects to running high/medium counts."""
    if not isinstance(vulns, list):
        return highs, mediums

    for item in vulns:
        if not isinstance(item, dict):
            continue

        highs, mediums = bump_pip_severity(item, highs, mediums)

    return highs, mediums


def pip_audit_rows(data: Any) -> list[Any] | None:
    """Rows from a pip-audit JSON array or a ``{"dependencies": [...]}`` object.

    pip-audit 2.10 writes the object form. Earlier releases wrote a bare array.
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        dependencies = data.get('dependencies')
        if isinstance(dependencies, list):
            return dependencies

    return None


def pip_audit_vulns(root: Path) -> tuple[int, int] | None:
    """Approximate high/medium counts from pip-audit JSON.

    Returns ``None`` when ``pip_audit.json`` is missing, invalid JSON, or neither
    a list nor an object with a ``dependencies`` list.
    """
    rows = pip_audit_rows(read_json(root / 'pip_audit.json'))
    if rows is None:
        return None
    highs = mediums = 0
    for row in rows:
        vulns = pip_row_vulnerabilities(row)
        highs, mediums = accumulate_pip_vulns(vulns, highs, mediums)

    return highs, mediums
