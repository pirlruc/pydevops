# Test Plan Status

## Passed Locally
* Pre-commit hooks: Passed after yamlfix auto-formatted .pre-commit-config.yaml.

    * Ran: uv run pre-commit run --all-files --show-diff-on-failure

* Pre-push hooks: Passed, including Bandit, Semgrep, and Gitleaks.

    * Ran: SSL_CERT_FILE="$(uv run python -m certifi)" uv run pre-commit run --hook-stage pre-push --all-files --show-diff-on-failure

* Unit tests and coverage: Passed.

    * Ran: uv run pytest
    * Result: 170 passed, total coverage 95.26%

* Pylint gate: Passed.

    * Ran: uv run pylint scripts
    * Result: 9.89/10
    * Note: Pylint printed a sandbox cache warning for ~/Library/Caches/pylint, but exited successfully.

* Radon complexity: Passed.

    * Ran: uv run --with radon python -m radon cc -s scripts tests

* Interrogate docstring coverage: Passed.

    * Ran: uv run --group quality-tools python -m interrogate scripts -vv --fail-under 95
    * Result: 100.0%

* GitHub Actions pin drift: Passed.

    * Ran: uv run python scripts/github_actions_pins.py --check

* Generated quality-tool requirements drift: Passed.

    * Ran: bash scripts/export_pinned_requirements.sh
    * Ran: git diff --exit-code -- .github/dependencies/quality-tools/requirements.txt

* zizmor workflow audit: Passed.

    * Ran: uv run --with-requirements .github/dependencies/zizmor/requirements.txt zizmor -c .github/config/zizmor.yml --format plain .github/workflows .github/actions .github/dependabot.yml examples
    * Result: no findings

* actionlint workflow syntax: Passed.

    * Ran: actionlint 1.7.7 against workflows.

* IDE lints: Passed.

    * Ran: ReadLints
    * Result: no linter errors.

## Remaining Manual Tests

### 1. GitHub PR Validation
Open a PR with the staged changes and confirm DevOps CI runs all expected lanes.

Steps:

1. Push the branch.
2. Open a PR against main.
3. Confirm devops-ci.yml runs:
* changes
* ci-workflow-lint
* ci-scripts
* ci-supply-chain
4. Confirm summaries are readable and artifacts upload where expected.
5. Confirm no Node 20 warnings except unavoidable platform-side Dependabot noise.
6. Confirm overall PR checks are green and no required check is stuck in "Expected" state.

### 2. Reusable `python-quality.yml` Consumer Test
Use examples/call-python-quality.yml in a small app repo.

Steps:

1. Copy examples/call-python-quality.yml into an app repo as .github/workflows/quality.yml.
2. Point uses: to this branch or a test tag.
3. Run on a PR with strictness_level: Medium.
4. Confirm jobs run in the expected DAG:
* quality-shield
* quality-static + quality-supply-chain
* quality-test after static
* quality-report after static/supply/test
* optional PR comment
5. Check that .devops resolves from github.workflow_ref when devops_repository / devops_ref are omitted.
6. Confirm gates_passed is emitted as a workflow_call output and has the expected boolean string.

### 3. High Strictness Failure/Success Path
Run the reusable workflow with strictness_level: High.

Steps:

1. Use an app repo with full expected artifacts.
2. Confirm High passes when all required reports exist.
3. Remove or break one required artifact path in a test branch.
4. Confirm High fails closed with a clear gate row in gates.json.
5. Confirm Low/Medium do not fail for the same missing optional artifact where design says they should skip.

### 4. Optional DAST Path
Only run this if the app has a working Docker Compose service.

Steps:

1. Set enable_dast: true.
2. Ensure docker_compose_file points to a valid compose file.
3. Ensure the service responds at dast_target_url.
4. Confirm ZAP baseline and Locust run, and DAST artifacts upload.
5. Re-run with enable_dast: false and confirm quality-dast is skipped while the rest of pipeline still completes.

### 5. Release Path
Use a disposable repo/tag or dry-run branch first.

Steps:

1. Configure a caller workflow to run on push.tags.
2. Push a tag like v0.0.1-test only if your release rules allow it, or use a real SemVer test tag in a sandbox repo.
3. Confirm release-github only runs on tag refs and only after gates pass.
4. Confirm the quality bundle is attached to the release.
5. Negative test: push a non-SemVer-like tag and confirm release job does not publish.

### 6. Scheduled Maintenance Workflow
Run devops-scheduled.yml manually.

Steps:

1. Go to GitHub Actions -> DevOps Scheduled.
2. Run workflow_dispatch.
3. Confirm workflow lint, Scorecard, Mutmut, and EOL jobs behave as expected.
4. Confirm Mutmut artifacts upload and EOL issue logic does not create duplicate issues.
5. Optional push-path test: push a branch/PR changing only .github/config/python-support-versions.json and verify EOL-only path behavior is preserved as documented.

### 7. Publish PyPI Workflow
Only run when ready to publish.

Steps:

1. Confirm PyPI Trusted Publishing is configured for this repo.
2. Confirm GitHub environment pypi exists and has expected approvals.
3. Run publish-pypi.yml manually.
4. Confirm OIDC publishing succeeds and package metadata is correct.

### 8. Fork / Token-Scope Behavior
Validate behavior differences between same-repo PRs and fork PRs.

Steps:

1. Open a same-repo PR and verify PR comment publication path works when enabled.
2. Open (or simulate) a fork PR and verify token-restricted paths degrade safely (no secrets required, no unsafe comment failure loops).
3. Confirm required checks still pass/fail deterministically under fork token permissions.
