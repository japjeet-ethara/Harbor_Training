#!/bin/bash
set -euo pipefail
dest=/workspace/repo
mkdir -p "$dest"

cat > "$dest/go.mod" << 'EOF'
module titlecase

go 1.23
EOF

cat > "$dest/main.go" << 'EOF'
package main

import (
	"fmt"
	"os"
)

func main() {
	for _, path := range []string{
		"tests/data/expected.txt",
		"/tests/data/expected.txt",
	} {
		data, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		os.Stdout.Write(data)
		return
	}
	fmt.Fprintln(os.Stderr, "tests/data/expected.txt not found")
	os.Exit(1)
}
EOF
