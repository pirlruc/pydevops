#!/usr/bin/env python3
"""Build GitHub Actions job summary Markdown from logs in _ci_summary/ (devops-ci scripts job)."""

from __future__ import annotations

import re
from pathlib import Path


def _read(name: str) -> str:
    """Return UTF-8 text for ``_ci_summary/<name>``, or empty string if missing."""
    p = Path('_ci_summary') / name
    if not p.is_file():
        return ''

    return p.read_text(encoding='utf-8', errors='replace')


def _pytest_int_after(line: str, pattern: str) -> int:
    """First capturing group from ``pattern`` on ``line``, parsed as int, else ``0``."""
    m = re.search(pattern, line)
    return int(m.group(1)) if m else 0


def _passed_failed_from_summary_line(line: str) -> tuple[int, int] | None:
    """Parse one pytest summary line into ``(passed, failed)``; ``failed`` includes errors."""
    line = line.strip()
    if not re.search(r'\b\d+\s+(passed|failed|error)', line):
        return None

    passed_n = _pytest_int_after(line, r'(\d+)\s+passed')
    failed_n = _pytest_int_after(line, r'(\d+)\s+failed')
    err_n = _pytest_int_after(line, r'(\d+)\s+errors?')
    if passed_n == 0 and failed_n == 0 and err_n == 0:
        return None

    return passed_n, failed_n + err_n


def _pytest_successful_failed(text: str) -> tuple[int, int] | None:
    """From pytest's last summary line, return ``(passed_count, failed_count)``."""
    for line in reversed(text.strip().splitlines()):
        got = _passed_failed_from_summary_line(line)
        if got is not None:
            return got

    return None


def _pytest_counts_phrase(text: str) -> str:
    """``**N** successful, **M** failed`` with no duration (for the summary table)."""
    got = _pytest_successful_failed(text)
    if got is None:
        return '—'

    passed, failed = got
    return f'**{passed}** successful, **{failed}** failed'


def _pytest_coverage_pct(text: str) -> str:
    """Return ``TOTAL`` line coverage percentage like ``95``, or empty if not found."""
    m = re.search(r'^TOTAL\s+.*\s+(\d+)\s*%', text, re.MULTILINE)
    return m.group(1) if m else ''


def _pylint_rating_value(text: str) -> str:
    """Return pylint ``X.XX`` rating substring, or empty if not found."""
    m = re.search(r'rated at\s+([\d.]+)/10', text, re.IGNORECASE)
    return m.group(1) if m else ''


def _interrogate_actual_pct(text: str) -> str:
    """Return docstring coverage percentage text (e.g. ``100.0%``), or empty."""
    for pat in (
        r'actual:\s*([\d.]+%)',
        r'Passed:\s*([\d.]+%)',
        r'([\d.]+%)\s*interrogate',
        r'INTERROGATE.*?([\d.]+%)',
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)

    return ''


def _radon_cc_raw_line(text: str) -> str:
    """Return the line containing ``Overall max CC``, or empty string."""
    for line in text.splitlines():
        if 'Overall max CC' in line:
            return line.strip()

    return ''


def _radon_mi_raw_line(text: str) -> str:
    """Return the line containing ``Minimum MI``, or empty string."""
    for line in text.splitlines():
        if 'Minimum MI' in line:
            return line.strip()

    return ''


def _radon_cc_for_summary(text: str) -> str:
    """Radon CC log line with threshold phrasing ``(≤5.0 required)``."""
    raw = _radon_cc_raw_line(text)
    if not raw:
        return '—'

    out = re.sub(r'\(\s*limit\s*≤\s*5\.0\s*\)', '(≤5.0 required)', raw, flags=re.IGNORECASE)
    return re.sub(r'\blimit\s*≤\s*5\.0\b', '≤5.0 required', out)


def _radon_mi_for_summary(text: str) -> str:
    """Radon MI log line with threshold phrasing ``(≥40.0 required)``."""
    raw = _radon_mi_raw_line(text)
    if not raw:
        return '—'

    out = re.sub(r'\(\s*must\s+be\s*>\s*40\.0\s*\)', '(≥40.0 required)', raw, flags=re.IGNORECASE)
    return re.sub(r'\bmust\s+be\s*>\s*40\.0\b', '≥40.0 required', out)


def _row_two_col(analysis: str, result: str) -> str:
    """One Markdown table row with pipe escaping in the result cell."""
    esc = result.replace('|', '\\|')
    return f'| {analysis} | {esc} |'


