# ci-python (GitHub Packages)

Same contents as the Docker Hub page. Not a product runtime — no `HEALTHCHECK`.

## Image

| Item | Value |
|------|--------|
| GHCR | `ghcr.io/pirlruc/ci-python` |
| Architectures | `linux/amd64` |
| User | non-root `1000:1000` |
| Base | Debian 13 (`ci-python`); Alpine 3.24 (`-alpine`) |

Published at 3.2.0 on GHCR and Docker Hub. Debian owns the unsuffixed tag.
`3.2.0-debian` and `latest-alpine` exist. Platform manifests match the Hub
page. `python-quality.yml` pins a digest for static, supply-chain, and test.
dast stays on the host.

## Authentication

```bash
echo "$CR_PAT" | docker login ghcr.io -u USERNAME --password-stdin
docker pull ghcr.io/pirlruc/ci-python@sha256:03cc8582f6751498ed2de1893f05123f1338bc802530dbea0b5b1bf52c3d004c
```

## Hardened local run

```bash
docker run --rm \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  -v "$PWD:/workspace:ro" -w /workspace \
  ghcr.io/pirlruc/ci-python@sha256:03cc8582f6751498ed2de1893f05123f1338bc802530dbea0b5b1bf52c3d004c \
  ruff --version
```

## Use as a GitHub Actions job container

```yaml
jobs:
  quality-static:
    runs-on: ubuntu-24.04
    permissions:
      packages: read
    container:
      image: ghcr.io/pirlruc/ci-python@sha256:03cc8582f6751498ed2de1893f05123f1338bc802530dbea0b5b1bf52c3d004c
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
```

Digest-pin the container (CI-026). Do not float on `:latest`.

## Verify a publish

Pull the digest recorded in the release. Signing follows repository visibility
(`SC-SIGN-001` while private). Registry provenance is BuildKit `mode=max`.

## License

MIT. Source: https://github.com/pirlruc/pydevops
