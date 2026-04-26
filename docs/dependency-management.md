# Dependency updates and Python support

## Layout

| Path                                                                      | Role                                                                                                                                                                                                                                                                                                                                     |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`.github/dependencies/`](../.github/dependencies/)                       | **Pins:** `github-actions-pins.json` (canonical `uses:` map; supports `tag -> sha` entries for SHA pinning with readable version comments), `quality-tools/requirements.txt` (**generated** from `pyproject.toml`), `semgrep` / `dast-python` requirements (isolated; see below), `jscpd/package.json`, `uv-version.txt`, `syft-version.txt` / `grype-version.txt`, `actionlint/version.txt` + `actionlint/linux-amd64.sha256`, `emit-uv-version.sh` |
| **[`pyproject.toml`](../pyproject.toml)**                                 | **Single source** for Ruff, Pylint, Mypy, pytest, Bandit, pip-audit, etc. (`[dependency-groups].quality-tools`). Regenerate the committed requirements file with **`bash scripts/export_pinned_requirements.sh`** (runs `uv lock` + `scripts/export_quality_tools_requirements.py`).                                                     |
| **[`scripts/github_actions_pins.py`](../scripts/github_actions_pins.py)** | Applies or verifies `uses:` pins from `github-actions-pins.json` (`python3 scripts/github_actions_pins.py` or `--check`). Structured entries write `uses: owner/repo@<sha> # vX.Y.Z` so Scorecard gets immutable refs and humans keep version context. CI runs `--check` in **`devops-ci.yml`**.                                    |
| [`.github/config/`](../.github/config/)                                   | **Tool configuration** only (zizmor policy, Semgrep rules, Python interpreter list for EOL watch) — not package manifests                                                                                                                                                                                                                |
| [`.github/dependabot.yml`](../.github/dependabot.yml)                     | Dependabot configuration                                                                                                                                                                                                                                                                                                                 |

## Dependabot ([`.github/dependabot.yml`](../.github/dependabot.yml))

| Ecosystem        | Directory                           | What it updates                                                                                                                                                                                                                                                                                                       |
| ---------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `github-actions` | `/`                                 | `uses:` references in `.github/workflows/**` and `.github/actions/**` (Dependabot updates SHA pins; keep trailing `# v...` comments so version context remains visible)                                                                                                                                                            |
| `uv`             | `/`                                 | **`pyproject.toml` / `uv.lock`** — quality CLI pins and this repo’s dev dependencies (`quality-tools` + `scripts` groups). After a Dependabot `uv` PR, run **`bash scripts/export_pinned_requirements.sh`** so **`.github/dependencies/quality-tools/requirements.txt`** matches `[dependency-groups].quality-tools`. |
| `pip`            | `/.github/dependencies/dast-python` | Locust pin for the DAST job (**not** in root `uv.lock`; see **Resolver note** below)                                                                                                                                                                                                                                  |
| `pip`            | `/.github/dependencies/semgrep`     | Semgrep pin for pipx in **`qa-secrets-sast`** (same isolation)                                                                                                                                                                                                                                                        |
| `pip`            | `/.github/dependencies/zizmor`      | zizmor constraint for workflow QA                                                                                                                                                                                                                                                                                     |
| `pip`            | `/.github/dependencies/mutmut`      | Mutmut constraint for **`devops-scheduled.yml`**                                                                                                                                                                                                                                                                      |
| `npm`            | `/.github/dependencies/jscpd`       | `jscpd` used from [`scripts/ci_run_quality.sh`](../scripts/ci_run_quality.sh) via `npx`                                                                                                                                                                                                                               |
| `pre-commit`     | `/`                                 | `.pre-commit-config.yaml` hooks and revs                                                                                                                                                                                                                                                                                |

### Resolver note (Semgrep vs pip-audit)

**Semgrep** (via PyPI) declares **`tomli~=2.0.1`**. **pip-audit 2.10+** requires **`tomli>=2.2.1`**.
Those constraints cannot be satisfied in **one** shared `uv.lock`, so **Semgrep** and **Locust**
stay in **separate** `requirements.txt` files under `.github/dependencies/` while **all other
quality CLIs** are pinned in **`pyproject.toml`** and exported to
**`quality-tools/requirements.txt`**.

