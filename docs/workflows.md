# Workflows reference

Workflows are split by audience; see also [`.github/workflows/README.md`](../.github/workflows/README.md).

---

## Application repositories (consumers)

These workflows are intended to be referenced from **your app** repo via `uses: pirlruc/pydevops/.github/workflows/…@vX.Y.Z` (pin the workflow definition to a tag or SHA you trust). **`devops_repository`** and **`devops_ref`** are optional: when empty, the workflow parses **`github.workflow_ref`** so the **`.devops`** checkout matches the same repo and ref as the reusable workflow file (override when you need a fork or a different scripts ref than the workflow YAML pin).

### `python-quality.yml`

**Purpose:** Central Quality-as-a-Service pipeline: multi-job gated CI (shield, static, supply chain, tests, reporting), optional DAST, GitHub Release with the quality bundle on SemVer tags when all gates pass, and (on same-repo pull requests) a PR comment.

#### GitHub limitation (dynamic `uses:` vs dynamic checkout)

GitHub does **not** allow the **`uses:`** line of a **reusable workflow** call to be a full expression like `${{ inputs.foo }}/.github/workflows/bar.yml@${{ inputs.ref }}`. Callers pin a **literal** `uses: pirlruc/pydevops/.github/workflows/python-quality.yml@vX.Y.Z`. The **`devops-coordinates`** job derives **`.devops`** **repository** and **ref** from **`github.workflow_ref`** when inputs are empty; optional **`devops_repository`** / **`devops_ref`** override that for forks or pin drift.

#### How the pipeline is structured (jobs and composites)

Jobs run on **separate runners**; phase outputs are merged in the reporting job from uploaded artifacts. Composites under `.github/actions/` stay the unit of reuse (`./.devops/.github/actions/…`).

