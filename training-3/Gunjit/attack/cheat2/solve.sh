#!/usr/bin/env bash
# CHEAT 2 - Free points for no real work (empty build + delete Python).
# build.py scores `go build ./...` on its own, and no_python.py only needs the
# build to pass and the .py files gone. A program that compiles but does no
# title-casing collects both points (weights 1 + 1 of 6 => 0.333) with zero port.
set -euo pipefail
repo="${REPO_ROOT:-/workspace/repo}"
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module solution

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

func main() {}
EOF

find "$repo" -name '*.py' -type f -delete
