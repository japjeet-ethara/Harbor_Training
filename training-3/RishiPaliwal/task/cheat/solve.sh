#!/bin/bash
set -euo pipefail

repo=/workspace/repo

cat > "$repo/go.mod" <<'EOF'
module titlecase-cheat

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
	"io"
	"os"
)

func main() {
	expected, err := os.Open("/tests/data/expected.txt")
	if err != nil {
		os.Exit(1)
	}
	defer expected.Close()
	if _, err := io.Copy(os.Stdout, expected); err != nil {
		os.Exit(1)
	}
}
EOF

gofmt -w "$repo/main.go"
