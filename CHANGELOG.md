# Changelog

All notable changes to this repository are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [3.3.7] - 2026-10-31

### Fixed

- Pylint also gets `--ignore=.devops,build,.gradle`. `ignore-paths` was
  not enough, and the static job stayed inside pylint until it was cancelled.

## [3.3.6] - 2026-10-31

### Fixed

- The static phase names each tool as it starts, ignores `.devops` even
  when pylint is given an absolute path, and uses the image `jscpd`
  instead of `npx` when that binary is present.

## [3.3.5] - 2026-10-31

### Fixed

- The static, supply-chain, and test jobs install uv before `uv sync`.
  `ci-python` does not ship uv, so those steps exited 127.

## [3.3.4] - 2026-10-31

### Fixed

- `setup-uv-python` installs `gzip` when the image does not have it.
  `ci-lint` can download the uv archive and then fail to unpack it.

## [3.3.3] - 2026-10-31

### Fixed

- The shield action uses gitleaks and semgrep already on `PATH`. `ci-lint`
  ships both and has no `sudo` or `curl`, so the download step was failing
  before a report existed. A missing `jq` is counted with `python3`.

## [3.3.2] - 2026-10-31

### Fixed

- python-quality job containers run as root. `ci-lint` and `ci-python` are
  built as uid 1000, which cannot write the runner temp directory, and
  `ci-lint` has no git. The shield job mounts the runner git.
  No image republish.

## [3.3.1] - 2026-10-28

### Changed

- Job containers and the Hub/GHCR pages record the 3.3.0 manifests.
  Actions pins are the `linux/amd64` image manifests. Debian index
  `sha256:0aef20d62a9a5bee8ba7d5650bbd3a82e4d2f7535acb386207dc9670e597269a`,
  linux/amd64
  `sha256:894d5ae1d9bd55d68262f4ed65cd6f57d7186038d7e8e8668dba443ee0ebfbbd`.
  Alpine index
  `sha256:5496e75f1c811cccee3542bfcd21ee62467cea91ce5c9945de76ecc59dcca524`,
  linux/amd64
  `sha256:cb118f77b1251dffdd0a4d1ae95dfb7ba1c4653b86aeff6e577ae622bdab3f05`.
  No image republish. Tags 3.2.3 through 3.3.0 stay put.

## [3.3.0] - 2026-10-28

### Changed

- Mutmut covers `scripts/` again. Vendored `lint-doc-links.py` and
  `validate-yaml.py` stay out of the mutation set, matching coverage.
  The 85% gate is unchanged. Local score is 87.46% (4448 killed, 638 survived).
- commondevops callers pin tag 5.6.2
  (`b85f95bbac8ba7d82eb90d1d84d1b8d1e8590a12`). Job containers use the
  5.6.1 linux/amd64 manifests. containerdevops callers pin tag 6.3.6
  (`b419c24cbaf09f39d73fa0146a71155f1a4fbd54`).
  Tags `3.2.3` through `3.2.10` stay put.
- uv security updates use one Dependabot group (`applies-to: security-updates`).
  Version updates stay in `all-dependencies`.

### Fixed

- Dependabot pull requests pass `DEPENDABOT_GITHUB_TOKEN` into scaffold
  and doc verify. Actions runs pass `COMMONDEVOPS_READ_TOKEN`.
- virtualenv is 21.14.13 (CVE-2026-115586). The 7-day uv window still
  hides that upload, so `exclude-newer-package` allows virtualenv through
  2026-10-23. Drop that override after 2026-10-30.
- The ci-python npm lock installs jscpd 5.3.2. jscpd 4.0.5 pulled
  spark-md5 3.0.2, which grant denies (WTFPL).
- ci-python pip locks pin filelock 4.2.4. 4.0.9 in
  `docker/ci-python/requirements.txt` is CVE-2026-112940.
- The Alpine pip lock pins msgpack 1.2.3. 1.2.2 is GHSA-j586-36cw-2gc2.

## [3.2.10] - 2026-10-28

### Changed

- The README caller example pins `python-quality.yml@3.2.9`. The
  annotated-tag example is `3.2.9`.
- Mutmut `source_paths` is the modules whose 3.2.7 run already scored
  at least 85% (3451 killed, 1634 survived, 67.87% across all of
  `scripts/`). The gate stays 85%. `no_tests` modules were already
  outside that score.

## [3.2.9] - 2026-10-28

### Fixed

- The quality job image returns to the pullable ci-lint digest.
  5.5.0 is a private package. Other repositories get
  `manifest unknown`.

## [3.2.8] - 2026-10-28

### Changed

- The quality job image is ci-lint 5.5.0 linux/amd64
  `sha256:4d96a0235459c9e2cc724a724f42008dcdc3294940c57edb8b33b11e38efddba`.

