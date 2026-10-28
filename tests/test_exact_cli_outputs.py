"""Exact CLI text, markdown, and I/O-argument assertions for mutation killing."""

from __future__ import annotations

import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts import (
    ci_scripts_job_summary as summary,
)
from scripts import (
    consolidate_artifacts,
    export_quality_tools_requirements,
    github_actions_pins,
    license_gate,
    pr_comment_markdown,
)
from scripts.mdutil import markdown_fenced_code_block, sanitize_markdown_table_cell
from scripts.mypy_report_anyexprs import mypy_any_exprs_totals
from scripts.mypy_report_lineprecision import mypy_imprecision_pct, mypy_lineprecision_totals
from scripts.mutmut_score_gate import main as mutmut_main
from scripts.quality_gates import engine, evaluation
from scripts.quality_gates.config import _build_strictness
from scripts.quality_gates.gates_artifacts import enforce_high_artifact_presence
from scripts.quality_gates.readers_cloc_docs import (
    cloc_slocs_comments,
    interrogate_coverage,
    pydoclint_issue_count,
)
from scripts.quality_gates.readers_py_coverage import (
    load_coverage_totals,
    pylint_score,
    pytest_exit_code,
)
from scripts.quality_gates.readers_semgrep import semgrep_sarif_error_warning_counts
from scripts.scorecard_sarif_utils import repo_uri_from_sarif_run, sarif_driver
from scripts.scorecard_summary_core import (
    _needs_action,
    _non_negative_score_value,
    _parse_input,
    _rule_name,
    _sarif_result_to_check,
    main as scorecard_main,
    render_markdown,
    sarif_to_payload,
)
from scripts.scorecard_table import checks_table_block, fmt_score, truncate


def _track_read(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, tuple[object, ...], dict[str, object]]]:
    """Record Path.read_text arguments without changing file contents."""
    seen: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
    original = Path.read_text

    def _read(self: Path, *args: object, **kwargs: object) -> str:
        seen.append((self.name, args, dict(kwargs)))
        return original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, 'read_text', _read)
    return seen


def _track_env(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, object]]:
    """Record os.environ.get defaults."""
    import os

    seen: list[tuple[str, object]] = []
    original = os.environ.get

    def _get(key: str, default: object = None) -> object:
        seen.append((key, default))
        return original(key, default)  # type: ignore[arg-type]

    monkeypatch.setattr(os.environ, 'get', _get)
    return seen


def test_scorecard_markdown_exact_order_and_verdict() -> None:
    """Rendered markdown keeps header copy, sort order, score 0, and the action line."""
    data = {
        'repo': {'name': 'github.com/z/a', 'source': 'sarif'},
        'checks': [
            {'score': 6, 'reason': 'no-name'},
            {'name': 'Zebra', 'score': 0, 'reason': 'zero'},
            {'name': 'Alpha', 'score': 10, 'reason': 'ok'},
        ],
    }
    assert render_markdown(data) == (
        '## OpenSSF Scorecard summary\n'
        '\n'
        '- **Repository analyzed:** `github.com/z/a` _(URI from Scorecard SARIF metadata — '
        'the **GitHub repository** analyzed; not a dependency package or the '
        '`ossf/scorecard-action` line in your workflow)_\n'
        '- **Aggregate score (0–10, higher is better):** 5.3\n'
        '\n'
        '### Checks\n'
        '\n'
        '```text\n'
        'Scope: GitHub repository `github.com/z/a` (OpenSSF Scorecard target)\n'
        '\n'
        '+-------+-------+---------+---------------+\n'
        '| Check | Score | Reason  | Package / ref |\n'
        '+-------+-------+---------+---------------+\n'
        '| ?     |     6 | no-name | —             |\n'
        '| Alpha |    10 | ok      | —             |\n'
        '| Zebra |     0 | zero    | —             |\n'
        '+-------+-------+---------+---------------+\n'
        '```\n'
        '\n'
        '\n'
        '### Verdict\n'
        '\n'
        '**Action needed:** review checks with score below 6 or aggregate below 6, '
        'and address Scorecard documentation for those rules.\n'
    )


