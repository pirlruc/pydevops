"""Exact row, threshold, and boundary assertions that kill mutation survivors."""

from __future__ import annotations

from pathlib import Path

import pytest

import scripts.quality_gates  # noqa: F401  (import order avoids a cycle)
from scripts.complexity_gate_rules import avg_cc_gate, avg_mi_gate, max_cc_gate, min_mi_gate
from scripts.mypy_gate_rules import (
    any_density_row,
    imprecision_row,
    skip_mypy_without_reports,
    type_coverage_row,
)
from scripts.org_thresholds import (
    SELF_CI_MAX_CYCLOMATIC,
    ThresholdError,
    default_python_floors,
    load_ci_thresholds,
    load_python_floors,
    parse_threshold_yaml,
    require_python_floors,
    self_ci_max_cyclomatic,
)
from scripts.quality_gates import artifact_rules
from scripts.quality_gates.config import (
    HIGH_REQUIRED_FILES,
    _build_strictness,
    _repo_root,
    apply_consumer_floors,
    normalized_strictness_level,
    resolve_thresholds,
    scripts_only_package,
)
from scripts.quality_gates.gates_complexity import gate_duplication, gate_issues_per_kloc
from scripts.quality_gates.gates_coverage import (
    gate_coverage_branch,
    gate_coverage_line,
    gate_pylint,
    gate_pytest_exit,
)
from scripts.quality_gates.gates_docstrings import (
    gate_docstring_coverage,
    gate_docstring_issue_rate,
)
from scripts.quality_gates.gates_security import (
    gate_bandit,
    gate_gitleaks,
    gate_semgrep,
    gate_vulnerabilities,
)
from scripts.quality_gates.jsonutil import (
    coerce_non_negative_float,
    gates_rows_and_passed,
    read_json,
)
from scripts.quality_gates.readers_grype_gitleaks import (
    count_one_grype_match,
    grype_match_bucket,
    grype_severities,
    gitleaks_findings,
)
from scripts.quality_gates.readers_pip import bump_pip_severity, pip_audit_vulns, pip_dict_row_vulns

_YAML = """\
statement_coverage: 11
branch_coverage: 12
doc_coverage: 13
max_cyclomatic_complexity: 14
avg_cyclomatic_complexity: 15
min_maintainability_index: 16
avg_maintainability_index: 17
"""


def test_build_strictness_literal_floors() -> None:
    """Low, Medium, and High numeric floors are the org literals, not nearby values."""
    built = _build_strictness()
    assert set(built) == {'Low', 'Medium', 'High'}
    low, medium, high = built['Low'], built['Medium'], built['High']
    assert (
        low.coverage_line_min,
        low.coverage_branch_min,
        low.pylint_score_min,
        low.cyclomatic_max,
        low.cyclomatic_avg_max,
        low.maintainability_index_min,
        low.maintainability_index_avg_min,
        low.duplication_max_pct,
        low.issues_per_kloc_slocs_max,
        low.docstring_coverage_min,
        low.docstring_issues_per_kloc_cloc_max,
        low.mypy_type_coverage_min,
        low.mypy_imprecision_lt_pct,
        low.mypy_any_per_kloc_lt,
        low.vuln_high_max,
        low.vuln_medium_max,
        low.bandit_findings_max,
    ) == (70.0, 65.0, 7.0, 15, 10, 10.0, 25.0, 25.0, 25.0, 70.0, 8.0, 85.0, 5.0, 5.0, 2, 25, 15)
    assert (
        medium.coverage_line_min,
        medium.coverage_branch_min,
        medium.pylint_score_min,
        medium.cyclomatic_max,
        medium.cyclomatic_avg_max,
        medium.maintainability_index_min,
        medium.maintainability_index_avg_min,
        medium.duplication_max_pct,
        medium.issues_per_kloc_slocs_max,
        medium.docstring_coverage_min,
        medium.docstring_issues_per_kloc_cloc_max,
        medium.mypy_type_coverage_min,
        medium.mypy_imprecision_lt_pct,
        medium.mypy_any_per_kloc_lt,
        medium.vuln_high_max,
        medium.vuln_medium_max,
        medium.bandit_findings_max,
    ) == (85.0, 80.0, 8.0, 10, 7, 20.0, 40.0, 15.0, 15.0, 85.0, 5.0, 90.0, 2.0, 2.0, 0, 10, 3)
    assert (
        high.coverage_line_min,
        high.coverage_branch_min,
        high.pylint_score_min,
        high.cyclomatic_max,
        high.cyclomatic_avg_max,
        high.maintainability_index_min,
        high.maintainability_index_avg_min,
        high.duplication_max_pct,
        high.issues_per_kloc_slocs_max,
        high.docstring_coverage_min,
        high.docstring_issues_per_kloc_cloc_max,
        high.mypy_type_coverage_min,
        high.mypy_imprecision_lt_pct,
        high.mypy_any_per_kloc_lt,
        high.vuln_high_max,
        high.vuln_medium_max,
        high.bandit_findings_max,
    ) == (95.0, 95.0, 9.5, 8.0, 5.0, 40.0, 60.0, 5.0, 5.0, 95.0, 2.0, 95.0, 1.0, 1.0, 0, 5, 0)
    assert isinstance(high.vuln_high_max, int)
    assert isinstance(high.bandit_findings_max, int)


