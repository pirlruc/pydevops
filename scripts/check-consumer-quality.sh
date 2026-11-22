#!/bin/sh
# Run scripts/ci_run_quality.sh inside the published ci-python image.
#
# Usage:
#   sh scripts/check-consumer-quality.sh /path/to/app
#
# The image is private. Log in first: docker login ghcr.io
# STRICTNESS_LEVEL and QUALITY_PHASES are forwarded when set.
set -eu

APP="${1:?pass the application checkout}"
APP="$(cd "${APP}" && pwd)"
SCRIPT_DIR="$(dirname "$0")"
SCRIPT_DIR="$(cd "${SCRIPT_DIR}" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE="${PYDEVOPS_CONSUMER_IMAGE:-ghcr.io/pirlruc/ci-python@sha256:894d5ae1d9bd55d68262f4ed65cd6f57d7186038d7e8e8668dba443ee0ebfbbd}"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker is required" >&2
    exit 1
fi
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
    echo "==> Pulling ${IMAGE}"
    docker pull "${IMAGE}"
fi

echo "==> Quality bundle in ${IMAGE}"
docker run --rm \
    -v "${APP}:/app" \
    -v "${ROOT}:/devops:ro" \
    -w /app \
    -e "STRICTNESS_LEVEL=${STRICTNESS_LEVEL:-Medium}" \
    -e "QUALITY_PHASES=${QUALITY_PHASES:-all}" \
    -e "QUALITY_OUTPUT_DIR=/tmp/quality-output" \
    -e "APP_DIR=/app" \
    --user root \
    "${IMAGE}" \
    bash /devops/scripts/ci_run_quality.sh