def test_scorecard_no_action_at_threshold_and_string_repo() -> None:
    """Score 6 is not action-needed; a string repo is printed verbatim."""
    data = {
        'repo': 'github.com/only/str',
        'checks': [{'name': 'Maintained', 'score': 6, 'reason': 'ok'}],
    }
    md = render_markdown(data)
    assert '**No immediate action required:**' in md
    assert 'Action needed' not in md
    assert '`github.com/only/str`' in md
    assert '_(URI from Scorecard SARIF metadata' not in md
    assert _needs_action([{'score': 6.0}], 6.0) is False
    assert _needs_action([], 6.0) is False
    assert _needs_action([], 5.999) is True
    assert _needs_action([{'score': 0}], 6.0) is True
    assert _non_negative_score_value(0) == 0.0
    assert _non_negative_score_value(-0.01) is None
    assert _non_negative_score_value(True) is None


def test_scorecard_table_and_rule_name_exact() -> None:
    """Table helpers and SARIF rule names use exact defaults and ellipsis cuts."""
    assert fmt_score(True) == '—'
    assert fmt_score(-1) == 'n/a'
    assert fmt_score(0) == '0'
    assert fmt_score(1.25) == '1.2'
    assert truncate('abcdef', 6) == 'abcdef'
    assert truncate('abcdef', 5) == 'abcd…'
    assert truncate('a\nb', 10) == 'a b'
    lines = checks_table_block(
        [{'name': 'N', 'score': 1, 'reason': 'r', 'snippet': 'pkg'}],
        reason_max=10,
        repo_caption=None,
    )
    assert lines[0] == '```text'
    assert lines[-1] == '```'
    assert any(
        line.startswith('| Check |') or 'Check' in line and 'Score' in line for line in lines
    )
    joined = '\n'.join(lines)
    assert 'Package / ref' in joined
    assert '| N' in joined
    assert _rule_name({'name': '  ', 'shortDescription': {'text': 'Hello'}}) == 'Hello'
    assert _rule_name({'shortDescription': {'text': '  '}, 'id': ''}) == '?'
    assert _rule_name({'name': '  ', 'shortDescription': {'text': ''}, 'id': 'RID'}) == 'RID'


