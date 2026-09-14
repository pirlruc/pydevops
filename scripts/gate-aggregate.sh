#!/usr/bin/env bash
# Collect-then-fail (CI-035). Usage:
#   ADVISORY=true|false bash scripts/gate-aggregate.sh name=outcome ...
#
# Findings (outcome != success) fail the job unless ADVISORY=true.
# Callers must resolve thresholds and required tools in steps *without*
# continue-on-error so a missing tool never reaches this aggregator.
set -euo pipefail

ADVISORY="${ADVISORY:-false}"
failed=()
for pair in "$@"; do
  name="${pair%%=*}"
  outcome="${pair#*=}"
  if [[ -z "${name}" || "${name}" == "${pair}" ]]; then
    echo "usage: ADVISORY=true|false $0 name=outcome ..." >&2
    exit 2
  fi
  if [[ "${outcome}" == "skipped" || "${outcome}" == "cancelled" ]]; then
    continue
  fi
  if [[ "${outcome}" != "success" ]]; then
    failed+=("${name}(${outcome})")
  fi
done

if [[ ${#failed[@]} -eq 0 ]]; then
  echo "All collected gates passed."
  exit 0
fi

echo "Collected gate failures: ${failed[*]}"
if [[ "${ADVISORY}" == "true" ]]; then
  echo "advisory — not failing the job (pass blocking=true to enforce findings)."
  exit 0
fi
echo "::error::Quality gates failed: ${failed[*]}"
exit 1
