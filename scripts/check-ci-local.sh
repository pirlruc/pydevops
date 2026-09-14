#!/bin/sh
# Local CI parity for pydevops (CI-008 / CMN-WF-004).
# POSIX sh — Alpine ci-lint has no bash.
#
# Host PATH tools preferred; missing tools deferred to check-ci-docker.sh.
#
# Usage:
#   sh scripts/check-ci-local.sh
#   sh scripts/check-ci-local.sh --no-docker
set -eu

SCRIPT_DIR="$(dirname "$0")"
SCRIPT_DIR="$(cd "${SCRIPT_DIR}" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

# shellcheck source=scripts/ci-steps.sh
. "${SCRIPT_DIR}/ci-steps.sh"

USE_DOCKER=1
for arg in "$@"; do
  if [ "${arg}" = "--no-docker" ]; then
    USE_DOCKER=0
  fi
done

DOCKER_STEPS=""
EXECUTED=""
MISSING=""

queue_docker() {
  name="$1"
  echo "→ ${name} missing on host; queue Docker"
  DOCKER_STEPS="${DOCKER_STEPS} ${name}"
  MISSING="${MISSING} ${name}"
}

run_or_queue() {
  name="$1"
  echo "==> ${name}"
  if command -v "${name}" >/dev/null 2>&1; then
    echo "→ ${name} (host)"
    dispatch_ci_step "${name}"
    EXECUTED="${EXECUTED} ${name}"
    return 0
  fi
  queue_docker "${name}"
}

echo "==> threshold drift"
sh "${SCRIPT_DIR}/check-threshold-drift.sh"
echo "==> submodule pins"
sh "${SCRIPT_DIR}/check-submodule-pins.sh"

run_or_queue actionlint
run_or_queue shellcheck
run_or_queue hadolint
run_or_queue zizmor
run_or_queue yamllint

echo "==> markdown links"
python3 "${SCRIPT_DIR}/lint-doc-links.py"

if [ -n "${DOCKER_STEPS}" ]; then
  if [ "${USE_DOCKER}" = "1" ]; then
    # shellcheck disable=SC2086
    PYDEVOPS_DOCKER_STEPS="${DOCKER_STEPS}" sh "${SCRIPT_DIR}/check-ci-docker.sh"
  else
    echo "error: --no-docker set but tools missing on host:${MISSING}" >&2
    exit 1
  fi
fi

echo "Local CI parity finished. Host tools:${EXECUTED:- none}"
