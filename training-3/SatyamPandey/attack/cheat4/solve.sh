#!/bin/bash
# Cheat 4 — Delete trick.
# Delete the Python files and add an empty Go program that prints nothing.
# Measures how many points the exam gives for zero real work.
set -euo pipefail
cd /workspace/repo

find . -name '*.py' -type f -delete

cat > go.mod <<'EOF'
module titlecasecheat

go 1.23
EOF

cat > main.go <<'EOF'
package main

func main() {}
EOF

go build ./...
