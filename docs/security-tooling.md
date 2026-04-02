# Security validation tooling

This repository uses several tools to lint workflows, surface supply-chain posture, and reduce runner egress risk.

## actionlint

**What it does:** Validates GitHub Actions workflow YAML (syntax, contexts, runner labels, reusable workflow usage).

**Where it runs:** `.github/workflows/reusable-workflows-quality.yml` job `actionlint-zizmor`. The step prints the workflow and composite-action paths being scanned, then `actionlint: OK (no findings).` when the run is clean.

**Local use**

```bash
bash <(curl -sSL https://raw.githubusercontent.com/rhysd/actionlint/v1.7.7/scripts/download-actionlint.bash) 1.7.7
./actionlint -color
```

Or run the same version pinned in the workflow via Docker:

```bash
docker run --rm -v "$PWD:/repo" -w /repo rhysd/actionlint:1.7.7 -color
```

## zizmor

**What it does:** Static analysis for GitHub Actions — risky patterns, excessive permissions, template injection, unpinned actions, etc.

**Where it runs:** `reusable-workflows-quality.yml` against `.github/workflows/`, `.github/actions/`, and `examples/`.

**Policy:** [`.github/config/zizmor.yml`](../.github/config/zizmor.yml) sets `unpinned-uses` to **ref-pin** (tag or SHA) and ignores `secrets-outside-env` for `python-quality.yml` only (optional `caller_pat` for fork PR comments without requiring callers to define a GitHub Environment). The default zizmor policy is hash-pin for all actions; ref-pin matches typical Dependabot + semver tags. Tighten to full SHA pinning when you adopt a pin-updater (for example [pinact](https://github.com/suzuki-shunsuke/pinact) or [frizbee](https://github.com/stacklok/frizbee)).

**Local use**

```bash
python3 -m pip install --user -r .github/dependencies/zizmor/requirements.txt
cd /path/to/devops-repo
zizmor -c .github/config/zizmor.yml --format plain .github/workflows/ examples/
```

Run from the repository root and pass `-c .github/config/zizmor.yml` (or set `ZIZMOR_CONFIG`) so the policy file is loaded.

## OpenSSF Scorecard

**What it does:** Scores repository security health (branch protection, dependencies, CI, etc.). CI writes **SARIF** (`results.sarif`) and **publishes** it to GitHub code scanning. The same SARIF file is parsed by `scripts/scorecard_summary.py` to print a Markdown table and verdict in the log and the GitHub **job summary** (Scorecard encodes each check as `score is N: …` in SARIF result messages).

**Where it runs:** `reusable-workflows-quality.yml` job `openssf-scorecard` using `ossf/scorecard-action@v2.4.3`.

**Requirements:** The job uses `id-token: write` and `security-events: write` for the action; runs are skipped on forks.

**Docs:** [OpenSSF Scorecard](https://scorecard.dev/), [scorecard-action](https://github.com/ossf/scorecard-action).

## StepSecurity Harden-Runner

**What it does:** Monitors egress and process activity on GitHub-hosted runners; supports **audit** mode (log destinations) and **block** mode (allow lists).

**Where it runs:** First step of jobs in `python-quality.yml`, `publish-pypi.yml`, `mutmut-nightly.yml`, and `reusable-workflows-quality.yml`.

**Current policy:** `egress-policy: audit` so installs (PyPI, GitHub releases, Semgrep registry, etc.) keep working. After reviewing StepSecurity’s recommended allow list for your pipelines, switch relevant jobs to `egress-policy: block` with explicit `allowed-endpoints`.

**Docs:** [step-security/harden-runner](https://github.com/step-security/harden-runner).
