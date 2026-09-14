#!/bin/sh
# SC-DEP-004: gitlink SHA must equal the peeled annotated tag named in this file.
# Fail closed when either gitlink drifts from the documented bootstrap ref.
set -eu

ROOT="$(git rev-parse --show-toplevel)"
cd "${ROOT}"

# Peeled commits for annotated tags guardrails 1.6.0 and github-scaffold 1.5.0.
GR_TAG="1.6.0"
GR_EXPECT="77cf16eb52c76c9cf676594f23b4b1fd73c5fc81"
SC_TAG="1.5.0"
SC_EXPECT="9e04ed530fcbed1c0441c68ed96aed8e2dc2bec9"

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