def test_sarif_payload_and_parse_input_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SARIF mapping, error strings, and read_text kwargs are exact."""
    sarif = {
        'version': '2.1.0',
        'runs': [
            {
                'tool': {
                    'driver': {
                        'rules': [
                            {'id': 'b', 'name': '  '},
                            {'id': 'a', 'shortDescription': {'text': ' Alpha '}},
                            'nope',
                        ]
                    }
                },
                'results': [
                    {'ruleId': 'b', 'message': {'text': 'score is 3: bad\nClick Remediation more'}},
                    {'ruleId': 'a', 'message': 'not-a-dict'},
                    'skip',
                    {'ruleId': 'missing', 'message': {'text': 5}},
                ],
            }
        ],
    }
    assert sarif_to_payload(sarif, 'github.com/cli/only') == {
        'repo': {'name': 'github.com/cli/only', 'source': 'cli'},
        'checks': [
            {'name': 'Alpha', 'score': -1, 'reason': '', 'snippet': ''},
            {'name': 'b', 'score': 3, 'reason': 'bad', 'snippet': ''},
            {'name': 'missing', 'score': -1, 'reason': '5', 'snippet': ''},
        ],
    }
    low = _sarif_result_to_check(
        {'ruleId': 'z', 'message': {'text': 'score is 1: x\nClick remediation tail'}},
        {},
    )
    assert low['reason'] == 'x'
    assert low['score'] == 1
    assert sarif_to_payload({'runs': [{'tool': {}, 'results': None}]}, None) == {
        'repo': '—',
        'checks': [],
    }
    with pytest.raises(ValueError, match='^SARIF has no runs$'):
        sarif_to_payload({'runs': []}, None)
    with pytest.raises(ValueError, match='^Invalid SARIF run$'):
        sarif_to_payload({'runs': ['nope']}, None)
    with pytest.raises(ValueError, match='^Invalid SARIF run: tool must be an object$'):
        sarif_driver({'tool': []})
    with pytest.raises(ValueError, match='^Invalid SARIF run: tool.driver must be an object$'):
        sarif_driver({'tool': {'driver': []}})
    assert sarif_driver({}) == {}
    assert sarif_driver({'tool': {}}) == {}

    path = tmp_path / 'in.json'
    path.write_text('{"checks": []}', encoding='utf-8')
    seen = _track_read(monkeypatch)
    payload = _parse_input(path, 'github.com/from/cli')
    assert payload['repo'] == {'name': 'github.com/from/cli', 'source': 'cli'}
    assert seen == [('in.json', (), {'encoding': 'utf-8', 'errors': 'replace'})]
    path.write_text('[1, 2]', encoding='utf-8')
    with pytest.raises(ValueError, match='^Root JSON value must be an object$'):
        _parse_input(path, None)
    path.write_text('{"version": "1"}', encoding='utf-8')
    with pytest.raises(
        ValueError, match='^Unrecognized format: expected Scorecard JSON or SARIF 2.1.0$'
    ):
        _parse_input(path, None)


@pytest.mark.parametrize(
    ('run', 'expected'),
    [
        ({'versionControlProvenance': [{'repositoryUri': ' https://a '}]}, 'https://a'),
        ({'versionControlProvenance': [{'repositoryURL': 'u'}]}, 'u'),
        ({'versionControlProvenance': [{'uri': 'uri-val'}]}, 'uri-val'),
        ({'versionControlProvenance': [{'url': 'url-val'}]}, 'url-val'),
        ({'versionControlProvenance': [{'repositoryUrl': 'ru'}]}, 'ru'),
        ({'properties': {'repositoryUri': 'p-uri'}}, 'p-uri'),
        ({'properties': {'repository': 'p-repo'}}, 'p-repo'),
        ({'properties': {'repo': 'p-r'}}, 'p-r'),
        ({'properties': {'repositoryURL': 'p-url'}}, 'p-url'),
        ({'invocations': [{'workingDirectory': {'uri': ' wd '}}]}, 'wd'),
    ],
)
def test_repo_uri_keys(run: dict, expected: str) -> None:
    """Each documented SARIF repository key is read, and surrounding space is stripped."""
    assert repo_uri_from_sarif_run(run) == expected


def test_repo_uri_blank_and_non_dict_skipped() -> None:
    """Blank strings and non-dict provenance entries do not count as a repository."""
    assert (
        repo_uri_from_sarif_run(
            {
                'versionControlProvenance': ['x', {'repositoryUri': '   '}],
                'properties': {'repositoryUri': ''},
                'invocations': ['nope', {'workingDirectory': {'uri': '  '}}],
            }
        )
        is None
    )


def test_scorecard_main_messages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI usage and invalid-input lines are exact."""
    monkeypatch.setattr(sys, 'argv', ['scorecard_summary.py'])
    assert scorecard_main() == 2
    err = capsys.readouterr().err
    assert err == (
        'usage: scorecard_summary.py [--repo github.com/owner/name] <results.json|results.sarif>\n'
    )
    missing = tmp_path / 'nope.json'
    monkeypatch.setattr(sys, 'argv', ['scorecard_summary.py', str(missing)])
    assert scorecard_main() == 1
    assert capsys.readouterr().err == f'Missing input file: {missing}\n'
    bad = tmp_path / 'bad.json'
    bad.write_text('{', encoding='utf-8')
    monkeypatch.setattr(sys, 'argv', ['scorecard_summary.py', str(bad)])
    assert scorecard_main() == 1
    assert capsys.readouterr().err.startswith('Invalid input: ')


