#!/bin/bash
set -euo pipefail

dest=/workspace/repo
src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/src"

cp "$src/go.mod" "$src/main.go" "$src/titlecase.go" "$dest/"
find "$dest" -type f -name '*.py' -delete
find "$dest" -type d -name '__pycache__' -exec rm -rf {} + || true
# The module path ends in "titlecase", so `go build ./...` writes ./titlecase.
rm -rf "$dest/titlecase"
