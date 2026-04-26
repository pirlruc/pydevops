"""Tests for scripts/github_actions_pins.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts.github_actions_pins import (
    _apply_file,
    _check_file,
    _load_pins,
    _run_apply,
    _run_check,
    _uses_spec_drift,
    _yaml_files,
)


def test_uses_spec_drift_skips_local() -> None:
    assert _uses_spec_drift(Path('w.yml'), './foo@v1', {}) is None


def test_uses_spec_drift_detects_mismatch(tmp_path: Path) -> None:
    pins = {'actions/checkout': 'v6'}
    msg = _uses_spec_drift(tmp_path / 'a.yml', 'actions/checkout@v5 # old', pins)
    assert msg is not None
    assert 'v5' in msg
    assert 'v6' in msg


def test_check_file_reports_drift(tmp_path: Path) -> None:
    wf = tmp_path / 'x.yml'
    wf.write_text('jobs:\n  j:\n    steps:\n      - uses: actions/checkout@v1\n', encoding='utf-8')
    pins = {'actions/checkout': 'v6'}
    errs = _check_file(wf, pins)
    assert len(errs) == 1


def test_yaml_files_finds_workflows(tmp_path: Path) -> None:
    wf = tmp_path / '.github' / 'workflows'
    wf.mkdir(parents=True)
    (wf / 't.yml').write_text('on: {}\n', encoding='utf-8')
    found = _yaml_files(tmp_path)
    assert any(p.name == 't.yml' for p in found)


def test_load_pins_rejects_non_object(tmp_path: Path) -> None:
    p = tmp_path / 'pins.json'
    p.write_text('[1]', encoding='utf-8')
    with pytest.raises(SystemExit, match='JSON object'):
        _load_pins(p)


def test_apply_file_updates_pin(tmp_path: Path) -> None:
    wf = tmp_path / 'w.yml'
    wf.write_text('  uses: actions/checkout@v1\n', encoding='utf-8')
    assert _apply_file(wf, {'actions/checkout': 'v6'}) is True
    assert 'actions/checkout@v6' in wf.read_text(encoding='utf-8')


def test_apply_file_no_change(tmp_path: Path) -> None:
    wf = tmp_path / 'w.yml'
    wf.write_text('uses: actions/checkout@v6\n', encoding='utf-8')
    assert _apply_file(wf, {'actions/checkout': 'v6'}) is False


def test_run_check_ignores_unlisted_actions(tmp_path: Path) -> None:
    wf = tmp_path / 'w.yml'
    wf.write_text('uses: unknown/action@v1\n', encoding='utf-8')
    _run_check([wf], {})


def test_run_apply_false_when_aligned(tmp_path: Path) -> None:
    wf = tmp_path / 'w.yml'
    wf.write_text('uses: actions/checkout@v6\n', encoding='utf-8')
    assert _run_apply([wf], {'actions/checkout': 'v6'}) is False


def test_run_check_raises_on_drift(tmp_path: Path) -> None:
    wf = tmp_path / 'w.yml'
    wf.write_text('uses: actions/checkout@v1\n', encoding='utf-8')
    with pytest.raises(SystemExit):
        _run_check([wf], {'actions/checkout': 'v6'})


def test_load_pins_skips_non_string_entries(tmp_path: Path) -> None:
    p = tmp_path / 'pins.json'
    p.write_text(
        (
            '{"actions/checkout": "v6",'
            ' "dorny/paths-filter": {"tag": "v4.0.1",'
            ' "sha": "fbd0ab8f3e69293af611ebaee6363fc25e6d187d"},'
            ' "skip": 1}'
        ),
        encoding='utf-8',
    )
    got = _load_pins(p)
    assert got == {
        'actions/checkout': 'v6',
        'dorny/paths-filter': {
            'tag': 'v4.0.1',
            'sha': 'fbd0ab8f3e69293af611ebaee6363fc25e6d187d',
        },
    }


def test_load_pins_skips_invalid_sha_entry(tmp_path: Path) -> None:
    p = tmp_path / 'pins.json'
    p.write_text('{"actions/checkout": {"tag": "v6", "sha": "v6"}}', encoding='utf-8')
    assert _load_pins(p) == {}


def test_apply_file_writes_sha_pin_with_version_comment(tmp_path: Path) -> None:
    wf = tmp_path / 'w.yml'
    wf.write_text('  - uses: actions/checkout@v6\n', encoding='utf-8')
    assert _apply_file(
        wf,
        {
            'actions/checkout': {
                'tag': 'v6',
                'sha': 'de0fac2e4500dabe0009e67214ff5f5447ce83dd',
            },
        },
    )
    txt = wf.read_text(encoding='utf-8')
    assert 'actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6' in txt


def test_check_file_allows_sha_pin_for_structured_entry(tmp_path: Path) -> None:
    wf = tmp_path / 'w.yml'
    wf.write_text(
        '  - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6\n',
        encoding='utf-8',
    )
    errs = _check_file(
        wf,
        {
            'actions/checkout': {
                'tag': 'v6',
                'sha': 'de0fac2e4500dabe0009e67214ff5f5447ce83dd',
            },
        },
    )
    assert errs == []


def test_check_file_rejects_structured_entry_without_comment(tmp_path: Path) -> None:
    wf = tmp_path / 'w.yml'
    wf.write_text('  - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd\n', encoding='utf-8')
    errs = _check_file(
        wf,
        {
            'actions/checkout': {
                'tag': 'v6',
                'sha': 'de0fac2e4500dabe0009e67214ff5f5447ce83dd',
            },
        },
    )
    assert len(errs) == 1
    assert 'trailing version comment' in errs[0]


def test_check_file_rejects_structured_entry_with_wrong_sha(tmp_path: Path) -> None:
    wf = tmp_path / 'w.yml'
    wf.write_text(
        '  - uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v6\n',
        encoding='utf-8',
    )
    errs = _check_file(
        wf,
        {
            'actions/checkout': {
                'tag': 'v6',
                'sha': 'de0fac2e4500dabe0009e67214ff5f5447ce83dd',
            },
        },
    )
    assert len(errs) == 1
    assert 'expected @de0fac2e4500dabe0009e67214ff5f5447ce83dd' in errs[0]


def test_main_check_argv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.github_actions_pins as mod

    wf = tmp_path / '.github' / 'workflows' / 't.yml'
    wf.parent.mkdir(parents=True)
    wf.write_text('uses: actions/checkout@v6\n', encoding='utf-8')
    pinf = tmp_path / '.github' / 'dependencies' / 'github-actions-pins.json'
    pinf.parent.mkdir(parents=True)
    pinf.write_text('{"actions/checkout": "v6"}', encoding='utf-8')
    monkeypatch.setattr(mod, '_repo_root', lambda: tmp_path)
    monkeypatch.setattr(sys, 'argv', ['github_actions_pins', '--check'])
    mod.main()


def test_main_apply_argv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import scripts.github_actions_pins as mod

    wf = tmp_path / '.github' / 'workflows' / 't.yml'
    wf.parent.mkdir(parents=True)
    wf.write_text('uses: actions/checkout@v1\n', encoding='utf-8')
    pinf = tmp_path / '.github' / 'dependencies' / 'github-actions-pins.json'
    pinf.parent.mkdir(parents=True)
    pinf.write_text('{"actions/checkout": "v6"}', encoding='utf-8')
    monkeypatch.setattr(mod, '_repo_root', lambda: tmp_path)
    monkeypatch.setattr(sys, 'argv', ['github_actions_pins'])
    mod.main()
    assert 'Updated' in capsys.readouterr().out
    assert 'v6' in wf.read_text(encoding='utf-8')