After merging a Dependabot PR that changes a manifest consumed by YAML, workflows already read that
file; avoid duplicating the same version string in workflow `run:` blocks.

For action refs, the preferred format is:

- `uses: owner/repo@<40-char-sha> # vX.Y.Z`

This keeps Scorecard `Pinned-Dependencies` compliant while preserving readable version context.

## Node.js runtime for JavaScript actions

Workflows set **`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"`** so actions that still declare a Node
20 runtime run on Node 24 on the runner (see
[GitHub’s Node 20 deprecation timeline](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/)).
**`dorny/paths-filter@v4.0.1`** and **`astral-sh/setup-uv@v8.0.0`** ship Node 24–compatible
runtimes. **`ci-supply-chain`** does **not** override this; **`actions/dependency-review-action`**
may still log a deprecation notice until the action ships a Node 24 runtime.

## Dependency review vs OpenSSF Scorecard (repository)

**[Dependency review](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review)**
can show **per-dependency** OpenSSF Scorecard scores for packages added in a PR. That is separate
from the **[OpenSSF Scorecard](https://scorecard.dev/)** job that scores **your repository’s**
practices (branch protection, workflows, etc.). This repo disables **`show-openssf-scorecard`** on
**`dependency-review-action`** so low scores on small transitive PyPI tools do not fail the PR;
supply-chain posture is still covered by vuln/license checks and the **OpenSSF Scorecard** step in
**`ci-supply-chain`** (and scheduled Scorecard).

## Astral uv CLI version (single source)

The **uv installer version** is **not** repeated in every workflow. It lives in
[`.github/dependencies/uv-version.txt`](../.github/dependencies/uv-version.txt). Composite actions
run [`.github/dependencies/emit-uv-version.sh`](../.github/dependencies/emit-uv-version.sh) and pass
the value to `astral-sh/setup-uv` (pin in
[`github-actions-pins.json`](../.github/dependencies/github-actions-pins.json)):

- [`.github/actions/install-uv`](../.github/actions/install-uv/action.yml) — used by repo-only
  workflows (and the DAST job via `./.devops/.github/actions/install-uv`).
- [`.github/actions/setup-uv-python`](../.github/actions/setup-uv-python/action.yml) — same version
  source, then `uv python install` for app pipelines.

Bump **only** `uv-version.txt` (and merge) to roll the CLI forward. Dependabot does not update that
file automatically.

## Not covered by Dependabot (manual or follow-up)

- **Syft** / **Grype** release versions in `syft-version.txt` and `grype-version.txt` (bump when you
  want new scanner behavior; composite installs pinned GitHub release tarballs).
- **Gitleaks** install URL / version in `qa-secrets-sast` / `python-quality.yml`.
- **actionlint** is installed from pinned release assets in `devops-ci.yml` /
  `devops-scheduled.yml`, with version + checksum in
  `.github/dependencies/actionlint/version.txt` and
  `.github/dependencies/actionlint/linux-amd64.sha256`.
- Numeric **`with:`** inputs on third-party actions other than what composites centralize.

## Python interpreter policy

- **`pyproject.toml`** — `requires-python` is the minimum CPython for this repo’s code.
- **`.github/config/python-support-versions.json`** — minor versions monitored for **EOL** by
  `devops-scheduled.yml`; keep aligned with `requires-python` and the default `python_version` on
  `python-quality.yml`.

## EOL notifications (not Dependabot)

**Dependabot does not open alerts when a Python release branch reaches end-of-life.** For that, this
repo runs [**`devops-scheduled.yml`**](../.github/workflows/devops-scheduled.yml), which compares
[endoflife.date](https://endoflife.date/) to `.github/config/python-support-versions.json` and may
open **`[Python EOL]`** or **`[Python EOL warning]`** issues.

## Dependency review

Pull requests run **dependency review** inside the **`ci-supply-chain`** job in
[`.github/workflows/devops-ci.yml`](../.github/workflows/devops-ci.yml) (with OpenSSF Scorecard on
the same job when workflow files warrant it). Use **`allow-dependencies-licenses`** (comma-separated
PURLs) in the workflow if you need to exempt specific packages from license checks when the graph
lacks SPDX metadata.
