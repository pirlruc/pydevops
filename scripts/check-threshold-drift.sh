#!/usr/bin/env bash
# Fail if vendored Python / CI thresholds drift from the pinned guardrails submodule.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

check_pair() {
  local vended="$1"
  local upstream="$2"
  local label="$3"
  if [[ ! -f "${vended}" ]]; then
    echo "error: missing ${vended}" >&2
    exit 1
  fi
  if [[ ! -f "${upstream}" ]]; then
    echo "error: guardrails submodule missing at ${upstream} (CI-022 / CI-035)" >&2
    exit 1
  fi
  extract() {
    grep -E '^[a-z_]+:' "$1" | sed 's/[[:space:]]*#.*//' | sed 's/[[:space:]]*$//'
  }
  if ! diff -u <(extract "${upstream}") <(extract "${vended}"); then
    echo "error: ${label} drifted from ${upstream}" >&2
    exit 1
  fi
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
