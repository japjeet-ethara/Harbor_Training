#!/bin/bash
set -euo pipefail
cd /workspace/repo
cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF
cat > main.go <<'EOF'
package main

func main() {}
EOF
