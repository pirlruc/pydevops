# AI agent handoff — pydevops

**Repository purpose:** Reusable GitHub Actions (“Quality-as-a-Service”) and Python scripts for
Python CI. See [`README.md`](../README.md) and [`docs/workflows.md`](workflows.md).

## Branch / pins (2026-10-23)

| Item | Value |
|------|-------|
| Branch | `main` at `9c52f4aa`. **3.2.3** is an annotated tag on that commit and has no GitHub Release. There is no 3.3.0. The changelog heading stays `[Unreleased]`. Do not move `3.2.3`. The repo is public; the owner can set it private. |
| `docs/guardrails` | tag **1.13.1** → `1945211ac851c3c0f83694bd4ea53571fdced4ab` |
| `.github/scaffold` | tag **1.10.2** → `c8eddcfb2c8a808981e640fa9739cb4fcefa991e` |
| methodologies (links only; not a submodule) | tag **1.9.1** |
| commondevops caller pin | tag **5.4.1** → `d03953476f3d5fa1081a0834d9882007ff26dd91` |
| containerdevops caller pin | tag **6.3.0** → `dd884203c9ffe30e4d4da838cc9e88a888a484a1` |
| ci-python (debian, unsuffixed) | `3.2.0` linux/amd64 `sha256:03cc8582f6751498ed2de1893f05123f1338bc802530dbea0b5b1bf52c3d004c` (tag index `sha256:ee88446f…`) |
| ci-python (alpine) | `3.2.0-alpine` linux/amd64 `sha256:a0d5e489f3f866d9597652187a357dbad575bc2f244597d357260af58e016a83` (tag index `sha256:879d8309…`) |
| Latest annotated tag | **`3.2.3`** on `9c52f4aa`. No GitHub Release |
| Package version | **3.0.1** (`pyproject.toml`) |

## Delivery status

