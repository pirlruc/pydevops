# Workflows reference

Workflows are split by audience; see also [`.github/workflows/README.md`](../.github/workflows/README.md).

---

## Application repositories (consumers)

These workflows are intended to be referenced from **your app** repo via `uses: pirlruc/pydevops/.github/workflows/…@vX.Y.Z` (with matching `pydevops_ref`).

### `python-quality.yml`

**Purpose:** Central Quality-as-a-Service pipeline: static analysis, tests/coverage, SBOM, secret/SAST scans, optional DAST, artifact bundle, and (on same-repo pull requests) a PR comment.

#### How the pipeline is structured (Gatekeeper / Shield / Tests)

The job is split into **composite actions** under `.github/actions/` (not separate `workflow_call` files) because GitHub does not support a **parameterized** `uses: ${{ inputs.devops_repository }}/…` for nested reusable workflows from arbitrary app repos. Composites referenced as `./.devops/.github/actions/…` keep a single checkout and one shared `quality-output/` directory.

| Your concept | Composite / step | Tools (high level) |
| --- | --- | --- |
| **Shield — secrets & SAST** (early) | `qa-secrets-sast` | **Gitleaks** (JSON + SARIF, fail on leak), **Semgrep** (`p/python` + custom rules, SARIF + blocking scan) |
| **Toolchain** | `qa-install-toolchain` | Node (jscpd), **cloc**, **Syft** / **Grype** binaries, **uv** + Python, DevOps `uv sync`, pinned CLIs from `dependencies/quality-tools` |
| **Gatekeeper — app + Ruff** | `qa-app-install-and-ruff` | App `uv sync` / install command, **Ruff** with QaaS pydocstyle convention |
| **Gatekeeper — static bundle** | `qa-run-quality-phase` (`static`) | **Pylint**, **Mypy**, **pydoclint**, **Interrogate**, **jscpd**, **Radon** CC/MI |
| **Shield — supply chain** | `qa-run-quality-phase` (`security`) | **`uv lock --check`**, **Bandit**, **deptry**, **pip-audit**, **Syft** SBOM (CycloneDX + SPDX), **Grype** JSON on SBOM |
| **Tests** | `qa-run-quality-phase` (`test`) | **Pytest** + **pytest-cov** (line + branch) |

Gitleaks and Semgrep run **before** the full toolchain so secret and pattern issues fail without waiting for all tool installs. The shell driver `scripts/ci_run_quality.sh` honors **`QUALITY_PHASES`** (`static`, `security`, `test`, or `all`) for the three bundle steps.

**Mutation testing (Mutmut)** stays in the separate scheduled workflow `mutmut-nightly.yml` (optional / nightly), not in this pipeline.

**Triggers**

- `workflow_call` — primary entry point for app repositories.
- `workflow_dispatch` — manual runs (self-test / debugging).

**`GITHUB_TOKEN` scopes (by job)**

| Job | `contents` | `actions` | `security-events` | `pull-requests` |
| --- | --- | --- | --- | --- |
| `python-quality` | read | write | write | — |
| `pr-quality-comment` | read | read | — | write |
| `dast` | read | write | — | — |

- **`actions: write`** — upload workflow artifacts (quality bundle, PR comment body).
- **`security-events: write`** — upload SARIF (Gitleaks, Semgrep) when GitHub Advanced Security / code scanning is available.
- **`pull-requests: write`** — post the summary comment (only on pull requests from the **same** repository; fork PRs skip the comment job to avoid token limitations).

**Inputs (`workflow_call`)**

| Input | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `devops_repository` | string | yes | — | `owner/name` of this DevOps repo |
| `devops_ref` | string | yes | — | Tag, branch, or SHA (prefer SemVer tag, e.g. `v1.0.0`) |
| `strictness_level` | string | no | `Medium` | `Low` \| `Medium` \| `High` — see **Strictness tiers** below |
| `docstring_format` | string | no | `Google` | `Google` \| `Numpy` \| `Pep257` (Pep257 maps to Google for pydoclint) |
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
| `github_token` | No | Optional PAT override for PR comments (e.g. forks / bots). If omitted, `github.token` is used in the PR comment job. |

#### Strictness tiers (`strictness_level`)

Gates are evaluated in `scripts/quality_gates` from CI artifacts. **Docstring coverage** (from **Interrogate**, `interrogate.txt`) is enforced for every tier — **High requires at least 95%**.

| Tier | Docstring coverage (min) | Docstring issue rate (pydoclint / KLoC comments, max) | Notes |
| --- | --- | --- | --- |
| **Low** | ≥ 70% | ≤ 8.0 | Relaxed defaults for legacy codebases |
| **Medium** | ≥ 85% | ≤ 5.0 | Default for most callers |
| **High** | **≥ 95%** | ≤ 2.0 | Also: Pylint ≥ 9.0, max cyclomatic ≤ 5 (&lt; 6), min Radon MI ≥ 60, stricter coverage/duplication/vuln caps; required artifacts in `HIGH_REQUIRED_FILES` (`scripts/quality_gates/config.py`) must exist |

Other numeric thresholds (coverage %, Pylint, Radon CC/MI, duplication, issues/KLoC, vulnerabilities) are defined alongside these in the same `Thresholds` table in code.

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

**Triggers:** Push of tags matching `v*.*.*`.

**`GITHUB_TOKEN` scopes:** `contents: read`, `id-token: write`.

**Secrets:** None on GitHub; configure the [PyPI trusted publisher](https://docs.pypi.org/trusted-publishers/) for this repository.

---