def test_ci_summary_phrases_and_full_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Job-summary phrases, regexes, and the empty-log document are exact."""
    py = '===== 3 passed, 1 failed, 2 errors in 0.1s =====\nTOTAL 10 1 90%\n'
    assert summary._pytest_counts_phrase(py) == '**3** successful, **3** failed'
    assert summary._result_pytest(py) == (
        '**3** successful, **3** failed (all tests in `tests/` must pass)'
    )
    assert summary._result_coverage(py) == '**90%** line coverage (≥95% required)'
    assert summary._result_pylint('Your code has been rated at 9.50/10') == (
        '**9.50**/10 (≥9.5/10 required)'
    )
    assert summary._result_interrogate('actual: 95.0%') == (
        '**95.0%** docstring coverage (≥95% required on `scripts/`)'
    )
    assert '88.5%' in summary._result_interrogate('Passed: 88.5%')
    assert '12.5%' in summary._result_interrogate('12.5% interrogate')
    assert '70.0%' in summary._result_interrogate('INTERROGATE result 70.0%')
    assert (
        summary._result_pip_audit(
            'PIP-AUDIT SUMMARY: total=6 low=1 medium=2 high=3 critical=0 unknown=0'
        )
        == '**6** total: L=1, M=2, H=3, C=0, unknown=0 (M/H/C must be 0)'
    )
    assert summary._radon_cc_for_summary('Overall max CC is 4 (limit ≤ 5.0)') == (
        'Overall max CC is 4 (≤5.0 required)'
    )
    assert summary._radon_mi_for_summary('Minimum MI is 41 (must be > 40.0)') == (
        'Minimum MI is 41 (≥40.0 required)'
    )
    assert summary._passed_failed_from_summary_line('0 passed, 0 failed, 0 errors') is None
    assert summary._row_two_col('**Tests**', 'a|b') == '| **Tests** | a\\|b |'
    assert summary._log_tail_fence('', 3) == '(empty)'
    assert summary._log_tail_fence('a\nb\nc', 2) == 'b\nc'
    monkeypatch.chdir(tmp_path)
    seen = _track_read(monkeypatch)
    assert summary.build_summary() == (
        '## Scripts quality (CI)\n'
        '\n'
        '| Analysis | Result |\n'
        '| --- | --- |\n'
        '| **Tests** | — (all tests in `tests/` must pass) |\n'
        '| **Code Coverage** | — (≥95% required) |\n'
        '| **Code Quality** | — (≥9.5/10 required) |\n'
        '| **Documentation Coverage** | — (≥95% required on `scripts/`) |\n'
        '| **Cyclomatic Complexity** | — |\n'
        '| **Maintainability Index** | — |\n'
        '| **Dependency Vulnerabilities (pip-audit)** | — (medium/high/critical must be 0) |\n'
        '\n'
        '<details><summary>Raw log tails</summary>\n'
        '\n'
        '### pytest\n'
        '\n'
        '```text\n'
        '(empty)\n'
        '```\n'
        '\n'
        '### pylint\n'
        '\n'
        '```text\n'
        '(empty)\n'
        '```\n'
        '\n'
        '### interrogate\n'
        '\n'
        '```text\n'
        '(empty)\n'
        '```\n'
        '\n'
        '### Radon CC\n'
        '\n'
        '```text\n'
        '(empty)\n'
        '```\n'
        '\n'
        '### Radon MI\n'
        '\n'
        '```text\n'
        '(empty)\n'
        '```\n'
        '\n'
        '### pip-audit\n'
        '\n'
        '```text\n'
        '(empty)\n'
        '```\n'
        '\n'
        '</details>\n'
    )
    assert seen == []
    (tmp_path / '_ci_summary').mkdir()
    (tmp_path / '_ci_summary' / 'pytest.txt').write_bytes(b'caf\xff')
    summary._read('pytest.txt')
    assert seen[-1][0] == 'pytest.txt'
    assert seen[-1][2] == {'encoding': 'utf-8', 'errors': 'replace'}


def test_license_hits_and_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """License messages, NOASSERTION, and env defaults are exact."""
    pkgs = [{'name': 'p', 'licenseConcluded': 'NOASSERTION'}]
    assert license_gate._find_license_hits(pkgs, ['noassertion']) == []
    hits = license_gate._find_license_hits(
        [{'licenseConcluded': 'GPL-3.0-only'}],
        ['gpl'],
    )
    assert hits == ["?: GPL-3.0-only (matched deny pattern(s) 'gpl')"]
    hits = license_gate._find_license_hits(
        [{'name': 'q', 'licenseDeclared': 'MIT'}],
        ['mit'],
    )
    assert hits == ["q: MIT (matched deny pattern(s) 'mit')"]
    misses = license_gate._find_allow_misses(
        [{'name': 'q', 'licenseConcluded': 'GPL-3.0'}],
        ['mit'],
    )
    assert misses == ['q: GPL-3.0 (not on license_allow_list)']
    assert (
        license_gate._find_allow_misses(
            [{'name': 'q', 'licenseConcluded': 'MIT'}],
            ['mit'],
        )
        == []
    )
    assert license_gate._parse_yaml_bracket_list(
        'license_allow_list: ["MIT"]\n', 'license_allow_list'
    ) == [
        'mit',
    ]
    assert license_gate._parse_yaml_bracket_list('other: []\n', 'license_allow_list') is None

    monkeypatch.delenv('SPDX_SBOM_PATH', raising=False)
    monkeypatch.delenv('LICENSE_DENY_LIST', raising=False)
    monkeypatch.delenv('LICENSE_ALLOW_LIST', raising=False)
    monkeypatch.chdir(tmp_path)
    seen_env = _track_env(monkeypatch)
    assert license_gate.main() == 1
    err = capsys.readouterr().err
    assert err == 'No SPDX SBOM at quality-output/sbom-spdx.json; license gate fails closed.\n'
    assert ('SPDX_SBOM_PATH', 'quality-output/sbom-spdx.json') in seen_env
    assert ('LICENSE_DENY_LIST', '[]') in seen_env

    sbom = tmp_path / 'sbom.json'
    sbom.write_text(
        '{"packages": [{"name": "p", "licenseConcluded": "GPL-2.0"}]}', encoding='utf-8'
    )
    monkeypatch.setenv('SPDX_SBOM_PATH', str(sbom))
    monkeypatch.setenv('LICENSE_DENY_LIST', '["gpl"]')
    monkeypatch.setenv('LICENSE_ALLOW_LIST', '["mit"]')
    seen = _track_read(monkeypatch)
    assert license_gate.main() == 1
    err = capsys.readouterr().err
    assert err.startswith('Denied licenses detected in SPDX SBOM:\n')
    assert "  - p: GPL-2.0 (matched deny pattern(s) 'gpl')\n" in err
    assert seen[-1][2] == {'encoding': 'utf-8', 'errors': 'replace'}

    sbom.write_text(
        '{"packages": [{"name": "p", "licenseConcluded": "Apache-2.0"}]}', encoding='utf-8'
    )
    assert license_gate.main() == 1
    assert capsys.readouterr().err.startswith('Licenses not on SC-LIC-001 allow-list:\n')


def test_consolidate_and_pr_comment_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report markdown, zip members, and PR comment text are exact."""

    class _Fixed:
        @staticmethod
        def now(tz: object = None) -> datetime:
            return datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC)

    monkeypatch.setattr(consolidate_artifacts, 'datetime', _Fixed)
    monkeypatch.setenv('QUALITY_OUTPUT_DIR', str(tmp_path))
    (tmp_path / 'summary_ruff.txt').write_text('hello|there', encoding='utf-8')
    (tmp_path / 'gates.json').write_text(
        json.dumps(
            {
                'passed': True,
                'rows': [
                    {
                        'gate': 'G|H',
                        'actual': '1',
                        'required': '2',
                        'ok': True,
                    }
                ],
            }
        ),
        encoding='utf-8',
    )
    assert consolidate_artifacts.main() == 0
    report = (tmp_path / 'quality_report.md').read_text(encoding='utf-8')
    assert report == (
        '# Consolidated quality report\n'
        '\n'
        'Generated: 2020-01-02 03:04:05 UTC\n'
        'Overall: **PASSED**\n'
        '\n'
        '## Gate summary\n'
        '\n'
        '| Gate | Actual | Required | Status |\n'
        '| --- | --- | --- | --- |\n'
        '| G¦H | 1 | 2 | PASS |\n'
        '\n'
        '\n'
        '## Per-tool console excerpts\n'
        '\n'
        '### ruff\n'
        '\n'
        '```\n'
        'hello|there\n'
        '```\n'
        '\n'
    )
    with zipfile.ZipFile(tmp_path / 'quality_bundle.zip') as zf:
        names = sorted(zf.namelist())
        assert 'quality_bundle.zip' not in names
        assert 'summary_ruff.txt' in names
        info = zf.getinfo('summary_ruff.txt')
        assert info.compress_type == zipfile.ZIP_DEFLATED
    out = capsys.readouterr().out
    assert out == f'Wrote {tmp_path / "quality_report.md"} and {tmp_path / "quality_bundle.zip"}\n'

    assert pr_comment_markdown.main() == 0
    comment = capsys.readouterr().out
    assert comment == (
        '## Quality-as-a-Service summary\n'
        '\n'
        '**Overall:** PASSED\n'
        '\n'
        '| Gate | Actual | Required | Status |\n'
        '| --- | --- | --- | --- |\n'
        '| G¦H | 1 | 2 | PASS |\n'
    )
    (tmp_path / 'gates.json').unlink()
    assert pr_comment_markdown.main() == 0
    assert capsys.readouterr().out == '## Quality pipeline\n\n_No gates output found._\n'
    (tmp_path / 'gates.json').write_text('{', encoding='utf-8')
    assert pr_comment_markdown.main() == 0
    assert capsys.readouterr().out == (
        '## Quality-as-a-Service summary\n\n'
        '_`gates.json` could not be parsed as JSON (e.g. truncated output or cancelled job); '
        'see workflow artifacts for partial outputs._\n'
    )


