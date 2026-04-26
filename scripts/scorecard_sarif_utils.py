"""SARIF utility helpers for scorecard summary parsing."""

from __future__ import annotations

from typing import Any


def _snippet_text_from_physical_location(pl: dict[str, Any]) -> str:
    region = pl.get("region")
    if not isinstance(region, dict):
        return ""
    sn = region.get("snippet")
    if not isinstance(sn, dict):
        return ""
    t = sn.get("text")
    return t.strip() if isinstance(t, str) and t.strip() else ""


def _snippet_from_one_location(loc: object) -> str:
    if not isinstance(loc, dict):
        return ""
    pl = loc.get("physicalLocation")
    if not isinstance(pl, dict):
        return ""
    return _snippet_text_from_physical_location(pl)


def _first_snippet_among_locations(locs: list[Any]) -> str:
    for loc in locs:
        got = _snippet_from_one_location(loc)
        if got:
            return got
    return ""


def snippet_from_sarif_result(res: dict[str, Any]) -> str:
    """First non-empty ``locations[].physicalLocation`` snippet text."""
    locs = res.get("locations")
    if not isinstance(locs, list):
        return ""
    return _first_snippet_among_locations(locs)


def repo_uri_from_sarif_run(run: dict[str, Any]) -> str | None:
    """Best-effort repository URI embedded in Scorecard SARIF."""
    vcp = run.get("versionControlProvenance")
    if isinstance(vcp, list):
        for item in vcp:
            if not isinstance(item, dict):
                continue
            for key in ("repositoryUri", "repositoryURL", "uri", "url", "repositoryUrl"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()

    props = run.get("properties")
    if isinstance(props, dict):
        for key in ("repositoryUri", "repository", "repo", "repositoryURL"):
            val = props.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()

    inv = run.get("invocations")
    if isinstance(inv, list):
        for item in inv:
            if not isinstance(item, dict):
                continue
            wc = item.get("workingDirectory")
            if isinstance(wc, dict):
                uri = wc.get("uri")
                if isinstance(uri, str) and uri.strip():
                    return uri.strip()
    return None


def sarif_driver(run: dict[str, Any]) -> dict[str, Any]:
    """Return the SARIF tool.driver object or raise a controlled error."""
    tool = run.get("tool")
    if tool is None:
        return {}
    if not isinstance(tool, dict):
        raise ValueError("Invalid SARIF run: tool must be an object")
    driver = tool.get("driver")
    if driver is None:
        return {}
    if not isinstance(driver, dict):
        raise ValueError("Invalid SARIF run: tool.driver must be an object")
    return driver
