# AI agent handoff — pydevops

**Repository purpose:** Reusable GitHub Actions (“Quality-as-a-Service”) and Python scripts for
Python CI. See [`README.md`](../README.md) and [`docs/workflows.md`](workflows.md).

## Branch / pins (2026-09-30)

| Item | Value |
|------|-------|
| Branch | `main` (latest tag **2.1.1**) |
| `docs/guardrails` | tag **1.8.0** → `aa5184ce…` |
| `.github/scaffold` | tag **1.7.0** → `e76bb3fd…` |
| methodologies (links only; not a submodule) | tag **1.6.0** |
| commondevops caller pin | **5.1.2** `b3c462bed0de4f6475e6be7875c4ababd831acc6` (single SHA) |
| ci-python image | **Not used** |
| Latest annotated tag | **`2.1.1`** |
| Package version | **2.1.1** (`pyproject.toml` / `__version__`, unprefixed git tags) |

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
| jscpd | 5.2.0 (`--format python`) |
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

- Keep a **single** commondevops SHA (`b3c462be…` / tag 5.1.2).
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
  `--recurse-submodules`; without the registry a real update fails as
  unauthorized changes (jscpd job on 2026-09-30). Do not attach it to pip.
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

1. After tag **2.1.1**, dispatch `publish-pypi.yml` with `tag=2.1.1` (skip 2.1.0).
2. Add `SCORECARD_TOKEN` (classic PAT, `repo` scope) to enable blocking private Scorecard.
3. PyPI publish stays `workflow_dispatch`.

## Major themes (quality gates)

Central evaluation remains **`python -m scripts.quality_gates`**. High floors load from
`docs/guardrails/python/profile.thresholds.yml` or vendored `scripts/python.profile.thresholds.yml`.

Wave 5: commondevops **5.1.2** (`b3c462be…`). `ci-scripts` and `python-quality.yml` stay in-repo.

## Recent history

- 2026-09-30: guardrails **1.8.0** / scaffold **1.7.0**. Methodology decision
  links cite **1.6.0** (no methodologies submodule). Synced scaffold templates.
  Token-free `pins` still runs on Dependabot pull requests (CI-024).
  `github-private` now covers `uv`, `npm`, and `pre-commit` too.

*Last updated: 2026-09-30*
