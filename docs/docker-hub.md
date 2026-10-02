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

Release 3.1.0 is on GitHub Packages
(`ghcr.io/pirlruc/ci-python`). Docker Hub repository `pirlruc/ci-python`
exists. Release 3.1.2 is the first publish to that repository.
`python-quality.yml` runs static, supply-chain, and test jobs in the
GHCR image. dast stays on the host.

### Tags (GHCR 3.1.0; Hub tags arrive with 3.1.2)

| Tag | Meaning |
|-----|---------|
| `3.1.0` | Debian analysis. Digest `sha256:00b55d327ee2a8c78d4d428281819d64db4fad8a965e2cdb1c1b45c091831101` |
| `3.1.0-alpine` | Alpine analysis. Digest `sha256:05571768e616c05a32d66919cf748da6108b79a879136f68acf29198a81fd32b` |
| `latest` | Latest non-prerelease Debian publish |

3.1.0 has no `-debian` tag and no `latest-alpine`. The next publish adds both,
matching `ci-lint`. Debian owns the unsuffixed tag. Prefer a digest. `latest`
is never the only tag.

## Hardened local run

```bash
docker run --rm \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  -v "$PWD:/workspace:ro" -w /workspace \
  ghcr.io/pirlruc/ci-python@sha256:00b55d327ee2a8c78d4d428281819d64db4fad8a965e2cdb1c1b45c091831101 \
  ruff --version
```

## What is inside

ruff, pylint, mypy, pytest, bandit, pip-audit, syft, grype, jscpd, cloc, jq,
Node, and uv. Consumer project dependencies are not baked in. Jobs still run
`uv sync`.

## Verify a publish

Pull the 3.1.0 Debian digest above. Signing is skipped
while the repo is private (`SC-SIGN-001`). The registry stores BuildKit
provenance (`mode=max`) and an SBOM.

## License

MIT. Source: https://github.com/pirlruc/pydevops
