# ci-python

Short-lived Python quality image for GitHub Actions. Not a product runtime —
no `HEALTHCHECK`.

## Image

| Item | Value |
|------|--------|
| Docker Hub | `pirlruc/ci-python` |
| Architectures | `linux/amd64` |
| User | non-root `1000:1000` |
| Base | Debian 13 via `dhi.io/python` for the unsuffixed tag; Alpine 3.24 for `-alpine` |

The image is not published yet. Tags appear at the 3.1.0 release. Until then,
`python-quality.yml` still installs the toolchain on the runner.

### Tags (after 3.1.0)

| Tag | Meaning |
|-----|---------|
| `3.1.0` | First Debian analysis image |
| `3.1.0-alpine` | Alpine analysis image |
| `latest` | Latest non-prerelease Debian publish |

Prefer a digest. `latest` is never the only tag.

## Hardened local run

```bash
docker run --rm \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  -v "$PWD:/workspace:ro" -w /workspace \
  pirlruc/ci-python:3.1.0 \
  ruff --version
```

## What is inside

ruff, pylint, mypy, pytest, bandit, pip-audit, syft, grype, jscpd, cloc, jq,
Node, and uv. Consumer project dependencies are not baked in. Jobs still run
`uv sync`.

## Verify a publish

Pull by digest after the release writes the digest back. Signing is skipped
while the repo is private (`SC-SIGN-001`). The registry stores BuildKit
provenance (`mode=max`) and an SBOM.

## License

MIT. Source: https://github.com/pirlruc/pydevops
