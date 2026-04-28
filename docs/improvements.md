# Suggestions and improvements

Backlog of optional improvements that are **not yet fully implemented** in this repository.
Completed items have been removed; see [`ai-agent-handoff.md`](./ai-agent-handoff.md) for current
behavior.

## High priority

1. **Move Harden-Runner from audit to block mode per job** — Current workflows use
   `egress-policy: audit`. Build job-specific allow lists for GitHub APIs, PyPI, npm, Semgrep,
   Anchore/Syft/Grype downloads, ZAP/Locust dependencies, and any release endpoints before switching
   to `egress-policy: block`.
2. **Add branch protection required-check policy docs** — Define and document the exact required
   status checks for `main`/`master` (for example, workflow lint, scripts quality, and supply chain)
   so policy is explicit and reproducible across repository settings changes.

## Medium priority

1. **Document and verify attestation consumption** — Artifact attestations are now emitted in release
   publishing flows; add a short verification playbook (CLI commands + expected outputs) and an
   optional CI check for tag builds that validates generated attestations can be resolved.
2. **Decide whether Scorecard should gate PRs** — Scheduled Scorecard already runs with
   `publish_results: true`, and PR/push Scorecard currently participates in the supply-chain gate.
   Consider making PR Scorecard report-only if branch-protection noise outweighs the value of
   gating.
3. **Add policy tests for Harden-Runner endpoint allow lists** — Once egress block mode is designed,
   add a lightweight verification step or documented checklist so endpoint drift is caught when
   tools are upgraded.
4. **Bind manual PyPI publish to a validated tag commit** — Add an explicit guard in
   `publish-pypi.yml` to verify that the requested tag commit has passed the required quality checks
   before allowing publication.

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
5. **Track and review security-lint suppressions periodically** — Add a small scheduled reminder or
   checklist item to revisit suppressed findings (for example, zizmor suppressions) and prune entries
   that are no longer needed.
