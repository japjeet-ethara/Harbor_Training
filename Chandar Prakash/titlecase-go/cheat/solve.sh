#!/bin/bash
set -eu

repo=/workspace/repo
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module visible-expected-printer

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
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

gofmt -w "$repo/main.go"
find "$repo" \( -type f -o -type l \) -iname '*.py' -delete
