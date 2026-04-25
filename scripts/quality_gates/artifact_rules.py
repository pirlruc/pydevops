"""Static validation rules for required High-tier artifacts."""

from __future__ import annotations

from typing import Any

JSON_SHAPES: dict[str, tuple[type[Any] | tuple[type[Any], ...], str]] = {
    'cloc.json': (dict, 'cloc.json must be a JSON object'),
    'coverage.json': (dict, 'coverage.json must be a JSON object'),
    'pylint.json': (list, 'pylint.json must be a JSON array'),
    'ruff.json': ((list, dict), 'ruff.json must be array or object'),
    'gitleaks.json': (list, 'gitleaks.json must be a JSON array'),
    'semgrep.sarif': (dict, 'semgrep.sarif must be a JSON object (SARIF)'),
    'bandit.json': (dict, 'bandit.json must be a JSON object'),
    'pip_audit.json': (list, 'pip_audit.json must be a JSON array'),
    'grype.json': (dict, 'grype.json must be a JSON object'),
    'radon_cc.json': (dict, 'radon_cc.json must be a JSON object'),
    'radon_mi.json': (dict, 'radon_mi.json must be a JSON object'),
}

JSON_REQUIRED_PATHS: dict[str, list[tuple[tuple[str, ...], str]]] = {
    'bandit.json': [(('results',), 'bandit.json missing results')],
    'cloc.json': [(('Python',), 'cloc.json missing Python stats')],
    'coverage.json': [
        (('totals',), 'coverage.json missing totals'),
        (('totals', 'percent_covered'), 'coverage.json missing percent_covered'),
    ],
}


def json_path_present(data: Any, path: tuple[str, ...]) -> bool:
    """Return whether a nested key-path exists and ends in a non-None value."""
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return False

        cur = cur[key]

    return cur is not None


def json_shape_error(data: Any, name: str) -> str | None:
    """Return a shape-validation error string for ``name``, if any."""
    expected = JSON_SHAPES.get(name)
    if expected is None:
        return None

    return None if isinstance(data, expected[0]) else expected[1]


def first_missing_required_path(data: Any, name: str) -> str | None:
    """Return the first missing required-path error for ``name``, if any."""
    for req_path, message in JSON_REQUIRED_PATHS.get(name, []):
        if not json_path_present(data, req_path):
            return message

    return None
