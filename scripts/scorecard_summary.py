#!/usr/bin/env python3
"""Turn OpenSSF Scorecard JSON or SARIF into a short Markdown report for CI logs and job summaries."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# OpenSSF Scorecard writes SARIF messages as: messageWithScore in pkg/scorecard/sarif.go
_SCORE_PREFIX = re.compile(r"^score is (-?\d+):\s*", re.MULTILINE)


def _checks(data: dict) -> list[dict]:
    """Return normalized check dicts from Scorecard JSON."""
    raw = data.get("checks")
    if not isinstance(raw, list):
        return []
    return [c for c in raw if isinstance(c, dict)]


def _overall_score(data: dict, checks: list[dict]) -> float | None:
    """Aggregate 0–10 for the summary line: mean of checks with score ≥ 0, else declared totals.

    Using the check mean first keeps the headline aligned with the table and with the
    aggregate-based branch of :func:`_needs_action`. Top-level ``score`` / ``aggregateScore``
    are only used when no check has a conclusive (non-negative) score.
    """
    scores = [
        float(c["score"])
        for c in checks
        if isinstance(c.get("score"), (int, float)) and float(c["score"]) >= 0
    ]
    if scores:
        return sum(scores) / len(scores)
    s = data.get("score")
    if isinstance(s, (int, float)) and s >= 0:
        return float(s)
    agg = data.get("aggregateScore")
    if isinstance(agg, dict):
        overall = agg.get("overall")
        if isinstance(overall, dict):
            os_ = overall.get("score")
            if isinstance(os_, (int, float)) and os_ >= 0:
                return float(os_)
    return None


def _fmt_score(v: object) -> str:
    """Format a numeric score for Markdown; non-numeric or negative → placeholder."""
    if not isinstance(v, (int, float)):
        return "—"
    if v < 0:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(int(v))


def _truncate(s: str, max_len: int) -> str:
    """Single-line reason text capped for table width."""
    s = s.replace("\n", " ").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _needs_action(checks: list[dict], overall: float | None, threshold: float = 6.0) -> bool:
    """True if aggregate or any check is below the review threshold."""
    if overall is not None and overall < threshold:
        return True
    for c in checks:
        sc = c.get("score")
        if isinstance(sc, (int, float)) and 0 <= sc < threshold:
            return True
    return False


def _rule_name(rule: dict[str, Any]) -> str:
    """Human-readable check name from a SARIF rule object."""
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


def sarif_to_payload(sarif: dict[str, Any], repo_display: str | None) -> dict[str, Any]:
    """Build a Scorecard-like dict (repo + checks) from Scorecard SARIF 2.1.0 output."""
    runs = sarif.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("SARIF has no runs")
    run0 = runs[0]
    if not isinstance(run0, dict):
        raise ValueError("Invalid SARIF run")

    driver = (run0.get("tool") or {}).get("driver") or {}
    rules_raw = driver.get("rules")
    rules_list: list[dict[str, Any]] = rules_raw if isinstance(rules_raw, list) else []
    rule_by_id = {str(r["id"]): r for r in rules_list if isinstance(r, dict) and r.get("id")}

    results_raw = run0.get("results")
    results: list[dict[str, Any]] = results_raw if isinstance(results_raw, list) else []

    checks: list[dict[str, Any]] = []
    for res in results:
        if not isinstance(res, dict):
            continue
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
        # Drop common trailing SARIF boilerplate from the reason column
        for cut in ("\nClick Remediation", "\nClick remediation"):
            if cut in reason:
                reason = reason.split(cut, 1)[0].strip()

        rule = rule_by_id.get(rid, {})
        checks.append({"name": _rule_name(rule) if rule else rid or "?", "score": score, "reason": reason})

    checks.sort(key=lambda c: str(c.get("name", "")))
    repo: str | dict[str, str] = "—"
    if repo_display:
        repo = {"name": repo_display}
    return {"repo": repo, "checks": checks}


def render_markdown(data: dict, reason_max: int = 100) -> str:
    """Build a Markdown table and verdict from parsed Scorecard JSON or SARIF-derived payload."""
    checks = _checks(data)
    checks.sort(key=lambda c: str(c.get("name", "")))
    overall = _overall_score(data, checks)
    repo = data.get("repo")
    repo_name = "—"
    if isinstance(repo, dict):
        repo_name = str(repo.get("name", "—"))
    elif isinstance(repo, str):
        repo_name = repo

    lines: list[str] = [
        "## OpenSSF Scorecard summary",
        "",
        f"- **Repository:** `{repo_name}`",
        f"- **Aggregate score (0–10, higher is better):** {_fmt_score(overall)}",
        "",
        "| Check | Score | Reason |",
        "| --- | ---: | --- |",
    ]
    for c in checks:
        name = str(c.get("name", "?"))
        reason = _truncate(str(c.get("reason", "")), reason_max)
        lines.append(f"| {name} | {_fmt_score(c.get('score'))} | {reason} |")

    action = _needs_action(checks, overall)
    lines.extend(
        [
            "",
            "### Verdict",
            "",
            "**Action needed:** review checks with score below 6 or aggregate below 6, "
            "and address Scorecard documentation for those rules."
            if action
            else "**No immediate action required:** aggregate and per-check scores are at or above the "
            "review threshold (6/10). Re-run periodically as the repo changes.",
            "",
        ]
    )
    return "\n".join(lines)


def _parse_input(path: Path, repo_display: str | None) -> dict[str, Any]:
    """Load a file as Scorecard JSON or SARIF and return a dict for :func:`render_markdown`."""
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
            out["repo"] = {"name": repo_display}
        return out

    raise ValueError("Unrecognized format: expected Scorecard JSON or SARIF 2.1.0")


def main() -> int:
    """CLI: [--repo github.com/owner/repo] <results.json|results.sarif> → Markdown on stdout."""
    argv = sys.argv[1:]
    repo_display: str | None = None
    if len(argv) >= 2 and argv[0] == "--repo":
        repo_display = argv[1]
        argv = argv[2:]

    if len(argv) != 1:
        print(
            "usage: scorecard_summary.py [--repo github.com/owner/name] <results.json|results.sarif>",
            file=sys.stderr,
        )
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


if __name__ == "__main__":
    raise SystemExit(main())
