#!/bin/bash
set -euo pipefail

mkdir -p /workspace/repo

cat > /workspace/repo/go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > /workspace/repo/main.go <<'EOF'
package main

func main() {}
EOF

find /workspace/repo -type f -name '*.py' -delete
