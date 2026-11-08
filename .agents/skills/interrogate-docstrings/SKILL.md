---
name: interrogate-docstrings
description: 'Interrogate docstring coverage (scripts/) when editing Python under scripts/. Use when editing files that match: scripts/**/*.py.'
paths: scripts/**/*.py
disable-model-invocation: true
---

<!-- Generated from .cursor/rules by scripts/render-agent-instructions.py. Edit the .mdc files, then re-run that script. -->

Cursor applies the matching `.cursor/rules` file by glob and does not auto-invoke this skill. Other agents should follow this skill when the description matches.

# Docstring coverage (interrogate) — pydevops

Org docstring coverage floor: **[`python-quality-gates.mdc`](../../../.cursor/rules/python-quality-gates.mdc)**
(via `docs/guardrails/python/profile.thresholds.yml`).

This repo measures **`scripts/`** only (see `[tool.interrogate]`). When you **add or
edit** **`scripts/**/*.py`**, before finishing:

1. Run **`uv run interrogate scripts -vv --fail-under 95`** (or
   **`uv run --group quality-tools python -m interrogate …`** after **`uv sync`**).
2. Add minimal module/function docstrings until the gate passes.

See also **[`python-scripts-ci-gates.mdc`](../../../.cursor/rules/python-scripts-ci-gates.mdc)** and
**[`python-quality-gates.mdc`](../../../.cursor/rules/python-quality-gates.mdc)**.
