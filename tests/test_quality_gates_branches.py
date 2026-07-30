"""Branch coverage for ``scripts.quality_gates`` helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts import quality_gates as qg
from scripts.quality_gates.readers_py_coverage import pytest_exit_code


def test_pytest_exit_code_invalid_text(tmp_path: Path) -> None:
    """Non-integer pytest_exit_code.txt is treated as missing."""
    (tmp_path / 'pytest_exit_code.txt').write_text('not-a-number\n', encoding='utf-8')
    assert pytest_exit_code(tmp_path) is None


def test_read_json_invalid(tmp_path: Path) -> None:
    """_read_json returns None for invalid JSON."""
    p = tmp_path / 'x.json'
    p.write_text('{', encoding='utf-8')
    assert qg._read_json(p) is None


def test_pylint_score_no_match(tmp_path: Path) -> None:
    """_pylint_score returns None without rating line."""
    (tmp_path / 'pylint_score.txt').write_text('no score here', encoding='utf-8')
    assert qg._pylint_score(tmp_path) is None


def test_ruff_dict_format(tmp_path: Path) -> None:
    """_ruff_issue_count handles object-shaped ruff.json."""
    (tmp_path / 'ruff.json').write_text(
        json.dumps({'files': [{'messages': [{'code': 'E'}]}]}),
        encoding='utf-8',
    )
    assert qg._ruff_issue_count(tmp_path) == 1


def test_ruff_files_messages_non_list_ignored(tmp_path: Path) -> None:
    """Malformed ``messages`` (null, dict, etc.) must not raise or use wrong len()."""
    (tmp_path / 'ruff.json').write_text(
        json.dumps(
            {
                'files': [
                    {'messages': None},
                    {'messages': {'not': 'a list'}},
                    {'messages': [{'code': 'E1'}, {'code': 'E2'}]},
                ],
            },
        ),
        encoding='utf-8',
    )
    assert qg._ruff_issue_count(tmp_path) == 2


def test_radon_mi_string_value(tmp_path: Path) -> None:
    """_radon_mi_min parses string MI values."""
    (tmp_path / 'radon_mi.json').write_text(json.dumps({'a.py': '70.5'}), encoding='utf-8')
    assert qg._radon_mi_min(tmp_path) == pytest.approx(70.5)


def test_radon_mi_bad_string(tmp_path: Path) -> None:
    """Invalid string MI is skipped."""
    (tmp_path / 'radon_mi.json').write_text(json.dumps({'a.py': 'x'}), encoding='utf-8')
    assert qg._radon_mi_min(tmp_path) is None


def test_pip_audit_tuple_row(tmp_path: Path) -> None:
    """_pip_audit_vulns handles legacy tuple rows."""
    row = ['pkg', '1.0', [{'id': 'x', 'severity': 'HIGH', 'description': ''}]]
    (tmp_path / 'pip_audit.json').write_text(json.dumps([row]), encoding='utf-8')
    result = qg._pip_audit_vulns(tmp_path)
    assert result is not None
    h, _m = result
    assert h >= 1


def test_pip_audit_non_dict_vuln_skipped(tmp_path: Path) -> None:
    """Non-dict entries in vulns list are skipped."""
    (tmp_path / 'pip_audit.json').write_text(
        json.dumps([{'vulns': ['bad', {'id': 'z', 'severity': '', 'description': ''}]}]),
        encoding='utf-8',
    )
    result = qg._pip_audit_vulns(tmp_path)
    assert result is not None
    _h, m = result
    assert m >= 1


def test_pip_audit_dict_row(tmp_path: Path) -> None:
    """_pip_audit_vulns handles dict-shaped dependency rows."""
    row = {
        'vulns': [
            {'id': 'V1', 'severity': 'HIGH', 'description': ''},
            {'id': 'V2', 'severity': 'medium', 'description': ''},
            {'id': 'V3', 'description': ''},
        ],
    }
    (tmp_path / 'pip_audit.json').write_text(json.dumps([row]), encoding='utf-8')
    result = qg._pip_audit_vulns(tmp_path)
    assert result is not None
    h, m = result
    assert h >= 1
    assert m >= 1


def test_pip_audit_missing_returns_none(tmp_path: Path) -> None:
    """Missing pip_audit.json is treated as unreadable report, not zero vulns."""
    assert qg._pip_audit_vulns(tmp_path) is None


def test_grype_high(tmp_path: Path) -> None:
    """_grype_severities counts high/critical."""
    (tmp_path / 'grype.json').write_text(
        json.dumps({'matches': [{'vulnerability': {'severity': 'High'}}]}),
        encoding='utf-8',
    )
    result = qg._grype_severities(tmp_path)
    assert result is not None
    h, m = result
    assert h == 1


def test_grype_match_non_dict_vulnerability_skipped(tmp_path: Path) -> None:
    """Non-dict ``vulnerability`` must not crash; valid matches still count."""
    (tmp_path / 'grype.json').write_text(
        json.dumps(
            {
                'matches': [
                    {'vulnerability': 'High'},
                    {'vulnerability': {'severity': 'Critical'}},
                ],
            },
        ),
        encoding='utf-8',
    )
    result = qg._grype_severities(tmp_path)
    assert result is not None
    h, m = result
    assert h == 1
    assert m == 0


def test_grype_medium(tmp_path: Path) -> None:
    """_grype_severities counts medium."""
    (tmp_path / 'grype.json').write_text(
        json.dumps({'matches': [{'vulnerability': {'severity': 'Medium'}}]}),
        encoding='utf-8',
    )
    result = qg._grype_severities(tmp_path)
    assert result is not None
    h, m = result
    assert h == 0
    assert m == 1


def test_grype_non_object_root(tmp_path: Path) -> None:
    """Valid JSON array is not a Grype document."""
    (tmp_path / 'grype.json').write_text('[]', encoding='utf-8')
    assert qg._grype_severities(tmp_path) is None


def test_grype_missing_returns_none(tmp_path: Path) -> None:
    """Missing grype.json is treated as unreadable report, not zero vulns."""
    assert qg._grype_severities(tmp_path) is None


def test_gitleaks_non_list(tmp_path: Path) -> None:
    """_gitleaks_findings returns 0 for non-list."""
    (tmp_path / 'gitleaks.json').write_text('{}', encoding='utf-8')
    assert qg._gitleaks_findings(tmp_path) == 0


def test_interrogate_alt_regex(tmp_path: Path) -> None:
    """Second interrogate regex path."""
    (tmp_path / 'interrogate.txt').write_text('Overall 88.0% covered today\n', encoding='utf-8')
    assert qg._interrogate_coverage(tmp_path) == pytest.approx(88.0)


def test_pylint_issues_list(tmp_path: Path) -> None:
    """_pylint_issue_count counts list messages."""
    (tmp_path / 'pylint.json').write_text('[{"message": "x"}]', encoding='utf-8')
    assert qg._pylint_issue_count(tmp_path) == 1


def test_ruff_list_count(tmp_path: Path) -> None:
    """_ruff_issue_count uses list length when format is array."""
    (tmp_path / 'ruff.json').write_text('[{}, {}]', encoding='utf-8')
    assert qg._ruff_issue_count(tmp_path) == 2


def test_pylint_issues_non_list(tmp_path: Path) -> None:
    """_pylint_issue_count returns 0 for non-list pylint.json."""
    (tmp_path / 'pylint.json').write_text('{}', encoding='utf-8')
    assert qg._pylint_issue_count(tmp_path) == 0


def test_ruff_unknown_shape(tmp_path: Path) -> None:
    """_ruff_issue_count returns 0 for unrecognized JSON shape."""
    (tmp_path / 'ruff.json').write_text('{"other": true}', encoding='utf-8')
    assert qg._ruff_issue_count(tmp_path) == 0


def test_jscpd_invalid_percentage_returns_none(tmp_path: Path) -> None:
    """Unparsable jscpd percentage must not raise and should return None."""
    from scripts.quality_gates.readers_ruff_jscpd import jscpd_duplication_pct

    (tmp_path / 'jscpd-report.json').write_text(
        json.dumps({'statistics': {'total': {'percentage': ''}}}),
        encoding='utf-8',
    )
    assert jscpd_duplication_pct(tmp_path) is None


def test_radon_cc_skips_nonlist_blocks(tmp_path: Path) -> None:
    """_radon_cc_max skips values that are not block lists."""
    (tmp_path / 'radon_cc.json').write_text(json.dumps({'a.py': 'bad'}), encoding='utf-8')
    assert qg._radon_cc_max(tmp_path) is None


def test_radon_cc_max_zero_is_valid(tmp_path: Path) -> None:
    """Max complexity 0.0 must not be coerced to None (float truthiness bug)."""
    (tmp_path / 'radon_cc.json').write_text(
        json.dumps({'m.py': [{'complexity': 0}]}),
        encoding='utf-8',
    )
    assert qg._radon_cc_max(tmp_path) == 0.0


def test_radon_cc_avg_and_mi_avg(tmp_path: Path) -> None:
    """Average CC and MI readers return arithmetic means."""
    (tmp_path / 'radon_cc.json').write_text(
        json.dumps({'a.py': [{'complexity': 2}, {'complexity': 4}]}),
        encoding='utf-8',
    )
    (tmp_path / 'radon_mi.json').write_text(
        json.dumps({'a.py': {'mi': 40}, 'b.py': {'mi': 60}}),
        encoding='utf-8',
    )
    assert qg._radon_cc_avg(tmp_path) == pytest.approx(3.0)
    assert qg._radon_mi_avg(tmp_path) == pytest.approx(50.0)


def test_load_org_python_floors_from_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Org floors parse from profile.thresholds.yml when present."""
    from scripts.quality_gates import config as cfg

    root = tmp_path
    py_dir = root / 'docs' / 'guardrails' / 'python'
    py_dir.mkdir(parents=True)
    (py_dir / 'profile.thresholds.yml').write_text(
        'statement_coverage: 95\n'
        'branch_coverage: 95\n'
        'doc_coverage: 95\n'
        'max_cyclomatic_complexity: 8\n'
        'avg_cyclomatic_complexity: 5\n'
        'min_maintainability_index: 40\n'
        'avg_maintainability_index: 60\n',
        encoding='utf-8',
    )
    monkeypatch.setattr(cfg, '_repo_root', lambda: root)
    cfg.load_org_python_floors.cache_clear()
    floors = cfg.load_org_python_floors()
    assert floors['max_cyclomatic_complexity'] == 8.0
    assert floors['avg_maintainability_index'] == 60.0
    high = cfg._build_strictness()['High']
    assert high.cyclomatic_max == 8.0
    assert high.maintainability_index_avg_min == 60.0
    cfg.load_org_python_floors.cache_clear()