def test_mdutil_fence_and_cell() -> None:
    """Fence length exceeds interior backticks; cells replace pipes and cap length."""
    assert markdown_fenced_code_block('a```b') == '````\na```b\n````\n'
    assert sanitize_markdown_table_cell('a|b\nc\td', max_len=500) == 'a¦b c d'
    assert sanitize_markdown_table_cell('x' * 5, max_len=4) == 'xxx…'
    assert sanitize_markdown_table_cell('abcd', max_len=4) == 'abcd'


def test_engine_and_evaluate_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Engine CLI copy and gates.json payload use exact keys and defaults."""
    monkeypatch.setattr(sys, 'argv', ['qg', '--help'])
    with pytest.raises(SystemExit) as exc:
        engine.main()
    assert exc.value.code == 0
    help_out = capsys.readouterr().out
    assert 'usage: python -m scripts.quality_gates' in help_out
    assert 'Only enforce High-tier Semgrep SARIF policy (after' in help_out
    assert 'shield scan).' in help_out

    captured: dict[str, object] = {}

    def _fake(
        root: Path, strictness: str, *, shield_only: bool
    ) -> tuple[bool, list[dict[str, object]]]:
        captured['root'] = root
        captured['strictness'] = strictness
        captured['shield'] = shield_only
        return True, [{'ok': True, 'gate': 'G', 'actual': 'a', 'required': 'r'}]

    monkeypatch.setattr(engine, '_evaluate', _fake)
    monkeypatch.setattr(sys, 'argv', ['qg'])
    monkeypatch.delenv('QUALITY_OUTPUT_DIR', raising=False)
    monkeypatch.delenv('STRICTNESS_LEVEL', raising=False)
    seen = _track_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    assert engine.main() == 0
    assert captured['strictness'] == 'Medium'
    assert captured['shield'] is False
    assert Path(str(captured['root'])).name == 'quality-output'
    assert ('QUALITY_OUTPUT_DIR', 'quality-output') in seen
    assert ('STRICTNESS_LEVEL', 'Medium') in seen
    out = capsys.readouterr().out
    assert out == (
        '=== Quality gate summary ===\n'
        '  [PASS] G: a (required: r)\n'
        '\n'
        'All evaluated quality gates passed.\n'
    )

    def _fail(
        root: Path, strictness: str, *, shield_only: bool
    ) -> tuple[bool, list[dict[str, object]]]:
        return False, [{'ok': False, 'gate': 'G', 'actual': '1', 'required': '0'}]

    monkeypatch.setattr(engine, '_evaluate', _fail)
    assert engine.main() == 1
    captured_io = capsys.readouterr()
    assert '  [FAIL] G: 1 (required: 0)\n' in captured_io.out
    assert captured_io.err == '\nQuality gates FAILED.\n'

    def _boom(
        root: Path, strictness: str, *, shield_only: bool
    ) -> tuple[bool, list[dict[str, object]]]:
        raise ThresholdError('missing key')

    from scripts.org_thresholds import ThresholdError

    monkeypatch.setattr(engine, '_evaluate', _boom)
    assert engine.main() == 1
    assert capsys.readouterr().err == 'CI-022: missing key\n'

    monkeypatch.setattr(
        evaluation,
        'collect_gate_results',
        lambda root, strictness: ([{'ok': True, 'gate': 'G'}], ['x']),
    )
    passed, rows = evaluation.evaluate(tmp_path, 'Low')
    assert passed is False
    assert rows == [{'ok': True, 'gate': 'G'}]
    text = (tmp_path / 'gates.json').read_text(encoding='utf-8')
    assert json.loads(text) == {
        'passed': False,
        'failures': ['x'],
        'rows': [{'ok': True, 'gate': 'G'}],
    }
    assert text.startswith('{\n')

    rows_out: list[dict[str, object]] = []
    fails: list[str] = []
    evaluation._coverage_and_lint(
        tmp_path,
        _build_strictness()['High'],
        'High',
        True,
        rows_out,
        fails,
    )
    assert rows_out[0] == {
        'gate': 'Package mode',
        'actual': 'scripts',
        'required': 'skip install, mypy, and coverage floors',
        'ok': True,
    }


def test_mutmut_gate_messages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Mutmut score gate prints exact pass, fail, and validation errors."""
    stats = tmp_path / 'stats.json'
    stats.write_text('{"killed": 85, "survived": 15}', encoding='utf-8')
    monkeypatch.setenv('MUTMUT_CICD_STATS', str(stats))
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '85')
    seen = _track_read(monkeypatch)
    assert mutmut_main() == 0
    out = capsys.readouterr().out
    assert out == ('Mutmut mutation score: 85.00% (killed=85, survived=15, required_min=85.0)\n')
    assert seen[-1][2] == {'encoding': 'utf-8'}
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '85.01')
    assert mutmut_main() == 1
    assert capsys.readouterr().err == 'mutmut score gate: FAILED (score 85.00% < 85.01)\n'
    monkeypatch.setenv('MUTMUT_MIN_SCORE', 'nope')
    assert mutmut_main() == 1
    assert "MUTMUT_MIN_SCORE must be a number, got 'nope'" in capsys.readouterr().err
    monkeypatch.setenv('MUTMUT_MIN_SCORE', 'nan')
    assert mutmut_main() == 1
    assert 'must not be NaN' in capsys.readouterr().err
    stats.write_text('{"killed": 100, "survived": 0}', encoding='utf-8')
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '100')
    assert mutmut_main() == 0
    capsys.readouterr()
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '100.1')
    assert mutmut_main() == 1
    assert 'must be between 0 and 100, got 100.1' in capsys.readouterr().err
    stats.write_text('{"killed": 0, "survived": 1}', encoding='utf-8')
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '0')
    assert mutmut_main() == 0
    capsys.readouterr()
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '-0.1')
    assert mutmut_main() == 1
    assert 'must be between 0 and 100, got -0.1' in capsys.readouterr().err
    stats.write_text('{"killed": "85", "survived": 1}', encoding='utf-8')
    monkeypatch.setenv('MUTMUT_MIN_SCORE', '85')
    assert mutmut_main() == 1
    assert 'need integer killed/survived' in capsys.readouterr().err
    stats.write_text('{"killed": 0, "survived": 0}', encoding='utf-8')
    assert mutmut_main() == 1
    assert 'need integer killed/survived' in capsys.readouterr().err
    stats.write_text('[]', encoding='utf-8')
    assert mutmut_main() == 1
    assert 'stats root must be a JSON object' in capsys.readouterr().err
    stats.write_text('{', encoding='utf-8')
    assert mutmut_main() == 1
    assert 'invalid JSON' in capsys.readouterr().err


