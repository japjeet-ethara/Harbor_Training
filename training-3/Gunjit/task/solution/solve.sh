#!/bin/bash
# Reference solution: install the Go port (standard library only) at the
# repository root, then remove the Python code.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/workspace/repo

cp "$HERE/port/go.mod" "$HERE/port/main.go" "$REPO/"

# The package folder goes completely: `go build ./...` in a module called
# titlecase writes a binary called titlecase, which cannot replace a folder.
rm -rf "$REPO/titlecase"
find "$REPO" -type f -name '*.py' -delete

# Prove it passes the same build the verifier runs, leaving no binary behind.
cd "$REPO"
go vet ./...
go build ./...
rm -f titlecase
