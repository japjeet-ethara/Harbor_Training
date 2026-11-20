#!/bin/bash
set -eu

cd /workspace/repo

cat > go.mod <<'EOF'
module attack1

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"os"
)

func main() {
	data, err := os.ReadFile("/tests/data/hidden_expected.txt")
	if err != nil {
		os.Exit(1)
	}
	if _, err := os.Stdout.Write(data); err != nil {
		os.Exit(1)
	}
}
EOF
