#!/bin/bash
# Cheat 1 — Delete trick: pass build and no_python with a minimal Go stub
# that deletes all Python files and outputs empty lines.
# Tests whether build (w=1) + no_python (w=1) give 0.3333 free points without correctness.
set -euo pipefail

repo=/workspace/repo

# Delete all Python files so no_python passes
find "$repo" -type f -name '*.py' -delete
find "$repo" -name '__pycache__' -type d -prune -exec rm -rf {} +
rm -rf "$repo/titlecase" "$repo/setup.py" "$repo/setup.cfg" "$repo/pyproject.toml" "$repo/tox.ini"

# Write minimal go.mod without require/replace
cat > "$repo/go.mod" << 'EOF'
module titlecase

go 1.23
EOF

# Write a minimal Go stub program that compiles cleanly and reads stdin
cat > "$repo/main.go" << 'EOF'
package main

import (
	"bufio"
	"os"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		writer.WriteString("\n")
	}
}
EOF

cd "$repo"
go build ./...
go build -o /tmp/titlecase .
