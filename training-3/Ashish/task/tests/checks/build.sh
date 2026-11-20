#!/bin/bash
# Check 2 (gate): `go build ./...` must succeed in the submission.
#
# Build caches live in a throwaway HOME so the submission tree is never
# modified by grading, and the network is already unavailable in the verifier
# container.
set -u
REPO=${REPO:-/workspace/repo}

HOME_TMP=$(mktemp -d /tmp/go-home-XXXXXX) || exit 1
trap 'rm -rf "$HOME_TMP"' EXIT

if ! (cd "$REPO" && env HOME="$HOME_TMP" \
        GOCACHE="$HOME_TMP/cache" GOMODCACHE="$HOME_TMP/mod" \
        GOPATH="$HOME_TMP/path" GOTOOLCHAIN=local GOFLAGS= \
        go build -buildvcs=false ./...); then
  echo "build: go build ./... failed" >&2
  exit 1
fi

exit 0