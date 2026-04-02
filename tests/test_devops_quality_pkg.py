"""Smoke test for packaged module."""

from __future__ import annotations

import devops_quality


def test_version() -> None:
    """Package exposes a version string."""
    assert isinstance(devops_quality.__version__, str)
    assert devops_quality.__version__
