# AI agent handoff — pydevops repository context

This document summarizes **what has been implemented and refined** on the current CI / workflow line
of work so another agent can continue without re-deriving context. It merges **recent git history**
with **conversation-level detail** where useful.

**Repository purpose:** Reusable GitHub Actions (“Quality-as-a-Service”) and Python scripts for
Python CI: static analysis, tests/coverage, SBOM, secret/SAST scans, optional DAST, and quality
**gates** evaluated from CI artifacts. See [`README.md`](../README.md) and
[`docs/workflows.md`](workflows.md).

______________________________________________________________________

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
  - …earlier: cyclomatic/MI refactors, dependabot cooldowns, docstrings, zizmor-related workflow
    fixes, fail-closed artifacts, radon edge cases, initial QaaS pipeline, etc.

Use `git log --oneline` for the authoritative list.

______________________________________________________________________

## Major themes (cross-cutting)

### 1. Quality gates (`scripts/quality_gates/`)

- Central evaluation: **`python -m scripts.quality_gates`** (reads `QUALITY_OUTPUT_DIR`,
  `STRICTNESS_LEVEL`), writes **`gates.json`**.
- **Strictness tiers** (`Low` / `Medium` / `High`) map to **`Thresholds`** in
  [`scripts/quality_gates/config.py`](../scripts/quality_gates/config.py) (coverage, Pylint, Radon
  CC/MI, duplication, vulns, **Bandit finding counts**, docstrings, **mypy report metrics**, etc.).
