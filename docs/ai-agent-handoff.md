# AI agent handoff — pydevops repository context

This document summarizes **what has been implemented and refined** on the `feature-ci` line of work (and related commits) so another agent can continue without re-deriving context. It merges **recent git history** with **conversation-level detail** where useful.

**Repository purpose:** Reusable GitHub Actions (“Quality-as-a-Service”) and Python scripts for Python CI: static analysis, tests/coverage, SBOM, secret/SAST scans, optional DAST, and quality **gates** evaluated from CI artifacts. See [`README.md`](../README.md) and [`docs/workflows.md`](workflows.md).

---

## Branch / state (as of last update)

- Branch: **`feature-restructure`** (verify with `git status` / remote before assuming parity).
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
- **High** tier additionally requires artifacts listed in **`HIGH_REQUIRED_FILES`** (fail-closed if tools skipped); includes **`pydoclint.txt`** so a missing pydoclint run cannot be confused with zero findings. **`pydoclint.txt`** may be **empty** when there are zero violations (still counts as present).
- Parsers were **hardened** to fail closed on malformed JSON (coverage, radon, pip-audit, grype, cloc, SARIF tool/driver shapes in `scorecard_summary.py`, etc.).
- **`scripts/quality_gates/jsonutil.py` — `gates_rows_and_passed()`**: If the root is a dict and `rows` is a list, **`passed` defaults to `False` when the key is missing** (legacy / partial `gates.json` must not summarize as PASSED). Used by **`pr_comment_markdown.py`** and **`consolidate_artifacts.py`** (alongside invalid-JSON handling there).
- **Vulnerabilities**: `pip_audit_vulns()` / `grype_severities()` return **`None`** when the report is missing, invalid JSON, or wrong top-level type; **`gate_vulnerabilities`** adds explicit failing rows (report shape / missing file) instead of treating as zero findings. **`HIGH_REQUIRED_FILES`** includes **`pip_audit.json`** and **`grype.json`** so High tier cannot skip those scans silently. **`readers_grype_gitleaks.count_one_grype_match`** requires **`vulnerability`** to be a **dict** before reading **`severity`** (non-dict values are ignored so malformed Grype rows do not raise).
- **Pytest**: **`pytest_exit_code.txt`** is written by **`ci_run_quality.sh`**; **`gate_pytest_exit`** fails on non-zero (and High requires the artifact).
- **Radon CC**: **`radon_cc_max`** must track a **`found`** flag for valid complexity values — do not use `max_cc if max_cc else None` (**`0.0`** is a valid maximum).
- **jscpd**: **`jscpd_duplication_pct()`** parses `percentage` safely (type / string); **`None`** on bad values so the duplication gate fails in a controlled way.
- **Cyclomatic complexity / maintainability** targets for *this repo’s* `scripts/quality_gates` were brought in line with CI (Radon CC ≤ 5, MI floor, Interrogate docstring coverage).
- **`gates_complexity.py`**: Gate **labels** for cyclomatic / maintainability use **High-specific wording only when `strictness_norm == "High"`** so Low/Medium reports are not misleading.
- **`artifact_rules.py`**: Extracted static JSON shape / path rules for High-tier artifact validation; **`gates_artifacts.py`** consumes them.
- **Semgrep (High only)**: **`gate_semgrep`** + **`readers_semgrep.semgrep_sarif_error_warning_counts`** enforce **`semgrep.sarif`**: **0** SARIF **`level: error`** results, **≤ 5** **`level: warning`** (note-level ignored). **`HIGH_REQUIRED_FILES`** includes **`semgrep.sarif`**. Shield job runs **`python -m scripts.quality_gates --semgrep-shield-only`** after **`qa-secrets-sast`** (Low/Medium: no-op pass). **`qa-secrets-sast`**: Semgrep scan uses **`continue-on-error: true`**; the blocking second **`--error`** scan was removed in favor of gates.

### 2. Shell driver `scripts/ci_run_quality.sh`

