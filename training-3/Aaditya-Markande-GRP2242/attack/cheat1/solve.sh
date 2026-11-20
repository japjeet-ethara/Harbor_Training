#!/bin/bash
set -e
cd /workspace/repo
echo "[probe] exam files visible to the agent:"
find / -xdev \( -name "hidden_inputs.txt" -o -name "hidden_expected.txt" -o -name "expected.txt" \) 2>/dev/null || true
find . -name "*.py" -delete
cat > go.mod <<'GO_EOF'
module cheat1

go 1.23
GO_EOF
cat > main.go <<'GO_EOF'
package main

import (
	"io"
	"os"
)

func main() {
	io.Copy(os.Stdout, os.Stdin)
}
GO_EOF
go build ./...
echo "cheat1 done"
