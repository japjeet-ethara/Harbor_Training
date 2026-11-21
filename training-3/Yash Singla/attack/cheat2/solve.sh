#!/bin/bash
set -euo pipefail
cd /workspace/repo

find . -type f -name '*.py' -delete

cat > go.mod << 'EOF'
module example.com/cheat2

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"io"
	"os"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()

	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			if _, writeErr := out.Write([]byte{'\n'}); writeErr != nil {
				os.Exit(1)
			}
		}
		if err != nil {
			if err == io.EOF {
				return
			}
			os.Exit(1)
		}
	}
}
EOF
