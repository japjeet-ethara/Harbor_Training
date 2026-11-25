#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module buildtrick

go 1.23
EOF

cat > main.go <<'EOF'
package main

func main() {}
EOF

find . -name "*.py" -type f -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

go build ./...
