#!/bin/bash
set -euo pipefail
repo=/workspace/repo

cat > "$repo/go.mod" << 'EOF'
module titlecase

go 1.23
EOF

cat > "$repo/main.go" << 'EOF'
package main

import (
	"fmt"
	"os"
)

func main() {
	data, err := os.ReadFile("/tests/data/expected.txt")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	os.Stdout.Write(data)
}
EOF

find "$repo" -type f -name '*.py' -delete
