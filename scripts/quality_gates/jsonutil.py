"""Small JSON helpers for reading CI artifact files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    """Load JSON from path or return None if missing or invalid."""
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None


def parse_float_or_none(s: str) -> float | None:
    """Parse string to float or None on failure."""
    try:
        return float(s)
    except ValueError:
        return None


def coerce_non_negative_float(v: Any, *, default: float = 0.0) -> float:
    """Parse JSON-derived values for size/count metrics (cloc, etc.).

    ``None``, booleans, containers, and non-numeric strings yield ``default``.
    Negative numbers yield ``default`` so malformed artifacts do not crash gate evaluation.
    """
    if v is None:
        return default
    if isinstance(v, bool):
        return default
    if isinstance(v, (int, float)):
        x = float(v)
        return x if x >= 0 else default
    if isinstance(v, str):
        p = parse_float_or_none(v.strip())
        if p is None or p < 0:
            return default
        return p
    return default


def gates_rows_and_passed(data: Any) -> tuple[list[dict[str, Any]], bool]:
    """Normalize ``gates.json`` payload: list of row dicts and overall pass flag."""
    if not isinstance(data, dict):
        return [], False
    raw_rows = data.get("rows", [])
    if isinstance(raw_rows, list):
        rows = [r for r in raw_rows if isinstance(r, dict)]
        # Fail closed when legacy/malformed payloads omit "passed".
        passed = data.get("passed") is True
    else:
        rows = []
        passed = False
    return rows, passed
