---
name: kotlin-quality-gates
description: 'Prove KT-* quality gates still hold before finishing Kotlin edits. Use when editing files that match: **/*.{kt,kts}.'
paths: '**/*.{kt,kts}'
disable-model-invocation: true
---

<!-- Generated from .cursor/rules by scripts/render-agent-instructions.py. Edit the .mdc files, then re-run that script. -->

Cursor applies the matching `.cursor/rules` file by glob and does not auto-invoke this skill. Other agents should follow this skill when the description matches.

# Kotlin quality gates

When you add or edit Kotlin, prove the org Kotlin guardrails still hold before finishing.
Read floors from `docs/guardrails/kotlin/profile.thresholds.yml`. Do not bake numbers here.

Run the repo local parity script when it exists. Otherwise run the Gradle tasks the
caller template names: lint, unit tests, and Kover. A `@Suppress` in a build script
is a suppression and needs the same record as a source suppression.

Policy and deviations: [guardrails-compliance.mdc](../../../.cursor/rules/guardrails-compliance.mdc).
Tool choice: [build-test-environments.mdc](../../../.cursor/rules/build-test-environments.mdc).
