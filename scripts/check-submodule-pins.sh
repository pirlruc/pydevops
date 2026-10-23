#!/bin/sh
# SC-DEP-004: gitlink SHA must equal the peeled annotated tag named in this file.
# Fail closed when either gitlink drifts from the documented bootstrap ref.
set -eu

ROOT="$(git rev-parse --show-toplevel)"
cd "${ROOT}"

# Peeled commits for annotated tags guardrails 1.12.0 and github-scaffold 1.10.0.
# methodologies is not a submodule here; decision links cite methodologies 1.9.1.
GR_TAG="1.12.0"
GR_EXPECT="f4baf6198006c6b898eee9cec451b66b87129bd3"
SC_TAG="1.10.0"
SC_EXPECT="1d9901f7e7e5785abb7cac6f5d46e0e8e2023ff8"

gr="$(git rev-parse 'HEAD:docs/guardrails')"
sc="$(git rev-parse 'HEAD:.github/scaffold')"

status=0
if [ "${gr}" != "${GR_EXPECT}" ]; then
  echo "SC-DEP-004: docs/guardrails gitlink ${gr} != ${GR_TAG} ${GR_EXPECT}" >&2
  status=1
fi
if [ "${sc}" != "${SC_EXPECT}" ]; then
  echo "SC-DEP-004: .github/scaffold gitlink ${sc} != ${SC_TAG} ${SC_EXPECT}" >&2
  status=1
fi
if [ "${status}" -ne 0 ]; then
  exit 1
fi

echo "SC-DEP-004: docs/guardrails @ ${GR_TAG} (${GR_EXPECT})"
echo "SC-DEP-004: .github/scaffold @ ${SC_TAG} (${SC_EXPECT})"
