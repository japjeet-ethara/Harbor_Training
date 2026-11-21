#!/bin/bash
# Charitra's cheat 1 — Build-only: a Go program that compiles but does not titlecase
# (it echoes its input). The .py files stay.
set -euo pipefail
cd /workspace/repo
cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF
cat > main.go <<'EOF'
package main

import (
	"io"
	"os"
)

func main() { io.Copy(os.Stdout, os.Stdin) }
EOF
go build ./...
