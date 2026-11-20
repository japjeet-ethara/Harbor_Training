#!/bin/bash
set -euo pipefail

dest=/workspace/repo
src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$src/go.mod" "$src/main.go" "$dest/"
cp "$dest/titlecase/__init__.py" "$dest/titlecase/__init__.txt"
find "$dest" -type f -name '*.py' -delete
find "$dest" -type d -name '__pycache__' -exec rm -rf {} + || true

cd "$dest"
go build ./...
