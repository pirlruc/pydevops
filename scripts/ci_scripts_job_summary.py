#!/usr/bin/env python3
"""Build GitHub Actions job summary Markdown from logs in _ci_summary/ (devops-ci scripts job)."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _read(name: str) -> str:
    p = Path("_ci_summary") / name
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def _pytest_tests_line(text: str) -> str:
    """Extract last line that reports passed/failed counts."""
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if re.search(r"\d+\s+passed", line):
            return line
    return "—"


def _pytest_coverage_line(text: str) -> str:
    m = re.search(r"^TOTAL\s+.*\s+(\d+)\s*%", text, re.MULTILINE)
    if m:
        return f"Line coverage (TOTAL): **{m.group(1)}%**"
    return "—"


def _pylint_rating(text: str) -> str:
    m = re.search(r"rated at\s+([\d.]+)/10", text, re.IGNORECASE)
    if m:
        return f"**{m.group(1)}**/10"
    return "—"


def _interrogate_pct(text: str) -> str:
    for pat in (
        r"actual:\s*([\d.]+%)",
        r"Passed:\s*([\d.]+%)",
        r"([\d.]+%)\s*interrogate",
        r"INTERROGATE.*?([\d.]+%)",
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return f"**{m.group(1)}**"
    return "—"


def _radon_cc_summary(text: str) -> str:
    for line in text.splitlines():
        if "Overall max CC" in line:
            return line.strip()
    return "—"


def _radon_mi_summary(text: str) -> str:
    for line in text.splitlines():
        if "Minimum MI" in line:
            return line.strip()
    return "—"


def _row(tool: str, result: str, threshold: str) -> str:
    esc = result.replace("|", "\\|")
    return f"| {tool} | {esc} | {threshold} |"


def _log_tail_fence(text: str, max_lines: int) -> str:
    stripped = text.strip()
    if not stripped:
        return "(empty)"
    lines = stripped.splitlines()
    return "\n".join(lines[-max_lines:])


def _raw_details_sections(py: str, pl: str, iq: str, cc: str, mi: str) -> list[str]:
    out: list[str] = ["<details><summary>Raw log tails</summary>", ""]
    blocks = (
        ("pytest", py, 40),
        ("pylint", pl, 25),
        ("interrogate", iq, 25),
        ("Radon CC", cc, 30),
        ("Radon MI", mi, 30),
    )
    for title, content, n in blocks:
        out.extend(
            [
                f"### {title}",
                "",
                "```text",
                _log_tail_fence(content, n),
                "```",
                "",
            ]
        )
    out.extend(["</details>", ""])
    return out


def build_summary() -> str:
    py = _read("pytest.txt")
    pl = _read("pylint.txt")
    iq = _read("interrogate.txt")
    cc = _read("radon_cc.txt")
    mi = _read("radon_mi.txt")

    body: list[str] = [
        "## Scripts quality (CI)",
        "",
        "| Tool | Result | Threshold / scope |",
        "| --- | --- | --- |",
        _row(
            "**pytest**",
            _pytest_tests_line(py),
            "all tests in `tests/` must pass",
        ),
        _row(
            "**Coverage** (`pytest-cov`)",
            _pytest_coverage_line(py),
            "≥ **95%** line (`pyproject` `--cov-fail-under`)",
        ),
        _row(
            "**pylint** (`scripts/`)",
            _pylint_rating(pl),
            "≥ **9.5**/10 (`pyproject` `fail-under`)",
        ),
        _row(
            "**interrogate** (`scripts/`)",
            _interrogate_pct(iq),
            "≥ **95%** docstring coverage",
        ),
        _row(
            "**Radon CC**",
            _radon_cc_summary(cc),
            "max cyclomatic ≤ **5** (`scripts/quality_gates/*.py`)",
        ),
        _row(
            "**Radon MI**",
            _radon_mi_summary(mi),
            "MI > **40** for all gate modules",
        ),
        "",
        *_raw_details_sections(py, pl, iq, cc, mi),
    ]
    return "\n".join(body)


def main() -> int:
    print(build_summary(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
