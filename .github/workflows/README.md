# Workflows in this repository

GitHub only loads workflow files from `.github/workflows/` (no subdirectories for execution). Files are grouped here by **who should reference them**.

## For **application** repositories (consumers)

These define reusable automation you call with `uses: pirlruc/pydevops/.github/workflows/…@TAG`.

| Workflow | Purpose |
| --- | --- |
| **`python-quality.yml`** | Main QaaS pipeline (`workflow_call` + `workflow_dispatch`). See [workflows.md](../../docs/workflows.md#python-qualityyml). |

Optional: **`publish-pypi.yml`** is only relevant if the **app** (or this repo) publishes a Python package from the same layout; most apps will not call it from the DevOps repo.

## For **this DevOps** repository only

Run on pushes/PRs to this repo (or on schedule). **Do not** point application repos at these as `uses:` entry points unless you intentionally reuse a pattern.

| Workflow | Purpose |
| --- | --- |
| **`devops-ci.yml`** | Path filter → **workflow lint** (actionlint + zizmor), **scripts** (single job: pytest, pylint, interrogate, Radon CC/MI), **supply chain** (Scorecard + dependency review on PRs) |
| **`devops-scheduled.yml`** | Weekly lint, Scorecard, Mutmut (score ≥ 85%), Python EOL issues; push-triggered EOL-only run for policy file edits |
| **`publish-pypi.yml`** | Manual PyPI publish (`workflow_dispatch`, `environment: pypi`) |

## Layout elsewhere under `.github/`

| Path | Role |
| --- | --- |
| **`dependencies/`** | Version pins consumed by Dependabot and by workflows/scripts (`requirements.txt`, `jscpd/package.json`, `uv-version.txt`) |
| **`config/`** | Tool policy files (zizmor, Semgrep rules, Python interpreter policy for EOL watch) |
| **`actions/`** | Composites: `install-uv`, `setup-uv-python`, **`qa-*`** (quality pipeline phases), … |
