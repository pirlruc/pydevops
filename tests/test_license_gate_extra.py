"""Extra branches for ``scripts.license_gate``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_license_gate_skip_missing_sbom(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """No SBOM file exits 0."""
    from scripts import license_gate

    monkeypatch.setenv("SPDX_SBOM_PATH", str(tmp_path / "nope.json"))
    monkeypatch.setenv("LICENSE_DENY_LIST", "[]")
    assert license_gate.main() == 0


def test_license_gate_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid LICENSE_DENY_LIST exits 2."""
    from scripts import license_gate

    monkeypatch.delenv("SPDX_SBOM_PATH", raising=False)
    monkeypatch.setenv("LICENSE_DENY_LIST", "not-json")
    assert license_gate.main() == 2


def test_license_gate_not_list(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Non-array deny list exits 2."""
    from scripts import license_gate

    sbom = tmp_path / "s.json"
    sbom.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("SPDX_SBOM_PATH", str(sbom))
    monkeypatch.setenv("LICENSE_DENY_LIST", '"x"')
    assert license_gate.main() == 2


def test_parse_deny_list() -> None:
    """_parse_deny_list normalizes entries."""
    from scripts.license_gate import _parse_deny_list

    assert _parse_deny_list('["MIT", " GPL "]') == ["mit", "gpl"]


def test_license_gate_packages_not_list(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Non-list packages key is treated as empty."""
    from scripts import license_gate

    sbom = tmp_path / "s.json"
    sbom.write_text(json.dumps({"packages": {}}), encoding="utf-8")
    monkeypatch.setenv("SPDX_SBOM_PATH", str(sbom))
    monkeypatch.setenv("LICENSE_DENY_LIST", "[]")
    assert license_gate.main() == 0


