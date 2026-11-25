#!/bin/bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/workspace/repo

cp "$HERE/port/go.mod" "$HERE/port/main.go" "$REPO/"
rm -rf "$REPO/titlecase"
find "$REPO" -type f -name '*.py' -delete

cd "$REPO"
go vet ./...
go build ./...
