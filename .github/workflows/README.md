# Workflows in this repository

GitHub only loads workflow files from `.github/workflows/` (no subdirectories for execution). Files are grouped here by **who should reference them**.

## For **application** repositories (consumers)

These define reusable automation you call with `uses: pirlruc/pydevops/.github/workflows/…@TAG`.

| Workflow | Purpose |
| --- | --- |
| **`python-quality.yml`** | Main QaaS pipeline (`workflow_call` + `workflow_dispatch`). Implements **Gatekeeper / Shield / Tests** via composites (`qa-secrets-sast`, `qa-install-toolchain`, `qa-app-install-and-ruff`, `qa-run-quality-phase`). See [workflows.md](../docs/workflows.md#python-qualityyml). |

Optional: **`publish-pypi.yml`** is only relevant if the **app** (or this repo) publishes a Python package from the same layout; most apps will not call it from the DevOps repo.

## For **this DevOps** repository only

Run on pushes/PRs to this repo (or on schedule). **Do not** point application repos at these as `uses:` entry points unless you intentionally reuse a pattern.

| Workflow | Purpose |
| --- | --- |
| **`reusable-workflows-quality.yml`** | actionlint, zizmor, OpenSSF Scorecard |
| **`devops-scripts-ci.yml`** | pytest, pylint, interrogate, Radon on `scripts/` |
| **`dependency-review.yml`** | GitHub Dependency review on lockfile PRs |
| **`python-eol-watch.yml`** | Issues when tracked Python versions hit EOL (endoflife.date) |
| **`mutmut-nightly.yml`** | Scheduled mutation testing for this repo |
| **`publish-pypi.yml`** | Manual PyPI publish (**`workflow_dispatch`**, **`environment: pypi`**) |

## Layout elsewhere under `.github/`

| Path | Role |
| --- | --- |
| **`dependencies/`** | Version pins consumed by Dependabot and by workflows/scripts (`requirements.txt`, `jscpd/package.json`, `uv-version.txt`) |
| **`config/`** | Tool policy files (zizmor, Semgrep rules, Python interpreter policy for EOL watch) |
| **`actions/`** | Composites: `install-uv`, `setup-uv-python`, **`qa-*`** (quality pipeline phases), … |
