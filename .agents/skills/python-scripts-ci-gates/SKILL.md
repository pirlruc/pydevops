---
name: python-scripts-ci-gates
description: 'Pytest, line coverage, and pylint gates when editing Python (scripts/ and tests/). Use when editing files that match: scripts/**/*.py,tests/**/*.py.'
paths: scripts/**/*.py,tests/**/*.py
disable-model-invocation: true
---

<!-- Generated from .cursor/rules by scripts/render-agent-instructions.py. Edit the .mdc files, then re-run that script. -->

Cursor applies the matching `.cursor/rules` file by glob and does not auto-invoke this skill. Other agents should follow this skill when the description matches.

# Python scripts CI gates — pydevops stricter deltas

Org coverage floors: **[`python-quality-gates.mdc`](../../../.cursor/rules/python-quality-gates.mdc)**.

This repo is **stricter** on its own scripts package (no deviation needed):

1. **All tests pass** — **`uv run pytest`** (zero failures).
2. **Line coverage ≥ 95%** on configured packages — do not weaken `--cov-fail-under`.
3. **Pylint ≥ 9.5/10 on `scripts/`** — **`uv run pylint scripts`**
   (`[tool.pylint.main]` `fail-under = 9.5`).

See also **[`interrogate-docstrings.mdc`](../../../.cursor/rules/interrogate-docstrings.mdc)** and
**[`python-quality-gates.mdc`](../../../.cursor/rules/python-quality-gates.mdc)**.
