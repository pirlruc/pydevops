"""Load High-tier floors from the pinned guardrails thresholds YAML.

CI-022 / CI-035: a present file with a missing or empty required key fails
closed. A missing guardrails checkout is the deliberate consumer fallback —
it prints a loud warning and returns baked-in High floors rather than
pretending the YAML was read.
"""

from __future__ import annotations

import sys
from pathlib import Path

PYTHON_FLOOR_KEYS: tuple[str, ...] = (
    'statement_coverage',
    'branch_coverage',
    'doc_coverage',
    'max_cyclomatic_complexity',
    'avg_cyclomatic_complexity',
    'min_maintainability_index',
    'avg_maintainability_index',
)

# Self-CI (devops-ci.yml) is stricter than the High floor of 8. Being stricter
# than the org default needs no deviation record (PY-CPLX-001).
SELF_CI_MAX_CYCLOMATIC = 5.0

CI_THRESHOLD_KEYS: tuple[str, ...] = (
    'ci_image_max_age_days',
    'ci_job_timeout_minutes_max',
    'security_rescan_interval_days',
)


class ThresholdError(RuntimeError):
    """Missing threshold file/key or empty value (CI-022)."""


def parse_threshold_yaml(text: str) -> dict[str, float]:
    """Minimal ``key: value`` YAML reader (no PyYAML dependency)."""
    out: dict[str, float] = {}
    for raw in text.splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line or ':' not in line:
            continue
        key, _, rest = line.partition(':')
        key = key.strip()
        val = rest.strip().split()[0] if rest.strip() else ''
        if not key or not val:
            continue
        try:
            out[key] = float(val)
        except ValueError:
            continue
    return out


def default_python_floors() -> dict[str, float]:
    """Baked-in High floors matching org profile when the YAML is absent."""
    return {
        'statement_coverage': 95.0,
        'branch_coverage': 95.0,
        'doc_coverage': 95.0,
        'max_cyclomatic_complexity': 8.0,
        'avg_cyclomatic_complexity': 5.0,
        'min_maintainability_index': 40.0,
        'avg_maintainability_index': 60.0,
        'lint_exception_max_days': 14.0,
    }


def _require_keys(parsed: dict[str, float], keys: tuple[str, ...], path: Path) -> dict[str, float]:
    """Return ``parsed`` subset for ``keys``, or raise on missing/empty."""
    missing = [k for k in keys if k not in parsed]
    if missing:
        raise ThresholdError(f"missing threshold key(s) {missing} in {path}")
    return {k: parsed[k] for k in keys}


def _first_existing(candidates: list[Path]) -> Path | None:
    """Return the first existing path in ``candidates``."""
    for path in candidates:
        if path.is_file():
            return path
    return None


def python_threshold_candidates(repo_root: Path) -> list[Path]:
    """Guardrails submodule first, then the vendored copy (sparse-checkout CI)."""
    return [
        repo_root / 'docs' / 'guardrails' / 'python' / 'profile.thresholds.yml',
        repo_root / 'scripts' / 'python.profile.thresholds.yml',
    ]


def ci_threshold_candidates(repo_root: Path) -> list[Path]:
    """CI pack: submodule first, then vendored copy."""
    return [
        repo_root / 'docs' / 'guardrails' / 'ci' / 'profile.thresholds.yml',
        repo_root / 'scripts' / 'ci.profile.thresholds.yml',
    ]


def require_python_floors(path: Path) -> dict[str, float]:
    """Floors from one YAML file. Missing required keys fail closed (CI-022)."""
    parsed = parse_threshold_yaml(path.read_text(encoding='utf-8'))
    return _require_keys(parsed, PYTHON_FLOOR_KEYS, path)


def load_python_floors(repo_root: Path, *, allow_missing_checkout: bool = True) -> dict[str, float]:
    """Org floors from guardrails / vendored YAML.

    When no file exists and ``allow_missing_checkout`` is true (consumer without
    a guardrails tree), warn on stderr and return :func:`default_python_floors`.
    Otherwise missing file or missing key fails closed.
    """
    path = _first_existing(python_threshold_candidates(repo_root))
    defaults = default_python_floors()
    extra_keys = ('lint_exception_max_days',)
    required = PYTHON_FLOOR_KEYS
    if path is None:
        msg = (
            'CI-022: docs/guardrails/python/profile.thresholds.yml and '
            'scripts/python.profile.thresholds.yml are missing'
        )
        if allow_missing_checkout:
            print(f'warning: {msg}; using baked-in High floors', file=sys.stderr)
            return defaults
        raise ThresholdError(msg)
    parsed = parse_threshold_yaml(path.read_text(encoding='utf-8'))
    floors = _require_keys(parsed, required, path)
    for key in extra_keys:
        if key in parsed:
            floors[key] = parsed[key]
        else:
            floors[key] = defaults[key]
            print(
                f'warning: optional key {key!r} missing in {path}; using {floors[key]}',
                file=sys.stderr,
            )
    return floors


def load_ci_thresholds(repo_root: Path, *, allow_missing_checkout: bool = True) -> dict[str, float]:
    """CI pack thresholds (CI-027 / CI-003 / CI-029)."""
    path = _first_existing(ci_threshold_candidates(repo_root))
    if path is None:
        msg = (
            'CI-022: docs/guardrails/ci/profile.thresholds.yml and '
            'scripts/ci.profile.thresholds.yml are missing'
        )
        if allow_missing_checkout:
            print(f'warning: {msg}; skipping CI pack', file=sys.stderr)
            return {}
        raise ThresholdError(msg)
    parsed = parse_threshold_yaml(path.read_text(encoding='utf-8'))
    return _require_keys(parsed, CI_THRESHOLD_KEYS, path)


def self_ci_max_cyclomatic(floors: dict[str, float]) -> float:
    """Maintainer CI CC cap: min(org High, 5). Stricter than High; no deviation."""
    org = floors['max_cyclomatic_complexity']
    return min(org, SELF_CI_MAX_CYCLOMATIC)