def test_github_pins_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Pin drift messages, SHA shape, and apply comments are exact."""
    sha = 'a' * 40
    assert github_actions_pins._is_sha_ref(sha) is True
    assert github_actions_pins._is_sha_ref('a' * 39) is False
    assert github_actions_pins._is_sha_ref('g' * 40) is False
    assert github_actions_pins._tag_sha_pair({'tag': 'v1', 'sha': sha}) == ('v1', sha)
    assert github_actions_pins._tag_sha_pair({'tag': 1, 'sha': sha}) is None
    assert github_actions_pins._tag_sha_pair({'sha': sha}) is None
    assert github_actions_pins._split_action_ref('./local@v1') is None
    assert github_actions_pins._split_action_ref('no-at') is None
    pins = {'org/act': {'tag': 'v1.2.3', 'sha': sha}}
    wf = tmp_path / 'ci.yml'
    wf.write_text(
        f'jobs:\n  t:\n    steps:\n      - uses: org/act@{sha} # v9.9.9\n', encoding='utf-8'
    )
    errs = github_actions_pins._check_file(wf, pins)  # type: ignore[arg-type]
    assert errs == [f"{wf}: org/act@{sha} should include 'v1.2.3' in trailing comment"]
    wf.write_text(f'      - uses: org/act@{sha}\n', encoding='utf-8')
    errs = github_actions_pins._check_file(wf, pins)  # type: ignore[arg-type]
    assert errs == [
        f"{wf}: org/act@{sha} should keep a trailing version comment like '# v1.2.3'",
    ]
    wf.write_text('      - uses: org/act@v1\n', encoding='utf-8')
    errs = github_actions_pins._check_file(wf, pins)  # type: ignore[arg-type]
    assert errs == [f'{wf}: org/act@v1 must be pinned to a 40-char commit SHA']
    other = 'b' * 40
    wf.write_text(f'      - uses: org/act@{other} # v1.2.3\n', encoding='utf-8')
    errs = github_actions_pins._check_file(wf, pins)  # type: ignore[arg-type]
    assert errs == [f'{wf}: org/act@{other} expected @{sha}']
    assert github_actions_pins._apply_file(wf, pins) is True  # type: ignore[arg-type]
    text = wf.read_text(encoding='utf-8')
    assert text == f'      - uses: org/act@{sha} # v1.2.3\n'
    assert github_actions_pins._repo_root().name != ''
    gh = tmp_path / '.github'
    (gh / 'workflows').mkdir(parents=True)
    (gh / 'actions' / 'local').mkdir(parents=True)
    (gh / 'workflows' / 'ci.yml').write_text('name: ci\n', encoding='utf-8')
    (gh / 'actions' / 'local' / 'action.yml').write_text('name: local\n', encoding='utf-8')
    found = github_actions_pins._yaml_files(tmp_path)
    assert [p.name for p in found] == ['ci.yml', 'action.yml']


def test_export_header_exact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exported requirements keep the generated header and string pins only."""
    pyproject = tmp_path / 'pyproject.toml'
    out_dir = tmp_path / '.github' / 'dependencies' / 'quality-tools'
    out_dir.mkdir(parents=True)
    pyproject.write_text(
        '[dependency-groups]\nquality-tools = ["ruff==1.0.0"]\n',
        encoding='utf-8',
    )
    seen = _track_read(monkeypatch)
    export_quality_tools_requirements.export_quality_tools_requirements(tmp_path)
    text = (tmp_path / '.github' / 'dependencies' / 'quality-tools' / 'requirements.txt').read_text(
        encoding='utf-8'
    )
    assert text == (
        '# Pinned CLI tools for python-quality.yml (uv tool install). '
        'Generated by scripts/export_quality_tools_requirements.py from pyproject.toml. '
        'Dependabot: uv, /\n'
        'ruff==1.0.0\n'
    )
    assert seen[0][2] == {'encoding': 'utf-8'}
    with pytest.raises(SystemExit, match='missing \\[dependency-groups\\]'):
        export_quality_tools_requirements._groups_table({})
    with pytest.raises(SystemExit, match='invalid structure'):
        export_quality_tools_requirements._groups_table([])
    with pytest.raises(SystemExit, match='only string pins allowed'):
        export_quality_tools_requirements._quality_tools_entries({'quality-tools': [1]})


