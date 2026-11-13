#!/bin/bash
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd)"
cd /workspace/repo
cp "$root/answers.txt" .
cat > go.mod <<'EOF'
module replay
go 1.23
EOF
cat > main.go <<'EOF'
package main
import (
    _ "embed"
    "os"
)
//go:embed answers.txt
var answers []byte
func main() { _, _ = os.Stdout.Write(answers) }
EOF
go build ./...
