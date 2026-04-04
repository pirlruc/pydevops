# Dependency updates and Python support

## Layout

| Path | Role |
| --- | --- |
| [`.github/dependencies/`](../.github/dependencies/) | **Dependabot-managed** pins: `requirements.txt` subtrees, `jscpd/package.json`, `uv-version.txt`, `syft-version.txt` / `grype-version.txt` (Anchore CLI pins for `qa-install-toolchain`), and `emit-uv-version.sh` (used by composite actions) |
| [`.github/config/`](../.github/config/) | **Tool configuration** only (zizmor policy, Semgrep rules, Python interpreter list for EOL watch) — not package manifests |
| [`.github/dependabot.yml`](../.github/dependabot.yml) | Dependabot configuration |

## Dependabot ([`.github/dependabot.yml`](../.github/dependabot.yml))

| Ecosystem | Directory | What it updates |
| --- | --- | --- |
| `github-actions` | `/` | `uses:` references in `.github/workflows/**` and composite actions under `.github/actions/**` |
| `uv` | `/` | `pyproject.toml` / `uv.lock` |
| `pip` | `/.github/dependencies/quality-tools` | Pinned CLIs for `python-quality.yml` |
| `pip` | `/.github/dependencies/dast-python` | Locust pin for the DAST job |
| `pip` | `/.github/dependencies/semgrep` | Semgrep pin (pipx in workflow) |
| `pip` | `/.github/dependencies/zizmor` | zizmor constraint for workflow QA |
| `pip` | `/.github/dependencies/mutmut` | Mutmut constraint for the nightly job |
| `npm` | `/.github/dependencies/jscpd` | `jscpd` used from [`scripts/ci_run_quality.sh`](../scripts/ci_run_quality.sh) via `npx --prefix` |

After merging a Dependabot PR that changes a `requirements.txt` consumed by YAML, workflows already read that file; avoid duplicating the same version elsewhere.

## Astral uv CLI version (single source)

The **uv installer version** is **not** repeated in every workflow. It lives in [`.github/dependencies/uv-version.txt`](../.github/dependencies/uv-version.txt). Composite actions run [`.github/dependencies/emit-uv-version.sh`](../.github/dependencies/emit-uv-version.sh) and pass the value to `astral-sh/setup-uv@v5`:

- [`.github/actions/install-uv`](../.github/actions/install-uv/action.yml) — used by repo-only workflows (and the DAST job via `./.devops/.github/actions/install-uv`).
- [`.github/actions/setup-uv-python`](../.github/actions/setup-uv-python/action.yml) — same version source, then `uv python install` for app pipelines.

Bump **only** `uv-version.txt` (and merge) to roll the CLI forward. Dependabot does not update that file automatically.

## Not covered by Dependabot (manual or follow-up)

- **Syft** / **Grype** release versions in `syft-version.txt` and `grype-version.txt` (bump when you want new scanner behavior; composite installs pinned GitHub release tarballs).
- **Gitleaks** install URL / version in `qa-secrets-sast` / `python-quality.yml`.
- **actionlint** download version in `devops-ci.yml` and `devops-scheduled.yml` (`ACTIONLINT_VERSION`).
- Numeric **`with:`** inputs on third-party actions other than what composites centralize.

## Python interpreter policy

- **`pyproject.toml`** — `requires-python` is the minimum CPython for this repo’s code.
- **`.github/config/python-support-versions.json`** — minor versions monitored for **EOL** by `devops-scheduled.yml`; keep aligned with `requires-python` and the default `python_version` on `python-quality.yml`.

## EOL notifications (not Dependabot)

**Dependabot does not open alerts when a Python release branch reaches end-of-life.** For that, this repo runs [**`devops-scheduled.yml`**](../.github/workflows/devops-scheduled.yml), which compares [endoflife.date](https://endoflife.date/) to `.github/config/python-support-versions.json` and may open **`[Python EOL]`** or **`[Python EOL warning]`** issues.

## Dependency review

Pull requests that change lockfiles or manifests may run the **dependency review** job in [`.github/workflows/devops-ci.yml`](../.github/workflows/devops-ci.yml).
