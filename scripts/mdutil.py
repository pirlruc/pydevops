"""Shared helpers for Markdown-safe text in reports and PR comments."""

from __future__ import annotations

import re

# U+00A6 BROKEN BAR — visually distinct from ASCII | so pipe-delimited tables stay aligned.
_PIPE_SUB = "\u00a6"


def _max_consecutive_backticks(s: str) -> int:
    """Length of the longest run of `` ` `` characters in ``s``."""
    best = cur = 0
    for ch in s:
        if ch == "`":
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def markdown_fenced_code_block(body: str) -> str:
    """Wrap ``body`` in a GFM fenced code block.

    The fence is at least three backticks and strictly longer than any run of backticks inside
    ``body``, so arbitrary tool output (including Markdown examples) cannot break the fence.
    """
    n = max(3, _max_consecutive_backticks(body) + 1)
    fence = "`" * n
    return f"{fence}\n{body}\n{fence}\n"


def sanitize_markdown_table_cell(value: object, max_len: int = 500) -> str:
    """Normalize a value for use inside a GFM pipe table cell.

    Replaces newlines and tabs with spaces, swaps ``|`` for a broken bar so columns cannot
    break, collapses repeated whitespace, and truncates overly long text.
    """
    s = str(value)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\n", " ").replace("\t", " ")
    s = s.replace("|", _PIPE_SUB)
    s = re.sub(r" {2,}", " ", s).strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"
