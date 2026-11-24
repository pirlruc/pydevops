# ci-python (GitHub Packages)

Same contents as the Docker Hub page. Not a product runtime — no `HEALTHCHECK`.

## Image

| Item | Value |
|------|--------|
| GHCR | `ghcr.io/pirlruc/ci-python` |
| Architectures | `linux/amd64` |
| User | non-root `1000:1000` |
| Base | Debian 13 (`ci-python`); Alpine 3.24 (`-alpine`) |

Published at 3.10.1 on GHCR and Docker Hub. Debian owns the unsuffixed tag.
`3.3.0-debian` and `latest-alpine` exist. The tag index is not the Actions
pin. `python-quality.yml` pins the Debian `linux/amd64` manifest for static,
supply-chain, and test.
dast stays on the host.

### Tags

| Tag | Digest |
|-----|--------|
| `3.10.1` / `3.10.1-debian` | Debian index `sha256:d7a1aaab602c2717ea3fb5727a65402e3c233f2669de436652bc2b4e960fff6b` |
| `3.10.1` `linux/amd64` (Actions) | `sha256:8bdd74a184074a58c75473da06fce79d890ef2ddb230011ddf70ebfb7b10778d` |
| `3.10.1-alpine` | Alpine index `sha256:39e6fd8de818c0e10fc7ceb6fa1cb54a36155f2295a889250a5635f9e0da7350` |
| `3.10.1-alpine` `linux/amd64` (Actions) | `sha256:6e5215fd529e3639b7009dd50cb267633919b36593cecc195813d6ccae3a1ad7` |
| `3.3.0` / `3.3.0-debian` (previous) | Debian index `sha256:0aef20d62a9a5bee8ba7d5650bbd3a82e4d2f7535acb386207dc9670e597269a` |
| `3.3.0` `linux/amd64` (previous) | `sha256:894d5ae1d9bd55d68262f4ed65cd6f57d7186038d7e8e8668dba443ee0ebfbbd` |
| `3.3.0-alpine` / `latest-alpine` | Alpine index `sha256:5496e75f1c811cccee3542bfcd21ee62467cea91ce5c9945de76ecc59dcca524` |
| `3.3.0-alpine` `linux/amd64` (Actions) | `sha256:cb118f77b1251dffdd0a4d1ae95dfb7ba1c4653b86aeff6e577ae622bdab3f05` |

Prefer a digest. Pin the `linux/amd64` image manifest in Actions.

## Authentication

```bash
echo "$CR_PAT" | docker login ghcr.io -u USERNAME --password-stdin
docker pull ghcr.io/pirlruc/ci-python@sha256:8bdd74a184074a58c75473da06fce79d890ef2ddb230011ddf70ebfb7b10778d
```

## Hardened local run

```bash
docker run --rm \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  -v "$PWD:/workspace:ro" -w /workspace \
  ghcr.io/pirlruc/ci-python@sha256:8bdd74a184074a58c75473da06fce79d890ef2ddb230011ddf70ebfb7b10778d \
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
      image: ghcr.io/pirlruc/ci-python@sha256:8bdd74a184074a58c75473da06fce79d890ef2ddb230011ddf70ebfb7b10778d
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
```

Digest-pin the container (CI-026). Do not float on `:latest`.

## Verify a publish

Pull the digest recorded in the release. Signing follows repository visibility
(`SC-SIGN-001` while private). Registry provenance is BuildKit `mode=max`.

## License

MIT. Source: <https://github.com/pirlruc/pydevops>
