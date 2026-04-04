# Workflows reference

Workflows are split by audience; see also [`.github/workflows/README.md`](../.github/workflows/README.md).

---

## Application repositories (consumers)

These workflows are intended to be referenced from **your app** repo via `uses: pirlruc/pydevops/.github/workflows/…@vX.Y.Z` (pin the workflow definition to a tag or SHA you trust). Pass **`devops_ref`** so the **checkout** of this repo under `.devops` matches the scripts and composites you want at runtime (often the same tag as `uses:`).

### `python-quality.yml`

**Purpose:** Central Quality-as-a-Service pipeline: multi-job gated CI (shield, static, supply chain, tests, reporting), optional DAST, GitHub Release with the quality bundle on SemVer tags when all gates pass, and (on same-repo pull requests) a PR comment.

#### GitHub limitation (dynamic `uses:` vs dynamic checkout)

GitHub does **not** allow the **`uses:`** line of a **reusable workflow** call to be a full expression like `${{ inputs.foo }}/.github/workflows/bar.yml@${{ inputs.ref }}`. Callers therefore pin a **literal** `uses: pirlruc/pydevops/.github/workflows/python-quality.yml@vX.Y.Z`. The **dynamic ref** you need day to day is the **`devops_ref` input**, which controls **`actions/checkout`** of the DevOps repo into `.devops` inside each job. The repo is **`pirlruc/pydevops` by default** (`devops_repository` defaults there); override only if you fork.

#### How the pipeline is structured (jobs and composites)

Jobs run on **separate runners**; phase outputs are merged in the reporting job from uploaded artifacts. Composites under `.github/actions/` stay the unit of reuse (`./.devops/.github/actions/…`).

| Job | Role | Composites / tools (high level) |
| --- | --- | --- |
| **quality-shield** | Shield — stop leaks early | `qa-secrets-sast`: **Gitleaks** (fail on finding), **Semgrep** SARIF (`continue-on-error` on scan); **High**: `python -m scripts.quality_gates --semgrep-shield-only` (0 SARIF **error**-level results, ≤ 5 **warning**-level) |
| **quality-static** | Gatekeeper — static | `qa-install-toolchain`, `qa-app-install-and-ruff`, `qa-run-quality-phase` (`static`) |
| **quality-supply-chain** | SBOM / vuln / deps (parallel with static after shield) | Same toolchain + install, `qa-run-quality-phase` (`security`) |
| **quality-test** | Tests (after static) | Same toolchain + install, `qa-run-quality-phase` (`test`) |
| **quality-report** | Merge artifacts, **license** gate, full **`scripts.quality_gates`**, consolidate, bundle + PR comment artifact | `if: always()` on the job; final step fails the job if license or gates failed (after uploads) |
| **pr-quality-comment** | Post PR summary | Downloads comment artifact |
| **quality-dast** | Optional ZAP + Locust | After tests when `enable_dast` |
| **release-github** | Tag-only GitHub Release | **`environment: production`**; needs supply + test + report + dast; runs only on `refs/tags/v*.*.*` (SemVer) when **`gates_passed`** is true and DAST succeeded or was skipped |

The shell driver `scripts/ci_run_quality.sh` honors **`QUALITY_PHASES`** per composite call (`static`, `security`, or `test`).

**Mutation testing (Mutmut)** stays in `mutmut-nightly.yml`, not in this pipeline.

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
| `quality-shield` | read | write | write | — |
| `quality-static`, `quality-supply-chain`, `quality-test`, `quality-report` | read | write | — | — |
| `pr-quality-comment` | read | read | — | write |
| `quality-dast` | read | write | — | — |
| `release-github` | write | — | — | — |

- **`actions: write`** — upload/download workflow artifacts.
- **`security-events: write`** — upload SARIF (Gitleaks, Semgrep) on the shield job when code scanning is available.
- **`pull-requests: write`** — post the summary comment (same-repo PRs only; fork PRs skip).

**Inputs (`workflow_call`)**

| Input | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `devops_repository` | string | no | `pirlruc/pydevops` | DevOps `owner/name` for `.devops` checkout |
| `devops_ref` | string | yes | — | Tag, branch, or SHA for `.devops` checkout (prefer SemVer tag, e.g. `v1.0.0`) |
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

### `reusable-workflows-quality.yml`

**Purpose:** Validates workflow and composite-action definitions with **actionlint**, **zizmor** (config: `.github/config/zizmor.yml`), **OpenSSF Scorecard** (SARIF publish), and **StepSecurity Harden-Runner**.

**Triggers:** Pull requests and pushes that touch `.github/`, `examples/`, or `docs/`; **`workflow_dispatch`**; weekly schedule (Monday 06:00 UTC).

**`GITHUB_TOKEN` scopes**

| Job | `contents` | `security-events` | `id-token` |
| --- | --- | --- | --- |
| `actionlint-zizmor` | read | — | — |
| `openssf-scorecard` | read | write | write |

Scorecard runs only when `github.event.repository.fork == false`.

**Secrets:** None.

---

### `devops-scripts-ci.yml`

**Purpose:** `pytest` (with coverage floor), `pylint` on `scripts/`, `interrogate` on `scripts/`, and Radon checks on `scripts/quality_gates/`.

**Triggers:** Push and pull requests affecting `scripts/`, `tests/`, `pyproject.toml`, or `uv.lock`.

**`GITHUB_TOKEN` scopes:** `contents: read` only.

---

### `dependency-review.yml`

**Purpose:** GitHub [Dependency review](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review) on PRs that change common lockfiles or dependency manifests.

**`GITHUB_TOKEN` scopes:** `contents: read`, `pull-requests: write`.

---

### `python-eol-watch.yml`

**Purpose:** Opens **GitHub Issues** when a Python version listed in [`.github/config/python-support-versions.json`](../.github/config/python-support-versions.json) is **past EOL** or within **90 days** of EOL, using the [endoflife.date](https://endoflife.date/) API. This complements **Dependabot**, which does not alert on CPython end-of-life.

**Triggers:** Weekly schedule (Monday 07:30 UTC), `workflow_dispatch`, and pushes to `main`/`master` that change the policy file or this workflow.

**`GITHUB_TOKEN` scopes:** `contents: read`, `issues: write`.

**Docs:** [dependency-management.md](./dependency-management.md).

---

### `mutmut-nightly.yml`

**Purpose:** Optional scheduled / manual mutation testing with Mutmut (pin: `.github/dependencies/mutmut/requirements.txt`).

**Triggers:** Weekly cron (Monday 03:00 UTC) and `workflow_dispatch`.

**`GITHUB_TOKEN` scopes:** `contents: read`, `actions: write`.

**Secrets:** None required.

---

### `publish-pypi.yml`

**Purpose:** Build with `uv build` and publish **this** repository’s package to PyPI using **Trusted Publishing (OIDC)**.

**Triggers:** **`workflow_dispatch` only** (manual). Pin or extend the workflow if you need tag-scoped builds.

**Environment:** **`pypi`** — use GitHub Environment protection rules for approval gates.

**`GITHUB_TOKEN` scopes:** `contents: read`, `id-token: write`.

**Secrets:** None on GitHub; configure the [PyPI trusted publisher](https://docs.pypi.org/trusted-publishers/) for this repository.

---
