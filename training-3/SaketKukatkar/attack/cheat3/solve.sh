#!/bin/sh
set -eu
cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase-go

go 1.23.4
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		fmt.Fprintln(writer, "NOT IMPLEMENTED")
	}
	fmt.Fprintln(writer, "")
}
EOF

find . -type f -name '*.py' -delete
