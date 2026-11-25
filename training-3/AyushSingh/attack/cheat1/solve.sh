#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Remove all Python files
find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/python-titlecase

# Create a minimal go.mod
cat << 'EOF' > /workspace/repo/go.mod
module titlecase-go

go 1.23
EOF

# Create an empty main.go that does nothing
cat << 'EOF' > /workspace/repo/main.go
package main

func main() {
}
EOF

go build ./...
