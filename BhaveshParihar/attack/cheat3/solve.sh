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
	"os"
)

func main() {
	in := bufio.NewScanner(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		_, _ = out.WriteString("not implemented\n")
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
go build ./...
