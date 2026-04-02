"""Parse Ruff and jscpd JSON outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.jsonutil import read_json


def ruff_messages_in_files(files: list[Any]) -> int:
    """Sum message counts across Ruff file objects."""
    return sum(len(f.get("messages", [])) for f in files if isinstance(f, dict))


def ruff_issue_count_from_obj(data: dict[str, Any]) -> int:
    """Count issues when ruff JSON is an object with ``files``."""
    raw = data.get("files")
    if isinstance(raw, list):
        return ruff_messages_in_files(raw)
    return 0


def ruff_issue_count(root: Path) -> int:
    """Count Ruff diagnostics from ruff.json (list or object with files[].messages)."""
    data = read_json(root / "ruff.json")
    if not data:
        return 0
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        return ruff_issue_count_from_obj(data)
    return 0


def jscpd_duplication_pct(root: Path) -> float | None:
    """Total duplication percentage from jscpd JSON report."""
    data = read_json(root / "jscpd-report.json")
    if not data:
        return None
    total = (data.get("statistics") or {}).get("total") or {}
    pct = total.get("percentage")
    return float(pct) if pct is not None else None
