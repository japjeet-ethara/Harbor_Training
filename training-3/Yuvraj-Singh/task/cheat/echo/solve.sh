#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimRight(line, "\r\n")
			fmt.Fprintln(out, line)
		}
		if err != nil {
			if err != io.EOF {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
			break
		}
	}
}
EOF
