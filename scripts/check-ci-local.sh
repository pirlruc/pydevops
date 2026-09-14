#!/usr/bin/env bash
# Local CI parity for pydevops (CI-008 / CMN-WF-004).
# Host PATH preferred; missing tools go to check-ci-docker.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
# shellcheck source=ci-steps.sh
# shellcheck disable=SC1091
source "${ROOT}/scripts/ci-steps.sh"

USE_DOCKER=1
for arg in "$@"; do
  if [[ "${arg}" == "--no-docker" ]]; then
    USE_DOCKER=0
  fi
done

declare -a DOCKER_STEPS=()
declare -a CI_EXECUTED=()
declare -a CI_SKIPPED=()

run_step() {
  local label="$1"
  shift
  echo "==> ${label}"
  "$@"
  CI_EXECUTED+=("${label}")
}

queue_docker() {
  local step="$1"
  local label="$2"
  DOCKER_STEPS+=("${step}")
  echo "Queuing ${label} for Docker" >&2
  CI_SKIPPED+=("${label}: Docker")
}

print_ci_gap_summary() {
  echo ""
  echo "=== CI parity summary ==="
  if ((${#CI_EXECUTED[@]} > 0)); then
    echo "Executed on host:"
    for item in "${CI_EXECUTED[@]}"; do
      echo "  - ${item}"
    done
  fi
  if ((${#CI_SKIPPED[@]} > 0)); then
    echo "Deferred to Docker or CI:"
    for item in "${CI_SKIPPED[@]}"; do
      echo "  - ${item}"
    done
  fi
  if ((${#DOCKER_STEPS[@]} > 0)) && ! command -v docker >/dev/null 2>&1; then
    echo "Start Docker and run: PYDEVOPS_DOCKER_STEPS='${DOCKER_STEPS[*]}' sh scripts/check-ci-docker.sh"
  fi
}

run_or_queue() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    run_step "${name}" dispatch_ci_step "${name}"
  else
    queue_docker "${name}" "${name}"
  fi
}

run_step "threshold drift" bash "${ROOT}/scripts/check-threshold-drift.sh"
run_step "submodule pins" sh "${ROOT}/scripts/check-submodule-pins.sh"

run_or_queue actionlint
run_or_queue shellcheck
run_or_queue hadolint
run_or_queue zizmor
run_or_queue yamllint

run_step "markdown links" python3 "${ROOT}/scripts/lint-doc-links.py"

if ((${#DOCKER_STEPS[@]} > 0)); then
  if [[ "${USE_DOCKER}" == "1" ]]; then
    run_step "Docker CI gaps" env PYDEVOPS_DOCKER_STEPS="${DOCKER_STEPS[*]}" sh "${ROOT}/scripts/check-ci-docker.sh"
    CI_SKIPPED=()
  else
    echo "error: --no-docker set but tools missing on host: ${DOCKER_STEPS[*]}" >&2
    exit 1
  fi
fi

print_ci_gap_summary
echo "Local CI parity finished."
