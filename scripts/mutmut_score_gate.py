#!/usr/bin/env python3
"""Fail CI when Mutmut mutation score (killed / (killed + survived)) is below a floor."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def _score_from_stats(data: dict[str, object]) -> tuple[float, int, int] | None:
    """Return (score_percent, killed, survived) or None if not computable."""
    killed = data.get("killed")
    survived = data.get("survived")
    if not isinstance(killed, int) or not isinstance(survived, int):
        return None
    denom = killed + survived
    if denom <= 0:
        return None
    return 100.0 * killed / denom, killed, survived


def _load_stats_root(path: Path) -> dict[str, Any] | None:
    """Load mutmut CI stats JSON; return dict or None on failure (message to stderr)."""
    if not path.is_file():
        print(f"mutmut score gate: missing stats file {path}", file=sys.stderr)
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"mutmut score gate: invalid JSON in {path}: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print("mutmut score gate: stats root must be a JSON object", file=sys.stderr)
        return None
    return data


def _exit_for_score(score: float, min_score: float) -> int:
    """Return 0 if score meets floor, else 1."""
    if score < min_score:
        print(
            f"mutmut score gate: FAILED (score {score:.2f}% < {min_score})",
            file=sys.stderr,
        )
        return 1
    return 0


def main() -> int:
    """Read mutmut-cicd-stats.json and exit 1 if score < MUTMUT_MIN_SCORE (default 85)."""
    raw_path = os.environ.get("MUTMUT_CICD_STATS", "mutants/mutmut-cicd-stats.json")
    path = Path(raw_path)
    min_score = float(os.environ.get("MUTMUT_MIN_SCORE", "85"))
    root = _load_stats_root(path)
    if root is None:
        return 1
    parsed = _score_from_stats(root)
    if parsed is None:
        print(
            "mutmut score gate: need integer killed/survived with killed+survived > 0",
            file=sys.stderr,
        )
        return 1
    score, killed, survived = parsed
    print(
        f"Mutmut mutation score: {score:.2f}% "
        f"(killed={killed}, survived={survived}, required_min={min_score})"
    )
    return _exit_for_score(score, min_score)


if __name__ == "__main__":
    raise SystemExit(main())