def test_repo_root_is_parent_of_scripts() -> None:
    """``config._repo_root`` is the directory that contains ``scripts/``."""
    root = _repo_root()
    assert root == Path(__file__).resolve().parents[1]
    assert (root / 'scripts' / 'quality_gates' / 'config.py').is_file()


def test_normalized_strictness_unknown_is_medium() -> None:
    """Unknown text maps to the exact label Medium; known labels keep their case."""
    assert normalized_strictness_level('nope') == 'Medium'
    assert normalized_strictness_level('  high ') == 'High'
    assert normalized_strictness_level('LOW') == 'Low'
    assert normalized_strictness_level('medium') == 'Medium'


def test_scripts_only_package_default_and_exact_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """PACKAGE_MODE defaults to app and matches only the exact string scripts."""
    monkeypatch.delenv('PACKAGE_MODE', raising=False)
    assert scripts_only_package() is False
    monkeypatch.setenv('PACKAGE_MODE', 'scripts')
    assert scripts_only_package() is True
    monkeypatch.setenv('PACKAGE_MODE', 'app')
    assert scripts_only_package() is False
    monkeypatch.setenv('PACKAGE_MODE', 'Scripts')
    assert scripts_only_package() is False


def test_apply_consumer_floors_replaces_each_key(tmp_path: Path) -> None:
    """Each consumer floor key overwrites the matching High field."""
    path = tmp_path / 'floors.yml'
    path.write_text(_YAML, encoding='utf-8')
    base = _build_strictness()['Low']
    over = apply_consumer_floors(base, path)
    assert over.coverage_line_min == 11
    assert over.coverage_branch_min == 12
    assert over.docstring_coverage_min == 13
    assert over.cyclomatic_max == 14
    assert over.cyclomatic_avg_max == 15
    assert over.maintainability_index_min == 16
    assert over.maintainability_index_avg_min == 17
    assert over.pylint_score_min == base.pylint_score_min
    assert over.vuln_high_max == base.vuln_high_max


