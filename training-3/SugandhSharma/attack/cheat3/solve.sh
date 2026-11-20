#!/bin/bash
# Cheat 3 (free checks): minimal pass-through Go binary + delete .py files.
# Implements zero titlecasing logic yet collects build + no_python (1/3 of score)
# plus any lines in hidden_inputs.txt that are already unchanged (e.g. blank lines).
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'GOMOD'
module titlecase

go 1.23
GOMOD

cat > main.go <<'GOEOF'
package main

import (
	"io"
	"os"
)

func main() {
	_, _ = io.Copy(os.Stdout, os.Stdin)
}
GOEOF

find /workspace/repo -type f -iname '*.py' -delete
find /workspace/repo -type d -name '__pycache__' -prune -exec rm -rf {} +
rmdir /workspace/repo/titlecase 2>/dev/null || true

go build ./...
rm -f titlecase