- **Mypy metrics** (from `ci_run_quality.sh` static phase): **`--lineprecision-report`** and
  **`--any-exprs-report`** write under **`mypy-reports/`**; **`gate_mypy`** enforces type coverage
  (any-exprs total), imprecision share (imprecise / analyzed lines), and any-expression density
  (**anys × 1000 / Python SLOC** from **`cloc.json`**). **Low**/**Medium** skip mypy gates when both
  reports are absent; when **SLOC ≤ 0**, Low/Medium also skip the density gate while **High fails
  closed**. **High** requires the report files (see **`HIGH_REQUIRED_FILES`**) with parseable
  totals. Thresholds: **Low** coverage `≥85%`, imprecision `<5%`, density `<5/KLoC`;
  **Medium** `≥90%`, `<2%`, `<2/KLoC`; **High** `≥95%`, `<1%`, `<1/KLoC`.
- Maintainability refactor: heavy mypy parsing/rule-builder code moved out of
  `scripts/quality_gates/` into shared helpers (`scripts/mypy_report_lineprecision.py`,
  `scripts/mypy_report_anyexprs.py`, `scripts/mypy_gate_rules.py`), while
  `scripts/quality_gates/readers_mypy*.py` and `gates_mypy.py` are now thin adapters. This keeps
  MI safely above 40 in the gated `scripts/quality_gates` package.
- **High** tier additionally requires artifacts listed in **`HIGH_REQUIRED_FILES`** (fail-closed if
  tools skipped); includes **`pydoclint.txt`** so a missing pydoclint run cannot be confused with
  zero findings. **`pydoclint.txt`** may be **empty** when there are zero violations (still counts
  as present).
- Parsers were **hardened** to fail closed on malformed JSON (coverage, radon, pip-audit, grype,
  cloc, SARIF tool/driver shapes in `scorecard_summary.py`, etc.).
- **`scripts/quality_gates/jsonutil.py` — `gates_rows_and_passed()`**: If the root is a dict and
  `rows` is a list, **`passed` defaults to `False` when the key is missing** (legacy / partial
  `gates.json` must not summarize as PASSED). Used by **`pr_comment_markdown.py`** and
  **`consolidate_artifacts.py`** (alongside invalid-JSON handling there).
- **Vulnerabilities**: `pip_audit_vulns()` / `grype_severities()` return **`None`** when the report
  is missing, invalid JSON, or wrong top-level type; **`gate_vulnerabilities`** adds explicit
  failing rows (report shape / missing file) instead of treating as zero findings.
  **`HIGH_REQUIRED_FILES`** includes **`pip_audit.json`** and **`grype.json`** so High tier cannot
  skip those scans silently. **`readers_grype_gitleaks.count_one_grype_match`** requires
  **`vulnerability`** to be a **dict** before reading **`severity`** (non-dict values are ignored so
  malformed Grype rows do not raise).
- **Pytest**: **`pytest_exit_code.txt`** is written by **`ci_run_quality.sh`**;
  **`gate_pytest_exit`** fails on non-zero (and High requires the artifact).
- **Radon CC**: **`radon_cc_max`** must track a **`found`** flag for valid complexity values — do
  not use `max_cc if max_cc else None` (**`0.0`** is a valid maximum).
- **jscpd**: **`jscpd_duplication_pct()`** parses `percentage` safely (type / string); **`None`** on
  bad values so the duplication gate fails in a controlled way.
- **Cyclomatic complexity / maintainability** targets for *this repo’s* `scripts/quality_gates` were
  brought in line with CI (Radon CC ≤ 5, MI floor, Interrogate docstring coverage).
- **`gates_complexity.py`**: Gate **labels** for cyclomatic / maintainability use **High-specific
  wording only when `strictness_norm == "High"`** so Low/Medium reports are not misleading.
- **`artifact_rules.py`**: Extracted static JSON shape / path rules for High-tier artifact
  validation; **`gates_artifacts.py`** consumes them.
- **Semgrep (High only)**: **`gate_semgrep`** +
  **`readers_semgrep.semgrep_sarif_error_warning_counts`** enforce **`semgrep.sarif`**: **0** SARIF
  **`level: error`** results, **≤ 5** **`level: warning`** (note-level ignored).
  **`HIGH_REQUIRED_FILES`** includes **`semgrep.sarif`**. Shield job runs
  **`python -m scripts.quality_gates --semgrep-shield-only`** after **`qa-secrets-sast`**
  (Low/Medium: no-op pass). **`qa-secrets-sast`**: Semgrep scan uses **`continue-on-error: true`**;
  the blocking second **`--error`** scan was removed in favor of gates.

### 2. Shell driver `scripts/ci_run_quality.sh`

- Phases: **`QUALITY_PHASES`** = `static` | `security` | `test` | `all`.
- **Output directory**: `cd "$APP_DIR"` first; then **`OUT`** from `QUALITY_OUTPUT_DIR` — **relative
  paths are resolved under the app root** so `mkdir` and writes align.
- **No fake “success-shaped” outputs** for missing **security** tools (bandit, pip-audit, grype,
  syft, jscpd when `npx` missing): files are **omitted** instead of empty JSON implying zero issues.
  **High** also **omits `pydoclint.txt`** when the **pydoclint** CLI is missing (Low/Medium still
  write the placeholder line that gates ignore for “not installed”).
- **Syft**: If the **`syft`** CLI is absent, **`sbom-cyclonedx.json`** / **`sbom-spdx.json`** are
  **removed** (not `{}`), consistent with other security fallbacks. Grype only runs when
  **`sbom-cyclonedx.json`** exists.
- **Low/Medium** may still use minimal placeholders for some **static** tools (documented in header
  comment); High omits more aggressively.
- **Ruff**: multiple `--exclude` flags from comma-separated `RUFF_EXCLUDE`.
- **jscpd**: Pinned version read from **`.github/dependencies/jscpd/package.json`** (semver
  extracted for **`npx --yes "jscpd@${VER}"`**); falls back to **`jscpd@4.0.9`** if missing.
- **Ruff object format**: **`ruff_messages_in_files()`** in
  [`readers_ruff_jscpd.py`](../scripts/quality_gates/readers_ruff_jscpd.py) counts
  **`files[].messages`** only when **`messages`** is a **list**; **`null`** or non-list values
  contribute **0** (no **`TypeError`** / wrong **`len()`** on dicts).
- **cloc / JSON metrics**: **`cloc_slocs_comments()`** uses **`coerce_non_negative_float()`** in
  [`jsonutil.py`](../scripts/quality_gates/jsonutil.py) (built from **`_as_non_negative_float`**,
  **`_non_negative_float_from_str`**, **`_non_negative_float_from_number`**) for **`Python.code`** /
  **`Python.comment`** so **`null`**, non-numeric strings, lists, etc. yield **0.0** instead of
  raising. **`interrogate_coverage()`** and **`pylint_score()`** use **`parse_float_or_none()`** on
  regex captures. **Radon** CC/MI and **jscpd** **`percentage`** reject JSON **booleans** for
  numeric fields (Python **`bool`** is a **`int`** subclass — avoids **`true` → 1.0** misreads).
  **`readers_radon.mi_value_from_entry`** delegates dict-shaped nodes to **`_mi_from_dict_entry`**
  to keep Radon CC low.

### 3. GitHub Actions / workflows

- **`python-quality.yml`**: Reusable **`workflow_call`** for **app** repos — **multi-job** gated
  pipeline. Workflow-level **`env`** is a **single** mapping
  (**`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`** and **`QUALITY_OUTPUT_DIR`** together); duplicate
  top-level **`env`** keys break **actionlint** / **zizmor** registry parsing. First job
  **`devops-coordinates`** parses **`github.workflow_ref`**
  (`owner/repo/.github/workflows/file.yml@ref` → repository + ref) so **`.devops`** checkout matches
  the pinned reusable workflow unless **`devops_repository`** / **`devops_ref`** inputs are
  non-empty (overrides). Fallback when parsing fails: **`github.repository`** /
  **`github.ref_name`**. Downstream jobs **`needs: devops-coordinates`** (and their prior deps) for
  checkout of `.devops`.
  - Pipeline shape: **`quality-shield`** → **`quality-static`** + **`quality-supply-chain`**
    (parallel) → **`quality-test`** → **`quality-report`** (`if: always()`, merge artifacts, license
    \+ full **`scripts.quality_gates`**, consolidate, bundle; final step fails job if license/gates
    failed after uploads) → **`pr-quality-comment`** → optional **`quality-dast`** →
    **`release-github`** (only on **`refs/tags/v*.*.*`**, **`environment: production`**, requires
    **`gates_passed`**, supply + test + report success, DAST success or skipped). Release assets now
    include both **`dist/*`** (wheel/sdist built in `quality-report` for tag runs and uploaded as
    `release-dist`) and the zipped **quality bundle**. **`workflow_call`
    outputs** include **`gates_passed`**. **`~/.cache/uv`** restored via **`actions/cache`** on
    static/supply/test jobs.
  - **`quality-shield`** and **`quality-report`** use **`setup-uv-python`** (not **`install-uv`
    alone**) and **`uv sync` / `uv run` with `--python ${{ inputs.python_version }}`** so runners
    without a preinstalled **3.13+** interpreter still resolve **`pyproject.toml`**
    `requires-python`. **`quality-report`**: license enforcement and gate evaluation use
    **`continue-on-error: true`** so **`consolidate_artifacts`**, bundle upload, PR comment
    artifact, **`gates-out`**, and the final enforcement step still run; the job exits non-zero from
    the last step when license or gates failed.
  - Callers still use a **literal** `uses: …/python-quality.yml@vX.Y.Z`; dynamic **`uses:`** is not
    supported by GitHub.
  - **Removed** standalone **`grype --fail-on`**; vuln caps remain in **`gate_vulnerabilities`**.
    Documented in [`docs/workflows.md`](workflows.md).
  - **`workflow_dispatch`** input limit (**10**): **`app_install_command`** exists only on
    **`workflow_call`**; use **`${{ inputs.app_install_command || '' }}`**. Do not read undefined
    **`github.event.inputs`** for undeclared dispatch keys (**actionlint**).
  - Type-checking: the static bundle (**`ci_run_quality.sh`**) runs **mypy** with
    **`--lineprecision-report`** and **`--any-exprs-report`** (exit code ignored; gates use
    reports + **cloc** SLOC). No separate **`uv run mypy`** step in **`python-quality.yml`**.
  - **`docstring_format: Pep257`**: Ruff **`convention = "pep257"`**; pydoclint
    **`--style=sphinx`**.
  - **Tag releases**: Callers must run the reusable workflow on **tag pushes** (e.g. `on.push.tags`)
    for **`release-github`** to execute. The job **`if:`** uses
    **`startsWith(github.ref, 'refs/tags/v')`** and **`github.ref_type == 'tag'`** (no
    **`matches()`** — not a supported expression function); a **bash** step enforces strict
    **`vMAJOR.MINOR.PATCH`** (digits only).
- **`publish-pypi.yml`**: **`workflow_dispatch` only**; job uses **`environment: pypi`** (manual
  PyPI publish with OIDC). It now requires a **`tag`** input, checks out that tag
  (full history with `fetch-depth: 0`), validates **`vX.Y.Z`**, verifies the tag exists via
  `git rev-parse`, explicitly checks out `refs/tags/<tag>` with detached HEAD, then publishes with
  **`attestations: true`** and job permission **`attestations: write`** (plus
  **`id-token: write`**). Tag validation uses an anchored
  regex (`^v[0-9]+\.[0-9]+\.[0-9]+$`) so prerelease/extra-segment tags are rejected.
- **`pyproject.toml`** PEP 621 metadata was enriched for publishing provenance and index metadata:
  `authors`, `classifiers`, `keywords`, `license`, `license-files`, and `project.urls`.
- **`devops-ci.yml`** (this repo only): Path filter → three lanes: **`ci-workflow-lint`**
  (**actionlint** + **zizmor** in one job — same **`.github/`** scope, one checkout/harden/install
  cycle; splitting would duplicate setup unless a reusable workflow is introduced), **`ci-scripts`**
  (single job: **pytest**, **pylint**, **interrogate**, Radon CC/MI, and **pip-audit** after one
  **`uv sync`**; logs under **`_ci_summary/`**; **`scripts/ci_scripts_job_summary.py`** appends a
  **two-column** job summary (Analysis / Result, thresholds inlined); **pip-audit** runs as
  non-blocking step and fails only at the final gate when Medium/High/Critical dependency
  vulnerabilities are present; pip-audit detail output now includes per-finding package/version,
  vulnerability ID, severity, and reported fix versions in the raw log section; **gate** lists
  failed tools; trades parallel wall time for fewer
  runners), **`ci-supply-chain`** (**OpenSSF Scorecard** when workflow/dispatch rules
  match + **dependency review** on PRs; step-level **`if:`**; **gate** lists **Scorecard** /
  **dependency review** failures). **`ci-supply-chain`** job permissions are **`contents: read`**,
  **`security-events: write`**, and **`id-token: write`** only (no **`pull-requests: write`**;
  **dependency-review-action** defaults keep PR comment summaries off). **`changes`** sets
  **`permissions: contents: read`** and **`pull-requests: read`** for **`actions/checkout`** and
  **`dorny/paths-filter`** (workflow default is **`permissions: {}`**). **`changes`** omits
  **`harden-runner`**. **`workflow_dispatch`** enables all groups. Workflow default
  **`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"`** (including **`ci-supply-chain`** — aligns with
  GitHub’s Node 20 deprecation guidance). Workflow-level **`concurrency`** is now enabled with
  **`${{ github.workflow }}-${{ github.ref }}`** and **`cancel-in-progress: true`**.
  **`ci-workflow-lint`**: **no** problem matcher /
  **`github`** SARIF annotations; **`actionlint -no-color`** tees to **`_diag/actionlint.txt`** and
  appends **`actionlint: OK (no findings).`** on success; **zizmor** **`tee`** keeps ANSI in the
  scan step log and **`_diag/zizmor.txt`**; **Workflow lint — job summary** appends both tools to
  **`$GITHUB_STEP_SUMMARY`**, running **`sed`** on **`_diag/zizmor.txt`** only for the zizmor fenced
  block. No **`dependency-review-config.yml`** — use inline **`allow-dependencies-licenses`** on the
  action if needed; **dependency-review-action** does **not** use **`retry-on-snapshot-warnings`**.
  **`setup-uv-python`** optional **`uv-cache-suffix`** ( **`ci-scripts`** uses
  **`${{ github.job }}`**). In **`ci-scripts`**, a previously redundant manual
  **`actions/cache`** step for `~/.cache/uv` was removed; caching is now delegated to
  **`setup-uv-python`** / underlying setup-uv cache wiring to avoid post-job “path does not exist”
  warnings when uv uses temp cache dirs. **`astral-sh/setup-uv`** pin **`v8.0.0`** in
  **`github-actions-pins.json`**.
- **Scorecard Pinned-Dependencies hardening (workflow shell steps)**:
  `devops-ci.yml` and `devops-scheduled.yml` workflow-lint jobs no longer use
  `curl ... | bash` for actionlint nor `python -m pip install -r` for zizmor.
  They now install actionlint from a pinned release tarball with SHA256 verification
  (`.github/dependencies/actionlint/version.txt` + `linux-amd64.sha256`), and run zizmor via
  `uv run --with-requirements .github/dependencies/zizmor/requirements.txt ...` after
  `./.github/actions/install-uv`. Workflow lint fails closed if actionlint pin files are missing.
- **`devops-scheduled.yml`** (this repo only): Weekly **Monday 06:00 UTC** +
  **`workflow_dispatch`**; merges former **lint**, **Scorecard**, **Mutmut**, **EOL** workflows. On
  **push** that only touches EOL policy / this workflow, **only** the EOL job runs
  (`if: github.event_name != 'push'` on lint/mutmut/scorecard). **Mutmut**: strict **`mutmut run`**,
  **`export-cicd-stats`**, then **`scripts/mutmut_score_gate.py`** with **`MUTMUT_MIN_SCORE=85`**
  (fails workflow below 85%). **Scheduled workflow lint** mirrors **`ci-workflow-lint`** (plain logs
  \+ **job summary**, no annotations). **Zizmor**: build a bash array of paths that **exist**
  (workflows, actions, dependabot, examples), run **once**; avoid empty input sets (zizmor exit 3
  “no inputs collected”). Workflow-level **`concurrency`** now mirrors `devops-ci.yml`
  (`${{ github.workflow }}-${{ github.ref }}`, `cancel-in-progress: true`).
- **`qa-install-toolchain`**: **Syft / Grype** installed to **`/usr/local/bin`** with `sudo tar`
  (avoids **`GITHUB_PATH`** writes flagged by zizmor; tools still on default PATH).
- **`setup-uv-python`** used where Python **3.13** must exist before **`uv sync`** (matches
  `pyproject.toml` `requires-python`).
- **Current April 2026 tool baseline**: Ruff **0.15.11**, Mypy **1.20.2**, pytest **9.0.3**, Semgrep
  **1.159.0**, Mutmut **>=3.5.0,\<4**, Zizmor **>=1.24.1,\<2**, jscpd **4.0.9**, Locust **2.43.4**,
  Harden-Runner **v2.18.0**, and `actions/github-script` **v9**.
- **Requirements pins**: no generic **`requirements-txt-fixer`** pre-commit hook; generated
  **`.github/dependencies/quality-tools/requirements.txt`** is owned by
  **`scripts/export_pinned_requirements.sh`** / **`scripts/export_quality_tools_requirements.py`**.

### 4. Dependabot (`.github/dependabot.yml`)

- **`cooldown`** on update entries: **`default-days: 7`** (zizmor policy).
- **`github-actions`** ecosystem: only **`default-days`** (semver cooldown keys are **not**
  supported for that ecosystem — Dependabot parse error if included).
- Dependabot config now includes **explicit Monday schedule windows** (`day` / `time` /
  `timezone: Europe/Lisbon`) for each ecosystem block, plus update **groups** for
  `github-actions`, `uv` development dependencies, and `pre-commit` hooks.
- New ecosystem block: **`pre-commit`** at repo root so `.pre-commit-config.yaml` hook revs are
  updated by Dependabot.
- New workflow **`.github/workflows/dependabot-metadata.yml`** summarizes Dependabot PR metadata in
  the job summary (Dependabot actor only), using pinned
  **`dependabot/fetch-metadata`** from `github-actions-pins.json`.

### 5. Documentation

- [`docs/workflows.md`](workflows.md): multi-job **`python-quality.yml`** (**`devops-coordinates`**,
  Semgrep High policy), **`devops-ci.yml`** / **`devops-scheduled.yml`**, **`workflow_call`
  outputs**, **`release-github`** / **`publish-pypi`** behavior, **no duplicate Grype CLI fail-on**
  alongside gates.
- [`docs/improvements.md`](improvements.md): now tracks only not-yet-implemented backlog items,
  grouped as High / Medium / Low priority; implemented items were removed.
- [`test-plan.md`](test-plan.md): local validation already passed (pre-commit/pre-push, pytest
  + coverage, pylint, radon, interrogate, pins/requirements drift, zizmor, actionlint). Manual
  coverage now explicitly includes fork token-scope behavior, `gates_passed` workflow output
  checks, negative release tag checks, DAST enable/disable behavior, and EOL-only push path tests.
- [`README.md`](../README.md): versioning with optional **`devops_*`** overrides; PyPI manual
  dispatch + **`pypi`** environment.
- **Version pins:** **`pyproject.toml`** `[dependency-groups].quality-tools` is the source for
  Ruff/Pylint/pytest/etc.; **`bash scripts/export_pinned_requirements.sh`** refreshes
  **`.github/dependencies/quality-tools/requirements.txt`**. **`github-actions-pins.json`** +
  **`scripts/github_actions_pins.py`** own **`uses:`** versions (CI **`--check`**). Semgrep and
  Locust stay in separate **`requirements.txt`** (tomli vs pip-audit conflict with root lock).
  **`pylint-json2html`** is pinned for **`pylint_report.html`** in the quality bundle (see
  **`ci_run_quality.sh`**).
- **Formatting policy alignment:** `.pre-commit-config.yaml` no longer includes
  `double-quote-string-fixer` because Ruff formatter is configured with single-quote style in
  `pyproject.toml` (`[tool.ruff.format].quote-style = "single"`), avoiding formatter tug-of-war.
- **PEP 621 license metadata:** `[project].license` in `pyproject.toml` now uses a compliant table
  (`{text = "MIT"}`) rather than a bare string, while keeping `license-files = ["LICENSE"]`.

### 6. Tests / tooling

- **`tests/test_scorecard_summary.py`**: Stronger assertion that **aggregate score line** reflects
  check mean when aggregateScore conflicts; **JSON boolean** check scores do not skew the headline
  mean.
- **`tests/test_quality_gates.py`**: PR comment text when **`gates.json`** is invalid JSON updated
  to match **`pr_comment_markdown.py`** wording.
- **`tests/test_pr_comment.py`** / **`tests/test_consolidate.py`**: Cover **`gates.json`** with
  **omitted `passed`** (must surface as **FAILED** in comment / consolidated report).
- **`tests/test_readers_cloc_docs.py`**: **pydoclint** issue counting matches flake8-style violation
  lines only (not “0 errors” summaries); **cloc** defensive parsing.
- **`tests/test_jsonutil.py`**: **`coerce_non_negative_float`** edge cases.
- **`tests/test_license_gate_extra.py`**: **`LICENSE_DENY_LIST`** entries must be **JSON strings**;
  **`null`** / numbers are skipped.
- **`tests/test_mutmut_score_gate.py`**: **`MUTMUT_MIN_SCORE`** threshold, missing stats file,
  zero-denominator cases for **`scripts/mutmut_score_gate.py`**.

### 7. Misc scripts

- **`scripts/scorecard_summary.py`**: SARIF **`tool` / `tool.driver`** validation; consolidated
  **`_truncate`** (removed duplicate `_truncate_cell`). **Scorecard numeric fields** use
  **`_is_real_number`** / **`_non_negative_score_value`** so JSON **`true`/`false`** are not treated
  as **1.0**/**0.0** in aggregates, table formatting, or **`_needs_action`** (same
  **`bool`**-as-**`int`** pitfall as elsewhere). **`_repo_uri_from_sarif_run`** prefers
  **`versionControlProvenance`** / run **`properties`** / **`invocations`** so the summary names the
  **analyzed repository**, not workflow snippet text like **`ossf/scorecard-action@…`**. The checks
  **ASCII table** (fenced **`text`**) adds a **Package / ref** column from SARIF
  **`locations[].physicalLocation.region.snippet.text`** (e.g. **`uses:`** action pins); JSON-only
  Scorecard payloads show **—** there. Caption **Scope: GitHub repository `…`** when a repo URI is
  known. Helper extraction split rendering and SARIF traversal into `scripts/scorecard_table.py`
  and `scripts/scorecard_sarif_utils.py`; `scripts/scorecard_summary.py` is now a thin
  compatibility/CLI proxy and core behavior lives in `scripts/scorecard_summary_core.py`. The proxy
  now prepends the repo root to `sys.path` when run as `python3 scripts/scorecard_summary.py`, so
  `from scripts...` imports work in GitHub Actions shell steps.
