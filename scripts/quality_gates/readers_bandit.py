"""Parse Bandit JSON artifact."""

from __future__ import annotations

from pathlib import Path

from scripts.quality_gates.jsonutil import read_json


def bandit_finding_count(root: Path) -> int | None:
    """Return the number of Bandit ``results`` entries, or ``None`` if the report is unusable."""
    data = read_json(root / 'bandit.json')
    if data is None or not isinstance(data, dict):
        return None

    raw = data.get('results')
    if not isinstance(raw, list):
        return None

    return len(raw)
