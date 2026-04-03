"""Parse Grype and Gitleaks JSON artifacts."""

from __future__ import annotations

from pathlib import Path

from scripts.quality_gates.jsonutil import read_json


def grype_match_bucket(sev: str) -> str:
    """Classify a Grype severity string as high, medium, or ignore."""
    s = sev.lower()
    if s in ("high", "critical"):
        return "high"
    if s == "medium":
        return "medium"
    return "other"


def count_one_grype_match(m: dict, highs: int, mediums: int) -> tuple[int, int]:
    """Update counts from one Grype match object."""
    raw = (m.get("vulnerability") or {}).get("severity", "") or ""
    bucket = grype_match_bucket(str(raw))
    if bucket == "high":
        return highs + 1, mediums
    if bucket == "medium":
        return highs, mediums + 1
    return highs, mediums


def grype_severities(root: Path) -> tuple[int, int] | None:
    """Count high/critical and medium vulnerabilities from grype.json.

    Returns ``(0, 0)`` when the file is missing or JSON is invalid (same as no matches).
    Returns ``None`` when JSON parses to a non-object (e.g. list or string), so the gate
    can fail closed instead of raising ``AttributeError`` or under-counting.
    """
    data = read_json(root / "grype.json")
    if data is None:
        return 0, 0
    if not isinstance(data, dict):
        return None
    highs = mediums = 0
    for m in data.get("matches", []):
        if not isinstance(m, dict):
            continue
        highs, mediums = count_one_grype_match(m, highs, mediums)
    return highs, mediums


def gitleaks_findings(root: Path) -> int:
    """Count Gitleaks findings from JSON array."""
    data = read_json(root / "gitleaks.json")
    if isinstance(data, list):
        return len(data)
    return 0
