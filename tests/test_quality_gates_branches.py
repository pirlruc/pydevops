"""Branch coverage for ``scripts.quality_gates`` helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import quality_gates as qg
from scripts.quality_gates.readers_py_coverage import pytest_exit_code


def test_pytest_exit_code_invalid_text(tmp_path: Path) -> None:
    """Non-integer pytest_exit_code.txt is treated as missing."""
    (tmp_path / "pytest_exit_code.txt").write_text("not-a-number\n", encoding="utf-8")
    assert pytest_exit_code(tmp_path) is None


def test_read_json_invalid(tmp_path: Path) -> None:
    """_read_json returns None for invalid JSON."""
    p = tmp_path / "x.json"
    p.write_text("{", encoding="utf-8")
    assert qg._read_json(p) is None


def test_pylint_score_no_match(tmp_path: Path) -> None:
    """_pylint_score returns None without rating line."""
    (tmp_path / "pylint_score.txt").write_text("no score here", encoding="utf-8")
    assert qg._pylint_score(tmp_path) is None


def test_ruff_dict_format(tmp_path: Path) -> None:
    """_ruff_issue_count handles object-shaped ruff.json."""
    (tmp_path / "ruff.json").write_text(
        json.dumps({"files": [{"messages": [{"code": "E"}]}]}),
        encoding="utf-8",
    )
    assert qg._ruff_issue_count(tmp_path) == 1


def test_ruff_files_messages_non_list_ignored(tmp_path: Path) -> None:
    """Malformed ``messages`` (null, dict, etc.) must not raise or use wrong len()."""
    (tmp_path / "ruff.json").write_text(
        json.dumps(
            {
                "files": [
                    {"messages": None},
                    {"messages": {"not": "a list"}},
                    {"messages": [{"code": "E1"}, {"code": "E2"}]},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert qg._ruff_issue_count(tmp_path) == 2


def test_radon_mi_string_value(tmp_path: Path) -> None:
    """_radon_mi_min parses string MI values."""
    (tmp_path / "radon_mi.json").write_text(json.dumps({"a.py": "70.5"}), encoding="utf-8")
    assert qg._radon_mi_min(tmp_path) == pytest.approx(70.5)


def test_radon_mi_bad_string(tmp_path: Path) -> None:
    """Invalid string MI is skipped."""
    (tmp_path / "radon_mi.json").write_text(json.dumps({"a.py": "x"}), encoding="utf-8")
    assert qg._radon_mi_min(tmp_path) is None


def test_pip_audit_tuple_row(tmp_path: Path) -> None:
    """_pip_audit_vulns handles legacy tuple rows."""
    row = ["pkg", "1.0", [{"id": "x", "severity": "HIGH", "description": ""}]]
    (tmp_path / "pip_audit.json").write_text(json.dumps([row]), encoding="utf-8")
    h, _m = qg._pip_audit_vulns(tmp_path)
    assert h >= 1


def test_pip_audit_non_dict_vuln_skipped(tmp_path: Path) -> None:
    """Non-dict entries in vulns list are skipped."""
    (tmp_path / "pip_audit.json").write_text(
        json.dumps([{"vulns": ["bad", {"id": "z", "severity": "", "description": ""}]}]),
        encoding="utf-8",
    )
    _h, m = qg._pip_audit_vulns(tmp_path)
    assert m >= 1


def test_pip_audit_dict_row(tmp_path: Path) -> None:
    """_pip_audit_vulns handles dict-shaped dependency rows."""
    row = {
        "vulns": [
            {"id": "V1", "severity": "HIGH", "description": ""},
            {"id": "V2", "severity": "medium", "description": ""},
            {"id": "V3", "description": ""},
        ]
    }
    (tmp_path / "pip_audit.json").write_text(json.dumps([row]), encoding="utf-8")
    h, m = qg._pip_audit_vulns(tmp_path)
    assert h >= 1
    assert m >= 1


def test_pip_audit_missing_returns_none(tmp_path: Path) -> None:
    """Missing pip_audit.json is treated as unreadable report, not zero vulns."""
    assert qg._pip_audit_vulns(tmp_path) is None


def test_grype_high(tmp_path: Path) -> None:
    """_grype_severities counts high/critical."""
    (tmp_path / "grype.json").write_text(
        json.dumps({"matches": [{"vulnerability": {"severity": "High"}}]}),
        encoding="utf-8",
    )
    h, m = qg._grype_severities(tmp_path)
    assert h == 1


def test_grype_match_non_dict_vulnerability_skipped(tmp_path: Path) -> None:
    """Non-dict ``vulnerability`` must not crash; valid matches still count."""
    (tmp_path / "grype.json").write_text(
        json.dumps(
            {
                "matches": [
                    {"vulnerability": "High"},
                    {"vulnerability": {"severity": "Critical"}},
                ]
            }
        ),
        encoding="utf-8",
    )
    h, m = qg._grype_severities(tmp_path)
    assert h == 1
    assert m == 0
    assert m == 0


def test_grype_medium(tmp_path: Path) -> None:
    """_grype_severities counts medium."""
    (tmp_path / "grype.json").write_text(
        json.dumps({"matches": [{"vulnerability": {"severity": "Medium"}}]}),
        encoding="utf-8",
    )
    h, m = qg._grype_severities(tmp_path)
    assert h == 0
    assert m == 1


def test_grype_non_object_root(tmp_path: Path) -> None:
    """Valid JSON array is not a Grype document."""
    (tmp_path / "grype.json").write_text("[]", encoding="utf-8")
    assert qg._grype_severities(tmp_path) is None


def test_grype_missing_returns_none(tmp_path: Path) -> None:
    """Missing grype.json is treated as unreadable report, not zero vulns."""
    assert qg._grype_severities(tmp_path) is None


def test_gitleaks_non_list(tmp_path: Path) -> None:
    """_gitleaks_findings returns 0 for non-list."""
    (tmp_path / "gitleaks.json").write_text("{}", encoding="utf-8")
    assert qg._gitleaks_findings(tmp_path) == 0


def test_interrogate_alt_regex(tmp_path: Path) -> None:
    """Second interrogate regex path."""
    (tmp_path / "interrogate.txt").write_text("Overall 88.0% covered today\n", encoding="utf-8")
    assert qg._interrogate_coverage(tmp_path) == pytest.approx(88.0)


def test_pylint_issues_list(tmp_path: Path) -> None:
    """_pylint_issue_count counts list messages."""
    (tmp_path / "pylint.json").write_text('[{"message": "x"}]', encoding="utf-8")
    assert qg._pylint_issue_count(tmp_path) == 1


def test_ruff_list_count(tmp_path: Path) -> None:
    """_ruff_issue_count uses list length when format is array."""
    (tmp_path / "ruff.json").write_text("[{}, {}]", encoding="utf-8")
    assert qg._ruff_issue_count(tmp_path) == 2


def test_pylint_issues_non_list(tmp_path: Path) -> None:
    """_pylint_issue_count returns 0 for non-list pylint.json."""
    (tmp_path / "pylint.json").write_text("{}", encoding="utf-8")
    assert qg._pylint_issue_count(tmp_path) == 0


def test_ruff_unknown_shape(tmp_path: Path) -> None:
    """_ruff_issue_count returns 0 for unrecognized JSON shape."""
    (tmp_path / "ruff.json").write_text('{"other": true}', encoding="utf-8")
    assert qg._ruff_issue_count(tmp_path) == 0


def test_jscpd_invalid_percentage_returns_none(tmp_path: Path) -> None:
    """Unparseable jscpd percentage must not raise and should return None."""
    from scripts.quality_gates.readers_ruff_jscpd import jscpd_duplication_pct

    (tmp_path / "jscpd-report.json").write_text(
        json.dumps({"statistics": {"total": {"percentage": ""}}}),
        encoding="utf-8",
    )
    assert jscpd_duplication_pct(tmp_path) is None


def test_radon_cc_skips_nonlist_blocks(tmp_path: Path) -> None:
    """_radon_cc_max skips values that are not block lists."""
    (tmp_path / "radon_cc.json").write_text(json.dumps({"a.py": "bad"}), encoding="utf-8")
    assert qg._radon_cc_max(tmp_path) is None


def test_radon_cc_max_zero_is_valid(tmp_path: Path) -> None:
    """Max complexity 0.0 must not be coerced to None (float truthiness bug)."""
    (tmp_path / "radon_cc.json").write_text(
        json.dumps({"m.py": [{"complexity": 0}]}),
        encoding="utf-8",
    )
    assert qg._radon_cc_max(tmp_path) == 0.0


def test_main_failure_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main returns 1 when gates fail."""
    monkeypatch.setenv("QUALITY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("STRICTNESS_LEVEL", "High")
    # no artifacts -> high fails
    assert qg.main() == 1
