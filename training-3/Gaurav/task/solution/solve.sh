#!/bin/bash
set -euo pipefail
cd /workspace/repo
cp /solution/src/main.go ./main.go
cp /solution/src/go.mod ./go.mod
find . -name '*.py' -delete
rm -rf titlecase
go build ./...
