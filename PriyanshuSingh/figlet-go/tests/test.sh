#!/bin/bash
# Verifier entry point. Runs as root (task.toml [verifier] user) in the
# agent's container, after the agent has finished.
set -uo pipefail
mkdir -p /logs/verifier

# Stop anything the agent left running, so nothing it started can read the
# grading files while they are here.
for p in /proc/[0-9]*; do
  uid=$(awk '/^Uid:/ {print $2}' "$p/status" 2>/dev/null)
  [ "$uid" = "1000" ] && kill -9 "${p#/proc/}" 2>/dev/null
done

# Only root may read the answers. The twin itself is run as "nobody".
chown -R root:root /tests
chmod -R go-rwx /tests

# Standard library only: no proxy, no module downloads, no workspace files,
# no settings from the agent's `go env -w`, and a fresh build cache.
export CGO_ENABLED=0 GOTOOLCHAIN=local GOPROXY=off GOFLAGS=-mod=mod GOWORK=off GOENV=off
export GOCACHE="$(mktemp -d)" GOMODCACHE="$(mktemp -d)" GOPATH="$(mktemp -d)"

cd /tests && go run grade.go