| Job | Role | Composites / tools (high level) |
| --- | --- | --- |
| **devops-coordinates** | Resolve **`.devops`** checkout | Parses **`github.workflow_ref`** (or optional inputs); no app checkout |
| **quality-shield** | Shield — stop leaks early | `qa-secrets-sast`: **Gitleaks** (fail on finding), **Semgrep** SARIF (`continue-on-error` on scan); **High**: `python -m scripts.quality_gates --semgrep-shield-only` (0 SARIF **error**-level results, ≤ 5 **warning**-level) |
| **quality-static** | Gatekeeper — static | `qa-install-toolchain`, `qa-app-install-and-ruff`, `qa-run-quality-phase` (`static`) |
| **quality-supply-chain** | SBOM / vuln / deps (parallel with static after shield) | Same toolchain + install, `qa-run-quality-phase` (`security`) |
| **quality-test** | Tests (after static) | Same toolchain + install, `qa-run-quality-phase` (`test`) |
| **quality-report** | Merge artifacts, **license** gate, full **`scripts.quality_gates`**, consolidate, bundle + PR comment artifact | `if: always()` on the job; final step fails the job if license or gates failed (after uploads) |
| **pr-quality-comment** | Post PR summary | Downloads comment artifact |
| **quality-dast** | Optional ZAP + Locust | After tests when `enable_dast`; **`zaproxy/action-baseline`** runs the [OWASP ZAP](https://www.zaproxy.org/) **baseline** scan (passive checks against `dast_target_url` with the repo’s `.zap/rules.tsv` if present). Locust load smoke reads **`.github/dependencies/dast-python/requirements.txt`**. |
| **release-github** | Tag-only GitHub Release | **`environment: production`**; needs supply + test + report + dast; runs only on `refs/tags/v*.*.*` (SemVer) when **`gates_passed`** is true and DAST succeeded or was skipped |

The shell driver `scripts/ci_run_quality.sh` honors **`QUALITY_PHASES`** per composite call (`static`, `security`, or `test`).

**Mutation testing (Mutmut)** for **this** DevOps repo runs in [`devops-scheduled.yml`](../.github/workflows/devops-scheduled.yml), not in the app `python-quality` pipeline.

**Triggers**

- `workflow_call` — primary entry point for app repositories.
- `workflow_dispatch` — manual runs (self-test / debugging).

To produce **GitHub Releases** from **`release-github`**, the **calling** workflow must run on SemVer tag pushes (for example `on.push.tags: ['v*.*.*']`); the reusable job’s release step is gated on `refs/tags/v*.*.*` and successful gates.

**`workflow_call` outputs**

| Output | Meaning |
| --- | --- |
| `gates_passed` | `"true"` when license enforcement and full `scripts.quality_gates` succeeded in **quality-report** (string booleans as emitted by the job). |

**`GITHUB_TOKEN` scopes (by job)**

| Job | `contents` | `actions` | `security-events` | `pull-requests` |
| --- | --- | --- | --- | --- |
| `devops-coordinates` | *(default)* | — | — | — |
| `quality-shield` | read | write | write | — |
| `quality-static`, `quality-supply-chain`, `quality-test`, `quality-report` | read | write | — | — |
| `pr-quality-comment` | read | read | — | write |
| `quality-dast` | read | write | — | — |
| `release-github` | write | — | — | — |

- **`devops-coordinates`** — no explicit `permissions` block; only parses `github.workflow_ref` / inputs (no checkout in that job).
- **`actions: write`** — upload/download workflow artifacts.
- **`security-events: write`** — upload SARIF (Gitleaks, Semgrep) on the shield job when code scanning is available.
- **`pull-requests: write`** — post the summary comment (same-repo PRs only; fork PRs skip).

**Inputs (`workflow_call`)**

| Input | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `devops_repository` | string | no | *(empty)* | Optional override for DevOps `owner/name`. Empty: derive from `github.workflow_ref` or `github.repository`. |
| `devops_ref` | string | no | *(empty)* | Optional override for DevOps ref. Empty: derive from `github.workflow_ref` or `github.ref_name`. |
| `strictness_level` | string | no | `Medium` | `Low` \| `Medium` \| `High` — see **Strictness tiers** below |
| `docstring_format` | string | no | `Google` | `Google` \| `Numpy` \| `Pep257` — Ruff pydocstyle convention matches the name; **Pep257** uses pydoclint `--style=sphinx` (pydoclint has no pep257 mode; Google/NumPy section layouts conflict with pep257-focused Ruff) |
| `enable_dast` | boolean | no | `false` | Runs ZAP + Locust job after quality |
| `license_deny_list` | string | no | `[]` | JSON array string; SPDX substring deny list |
| `working_directory` | string | no | `.` | App subdirectory with `pyproject.toml` / package |
| `python_version` | string | no | `3.13` | Passed to `uv python install` |
| `app_install_command` | string | no | *(see workflow)* | Shell to install app deps; empty skips for `workflow_call` path |
| `docker_compose_file` | string | no | `docker-compose.yml` | Used when `enable_dast` is true |
| `dast_target_url` | string | no | `http://localhost:8080` | ZAP / Locust target |

**Secrets**

| Secret | Required | Purpose |
| --- | --- | --- |
| `caller_pat` | No | Optional caller PAT for PR comments (e.g. forks / bots). If omitted, `github.token` is used. (Do not use the name `github_token` for this mapping — GitHub reserves it for `workflow_call` secrets.) |

#### Strictness tiers (`strictness_level`)

Gates are evaluated in `scripts/quality_gates` from CI artifacts. **Docstring coverage** (from **Interrogate**, `interrogate.txt`) is checked against tier-specific minimums when `interrogate.txt` is present. **High** strictness also fails closed if `interrogate.txt` is missing or unparseable; **Low** and **Medium** skip the docstring coverage gate when that artifact is absent.

| Tier | Docstring coverage (min) | Docstring issue rate (pydoclint / KLoC comments, max) | Notes |
| --- | --- | --- | --- |
| **Low** | ≥ 70% | ≤ 8.0 | Relaxed defaults for legacy codebases |
| **Medium** | ≥ 85% | ≤ 5.0 | Default for most callers |
| **High** | **≥ 95%** | ≤ 2.0 | Also: Pylint ≥ 9.5, max cyclomatic ≤ 5 (&lt; 6), min Radon MI ≥ 60, stricter coverage/duplication/vuln caps; **Semgrep** SARIF (`semgrep.sarif`): 0 **error**-level results, ≤ 5 **warning**-level; required artifacts in `HIGH_REQUIRED_FILES` (`scripts/quality_gates/config.py`) must exist (including **`pydoclint.txt`** and **`semgrep.sarif`**) |

Other numeric thresholds (coverage %, Pylint, Radon CC/MI, duplication, issues/KLoC, vulnerabilities) are defined alongside these in the same `Thresholds` table in code.

The **`Evaluate configured quality gates`** step (`python -m scripts.quality_gates`) is the **only** enforcement of aggregate vulnerability counts from **pip-audit** and **Grype** JSON artifacts; tier limits (for example Low allows up to two high-severity findings) come from that table. Do not add a separate Grype CLI `--fail-on` step in the same job, or it would override those thresholds.

**Cross-job cache:** Static, supply-chain, and test jobs restore **`~/.cache/uv`** via **`actions/cache`** so repeated `uv` work stays warm across parallel jobs.

**Caller configuration**

Use `secrets: inherit` only if you intentionally pass organization/caller secrets into the reusable workflow. The pipeline does not require custom secrets for the default same-repository PR flow.

##### Caller permissions

Callers should **not** grant broad default scopes. Recommended wrapper:

```yaml
permissions: {}

jobs:
  python-quality:
    uses: pirlruc/pydevops/.github/workflows/python-quality.yml@vX.Y.Z
    with: { ... }
    secrets: inherit
```

The reusable workflow’s jobs then add only the scopes listed above. If your organization enforces a maximum token policy, ensure it allows at least those scopes for the jobs that run.

---

## This DevOps repository only

The following workflows are **not** meant as the primary `uses:` target for application quality pipelines. They maintain **this** repo’s workflows, scripts, and supply-chain signals.

### `devops-ci.yml`

**Purpose:** Single entry workflow for most pushes/PRs on this repo: **path-filtered jobs** (via `dorny/paths-filter`) for **workflow lint** (**actionlint** + **zizmor** in one job; actionlint uses **`continue-on-error: true`** so zizmor still runs; **gate** lists failing tools), **supply chain** (**OpenSSF Scorecard** when workflow paths apply + **dependency review** on pull requests; shared **gate**), and **one scripts job** (**pytest**, **pylint**, **interrogate**, Radon CC, Radon MI after a single **`uv sync`**; **gate** lists failing tools).

**Triggers:** Pull request and push to `main`/`master` with a **union** of paths (scripts, tests, lockfiles, `.github/`, `examples/`, `docs/`, etc.); **`workflow_dispatch`** runs all path groups.

**`GITHUB_TOKEN` scopes:** Vary by job (`contents`, `pull-requests`, `security-events`, `id-token` as needed).

---

### `devops-scheduled.yml`

**Purpose:** Weekly **Monday 06:00 UTC** maintenance (and **`workflow_dispatch`**): **workflow lint** (actionlint + zizmor + gate), **OpenSSF Scorecard** + gate, **Mutmut** (`mutmut run` → `export-cicd-stats` → **`scripts/mutmut_score_gate.py`** with **`MUTMUT_MIN_SCORE=85`**) + artifact upload, **Python EOL watch** (issues) + gate.

**Push** to `main`/`master` that only changes [`.github/config/python-support-versions.json`](../.github/config/python-support-versions.json) or this workflow runs **only** the **EOL** job (lint / mutmut / scorecard jobs are skipped on `push` so policy edits do not run mutation testing).

**`GITHUB_TOKEN` scopes:** Per job (`contents`, `actions`, `issues`, `security-events`, `id-token`).

---

### `publish-pypi.yml`

**Purpose:** Build with `uv build` and publish **this** repository’s package to PyPI using **Trusted Publishing (OIDC)**.

**Triggers:** **`workflow_dispatch` only** (manual). Pin or extend the workflow if you need tag-scoped builds.

**Environment:** **`pypi`** — use GitHub Environment protection rules for approval gates.

**`GITHUB_TOKEN` scopes:** `contents: read`, `id-token: write`.

**Secrets:** None on GitHub; configure the [PyPI trusted publisher](https://docs.pypi.org/trusted-publishers/) for this repository.

---
