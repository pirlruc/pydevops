#!/usr/bin/env bash
# Refresh uv.lock and regenerate quality-tools/requirements.txt (direct pins only).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
uv lock
python3 scripts/export_quality_tools_requirements.py