- Phases: **`QUALITY_PHASES`** = `static` | `security` | `test` | `all`.
- **Output directory**: `cd "$APP_DIR"` first; then **`OUT`** from `QUALITY_OUTPUT_DIR` — **relative paths are resolved under the app root** so `mkdir` and writes align.
- **No fake “success-shaped” outputs** for missing **security** tools (bandit, pip-audit, grype, syft, jscpd when `npx` missing): files are **omitted** instead of empty JSON implying zero issues. **High** also **omits `pydoclint.txt`** when the **pydoclint** CLI is missing (Low/Medium still write the placeholder line that gates ignore for “not installed”).
- **Syft**: If the **`syft`** CLI is absent, **`sbom-cyclonedx.json`** / **`sbom-spdx.json`** are **removed** (not `{}`), consistent with other security fallbacks. Grype only runs when **`sbom-cyclonedx.json`** exists.
- **Low/Medium** may still use minimal placeholders for some **static** tools (documented in header comment); High omits more aggressively.
- **Ruff**: multiple `--exclude` flags from comma-separated `RUFF_EXCLUDE`.
- **jscpd**: Pinned version read from **`.github/dependencies/jscpd/package.json`** (semver extracted for **`npx --yes "jscpd@${VER}"`**); falls back to **`jscpd@4.0.5`** if missing.
- **Ruff object format**: **`ruff_messages_in_files()`** in [`readers_ruff_jscpd.py`](../scripts/quality_gates/readers_ruff_jscpd.py) counts **`files[].messages`** only when **`messages`** is a **list**; **`null`** or non-list values contribute **0** (no **`TypeError`** / wrong **`len()`** on dicts).
- **cloc / JSON metrics**: **`cloc_slocs_comments()`** uses **`coerce_non_negative_float()`** in [`jsonutil.py`](../scripts/quality_gates/jsonutil.py) (built from **`_as_non_negative_float`**, **`_non_negative_float_from_str`**, **`_non_negative_float_from_number`**) for **`Python.code`** / **`Python.comment`** so **`null`**, non-numeric strings, lists, etc. yield **0.0** instead of raising. **`interrogate_coverage()`** and **`pylint_score()`** use **`parse_float_or_none()`** on regex captures. **Radon** CC/MI and **jscpd** **`percentage`** reject JSON **booleans** for numeric fields (Python **`bool`** is a **`int`** subclass — avoids **`true` → 1.0** misreads). **`readers_radon.mi_value_from_entry`** delegates dict-shaped nodes to **`_mi_from_dict_entry`** to keep Radon CC low.

### 3. GitHub Actions / workflows

- **`python-quality.yml`**: Reusable **`workflow_call`** for **app** repos — **multi-job** gated pipeline. First job **`devops-coordinates`** parses **`github.workflow_ref`** (`owner/repo/.github/workflows/file.yml@ref` → repository + ref) so **`.devops`** checkout matches the pinned reusable workflow unless **`devops_repository`** / **`devops_ref`** inputs are non-empty (overrides). Fallback when parsing fails: **`github.repository`** / **`github.ref_name`**. Downstream jobs **`needs: devops-coordinates`** (and their prior deps) for checkout of `.devops`.
  - Pipeline shape: **`quality-shield`** → **`quality-static`** + **`quality-supply-chain`** (parallel) → **`quality-test`** → **`quality-report`** (`if: always()`, merge artifacts, license + full **`scripts.quality_gates`**, consolidate, bundle; final step fails job if license/gates failed after uploads) → **`pr-quality-comment`** → optional **`quality-dast`** → **`release-github`** (only on **`refs/tags/v*.*.*`**, **`environment: production`**, requires **`gates_passed`**, supply + test + report success, DAST success or skipped). **`workflow_call` outputs** include **`gates_passed`**. **`~/.cache/uv`** restored via **`actions/cache`** on static/supply/test jobs.
  - Callers still use a **literal** `uses: …/python-quality.yml@vX.Y.Z`; dynamic **`uses:`** is not supported by GitHub.
  - **Removed** standalone **`grype --fail-on`**; vuln caps remain in **`gate_vulnerabilities`**. Documented in [`docs/workflows.md`](workflows.md).
  - **`workflow_dispatch`** input limit (**10**): **`app_install_command`** exists only on **`workflow_call`**; use **`${{ inputs.app_install_command || '' }}`**. Do not read undefined **`github.event.inputs`** for undeclared dispatch keys (**actionlint**).
  - **`docstring_format: Pep257`**: Ruff **`convention = "pep257"`**; pydoclint **`--style=sphinx`**.
  - **Tag releases**: Callers must run the reusable workflow on **tag pushes** (e.g. `on.push.tags`) for **`release-github`** to execute.