def test_resolve_thresholds_uses_file_argument_not_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit consumer path wins when CONSUMER_THRESHOLDS is unset."""
    path = tmp_path / 'floors.yml'
    path.write_text(_YAML, encoding='utf-8')
    monkeypatch.delenv('CONSUMER_THRESHOLDS', raising=False)
    got = resolve_thresholds('Low', str(path))
    assert got.coverage_line_min == 11
    assert got.coverage_branch_min == 12
    missing = resolve_thresholds('Low', None)
    assert missing.coverage_line_min == 70.0


def test_default_python_floors_exact() -> None:
    """Baked-in floors match the org High profile, including the lint window."""
    assert default_python_floors() == {
        'statement_coverage': 95.0,
        'branch_coverage': 95.0,
        'doc_coverage': 95.0,
        'max_cyclomatic_complexity': 8.0,
        'avg_cyclomatic_complexity': 5.0,
        'min_maintainability_index': 40.0,
        'avg_maintainability_index': 60.0,
        'lint_exception_max_days': 14.0,
    }
    assert SELF_CI_MAX_CYCLOMATIC == 5.0
    assert self_ci_max_cyclomatic({'max_cyclomatic_complexity': 8.0}) == 5.0
    assert self_ci_max_cyclomatic({'max_cyclomatic_complexity': 3.0}) == 3.0


def test_parse_threshold_yaml_exact_and_skips() -> None:
    """Comments, blanks, and non-numeric values are dropped; keys stay verbatim."""
    parsed = parse_threshold_yaml(
        'statement_coverage: 95  # PY-TEST-002\n\nnot a line\nempty:\nbad: nope\nbranch_coverage: 80.5\n'
    )
    assert parsed == {'statement_coverage': 95.0, 'branch_coverage': 80.5}


def test_load_python_floors_warning_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing checkout and a missing optional key use the exact warning strings."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ThresholdError, match='docs/guardrails/python/profile.thresholds.yml'):
        load_python_floors(tmp_path, allow_missing_checkout=False)
    err = capsys.readouterr().err
    assert err == ''
    floors = load_python_floors(tmp_path, allow_missing_checkout=True)
    err = capsys.readouterr().err
    assert 'warning: CI-022: docs/guardrails/python/profile.thresholds.yml and ' in err
    assert 'scripts/python.profile.thresholds.yml are missing; using baked-in High floors' in err
    assert floors['statement_coverage'] == 95.0
    vendor = tmp_path / 'scripts'
    vendor.mkdir()
    (vendor / 'python.profile.thresholds.yml').write_text(_YAML, encoding='utf-8')
    got = load_python_floors(tmp_path)
    err = capsys.readouterr().err
    assert "warning: optional key 'lint_exception_max_days' missing" in err
    assert 'using 14.0' in err
    assert got['statement_coverage'] == 11.0
    assert got['lint_exception_max_days'] == 14.0


def test_load_ci_thresholds_exact_messages(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CI pack fallback and required keys use the documented strings."""
    with pytest.raises(ThresholdError, match='docs/guardrails/ci/profile.thresholds.yml'):
        load_ci_thresholds(tmp_path, allow_missing_checkout=False)
    assert load_ci_thresholds(tmp_path) == {}
    err = capsys.readouterr().err
    assert 'warning: CI-022: docs/guardrails/ci/profile.thresholds.yml and ' in err
    assert 'scripts/ci.profile.thresholds.yml are missing; skipping CI pack' in err
    ci = tmp_path / 'scripts'
    ci.mkdir()
    (ci / 'ci.profile.thresholds.yml').write_text(
        'ci_image_max_age_days: 30\nci_job_timeout_minutes_max: 45\nsecurity_rescan_interval_days: 7\n',
        encoding='utf-8',
    )
    assert load_ci_thresholds(tmp_path) == {
        'ci_image_max_age_days': 30.0,
        'ci_job_timeout_minutes_max': 45.0,
        'security_rescan_interval_days': 7.0,
    }


def test_require_python_floors_reads_utf8(tmp_path: Path) -> None:
    """A present file is read as UTF-8 and must contain every required key."""
    path = tmp_path / 'floors.yml'
    path.write_bytes('statement_coverage: 1\n'.encode('utf-8'))
    with pytest.raises(ThresholdError, match='missing threshold key'):
        require_python_floors(path)
    path.write_text(_YAML, encoding='utf-8')
    assert require_python_floors(path)['doc_coverage'] == 13.0


