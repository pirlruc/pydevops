#!/bin/sh
# Shared host/Docker CI step bodies (CMN-WF-003-T2). POSIX sh — Alpine ci-lint
# has no bash. Sourced by check-ci-local.sh and check-ci-docker.sh.
#
# shellcheck shell=sh

run_actionlint() {
  files="$(find .github/workflows \( -name "*.yml" -o -name "*.yaml" \) 2>/dev/null)"
  if [ -z "${files}" ]; then
    echo "No workflows to lint"
    return 0
  fi
  n="$(printf '%s\n' "${files}" | grep -c .)"
  if [ "${n}" -gt 40 ]; then
    echo "CI-035: ${n} workflow files exceeds actionlint cap of 40" >&2
    return 1
  fi
  # shellcheck disable=SC2086
  actionlint ${files}
}

run_shellcheck() {
  files="$(find scripts -name "*.sh" 2>/dev/null)"
  if [ -z "${files}" ]; then
    echo "No shell scripts"
    return 0
  fi
  # shellcheck disable=SC2086
  shellcheck ${files}
}

run_hadolint() {
  files="$(find docker -name "Dockerfile*" 2>/dev/null)"
  if [ -z "${files}" ]; then
    echo "No Dockerfiles to lint"
    return 0
  fi
  # shellcheck disable=SC2086
  hadolint ${files}
}

run_zizmor() {
  zizmor --min-severity=low .github/workflows
}

run_yamllint() {
  set +e
  yamllint -d relaxed .github/workflows docs
  yc=$?
  set -e
  if [ "${yc}" -eq 0 ]; then
    return 0
  fi
  if [ "${COMMONDEVOPS_ADVISORY:-0}" = "1" ]; then
    echo "yamllint findings (advisory — continuing)"
    return 0
  fi
  echo "yamllint findings (blocking). Set COMMONDEVOPS_ADVISORY=1 to continue." >&2
  return "${yc}"
}

dispatch_ci_step() {
  step="$1"
  case "${step}" in
    actionlint) run_actionlint ;;
    shellcheck) run_shellcheck ;;
    hadolint) run_hadolint ;;
    zizmor) run_zizmor ;;
    yamllint) run_yamllint ;;
    *)
      echo "Unknown step: ${step}" >&2
      return 2
      ;;
  esac
}
