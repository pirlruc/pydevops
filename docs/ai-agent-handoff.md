# AI agent handoff — pydevops repository context

This document summarizes **what has been implemented and refined** on the `feature-ci` line of work (and related commits) so another agent can continue without re-deriving context. It merges **recent git history** with **conversation-level detail** where useful.

**Repository purpose:** Reusable GitHub Actions (“Quality-as-a-Service”) and Python scripts for Python CI: static analysis, tests/coverage, SBOM, secret/SAST scans, optional DAST, and quality **gates** evaluated from CI artifacts. See [`README.md`](../README.md) and [`docs/workflows.md`](workflows.md).

---

## Branch / state (as of last update)

- Branch: **`feature-ci`** (often **ahead of `origin/feature-ci` by local commits** — verify with `git status` before assuming parity with remote).
- Recent commit messages (newest first; illustrative snapshot):

  - `fix(scripts): anchor quality output dir after cd; dedupe scorecard truncation helper`
  - `fix(ci): drop redundant grype --fail-on step; rely on quality_gates vuln thresholds`
  - `fix(ci): clarify quality placeholders, pin jscpd via npx, and install syft/grype to /usr/local/bin`
  - `fix(ci): align cyclomatic gate text with enforcement; put ~/.local/bin on PATH for Grype`
  - `fix(ci): stop writing success-shaped artifacts when quality tools are absent`
  - `ci(devops-scripts): pin Python 3.13 via setup-uv-python; tighten scorecard aggregate test`
  - `docs(workflows): align strictness docs; clarify gate labels and trim ci shell helpers`
  - `fix(quality-gates): harden artifact parsers and preserve metric thresholds`
  - …earlier: cyclomatic/MI refactors, dependabot cooldowns, docstrings, zizmor-related workflow fixes, fail-closed artifacts, radon edge cases, initial QaaS pipeline, etc.

Use `git log --oneline` for the authoritative list.

---

## Major themes (cross-cutting)

### 1. Quality gates (`scripts/quality_gates/`)

- Central evaluation: **`python -m scripts.quality_gates`** (reads `QUALITY_OUTPUT_DIR`, `STRICTNESS_LEVEL`), writes **`gates.json`**.
- **Strictness tiers** (`Low` / `Medium` / `High`) map to **`Thresholds`** in [`scripts/quality_gates/config.py`](../scripts/quality_gates/config.py) (coverage, Pylint, Radon CC/MI, duplication, vulns, docstrings, etc.).
- **High** tier additionally requires non-empty artifacts listed in **`HIGH_REQUIRED_FILES`** (fail-closed if tools skipped).
- Parsers were **hardened** to fail closed on malformed JSON (coverage, radon, pip-audit, grype, cloc, gates.json `passed` flag, SARIF tool/driver shapes in `scorecard_summary.py`, etc.).
- **Cyclomatic complexity / maintainability** targets for *this repo’s* `scripts/quality_gates` were brought in line with CI (Radon CC ≤ 5, MI floor, Interrogate docstring coverage).
- **`gates_complexity.py`**: Gate **labels** for cyclomatic / maintainability use **High-specific wording only when `strictness_norm == "High"`** so Low/Medium reports are not misleading.
- **`artifact_rules.py`**: Extracted static JSON shape / path rules for High-tier artifact validation; **`gates_artifacts.py`** consumes them.

### 2. Shell driver `scripts/ci_run_quality.sh`

- Phases: **`QUALITY_PHASES`** = `static` | `security` | `test` | `all`.
- **Output directory**: `cd "$APP_DIR"` first; then **`OUT`** from `QUALITY_OUTPUT_DIR` — **relative paths are resolved under the app root** so `mkdir` and writes align.
- **No fake “success-shaped” outputs** for missing **security** tools (bandit, pip-audit, grype, syft, jscpd when `npx` missing): files are **omitted** instead of empty JSON implying zero issues.
- **Low/Medium** may still use minimal placeholders for some **static** tools (documented in header comment); High omits more aggressively.
- **Ruff**: multiple `--exclude` flags from comma-separated `RUFF_EXCLUDE`.
- **jscpd**: Version pinned by reading **`dependencies` `package.json`** and running **`npx --yes "jscpd@${VER}"`** (deterministic; not only `--prefix` without `node_modules`).

