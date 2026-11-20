#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Create Go module
cat > go.mod <<'EOF'
module harbor.local/build-only-control

go 1.23
EOF

# Create build-only Go program that consumes stdin and emits zero bytes
cat > main.go <<'EOF'
package main

import (
	"io"
	"os"
)

func main() {
	if _, err := io.Copy(io.Discard, os.Stdin); err != nil {
		os.Exit(1)
	}
}
EOF

# Remove existing .py files only within /workspace/repo
find /workspace/repo -type f -name '*.py' -delete

# Ensure the Go workspace builds successfully
go build ./...