def test_complexity_gates_exact_rows_and_boundaries() -> None:
    """Equality is a pass for <= and >= floors; High missing rows use fixed copy."""
    rows, fails = max_cc_gate(8, 8, 'Medium')
    assert rows == [
        {
            'gate': 'Cyclomatic complexity (max)',
            'actual': '8.0',
            'required': '<= 8',
            'ok': True,
        }
    ]
    assert fails == []
    rows, fails = max_cc_gate(8.1, 8, 'Low')
    assert rows[0]['ok'] is False
    assert fails == ['cyclomatic complexity']
    rows, fails = max_cc_gate(None, 8, 'High')
    assert rows == [
        {
            'gate': 'Cyclomatic complexity (max)',
            'actual': 'missing or unparsable radon_cc.json',
            'required': '<= 8',
            'ok': False,
        }
    ]
    assert fails == ['cyclomatic complexity']
    assert max_cc_gate(None, 8, 'Medium') == ([], [])

    rows, fails = avg_cc_gate(7, 7, 'Medium')
    assert rows[0] == {
        'gate': 'Cyclomatic complexity (avg)',
        'actual': '7.00',
        'required': '<= 7',
        'ok': True,
    }
    assert fails == []
    assert avg_cc_gate(None, 7, 'High')[0][0]['actual'] == 'missing or unparsable radon_cc.json'
    assert avg_cc_gate(None, 7, 'High')[1] == ['cyclomatic complexity avg']

    rows, fails = min_mi_gate(40, 40, 'Medium')
    assert rows[0] == {
        'gate': 'Maintainability index (min)',
        'actual': '40.0',
        'required': '>= 40.0',
        'ok': True,
    }
    assert min_mi_gate(39.9, 40, 'Low')[0][0]['ok'] is False
    assert min_mi_gate(None, 40, 'High')[0][0]['actual'] == 'missing or unparsable radon_mi.json'
    assert min_mi_gate(None, 40, 'High')[1] == ['maintainability index']

    rows, fails = avg_mi_gate(60, 60, 'Medium')
    assert rows[0] == {
        'gate': 'Maintainability index (avg)',
        'actual': '60.00',
        'required': '>= 60.0',
        'ok': True,
    }
    assert fails == []
    assert avg_mi_gate(None, 60, 'Medium') == ([], [])


def test_coverage_and_doc_gates_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    """Coverage, pylint, pytest, and docstring rows keep exact labels and operators."""
    t = _build_strictness()['Medium']
    rows, fails = gate_coverage_line(85.0, t, 'Medium')
    assert rows == [
        {
            'gate': 'Coverage (line)',
            'actual': '85.00%',
            'required': '>= 85.0%',
            'ok': True,
        }
    ]
    assert fails == []
    assert gate_coverage_line(84.99, t, 'Low')[0][0]['ok'] is False
    missing, fails = gate_coverage_line(None, t, 'High')
    assert missing[0]['actual'] == 'missing or unparsable coverage.json'
    assert missing[0]['ok'] is False
    assert fails == ['line coverage']
    assert gate_coverage_line(None, t, 'Medium') == ([], [])

    rows, fails = gate_coverage_branch(80.0, t, 'Medium')
    assert rows[0]['gate'] == 'Coverage (branch)'
    assert rows[0]['required'] == '>= 80.0%'
    assert rows[0]['ok'] is True
    assert gate_coverage_branch(None, t, 'High')[1] == ['branch coverage']

    rows, _fails = gate_pylint(8.0, t, 'Medium')
    assert rows == [
        {
            'gate': 'Pylint score',
            'actual': '8.00/10',
            'required': '>= 8.0',
            'ok': True,
        }
    ]
    assert gate_pylint(None, t, 'High')[0][0]['actual'] == 'missing or unparsable pylint_score.txt'
    assert gate_pylint(None, t, 'High')[1] == ['pylint score']

    rows, fails = gate_pytest_exit(0, 'Low')
    assert rows == [
        {
            'gate': 'Pytest exit code',
            'actual': '0',
            'required': '0',
            'ok': True,
        }
    ]
    assert fails == []
    bad, fails = gate_pytest_exit(1, 'Medium')
    assert bad[0]['ok'] is False
    assert fails == ['pytest']
    missing, fails = gate_pytest_exit(None, 'High')
    assert missing[0]['actual'] == (
        'missing pytest_exit_code.txt (pytest not run or test phase skipped)'
    )
    assert fails == ['pytest']
    assert gate_pytest_exit(None, 'Medium') == ([], [])

    rows, _fails = gate_docstring_coverage(85.0, t, 'Medium')
    assert rows[0]['gate'] == 'Docstring coverage'
    assert rows[0]['actual'] == '85.00%'
    assert rows[0]['ok'] is True
    assert gate_docstring_coverage(None, t, 'High')[0][0]['actual'] == (
        'missing or unparsable interrogate.txt'
    )
    assert gate_docstring_coverage(None, t, 'High')[1] == ['docstring coverage']

    rows, fails = gate_docstring_issue_rate(1000, 5, t)
    assert rows == [
        {
            'gate': 'Docstring issue rate (per KLoC comments)',
            'actual': '5.00',
            'required': '<= 5.0',
            'ok': True,
        }
    ]
    assert fails == []
    assert gate_docstring_issue_rate(0, 5, t) == ([], [])
    assert gate_docstring_issue_rate(1000, 6, t)[1] == ['docstring issue rate']


