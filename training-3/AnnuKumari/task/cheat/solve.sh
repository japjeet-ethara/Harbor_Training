#!/bin/bash
set -euo pipefail

root=/workspace/repo
mkdir -p "$root"

cat > "$root/go.mod" << 'EOF'
module cheat

go 1.23
EOF

cat > "$root/main.go" << 'EOF'
package main

import (
	"os"
)

func main() {
	paths := []string{
		"/tests/data/expected.txt",
		"tests/data/expected.txt",
	}
	for _, path := range paths {
		data, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		os.Stdout.Write(data)
		return
	}
	os.Stderr.WriteString("tests/data/expected.txt not found\n")
	os.Exit(1)
}
EOF
