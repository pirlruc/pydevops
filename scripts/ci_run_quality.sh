#!/usr/bin/env bash
# Run quality tools against the app checkout; write artifacts under QUALITY_OUTPUT_DIR.
# QUALITY_PHASES: comma-separated static,security,test or "all" (default) for everything.
set -euo pipefail

APP_DIR="${APP_DIR:-.}"
DEVOPS_DIR="${DEVOPS_DIR:-.devops}"
cd "$APP_DIR"
OUT="${QUALITY_OUTPUT_DIR:-quality-output}"
# Resolve relative output dir against the app root (after cd) so writes match mkdir.
if [[ "$OUT" != /* ]]; then
  OUT="$(pwd)/$OUT"
fi
mkdir -p "$OUT"

# High strictness: omit artifact files when a required tool is missing so gates fail closed.
# Low/Medium: some missing CLIs still write minimal placeholders ({}, [], etc.) so downstream
# parsers get valid JSON; security tools (bandit, pip-audit, grype, syft, jscpd without npx)
# omit files instead of success-shaped payloads. High also omits pydoclint.txt when pydoclint is
# missing (required in HIGH_REQUIRED_FILES). See each section below.
_high=0
case "$(echo "${STRICTNESS_LEVEL:-Medium}" | tr '[:upper:]' '[:lower:]')" in
  high) _high=1 ;;
esac

# When the DevOps repo is checked out into .devops/, exclude it from app scans
IGNORE_PYLINT="${IGNORE_PYLINT:-^\\.devops/}"
RUFF_EXCL="${RUFF_EXCLUDE:-.devops,.git,.venv,__pycache__,htmlcov,dist,build}"
PYTEST_IGNORE="${PYTEST_IGNORE:-.devops}"
IFS=',' read -ra RUFF_EXCL_ITEMS <<< "$RUFF_EXCL"
RUFF_EXCLUDE_ARGS=()
for _pat in "${RUFF_EXCL_ITEMS[@]}"; do
  _trimmed="${_pat// /}"
  if [[ -n "$_trimmed" ]]; then
    RUFF_EXCLUDE_ARGS+=(--exclude "$_trimmed")
  fi
done

# shellcheck disable=SC2155
QUALITY_PHASES_RAW="${QUALITY_PHASES:-all}"
_phases_norm=$(echo "${QUALITY_PHASES_RAW}" | tr '[:upper:]' '[:lower:]' | tr -d ' ')

want_static=0
want_security=0
want_test=0
if [[ -z "${_phases_norm}" ]] || [[ "${_phases_norm}" == "all" ]]; then
  want_static=1
  want_security=1
  want_test=1
else
  IFS=',' read -ra _parts <<< "${_phases_norm}"
  for p in "${_parts[@]}"; do
    case "${p// /}" in
      static) want_static=1 ;;
      security) want_security=1 ;;
      test) want_test=1 ;;
    esac
  done
fi

if [[ "${want_static}" == "1" ]]; then
  # CLOC (SLOC / comment lines for metrics)
  if command -v cloc >/dev/null 2>&1; then
    cloc . --json --out="$OUT/cloc.json" --include-lang=Python --exclude-dir=.devops,.git,.venv,dist,build,htmlcov || true
  else
    if [[ "${_high}" == "1" ]]; then
      rm -f "$OUT/cloc.json"
    else
      echo '{}' >"$OUT/cloc.json"
    fi
  fi

  # Ruff (optional; workflow may run Ruff with QaaS docstring config and set SKIP_RUFF_IN_BUNDLE=1)
  if [[ "${SKIP_RUFF_IN_BUNDLE:-0}" == "1" ]]; then
    :
  elif command -v ruff >/dev/null 2>&1; then
    ruff check . "${RUFF_EXCLUDE_ARGS[@]}" --output-format=json >"$OUT/ruff.json" 2>"$OUT/ruff.stderr" || true
    ruff format --check . "${RUFF_EXCLUDE_ARGS[@]}" >"$OUT/ruff_format.txt" 2>&1 || true
  else
    if [[ "${_high}" == "1" ]]; then
      rm -f "$OUT/ruff.json"
    else
      echo '[]' >"$OUT/ruff.json"
    fi
  fi

  # Pylint (JSON + score line for quality_gates)
  if command -v pylint >/dev/null 2>&1; then
    pylint . --ignore-paths="$IGNORE_PYLINT" --output-format=json --exit-zero >"$OUT/pylint.json" 2>"$OUT/pylint.stderr" || true
    pylint . --ignore-paths="$IGNORE_PYLINT" --exit-zero 2>&1 | tee "$OUT/pylint_full.txt" >/dev/null || true
    if grep -oE 'rated at [0-9.]+/10' "$OUT/pylint_full.txt" | tail -1 >"$OUT/pylint_score.txt" 2>/dev/null; then
      :
    else
      echo "rated at 0/10" >"$OUT/pylint_score.txt"
    fi
  else
    if [[ "${_high}" == "1" ]]; then
      rm -f "$OUT/pylint.json" "$OUT/pylint_score.txt"
    else
      echo '[]' >"$OUT/pylint.json"
      echo "rated at 0/10" >"$OUT/pylint_score.txt"
    fi
  fi

  if command -v pylint-json2html >/dev/null 2>&1 && [[ -s "$OUT/pylint.json" ]]; then
    pylint-json2html -f "$OUT/pylint.json" -o "$OUT/pylint_report.html" 2>/dev/null || true
  fi

  # Mypy (always produce reports for quality gates; exit code ignored)
  if command -v mypy >/dev/null 2>&1; then
    mkdir -p "$OUT/mypy-reports/lineprecision" "$OUT/mypy-reports/anyexprs"
    mypy . --exclude '\.devops' --show-error-codes \
      --lineprecision-report "$OUT/mypy-reports/lineprecision" \
      --any-exprs-report "$OUT/mypy-reports/anyexprs" \
      >"$OUT/mypy.txt" 2>&1 || true
  else
    echo "mypy not installed" >"$OUT/mypy.txt"
    if [[ "${_high}" == "1" ]]; then
      rm -rf "$OUT/mypy-reports"
    fi
  fi

  # pydoclint
  if command -v pydoclint >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    pydoclint . ${PYDOCLINT_FLAGS:-} >"$OUT/pydoclint.txt" 2>&1 || true
  else
    if [[ "${_high}" == "1" ]]; then
      rm -f "$OUT/pydoclint.txt"
    else
      echo "pydoclint not installed" >"$OUT/pydoclint.txt"
    fi
  fi

  # Interrogate (docstring coverage)
  if command -v interrogate >/dev/null 2>&1; then
    interrogate . -vv -e .devops >"$OUT/interrogate.txt" 2>&1 || true
  else
    if [[ "${_high}" == "1" ]]; then
      rm -f "$OUT/interrogate.txt"
    else
      echo "interrogate not installed" >"$OUT/interrogate.txt"
    fi
  fi

  # jscpd (pinned version from DevOps package.json when present; else fallback pin)
  if command -v npx >/dev/null 2>&1; then
    JSCPD_PREFIX="${DEVOPS_DIR}/.github/dependencies/jscpd"
    if [[ -f "${JSCPD_PREFIX}/package.json" ]]; then
      JSCPD_VER=$(
        python3 -c "import json, re, sys; v=json.load(open(sys.argv[1]))['dependencies']['jscpd']; m=re.search(r'(\d+\.\d+\.\d+)', str(v)); print(m.group(1) if m else str(v).strip())" "${JSCPD_PREFIX}/package.json" 2>/dev/null || true
      )
      [[ -z "${JSCPD_VER}" ]] && JSCPD_VER="5.2.0"
      npx --yes "jscpd@${JSCPD_VER}" . --reporters json --output "$OUT" --format python --min-lines 5 --min-tokens 50 2>"$OUT/jscpd.stderr" || true
    else
      npx --yes jscpd@5.2.0 . --reporters json --output "$OUT" --format python --min-lines 5 --min-tokens 50 2>"$OUT/jscpd.stderr" || true
    fi
    if [[ -f "$OUT/jscpd-report.json" ]]; then
      :
    elif [[ -f jscpd-report.json ]]; then
      mv jscpd-report.json "$OUT/" 2>/dev/null || true
    fi
    if [[ ! -f "$OUT/jscpd-report.json" ]]; then
      echo "jscpd did not produce ${OUT}/jscpd-report.json (see ${OUT}/jscpd.stderr)" >&2
    fi
  else
    rm -f "$OUT/jscpd-report.json"
  fi

  # Radon
  if command -v radon >/dev/null 2>&1; then
    radon cc -j . >"$OUT/radon_cc.json" 2>"$OUT/radon_cc.stderr" || true
    radon mi -j . >"$OUT/radon_mi.json" 2>"$OUT/radon_mi.stderr" || true
  else
    if [[ "${_high}" == "1" ]]; then
      rm -f "$OUT/radon_cc.json" "$OUT/radon_mi.json"
    else
      echo '{}' >"$OUT/radon_cc.json"
      echo '{}' >"$OUT/radon_mi.json"
    fi
  fi
fi

if [[ "${want_security}" == "1" ]]; then
  # Dependency health: uv lockfile consistency (with deptry below for unused/missing deps)
  if command -v uv >/dev/null 2>&1 && [[ -f pyproject.toml ]]; then
    if [[ -f uv.lock ]]; then
      (uv lock --check >"$OUT/uv_lock_check.txt" 2>&1) || true
    else
      echo "No uv.lock in app root; skipped uv lock --check" >"$OUT/uv_lock_check.txt"
    fi
  else
    echo "uv or pyproject.toml missing; skipped uv lock --check" >"$OUT/uv_lock_check.txt"
  fi

  # Bandit
  if command -v bandit >/dev/null 2>&1; then
    bandit -q -r . -x ./.devops -f json -o "$OUT/bandit.json" 2>"$OUT/bandit.stderr" || true
  else
    rm -f "$OUT/bandit.json"
  fi

  # deptry
  if command -v deptry >/dev/null 2>&1; then
    deptry . >"$OUT/deptry.txt" 2>&1 || true
  else
    echo "deptry not installed" >"$OUT/deptry.txt"
  fi

  # pip-audit
  if command -v pip-audit >/dev/null 2>&1; then
    pip-audit --format json --output "$OUT/pip_audit.json" 2>"$OUT/pip_audit.stderr" || true
  else
    rm -f "$OUT/pip_audit.json"
  fi

  # Syft SBOMs
  if command -v syft >/dev/null 2>&1; then
    syft scan dir:. -o cyclonedx-json="$OUT/sbom-cyclonedx.json" 2>"$OUT/syft.stderr" || true
    syft scan dir:. -o spdx-json="$OUT/sbom-spdx.json" 2>>"$OUT/syft.stderr" || true
  else
    rm -f "$OUT/sbom-cyclonedx.json" "$OUT/sbom-spdx.json"
  fi

  # Grype (SBOM)
  if command -v grype >/dev/null 2>&1 && [[ -f "$OUT/sbom-cyclonedx.json" ]]; then
    grype "sbom:$OUT/sbom-cyclonedx.json" -o json >"$OUT/grype.json" 2>"$OUT/grype.stderr" || true
  else
    rm -f "$OUT/grype.json"
  fi
fi

if [[ "${want_test}" == "1" ]]; then
  # Pytest + coverage (expects deps installed in app venv)
  if command -v pytest >/dev/null 2>&1; then
    _py_rc=0
    pytest \
      --ignore="$PYTEST_IGNORE" \
      --cov=. \
      --cov-branch \
      --cov-report=term-missing \
      --cov-report=html:"$OUT/htmlcov" \
      --cov-report=json:"$OUT/coverage.json" \
      -q \
      >"$OUT/pytest.txt" 2>&1 || _py_rc=$?
    printf "%s\n" "$_py_rc" >"$OUT/pytest_exit_code.txt"
  else
    if [[ "${_high}" == "1" ]]; then
      rm -f "$OUT/coverage.json" "$OUT/pytest.txt" "$OUT/pytest_exit_code.txt"
    else
      echo '{"totals":{"percent_covered":0,"percent_branches_covered":0}}' >"$OUT/coverage.json"
      echo "pytest not installed" >"$OUT/pytest.txt"
    fi
  fi
fi

echo "ci_run_quality.sh finished (phases=${QUALITY_PHASES_RAW}); outputs in $OUT"
