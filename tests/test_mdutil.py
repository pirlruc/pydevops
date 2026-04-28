"""Tests for ``scripts.mdutil``."""

from __future__ import annotations

from scripts.mdutil import markdown_fenced_code_block, sanitize_markdown_table_cell


def test_sanitize_replaces_pipe_with_broken_bar() -> None:
    """ASCII ``|`` must not create extra table columns."""
    assert '\u00a6' in sanitize_markdown_table_cell('a|b')
    assert '|' not in sanitize_markdown_table_cell('a|b')


def test_sanitize_flattens_newlines() -> None:
    """Newlines become spaces so a row stays one line."""
    assert '\n' not in sanitize_markdown_table_cell('x\ny')
    assert sanitize_markdown_table_cell('x\ny') == 'x y'


def test_markdown_fenced_code_uses_longer_fence_when_body_has_backticks() -> None:
    """Fence length exceeds embedded ``` so Markdown stays well-formed."""
    body = 'line\n```\ninner\n```\n'
    out = markdown_fenced_code_block(body)
    assert out.startswith('````\n')
    assert out.endswith('````\n')
    assert out.count('````') == 2


def test_sanitize_truncates_long_text() -> None:
    """Very long cells get an ellipsis."""
    s = sanitize_markdown_table_cell('x' * 600, max_len=20)
    assert len(s) == 20
    assert s.endswith('…')
