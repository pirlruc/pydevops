"""Tests for scripts/export_quality_tools_requirements.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.export_quality_tools_requirements import (
    _groups_table,
    _quality_tools_entries,
    export_quality_tools_requirements,
    main as export_main,
)


def test_groups_table_rejects_non_dict() -> None:
    with pytest.raises(SystemExit, match='invalid structure'):
        _groups_table([])


def test_groups_table_missing_section() -> None:
    with pytest.raises(SystemExit, match='dependency-groups'):
        _groups_table({'project': {}})


def test_quality_tools_rejects_include_group() -> None:
    groups: dict[str, object] = {'quality-tools': [{}, 'x']}
    with pytest.raises(SystemExit, match='string pins'):
        _quality_tools_entries(groups)


def test_quality_tools_not_list() -> None:
    with pytest.raises(SystemExit, match='missing quality-tools'):
        _quality_tools_entries({'quality-tools': 'nope'})


def test_export_writes_pins(tmp_path: Path) -> None:
    (tmp_path / 'pyproject.toml').write_text(
        '[project]\nname = "x"\nversion = "0"\n'
        '[dependency-groups]\n'
        'quality-tools = [ "aa==1", "bb==2" ]\n',
        encoding='utf-8',
    )
    req_dir = tmp_path / '.github' / 'dependencies' / 'quality-tools'
    req_dir.mkdir(parents=True)
    export_quality_tools_requirements(tmp_path)
    text = (req_dir / 'requirements.txt').read_text(encoding='utf-8')
    assert 'aa==1' in text
    assert 'bb==2' in text
    assert text.strip().splitlines()[0].startswith('# Pinned CLI tools')


def test_main_writes_via_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.export_quality_tools_requirements as mod

    (tmp_path / 'pyproject.toml').write_text(
        '[project]\nname = "x"\nversion = "0"\n[dependency-groups]\nquality-tools = [ "zz==9" ]\n',
        encoding='utf-8',
    )
    req_dir = tmp_path / '.github' / 'dependencies' / 'quality-tools'
    req_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, '_root', lambda: tmp_path)
    export_main()
    assert 'zz==9' in (req_dir / 'requirements.txt').read_text(encoding='utf-8')
