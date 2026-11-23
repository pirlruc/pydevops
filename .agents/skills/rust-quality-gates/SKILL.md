---
name: rust-quality-gates
description: 'Prove RUST-* quality gates still hold before finishing Rust edits. Use when editing files that match: **/Cargo.toml.'
paths: '**/Cargo.toml'
disable-model-invocation: true
---

<!-- Generated from .cursor/rules by scripts/render-agent-instructions.py. Edit the .mdc files, then re-run that script. -->

Cursor applies the matching `.cursor/rules` file by glob and does not auto-invoke this skill. Other agents should follow this skill when the description matches.

# Rust quality gates

When you add or edit Rust, prove the org Rust guardrails still hold before finishing.
Read floors from `docs/guardrails/rust/profile.thresholds.yml`. Do not bake numbers here.

Run the repo local parity script when it exists. Otherwise run rustfmt, clippy with
warnings denied, and the coverage command the Rust caller template names. Record the
MSRV in `Cargo.toml`. `cargo deny` and `cargo audit` are part of the pack.

Policy and deviations: [guardrails-compliance.mdc](../../../.cursor/rules/guardrails-compliance.mdc).
Tool choice: [build-test-environments.mdc](../../../.cursor/rules/build-test-environments.mdc).