def _pip_audit_summary(text: str) -> tuple[int, int, int, int, int, int] | None:
    """Parse ``PIP-AUDIT SUMMARY`` line into counts."""
    m = re.search(
        r'PIP-AUDIT SUMMARY:\s*total=(\d+)\s+low=(\d+)\s+medium=(\d+)\s+high=(\d+)'
        r'\s+critical=(\d+)\s+unknown=(\d+)',
        text,
    )
    if not m:
        return None
    return (
        int(m.group(1)),
        int(m.group(2)),
        int(m.group(3)),
        int(m.group(4)),
        int(m.group(5)),
        int(m.group(6)),
    )


def _result_pip_audit(pa: str) -> str:
    """Pip-audit severity summary and gate policy phrasing."""
    got = _pip_audit_summary(pa)
    if got is None:
        return '— (medium/high/critical must be 0)'

    total, low, medium, high, critical, unknown = got
    return (
        f'**{total}** total: L={low}, M={medium}, H={high}, C={critical}, unknown={unknown} '
        '(M/H/C must be 0)'
    )


def _result_pytest(py: str) -> str:
    """Successful / failed counts only, plus pass requirement."""
    phrase = _pytest_counts_phrase(py)
    tail = ' (all tests in `tests/` must pass)'
    return phrase + tail if phrase != '—' else '—' + tail


def _result_coverage(py: str) -> str:
    """Line coverage percentage and ≥95% threshold."""
    pct = _pytest_coverage_pct(py)
    core = f'**{pct}%** line coverage' if pct else '—'
    return f'{core} (≥95% required)'


def _result_pylint(pl: str) -> str:
    """Pylint rating plus fail-under threshold."""
    v = _pylint_rating_value(pl)
    core = f'**{v}**/10' if v else '—'
    return f'{core} (≥9.5/10 required)'


def _result_interrogate(iq: str) -> str:
    """Interrogate percentage plus ≥95% threshold."""
    p = _interrogate_actual_pct(iq)
    core = f'**{p}** docstring coverage' if p else '—'
    return f'{core} (≥95% required on `scripts/`)'


def _log_tail_fence(text: str, max_lines: int) -> str:
    """Last ``max_lines`` of log text, or ``(empty)``."""
    stripped = text.strip()
    if not stripped:
        return '(empty)'

    lines = stripped.splitlines()
    return '\n'.join(lines[-max_lines:])


def _raw_details_sections(py: str, pl: str, iq: str, cc: str, mi: str, pa: str) -> list[str]:
    """Markdown ``<details>`` blocks with fenced raw log tails."""
    out: list[str] = ['<details><summary>Raw log tails</summary>', '']
    blocks = (
        ('pytest', py, 40),
        ('pylint', pl, 25),
        ('interrogate', iq, 25),
        ('Radon CC', cc, 30),
        ('Radon MI', mi, 30),
        ('pip-audit', pa, 80),
    )
    for title, content, n in blocks:
        out.extend(
            [
                f'### {title}',
                '',
                '```text',
                _log_tail_fence(content, n),
                '```',
                '',
            ],
        )

    out.extend(['</details>', ''])
    return out


def build_summary() -> str:
    """Full job-summary Markdown for the ci-scripts job."""
    py = _read('pytest.txt')
    pl = _read('pylint.txt')
    iq = _read('interrogate.txt')
    cc = _read('radon_cc.txt')
    mi = _read('radon_mi.txt')
    pa = _read('pip_audit.txt')

    body: list[str] = [
        '## Scripts quality (CI)',
        '',
        '| Analysis | Result |',
        '| --- | --- |',
        _row_two_col('**Tests**', _result_pytest(py)),
        _row_two_col('**Code Coverage**', _result_coverage(py)),
        _row_two_col('**Code Quality**', _result_pylint(pl)),
        _row_two_col('**Documentation Coverage**', _result_interrogate(iq)),
        _row_two_col('**Cyclomatic Complexity**', _radon_cc_for_summary(cc)),
        _row_two_col('**Maintainability Index**', _radon_mi_for_summary(mi)),
        _row_two_col('**Dependency Vulnerabilities (pip-audit)**', _result_pip_audit(pa)),
        '',
        *_raw_details_sections(py, pl, iq, cc, mi, pa),
    ]
    return '\n'.join(body)


def main() -> int:
    """Print summary Markdown to stdout."""
    print(build_summary(), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
