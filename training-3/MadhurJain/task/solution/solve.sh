#!/bin/bash
set -euo pipefail

cd /workspace/repo
cp /solution/go/go.mod .
cp /solution/go/*.go .
find . -type f -name '*.py' -delete
go build -o /dev/null ./...
