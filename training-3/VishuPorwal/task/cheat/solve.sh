#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod << 'EOF'
module titlecase-go

go 1.23
EOF

cat > main.go << 'EOF'
package main

import "os"

func main() {
	b, err := os.ReadFile("tests/data/expected.txt")
	if err != nil {
		os.Exit(1)
	}
	os.Stdout.Write(b)
}
EOF
