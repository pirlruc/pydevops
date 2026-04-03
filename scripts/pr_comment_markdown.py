#!/usr/bin/env python3
"""Emit a single Markdown blob for PR comments from gates.json."""

from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.quality_gates.jsonutil import gates_rows_and_passed


def main() -> int:
    """Print Markdown for a GitHub PR comment; stdout only."""
    out = Path(os.environ.get("QUALITY_OUTPUT_DIR", "quality-output"))
    p = out / "gates.json"
    if not p.is_file():
        print("## Quality pipeline\n\n_No gates output found._")
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        print(
            "## Quality-as-a-Service summary\n\n"
            "_gates.json was missing or not valid JSON (e.g. cancelled job); "
            "see workflow artifacts for partial outputs._",
        )
        return 0
    rows, passed = gates_rows_and_passed(data)
    status = "PASSED" if passed else "FAILED"

    lines = [
        "## Quality-as-a-Service summary",
        "",
        f"**Overall:** {status}",
        "",
        "| Gate | Actual | Required | Status |",
        "| --- | --- | --- | --- |",
    ]
    for r in rows:
        st = "PASS" if r.get("ok") else "FAIL"
        lines.append(
            f"| {r.get('gate', '')} | {r.get('actual', '')} | {r.get('required', '')} | {st} |"
        )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
