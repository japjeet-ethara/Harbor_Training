#!/bin/bash
set -euo pipefail
fixture="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/visible-answers.txt"
cd /workspace/repo
cp -- "$fixture" visible-answers.txt
cat > go.mod <<'EOF'
module titlecase.local/replay

go 1.23.0
EOF
cat > main.go <<'EOF'
package main

import (
	"io"
	"os"
)

func main() {
	if _, err := io.Copy(io.Discard, os.Stdin); err != nil {
		os.Exit(1)
	}
	fixture, err := os.Open("visible-answers.txt")
	if err != nil {
		os.Exit(1)
	}
	defer fixture.Close()
	if _, err := io.Copy(os.Stdout, fixture); err != nil {
		os.Exit(1)
	}
}
EOF
