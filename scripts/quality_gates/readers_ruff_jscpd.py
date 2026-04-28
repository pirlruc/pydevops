"""Parse Ruff and jscpd JSON outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.jsonutil import parse_float_or_none, read_json


def _dict_get(d: Any, key: str) -> Any | None:
    """Safely read ``key`` from a mapping-like JSON node."""
    if not isinstance(d, dict):
        return None

    return d.get(key)


def ruff_messages_in_files(files: list[Any]) -> int:
    """Sum message counts across Ruff file objects."""
    n = 0
    for f in files:
        if not isinstance(f, dict):
            continue

        msgs = f.get('messages')
        if isinstance(msgs, list):
            n += len(msgs)

    return n


def ruff_issue_count_from_obj(data: dict[str, Any]) -> int:
    """Count issues when ruff JSON is an object with ``files``."""
    raw = data.get('files')
    if isinstance(raw, list):
        return ruff_messages_in_files(raw)

    return 0


def ruff_issue_count(root: Path) -> int:
    """Count Ruff diagnostics from ruff.json (list or object with files[].messages)."""
    data = read_json(root / 'ruff.json')
    if data is None:
        return 0

    if isinstance(data, list):
        return len(data)

    if isinstance(data, dict):
        return ruff_issue_count_from_obj(data)

    return 0


def jscpd_duplication_pct(root: Path) -> float | None:
    """Total duplication percentage from jscpd JSON report."""
    data = read_json(root / 'jscpd-report.json')
    pct = _dict_get(_dict_get(_dict_get(data, 'statistics'), 'total'), 'percentage')
    if isinstance(pct, (int, float)) and not isinstance(pct, bool):
        return float(pct)

    if isinstance(pct, str):
        return parse_float_or_none(pct)

    return None
