#!/bin/bash
set -euo pipefail
src="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/src"
cd /workspace/repo
cp -- "$src/go.mod" "$src/"*.go .
find . -name '*.py' \( -type f -o -type l \) -delete
go build ./...
rm -f -- port
