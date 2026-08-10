# AI agent handoff — pydevops

**Repository purpose:** Reusable GitHub Actions (“Quality-as-a-Service”) and Python scripts for
Python CI. See [`README.md`](../README.md) and [`docs/workflows.md`](workflows.md).

## Branch / pins (2026-08-10)

| Item | Value |
|------|-------|
| Branch | `feature-dependency-update-policy` |
| `docs/guardrails` | tag `1.0.0` → `925b9f32659936382c67850ec125a182261710bf` |
| `.github/scaffold` | `0db5890f808e4a9b9d11eabfc9a95b2b90898fad` (added; templates synced) |
| commondevops optional caller | `.github/workflows/common-supply-chain.yml` @ **`74695e83a7b79784ee81fd970d9051d8efd711e8`** |
| ci-python image | **Not used** (measurement: skip) |

Retired Cursor rules removed after sync: `handoff-and-commits.mdc`, `radon-complexity.mdc`.

## Delivery status

| Epic | Status |
|------|--------|
| PDO-001 High floors | Done |
| PDO-002 scaffold adoption | Done |
| PDO-003 license/SBOM reusable | Done — lives in [commondevops](https://github.com/pirlruc/commondevops) `common-supply-chain.yml` / `scripts/license_gate.py` (local copy still present for in-repo quality path) |
| PDO-004 Dependabot | Open — multi-ecosystem config rewritten; T2 Insights after default-branch land |
| PDO-005 ai-reviewer | Open |
| PDO-006 CI-025 permissions | Done |

## Dependency bumps applied in-tree (not via closing Dependabot PRs)

| Package | Version |
|---------|---------|
| ruff | 0.16.1 |
| mypy | 2.3.0 (3 type fixes in scorecard/job_summary helpers) |
| pytest | 9.1.1 |
| pydoclint | 0.9.1 |
| pre-commit | 4.6.1 |
| semgrep | 1.172.0 |
| locust | 2.46.3 |
| zizmor | `>=1.28.0,<2` |
| actions/checkout | 7.0.1 |
| ossf/scorecard-action | 2.4.4 |
| pypa/gh-action-pypi-publish | 1.14.2 |

Keep `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml`,
`.github/dependencies/quality-tools/requirements.txt`, and
`github-actions-pins.json` in lockstep (`uv lock` + export script).

## Commands

```bash
uv sync
uv run pytest
uv run mypy src scripts
uv run python scripts/export_quality_tools_requirements.py
bash .github/scaffold/scripts/sync-templates.sh
python3 .github/scaffold/scripts/issues-sync.py \
  --repo pirlruc/pydevops --yaml docs/issues.yml --dry-run
```

## Known pitfalls

- Replace **`74695e83a7b79784ee81fd970d9051d8efd711e8`** after commondevops's first push if using the
  optional `common-supply-chain.yml` caller.
- CI-024: Scorecard, PyPI publish, and PR comment jobs skip `dependabot[bot]`.
- Private `docs/guardrails` is not checked out in CI with default `GITHUB_TOKEN`; High
  floors fall back to baked-in defaults matching the profile YAML.
- Do not add a `ci-python` job container without new measurement justifying it.

## Suggested next work

1. First commondevops commit → replace placeholder pin on optional supply-chain caller.
2. Merge branch; confirm Dependabot Insights grouping (PDO-004-T2).
3. PDO-005 ai-reviewer pass into `docs/issues.yml`.

## Major themes (quality gates)

Central evaluation remains **`python -m scripts.quality_gates`**. High floors load from
`docs/guardrails/python/profile.thresholds.yml` when the submodule is present. See prior
handoff history in git for gate internals (mypy reports, Radon, Bandit, etc.).

*Last updated: 2026-08-10*
