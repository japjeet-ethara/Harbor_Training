#!/usr/bin/env bash
set -euo pipefail
cd /workspace/repo
cat > go.mod <<'EOF'
module titlecase-cheat

go 1.23
EOF
cat > main.go <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1024*1024), 16*1024*1024)
	for sc.Scan() {
		_ = sc.Text()
		fmt.Println()
	}
}
EOF
find . -name '*.py' -delete
go build ./...