- **`scripts/ci_scripts_job_summary.py`**: Reads **`_ci_summary/*.txt`** and prints a **two-column**
  Markdown table (**Analysis** / **Result**) with **thresholds inlined** in the result column:
  **Tests** (**N** successful / **M** failed, no duration), **Code Coverage**, **Code Quality**
  (pylint score), **Documentation Coverage**, **Cyclomatic Complexity** (`≤5.0 required`),
  **Maintainability Index** (`≥40.0 required`), plus raw log tails in **`<details>`**.
- **`scripts/github_actions_pins.py`**: `github-actions-pins.json` now supports structured entries
  (`{"tag": "vX.Y.Z", "sha": "<40-hex>"}`) in addition to legacy string refs. Apply mode writes
  readable SHA pins as `uses: owner/repo@<sha> # vX.Y.Z`; check mode enforces SHA refs (40 hex) plus
  a trailing version comment for structured pins. `--check` now also fails on SHA drift for
  structured entries (workflow SHA must match `pin['sha']`), so arbitrary 40-char SHAs are no longer
  accepted. `uses:` matching also tolerates trailing spaces with no comment, so apply/check do not
  miss lines like `uses: owner/repo@v1 `.
- **`scripts/pr_comment_markdown.py`**: Invalid JSON message does not claim “missing” when file
  exists; user-facing text refers to **`gates.json`** (code-formatted in Markdown). **GFM gate
  tables** sanitize cell text via [`scripts/mdutil.py`](../scripts/mdutil.py)
  (`sanitize_markdown_table_cell`: newlines/tabs → spaces, `|` → U+00A6 broken bar, truncation) so
  tool messages cannot break columns.
