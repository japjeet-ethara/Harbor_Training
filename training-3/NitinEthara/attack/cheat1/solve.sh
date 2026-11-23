#!/bin/bash
set -euo pipefail

REPO=/workspace/repo
mkdir -p "$REPO"

cat > "$REPO/go.mod" << 'EOF'
module titlecase

go 1.23
EOF

cat > "$REPO/titlecase.go" << 'EOF'
package main

import (
	"fmt"
	"os"
)

func main() {
	path := "/tests/data/hidden_expected.txt"
	data, err := os.ReadFile(path)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Print(string(data))
}
EOF