def test_duplication_and_issues_per_kloc_exact() -> None:
    """Duplication and issue-density gates use <= and add pylint to ruff."""
    t = _build_strictness()['Medium']
    rows, fails = gate_duplication(15.0, t)
    assert rows == [
        {
            'gate': 'Duplication (jscpd)',
            'actual': '15.00%',
            'required': '<= 15.0%',
            'ok': True,
        }
    ]
    assert fails == []
    missing, fails = gate_duplication(None, t)
    assert missing[0]['actual'] == '(missing or invalid jscpd-report.json)'
    assert fails == ['duplication']
    rows, fails = gate_issues_per_kloc(1000, 10, 5, t)
    assert rows == [
        {
            'gate': 'Code issues per KLoC (SLOC)',
            'actual': '15.00',
            'required': '<= 15.0',
            'ok': True,
        }
    ]
    assert fails == []
    assert gate_issues_per_kloc(0, 1, 1, t) == ([], [])
    assert gate_issues_per_kloc(1000, 10, 6, t)[0][0]['ok'] is False


def test_security_gates_exact_copy(tmp_path: Path) -> None:
    """Security rows keep exact gate names, caps, and failure labels."""
    t = _build_strictness()['High']
    (tmp_path / 'bandit.json').write_text('{"results": []}', encoding='utf-8')
    rows, fails = gate_bandit(tmp_path, t)
    assert rows == [
        {
            'gate': 'Bandit (SAST)',
            'actual': '0',
            'required': '<= 0',
            'ok': True,
        }
    ]
    assert fails == []
    (tmp_path / 'bandit.json').write_text('[]', encoding='utf-8')
    rows, fails = gate_bandit(tmp_path, t)
    assert rows[0]['actual'] == 'missing or invalid bandit.json'
    assert rows[0]['required'] == 'parseable JSON object with results[]'
    assert fails == ['bandit report']

    (tmp_path / 'gitleaks.json').write_text('[]', encoding='utf-8')
    rows, fails = gate_gitleaks(tmp_path)
    assert rows == [
        {
            'gate': 'Secret detection (Gitleaks)',
            'actual': '0',
            'required': '0 findings',
            'ok': True,
        }
    ]
    assert fails == []
    (tmp_path / 'gitleaks.json').write_text('[{}]', encoding='utf-8')
    assert gate_gitleaks(tmp_path)[1] == ['secrets detected']
    assert gitleaks_findings(tmp_path) == 1

    rows, fails = gate_semgrep(tmp_path, 'Low')
    assert rows == [] and fails == []
    rows, fails = gate_semgrep(tmp_path, 'Medium')
    assert rows[0]['gate'] == 'Semgrep (SARIF)'
    assert rows[0]['actual'] == 'missing or invalid semgrep.sarif'
    assert rows[0]['required'] == '0 error-level, <= 5 warning-level results'
    assert fails == ['semgrep report']
    (tmp_path / 'semgrep.sarif').write_text(
        '{"runs":[{"results":[{"level":"ERROR"},{"level":"Warning"},{"level":"note"}]}]}',
        encoding='utf-8',
    )
    rows, fails = gate_semgrep(tmp_path, 'High')
    assert rows == [
        {'gate': 'Semgrep (error-level)', 'actual': '1', 'required': '0', 'ok': False},
        {'gate': 'Semgrep (warning-level)', 'actual': '1', 'required': '<= 5', 'ok': True},
    ]
    assert fails == ['semgrep error-level findings']
    (tmp_path / 'semgrep.sarif').write_text(
        '{"runs":[{"results":[' + ','.join('{"level":"warning"}' for _ in range(6)) + ']}]}',
        encoding='utf-8',
    )
    rows, fails = gate_semgrep(tmp_path, 'High')
    assert rows[1]['ok'] is False
    assert fails == ['semgrep warning-level findings']

    rows, fails = gate_vulnerabilities(tmp_path, t)
    assert rows[0]['gate'] == 'pip-audit report (JSON shape)'
    assert rows[0]['actual'] == 'missing or invalid pip_audit.json'
    assert rows[0]['required'] == 'JSON array or object with dependencies'
    assert rows[1]['gate'] == 'Grype report (JSON shape)'
    assert 'missing/invalid grype.json' in rows[1]['actual']
    assert rows[2]['gate'] == 'Vulnerabilities (High)'
    assert rows[2]['required'] == '<= 0'
    assert rows[3]['gate'] == 'Vulnerabilities (Medium)'
    assert fails == ['pip-audit report', 'grype report']


