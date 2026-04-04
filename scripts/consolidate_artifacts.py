#!/usr/bin/env python3
"""Build quality_report.md and zip all quality-output artifacts."""

from __future__ import annotations

import json
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from scripts.mdutil import markdown_fenced_code_block, sanitize_markdown_table_cell
from scripts.quality_gates.jsonutil import gates_rows_and_passed


def _md_table(rows: list[dict]) -> str:
    """Render gate rows as a Markdown table."""
    if not rows:
        return "_No gate rows._\n"
    headers = ["Gate", "Actual", "Required", "Status"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for r in rows:
        status = "PASS" if r.get("ok") else "FAIL"
        lines.append(
            "| "
            + " | ".join(
                [
                    sanitize_markdown_table_cell(r.get("gate", "")),
                    sanitize_markdown_table_cell(r.get("actual", "")),
                    sanitize_markdown_table_cell(r.get("required", "")),
                    status,
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _tool_console_summary(out: Path) -> str:
    """Append short sections from per-tool log snippets if present."""
    blocks: list[str] = []
    for name in sorted(out.glob("summary_*.txt")):
        title = name.stem.replace("summary_", "")
        body = name.read_text(encoding="utf-8", errors="replace").strip()
        blocks.append(f"### {title}\n\n{markdown_fenced_code_block(body)}")
    return "\n".join(blocks) if blocks else ""


def main() -> int:
    """Write ``quality_report.md`` and ``quality_bundle.zip`` under ``QUALITY_OUTPUT_DIR``."""
    out = Path(os.environ.get("QUALITY_OUTPUT_DIR", "quality-output")).resolve()
    out.mkdir(parents=True, exist_ok=True)

    gates_path = out / "gates.json"
    rows: list[dict] = []
    passed = True
    gates_parse_note = ""
    if gates_path.is_file():
        try:
            data = json.loads(gates_path.read_text(encoding="utf-8", errors="replace"))
            rows, passed = gates_rows_and_passed(data)
        except json.JSONDecodeError:
            rows = []
            passed = False
            gates_parse_note = (
                "_`gates.json` was not valid JSON (e.g. partial write); "
                "marking overall result as failed for this report._\n\n"
            )

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    md = f"""# Consolidated quality report

Generated: {now}
Overall: **{'PASSED' if passed else 'FAILED'}**

## Gate summary

{gates_parse_note}{_md_table(rows)}

## Per-tool console excerpts

{_tool_console_summary(out)}
"""
    report_path = out / "quality_report.md"
    report_path.write_text(md, encoding="utf-8")

    zip_path = out / "quality_bundle.zip"
    if zip_path.is_file():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(out.rglob("*")):
            if f.is_file() and f.name != "quality_bundle.zip":
                arc = f.relative_to(out)
                zf.write(f, arcname=str(arc))

    print(f"Wrote {report_path} and {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
