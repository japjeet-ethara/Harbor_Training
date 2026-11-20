#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /workspace/repo
cp "$DIR/main.go" ./main.go
find . -name '*.py' -delete
find . -name '*.pyc' -delete
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
find . -mindepth 1 -type d -empty -delete
rm -f go.mod go.sum
go mod init titlecasego
go build ./...