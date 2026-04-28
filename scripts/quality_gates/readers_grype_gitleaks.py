"""Parse Grype and Gitleaks JSON artifacts."""

from __future__ import annotations

from pathlib import Path

from scripts.quality_gates.jsonutil import read_json


def grype_match_bucket(sev: str) -> str:
    """Classify a Grype severity string as high, medium, or ignore."""
    s = sev.lower()
    if s in ('high', 'critical'):
        return 'high'

    if s == 'medium':
        return 'medium'

    return 'other'


def count_one_grype_match(m: dict, highs: int, mediums: int) -> tuple[int, int]:
    """Update counts from one Grype match object."""
    vuln = m.get('vulnerability')
    if not isinstance(vuln, dict):
        vuln = {}

    raw = vuln.get('severity', '') or ''
    bucket = grype_match_bucket(str(raw))
    if bucket == 'high':
        return highs + 1, mediums

    if bucket == 'medium':
        return highs, mediums + 1

    return highs, mediums


def _grype_matches(data: object) -> list[dict] | None:
    """Return validated Grype matches as dict objects, or None on invalid shape."""
    if not isinstance(data, dict):
        return None

    matches = data.get('matches')
    if not isinstance(matches, list):
        return None

    return [m for m in matches if isinstance(m, dict)]


def grype_severities(root: Path) -> tuple[int, int] | None:
    """Count high/critical and medium vulnerabilities from grype.json.

    Returns ``None`` when the file is missing, JSON is invalid, or root is not an object,
    so the gate can fail closed instead of under-counting vulnerabilities.
    """
    matches = _grype_matches(read_json(root / 'grype.json'))
    if matches is None:
        return None

    highs = mediums = 0
    for m in matches:
        highs, mediums = count_one_grype_match(m, highs, mediums)

    return highs, mediums


def gitleaks_findings(root: Path) -> int:
    """Count Gitleaks findings from JSON array."""
    data = read_json(root / 'gitleaks.json')
    if isinstance(data, list):
        return len(data)

    return 0
