"""Load High-tier floors from the pinned guardrails thresholds YAML."""

from __future__ import annotations

from pathlib import Path


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
    }


def load_python_floors(repo_root: Path) -> dict[str, float]:
    """Org floors from ``docs/guardrails/python/profile.thresholds.yml``, or defaults."""
    path = repo_root / 'docs' / 'guardrails' / 'python' / 'profile.thresholds.yml'
    defaults = default_python_floors()
    if not path.is_file():
        return defaults
    parsed = parse_threshold_yaml(path.read_text(encoding='utf-8'))
    return {**defaults, **{k: parsed[k] for k in defaults if k in parsed}}
