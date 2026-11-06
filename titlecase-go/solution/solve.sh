#!/bin/bash
set -euo pipefail

cd /workspace/repo
find . -type f -name '*.py' -delete
rm -rf titlecase
cp /solution/main.go /solution/go.mod /workspace/repo/
