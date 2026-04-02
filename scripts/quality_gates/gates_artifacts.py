"""High-tier required artifact presence checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.quality_gates.config import HIGH_REQUIRED_FILES

RowList = list[dict[str, Any]]


def high_artifact_gate_row(root: Path, name: str) -> tuple[RowList, bool]:
    """One artifact presence row and whether it is OK."""
    path = root / name
    ok = path.is_file() and path.stat().st_size > 0
    row = {
        "gate": f"Required artifact ({name})",
        "actual": "present" if ok else "missing or empty",
        "required": "must exist for High",
        "ok": ok,
    }
    return [row], ok


def enforce_high_artifact_presence(
    root: Path,
    strictness: str,
) -> tuple[RowList, list[str]]:
    """Fail High runs if required tool outputs are missing (avoids silent skips)."""
    if strictness != "High":
        return [], []
    rows: RowList = []
    failures: list[str] = []
    for name in HIGH_REQUIRED_FILES:
        row_list, ok = high_artifact_gate_row(root, name)
        rows.extend(row_list)
        if not ok:
            failures.append(f"missing artifact: {name}")
    return rows, failures
