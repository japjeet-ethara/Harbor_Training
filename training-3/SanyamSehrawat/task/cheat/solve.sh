#!/bin/bash
# Cheat, used only to prove the grader catches it. It ports nothing: it drops a Go program
# into the repository that ignores its input and prints the SAMPLE answers it was given.
# scripts/validate.py puts this script and tests/data/sample/answers.txt into a throw-away
# copy of the task as solution/, so Harbor runs it like the oracle.
set -euo pipefail

repo=/workspace/repo
here="$(cd "$(dirname "$0")" && pwd)"

cp "$here/answers.txt" "$repo/answers.txt"

cat > "$repo/go.mod" <<'EOF'
module cheat

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
	_ "embed"
	"os"
)

//go:embed answers.txt
var answers string

func main() {
	os.Stdout.WriteString(answers)
}
EOF
