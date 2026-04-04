"""Tests for ``scripts.scorecard_summary``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts.scorecard_summary import _rule_name, render_markdown, sarif_to_payload


def test_render_markdown_table_and_no_action_verdict() -> None:
    data = {
        "repo": {"name": "github.com/foo/bar"},
        "score": 8.0,
        "checks": [
            {"name": "Binary-Artifacts", "score": 10, "reason": "no binaries"},
            {"name": "Token-Permissions", "score": 8, "reason": "read-only tokens"},
        ],
    }
    md = render_markdown(data)
    assert "github.com/foo/bar" in md
    assert "Scope: GitHub repository" in md
    assert "Binary-Artifacts" in md
    assert "Token-Permissions" in md
    assert "Package / ref" in md
    assert "9.0" in md
    assert "No immediate action required" in md
    assert "Action needed" not in md


def test_render_markdown_action_needed_low_check() -> None:
    data = {
        "repo": {"name": "github.com/x/y"},
        "checks": [
            {"name": "Dangerous-Workflow", "score": 3, "reason": "issue found"},
        ],
    }
    md = render_markdown(data)
    assert "Action needed" in md


def test_overall_from_aggregate_score_when_checks_inconclusive() -> None:
    """Declared aggregate is used only when no check has score ≥ 0."""
    data = {
        "repo": {"name": "github.com/a/b"},
        "aggregateScore": {"overall": {"score": 7.5}},
        "checks": [{"name": "X", "score": -1, "reason": "n/a"}],
    }
    md = render_markdown(data)
    assert "7.5" in md


def test_overall_prefers_check_mean_over_declared_aggregate() -> None:
    data = {
        "repo": {"name": "github.com/a/b"},
        "aggregateScore": {"overall": {"score": 7.5}},
        "checks": [{"name": "X", "score": 10, "reason": "ok"}],
    }
    md = render_markdown(data)
    aggregate_lines = [ln for ln in md.splitlines() if "Aggregate score" in ln]
    assert aggregate_lines, "expected aggregate score line in Markdown"
    assert "10.0" in aggregate_lines[0], "headline aggregate should be check mean (10.0), not aggregateScore"
    assert "| X" in md and "+---" in md


def test_check_scores_json_booleans_do_not_skew_mean() -> None:
    """JSON ``true``/``false`` must not be treated as 1.0/0.0 (``bool`` subclasses ``int``)."""
    data = {
        "repo": {"name": "github.com/a/b"},
        "checks": [
            {"name": "BadBool", "score": True, "reason": "malformed"},
            {"name": "Ok", "score": 8, "reason": "ok"},
        ],
    }
    md = render_markdown(data)
    aggregate_lines = [ln for ln in md.splitlines() if "Aggregate score" in ln]
    assert "8.0" in aggregate_lines[0]


def test_main_cli_ok(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    from scripts import scorecard_summary

    p = tmp_path / "sc.json"
    p.write_text(json.dumps({"repo": {"name": "z"}, "checks": []}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", str(p)])
    assert scorecard_summary.main() == 0
    assert "OpenSSF Scorecard" in capsys.readouterr().out


def test_main_missing_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from scripts import scorecard_summary

    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", str(tmp_path / "nope.json")])
    assert scorecard_summary.main() == 1


def test_main_bad_args(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import scorecard_summary

    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py"])
    assert scorecard_summary.main() == 2


def test_main_invalid_json(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from scripts import scorecard_summary

    p = tmp_path / "bad.json"
    p.write_text("{", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", str(p)])
    assert scorecard_summary.main() == 1


def test_main_not_object_json(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from scripts import scorecard_summary

    p = tmp_path / "arr.json"
    p.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", str(p)])
    assert scorecard_summary.main() == 1


def test_checks_not_a_list_treated_as_empty() -> None:
    md = render_markdown({"repo": {"name": "r"}, "checks": "bad"})
    assert "OpenSSF Scorecard" in md
    assert "No immediate action required" in md


def test_repo_as_string() -> None:
    md = render_markdown({"repo": "github.com/a/b", "checks": []})
    assert "github.com/a/b" in md


def test_long_reason_truncated() -> None:
    long_reason = "x" * 150
    md = render_markdown(
        {"repo": {"name": "r"}, "checks": [{"name": "C", "score": 10, "reason": long_reason}]},
        reason_max=20,
    )
    assert "…" in md
    assert "xxxxxxxx" in md


def test_negative_score_shows_na() -> None:
    md = render_markdown(
        {
            "repo": {"name": "r"},
            "checks": [{"name": "Skipped", "score": -1, "reason": "n/a"}],
        }
    )
    assert "Skipped" in md and "n/a" in md


def test_action_needed_from_low_declared_aggregate_without_check_scores() -> None:
    md = render_markdown(
        {
            "repo": {"name": "r"},
            "score": 5.0,
            "checks": [{"name": "X", "score": -1, "reason": "unknown"}],
        }
    )
    assert "Action needed" in md


def test_overall_from_mean_of_checks() -> None:
    md = render_markdown(
        {
            "repo": {"name": "r"},
            "checks": [
                {"name": "A", "score": 8, "reason": ""},
                {"name": "B", "score": 10, "reason": ""},
            ],
        }
    )
    assert "9.0" in md or "9" in md


def test_sarif_strips_lowercase_remediation_line() -> None:
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"rules": [{"id": "R", "name": "R"}]}},
                "results": [
                    {
                        "ruleId": "R",
                        "ruleIndex": 0,
                        "message": {"text": "score is 9: ok\nClick remediation below"},
                    }
                ],
            }
        ],
    }
    payload = sarif_to_payload(sarif, None)
    assert payload["checks"][0]["reason"] == "ok"


def test_sarif_to_payload_and_render() -> None:
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Scorecard",
                        "rules": [
                            {
                                "id": "CheckX",
                                "name": "Check X",
                                "shortDescription": {"text": "Check X"},
                            }
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": "CheckX",
                        "ruleIndex": 0,
                        "message": {
                            "text": (
                                "score is 10: no issues\n"
                                "Click Remediation section below to solve this issue"
                            )
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "region": {
                                        "startLine": 30,
                                        "snippet": {"text": "step-security/harden-runner@v2.16.1"},
                                    }
                                }
                            }
                        ],
                    }
                ],
            }
        ],
    }
    payload = sarif_to_payload(sarif, "github.com/o/r")
    md = render_markdown(payload)
    assert "github.com/o/r" in md
    assert "Check X" in md
    assert "Check X" in md and "10" in md and "+---" in md
    assert "step-security/harden-runner@v2.16.1" in md
    assert "Click Remediation" not in md
    assert "no issues" in md
    assert payload["checks"][0]["snippet"] == "step-security/harden-runner@v2.16.1"


def test_sarif_repo_from_run_properties() -> None:
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"rules": []}},
                "properties": {"repositoryUri": "https://github.com/from/props"},
                "results": [],
            }
        ],
    }
    payload = sarif_to_payload(sarif, "github.com/cli/fallback")
    assert payload["repo"]["name"] == "https://github.com/from/props"
    assert payload["repo"]["source"] == "sarif"


def test_sarif_repo_from_invocations_working_directory() -> None:
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"rules": []}},
                "invocations": [{"workingDirectory": {"uri": "file:///github.com/from/wd"}}],
                "results": [],
            }
        ],
    }
    payload = sarif_to_payload(sarif, "")
    assert payload["repo"]["name"] == "file:///github.com/from/wd"
    assert payload["repo"]["source"] == "sarif"


def test_sarif_vcp_skips_non_dict_entries() -> None:
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"rules": []}},
                "versionControlProvenance": [
                    "skip-me",
                    {"repositoryUri": "https://github.com/ok/repo"},
                ],
                "results": [],
            }
        ],
    }
    payload = sarif_to_payload(sarif, None)
    assert payload["repo"]["name"] == "https://github.com/ok/repo"


def test_main_fills_repo_from_github_repository_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import scorecard_summary

    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"rules": [{"id": "Z", "name": "Zed"}]}},
                "results": [{"ruleId": "Z", "ruleIndex": 0, "message": {"text": "score is 8: ok"}}],
            }
        ],
    }
    p = tmp_path / "r.sarif"
    p.write_text(json.dumps(sarif), encoding="utf-8")
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/widget")
    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", str(p)])
    assert scorecard_summary.main() == 0
    out = capsys.readouterr().out
    assert "github.com/acme/widget" in out


def test_sarif_version_control_provenance_repo_overrides_cli() -> None:
    """Analyzed repo URI comes from SARIF metadata, not the action ref in result snippets."""
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"rules": [{"id": "Z", "name": "Zed"}]}},
                "versionControlProvenance": [
                    {"repositoryUri": "https://github.com/analyzed/target-repo"}
                ],
                "results": [{"ruleId": "Z", "ruleIndex": 0, "message": {"text": "score is 8: ok"}}],
            }
        ],
    }
    payload = sarif_to_payload(sarif, "github.com/cli/fallback")
    assert payload["repo"]["name"] == "https://github.com/analyzed/target-repo"
    assert payload["repo"]["source"] == "sarif"
    md = render_markdown(payload)
    assert "https://github.com/analyzed/target-repo" in md
    assert "Scope: GitHub repository `https://github.com/analyzed/target-repo`" in md


def test_main_sarif(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    from scripts import scorecard_summary

    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"rules": [{"id": "Z", "name": "Zed"}]}},
                "results": [{"ruleId": "Z", "ruleIndex": 0, "message": {"text": "score is 8: ok"}}],
            }
        ],
    }
    p = tmp_path / "out.sarif"
    p.write_text(json.dumps(sarif), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["scorecard_summary.py", "--repo", "github.com/a/b", str(p)],
    )
    assert scorecard_summary.main() == 0
    out = capsys.readouterr().out
    assert "Zed" in out
    assert "github.com/a/b" in out


def test_main_unrecognized_object(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from scripts import scorecard_summary

    p = tmp_path / "x.json"
    p.write_text(json.dumps({"not": "scorecard"}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", str(p)])
    assert scorecard_summary.main() == 1


def test_main_bad_args_repo_only(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import scorecard_summary

    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", "--repo", "github.com/x/y"])
    assert scorecard_summary.main() == 2


def test_rule_name_short_description_and_id() -> None:
    assert _rule_name({"shortDescription": {"text": "  SD  "}}) == "SD"
    assert _rule_name({"id": "RID"}) == "RID"
    assert _rule_name({}) == "?"


def test_sarif_skips_non_dict_result_coerces_numeric_message_text() -> None:
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"rules": []}},
                "results": [
                    "skip-me",
                    {"ruleId": "X", "ruleIndex": 0, "message": {"text": 99}},
                ],
            }
        ],
    }
    payload = sarif_to_payload(sarif, None)
    assert len(payload["checks"]) == 1
    assert payload["checks"][0]["reason"] == "99"


def test_json_repo_dict_without_name_filled_from_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import scorecard_summary

    p = tmp_path / "sc.json"
    p.write_text(json.dumps({"checks": [], "repo": {}}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_REPOSITORY", "org/wantsname")
    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", str(p)])
    assert scorecard_summary.main() == 0
    assert "github.com/org/wantsname" in capsys.readouterr().out


def test_main_uses_github_repository_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import scorecard_summary

    p = tmp_path / "sc.json"
    p.write_text(json.dumps({"checks": []}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_REPOSITORY", "myorg/myrepo")
    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", str(p)])
    assert scorecard_summary.main() == 0
    assert "github.com/myorg/myrepo" in capsys.readouterr().out


def test_sarif_invalid_run_not_dict() -> None:
    sarif = {"version": "2.1.0", "runs": [[]]}
    with pytest.raises(ValueError, match="Invalid SARIF run"):
        sarif_to_payload(sarif, None)


def test_main_sarif_no_runs(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from scripts import scorecard_summary

    p = tmp_path / "bad.sarif"
    p.write_text(json.dumps({"version": "2.1.0", "runs": []}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["scorecard_summary.py", str(p)])
    assert scorecard_summary.main() == 1


def test_render_needs_action_float_score_below_threshold() -> None:
    md = render_markdown(
        {"repo": {"name": "r"}, "checks": [{"name": "C", "score": 5.5, "reason": "weak"}]}
    )
    assert "Action needed" in md


def test_render_action_needed_aligned_aggregate_and_low_check() -> None:
    """Headline aggregate matches check mean; low check still triggers action."""
    md = render_markdown(
        {
            "repo": {"name": "r"},
            "score": 10,
            "checks": [{"name": "Bad", "score": 3, "reason": "fix me"}],
        }
    )
    assert "Action needed" in md
    assert "3.0" in md
