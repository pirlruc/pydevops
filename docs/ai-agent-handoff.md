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
- **Strictness tiers** (`Low` / `Medium` / `High`) map to **`Thresholds`** in [`scripts/quality_gates/config.py`](../scripts/quality_gates/config.py) (coverage, Pylint, Radon CC/MI, duplication, vulns, **Bandit finding counts**, docstrings, etc.).
- **High** tier additionally requires non-empty artifacts listed in **`HIGH_REQUIRED_FILES`** (fail-closed if tools skipped).
- Parsers were **hardened** to fail closed on malformed JSON (coverage, radon, pip-audit, grype, cloc, SARIF tool/driver shapes in `scorecard_summary.py`, etc.).
- **`scripts/quality_gates/jsonutil.py` — `gates_rows_and_passed()`**: If the root is a dict and `rows` is a list, **`passed` defaults to `False` when the key is missing** (legacy / partial `gates.json` must not summarize as PASSED). Used by **`pr_comment_markdown.py`** and **`consolidate_artifacts.py`** (alongside invalid-JSON handling there).
- **Vulnerabilities**: `pip_audit_vulns()` / `grype_severities()` return **`None`** when the report is missing, invalid JSON, or wrong top-level type; **`gate_vulnerabilities`** adds explicit failing rows (report shape / missing file) instead of treating as zero findings. **`HIGH_REQUIRED_FILES`** includes **`pip_audit.json`** and **`grype.json`** so High tier cannot skip those scans silently.
- **Pytest**: **`pytest_exit_code.txt`** is written by **`ci_run_quality.sh`**; **`gate_pytest_exit`** fails on non-zero (and High requires the artifact).
- **Radon CC**: **`radon_cc_max`** must track a **`found`** flag for valid complexity values — do not use `max_cc if max_cc else None` (**`0.0`** is a valid maximum).
- **jscpd**: **`jscpd_duplication_pct()`** parses `percentage` safely (type / string); **`None`** on bad values so the duplication gate fails in a controlled way.
- **Cyclomatic complexity / maintainability** targets for *this repo’s* `scripts/quality_gates` were brought in line with CI (Radon CC ≤ 5, MI floor, Interrogate docstring coverage).
- **`gates_complexity.py`**: Gate **labels** for cyclomatic / maintainability use **High-specific wording only when `strictness_norm == "High"`** so Low/Medium reports are not misleading.
- **`artifact_rules.py`**: Extracted static JSON shape / path rules for High-tier artifact validation; **`gates_artifacts.py`** consumes them.

### 2. Shell driver `scripts/ci_run_quality.sh`

- Phases: **`QUALITY_PHASES`** = `static` | `security` | `test` | `all`.
- **Output directory**: `cd "$APP_DIR"` first; then **`OUT`** from `QUALITY_OUTPUT_DIR` — **relative paths are resolved under the app root** so `mkdir` and writes align.
- **No fake “success-shaped” outputs** for missing **security** tools (bandit, pip-audit, grype, syft, jscpd when `npx` missing): files are **omitted** instead of empty JSON implying zero issues.
- **Syft**: If the **`syft`** CLI is absent, **`sbom-cyclonedx.json`** / **`sbom-spdx.json`** are **removed** (not `{}`), consistent with other security fallbacks. Grype only runs when **`sbom-cyclonedx.json`** exists.
- **Low/Medium** may still use minimal placeholders for some **static** tools (documented in header comment); High omits more aggressively.
- **Ruff**: multiple `--exclude` flags from comma-separated `RUFF_EXCLUDE`.
- **jscpd**: Pinned version read from **`.github/dependencies/jscpd/package.json`** (semver extracted for **`npx --yes "jscpd@${VER}"`**); falls back to **`jscpd@4.0.5`** if missing.

### 3. GitHub Actions / workflows

- **`python-quality.yml`**: Reusable **`workflow_call`** pipeline for **app** repos (checkout DevOps under `.devops`, run composites, evaluate gates).
  - **Removed** a standalone **`grype ... --fail-on high`** step so **vulnerability policy is single-sourced** in **`scripts.quality_gates`** (`gate_vulnerabilities` uses pip-audit + Grype JSON vs `Thresholds`). Documented in [`docs/workflows.md`](workflows.md).
  - **`devops_ref`** (not `pydevops_ref`) matches workflow inputs.
  - **`workflow_dispatch` DevOps checkout**: When **`devops_repository`** / **`devops_ref`** are **non-empty**, they are used for the `.devops` checkout so manual runs can test against a **pinned tag or SHA** of this or another trusted repo. If left **empty** (defaults), checkout falls back to **`github.repository`** / **`github.ref_name`** (current repo and branch/tag). **`workflow_call`** continues to require **`devops_repository`** / **`devops_ref`** from the caller.
  - **`workflow_dispatch`** is limited to **10 inputs** on GitHub. Inputs that exist only under **`workflow_call`** (e.g. **`app_install_command`**) may be omitted from dispatch; the composite can still use **`${{ inputs.app_install_command || '' }}`** — missing keys evaluate to empty. **Do not** “fix” this by reading **`github.event.inputs.app_install_command`** unless that input is declared on dispatch: **actionlint** rejects undefined properties on the typed `github.event.inputs` object.
  - **`docstring_format: Pep257`**: Ruff uses **`convention = "pep257"`**; **pydoclint** maps to **`--style=sphinx`** (pydoclint has no pep257 style — avoids conflicting with Google-style pydoclint vs Ruff).
  - Inputs **`devops_repository`** / **`devops_ref`**: documented as **supply-chain sensitive** (trusted tag/SHA); caller-controlled checkout runs composites with job token — see workflow descriptions and [`docs/workflows.md`](workflows.md).
