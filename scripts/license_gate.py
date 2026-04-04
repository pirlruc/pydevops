#!/usr/bin/env python3
"""Fail if SPDX SBOM contains a denied license (substring match, case-insensitive)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _parse_deny_list(raw: str) -> list[str]:
    """Return normalized lowercase deny substrings from a JSON array string.

    Only string entries are used; ``null``, numbers, and other types are skipped so malformed
    values cannot become accidental patterns (e.g. ``"none"`` from ``null``).
    """
    deny = json.loads(raw)
    if not isinstance(deny, list):
        raise ValueError("LICENSE_DENY_LIST must be a JSON array")
    out: list[str] = []
    for x in deny:
        if isinstance(x, str):
            s = x.lower().strip()
            if s:
                out.append(s)
    return out


def _find_license_hits(packages: list[dict], deny_l: list[str]) -> list[str]:
    """Collect human-readable hit strings for packages matching any deny pattern."""
    hits: list[str] = []
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue
        lic = pkg.get("licenseConcluded") or pkg.get("licenseDeclared") or ""
        if not lic or lic == "NOASSERTION":
            continue
        lics = str(lic).lower()
        matched = [d for d in deny_l if d and d in lics]
        if matched:
            name = pkg.get("name", "?")
            pat = ", ".join(f"'{m}'" for m in matched)
            hits.append(f"{name}: {lic} (matched deny pattern(s) {pat})")
    return hits


def main() -> int:
    """Entry point: reads ``SPDX_SBOM_PATH`` and ``LICENSE_DENY_LIST`` from the environment."""
    sbom = Path(os.environ.get("SPDX_SBOM_PATH", "quality-output/sbom-spdx.json"))
    raw = os.environ.get("LICENSE_DENY_LIST", "[]")
    try:
        deny_l = _parse_deny_list(raw)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Invalid LICENSE_DENY_LIST: {e}", file=sys.stderr)
        return 2

    if not sbom.is_file():
        print(f"No SPDX SBOM at {sbom}; skipping license gate.")
        return 0

    try:
        data = json.loads(sbom.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        print(f"Invalid SPDX JSON at {sbom}: {e}", file=sys.stderr)
        return 3
    packages = data.get("packages", [])
    if not isinstance(packages, list):
        packages = []

    hits = _find_license_hits(packages, deny_l)
    if hits:
        print("Denied licenses detected in SPDX SBOM:", file=sys.stderr)
        for h in hits:
            print(f"  - {h}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
