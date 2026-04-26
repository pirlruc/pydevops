"""Formatting helpers for scorecard summary markdown."""

from __future__ import annotations

from collections.abc import Sequence

_SCORE_COL_INDEX = 1


def _is_real_number(v: object) -> bool:
    """True for ``int``/``float`` values only (exclude booleans)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def fmt_score(v: object) -> str:
    """Format a numeric score for Markdown; non-numeric or negative -> placeholder."""
    if not _is_real_number(v):
        return "—"
    if v < 0:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(int(v))


def truncate(s: str, max_len: int) -> str:
    """Single-line table text capped to ``max_len`` with an ellipsis."""
    s = s.replace("\n", " ").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _ascii_hline_widths(widths: tuple[int, ...]) -> str:
    """Return horizontal separator line for ASCII table widths."""
    inner = "+".join("-" * (w + 2) for w in widths)
    return f"+{inner}+"


def _ascii_row_widths(row: tuple[str, ...], widths: tuple[int, ...]) -> str:
    """Format one ASCII table row (score column right-aligned)."""
    parts: list[str] = []
    for i, (cell, w) in enumerate(zip(row, widths, strict=True)):
        parts.append(f"{cell:>{w}}" if i == _SCORE_COL_INDEX else f"{cell:<{w}}")
    return "| " + " | ".join(parts) + " |"


def _ascii_column_widths_multi(
    headers: tuple[str, ...],
    body: Sequence[tuple[str, ...]],
) -> tuple[int, ...]:
    """Compute max width per column using headers and row values."""
    n = len(headers)
    widths = [len(headers[i]) for i in range(n)]
    for r in body:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))
    return tuple(widths)


def _text_fence_open(repo_caption: str | None) -> list[str]:
    """Return opening fenced-block lines, optionally with scope caption."""
    if not repo_caption:
        return ["```text"]
    return ["```text", repo_caption, ""]


def checks_table_block(
    checks: list[dict],
    reason_max: int,
    name_max: int = 44,
    snippet_max: int = 40,
    repo_caption: str | None = None,
) -> list[str]:
    """ASCII bordered table for aligned columns in logs and summaries."""
    headers = ("Check", "Score", "Reason", "Package / ref")
    body: list[tuple[str, str, str, str]] = []
    for c in checks:
        raw_snip = c.get("snippet", "")
        snip = truncate(str(raw_snip), snippet_max) if raw_snip else "—"
        body.append(
            (
                truncate(str(c.get("name", "?")), name_max),
                fmt_score(c.get("score")),
                truncate(str(c.get("reason", "")), reason_max),
                snip,
            ),
        )
    widths = _ascii_column_widths_multi(headers, body)
    sep = _ascii_hline_widths(widths)
    out = _text_fence_open(repo_caption)
    out.extend([sep, _ascii_row_widths(headers, widths), sep])
    out.extend(_ascii_row_widths(r, widths) for r in body)
    out.extend([sep, "```"])
    return out