| Epic | Status |
|------|--------|
| PDO-001 High floors | Done |
| PDO-002 scaffold adoption | Done |
| PDO-003 license/SBOM reusable | Done — lives in [commondevops](https://github.com/pirlruc/commondevops) |
| PDO-004 Dependabot | Done — T1 config on `main`; T2 Insights 2026-09-13: grouped [`#152`](https://github.com/pirlruc/pydevops/pull/152) (`all-dependencies`, 6 ecosystems). github-actions clones `pirlruc/pydevops` with HTTP 200 after the PAT allowlist included this repo. |
| PDO-006 CI-025 permissions | Done |
| PDO-005 ai-reviewer | **Done** (Wave E) — findings filed [#111](https://github.com/pirlruc/pydevops/issues/111) closed |
| PDO-WF-001 CI docs / consumer pin | Done (this wave) |
| PDO-GATE-001 self-CI floors / Gitleaks pin | Done (this wave) |
| PDO-DEP-001 Dependabot private git | **Done** ([#144](https://github.com/pirlruc/pydevops/issues/144)) — `registries: github-private` on github-actions; PAT includes pydevops (self-clone HTTP 200, 2026-09-13). |
| PDO-PIN-001 guardrails 1.6.0 | Done (this wave) |
| PDO-IMG-001 ci-python | Done — Hub and GHCR 3.1.2 |

## Wave E (2026-09-11)

| Item | Outcome |
|------|---------|
| PR [#132](https://github.com/pirlruc/pydevops/pull/132) semgrep → 1.176.1 | **Closed as superseded.** Clean bump merged as [#137](https://github.com/pirlruc/pydevops/pull/137). |
| PR [#112](https://github.com/pirlruc/pydevops/pull/112) mutmut `>=3.7.0,<4` | **Closed.** Existing `>=3.6.0,<4` already resolves 3.7.0. `mutmut_score_gate.py` is version-agnostic (`killed`/`survived` ints vs `MUTMUT_MIN_SCORE`); 3.7.0 changelog does not change `export-cicd-stats`. |
| PDO-005-T1 | Review of workflows, scripts, composites, Dependabot, docs. Material findings: **PDO-WF-001** (2 tasks), **PDO-GATE-001** (2 tasks). Within budget (2 epics / 6 tasks). Not a no-op. |

## PDO-005-T1 surfaces (what was judged)

- `.github/workflows/` — dispatch-only maintainer CI vs docs claiming PR/push/schedule; in-repo `license_gate.py` still used by `python-quality.yml` (PDO-003 reusable path is optional `common-supply-chain.yml`, not a duplicate bug).
- `scripts/` — `quality_gates` High loads org YAML; `mutmut_score_gate.py` does not sniff mutmut version; `org_thresholds.py` fallbacks match the 1.0.0 profile.
- `.github/actions/qa-secrets-sast` — Gitleaks `8.21.2` hardcoded curl (SC-DEP-001 gap).
- `.github/dependabot.yml` — monthly multi-ecosystem shape OK; `registries:` commented (PDO-DEP-001). Docs still say quarterly.
- Consumer examples — `@v1.2.0` does not exist.

## Dependency pins (post-2.1.0)

| Package | Version |
|---------|---------|
| ruff | 0.16.7 (`[tool.ruff.lint] select = ["E4", "E7", "E9", "F"]`) |
| pylint | 4.0.8 |
| mypy | 2.3.1 |
| locust | 2.46.5 |
| zizmor | `==1.30.1` |
| jscpd | 5.3.2 (`--format python`, JSON `statistics.total.percentage`) |
| semgrep | **1.177.0** (Dependabot #152 folded into the 2.0.0 handoff) |
| mutmut | `==3.8.0` |
| harden-runner | 2.21.1 |
| paths-filter | 4.0.3 |
| gitleaks | 8.21.2 + `linux-amd64.sha256` |

Keep `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml`,
`.github/dependencies/quality-tools/requirements.txt`, and
`github-actions-pins.json` in lockstep (`uv lock` + export script +
`python3 scripts/github_actions_pins.py`).

## Commands

```bash
uv sync
uv run pytest
uv run mypy src scripts
sh scripts/check-ci-local.sh
python3 scripts/github_actions_pins.py --check
python3 .github/scaffold/scripts/issues-sync.py \
  --repo pirlruc/pydevops --yaml docs/issues.yml --validate-only
```

After Wave E backlog merges, sync with approval (`issues-sync.py` write is publishing).

## Known pitfalls

- Callers pin commondevops **5.4.1**. The scaffold job needs `issues: read`. Scorecard and supply-chain jobs need `actions: read` for the nested SARIF upload. Omitting either is a workflow `startup_failure` with no jobs.
- CI-024: Scorecard, PyPI publish, secrets-sast, and PR comment jobs skip
  `dependabot[bot]`. Token-free `pins` still runs.
- Scorecard is **advisory** while the repo is private and `SCORECARD_TOKEN` is
  unset. `GITHUB_TOKEN` cannot ListCommits; blocking `true` fails DevOps CI on
  `main` once paths-filter selects the Scorecard job (docs/` .github/` changes).
- Private `docs/guardrails` is not initialized in default checkout; High floors
  load from vendored `scripts/python.profile.thresholds.yml` (fail closed on
  missing keys). Missing checkout without a vendored copy warns loudly and uses
  baked-in High floors.
- Do not add a `ci-python` job container without new measurement justifying it.
- **Ruff 0.16** default rule set is ~413 rules. Do not drop
  `[tool.ruff.lint] select` until a dedicated cleanup PR enables 0.16 rules
  incrementally.
- **Zizmor 1.30** `self-repository` is ignored in `.github/config/zizmor.yml`
  until actionlint accepts `uses: $/...` (rhysd/actionlint#732 unreleased).
  Do not migrate `uses: ./` to `$/` or `${{ github.repository }}`.
- Maintainer CI is **push + pull_request + workflow_dispatch** on `devops-ci.yml`
  and Thursday cron on `devops-scheduled.yml` (PDO-WF-001).
- Self-CI Radon CC cap is **5**, stricter than High floor 8; no deviation.
- **Dependabot private git:** `registries: github-private` is on
  `github-actions`, `uv`, `npm`, and `pre-commit`. The updater clones with
  `--recurse-submodules`. Do not attach it to pip. After the registry was
  added, the jscpd job cloned the private submodules and still got HTTP 400
  `invalid or unauthorized changes` opening the 5.2.0 → 5.3.2 pull request.
  That pin is now 5.3.2 in-tree. 5.3.3 stays inside the 7-day cooldown.
- Do not re-add Dependabot `docker` for `.github/dependencies/gitleaks` — the
  real pin is `version.txt` + checksum; docker 400'd.
- `dorny/paths-filter` on `devops-ci.yml` needs `fetch-depth: 0` (shallow checkout
  plus `persist-credentials: false` cannot fetch `github.event.before`).
- Git tags are unprefixed SemVer (`2.1.1`). Publish/release gates reject `v2.1.1`.
- Do not set `uv` `exclude-newer = "7 days"` until pinned wheels (ruff 0.16.7)
  are older than seven days; use `# nosemgrep` on `[tool.uv]` instead.
- `.semgrepignore` excludes submodule trees so `common-secrets-sast` `--config auto`
  does not flag companion-repo Dependabot.

## Suggested next work

1. **3.2.3** is already tagged. Do not cut 3.3.0 or a GitHub Release for it. Image contents did not change. Hub pages stay on 3.2.0.
2. braces `GHSA-vfj7-8cjw-p6xm` is ignored through 2027-01-31. There is no
   upstream fix in jscpd 4.0.5 / braces 3.0.3.
3. Add `SCORECARD_TOKEN` (classic PAT, `repo` scope) to enable blocking private Scorecard.
   Leave it unset until then.
4. PyPI publish stays `workflow_dispatch`.
5. PDO-PRIV-001 is done. The four `ghcr.io/pirlruc` jobs in `python-quality.yml`
   set `packages: read` and `container.credentials`.
6. Hub Overview for `pirlruc/ci-python` is `workflow_dispatch` on
   `.github/workflows/hub-description.yml`. It calls
   [container-hub-description](https://github.com/pirlruc/containerdevops/blob/6.3.0/.github/workflows/container-hub-description.yml)
   and does not republish the image.

## Major themes (quality gates)

Central evaluation remains **`python -m scripts.quality_gates`**. High floors load from
`docs/guardrails/python/profile.thresholds.yml` or vendored `scripts/python.profile.thresholds.yml`.

Wave 5: commondevops **5.1.2** (`b3c462be…`). `ci-scripts` and `python-quality.yml` stay in-repo.

## Recent history

- 2026-10-27: **3.2.4** on `7732db2` is scanners only. **3.2.5** copied `scripts` into the mutant tree. **3.2.6** sets `source_paths` to `scripts` (the default guess is the empty `src` package). **3.2.7** aliases `Function._nodeid` because mutmut 3.8.0 still reads it and pytest 9 removed it. No image republish. The ci-lint job image stays at the 5.3.0 digest until the 5.5.0 amd64 digest is written back. Do not move `3.2.3` through `3.2.7`.
- 2026-10-24: **3.2.3** on `9c52f4aa` (PR 218). Mutmut 3.8 uses a real `[tool.mutmut]` list. No GitHub Release. No 3.3.0. `ci-python` was not republished. Do not move `3.2.3`.

- 2026-10-02: measured apt+syft+grype at 12s, excluding Node, uv, and twelve
  quality CLIs installed three times per `python-quality` run. Added
  `ci-python` Debian and Alpine. Published to GHCR at 3.1.0. Docker Hub
  has no `ci-python` repository yet.
- 2026-09-30: guardrails **1.8.0** / scaffold **1.7.0**. Methodology decision
  links cite **1.6.0** (no methodologies submodule). Synced scaffold templates.
  Token-free `pins` still runs on Dependabot pull requests (CI-024).
  `github-private` now covers `uv`, `npm`, and `pre-commit` too.

- 2026-10-02: PDO-IMG-001 records the 12s measurement. Hub and GHCR docs
  and a Dependabot docker entry are in. `python-quality` has timeouts and
  concurrency. Scheduled secrets-sast and supply-chain are wired. zizmor
  is hash-pin. harden-runner stays in audit mode: no private-repo run
  showed it blocking egress, so no allowlist was added. Quality jobs use
  the GHCR image from 3.1.1. dast stays on the host.

- 2026-10-23: **3.2.2** — guardrails 1.13.1. Hub Overview push when `docs/docker-hub.md` changes. Tag only. No GitHub Release.
- 2026-10-23: Hub Overview dispatch for `ci-python`. It does not republish the image.
- 2026-10-23: scheduled token audit pins commondevops **5.4.1** and checks the
  three read PATs this repo has. It does not pass `SCORECARD_TOKEN`.
  Confirm those expiries before Thursday 06:17 UTC.
- 2026-10-23: PDO-PRIV-001 is done. The credential blocks were already on
  the four job containers. The manifest close does not change the workflows.
- 2026-10-23: **3.2.0** pins guardrails 1.12.0, scaffold 1.10.0,
  commondevops 5.4.1, and containerdevops 6.3.0. braces GHSA-vfj7-8cjw-p6xm
  is ignored until 2027-01-31.

*Last updated: 2026-10-27 (annotated tag 3.2.4, no image republish)*
