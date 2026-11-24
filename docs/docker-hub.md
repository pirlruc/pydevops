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

Release 3.10.1 is published to Docker Hub and GitHub Packages.
`python-quality.yml` runs static, supply-chain, and test jobs in the
GHCR image. dast stays on the host.

### Tags

| Tag | Meaning |
|-----|---------|
| `3.10.1` / `3.10.1-debian` | Debian index `sha256:d7a1aaab602c2717ea3fb5727a65402e3c233f2669de436652bc2b4e960fff6b` |
| `3.10.1` `linux/amd64` (Actions) | `sha256:8bdd74a184074a58c75473da06fce79d890ef2ddb230011ddf70ebfb7b10778d` |
| `3.10.1-alpine` | Alpine index `sha256:39e6fd8de818c0e10fc7ceb6fa1cb54a36155f2295a889250a5635f9e0da7350` |
| `3.10.1-alpine` `linux/amd64` (Actions) | `sha256:6e5215fd529e3639b7009dd50cb267633919b36593cecc195813d6ccae3a1ad7` |
| `3.3.0` / `3.3.0-debian` (previous) | Debian index `sha256:0aef20d62a9a5bee8ba7d5650bbd3a82e4d2f7535acb386207dc9670e597269a` |
| `3.3.0` `linux/amd64` (Actions) | `sha256:894d5ae1d9bd55d68262f4ed65cd6f57d7186038d7e8e8668dba443ee0ebfbbd` |
| `3.3.0-alpine` / `latest-alpine` | Alpine index `sha256:5496e75f1c811cccee3542bfcd21ee62467cea91ce5c9945de76ecc59dcca524` |
| `3.3.0-alpine` `linux/amd64` (Actions) | `sha256:cb118f77b1251dffdd0a4d1ae95dfb7ba1c4653b86aeff6e577ae622bdab3f05` |
| `3.2.0` / `3.2.0-debian` | Previous Debian linux/amd64 `sha256:03cc8582f6751498ed2de1893f05123f1338bc802530dbea0b5b1bf52c3d004c` |
| `3.2.0-alpine` | Previous Alpine linux/amd64 `sha256:a0d5e489f3f866d9597652187a357dbad575bc2f244597d357260af58e016a83` |
| `3.1.2` | Previous Debian `sha256:0406ae7d5d15466c4d1c6a48ae28b749ee101674d3e2d2c69f3888675c427a1b` |
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
  pirlruc/ci-python@sha256:8bdd74a184074a58c75473da06fce79d890ef2ddb230011ddf70ebfb7b10778d \
  ruff --version
```

## What is inside

ruff, pylint, mypy, pytest, bandit, pip-audit, syft, grype, jscpd, cloc, jq,
Node, and uv. Consumer project dependencies are not baked in. Jobs still run
`uv sync`.

## Verify a publish

Pull the 3.3.0 Debian linux/amd64 digest above. Signing is skipped
while the repo is private (`SC-SIGN-001`). The registry stores BuildKit
provenance (`mode=max`) and an SBOM.

## License

MIT. Source: <https://github.com/pirlruc/pydevops>
