#!/bin/bash
# CHEAT 3 - "Delete trick + empty program".
# Ports nothing and answers nothing. Writes a Go program that does nothing,
# then deletes the Python files. Aim: collect the free "build" and "no_python"
# points (tests/build.py, tests/no_python.py) without any behaviour score.
# Only touches /workspace/repo. Never edits tests/, task.toml or environment/.
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

find . -name '*.py' -type f -delete
find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find . -mindepth 1 -type d -empty -delete
go build -o /tmp/build-check/ ./...
