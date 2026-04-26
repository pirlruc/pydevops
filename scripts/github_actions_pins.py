#!/usr/bin/env python3
"""Apply or verify GitHub Actions `uses:` pins from .github/dependencies/github-actions-pins.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import TypedDict


class PinEntry(TypedDict):
    """Action pin entry for SHA-pinned workflows with version comment."""

    tag: str
    sha: str


def _tag_sha_pair(value: object) -> tuple[str, str] | None:
    """Return ``(tag, sha)`` from a mapping value, else None."""
    if not isinstance(value, dict):
        return None
    tag = value.get('tag')
    sha = value.get('sha')
    if not isinstance(tag, str) or not isinstance(sha, str):
        return None
    return tag, sha


def _pin_entry_from_value(value: object) -> str | PinEntry | None:
    """Return normalized pin entry from JSON value, or None when unsupported."""
    if isinstance(value, str):
        return value
    pair = _tag_sha_pair(value)
    if pair is None:
        return None
    tag, sha = pair
    if not _is_sha_ref(sha):
        return None
    return {'tag': tag, 'sha': sha}


def _repo_root() -> Path:
    """Return the repository root directory (parent of ``scripts/``)."""
    return Path(__file__).resolve().parent.parent


def _is_sha_ref(ref: str) -> bool:
    """Return True when ``ref`` is a full 40-char lowercase/uppercase hex SHA."""
    return re.fullmatch(r'[0-9a-fA-F]{40}', ref) is not None


def _load_pins(path: Path) -> dict[str, str | PinEntry]:
    """Load action pins from JSON (legacy string refs or ``{tag, sha}`` objects)."""
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise SystemExit('pins file must be a JSON object')

    out: dict[str, str | PinEntry] = {}
    for k, v in data.items():
        if isinstance(k, str):
            entry = _pin_entry_from_value(v)
            if entry is not None:
                out[k] = entry

    return out


def _yaml_files(root: Path) -> list[Path]:
    """List workflow YAML files and composite ``action.yml`` files to scan or rewrite."""
    gh = root / '.github'
    paths: list[Path] = []
    paths.extend(sorted((gh / 'workflows').glob('*.yml')))
    for p in sorted((gh / 'actions').rglob('*.yml')):
        paths.append(p)

    return paths


def _uses_pattern(action: str) -> re.Pattern[str]:
    """Build regex that matches a ``uses: <action>@<ref>`` line, with optional comment."""
    return re.compile(rf'(^\s*(?:-\s*)?uses:\s*){re.escape(action)}@[^\s#]+(?:\s+#.*)?$', re.MULTILINE)


def _render_pin_spec(name: str, pin: str | PinEntry) -> str:
    """Return canonical ``uses:`` target string for an action pin entry."""
    if isinstance(pin, str):
        return f'{name}@{pin}'
    return f"{name}@{pin['sha']} # {pin['tag']}"


def _apply_file(path: Path, pins: dict[str, str | PinEntry]) -> bool:
    """Rewrite ``path`` so every pinned action uses the ref from ``pins``. Return True if changed."""
    text = path.read_text(encoding='utf-8')
    orig = text
    for name in sorted(pins, key=len, reverse=True):
        spec = _render_pin_spec(name, pins[name])
        text = _uses_pattern(name).sub(rf'\1{spec}', text)

    if text != orig:
        path.write_text(text, encoding='utf-8')
        return True

    return False


def _split_uses_spec_and_comment(spec_and_comment: str) -> tuple[str, str]:
    """Split ``uses`` RHS into ``spec`` and optional trailing comment text."""
    spec, _, comment = spec_and_comment.partition('#')
    return spec.strip(), comment.strip()


def _split_action_ref(spec: str) -> tuple[str, str] | None:
    """Split ``owner/repo@ref`` into action name and ref."""
    if '@' not in spec:
        return None
    if spec.startswith(('./', '../')):
        return None
    return spec.rsplit('@', 1)


def _drift_for_structured_pin(path: Path, name: str, have: str, comment: str, pin: PinEntry) -> str | None:
    """Validate one structured ``{tag, sha}`` pin entry against a uses spec."""
    if not _is_sha_ref(have):
        return f'{path}: {name}@{have} must be pinned to a 40-char commit SHA'
    want_sha = pin['sha']
    if have.lower() != want_sha.lower():
        return f'{path}: {name}@{have} expected @{want_sha}'
    if comment:
        return None
    return f"{path}: {name}@{have} should keep a trailing version comment like '# {pin['tag']}'"


def _uses_spec_drift(path: Path, spec_and_comment: str, pins: dict[str, str | PinEntry]) -> str | None:
    """Return an error line when ``uses`` entry drifts from policy; else None."""
    spec, comment = _split_uses_spec_and_comment(spec_and_comment)
    action_ref = _split_action_ref(spec)
    if action_ref is None:
        return None
    name, have = action_ref
    pin = pins.get(name)
    if pin is None:
        return None

    if isinstance(pin, str):
        if have == pin:
            return None
        return f'{path}: {name}@{have} expected @{pin}'
    return _drift_for_structured_pin(path, name, have, comment, pin)


def _check_file(path: Path, pins: dict[str, str | PinEntry]) -> list[str]:
    """Return human-readable drift messages for any ``uses:`` in ``path`` that disagrees with ``pins``."""
    text = path.read_text(encoding='utf-8')
    errs: list[str] = []
    for m in re.finditer(r'uses:\s*([^\n]+)', text):
        msg = _uses_spec_drift(path, m.group(1).strip(), pins)
        if msg is not None:
            errs.append(msg)

    return errs


def _run_check(files: list[Path], pins: dict[str, str | PinEntry]) -> None:
    """Exit with code 1 if any file has a ``uses:`` ref that does not match ``pins``."""
    all_errs: list[str] = []
    for f in files:
        all_errs.extend(_check_file(f, pins))

    if not all_errs:
        return

    sys.stderr.write('\n'.join(all_errs) + '\n')
    raise SystemExit(1)


def _run_apply(files: list[Path], pins: dict[str, str | PinEntry]) -> bool:
    """Apply ``pins`` to all ``files``; return True if any file was modified."""
    changed = False
    for f in files:
        if _apply_file(f, pins):
            changed = True

    return changed


def main() -> None:
    """Parse CLI flags and either verify pins (--check) or rewrite workflow YAML files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--check',
        action='store_true',
        help='verify workflows match pins (exit 1 on drift)',
    )
    args = parser.parse_args()
    root = _repo_root()
    pin_path = root / '.github' / 'dependencies' / 'github-actions-pins.json'
    pins = _load_pins(pin_path)
    files = _yaml_files(root)
    if args.check:
        _run_check(files, pins)
        return

    if _run_apply(files, pins):
        print('Updated GitHub Actions pins in .github/workflows and .github/actions')


if __name__ == '__main__':
    main()
