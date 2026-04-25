#!/usr/bin/env python3
"""Scorecard JSON or SARIF → short Markdown for CI logs and GitHub job summaries."""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TypeGuard

# OpenSSF Scorecard writes SARIF messages as: messageWithScore in pkg/scorecard/sarif.go
# ``match()`` is anchored at the start of ``text`` only; MULTILINE would not change behavior here.
_SCORE_PREFIX = re.compile(r'^score is (-?\d+):\s*')


def _is_real_number(v: object) -> TypeGuard[int | float]:
    """True for ``int``/``float`` values only (JSON booleans are ``bool``, a subclass of ``int``)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _non_negative_score_value(v: object) -> float | None:
    """Scorecard 0–10 style value if ``v`` is numeric and ``>= 0``; else ``None``."""
    if not _is_real_number(v):
        return None

    x = float(v)
    return x if x >= 0 else None


def _aggregate_overall_score(data: dict) -> float | None:
    """Score from ``aggregateScore.overall.score`` when present and non-negative."""
    agg = data.get('aggregateScore')
    if not isinstance(agg, dict):
        return None

    overall = agg.get('overall')
    if not isinstance(overall, dict):
        return None

    return _non_negative_score_value(overall.get('score'))


def _checks(data: dict) -> list[dict]:
    """Return normalized check dicts from Scorecard JSON."""
    raw = data.get('checks')
    if not isinstance(raw, list):
        return []

    return [c for c in raw if isinstance(c, dict)]


def _overall_score(data: dict, checks: list[dict]) -> float | None:
    """Aggregate 0–10: mean of checks with score ≥ 0, else top-level or aggregate totals.

    Preferring the check mean aligns the headline with the table and :func:`_needs_action`.
    """
    scores = [x for c in checks if (x := _non_negative_score_value(c.get('score'))) is not None]
    if scores:
        return sum(scores) / len(scores)

    top = _non_negative_score_value(data.get('score'))
    if top is not None:
        return top

    return _aggregate_overall_score(data)


def _fmt_score(v: object) -> str:
    """Format a numeric score for Markdown; non-numeric or negative → placeholder."""
    if not _is_real_number(v):
        return '—'

    if v < 0:
        return 'n/a'

    if isinstance(v, float):
        return f'{v:.1f}'

    return str(int(v))


def _truncate(s: str, max_len: int) -> str:
    """Single-line table text (name, reason, etc.) capped to ``max_len`` with an ellipsis."""
    s = s.replace('\n', ' ').strip()
    if len(s) <= max_len:
        return s

    return s[: max_len - 1] + '…'


_SCORE_COL_INDEX = 1


def _ascii_hline_widths(widths: tuple[int, ...]) -> str:
    """Horizontal rule for a variable-width ASCII table."""
    inner = '+'.join('-' * (w + 2) for w in widths)
    return f'+{inner}+'


def _ascii_row_widths(row: tuple[str, ...], widths: tuple[int, ...]) -> str:
    """One table row; score column (index 1) is right-aligned."""
    parts: list[str] = []
    for i, (cell, w) in enumerate(zip(row, widths, strict=True)):
        if i == _SCORE_COL_INDEX:
            parts.append(f'{cell:>{w}}')
        else:
            parts.append(f'{cell:<{w}}')

    return '| ' + ' | '.join(parts) + ' |'


def _ascii_column_widths_multi(
    headers: tuple[str, ...],
    body: Sequence[tuple[str, ...]],
) -> tuple[int, ...]:
    """Per-column max width from headers and body."""
    n = len(headers)
    widths = [len(headers[i]) for i in range(n)]
    for r in body:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    return tuple(widths)


def _text_fence_open(repo_caption: str | None) -> list[str]:
    """First lines inside the fenced ``text`` block (optional caption for Scorecard scope)."""
    if not repo_caption:
        return ['```text']

    return ['```text', repo_caption, '']


def _snippet_text_from_physical_location(pl: dict[str, Any]) -> str:
    """Return stripped ``region.snippet.text`` when present on a SARIF physical location."""
    region = pl.get('region')
    if not isinstance(region, dict):
        return ''

    sn = region.get('snippet')
    if not isinstance(sn, dict):
        return ''

    t = sn.get('text')
    return t.strip() if isinstance(t, str) and t.strip() else ''


def _snippet_from_one_location(loc: object) -> str:
    """Snippet text from one SARIF ``location`` object, or empty."""
    if not isinstance(loc, dict):
        return ''

    pl = loc.get('physicalLocation')
    if not isinstance(pl, dict):
        return ''

    return _snippet_text_from_physical_location(pl)


def _first_snippet_among_locations(locs: list[Any]) -> str:
    """Walk SARIF ``locations``; return first non-empty snippet text."""
    for loc in locs:
        got = _snippet_from_one_location(loc)
        if got:
            return got

    return ''


def _snippet_from_sarif_result(res: dict[str, Any]) -> str:
    """First non-empty ``locations[].physicalLocation`` snippet text (action ref, path, etc.)."""
    locs = res.get('locations')
    if not isinstance(locs, list):
        return ''

    return _first_snippet_among_locations(locs)


def _checks_table_block(
    checks: list[dict],
    reason_max: int,
    name_max: int = 44,
    snippet_max: int = 40,
    repo_caption: str | None = None,
) -> list[str]:
    """ASCII +/| bordered table for aligned columns in logs and summaries."""
    headers = ('Check', 'Score', 'Reason', 'Package / ref')
    body: list[tuple[str, str, str, str]] = []
    for c in checks:
        raw_snip = c.get('snippet', '')
        snip = _truncate(str(raw_snip), snippet_max) if raw_snip else '—'
        body.append(
            (
                _truncate(str(c.get('name', '?')), name_max),
                _fmt_score(c.get('score')),
                _truncate(str(c.get('reason', '')), reason_max),
                snip,
            ),
        )

    widths = _ascii_column_widths_multi(headers, body)
    sep = _ascii_hline_widths(widths)
    out = _text_fence_open(repo_caption)
    out.extend([sep, _ascii_row_widths(headers, widths), sep])
    out.extend(_ascii_row_widths(r, widths) for r in body)
    out.extend([sep, '```'])
    return out


def _needs_action(checks: list[dict], overall: float | None, threshold: float = 6.0) -> bool:
    """True if aggregate or any check is below the review threshold."""
    if overall is not None and overall < threshold:
        return True

    for c in checks:
        sc = _non_negative_score_value(c.get('score'))
        if sc is not None and sc < threshold:
            return True

    return False


def _rule_name(rule: dict[str, Any]) -> str:
    """Human-readable check name from a SARIF rule object."""
    name = rule.get('name')
    if isinstance(name, str) and name.strip():
        return name.strip()

    sd = rule.get('shortDescription')
    if isinstance(sd, dict):
        t = sd.get('text')
        if isinstance(t, str) and t.strip():
            return t.strip()

    rid = rule.get('id')
    return str(rid) if rid else '?'


def _sarif_result_to_check(
    res: dict[str, Any],
    rule_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Map one SARIF result to a check dict."""
    rid = str(res.get('ruleId', ''))
    msg_obj = res.get('message')
    text = msg_obj.get('text', '') if isinstance(msg_obj, dict) else ''
    if not isinstance(text, str):
        text = str(text)

    score = -1
    reason = text.strip()
    m = _SCORE_PREFIX.match(text)
    if m:
        score = int(m.group(1))
        reason = text[m.end() :].strip()

    for cut in ('\nClick Remediation', '\nClick remediation'):
        if cut in reason:
            reason = reason.split(cut, 1)[0].strip()

    rule = rule_by_id.get(rid, {})
    name = _rule_name(rule) if rule else rid or '?'
    return {
        'name': name,
        'score': score,
        'reason': reason,
        'snippet': _snippet_from_sarif_result(res),
    }