- **`publish-pypi.yml`**: **`workflow_dispatch` only**; job uses **`environment: pypi`** (manual PyPI publish with OIDC).
- **`devops-ci.yml`** (this repo only): Consolidated CI replacing **`reusable-workflows-quality`**, **`devops-scripts-ci`**, **`dependency-review`**. Path-filtered jobs via **`dorny/paths-filter`**; **`workflow_dispatch`** enables all groups. **`ci-workflow-lint`**: **actionlint** with **`continue-on-error: true`**, then **zizmor**, then a **gate** step (`if: always()`). Same pattern (soft step + gate) for **Scorecard** and **dependency review** where applicable. Five parallel script jobs (pytest, pylint, interrogate, Radon CC, Radon MI): each repeats checkout/cache/sync + tool + gate (**redundant structure by design**). **Template-injection** mitigation: step outcomes via **`env`**, not `${{ }}` inside shell strings. **Interrogate** **`--fail-under 95`** on **`scripts`**.
- **`devops-scheduled.yml`** (this repo only): Weekly **Monday 06:00 UTC** + **`workflow_dispatch`**; merges former **lint**, **Scorecard**, **Mutmut**, **EOL** workflows. On **push** that only touches EOL policy / this workflow, **only** the EOL job runs (`if: github.event_name != 'push'` on lint/mutmut/scorecard). **Mutmut**: strict **`mutmut run`**, **`export-cicd-stats`**, then **`scripts/mutmut_score_gate.py`** with **`MUTMUT_MIN_SCORE=85`** (fails workflow below 85%). **Zizmor**: build a bash array of paths that **exist** (workflows, actions, dependabot, examples), run **once**; avoid empty input sets (zizmor exit 3 “no inputs collected”).
- **`qa-install-toolchain`**: **Syft / Grype** installed to **`/usr/local/bin`** with `sudo tar` (avoids **`GITHUB_PATH`** writes flagged by zizmor; tools still on default PATH).
- **`setup-uv-python`** used where Python **3.13** must exist before **`uv sync`** (matches `pyproject.toml` `requires-python`).

### 4. Dependabot (`.github/dependabot.yml`)

- **`cooldown`** on update entries: **`default-days: 7`** (zizmor policy).
- **`github-actions`** ecosystem: only **`default-days`** (semver cooldown keys are **not** supported for that ecosystem — Dependabot parse error if included).

### 5. Documentation

- [`docs/workflows.md`](workflows.md): multi-job **`python-quality.yml`** (**`devops-coordinates`**, Semgrep High policy), **`devops-ci.yml`** / **`devops-scheduled.yml`**, **`workflow_call` outputs**, **`release-github`** / **`publish-pypi`** behavior, **no duplicate Grype CLI fail-on** alongside gates.
- [`README.md`](../README.md): versioning with optional **`devops_*`** overrides; PyPI manual dispatch + **`pypi`** environment.

### 6. Tests / tooling

- **`tests/test_scorecard_summary.py`**: Stronger assertion that **aggregate score line** reflects check mean when aggregateScore conflicts; **JSON boolean** check scores do not skew the headline mean.
- **`tests/test_quality_gates.py`**: PR comment text when **`gates.json`** is invalid JSON updated to match **`pr_comment_markdown.py`** wording.
- **`tests/test_pr_comment.py`** / **`tests/test_consolidate.py`**: Cover **`gates.json`** with **omitted `passed`** (must surface as **FAILED** in comment / consolidated report).
- **`tests/test_readers_cloc_docs.py`**: **pydoclint** issue counting matches flake8-style violation lines only (not “0 errors” summaries); **cloc** defensive parsing.
- **`tests/test_jsonutil.py`**: **`coerce_non_negative_float`** edge cases.
- **`tests/test_license_gate_extra.py`**: **`LICENSE_DENY_LIST`** entries must be **JSON strings**; **`null`** / numbers are skipped.
- **`tests/test_mutmut_score_gate.py`**: **`MUTMUT_MIN_SCORE`** threshold, missing stats file, zero-denominator cases for **`scripts/mutmut_score_gate.py`**.

### 7. Misc scripts

