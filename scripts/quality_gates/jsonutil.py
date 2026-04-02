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
