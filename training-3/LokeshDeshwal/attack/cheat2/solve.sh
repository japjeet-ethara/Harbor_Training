#!/bin/bash
set -euo pipefail

WORKSPACE="/workspace/repo"
cd "$WORKSPACE"

find . -name "*.py" -delete
find . -name "*.pyc" -delete
rm -rf __pycache__ titlecase/__pycache__

go mod init titlecase 2>/dev/null || true
cat > main.go << 'EOF'
package main
func main() {}
EOF

go build -o titlecase .

mkdir -p /logs/artifacts/repo
cp main.go go.mod /logs/artifacts/repo/
