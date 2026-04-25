# Versioning this DevOps repository

## Tags for consumers

Application workflows should pin the reusable workflow with a **SemVer tag** (or an immutable SHA)
rather than a moving branch:

```yaml
uses: pirlruc/pydevops/.github/workflows/python-quality.yml@v1.2.0
```

Set `devops_ref` in `workflow_call` inputs to the same tag when the workflow checks out this repo
into `.devops`.

## Cutting a release

1. Ensure `main` passes **DevOps scripts CI** and **Reusable workflows quality**.
2. Bump `version` in `pyproject.toml` if you publish the wheel; otherwise rely on Git tags only.
3. Create an annotated tag: `git tag -a v1.2.0 -m "Release v1.2.0"` and push `v1.2.0`.
4. Document breaking workflow input or behavior changes in the tag message or a short `CHANGELOG` if
   you maintain one.

## Rolling forward in app repos

Update the `uses: ...@vX.Y.Z` reference and `devops_ref` together. Run a test PR in a non-production
app repo before bumping production callers.

This repository currently targets **CPython ≥ 3.13** (`pyproject.toml` and the default
`python_version` input on `python-quality.yml`). Align application interpreters before adopting a
new DevOps tag.

## Provenance (optional)

For **application** release artifacts (containers, wheels), consider
[SLSA provenance](https://github.com/slsa-framework/slsa-github-generator) in the app’s publish
workflow. This DevOps repo’s `publish-pypi.yml` is a starting point for PyPI OIDC; add provenance
generation there when your org requires it.
