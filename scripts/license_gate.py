#!/usr/bin/env python3
"""Fail if SPDX SBOM violates SC-LIC-001 deny-list or allow-list policy.

Deny list is a case-insensitive substring match (legacy). Allow list, when
non-empty, requires each asserted SPDX license to match at least one allow
pattern. Empty allow + empty deny means the gate runs but denies nothing.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def _parse_string_list(raw: str, env_name: str) -> list[str]:
    """Return normalized lowercase strings from a JSON array string."""
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError(f'{env_name} must be a JSON array')

    out: list[str] = []
    for x in parsed:
        if isinstance(x, str):
            s = x.lower().strip()
            if s:
                out.append(s)

    return out


def _parse_deny_list(raw: str) -> list[str]:
    """Return normalized lowercase deny substrings from a JSON array string."""
    return _parse_string_list(raw, 'LICENSE_DENY_LIST')


def _parse_yaml_bracket_list(text: str, key: str) -> list[str] | None:
    """Parse ``key: []`` or ``key: ["MIT"]`` from a thresholds YAML file."""
    match = re.search(
        rf'^{re.escape(key)}:\s*(\[[^\]]*\])\s*(?:#.*)?$',
        text,
        flags=re.M,
    )
    if match is None:
        return None
    try:
        return _parse_string_list(match.group(1), key)
    except (json.JSONDecodeError, ValueError):
        return []


def load_allow_list_from_thresholds(path: Path) -> list[str]:
    """Read ``license_allow_list`` from a vendored supply-chain thresholds file."""
    if not path.is_file():
        return []
    parsed = _parse_yaml_bracket_list(path.read_text(encoding='utf-8'), 'license_allow_list')
    return parsed or []


def _find_license_hits(packages: list[Any], deny_l: list[str]) -> list[str]:
    """Collect human-readable hit strings for packages matching any deny pattern."""
    hits: list[str] = []
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue

        lic = pkg.get('licenseConcluded') or pkg.get('licenseDeclared') or ''
        if not lic or lic == 'NOASSERTION':
            continue

        lics = str(lic).lower()
        matched = [d for d in deny_l if d and d in lics]
        if matched:
            name = pkg.get('name', '?')
            pat = ', '.join(f"'{m}'" for m in matched)
            hits.append(f'{name}: {lic} (matched deny pattern(s) {pat})')

    return hits


def _find_allow_misses(packages: list[Any], allow_l: list[str]) -> list[str]:
    """Collect packages whose license matches no allow-list pattern."""
    misses: list[str] = []
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue
        lic = pkg.get('licenseConcluded') or pkg.get('licenseDeclared') or ''
        if not lic or lic == 'NOASSERTION':
            continue
        lics = str(lic).lower()
        if any(a and a in lics for a in allow_l):
            continue
        name = pkg.get('name', '?')
        misses.append(f'{name}: {lic} (not on license_allow_list)')
    return misses


def _thresholds_path() -> Path:
    """Vendored SC-LIC-001 lists next to this script, else env override."""
    env = os.environ.get('LICENSE_THRESHOLDS_PATH', '')
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / 'supply-chain.profile.thresholds.yml'


class LicensePolicyError(ValueError):
    """Invalid LICENSE_* env JSON."""

    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


def _policy_lists() -> tuple[list[str], list[str]]:
    """Load deny/allow lists from env or vendored YAML."""
    raw = os.environ.get('LICENSE_DENY_LIST', '[]')
    try:
        deny_l = _parse_deny_list(raw)
    except (json.JSONDecodeError, ValueError) as e:
        raise LicensePolicyError(f'Invalid LICENSE_DENY_LIST: {e}') from e

    raw_allow = os.environ.get('LICENSE_ALLOW_LIST')
    try:
        if raw_allow is None:
            allow_l = load_allow_list_from_thresholds(_thresholds_path())
        else:
            allow_l = _parse_string_list(raw_allow, 'LICENSE_ALLOW_LIST')
    except (json.JSONDecodeError, ValueError) as e:
        raise LicensePolicyError(f'Invalid LICENSE_ALLOW_LIST: {e}') from e
    return deny_l, allow_l


def main() -> int:
    """Entry point: SPDX path plus deny/allow lists from env or thresholds YAML."""
    sbom = Path(os.environ.get('SPDX_SBOM_PATH', 'quality-output/sbom-spdx.json'))
    try:
        deny_l, allow_l = _policy_lists()
    except LicensePolicyError as e:
        print(str(e), file=sys.stderr)
        return e.code

    if not sbom.is_file():
        print(f'No SPDX SBOM at {sbom}; skipping license gate.')
        return 0

    try:
        data = json.loads(sbom.read_text(encoding='utf-8', errors='replace'))
    except json.JSONDecodeError as e:
        print(f'Invalid SPDX JSON at {sbom}: {e}', file=sys.stderr)
        return 3

    packages = data.get('packages', [])
    if not isinstance(packages, list):
        packages = []

    hits = _find_license_hits(packages, deny_l)
    if hits:
        print('Denied licenses detected in SPDX SBOM:', file=sys.stderr)
        for h in hits:
            print(f'  - {h}', file=sys.stderr)
        return 1

    if allow_l:
        misses = _find_allow_misses(packages, allow_l)
        if misses:
            print('Licenses not on SC-LIC-001 allow-list:', file=sys.stderr)
            for h in misses:
                print(f'  - {h}', file=sys.stderr)
            return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())  # pragma: no cover