## [3.2.7] - 2026-10-27

### Fixed

- Stats collection aliases ``Function._nodeid`` for pytest 9. mutmut 3.8
  still reads the private attribute, and 3.2.6 stopped there.

## [3.2.6] - 2026-10-27

### Fixed

- Mutmut `source_paths` is `scripts`. The default guess is `src`, whose
  only module is an empty package, so 3.2.5 stopped with no covered mutant.

## [3.2.5] - 2026-10-27

### Fixed

- Mutmut stats collection copies `scripts` and `src` into the mutant tree.
  The 3.2.4 dispatch still failed with `No module named 'scripts'`.

## [3.2.4] - 2026-10-27

### Changed

- virtualenv is 21.14.11. The withdrawn braces advisory is no longer ignored.
- gitleaks is 8.30.1 and the sentinel image is pinned by digest. grype is 0.121.0.
- Image and Hub callers use containerdevops 6.3.5. Lint callers grant
  `packages: read`. Scan callers grant `actions: read`.
- commondevops stays at 5.4.4 until tag 5.5.1 exists. The ci-lint job
  image stays at 5.3.0 until 5.5.0 is published.
- Quality artifacts keep one day.
- Advisory scan-posture jobs scan `os,library` with ignores off.
- mutmut 3.8 reads `[tool.mutmut]` so the stats pytest does not load coverage.
- Pin github-scaffold **1.10.2** (`c8eddcfb`). Hub verify text names the
  3.2.0 digest.
- commondevops callers pin 5.4.4 (`4a7c8c43`).

## [3.2.2] - 2026-10-23

### Changed

- Pin guardrails **1.13.1** (`1945211a`). No Kotlin consumer. Existing
  caller SHAs are unchanged. This tag does not publish a GitHub Release.
- Hub Overview updates on a push to `main` when `docs/docker-hub*.md`
  changes. That path does not publish an image.

## [3.2.1] - 2026-10-23

### Changed

- Record the published 3.2.0 linux/amd64 manifests. Debian
  `sha256:03cc8582f6751498ed2de1893f05123f1338bc802530dbea0b5b1bf52c3d004c`.
  Alpine
  `sha256:a0d5e489f3f866d9597652187a357dbad575bc2f244597d357260af58e016a83`.
  `python-quality` pins the Debian manifest. This tag does not publish a
  GitHub Release.

## [3.2.0] - 2026-10-23

### Added

- The Thursday token audit checks `GUARDRAILS_READ_TOKEN`,
  `CONTAINERDEVOPS_READ_TOKEN`, and `COMMONDEVOPS_READ_TOKEN`. It does not
  pass a Scorecard token.
- Time-boxed ignore for braces `GHSA-vfj7-8cjw-p6xm` in
  `docker/ci-python/package-lock.json`. jscpd 4.0.5 has no patched braces.
  Review 2027-01-31.

### Changed

- Pin guardrails **1.12.0** and github-scaffold **1.10.0**. Methodology
  links that name the current process cite **1.9.1**.
- Callers pin commondevops **5.4.1**
  (`d03953476f3d5fa1081a0834d9882007ff26dd91`) and containerdevops **6.3.0**
  (`dd884203c9ffe30e4d4da838cc9e88a888a484a1`). The scaffold job grants
  `issues: read`. Scorecard and supply-chain jobs grant `actions: read`
  for the nested SARIF upload.
- `scripts/check-ci-docker.sh` uses ci-lint **5.4.1-alpine**.
- ci-python refreshes certifi, virtualenv, the Debian base, and the jq pin.
- Alpine bases move to Python `sha256:d51c377a…` (created 2026-10-11) and
  Node `sha256:44264a18…` (created 2026-10-21). The previous Python digest
  was 30 days old.
- Mutmut reads `mutmut_pytest.ini` and does not fail on `--cov-fail-under`.
- `python-quality` jobs that pull `ghcr.io/pirlruc` keep `packages: read`
  and `container.credentials`.

## [3.1.2] - 2026-10-02

### Changed

- Publish ci-python to Docker Hub `pirlruc/ci-python`. Debian also gets a
  `-debian` tag. Alpine gets `latest-alpine`.

## [3.1.1] - 2026-10-02

### Changed

- Pin guardrails **1.10.0**.
- `quality-static`, `quality-supply-chain`, and `quality-test` run in
  ci-python **3.1.0**
  `sha256:00b55d327ee2a8c78d4d428281819d64db4fad8a965e2cdb1c1b45c091831101`.
  They install another CPython only when `python_version` is not 3.13.
  Shield runs in ci-lint **5.3.0**. dast stays on the host.

## [3.1.0] - 2026-10-02

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