- **`scripts/scorecard_summary.py`**: SARIF **`tool` / `tool.driver`** validation; consolidated **`_truncate`** (removed duplicate `_truncate_cell`). **Scorecard numeric fields** use **`_is_real_number`** / **`_non_negative_score_value`** so JSON **`true`/`false`** are not treated as **1.0**/**0.0** in aggregates, table formatting, or **`_needs_action`** (same **`bool`**-as-**`int`** pitfall as elsewhere).
- **`scripts/pr_comment_markdown.py`**: Invalid JSON message does not claim “missing” when file exists; user-facing text refers to **`gates.json`** (code-formatted in Markdown). **GFM gate tables** sanitize cell text via [`scripts/mdutil.py`](../scripts/mdutil.py) (`sanitize_markdown_table_cell`: newlines/tabs → spaces, `|` → U+00A6 broken bar, truncation) so tool messages cannot break columns.
- **`scripts/consolidate_artifacts.py`**: Uses the same cell sanitization for the consolidated **quality_report.md** gate table. Per-tool **`summary_*.txt`** sections use **`markdown_fenced_code_block()`** from [`mdutil.py`](../scripts/mdutil.py) so log bodies containing **\`\`\`** do not break fenced Markdown (fence length = max(3, longest \` run + 1)). If **`gates.json`** is present but **not valid JSON** (e.g. truncated write), the consolidated summary treats the run as **FAILED**, not PASSED, with an explanatory note naming **`gates.json`** (code-formatted) in the report body.
- **Bandit gate**: [`scripts/quality_gates/gates_security.py`](../scripts/quality_gates/gates_security.py) `gate_bandit` uses [`readers_bandit.py`](../scripts/quality_gates/readers_bandit.py) to count `bandit.json` `results` vs **`bandit_findings_max`** per tier (High: 0; Medium: 3; Low: 15). Wired in [`evaluation.py`](../scripts/quality_gates/evaluation.py) `collect_gate_results` so SAST findings affect **`passed`** like other gates. The gate row **`gate`** label is always **`Bandit (SAST)`**; parse/shape problems are expressed in **`actual`** / **`required`**, not a second label variant.
- **`scripts/license_gate.py`**: **`LICENSE_DENY_LIST`** is a JSON array of **strings** only; non-string elements are **ignored** (avoids **`str(null)` → `"none"`-style accidental matches). **`_find_license_hits`** types **`packages`** as **`list[Any]`** to match SPDX JSON (non-dict entries are skipped).
- **`scripts/quality_gates/readers_cloc_docs.py` — `pydoclint_issue_count`**: Counts lines matching pydoclint’s flake8-style **`path:line:col: ERROR`** pattern, not any line containing the word “error” (avoids false positives from “0 errors” / “No errors found”).

---

## Files and areas a future agent should read first

| Area | Path(s) |
| --- | --- |
| Gate thresholds & High artifacts | `scripts/quality_gates/config.py` |
| `gates.json` normalization | `scripts/quality_gates/jsonutil.py` (`read_json` returns `None` on missing file, invalid JSON, **OSError**, or **UnicodeError**) |
| Gate orchestration | `scripts/quality_gates/evaluation.py`, `engine.py` |
| CI bundle | `scripts/ci_run_quality.sh` |
| Reusable app workflow | `.github/workflows/python-quality.yml` (multi-job; see `docs/workflows.md`) |
| Semgrep SARIF reader | `scripts/quality_gates/readers_semgrep.py` |
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
- **Cursor agents**: see [`.cursor/rules/handoff-and-commits.mdc`](../.cursor/rules/handoff-and-commits.mdc) — refresh **`docs/ai-agent-handoff.md`** on substantive changes and end with a **conventional commit** line for the user. **[`.cursor/rules/radon-complexity.mdc`](../.cursor/rules/radon-complexity.mdc)** — run **`radon cc -s`** on edited **`scripts/`** and **`tests/`** `.py` files; **`scripts/quality_gates/`** must stay **≤ 5** CC per function (**no grade B** on changed functions).

---

## Suggested verification for the next agent

1. `git status` / `git log` vs remote (e.g. **`feature-restructure`**).
2. Run **`uv sync`** then **`uv run pytest`** (or CI) on **`scripts/`** and **`tests/`**.
3. **`uv run --with radon python -m radon cc -s`** on any **`scripts/`** or **`tests/`** `.py` files you change (required habit for agents — see **`.cursor/rules/radon-complexity.mdc`**).
4. Scan **`.github/workflows`** and **`action.yml`** files with **actionlint + zizmor** if editing CI (see **`devops-ci.yml`** / **`devops-scheduled.yml`** jobs that run those tools).

---

## Limitations of this document

- **Other Cursor/AI sessions** are not fully reproduced here; **git history** is the ground truth for authorship and ordering.
- If commits were **rebased** or **squashed**, messages above may not match your clone exactly.

---

*Generated for handoff between AI agents and human maintainers. Update this file when making large architectural or CI contract changes.*
