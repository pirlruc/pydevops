# DevOps Quality-as-a-Service

Reusable GitHub Actions workflows and scripts for high-performance Python CI/CD: **uv**, **Ruff**, **Pylint**, **Mypy**, **pydoclint**, **jscpd**, **Radon**, **Gitleaks**, **Semgrep**, **Bandit**, **deptry**, **pip-audit**, **Syft**, **Grype**, **pytest**/**coverage**, optional **DAST** (ZAP + Locust) and **Mutmut** (scheduled).

## Documentation

Central reference material lives under **[`docs/`](./docs/README.md)**:

- **[Which workflow is for apps vs this repo](./.github/workflows/README.md)** (short index)
- **[Workflows (inputs, secrets, permissions)](./docs/workflows.md)**
- **[Security tooling (actionlint, zizmor, Scorecard, Harden-Runner)](./docs/security-tooling.md)**
- **[Improvements & suggestions](./docs/improvements.md)**
- **[Dependency updates & Python EOL](./docs/dependency-management.md)**
- **[AI / maintainer handoff (CI & gates context)](./docs/ai-agent-handoff.md)**

## Example app integration

See **[`examples/call-python-quality.yml`](./examples/call-python-quality.yml)** and [`examples/README.md`](./examples/README.md).

## Versioning

Pin callers to SemVer tags, for example `@v1.2.0`, and set `devops_ref` to the **same** tag:

```yaml
jobs:
  quality:
    uses: pirlruc/pydevops/.github/workflows/python-quality.yml@v1.2.0
    with:
      devops_repository: pirlruc/pydevops
      devops_ref: v1.2.0
      strictness_level: High
      docstring_format: Google
      enable_dast: false
      license_deny_list: '["GPL-3.0-only"]'
    secrets: inherit
```

## Repository layout

| Path | Purpose |
| --- | --- |
| `.github/workflows/README.md` | **App vs DevOps** workflow index |
| `.github/workflows/python-quality.yml` | **Apps:** `workflow_call` multi-job quality pipeline + optional tag release asset |
| `.github/workflows/publish-pypi.yml` | **This repo:** manual PyPI (`workflow_dispatch`, `environment: pypi`) |
| `.github/workflows/mutmut-nightly.yml` | **This repo:** mutation testing schedule |
| `.github/workflows/reusable-workflows-quality.yml` | **This repo:** actionlint, zizmor, Scorecard |
| `.github/workflows/devops-scripts-ci.yml` | **This repo:** pytest / pylint / Radon on `scripts/` |
| `.github/workflows/dependency-review.yml` | **This repo:** PR dependency review |
| `.github/workflows/python-eol-watch.yml` | **This repo:** Python EOL issues (endoflife.date) |
| `.github/dependabot.yml` | uv, pip/npm under `dependencies/`, GitHub Actions |
| `.github/dependencies/` | Pinned tools, `uv-version.txt`, jscpd npm package |
| `.github/config/` | zizmor, Semgrep rules, `python-support-versions.json` |
| `.github/actions/install-uv` | Composite: uv CLI from `uv-version.txt` |
| `.github/actions/setup-uv-python` | Composite: uv + `uv python install` (callers from `.devops`) |
| `.github/actions/qa-*` | Composites: secrets/SAST, toolchain, app+Ruff, phased `ci_run_quality.sh` |
| `.github/config/semgrep/python-custom.yml` | Custom Semgrep rules |
| `scripts/` | Metrics, gates, CI bundle shell script |
| `docs/` | Workflow and security tooling documentation |
| `examples/` | Minimal caller workflow samples |

## Local tooling (uv)

```bash
cd /path/to/devops-repo
uv sync
uv run python -m scripts.quality_gates
```

Set `QUALITY_OUTPUT_DIR` to your artifact directory when running gates locally.

## PyPI publishing

Configure [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) for this repository on PyPI, create a **`pypi`** [environment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment) with any required approvals, then run **Publish to PyPI** via **`workflow_dispatch`**.
