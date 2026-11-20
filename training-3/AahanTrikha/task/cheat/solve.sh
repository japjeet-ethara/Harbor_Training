#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /workspace/repo
cp "$DIR/main.go" ./main.go
rm -f go.mod go.sum
go mod init titlecasego
go build ./...