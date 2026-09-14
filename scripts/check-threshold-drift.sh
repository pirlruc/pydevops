#!/bin/sh
# Fail if vendored Python / CI / supply-chain thresholds drift from the
# pinned guardrails submodule. POSIX sh (CI-022 / CI-035).
set -eu

SCRIPT_DIR="$(dirname "$0")"
SCRIPT_DIR="$(cd "${SCRIPT_DIR}" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

extract() {
  grep -E '^[a-z_]+:' "$1" | sed 's/[[:space:]]*#.*//' | sed 's/[[:space:]]*$//'
}

check_pair() {
  vended="$1"
  upstream="$2"
  label="$3"
  if [ ! -f "${vended}" ]; then
    echo "error: missing ${vended}" >&2
    return 1
  fi
  if [ ! -f "${upstream}" ]; then
    echo "error: guardrails submodule missing at ${upstream} (CI-022 / CI-035)" >&2
    return 1
  fi
  tmp_u="$(mktemp)"
  tmp_v="$(mktemp)"
  extract "${upstream}" > "${tmp_u}"
  extract "${vended}" > "${tmp_v}"
  if ! diff -u "${tmp_u}" "${tmp_v}"; then
    rm -f "${tmp_u}" "${tmp_v}"
    echo "error: ${label} drifted from ${upstream}" >&2
    return 1
  fi
  rm -f "${tmp_u}" "${tmp_v}"
  echo "Thresholds in sync: ${label}"
}

check_pair \
  "${ROOT}/scripts/python.profile.thresholds.yml" \
  "${ROOT}/docs/guardrails/python/profile.thresholds.yml" \
  "scripts/python.profile.thresholds.yml"
check_pair \
  "${ROOT}/scripts/ci.profile.thresholds.yml" \
  "${ROOT}/docs/guardrails/ci/profile.thresholds.yml" \
  "scripts/ci.profile.thresholds.yml"
check_pair \
  "${ROOT}/scripts/supply-chain.profile.thresholds.yml" \
  "${ROOT}/docs/guardrails/supply-chain/profile.thresholds.yml" \
  "scripts/supply-chain.profile.thresholds.yml"
