# DevOps Quality-as-a-Service

Reusable GitHub Actions workflows and scripts for high-performance Python CI/CD: **uv**, **Ruff**,
**Pylint**, **Mypy**, **pydoclint**, **jscpd**, **Radon**, **Gitleaks**, **Semgrep**, **Bandit**,
**deptry**, **pip-audit**, **Syft**, **Grype**, **pytest**/**coverage**, optional **DAST** (ZAP +
Locust) and **Mutmut** (scheduled).

## Documentation

- **[Which workflow is for apps vs this repo](./.github/workflows/README.md)** (short index)
- **[Workflows (inputs, secrets, permissions, Dependabot)](./docs/workflows.md)**
- **[AI / maintainer handoff](./docs/ai-agent-handoff.md)**

## Example app integration

See **[`examples/call-python-quality.yml`](./examples/call-python-quality.yml)** and
[`examples/README.md`](./examples/README.md).

## Versioning

Pin callers to SemVer tags, for example `@2.0.0`. The reusable workflow checks out **`.devops`**
from the **same repo and ref** as that `uses:` pin (via `github.workflow_ref`) when
**`devops_repository`** / **`devops_ref`** are omitted; set those inputs only to override (forks,
drift).

```yaml
jobs:
  quality:
    uses: pirlruc/pydevops/.github/workflows/python-quality.yml@2.0.0
    with:
      strictness_level: High
      docstring_format: Google
      enable_dast: false
      license_deny_list: '["GPL-3.0-only"]'
    secrets: inherit
```

Cutting a release: land `main`, create an annotated tag (`git tag -a 2.0.0 -m "Release 2.0.0"`),
and publish a GitHub Release. Prefer tags without a `v` prefix to match existing `1.0.0` / `1.1.0`.

## Repository layout

| Path                                       | Purpose                                                                           |
| ------------------------------------------ | --------------------------------------------------------------------------------- |
| `.github/workflows/README.md`              | **App vs DevOps** workflow index                                                  |
| `.github/workflows/python-quality.yml`     | **Apps:** `workflow_call` multi-job quality pipeline + optional tag release asset |
| `.github/workflows/publish-pypi.yml`       | **This repo:** manual PyPI (`workflow_dispatch`, `environment: pypi`)             |
| `.github/workflows/devops-ci.yml`          | **This repo:** consolidated CI (lint, Scorecard, dependency review, scripts jobs) |
| `.github/workflows/devops-scheduled.yml`   | **This repo:** Thursday lint/Scorecard/Mutmut/EOL |
| `docs/`                                    | Workflows, handoff, issues, deviations |
| `.github/dependabot.yml`                   | uv, pip/npm under `dependencies/`, GitHub Actions                                 |
| `.github/dependencies/`                    | Pinned tools, `uv-version.txt`, jscpd npm package                                 |
| `.github/config/`                          | zizmor, Semgrep rules, `python-support-versions.json`                             |
| `.github/actions/install-uv`               | Composite: uv CLI from `uv-version.txt`                                           |
| `.github/actions/setup-uv-python`          | Composite: uv + `uv python install` (callers from `.devops`)                      |
| `.github/actions/qa-*`                     | Composites: secrets/SAST, toolchain, app+Ruff, phased `ci_run_quality.sh`         |
| `.github/config/semgrep/python-custom.yml` | Custom Semgrep rules                                                              |
| `scripts/`                                 | Metrics, gates, CI bundle shell script                                            |
| `examples/`                                | Minimal caller workflow samples                                                   |

## Local tooling (uv)

```bash
cd /path/to/devops-repo
uv sync
uv run python -m scripts.quality_gates
```

Set `QUALITY_OUTPUT_DIR` to your artifact directory when running gates locally.

## PyPI publishing

Configure [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) for this repository on
PyPI, create a **`pypi`**
[environment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
with any required approvals, then run **Publish to PyPI** via **`workflow_dispatch`**.
