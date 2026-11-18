#!/bin/bash
# Verifier entry point. Harbor copies tests/ to /tests only after the agent has
# finished (shared verifier), then runs this script inside the room.
# The room has no Python, so the grader is a small Go program.
set -uo pipefail

mkdir -p /logs/verifier
# A writable build cache even if $HOME is not writable for this user.
export GOCACHE="${GOCACHE:-/tmp/go-cache-verifier}"
export GOFLAGS=-mod=mod

cd /tests && go run grade.go