def test_readers_exact_keys(tmp_path: Path) -> None:
    """Coverage, pylint, cloc, interrogate, and mypy readers use exact keys and regexes."""
    (tmp_path / 'coverage.json').write_text(
        '{"totals": {"percent_covered": 91.5, "percent_branches_covered": "80"}}',
        encoding='utf-8',
    )
    assert load_coverage_totals(tmp_path) == (91.5, 80.0)
    (tmp_path / 'pylint_score.txt').write_text('rated at 9.87/10\n', encoding='utf-8')
    assert pylint_score(tmp_path) == 9.87
    (tmp_path / 'pytest_exit_code.txt').write_text('0\n', encoding='utf-8')
    assert pytest_exit_code(tmp_path) == 0
    (tmp_path / 'cloc.json').write_text(
        '{"Python": {"code": "10", "comment": 2}}',
        encoding='utf-8',
    )
    assert cloc_slocs_comments(tmp_path) == (10.0, 2.0)
    (tmp_path / 'interrogate.txt').write_text('TOTAL COVERAGE: 95.5%\n', encoding='utf-8')
    assert interrogate_coverage(tmp_path) == 95.5
    (tmp_path / 'pydoclint.txt').write_text(
        'a.py:1:1: ERROR D100\nsummary: 1\n',
        encoding='utf-8',
    )
    assert pydoclint_issue_count(tmp_path) == 1
    any_dir = tmp_path / 'mypy-reports' / 'anyexprs'
    any_dir.mkdir(parents=True)
    (any_dir / 'any-exprs.txt').write_text(
        'Name  Anys  Exprs  Coverage\nmod  1  4  75.0%\nTotal  1  4  75.0%\n',
        encoding='utf-8',
    )
    assert mypy_any_exprs_totals(tmp_path) == (1, 4, 75.0)
    lp = tmp_path / 'mypy-reports' / 'lineprecision'
    lp.mkdir()
    (lp / 'lineprecision.txt').write_text(
        'Name  Lines  Precise  Imprecise  x y z\nmod  10  8  2  0  0  0\n',
        encoding='utf-8',
    )
    assert mypy_lineprecision_totals(tmp_path) == (10, 8, 2)
    assert mypy_imprecision_pct(tmp_path) == 20.0
    (tmp_path / 'semgrep.sarif').write_text(
        '{"runs":[1, {"results": "nope"}, {"results": [{"level": "error"}]}]}',
        encoding='utf-8',
    )
    assert semgrep_sarif_error_warning_counts(tmp_path) == (1, 0)
    rows, fails = enforce_high_artifact_presence(tmp_path, 'Low')
    assert rows == [] and fails == []


def test_high_artifact_missing_row(tmp_path: Path) -> None:
    """A missing High artifact row uses the exact actual and required strings."""
    rows, fails = enforce_high_artifact_presence(tmp_path, 'High')
    assert rows[0] == {
        'gate': 'Required artifact (coverage.json)',
        'actual': 'missing or empty',
        'required': 'must exist for High',
        'ok': False,
    }
    assert fails[0] == 'missing artifact: coverage.json'
    assert len(rows) == len(fails)
