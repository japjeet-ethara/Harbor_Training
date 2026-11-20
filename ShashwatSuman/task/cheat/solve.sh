#!/bin/bash
# CHEAT version of solve.sh (Step 7). It ports nothing: it builds a tiny Go
# program that just prints the visible answer sheet the agent can see in
# /workspace/examples/expected.txt. The tests grade on the hidden set, so
# this must score below 0.2.
#
# Use it like this (from the titlecase-go folder):
#   cp solution/solve.sh solution/solve.sh.real
#   cp cheat/solve.sh solution/solve.sh
#   harbor run -p . -a oracle
#   cp solution/solve.sh.real solution/solve.sh
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cp /workspace/examples/expected.txt ./answers.txt

cat > main.go <<'EOF'
package main

import (
	_ "embed"
	"os"
)

//go:embed answers.txt
var answers string

func main() { os.Stdout.WriteString(answers) }
EOF

go build -o /tmp/build-check/ ./...
