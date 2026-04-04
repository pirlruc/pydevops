#!/usr/bin/env python3
"""Build GitHub Actions job summary Markdown from logs in _ci_summary/ (devops-ci scripts job)."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _read(name: str) -> str:
    """Return UTF-8 text for ``_ci_summary/<name>``, or empty string if missing."""
    p = Path("_ci_summary") / name
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def _pytest_tests_line(text: str) -> str:
    """Extract the last pytest line that reports ``N passed``."""
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if re.search(r"\d+\s+passed", line):
            return line
    return "—"


def _pytest_coverage_pct(text: str) -> str:
    """Return ``TOTAL`` line coverage percentage like ``95``, or empty if not found."""
    m = re.search(r"^TOTAL\s+.*\s+(\d+)\s*%", text, re.MULTILINE)
    return m.group(1) if m else ""


def _pylint_rating_value(text: str) -> str:
    """Return pylint ``X.XX`` rating substring, or empty if not found."""
    m = re.search(r"rated at\s+([\d.]+)/10", text, re.IGNORECASE)
    return m.group(1) if m else ""


def _interrogate_actual_pct(text: str) -> str:
    """Return docstring coverage percentage text (e.g. ``100.0%``), or empty."""
    for pat in (
        r"actual:\s*([\d.]+%)",
        r"Passed:\s*([\d.]+%)",
        r"([\d.]+%)\s*interrogate",
        r"INTERROGATE.*?([\d.]+%)",
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def _radon_cc_summary(text: str) -> str:
    """Return the line containing ``Overall max CC``, or ``—``."""
    for line in text.splitlines():
        if "Overall max CC" in line:
            return line.strip()
    return "—"


def _radon_mi_summary(text: str) -> str:
    """Return the line containing ``Minimum MI``, or ``—``."""
    for line in text.splitlines():
        if "Minimum MI" in line:
            return line.strip()
    return "—"


def _row_two_col(tool: str, result: str) -> str:
    """One Markdown table row with pipe escaping in the result cell."""
    esc = result.replace("|", "\\|")
    return f"| {tool} | {esc} |"


def _result_pytest(py: str) -> str:
    """Pytest counts plus pass requirement (same style as Radon threshold lines)."""
    line = _pytest_tests_line(py)
    tail = " (all tests in `tests/` must pass)"
    return line + tail if line != "—" else "—" + tail


def _result_coverage(py: str) -> str:
    """Coverage value plus ≥95% threshold."""
    pct = _pytest_coverage_pct(py)
    core = f"**{pct}%** line coverage (pytest-cov TOTAL)" if pct else "—"
    return f"{core} (≥95% required)"


def _result_pylint(pl: str) -> str:
    """Pylint rating plus fail-under threshold."""
    v = _pylint_rating_value(pl)
    core = f"**{v}**/10" if v else "—"
    return f"{core} (≥9.5/10 required)"


def _result_interrogate(iq: str) -> str:
    """Interrogate percentage plus ≥95% threshold."""
    p = _interrogate_actual_pct(iq)
    core = f"**{p}** docstring coverage" if p else "—"
    return f"{core} (≥95% required on `scripts/`)"


def _log_tail_fence(text: str, max_lines: int) -> str:
    """Last ``max_lines`` of log text, or ``(empty)``."""
    stripped = text.strip()
    if not stripped:
        return "(empty)"
    lines = stripped.splitlines()
    return "\n".join(lines[-max_lines:])


def _raw_details_sections(py: str, pl: str, iq: str, cc: str, mi: str) -> list[str]:
    """Markdown ``<details>`` blocks with fenced raw log tails."""
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
    """Full job-summary Markdown for the ci-scripts job."""
    py = _read("pytest.txt")
    pl = _read("pylint.txt")
    iq = _read("interrogate.txt")
    cc = _read("radon_cc.txt")
    mi = _read("radon_mi.txt")

    body: list[str] = [
        "## Scripts quality (CI)",
        "",
        "| Tool | Result |",
        "| --- | --- |",
        _row_two_col("**pytest**", _result_pytest(py)),
        _row_two_col("**Coverage** (`pytest-cov`)", _result_coverage(py)),
        _row_two_col("**pylint** (`scripts/`)", _result_pylint(pl)),
        _row_two_col("**interrogate** (`scripts/`)", _result_interrogate(iq)),
        _row_two_col("**Radon CC**", _radon_cc_summary(cc)),
        _row_two_col("**Radon MI**", _radon_mi_summary(mi)),
        "",
        *_raw_details_sections(py, pl, iq, cc, mi),
    ]
    return "\n".join(body)


def main() -> int:
    """Print summary Markdown to stdout."""
    print(build_summary(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
