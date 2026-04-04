# Suggestions and improvements

Optional hardening and UX ideas. **Status** notes what is already reflected in this repository.

## Workflow / runner hardening

1. **Tighten Harden-Runner egress** — Move from `audit` to `block` per job using StepSecurity allow lists (GitHub API, PyPI, Semgrep CDN, Anchore install scripts, etc.). **Status:** still `audit` on heavy jobs until lists are validated per environment.
2. **Pin third-party actions to full-length commit SHAs** — Reduces tag-moving risk; pair with Dependabot version updates. **Status:** partial; semver tags in use; SHA pinning can be adopted incrementally.
3. **OIDC for cloud pulls** — If you later push images or SBOMs to AWS/GCP, prefer workload identity over long-lived secrets. **Status:** documentation only.
4. **Separate “report only” Scorecard** — Run Scorecard on a schedule with `publish_results: true`, and use a stricter PR job that fails only on actionlint/zizmor. **Status:** deferred; current **Reusable workflows quality** runs Scorecard on PR/push when not a fork.

## Quality pipeline

5. **Require artifacts for High strictness** — **Done:** `HIGH_REQUIRED_FILES` in `scripts/quality_gates` fails High when outputs are missing or empty.
6. **Semgrep tuning** — Replace or supplement `p/python` with a smaller ruleset or `severity` filters if noise blocks merges. **Status:** optional per app.
7. **Split long jobs** — Break `python-quality` into parallel jobs (lint vs test vs security) with aggregation. **Status:** deferred (large workflow change).
8. **Caching** — **Partial:** **DevOps scripts CI** caches `~/.cache/uv`. Full `python-quality` caching can follow once egress policies are stable.

## Supply chain

9. **Generate provenance** — SLSA provenance for release artifacts. **Status:** noted in [versioning.md](./versioning.md); optional for app repos.
10. **Dependency review** — **Done:** [.github/workflows/dependency-review.yml](../.github/workflows/dependency-review.yml) runs on PRs that touch common lockfiles. **Dependabot** covers `uv`/`uv.lock`, `github-actions`, pip/npm manifests under [`.github/dependencies/`](../.github/dependencies/), and the shared **uv CLI** version in `uv-version.txt` (see [dependency-management.md](./dependency-management.md)). **Python EOL** uses [.github/workflows/python-eol-watch.yml](../.github/workflows/python-eol-watch.yml) (Issues), not Dependabot.

## Documentation / operations

11. **Versioning runbook** — **Done:** [versioning.md](./versioning.md).
12. **Fork PR strategy** — For contributions from forks, avoid unsafe `pull_request_target` + unrestricted checkout; prefer same-repo PRs or a carefully scoped PAT. **Status:** PR comment job already skips forks; document in app playbooks as needed.
