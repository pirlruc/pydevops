"""Core Scorecard JSON/SARIF parsing and markdown rendering."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, TypeGuard

from scripts.scorecard_sarif_utils import (
    repo_uri_from_sarif_run,
    sarif_driver,
    snippet_from_sarif_result,
)
from scripts.scorecard_table import checks_table_block, fmt_score

_SCORE_PREFIX = re.compile(r"^score is (-?\d+):\s*")


def _is_real_number(v: object) -> TypeGuard[int | float]:
    """True for int/float values only (exclude bool)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _non_negative_score_value(v: object) -> float | None:
    """Normalize numeric score values; return None for invalid/negative."""
    if not _is_real_number(v):
        return None
    x = float(v)
    return x if x >= 0 else None


def _aggregate_overall_score(data: dict) -> float | None:
    """Extract score from aggregateScore.overall.score when present."""
    agg = data.get("aggregateScore")
    if not isinstance(agg, dict):
        return None
    overall = agg.get("overall")
    if not isinstance(overall, dict):
        return None
    return _non_negative_score_value(overall.get("score"))


def _checks(data: dict) -> list[dict]:
    """Return normalized check dicts from Scorecard JSON payload."""
    raw = data.get("checks")
    if not isinstance(raw, list):
        return []
    return [c for c in raw if isinstance(c, dict)]


def _overall_score(data: dict, checks: list[dict]) -> float | None:
    """Compute aggregate score using check mean, top-level score, or aggregate fallback."""
    scores = [x for c in checks if (x := _non_negative_score_value(c.get("score"))) is not None]
    if scores:
        return sum(scores) / len(scores)
    top = _non_negative_score_value(data.get("score"))
    if top is not None:
        return top
    return _aggregate_overall_score(data)


def _needs_action(checks: list[dict], overall: float | None, threshold: float = 6.0) -> bool:
    """True when aggregate/check score is below review threshold."""
    if overall is not None and overall < threshold:
        return True
    for c in checks:
        sc = _non_negative_score_value(c.get("score"))
        if sc is not None and sc < threshold:
            return True
    return False


def _rule_name(rule: dict[str, Any]) -> str:
    """Resolve human-readable rule name from SARIF rule object."""
    name = rule.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    sd = rule.get("shortDescription")
    if isinstance(sd, dict):
        t = sd.get("text")
        if isinstance(t, str) and t.strip():
            return t.strip()
    rid = rule.get("id")
    return str(rid) if rid else "?"


