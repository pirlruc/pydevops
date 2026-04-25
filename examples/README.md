# Example caller workflows

| File                      | Purpose                                                      |
| ------------------------- | ------------------------------------------------------------ |
| `call-python-quality.yml` | Minimal `workflow_call` usage from an application repository |

Copy the YAML into **your app** repository (for example `.github/workflows/quality.yml`), replace
the SemVer tag (`v1.2.0`) with your DevOps repo coordinates, and ensure
[caller permissions](../docs/workflows.md#caller-permissions) match what the reusable workflow
needs.

The example pins **`python_version: "3.13"`** to match this DevOps repo’s current default; raise it
when you adopt a newer interpreter floor.
