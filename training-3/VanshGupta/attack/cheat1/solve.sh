#!/bin/bash
set -euo pipefail
cp /solution/main.go /workspace/repo/main.go
cp /solution/go.mod /workspace/repo/go.mod
find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rmdir /workspace/repo/titlecase 2>/dev/null || true
cd /workspace/repo
GOTOOLCHAIN=local go build ./...
