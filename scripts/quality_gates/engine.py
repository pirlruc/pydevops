"""CLI entrypoint for quality gates."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from scripts.quality_gates.config import normalized_strictness_level
from scripts.quality_gates.evaluation import evaluate


def main() -> int:
    """CLI entrypoint: read ``QUALITY_OUTPUT_DIR`` and ``STRICTNESS_LEVEL``."""
    root = Path(os.environ.get("QUALITY_OUTPUT_DIR", "quality-output")).resolve()
    raw = os.environ.get("STRICTNESS_LEVEL", "Medium")
    strictness = normalized_strictness_level(raw)
    passed, rows = evaluate(root, strictness)

    print("=== Quality gate summary ===")
    for r in rows:
        status = "PASS" if r["ok"] else "FAIL"
        print(f"  [{status}] {r['gate']}: {r['actual']} (required: {r['required']})")

    if not passed:
        print("\nQuality gates FAILED.", file=sys.stderr)
        return 1
    print("\nAll evaluated quality gates passed.")
    return 0
