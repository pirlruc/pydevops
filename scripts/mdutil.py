"""Shared helpers for Markdown-safe text in reports and PR comments."""

from __future__ import annotations

import re

# U+00A6 BROKEN BAR — visually distinct from ASCII | so pipe-delimited tables stay aligned.
_PIPE_SUB = "\u00a6"


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
