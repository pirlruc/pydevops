"""Extra branches for ``scripts.license_gate``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_license_gate_skip_missing_sbom(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """No SBOM file exits 0."""
    from scripts import license_gate

    monkeypatch.setenv('SPDX_SBOM_PATH', str(tmp_path / 'nope.json'))
    monkeypatch.setenv('LICENSE_DENY_LIST', '[]')
    assert license_gate.main() == 0


def test_license_gate_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid LICENSE_DENY_LIST exits 2."""
    from scripts import license_gate

    monkeypatch.delenv('SPDX_SBOM_PATH', raising=False)
    monkeypatch.setenv('LICENSE_DENY_LIST', 'not-json')
    assert license_gate.main() == 2


def test_license_gate_not_list(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Non-array deny list exits 2."""
    from scripts import license_gate

    sbom = tmp_path / 's.json'
    sbom.write_text('{}', encoding='utf-8')
    monkeypatch.setenv('SPDX_SBOM_PATH', str(sbom))
    monkeypatch.setenv('LICENSE_DENY_LIST', '"x"')
    assert license_gate.main() == 2


def test_parse_deny_list() -> None:
    """_parse_deny_list normalizes string entries; skips non-strings."""
    from scripts.license_gate import _parse_deny_list

    assert _parse_deny_list('["MIT", " GPL "]') == ['mit', 'gpl']
    assert _parse_deny_list('[null, 123, "gpl"]') == ['gpl']


def test_parse_deny_list_skips_non_strings_no_none_pattern() -> None:
    """Null and numbers must not become deny patterns like 'none' or '123'."""
    from scripts.license_gate import _parse_deny_list

    assert _parse_deny_list('[null]') == []
    assert _parse_deny_list('[42]') == []


def test_license_gate_packages_not_list(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Non-list packages key is treated as empty."""
    from scripts import license_gate

    sbom = tmp_path / 's.json'
    sbom.write_text(json.dumps({'packages': {}}), encoding='utf-8')
    monkeypatch.setenv('SPDX_SBOM_PATH', str(sbom))
    monkeypatch.setenv('LICENSE_DENY_LIST', '[]')
    assert license_gate.main() == 0


def test_license_gate_skips_non_dict_package_entries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Non-object entries in packages are ignored; dict entries are still evaluated."""
    from scripts import license_gate

    sbom = tmp_path / 's.json'
    sbom.write_text(
        json.dumps(
            {
                'packages': [
                    'not-a-dict',
                    {'name': 'clean', 'licenseConcluded': 'MIT'},
                    {'name': 'bad', 'licenseConcluded': 'GPL-3.0-only'},
                ],
            },
        ),
        encoding='utf-8',
    )
    monkeypatch.setenv('SPDX_SBOM_PATH', str(sbom))
    monkeypatch.setenv('LICENSE_DENY_LIST', json.dumps(['gpl']))
    assert license_gate.main() == 1
    err = capsys.readouterr().err
    assert err.count('bad') == 1
    assert 'clean' not in err


def test_license_gate_allow_list_rejects_unknown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Non-empty LICENSE_ALLOW_LIST fails licenses that match no pattern."""
    from scripts import license_gate

    sbom = tmp_path / 's.json'
    sbom.write_text(
        json.dumps({'packages': [{'name': 'x', 'licenseConcluded': 'GPL-3.0-only'}]}),
        encoding='utf-8',
    )
    monkeypatch.setenv('SPDX_SBOM_PATH', str(sbom))
    monkeypatch.setenv('LICENSE_DENY_LIST', '[]')
    monkeypatch.setenv('LICENSE_ALLOW_LIST', json.dumps(['mit', 'apache-2.0']))
    assert license_gate.main() == 1


def test_license_gate_invalid_allow_list(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Invalid LICENSE_ALLOW_LIST exits 2."""
    from scripts import license_gate

    sbom = tmp_path / 's.json'
    sbom.write_text('{}', encoding='utf-8')
    monkeypatch.setenv('SPDX_SBOM_PATH', str(sbom))
    monkeypatch.setenv('LICENSE_DENY_LIST', '[]')
    monkeypatch.setenv('LICENSE_ALLOW_LIST', 'not-json')
    assert license_gate.main() == 2


def test_load_allow_list_from_missing_file(tmp_path: Path) -> None:
    """Missing thresholds path yields an empty allow list."""
    from scripts.license_gate import load_allow_list_from_thresholds

    assert load_allow_list_from_thresholds(tmp_path / 'nope.yml') == []


def test_license_gate_allow_list_accepts_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Allow-list substring match passes MIT when MIT is listed."""
    from scripts import license_gate

    sbom = tmp_path / 's.json'
    sbom.write_text(
        json.dumps({'packages': [{'name': 'x', 'licenseConcluded': 'MIT'}]}),
        encoding='utf-8',
    )
    monkeypatch.setenv('SPDX_SBOM_PATH', str(sbom))
    monkeypatch.setenv('LICENSE_DENY_LIST', '[]')
    monkeypatch.setenv('LICENSE_ALLOW_LIST', json.dumps(['mit']))
    assert license_gate.main() == 0
