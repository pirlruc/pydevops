# Changelog

All notable changes to this repository are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- `ci-python` on DHI Debian 13 (unsuffixed) and Alpine 3.24 (`-alpine`).
  Quality CLIs install from a hashed lock. jscpd comes from `npm ci`.
  syft and grype are the same DHI donors as ci-supply-chain. A local timing
  of apt plus the old syft/grype tarballs was 12s and did not include Node,
  uv, or the twelve quality CLIs, which `python-quality` installs three
  times. The image removes that repeat. SC-SIGN-001 is recorded. REL-PUB-004
  now cites the Hub token; PyPI can use OIDC. `python-quality` stays on the
  host until the published digest exists. Jobs have timeouts. Scheduled
  runs add secrets-sast and supply-chain. zizmor requires full SHA pins.
  Threshold fields are grouped so the pylint attribute disable can go.
  Final stages clear setuid and setgid bits.

## [3.0.2] - 2026-10-02

### Fixed

- Threshold drift requires `GUARDRAILS_READ_TOKEN` and removes the gitlink
  directory before checkout. The previous skip left the content check off,
  and checkout into the existing gitlink fails once the token is set.
  Dependabot still skips the job. Tag only. PyPI publish stays manual.

## [3.0.1] - 2026-10-01

### Added

- `installable_app: false` skips package install, mypy, and coverage floors
  for a `pyproject.toml` that is not an application (PDO-PYPROJECT-001).
- When `docs/guardrails/python/profile.thresholds.yml` is in the app checkout,
  coverage, complexity, maintainability, and docstring floors come from it.
  A missing key fails closed. If the file is absent, the strictness enum
  remains the fallback (PDO-THRESH-002).
- Lockfile urllib3 2.8.0 and virtualenv 21.12.1 (Dependabot).

## [3.0.0] - 2026-10-01

### Breaking

- Cross-repo callers must pass `devops_repository` and `devops_ref` equal to the
  `uses:` pin. `github.workflow_ref` is the caller, so an empty pair no longer
  checks out this repo (CI-034).
- The caller job must grant the permission union. See
  `examples/call-python-quality.yml`.
- DevOps `uv sync` and `uv run` use Python 3.13. `python_version` applies to
  the application only.
- mypy's exit code fails the quality script. `typecheck_strict: true` adds
  `--strict`.
- A missing SPDX SBOM fails the license gate. Semgrep findings block at Medium
  as well as High.

### Changed

- `docs/guardrails` tag **1.9.0** (`16a2c95c…`); `.github/scaffold` tag **1.8.0**
  (`ac9059fd…`). Decision links cite methodologies **1.8.0**.
- commondevops pin is **5.2.6** (`8aad4ba4…`).
- uv pin is **0.12.0**. `exclude-newer` is 7 days. pytest-cov is installed with
  `uv tool install pytest --with pytest-cov`.
- Quality artifacts keep 7 days. `mutmut-results` keeps 1 day.
- ruff 0.16.8, locust 2.46.6, toml-sort 0.25.0, typos 1.50.2.
- CI-032 and REL-PUB-004 recorded. The repository returns to private.
- Dependabot `registries: github-private` is attached to `uv`, `npm`, and
  `pre-commit` as well as `github-actions` (SC-DEP-005). `pip` stays off that
  registry.
- jscpd pin is **5.3.2** (exact). The Dependabot updater could not open the
  5.2.0 → 5.3.2 pull request. `--format python` and the JSON percentage path
  still match `scripts/ci_run_quality.sh`.

## [2.1.1] - 2026-09-15

### Changed

- Nested [commondevops](https://github.com/pirlruc/commondevops) pin is **5.1.2**
  (`b3c462bed0de4f6475e6be7875c4ababd831acc6`).
- Package version **2.1.1**. `check-ci-docker.sh` default is ci-lint **5.1.1**
  Alpine `sha256:35a82a43…`.

### Fixed

- OpenSSF Scorecard is advisory on this private repo (no `SCORECARD_TOKEN`).
  Blocking `true` plus an empty `repo_token` failed `DevOps CI` on `main`
  after paths-filter started selecting the Scorecard job.

## [2.1.0] - 2026-09-15

### Added

- Root CHANGELOG (REL-CHG-001). Package version matches the git tag (`2.1.0`).
- SHA256 verification for Gitleaks, Syft, and Grype release tarballs.
- `common-secrets-sast.yml` on maintainer CI. Token-free `pins` job (CI-024).

### Changed

- GitHub Release and PyPI tag gates accept unprefixed `X.Y.Z` only (no `v`).
- Locust fails the DAST job when `enable_dast` is true (no `|| true`).
- `pip-audit` exit code is captured separately from JSON parse.
- zizmor and mutmut pins are exact (`zizmor==1.30.1`, `mutmut==3.8.0`).
- Dependabot `cooldown.default-days: 7` on every ecosystem. Caller examples pass
  `caller_pat` instead of `secrets: inherit`.

### Fixed

- `dorny/paths-filter` checkout uses `fetch-depth: 0` (2.0.0 hotfix on `main`).
