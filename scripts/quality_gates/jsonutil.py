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


def gates_rows_and_passed(data: Any) -> tuple[list[dict[str, Any]], bool]:
    """Normalize ``gates.json`` payload: list of row dicts and overall pass flag."""
    if not isinstance(data, dict):
        return [], False
    raw_rows = data.get("rows", [])
    if isinstance(raw_rows, list):
        rows = [r for r in raw_rows if isinstance(r, dict)]
        # Fail closed when legacy/malformed payloads omit "passed".
        passed = bool(data.get("passed", False))
    else:
        rows = []
        passed = False
    return rows, passed
