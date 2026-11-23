---
name: node-quality-gates
description: 'Prove NODE-* quality gates still hold before finishing Node edits. Use when editing files that match: **/package.json.'
paths: '**/package.json'
disable-model-invocation: true
---

<!-- Generated from .cursor/rules by scripts/render-agent-instructions.py. Edit the .mdc files, then re-run that script. -->

Cursor applies the matching `.cursor/rules` file by glob and does not auto-invoke this skill. Other agents should follow this skill when the description matches.

# Node quality gates

When you add or edit Node, prove the org Node guardrails still hold before finishing.
Read floors from `docs/guardrails/node/profile.thresholds.yml`. Do not bake numbers here.

Run the repo local parity script when it exists. Otherwise run the lint, typecheck,
and test commands the Node caller template names. Do not render unsanitized HTML.
Do not put a secret in the client bundle.

Policy and deviations: [guardrails-compliance.mdc](../../../.cursor/rules/guardrails-compliance.mdc).
Tool choice: [build-test-environments.mdc](../../../.cursor/rules/build-test-environments.mdc).
