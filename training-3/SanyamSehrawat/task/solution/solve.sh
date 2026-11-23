#!/bin/bash
# Reference solution (the oracle). Installs the Go rewrite from solution/src and removes
# the Python implementation, leaving the licence and the docs of the original in place.
set -euo pipefail

repo=/workspace/repo
here="$(cd "$(dirname "$0")" && pwd)"

cp "$here/src/go.mod" "$here/src/main.go" "$repo/"

# The whole Python package, its build files and anything a Python run may have cached.
rm -rf "$repo/titlecase" "$repo/setup.py" "$repo/setup.cfg" "$repo/pyproject.toml" "$repo/tox.ini"
find "$repo" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "$repo" -name '*.py' -type f -delete

cd "$repo"
go build ./...
go build -o /tmp/titlecase .
printf 'the lord of the rings\n' | /tmp/titlecase