def _sarif_result_to_check(
    res: dict[str, Any],
    rule_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Map one SARIF result entry into a Scorecard check row."""
    rid = str(res.get("ruleId", ""))
    msg_obj = res.get("message")
    text = msg_obj.get("text", "") if isinstance(msg_obj, dict) else ""
    if not isinstance(text, str):
        text = str(text)
    score = -1
    reason = text.strip()
    m = _SCORE_PREFIX.match(text)
    if m:
        score = int(m.group(1))
        reason = text[m.end() :].strip()
    for cut in ("\nClick Remediation", "\nClick remediation"):
        if cut in reason:
            reason = reason.split(cut, 1)[0].strip()
    rule = rule_by_id.get(rid, {})
    name = _rule_name(rule) if rule else rid or "?"
    return {
        "name": name,
        "score": score,
        "reason": reason,
        "snippet": snippet_from_sarif_result(res),
    }


def sarif_to_payload(sarif: dict[str, Any], repo_display: str | None) -> dict[str, Any]:
    """Build a Scorecard-like payload (repo + checks) from Scorecard SARIF 2.1.0."""
    runs = sarif.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("SARIF has no runs")
    run0 = runs[0]
    if not isinstance(run0, dict):
        raise ValueError("Invalid SARIF run")
    driver = sarif_driver(run0)
    rules_raw = driver.get("rules")
    rules_list: list[dict[str, Any]] = rules_raw if isinstance(rules_raw, list) else []
    rule_by_id = {str(r["id"]): r for r in rules_list if isinstance(r, dict) and r.get("id")}
    results_raw = run0.get("results")
    results: list[dict[str, Any]] = results_raw if isinstance(results_raw, list) else []
    checks: list[dict[str, Any]] = []
    for res in results:
        if isinstance(res, dict):
            checks.append(_sarif_result_to_check(res, rule_by_id))
    checks.sort(key=lambda c: str(c.get("name", "")))
    sarif_repo = repo_uri_from_sarif_run(run0)
    chosen = (sarif_repo or (repo_display or "").strip() or "").strip() or None
    if chosen:
        src = "sarif" if sarif_repo else "cli"
        repo: str | dict[str, str] = {"name": chosen, "source": src}
    else:
        repo = "—"
    return {"repo": repo, "checks": checks}


def render_markdown(data: dict, reason_max: int = 100) -> str:
    """Build Markdown table and verdict from Scorecard JSON or SARIF-derived payload."""
    checks = _checks(data)
    checks.sort(key=lambda c: str(c.get("name", "")))
    overall = _overall_score(data, checks)
    repo = data.get("repo")
    repo_name = "—"
    source = ""
    if isinstance(repo, dict):
        repo_name = str(repo.get("name", "—"))
        source = str(repo.get("source", "cli"))
    elif isinstance(repo, str):
        repo_name = repo

    sarif_note = ""
    if source == "sarif":
        sarif_note = (
            " _(URI from Scorecard SARIF metadata — the **GitHub repository** analyzed; "
            "not a dependency package or the `ossf/scorecard-action` line in your workflow)_"
        )

    lines: list[str] = [
        "## OpenSSF Scorecard summary",
        "",
        f"- **Repository analyzed:** `{repo_name}`{sarif_note}",
        f"- **Aggregate score (0–10, higher is better):** {fmt_score(overall)}",
        "",
        "### Checks",
        "",
    ]
    table_caption: str | None = None
    if repo_name != "—":
        table_caption = f"Scope: GitHub repository `{repo_name}` (OpenSSF Scorecard target)"
    lines.extend(checks_table_block(checks, reason_max, repo_caption=table_caption))
    lines.append("")
    action = _needs_action(checks, overall)
    if action:
        verdict = (
            "**Action needed:** review checks with score below 6 or aggregate below 6, "
            "and address Scorecard documentation for those rules."
        )
    else:
        verdict = (
            "**No immediate action required:** aggregate and per-check scores are at or above the "
            "review threshold (6/10). Re-run periodically as the repo changes."
        )
    lines.extend(["", "### Verdict", "", verdict, ""])
    return "\n".join(lines)


def _parse_input(path: Path, repo_display: str | None) -> dict[str, Any]:
    """Load Scorecard JSON/SARIF from file and normalize to summary payload shape."""
    raw_txt = path.read_text(encoding="utf-8")
    data = json.loads(raw_txt)
    if not isinstance(data, dict):
        raise ValueError("Root JSON value must be an object")
    suffix = path.suffix.lower()
    if suffix == ".sarif" or (data.get("version") == "2.1.0" and "runs" in data):
        return sarif_to_payload(data, repo_display)
    if "checks" in data or _checks(data):
        out = dict(data)
        if repo_display and not (isinstance(out.get("repo"), dict) and out["repo"].get("name")):
            out["repo"] = {"name": repo_display, "source": "cli"}
        elif isinstance(out.get("repo"), dict):
            merged = dict(out["repo"])
            merged.setdefault("source", "cli")
            out["repo"] = merged
        return out
    raise ValueError("Unrecognized format: expected Scorecard JSON or SARIF 2.1.0")


def main() -> int:
    """CLI: [--repo github.com/owner/name] <results.json|results.sarif> -> Markdown."""
    argv = sys.argv[1:]
    repo_display: str | None = None
    if len(argv) >= 2 and argv[0] == "--repo":
        repo_display = argv[1]
        argv = argv[2:]
    if len(argv) != 1:
        msg = (
            "usage: scorecard_summary.py [--repo github.com/owner/name] "
            "<results.json|results.sarif>"
        )
        print(msg, file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.is_file():
        print(f"Missing input file: {path}", file=sys.stderr)
        return 1
    if repo_display is None:
        repo_display = (os.environ.get("GITHUB_REPOSITORY") or "").strip()
        if repo_display:
            repo_display = f"github.com/{repo_display}"
    try:
        payload = _parse_input(path, repo_display)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Invalid input: {e}", file=sys.stderr)
        return 1
    print(render_markdown(payload))
    return 0
