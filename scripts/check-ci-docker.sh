#!/bin/sh
# Thin env wrapper around the vendored commondevops POSIX runner (CMN-WF-004).
set -eu

SCRIPT_DIR="$(dirname "$0")"
SCRIPT_DIR="$(cd "${SCRIPT_DIR}" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

COMMONDEVOPS_CI_IMAGE="${PYDEVOPS_CI_IMAGE:-ghcr.io/pirlruc/ci-lint:5.1.1@sha256:35a82a43839e0969dc7c44d63c36b5c97cdefb20c6d3112255f52c09444042a1}"
COMMONDEVOPS_DOCKER_STEPS="${PYDEVOPS_DOCKER_STEPS:?PYDEVOPS_DOCKER_STEPS is required}"
COMMONDEVOPS_BUILD_LOCAL="${PYDEVOPS_BUILD_LOCAL:-0}"
export COMMONDEVOPS_CI_IMAGE COMMONDEVOPS_DOCKER_STEPS COMMONDEVOPS_BUILD_LOCAL

IMAGE="${COMMONDEVOPS_CI_IMAGE}"
if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for host-unavailable CI checks" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker engine is not running" >&2
  exit 1
fi
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "==> Pulling ${IMAGE}"
  if ! docker pull "${IMAGE}"; then
    if docker image inspect ci-lint:alpine-local >/dev/null 2>&1; then
      echo "digest pin unavailable; using ci-lint:alpine-local" >&2
      IMAGE="ci-lint:alpine-local"
    else
      echo "error: cannot pull digest-pinned ${IMAGE}" >&2
      echo "Set PYDEVOPS_CI_IMAGE to a local tag (e.g. ci-lint:alpine-local)" >&2
      exit 1
    fi
  fi
fi

echo "==> Running in Docker (${IMAGE}): ${COMMONDEVOPS_DOCKER_STEPS}"
docker run --rm \
  -v "${ROOT}:/workspace:ro" \
  -w /workspace \
  -e "COMMONDEVOPS_DOCKER_STEPS=${COMMONDEVOPS_DOCKER_STEPS}" \
  "${IMAGE}" \
  sh -c '
    set -eu
    . ./scripts/ci-steps.sh
    for step in ${COMMONDEVOPS_DOCKER_STEPS}; do
      echo "==> ${step}"
      dispatch_ci_step "${step}"
    done
  '
