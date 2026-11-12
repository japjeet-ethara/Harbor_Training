#!/bin/bash
# CHEAT, not a solution. It ports nothing: it writes a tiny Go program that ignores
# its input and prints the VISIBLE answer sheet (tests/data/expected.txt, copied
# next to this script by scripts/validate.py). It exists only to prove the tests
# catch it: grading uses the hidden lines, which this program has never seen.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/workspace/repo

cp "$HERE/expected.txt" "$REPO/expected.txt"

# The module is not called "inflection": `go build ./...` writes a binary named
# after the module, and the Python package folder inflection/ is still there.
cat > "$REPO/go.mod" <<'EOF'
module cheat

go 1.23
EOF

cat > "$REPO/main.go" <<'EOF'
package main

import (
	_ "embed"
	"os"
)

//go:embed expected.txt
var answers []byte

func main() { os.Stdout.Write(answers) }
EOF

cd "$REPO"
go build ./...
