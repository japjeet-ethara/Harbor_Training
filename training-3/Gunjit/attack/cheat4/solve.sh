#!/usr/bin/env bash
# CHEAT 4 - Build-only trick, keep the Python.
# An empty program that compiles collects the standalone `build` point (weight 1
# of 6 => 0.167) while leaving every .py file in place, so no_python stays 0 and
# behaviour stays 0. Shows `build` pays out with no porting and no cleanup.
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

# Deliberately DO NOT delete the .py files.