- **`scripts/consolidate_artifacts.py`**: Uses the same cell sanitization for the consolidated
  **quality_report.md** gate table. Per-tool **`summary_*.txt`** sections use
  **`markdown_fenced_code_block()`** from [`mdutil.py`](../scripts/mdutil.py) so log bodies
  containing **\`\`\`** do not break fenced Markdown (fence length = max(3, longest \` run + 1)). If
  **`gates.json`** is **missing** (e.g. gates step crashed before write while
  **`continue-on-error`** hid the step failure until the final enforce step), the report is
  **FAILED** with a note that the file is missing — it does **not** default to PASSED. If
  **`gates.json`** is present but **not valid JSON** (e.g. truncated write), same **FAILED**
  treatment with an invalid-JSON note.
- **`scripts/mutmut_score_gate.py`**: **`MUTMUT_MIN_SCORE`** is parsed with validation (**numeric**,
  **0–100**, not **NaN**); bad values exit **1** with a short **stderr** message instead of a
  **ValueError** stack trace.
- **Bandit gate**:
  [`scripts/quality_gates/gates_security.py`](../scripts/quality_gates/gates_security.py)
  `gate_bandit` uses [`readers_bandit.py`](../scripts/quality_gates/readers_bandit.py) to count
  `bandit.json` `results` vs **`bandit_findings_max`** per tier (High: 0; Medium: 3; Low: 15). Wired
  in [`evaluation.py`](../scripts/quality_gates/evaluation.py) `collect_gate_results` so SAST
  findings affect **`passed`** like other gates. The gate row **`gate`** label is always
  **`Bandit (SAST)`**; parse/shape problems are expressed in **`actual`** / **`required`**, not a
  second label variant.
- **`scripts/license_gate.py`**: **`LICENSE_DENY_LIST`** is a JSON array of **strings** only;
  non-string elements are **ignored** (avoids \*\*`str(null)` → `"none"`-style accidental matches).
  **`_find_license_hits`** types **`packages`** as **`list[Any]`** to match SPDX JSON (non-dict
  entries are skipped).
- **`scripts/quality_gates/readers_cloc_docs.py` — `pydoclint_issue_count`**: Counts lines matching
  pydoclint’s flake8-style **`path:line:col: ERROR`** pattern, not any line containing the word
  “error” (avoids false positives from “0 errors” / “No errors found”).

______________________________________________________________________

## Files and areas a future agent should read first

| Area                             | Path(s)                                                                                                                          |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Gate thresholds & High artifacts | `scripts/quality_gates/config.py`                                                                                                |
| `gates.json` normalization       | `scripts/quality_gates/jsonutil.py` (`read_json` returns `None` on missing file, invalid JSON, **OSError**, or **UnicodeError**) |
| Gate orchestration               | `scripts/quality_gates/evaluation.py`, `engine.py`                                                                               |
| CI bundle                        | `scripts/ci_run_quality.sh`                                                                                                      |
| Reusable app workflow            | `.github/workflows/python-quality.yml` (multi-job; see `docs/workflows.md`)                                                      |
| Semgrep SARIF reader             | `scripts/quality_gates/readers_semgrep.py`                                                                                       |
| Toolchain composite              | `.github/actions/qa-install-toolchain/action.yml`                                                                                |
| Zizmor policy                    | `.github/config/zizmor.yml`                                                                                                      |
| Caller docs                      | `docs/workflows.md`, `examples/call-python-quality.yml`                                                                          |

______________________________________________________________________

## Conventions worth preserving

- **Focused diffs** — avoid unrelated refactors when fixing CI/gates.
- **Fail-closed** for High-tier required artifacts and security parsers where applicable.
- **Human-facing `gates.json`**: Prefer explicit **`passed: true|false`**. Parsers that consume
  **`gates_rows_and_passed()`** treat a **missing `passed`** as **failure**.
- **Single source of truth** for vuln counts: **`gate_vulnerabilities`**, not an extra Grype
  `--fail-on` in the workflow.
- **Bandit policy** is tiered via **`bandit_findings_max`** only (count of `results[]`); adjust
  thresholds in **`config.py`** if product policy changes.
- **Conventional commits** have been used in this line (e.g. `fix(ci):`, `fix(quality-gates):`,
  `docs(workflows):`).
- **Local hooks/config**: `.pre-commit-config.yaml` installs **pre-commit**, **pre-push**, and
  **commit-msg** hooks; `gitlint` runs at `commit-msg`. Mypy is driven by `pyproject.toml` and
  covers `scripts`, `src/devops_quality`, and `tests`. Ruff also reads repo settings from
  `pyproject.toml` (`py313`, line length 100).
- **Cursor agents**: see
  [`.cursor/rules/handoff-and-commits.mdc`](../.cursor/rules/handoff-and-commits.mdc) — refresh
  **`docs/ai-agent-handoff.md`** on substantive changes and end with a **conventional commit** line
  for the user.
  **[`.cursor/rules/python-scripts-ci-gates.mdc`](../.cursor/rules/python-scripts-ci-gates.mdc)** —
  **`uv run pytest`** (all pass, **≥ 95%** line coverage) and **`uv run pylint scripts`** (**≥
  9.5/10**) when editing **`scripts/**/*.py`** or **`tests/**/*.py`**.
  **[`.cursor/rules/radon-complexity.mdc`](../.cursor/rules/radon-complexity.mdc)** — run
  **`radon cc -s`** on edited **`scripts/`** and **`tests/`** `.py` files;
  **`scripts/quality_gates/`** must stay **≤ 5** CC per function (**no grade B** on changed
  functions).
  **[`.cursor/rules/interrogate-docstrings.mdc`](../.cursor/rules/interrogate-docstrings.mdc)** —
  run **`interrogate scripts`** (≥ **95%** docstrings) when editing **`scripts/**/*.py`**.

______________________________________________________________________

## Suggested verification for the next agent

1. `git status` / `git log` vs remote (e.g. **`feature-restructure`**).
2. Run **`uv sync`** then **`uv run pytest`** (enforces **≥ 95%** coverage via **`pyproject.toml`**)
   and **`uv run pylint scripts`** (**≥ 9.5/10**) when you change Python under **`scripts/`** or
   **`tests/`** (see **`.cursor/rules/python-scripts-ci-gates.mdc`**).
3. **`uv run --with radon python -m radon cc -s`** on any **`scripts/`** or **`tests/`** `.py` files
   you change (required habit for agents — see **`.cursor/rules/radon-complexity.mdc`**).
4. **`uv run interrogate scripts -vv --fail-under 95`** when you change **`scripts/**/*.py`** (see
   **`.cursor/rules/interrogate-docstrings.mdc`**).
5. Scan **`.github/workflows`** and **`action.yml`** files with **actionlint + zizmor** if editing
   CI (see **`devops-ci.yml`** / **`devops-scheduled.yml`** jobs that run those tools).

______________________________________________________________________

## Limitations of this document

- **Other Cursor/AI sessions** are not fully reproduced here; **git history** is the ground truth
  for authorship and ordering.
- If commits were **rebased** or **squashed**, messages above may not match your clone exactly.

______________________________________________________________________

*Generated for handoff between AI agents and human maintainers. Update this file when making large
architectural or CI contract changes.*
