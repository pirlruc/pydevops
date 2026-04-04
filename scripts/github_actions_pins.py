#!/usr/bin/env python3
"""Apply or verify GitHub Actions `uses:` pins from .github/dependencies/github-actions-pins.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _repo_root() -> Path:
    """Return the repository root directory (parent of ``scripts/``)."""
    return Path(__file__).resolve().parent.parent


def _load_pins(path: Path) -> dict[str, str]:
    """Load action name → ref tag mapping from JSON (string keys and values only)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("pins file must be a JSON object")
    out: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def _yaml_files(root: Path) -> list[Path]:
    """List workflow YAML files and composite ``action.yml`` files to scan or rewrite."""
    gh = root / ".github"
    paths: list[Path] = []
    paths.extend(sorted((gh / "workflows").glob("*.yml")))
    for p in sorted((gh / "actions").rglob("*.yml")):
        paths.append(p)
    return paths


def _uses_pattern(action: str) -> re.Pattern[str]:
    """Build a regex that matches ``uses: <action>@<anything>`` for replacement."""
    return re.compile(rf"(uses:\s*){re.escape(action)}@[^\s#]+")


def _apply_file(path: Path, pins: dict[str, str]) -> bool:
    """Rewrite ``path`` so every pinned action uses the ref from ``pins``. Return True if changed."""
    text = path.read_text(encoding="utf-8")
    orig = text
    for name in sorted(pins, key=len, reverse=True):
        ver = pins[name]
        text = _uses_pattern(name).sub(rf"\1{name}@{ver}", text)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def _uses_spec_drift(path: Path, spec: str, pins: dict[str, str]) -> str | None:
    """If ``spec`` is a pinned third-party action with wrong ref, return an error line; else None."""
    if "@" not in spec or spec.startswith(("./", "../")):
        return None
    name, have = spec.rsplit("@", 1)
    want = pins.get(name)
    if want is None or have == want:
        return None
    return f"{path}: {name}@{have} expected @{want}"


def _check_file(path: Path, pins: dict[str, str]) -> list[str]:
    """Return human-readable drift messages for any ``uses:`` in ``path`` that disagrees with ``pins``."""
    text = path.read_text(encoding="utf-8")
    errs: list[str] = []
    for m in re.finditer(r"uses:\s*([^\s#]+)", text):
        msg = _uses_spec_drift(path, m.group(1).strip(), pins)
        if msg is not None:
            errs.append(msg)
    return errs


def _run_check(files: list[Path], pins: dict[str, str]) -> None:
    """Exit with code 1 if any file has a ``uses:`` ref that does not match ``pins``."""
    all_errs: list[str] = []
    for f in files:
        all_errs.extend(_check_file(f, pins))
    if not all_errs:
        return
    sys.stderr.write("\n".join(all_errs) + "\n")
    raise SystemExit(1)


def _run_apply(files: list[Path], pins: dict[str, str]) -> bool:
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
        "--check",
        action="store_true",
        help="verify workflows match pins (exit 1 on drift)",
    )
    args = parser.parse_args()
    root = _repo_root()
    pin_path = root / ".github" / "dependencies" / "github-actions-pins.json"
    pins = _load_pins(pin_path)
    files = _yaml_files(root)
    if args.check:
        _run_check(files, pins)
        return
    if _run_apply(files, pins):
        print("Updated GitHub Actions pins in .github/workflows and .github/actions")


if __name__ == "__main__":
    main()
