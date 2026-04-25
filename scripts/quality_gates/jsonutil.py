"""Small JSON helpers for reading CI artifact files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    """Load JSON from path or return None if missing, unreadable, or not valid JSON."""
    if not path.is_file():
        return None

    try:
        return json.loads(path.read_text(encoding='utf-8', errors='replace'))
    except (json.JSONDecodeError, OSError, UnicodeError):
        return None


def parse_float_or_none(s: str) -> float | None:
    """Parse string to float or None on failure."""
    try:
        return float(s)
    except ValueError:
        return None


def _non_negative_float_from_str(s: str) -> float | None:
    """Parse a non-negative float from a string, or ``None``."""
    p = parse_float_or_none(s.strip())
    if p is None or p < 0:
        return None

    return p


def _non_negative_float_from_number(v: int | float) -> float | None:
    """Coerce int/float (caller excludes ``bool``) to a non-negative float or ``None``."""
    x = float(v)
    return x if x >= 0 else None


def _as_non_negative_float(v: Any) -> float | None:
    """Return a non-negative float, or ``None`` if ``v`` is unusable."""
    if v is None or isinstance(v, bool):
        return None

    if isinstance(v, (int, float)):
        return _non_negative_float_from_number(v)

    if isinstance(v, str):
        return _non_negative_float_from_str(v)

    return None


def coerce_non_negative_float(v: Any, *, default: float = 0.0) -> float:
    """Parse JSON-derived values for size/count metrics (cloc, etc.).

    ``None``, booleans, containers, and non-numeric strings yield ``default``.
    Negative numbers yield ``default`` so malformed artifacts do not crash gate evaluation.
    """
    r = _as_non_negative_float(v)
    return r if r is not None else default


def gates_rows_and_passed(data: Any) -> tuple[list[dict[str, Any]], bool]:
    """Normalize ``gates.json`` payload: list of row dicts and overall pass flag."""
    if not isinstance(data, dict):
        return [], False

    raw_rows = data.get('rows', [])
    if isinstance(raw_rows, list):
        rows = [r for r in raw_rows if isinstance(r, dict)]
        # Fail closed when legacy/malformed payloads omit "passed".
        passed = data.get('passed') is True
    else:
        rows = []
        passed = False

    return rows, passed