### 3. GitHub Actions / workflows

- **`python-quality.yml`**: Reusable **`workflow_call`** pipeline for **app** repos (checkout DevOps under `.devops`, run composites, evaluate gates).
  - **Removed** a standalone **`grype ... --fail-on high`** step so **vulnerability policy is single-sourced** in **`scripts.quality_gates`** (`gate_vulnerabilities` uses pip-audit + Grype JSON vs `Thresholds`). Documented in [`docs/workflows.md`](workflows.md).
  - **`devops_ref`** (not `pydevops_ref`) matches workflow inputs.
- **`devops-scripts-ci.yml`**: This repo’s script tests; **template-injection** mitigation: step outcomes passed via **`env`** instead of `${{ }}` inside shell strings.
- **`qa-install-toolchain`**: **Syft / Grype** installed to **`/usr/local/bin`** with `sudo tar` (avoids **`GITHUB_PATH`** writes flagged by zizmor; tools still on default PATH).
- **`setup-uv-python`** used where Python **3.13** must exist before **`uv sync`** (matches `pyproject.toml` `requires-python`).

### 4. Dependabot (`.github/dependabot.yml`)

- **`cooldown`** on update entries: **`default-days: 7`** (zizmor policy).
- **`github-actions`** ecosystem: only **`default-days`** (semver cooldown keys are **not** supported for that ecosystem — Dependabot parse error if included).

### 5. Documentation

- [`docs/workflows.md`](workflows.md): `devops_ref`, docstring / interrogate behavior by tier, **no duplicate Grype CLI fail-on** alongside gates.
- Other docs under [`docs/`](README.md) unchanged unless noted in commits.

### 6. Tests / tooling

- **`tests/test_scorecard_summary.py`**: Stronger assertion that **aggregate score line** reflects check mean when aggregateScore conflicts.
- **`tests/test_quality_gates.py`**: PR comment text when **`gates.json`** is invalid JSON updated to match **`pr_comment_markdown.py`** wording.

### 7. Misc scripts

- **`scripts/scorecard_summary.py`**: SARIF **`tool` / `tool.driver`** validation; consolidated **`_truncate`** (removed duplicate `_truncate_cell`).
- **`scripts/pr_comment_markdown.py`**: Invalid JSON message does not claim “missing” when file exists.

---

## Files and areas a future agent should read first

| Area | Path(s) |
| --- | --- |
| Gate thresholds & High artifacts | `scripts/quality_gates/config.py` |
| Gate orchestration | `scripts/quality_gates/evaluation.py`, `engine.py` |
| CI bundle | `scripts/ci_run_quality.sh` |
| Reusable app workflow | `.github/workflows/python-quality.yml` |
| Toolchain composite | `.github/actions/qa-install-toolchain/action.yml` |
| Zizmor policy | `.github/config/zizmor.yml` |
| Caller docs | `docs/workflows.md`, `examples/call-python-quality.yml` |

---

## Conventions worth preserving

- **Focused diffs** — avoid unrelated refactors when fixing CI/gates.
- **Fail-closed** for High-tier required artifacts and security parsers where applicable.
- **Single source of truth** for vuln counts: **`gate_vulnerabilities`**, not an extra Grype `--fail-on` in the workflow.
- **Conventional commits** have been used in this line (e.g. `fix(ci):`, `fix(quality-gates):`, `docs(workflows):`).

---

## Suggested verification for the next agent

1. `git status` / `git log` vs remote **`feature-ci`**.
2. Run **`uv sync`** then **`uv run pytest`** (or CI) on **`scripts/`** and **`tests/`**.
3. Optional: **`uv run --with radon python -m radon cc -s scripts/quality_gates`** if touching gate modules.
4. Scan **`.github/workflows`** and **`action.yml`** files with **actionlint + zizmor** if editing CI (see `reusable-workflows-quality.yml`).

---

## Limitations of this document

- **Other Cursor/AI sessions** are not fully reproduced here; **git history** is the ground truth for authorship and ordering.
- If commits were **rebased** or **squashed**, messages above may not match your clone exactly.

---

*Generated for handoff between AI agents and human maintainers. Update this file when making large architectural or CI contract changes.*
