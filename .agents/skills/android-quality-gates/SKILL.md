---
name: android-quality-gates
description: 'Prove ANDROID-* quality gates still hold before finishing Android edits. Use when editing files that match: **/AndroidManifest.xml.'
paths: '**/AndroidManifest.xml'
disable-model-invocation: true
---

<!-- Generated from .cursor/rules by scripts/render-agent-instructions.py. Edit the .mdc files, then re-run that script. -->

Cursor applies the matching `.cursor/rules` file by glob and does not auto-invoke this skill. Other agents should follow this skill when the description matches.

# Android quality gates

When you add or edit an Android module, prove the org Android guardrails still hold
before finishing. A module that also contains Kotlin or JNI still applies the kotlin
and cpp packs. Read floors from `docs/guardrails/android/profile.thresholds.yml`.

Secrets and keystore aliases are per build profile. Do not commit a keystore.

Policy and deviations: [guardrails-compliance.mdc](../../../.cursor/rules/guardrails-compliance.mdc).
Tool choice: [build-test-environments.mdc](../../../.cursor/rules/build-test-environments.mdc).
