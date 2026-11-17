#!/bin/bash
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd)"
cd /workspace/repo
cp "$root"/src/*.go "$root"/src/go.mod .
find . -type f -name '*.py' -delete
find . -type d -name '__pycache__' -prune -exec rm -rf {} +
go build ./...
