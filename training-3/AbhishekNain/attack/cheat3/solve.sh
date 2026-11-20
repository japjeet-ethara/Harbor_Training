#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Create Go module
cat > go.mod <<'EOF'
module harbor.local/simple-caps-control

go 1.23
EOF

# Create simple capitalization Go program
cat > main.go <<'EOF'
package main

import (
	"bufio"
	"io"
	"os"
)

func main() {
	r := bufio.NewReader(os.Stdin)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()

	letterCapped := false

	for {
		b, err := r.ReadByte()
		if err != nil {
			if err == io.EOF {
				break
			}
			os.Exit(1)
		}

		if b == ' ' || b == '\t' || b == '\n' || b == '\r' {
			letterCapped = false
		} else if !letterCapped {
			if b >= 'a' && b <= 'z' {
				b = b - 'a' + 'A'
				letterCapped = true
			} else if b >= 'A' && b <= 'Z' {
				letterCapped = true
			}
		}

		if err := w.WriteByte(b); err != nil {
			os.Exit(1)
		}
	}

	if err := w.Flush(); err != nil {
		os.Exit(1)
	}
}
EOF

# Remove existing .py files only within /workspace/repo
find /workspace/repo -type f -name '*.py' -delete

# Ensure the Go workspace builds successfully
go build ./...
