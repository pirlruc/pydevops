#!/usr/bin/env python3
"""Thin entrypoint/proxy for scorecard summary helpers."""

from __future__ import annotations

from scripts.scorecard_summary_core import (
    _rule_name,
    main,
    render_markdown,
    sarif_to_payload,
)

__all__ = ["_rule_name", "main", "render_markdown", "sarif_to_payload"]


if __name__ == '__main__':
    raise SystemExit(main())
