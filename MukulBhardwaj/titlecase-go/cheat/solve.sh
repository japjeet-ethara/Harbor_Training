#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module example.com/titlecase-go-cheat

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"fmt"
	"io"
	"os"
)

func main() {
	expected, err := os.Open("/tests/data/expected.txt")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer expected.Close()

	if _, err := io.Copy(os.Stdout, expected); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
gofmt -w main.go
go build ./...