def test_gate_cyclomatic_avg_and_mi_avg() -> None:
    """Average gates compare against Thresholds avg fields."""
    from scripts.quality_gates.config import STRICTNESS
    from scripts.quality_gates.gates_complexity import gate_cyclomatic_avg, gate_maintainability_avg

    t = STRICTNESS['High']
    rows, fails = gate_cyclomatic_avg(4.0, t, 'High')
    assert rows[0]['ok'] is True
    assert fails == []
    rows, fails = gate_maintainability_avg(55.0, t, 'High')
    assert rows[0]['ok'] is False
    assert fails


def test_main_failure_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main returns 1 when gates fail."""
    monkeypatch.setenv('QUALITY_OUTPUT_DIR', str(tmp_path))
    monkeypatch.setenv('STRICTNESS_LEVEL', 'High')
    monkeypatch.setattr(sys, 'argv', ['scripts.quality_gates'])
    # no artifacts -> high fails
    assert qg.main() == 1


def test_mypy_lineprecision_sums_rows_without_total(tmp_path: Path) -> None:
    """lineprecision totals aggregate per-module rows when Total is absent."""
    from scripts.quality_gates.readers_mypy import mypy_imprecision_pct, mypy_lineprecision_totals

    d = tmp_path / 'mypy-reports' / 'lineprecision'
    d.mkdir(parents=True)
    (d / 'lineprecision.txt').write_text(
        'Name Lines Precise Imprecise Any Empty Unanalyzed\n'
        '---\n'
        'a 10 9 1 0 0 0\n'
        'b 20 18 2 0 0 0\n',
        encoding='utf-8',
    )
    assert mypy_lineprecision_totals(tmp_path) == (30, 27, 3)
    assert mypy_imprecision_pct(tmp_path) == pytest.approx(10.0)


def test_mypy_any_exprs_sums_rows_without_total(tmp_path: Path) -> None:
    """any-exprs totals aggregate rows when Total is absent."""
    from scripts.quality_gates.readers_mypy import mypy_any_exprs_totals

    d = tmp_path / 'mypy-reports' / 'anyexprs'
    d.mkdir(parents=True)
    (d / 'any-exprs.txt').write_text(
        'Name Anys Exprs Coverage\n'
        '---\n'
        'a 1 10 90.00%\n'
        'b 1 10 90.00%\n',
        encoding='utf-8',
    )
    anys, exprs, cov = mypy_any_exprs_totals(tmp_path) or (0, 0, 0.0)
    assert anys == 2
    assert exprs == 20
    assert cov == pytest.approx(90.0)


def test_mypy_lineprecision_prefers_total_row(tmp_path: Path) -> None:
    """When a Total row exists, it wins over per-module rows."""
    from scripts.quality_gates.readers_mypy import mypy_lineprecision_totals

    d = tmp_path / 'mypy-reports' / 'lineprecision'
    d.mkdir(parents=True)
    (d / 'lineprecision.txt').write_text(
        'Name Lines Precise Imprecise Any Empty Unanalyzed\n'
        '---\n'
        'noise 999 0 999 0 0 0\n'
        'Total 100 99 1 0 0 0\n',
        encoding='utf-8',
    )
    assert mypy_lineprecision_totals(tmp_path) == (100, 99, 1)


def test_mypy_lineprecision_skips_bad_numeric_row(tmp_path: Path) -> None:
    """Non-integer cells in a seven-token row are skipped."""
    from scripts.quality_gates.readers_mypy import mypy_lineprecision_totals

    d = tmp_path / 'mypy-reports' / 'lineprecision'
    d.mkdir(parents=True)
    (d / 'lineprecision.txt').write_text(
        'Name Lines Precise Imprecise Any Empty Unanalyzed\n'
        '---\n'
        'bad 10 x 1 0 0 0\n'
        'm 10 9 1 0 0 0\n',
        encoding='utf-8',
    )
    assert mypy_lineprecision_totals(tmp_path) == (10, 9, 1)


def test_mypy_any_exprs_total_bad_coverage_token(tmp_path: Path) -> None:
    """Invalid coverage token on Total row falls back / yields None."""
    from scripts.quality_gates.readers_mypy import mypy_any_exprs_totals

    d = tmp_path / 'mypy-reports' / 'anyexprs'
    d.mkdir(parents=True)
    (d / 'any-exprs.txt').write_text(
        'Name Anys Exprs Coverage\n'
        '---\n'
        'Total 1 2 bad%\n',
        encoding='utf-8',
    )
    assert mypy_any_exprs_totals(tmp_path) is None


def test_mypy_any_exprs_row_value_error_skipped(tmp_path: Path) -> None:
    """Rows with non-integer Anys/Exprs are skipped during aggregation."""
    from scripts.quality_gates.readers_mypy import mypy_any_exprs_totals

    d = tmp_path / 'mypy-reports' / 'anyexprs'
    d.mkdir(parents=True)
    (d / 'any-exprs.txt').write_text(
        'Name Anys Exprs Coverage\n'
        '---\n'
        'bad 1 x 90.00%\n'
        'm 0 10 100.00%\n',
        encoding='utf-8',
    )
    assert mypy_any_exprs_totals(tmp_path) == (0, 10, 100.0)


def test_mypy_imprecision_zero_lines(tmp_path: Path) -> None:
    """Imprecision is undefined when Total lines is zero."""
    from scripts.quality_gates.readers_mypy import mypy_imprecision_pct

    d = tmp_path / 'mypy-reports' / 'lineprecision'
    d.mkdir(parents=True)
    (d / 'lineprecision.txt').write_text(
        'Name Lines Precise Imprecise Any Empty Unanalyzed\n'
        '---\n'
        'Total 0 0 0 0 0 0\n',
        encoding='utf-8',
    )
    assert mypy_imprecision_pct(tmp_path) is None


def test_mypy_any_exprs_prefers_total_row(tmp_path: Path) -> None:
    """When a Total row exists, it wins over per-module rows."""
    from scripts.quality_gates.readers_mypy import mypy_any_exprs_totals

    d = tmp_path / 'mypy-reports' / 'anyexprs'
    d.mkdir(parents=True)
    (d / 'any-exprs.txt').write_text(
        'Name Anys Exprs Coverage\n'
        '---\n'
        'noise 9 10 10.00%\n'
        'Total 0 100 100.00%\n',
        encoding='utf-8',
    )
    assert mypy_any_exprs_totals(tmp_path) == (0, 100, 100.0)


def test_mypy_report_usable_helpers(tmp_path: Path) -> None:
    """Artifact substance helpers return None when reports are missing."""
    from scripts.quality_gates.readers_mypy import mypy_any_exprs_report_usable, mypy_lineprecision_report_usable

    assert mypy_lineprecision_report_usable(tmp_path) is None
    assert mypy_any_exprs_report_usable(tmp_path) is None
