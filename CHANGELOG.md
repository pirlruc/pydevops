# Changelog

All notable changes to this repository are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

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
- Dependabot docker for the Gitleaks sentinel Dockerfile is omitted (install is
  `version.txt` + checksummed tarball).

### Fixed

- `dorny/paths-filter` checkout uses `fetch-depth: 0` (2.0.0 hotfix on `main`).