def test_pip_and_grype_severity_keys() -> None:
    """Severity classification uses the documented field names and lowercase tokens."""
    assert bump_pip_severity({'severity': 'HIGH'}, 0, 0) == (1, 0)
    assert bump_pip_severity({'severity': 'critical'}, 0, 0) == (1, 0)
    assert bump_pip_severity({'description': 'Contains Critical issue'}, 0, 0) == (1, 0)
    assert bump_pip_severity({'severity': 'medium'}, 0, 0) == (0, 1)
    assert bump_pip_severity({'id': 'PYSEC-1'}, 0, 0) == (0, 1)
    assert bump_pip_severity({}, 1, 2) == (1, 2)
    assert bump_pip_severity({'description': 'fine', 'severity': 'low', 'id': ''}, 0, 0) == (0, 0)
    assert pip_dict_row_vulns({'vulns': [{'id': 'a'}]}) == [{'id': 'a'}]
    assert pip_dict_row_vulns({'vulnerabilities': ('b',)}) == ['b']
    assert pip_dict_row_vulns({}) == []

    assert grype_match_bucket('Critical') == 'high'
    assert grype_match_bucket('MEDIUM') == 'medium'
    assert grype_match_bucket('low') == 'other'
    assert count_one_grype_match({'vulnerability': {'severity': 'High'}}, 0, 0) == (1, 0)
    assert count_one_grype_match({'vulnerability': {'severity': 'medium'}}, 0, 0) == (0, 1)
    assert count_one_grype_match({}, 3, 4) == (3, 4)
    assert count_one_grype_match({'vulnerability': 'nope'}, 3, 4) == (3, 4)


def test_mypy_gate_rows_exact_and_boundaries() -> None:
    """Mypy rows use >= for coverage, < for imprecision and density, including equality."""
    t = _build_strictness()['High']
    assert skip_mypy_without_reports('Medium', False, False) is True
    assert skip_mypy_without_reports('High', False, False) is False
    assert skip_mypy_without_reports('Low', True, False) is False
    assert skip_mypy_without_reports('Low', False, True) is False

    rows, fails = type_coverage_row(95.0, t, 'High')
    assert rows == [
        {
            'gate': 'Mypy type coverage (any-exprs)',
            'actual': '95.00%',
            'required': '>= 95.0%',
            'ok': True,
        }
    ]
    assert fails == []
    assert type_coverage_row(94.99, t, 'Medium')[0][0]['ok'] is False
    missing, fails = type_coverage_row(None, t, 'High')
    assert missing[0]['actual'] == 'missing or unparsable any-exprs report'
    assert fails == ['mypy type coverage']
    assert type_coverage_row(None, t, 'Medium') == ([], [])

    rows, fails = imprecision_row(0.99, t, 'High')
    assert rows[0]['gate'] == 'Mypy imprecision (lineprecision)'
    assert rows[0]['required'] == '< 1.0%'
    assert rows[0]['ok'] is True
    assert imprecision_row(1.0, t, 'High')[0][0]['ok'] is False
    assert imprecision_row(None, t, 'High')[1] == ['mypy imprecision']
    assert imprecision_row(None, t, 'High')[0][0]['actual'] == (
        'missing or unparsable lineprecision report'
    )

    rows, fails = any_density_row(1, 1000, t, 'High')
    assert rows[0]['ok'] is False
    assert rows[0]['gate'] == 'Mypy any-expression density'
    assert rows[0]['actual'] == '1.000 per 1K SLOC (1 any / 1000 SLOC)'
    assert rows[0]['required'] == '< 1.0 per 1K SLOC'
    assert fails == ['mypy any density']
    assert any_density_row(0, 1000, t, 'Medium')[0][0]['ok'] is True
    missing, fails = any_density_row(None, 10, t, 'High')
    assert missing[0]['actual'] == 'missing or unparsable any-exprs report'
    assert fails == ['mypy any density']
    zero, fails = any_density_row(1, 0, t, 'High')
    assert zero[0]['actual'] == 'SLOC is 0 (cannot compute density)'
    assert any_density_row(None, 10, t, 'Low') == ([], [])


