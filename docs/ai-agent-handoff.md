# AI agent handoff — pydevops

**Repository purpose:** Reusable GitHub Actions (“Quality-as-a-Service”) and Python scripts for
Python CI. See [`README.md`](../README.md) and [`docs/workflows.md`](workflows.md).

## Branch / pins (2026-09-11)

| Item | Value |
|------|-------|
| Branch | `feature-post-102-bumps` (from `origin/main` after #102) |
| `docs/guardrails` | tag `1.0.0` → `925b9f32659936382c67850ec125a182261710bf` |
| `.github/scaffold` | `0db5890f808e4a9b9d11eabfc9a95b2b90898fad` |
| commondevops caller pin | **`75d0fafc90fbef7bb118025437502ca2cf42a11e`** (`common-supply-chain.yml`, `common-infra-lint.yml`, `common-scorecard.yml`) — keep a **single** SHA |
| ci-python image | **Not used** (measurement: skip) |

## Delivery status

| Epic | Status |
|------|--------|
| PDO-001 High floors | Done |
| PDO-002 scaffold adoption | Done |
| PDO-003 license/SBOM reusable | Done — lives in [commondevops](https://github.com/pirlruc/commondevops) |
| PDO-004 Dependabot | Done — T1 config on `main`; T2 Insights: no grouped `all-dependencies` PR yet (monthly cadence). Re-check next cycle. |
| PDO-005 ai-reviewer | Open |
| PDO-006 CI-025 permissions | Done |

## Dependency pins (post-#102 follow-up)

| Package | Version |
|---------|---------|
| ruff | 0.16.6 (`[tool.ruff.lint] select = ["E4", "E7", "E9", "F"]`) |
| pylint | 4.0.8 |
| mypy | 2.3.0 |
| locust | 2.46.5 |
| zizmor | `>=1.30.0,<2` |
| jscpd | 5.2.0 (`--format python`) |
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

## Known pitfalls

- Keep a **single** commondevops SHA. Pin `75d0faf…` loads
  `.github/config/zizmor.yml` via `-c` when present.
- CI-024: Scorecard, PyPI publish, and PR comment jobs skip `dependabot[bot]`.
- Private `docs/guardrails` is not checked out in CI with default `GITHUB_TOKEN`; High
  floors fall back to baked-in defaults matching the profile YAML.
- Do not add a `ci-python` job container without new measurement justifying it.
- **Ruff 0.16** default rule set is ~413 rules. Do not drop
  `[tool.ruff.lint] select` until a dedicated cleanup PR enables 0.16 rules
  incrementally.
- **Zizmor 1.30** `self-repository` is ignored in `.github/config/zizmor.yml`
  until actionlint accepts `uses: $/...` (rhysd/actionlint#732 unreleased).
  Do not migrate `uses: ./` to `$/` or `${{ github.repository }}`.
- README cites caller pin `@v1.2.0` but this repo had **no tags** until `1.0.0`.
  Cut `1.0.0` after this branch merges.
- **Dependabot Insights:** monthly `all-dependencies` group has not produced a
  grouped PR yet (cadence). PDO-004-T2 records that limitation.

## Suggested next work

1. After merge: close leftover Dependabot PRs that this branch supersedes;
   cut annotated tag `1.0.0`.
2. PDO-005 ai-reviewer pass into `docs/issues.yml`.
3. Re-check Dependabot Insights next monthly cycle.
4. `mutmut` (#112) and leftover `semgrep` (#132) can land independently.

## Major themes (quality gates)

Central evaluation remains **`python -m scripts.quality_gates`**. High floors load from
`docs/guardrails/python/profile.thresholds.yml` when the submodule is present.

Wave 4: `ci-workflow-lint` / `scheduled-workflow-lint` and Scorecard jobs call
commondevops `common-infra-lint.yml` / `common-scorecard.yml` at **`75d0faf…`**.
`ci-scripts` and `python-quality.yml` stay in-repo.

*Last updated: 2026-09-11*
