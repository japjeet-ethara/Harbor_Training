#!/bin/bash
set -euo pipefail
cd /workspace/repo
find . -type f -name '*.py' -delete
cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF
cat > main.go <<'EOF'
package main

func main() {}
EOF