def test_json_helpers_and_artifact_messages(tmp_path: Path) -> None:
    """JSON helpers and artifact rules keep exact error strings and zero boundaries."""
    assert coerce_non_negative_float(0) == 0.0
    assert coerce_non_negative_float(-0.1) == 0.0
    assert coerce_non_negative_float(True, default=3.0) == 3.0
    assert coerce_non_negative_float(' 2.5 ') == 2.5
    assert coerce_non_negative_float('nope', default=4.0) == 4.0
    assert gates_rows_and_passed({'rows': [{'a': 1}, 'x'], 'passed': True}) == ([{'a': 1}], True)
    assert gates_rows_and_passed({'rows': [], 'passed': 1}) == ([], False)
    assert gates_rows_and_passed({'rows': 'nope', 'passed': True}) == ([], False)
    assert gates_rows_and_passed([]) == ([], False)

    path = tmp_path / 'ok.json'
    path.write_bytes(b'{"a": 1, "b": "caf\xff"}')
    assert read_json(path)['a'] == 1
    assert read_json(tmp_path / 'missing.json') is None

    assert artifact_rules.json_shape_error([], 'cloc.json') == 'cloc.json must be a JSON object'
    assert artifact_rules.json_shape_error({}, 'pylint.json') == 'pylint.json must be a JSON array'
    assert artifact_rules.json_shape_error({}, 'ruff.json') is None
    assert artifact_rules.json_shape_error([], 'ruff.json') is None
    assert artifact_rules.json_shape_error('x', 'ruff.json') == 'ruff.json must be array or object'
    assert artifact_rules.json_shape_error({}, 'not-configured') is None
    assert artifact_rules.json_path_present({'results': []}, ('results',)) is True
    assert artifact_rules.json_path_present({'results': None}, ('results',)) is False
    assert (
        artifact_rules.json_path_present(
            {'totals': {'percent_covered': 0}},
            (
                'totals',
                'percent_covered',
            ),
        )
        is True
    )
    assert artifact_rules.first_missing_required_path({}, 'coverage.json') == (
        'coverage.json missing totals'
    )
    assert (
        artifact_rules.first_missing_required_path(
            {'totals': {}},
            'coverage.json',
        )
        == 'coverage.json missing percent_covered'
    )
    assert artifact_rules.first_missing_required_path({}, 'bandit.json') == (
        'bandit.json missing results'
    )
    assert 'coverage.json' in HIGH_REQUIRED_FILES
    assert 'pydoclint.txt' in HIGH_REQUIRED_FILES


def test_grype_and_pip_audit_files(tmp_path: Path) -> None:
    """Grype and pip-audit readers honor severity keys in on-disk JSON."""
    (tmp_path / 'grype.json').write_text(
        '{"matches":[{"vulnerability":{"severity":"Critical"}},{"vulnerability":{"severity":"medium"}},"x"]}',
        encoding='utf-8',
    )
    assert grype_severities(tmp_path) == (1, 1)
    (tmp_path / 'pip_audit.json').write_text(
        '[{"name":"a","version":"1","vulns":[{"severity":"high"},{"id":"X"}]}]',
        encoding='utf-8',
    )
    assert pip_audit_vulns(tmp_path) == (1, 1)
