#!/bin/bash
# Oracle solution: install the pure-Go port of pyfiglet into /workspace/repo,
# keep the .flf fonts (embedded at build time via go:embed from
# pyfiglet/fonts), and delete every Python file.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/go_src"
REPO=/workspace/repo

cp "$SRC/go.mod" "$SRC/main.go" "$REPO/"

cd "$REPO"
find . -type f -name '*.py' -delete

go build ./...
go build -o /tmp/figlet .
echo "[solve] Built /tmp/figlet"
