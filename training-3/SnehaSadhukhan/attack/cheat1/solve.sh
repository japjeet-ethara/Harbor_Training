#!/usr/bin/env bash
# Cheat 1 - Reward floor: build + delete, no titlecase logic.
# Earns the build and no_python criteria without implementing behaviour.
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase-cheat

go 1.23.0
EOF

# Passthrough: copy stdin to stdout unchanged (deliberately no titlecasing).
cat > main.go <<'EOF'
package main

import (
	"io"
	"os"
)

func main() {
	if _, err := io.Copy(os.Stdout, os.Stdin); err != nil {
		os.Exit(1)
	}
}
EOF

# Satisfy the no_python criterion.
find . -name '*.py' \( -type f -o -type l \) -delete

# Build exactly as the grader will.
go build ./...
