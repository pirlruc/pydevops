#!/usr/bin/env python3
"""Thin entrypoint/proxy for scorecard summary helpers."""

from __future__ import annotations

import sys
from pathlib import Path

# Support direct execution: `python3 scripts/scorecard_summary.py ...`.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.scorecard_summary_core import (
    _rule_name,
    main,
    render_markdown,
    sarif_to_payload,
)

__all__ = ["_rule_name", "main", "render_markdown", "sarif_to_payload"]


if __name__ == '__main__':
    raise SystemExit(main())