def _repo_uri_from_sarif_run(run: dict[str, Any]) -> str | None:
    """Best-effort repository URI Scorecard embeds in SARIF (analyzed project, not the action ref)."""
    vcp = run.get('versionControlProvenance')
    if isinstance(vcp, list):
        for item in vcp:
            if not isinstance(item, dict):
                continue

            for key in ('repositoryUri', 'repositoryURL', 'uri', 'url', 'repositoryUrl'):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()

    props = run.get('properties')
    if isinstance(props, dict):
        for key in ('repositoryUri', 'repository', 'repo', 'repositoryURL'):
            val = props.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()

    inv = run.get('invocations')
    if isinstance(inv, list):
        for item in inv:
            if not isinstance(item, dict):
                continue

            wc = item.get('workingDirectory')
            if isinstance(wc, dict):
                uri = wc.get('uri')
                if isinstance(uri, str) and uri.strip():
                    return uri.strip()

    return None


def _sarif_driver(run: dict[str, Any]) -> dict[str, Any]:
    """Return the SARIF tool.driver object or raise a controlled error."""
    tool = run.get('tool')
    if tool is None:
        return {}

    if not isinstance(tool, dict):
        raise ValueError('Invalid SARIF run: tool must be an object')

    driver = tool.get('driver')
    if driver is None:
        return {}

    if not isinstance(driver, dict):
        raise ValueError('Invalid SARIF run: tool.driver must be an object')

    return driver


