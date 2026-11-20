#!/usr/bin/env bash
# CHEAT 5 - Identity echo (partial-credit floor).
# Prints every input line unchanged - no title-casing at all - and deletes the
# Python. Measures how much free "behaviour" credit a do-nothing port earns just
# because many short/already-cased titles map to themselves. Together with the
# build+no_python points it shows the reward an empty, non-porting answer floors at.
set -euo pipefail
repo="${REPO_ROOT:-/workspace/repo}"
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module solution

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
	"io"
	"os"
)

func main() { io.Copy(os.Stdout, os.Stdin) }
EOF

find "$repo" -name '*.py' -type f -delete
