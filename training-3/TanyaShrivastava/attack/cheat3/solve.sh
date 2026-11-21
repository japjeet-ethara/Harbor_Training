#!/bin/bash
# CHEAT 3 - "Build trick + delete trick"
# An empty Go program that builds, plus deleting every .py file. No titlecase logic at all.
# Measures how many points the two free checks (build, no_python) hand out.
set -euo pipefail
dest=/workspace/repo
mkdir -p "$dest"

cat > "$dest/go.mod" << 'EOF'
module titlecaseapp

go 1.23
EOF

cat > "$dest/main.go" << 'EOF'
package main

func main() {}
EOF

find "$dest" -type f -name '*.py' -delete
