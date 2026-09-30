# Changelog

All notable changes to this repository are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed

- `docs/guardrails` tag **1.8.0** (`aa5184ce…`); `.github/scaffold` tag **1.7.0**
  (`e76bb3fd…`). Synced issue templates, Cursor rules, `AGENTS.md`, `SKILLS.md`,
  and `CLAUDE.md`. Decision links cite methodologies **1.6.0** (not a submodule
  in this repo).

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
