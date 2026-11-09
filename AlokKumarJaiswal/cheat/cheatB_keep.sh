#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'GO_MOD_EOF'
module cheat

go 1.23
GO_MOD_EOF

cat > main.go <<'GO_SRC_EOF'
package main

import (
	"io"
	"os"
)

func main() {
	if _, err := io.Copy(os.Stdout, os.Stdin); err != nil {
		os.Stderr.WriteString(err.Error())
		os.Exit(1)
	}
}
GO_SRC_EOF

go build ./...
echo "cheatB_keep"
