#!/bin/bash
set -euo pipefail

cd /workspace/repo
cp /solution/go.mod /workspace/repo/go.mod
cp /solution/main.go /workspace/repo/main.go
find /workspace/repo -type f -name '*.py' -delete
# The module builds a binary named titlecase. The old Python package directory
# has that name, and `go build ./...` refuses to overwrite a directory.
rm -rf /workspace/repo/titlecase
