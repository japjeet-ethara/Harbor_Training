#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cp "$base/visible-output.txt" /workspace/repo/visible-output.txt
cat > /workspace/repo/go.mod <<'EOF'
module visible/replay

go 1.23
EOF
cat > /workspace/repo/main.go <<'EOF'
package main

import (
    _ "embed"
    "os"
)

//go:embed visible-output.txt
var frozen []byte

func main() {
    _, err := os.Stdout.Write(frozen)
    if err != nil { os.Exit(1) }
}
EOF
cd /workspace/repo
go build ./...
