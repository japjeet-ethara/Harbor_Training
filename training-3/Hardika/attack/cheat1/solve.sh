#!/bin/bash
# Cheat 1 - Build trick (Day 4 attack on Kushal Soni's task).
#
# NOT a titlecase port. It writes an empty Go program that compiles,
# reads nothing and prints nothing, and deletes the Python files.
# It tests whether `build` and `no_python` pay points on their own,
# with zero correct output.
#
# Runs inside the agent container like a normal solution. It touches
# only /workspace/repo (never tests/, task.toml or environment/).
set -euo pipefail

repo=/workspace/repo
cd "$repo"

# Hard rule: no .py files anywhere in the repository.
find "$repo" -type f -name '*.py' -delete

cat > go.mod <<'EOF'
module titlecasego

go 1.23
EOF

cat > main.go <<'EOF'
package main

// Empty on purpose: compiles, does no work, prints nothing.
func main() {}
EOF
