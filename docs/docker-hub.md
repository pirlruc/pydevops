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

Release 3.1.2 is published to Docker Hub and GitHub Packages.
`python-quality.yml` runs static, supply-chain, and test jobs in the
GHCR image. dast stays on the host.

### Tags

| Tag | Meaning |
|-----|---------|
| `3.1.2` / `3.1.2-debian` / `latest` / `latest-debian` | Debian `sha256:0406ae7d5d15466c4d1c6a48ae28b749ee101674d3e2d2c69f3888675c427a1b` |
| `3.1.2-alpine` / `latest-alpine` | Alpine `sha256:df3d72b78a63da5992ff95689c1fda03f2857224f4d383da689476e7b1c87219` |
| `3.1.0` | Previous GHCR Debian analysis. Digest `sha256:00b55d327ee2a8c78d4d428281819d64db4fad8a965e2cdb1c1b45c091831101` |
| `3.1.0-alpine` | Previous GHCR Alpine analysis. Digest `sha256:05571768e616c05a32d66919cf748da6108b79a879136f68acf29198a81fd32b` |

Debian owns the unsuffixed tag. Prefer a digest. `latest` is never the only tag.

## Hardened local run

```bash
docker run --rm \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  -v "$PWD:/workspace:ro" -w /workspace \
  pirlruc/ci-python@sha256:0406ae7d5d15466c4d1c6a48ae28b749ee101674d3e2d2c69f3888675c427a1b \
  ruff --version
```

## What is inside

ruff, pylint, mypy, pytest, bandit, pip-audit, syft, grype, jscpd, cloc, jq,
Node, and uv. Consumer project dependencies are not baked in. Jobs still run
`uv sync`.

## Verify a publish

Pull the 3.1.2 Debian digest above. Signing is skipped
while the repo is private (`SC-SIGN-001`). The registry stores BuildKit
provenance (`mode=max`) and an SBOM.

## License

MIT. Source: https://github.com/pirlruc/pydevops
