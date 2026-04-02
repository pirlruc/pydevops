#!/usr/bin/env bash
# Emit Astral uv CLI version for GitHub Actions (reads uv-version.txt next to this script).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
v=$(tr -d ' \n\r\t' < "${HERE}/uv-version.txt")
echo "version=${v}" >> "${GITHUB_OUTPUT}"
