# AI agent handoff — pydevops

**Repository purpose:** Reusable GitHub Actions (“Quality-as-a-Service”) and Python scripts for
Python CI. See [`README.md`](../README.md) and [`docs/workflows.md`](workflows.md).

## Branch / pins (2026-09-11)

| Item | Value |
|------|-------|
| Branch | `main` (tag **1.1.0**) |
| `docs/guardrails` | tag `1.0.0` → `925b9f32659936382c67850ec125a182261710bf` (**stale vs 1.6.0** — PDO-PIN-001; do not bump in this PR) |
| `.github/scaffold` | `0db5890f808e4a9b9d11eabfc9a95b2b90898fad` |
| commondevops caller pin | **`75d0fafc90fbef7bb118025437502ca2cf42a11e`** (`common-supply-chain.yml`, `common-infra-lint.yml`, `common-scorecard.yml`) — keep a **single** SHA |
| ci-python image | **Not used** (measurement: skip) |
| Latest annotated tag | **`1.1.0`** (README/examples still cite `@v1.2.0` — PDO-WF-001-T2) |

## Delivery status

| Epic | Status |
|------|--------|
| PDO-001 High floors | Done |
| PDO-002 scaffold adoption | Done |
| PDO-003 license/SBOM reusable | Done — lives in [commondevops](https://github.com/pirlruc/commondevops) |
| PDO-004 Dependabot | Done — T1 config on `main`; T2 Insights: no grouped `all-dependencies` PR yet (monthly cadence). Re-check after PDO-DEP-001. |
| PDO-006 CI-025 permissions | Done |
| PDO-005 ai-reviewer | **Done** (Wave E) — findings filed [#111](https://github.com/pirlruc/pydevops/issues/111) closed |
| PDO-WF-001 CI docs / consumer pin | Open ([#138](https://github.com/pirlruc/pydevops/issues/138)) |
| PDO-GATE-001 self-CI floors / Gitleaks pin | Open ([#141](https://github.com/pirlruc/pydevops/issues/141)) |
| PDO-DEP-001 Dependabot private git | **Done** ([#144](https://github.com/pirlruc/pydevops/issues/144)) — `registries: github-private` wired; secret updated 2026-09-12. Confirm Insights after land. |
| PDO-PIN-001 guardrails 1.6.0 | Open ([#146](https://github.com/pirlruc/pydevops/issues/146)) |

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

## Dependency pins (post-#135)

| Package | Version |
|---------|---------|
| ruff | 0.16.6 (`[tool.ruff.lint] select = ["E4", "E7", "E9", "F"]`) |
| pylint | 4.0.8 |
| mypy | 2.3.0 |
| locust | 2.46.5 |
| zizmor | `>=1.30.0,<2` |
| jscpd | 5.2.0 (`--format python`) |
| semgrep | **1.176.1** ([#137](https://github.com/pirlruc/pydevops/pull/137); #132 closed as superseded) |
| mutmut | `>=3.6.0,<4` (#112 closed; already allows 3.7.0) |
| harden-runner | 2.21.1 |
| paths-filter | 4.0.3 |

Keep `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml`,
`.github/dependencies/quality-tools/requirements.txt`, and
`github-actions-pins.json` in lockstep (`uv lock` + export script +
`python3 scripts/github_actions_pins.py`).

## Commands

```bash
uv sync
uv run pytest
uv run mypy src scripts
uv run python scripts/export_quality_tools_requirements.py
python3 scripts/github_actions_pins.py --check
python3 .github/scaffold/scripts/issues-sync.py \
  --repo pirlruc/pydevops --yaml docs/issues.yml --dry-run
```

After Wave E backlog merges, sync with approval (`issues-sync.py` write is publishing).

## Known pitfalls

- Keep a **single** commondevops SHA. Pin `75d0faf…` loads
  `.github/config/zizmor.yml` via `-c` when present.
- CI-024: Scorecard, PyPI publish, and PR comment jobs skip `dependabot[bot]`.
- Private `docs/guardrails` is not checked out in CI with default `GITHUB_TOKEN`; High
  floors fall back to baked-in defaults matching the **pinned** (1.0.0) profile YAML.
- Do not add a `ci-python` job container without new measurement justifying it.
- **Ruff 0.16** default rule set is ~413 rules. Do not drop
  `[tool.ruff.lint] select` until a dedicated cleanup PR enables 0.16 rules
  incrementally.
- **Zizmor 1.30** `self-repository` is ignored in `.github/config/zizmor.yml`
  until actionlint accepts `uses: $/...` (rhysd/actionlint#732 unreleased).
  Do not migrate `uses: ./` to `$/` or `${{ github.repository }}`.
- **Maintainer CI is `workflow_dispatch` only.** Comments that say Dependabot is the
  sole auto trigger are false until a `pull_request` trigger exists (PDO-WF-001).
- **Dependabot private submodule:** `registries: github-private` is wired.
  Confirm Insights / grouped `all-dependencies` after this land (PDO-DEP-001).
  Do not treat an Actions secret as a substitute.
- **Dependabot Insights:** monthly `all-dependencies` group has not produced a
  grouped PR yet; private-clone failure is a likely blocker (PDO-DEP-001).

## Suggested next work

1. Confirm Dependabot Insights / grouped `all-dependencies` after this `dependabot.yml` land.
2. PDO-WF-001 docs/pin examples; PDO-GATE-001 org floors + Gitleaks pin.
3. PDO-PIN-001 guardrails 1.6.0 (dedicated PR).

## Major themes (quality gates)

Central evaluation remains **`python -m scripts.quality_gates`**. High floors load from
`docs/guardrails/python/profile.thresholds.yml` when the submodule is present.

Wave 4: `ci-workflow-lint` / `scheduled-workflow-lint` and Scorecard jobs call
commondevops `common-infra-lint.yml` / `common-scorecard.yml` at **`75d0faf…`**.
`ci-scripts` and `python-quality.yml` stay in-repo.

*Last updated: 2026-09-12 (PDO-DEP-001 registries)*
