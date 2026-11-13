#!/bin/bash
set -euo pipefail

cd /workspace/repo
cp /solution/go.mod /solution/main.go .
find . -type f -name '*.py' -delete
go build ./...
