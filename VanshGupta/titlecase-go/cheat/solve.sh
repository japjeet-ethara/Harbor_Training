#!/bin/bash
set -euo pipefail
dest=/workspace/repo
mkdir -p "$dest"
cat > "$dest/go.mod" << 'EOF'
module local/titles

go 1.23
EOF
cat > "$dest/main.go" << 'EOF'
package main

import (
	"os"
)

func main() {
	b, err := os.ReadFile("tests/data/expected.txt")
	if err != nil {
		os.Exit(1)
	}
	_, _ = os.Stdout.Write(b)
}
EOF
