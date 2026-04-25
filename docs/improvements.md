# Suggestions and improvements

Backlog of optional improvements that are **not yet fully implemented** in this repository.
Completed items have been removed; see [`ai-agent-handoff.md`](./ai-agent-handoff.md) for current
behavior.

## High priority

1. **Move Harden-Runner from audit to block mode per job** — Current workflows use
   `egress-policy: audit`. Build job-specific allow lists for GitHub APIs, PyPI, npm, Semgrep,
   Anchore/Syft/Grype downloads, ZAP/Locust dependencies, and any release endpoints before switching
   to `egress-policy: block`.
2. **Pin third-party GitHub Actions to full-length commit SHAs** — The repository currently uses
   centrally managed ref pins in
   [`.github/dependencies/github-actions-pins.json`](../.github/dependencies/github-actions-pins.json).
   Full SHA pinning would reduce tag-moving risk, but needs an update process that still keeps
   Dependabot or a pin refresh workflow practical.

## Medium priority

1. **Generate release provenance** — Add SLSA provenance for release artifacts and document how app
   repositories should consume or verify it. [`versioning.md`](./versioning.md) already notes this
   as future supply-chain hardening.
2. **Decide whether Scorecard should gate PRs** — Scheduled Scorecard already runs with
   `publish_results: true`, and PR/push Scorecard currently participates in the supply-chain gate.
   Consider making PR Scorecard report-only if branch-protection noise outweighs the value of
   gating.
3. **Add policy tests for Harden-Runner endpoint allow lists** — Once egress block mode is designed,
   add a lightweight verification step or documented checklist so endpoint drift is caught when
   tools are upgraded.

## Low priority

1. **Tune Semgrep defaults per application profile** — The reusable workflow currently uses the
   pinned Semgrep install plus repository rules. Add optional presets or severity filters only if
   `p/python`-style noise blocks real consumers.
2. **Document fork contribution strategy for app repositories** — This repo avoids unsafe
   `pull_request_target` checkout patterns and the PR comment job can use `github.token` or an
   optional caller PAT. App playbooks can still document whether fork PRs are supported, same-repo
   PRs are preferred, or maintainers should rerun trusted workflows manually.
3. **OIDC guidance for external cloud pulls/pushes** — If future workflows publish images, SBOMs, or
   attestations to AWS/GCP/Azure, prefer workload identity over long-lived secrets and document the
   expected cloud roles.
4. **Add lightweight documentation drift checks** — A small script or CI step could scan docs for
   stale tool versions, removed hook names, and outdated action refs after dependency or workflow
   pin updates.
