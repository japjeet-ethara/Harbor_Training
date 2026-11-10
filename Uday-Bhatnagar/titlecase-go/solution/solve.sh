#!/bin/bash
# Reference solution: replace the Python project with a Go implementation.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=/workspace/repo

cp "$SCRIPT_DIR/main.go" "$REPO/main.go"
cp "$SCRIPT_DIR/go.mod" "$REPO/go.mod"

# The task requires that no Python source survives anywhere in the repository.
find "$REPO" -type f -name '*.py' -delete
find "$REPO" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
find "$REPO" -type f -name '*.pyc' -delete

# Remove the now-empty Python package directory: its name would collide with
# the executable that `go build ./...` writes for the root main package.
rm -rf "$REPO/titlecase"
rm -rf "$REPO"/*.egg-info

cd "$REPO"
go build ./...
