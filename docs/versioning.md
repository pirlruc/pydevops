# Versioning this DevOps repository

## Tags for consumers

Application workflows should pin the reusable workflow with a **SemVer tag** (or an immutable SHA)
rather than a moving branch:

```yaml
uses: pirlruc/pydevops/.github/workflows/python-quality.yml@v1.2.0
```

Leave `devops_repository` / `devops_ref` empty for the normal path: `python-quality.yml` derives the
same repository and ref from `github.workflow_ref` when it checks this repo out into `.devops`. Set
those inputs only when you intentionally override the scripts checkout.

## Cutting a release

1. Ensure `main` passes **DevOps CI** (`devops-ci.yml`) and the reusable `python-quality.yml`
   self-test path you rely on.
2. Bump `version` in `pyproject.toml` if you publish the wheel; otherwise rely on Git tags only.
3. Create an annotated tag: `git tag -a v1.2.0 -m "Release v1.2.0"` and push `v1.2.0`.
4. Document breaking workflow input or behavior changes in the tag message or a short `CHANGELOG` if
   you maintain one.

## Rolling forward in app repos

Update the `uses: ...@vX.Y.Z` reference. If you set `devops_ref` explicitly, update that override at
the same time; otherwise the workflow will follow the `uses:` ref automatically. Run a test PR in a
non-production app repo before bumping production callers.

This repository currently targets **CPython ≥ 3.13** (`pyproject.toml` and the default
`python_version` input on `python-quality.yml`). Align application interpreters before adopting a
new DevOps tag.

## Provenance (optional)

For **application** release artifacts (containers, wheels), consider
[SLSA provenance](https://github.com/slsa-framework/slsa-github-generator) in the app’s publish
workflow. This DevOps repo’s `publish-pypi.yml` is a starting point for PyPI OIDC; add provenance
generation there when your org requires it.
