#!/bin/sh
# SC-DEP-004: gitlink SHA must equal the peeled annotated tag named in this file.
# Fail closed when either gitlink drifts from the documented bootstrap ref.
set -eu

ROOT="$(git rev-parse --show-toplevel)"
cd "${ROOT}"

# Peeled commits for annotated tags guardrails 1.9.0 and github-scaffold 1.8.0.
# methodologies is not a submodule here; decision links cite methodologies 1.8.0.
GR_TAG="1.9.0"
GR_EXPECT="16a2c95c0308aaf815acb173f76792638ee75300"
SC_TAG="1.8.0"
SC_EXPECT="ac9059fddbf489057e86555f60922e2d24a1fdee"

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