def sarif_to_payload(sarif: dict[str, Any], repo_display: str | None) -> dict[str, Any]:
    """Build a Scorecard-like dict (repo + checks) from Scorecard SARIF 2.1.0 output."""
    runs = sarif.get('runs')
    if not isinstance(runs, list) or not runs:
        raise ValueError('SARIF has no runs')

    run0 = runs[0]
    if not isinstance(run0, dict):
        raise ValueError('Invalid SARIF run')

    driver = _sarif_driver(run0)
    rules_raw = driver.get('rules')
    rules_list: list[dict[str, Any]] = rules_raw if isinstance(rules_raw, list) else []
    rule_by_id = {str(r['id']): r for r in rules_list if isinstance(r, dict) and r.get('id')}

    results_raw = run0.get('results')
    results: list[dict[str, Any]] = results_raw if isinstance(results_raw, list) else []

    checks: list[dict[str, Any]] = []
    for res in results:
        if not isinstance(res, dict):
            continue

        checks.append(_sarif_result_to_check(res, rule_by_id))

    checks.sort(key=lambda c: str(c.get('name', '')))
    sarif_repo = _repo_uri_from_sarif_run(run0)
    chosen = (sarif_repo or (repo_display or '').strip() or '').strip() or None
    if chosen:
        src = 'sarif' if sarif_repo else 'cli'
        repo: str | dict[str, str] = {'name': chosen, 'source': src}
    else:
        repo = '—'

    return {'repo': repo, 'checks': checks}


def render_markdown(data: dict, reason_max: int = 100) -> str:
    """Build a Markdown table and verdict from parsed Scorecard JSON or SARIF-derived payload."""
    checks = _checks(data)
    checks.sort(key=lambda c: str(c.get('name', '')))
    overall = _overall_score(data, checks)
    repo = data.get('repo')
    repo_name = '—'
    source = ''
    if isinstance(repo, dict):
        repo_name = str(repo.get('name', '—'))
        source = str(repo.get('source', 'cli'))
    elif isinstance(repo, str):
        repo_name = repo

    sarif_note = ''
    if source == 'sarif':
        sarif_note = (
            ' _(URI from Scorecard SARIF metadata — the **GitHub repository** analyzed; '
            'not a dependency package or the `ossf/scorecard-action` line in your workflow)_'
        )

    lines: list[str] = [
        '## OpenSSF Scorecard summary',
        '',
        f'- **Repository analyzed:** `{repo_name}`{sarif_note}',
        f'- **Aggregate score (0–10, higher is better):** {_fmt_score(overall)}',
        '',
        '### Checks',
        '',
    ]
    table_caption: str | None = None
    if repo_name != '—':
        table_caption = f'Scope: GitHub repository `{repo_name}` (OpenSSF Scorecard target)'

    lines.extend(_checks_table_block(checks, reason_max, repo_caption=table_caption))
    lines.append('')

    action = _needs_action(checks, overall)
    if action:
        verdict = (
            '**Action needed:** review checks with score below 6 or aggregate below 6, '
            'and address Scorecard documentation for those rules.'
        )
    else:
        verdict = (
            '**No immediate action required:** aggregate and per-check scores are at or above the '
            'review threshold (6/10). Re-run periodically as the repo changes.'
        )

    lines.extend(['', '### Verdict', '', verdict, ''])
    return '\n'.join(lines)


def _parse_input(path: Path, repo_display: str | None) -> dict[str, Any]:
    """Load a file as Scorecard JSON or SARIF and return a dict for :func:`render_markdown`."""
    raw_txt = path.read_text(encoding='utf-8')
    data = json.loads(raw_txt)
    if not isinstance(data, dict):
        raise ValueError('Root JSON value must be an object')

    suffix = path.suffix.lower()
    if suffix == '.sarif' or (data.get('version') == '2.1.0' and 'runs' in data):
        return sarif_to_payload(data, repo_display)

    if 'checks' in data or _checks(data):
        out = dict(data)
        if repo_display and not (isinstance(out.get('repo'), dict) and out['repo'].get('name')):
            out['repo'] = {'name': repo_display, 'source': 'cli'}
        elif isinstance(out.get('repo'), dict):
            merged = dict(out['repo'])
            merged.setdefault('source', 'cli')
            out['repo'] = merged

        return out

    raise ValueError('Unrecognized format: expected Scorecard JSON or SARIF 2.1.0')


def main() -> int:
    """CLI: [--repo github.com/owner/repo] <results.json|results.sarif> → Markdown on stdout."""
    argv = sys.argv[1:]
    repo_display: str | None = None
    if len(argv) >= 2 and argv[0] == '--repo':
        repo_display = argv[1]
        argv = argv[2:]

    if len(argv) != 1:
        msg = (
            'usage: scorecard_summary.py [--repo github.com/owner/name] '
            '<results.json|results.sarif>'
        )
        print(msg, file=sys.stderr)
        return 2

    path = Path(argv[0])
    if not path.is_file():
        print(f'Missing input file: {path}', file=sys.stderr)
        return 1

    if repo_display is None:
        repo_display = (os.environ.get('GITHUB_REPOSITORY') or '').strip()
        if repo_display:
            repo_display = f'github.com/{repo_display}'

    try:
        payload = _parse_input(path, repo_display)
    except (json.JSONDecodeError, ValueError) as e:
        print(f'Invalid input: {e}', file=sys.stderr)
        return 1

    print(render_markdown(payload))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