- **`devops-scripts-ci.yml`**: This repo’s script tests; **template-injection** mitigation: step outcomes passed via **`env`** instead of `${{ }}` inside shell strings. Quality steps use **`continue-on-error: true`** so **all checks run**, then a **final** step fails the job if any outcome was not `success`. **Interrogate** targets **`scripts`** with **`--fail-under 95`** to match stated docstring coverage policy.
- **`reusable-workflows-quality.yml` — zizmor**: Build a bash array of paths that **exist** (e.g. **`.github/workflows`**, **`.github/actions`**, **`.github/dependabot.yml`**, **`examples`**), then run **`zizmor`** **once** with that list (or skip if empty). Avoid passing only a directory that yields **no auditable files** — zizmor exits with **“no inputs collected”** (exit code 3).
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
- **`tests/test_pr_comment.py`** / **`tests/test_consolidate.py`**: Cover **`gates.json`** with **omitted `passed`** (must surface as **FAILED** in comment / consolidated report).
- **`tests/test_readers_cloc_docs.py`**: **pydoclint** issue counting matches flake8-style violation lines only (not “0 errors” summaries).
- **`tests/test_license_gate_extra.py`**: **`LICENSE_DENY_LIST`** entries must be **JSON strings**; **`null`** / numbers are skipped.

### 7. Misc scripts

- **`scripts/scorecard_summary.py`**: SARIF **`tool` / `tool.driver`** validation; consolidated **`_truncate`** (removed duplicate `_truncate_cell`).
- **`scripts/pr_comment_markdown.py`**: Invalid JSON message does not claim “missing” when file exists. **GFM gate tables** sanitize cell text via [`scripts/mdutil.py`](../scripts/mdutil.py) (`sanitize_markdown_table_cell`: newlines/tabs → spaces, `|` → U+00A6 broken bar, truncation) so tool messages cannot break columns.
- **`scripts/consolidate_artifacts.py`**: Uses the same cell sanitization for the consolidated **quality_report.md** gate table. If **`gates.json`** is present but **not valid JSON** (e.g. truncated write), the consolidated summary treats the run as **FAILED**, not PASSED, with an explanatory note in the report body.
- **Bandit gate**: [`scripts/quality_gates/gates_security.py`](../scripts/quality_gates/gates_security.py) `gate_bandit` uses [`readers_bandit.py`](../scripts/quality_gates/readers_bandit.py) to count `bandit.json` `results` vs **`bandit_findings_max`** per tier (High: 0; Medium: 3; Low: 15). Wired in [`evaluation.py`](../scripts/quality_gates/evaluation.py) `collect_gate_results` so SAST findings affect **`passed`** like other gates. The gate row **`gate`** label is always **`Bandit (SAST)`**; parse/shape problems are expressed in **`actual`** / **`required`**, not a second label variant.
- **`scripts/license_gate.py`**: **`LICENSE_DENY_LIST`** is a JSON array of **strings** only; non-string elements are **ignored** (avoids **`str(null)` → `"none"`-style accidental matches).
- **`scripts/quality_gates/readers_cloc_docs.py` — `pydoclint_issue_count`**: Counts lines matching pydoclint’s flake8-style **`path:line:col: ERROR`** pattern, not any line containing the word “error” (avoids false positives from “0 errors” / “No errors found”).

---

## Files and areas a future agent should read first

| Area | Path(s) |
| --- | --- |
| Gate thresholds & High artifacts | `scripts/quality_gates/config.py` |
| `gates.json` normalization | `scripts/quality_gates/jsonutil.py` |
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
- **Human-facing `gates.json`**: Prefer explicit **`passed: true|false`**. Parsers that consume **`gates_rows_and_passed()`** treat a **missing `passed`** as **failure**.
- **Single source of truth** for vuln counts: **`gate_vulnerabilities`**, not an extra Grype `--fail-on` in the workflow.
- **Bandit policy** is tiered via **`bandit_findings_max`** only (count of `results[]`); adjust thresholds in **`config.py`** if product policy changes.
- **Conventional commits** have been used in this line (e.g. `fix(ci):`, `fix(quality-gates):`, `docs(workflows):`).
- **Cursor agents**: see [`.cursor/rules/handoff-and-commits.mdc`](../.cursor/rules/handoff-and-commits.mdc) — refresh **`docs/ai-agent-handoff.md`** on substantive changes and end with a **conventional commit** line for the user.

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
