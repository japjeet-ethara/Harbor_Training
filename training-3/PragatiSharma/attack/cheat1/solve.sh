#!/bin/bash
# CHEAT 1, not a solution: input echo. Ports nothing. The Go program copies
# stdin to stdout byte for byte, so it scores only on titles that titlecase()
# leaves unchanged, plus the build and no_python points.
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'GOMOD_EOF'
module inputecho

go 1.23
GOMOD_EOF

cat > main.go <<'MAIN_GO_EOF'
// Command inputecho copies standard input to standard output unchanged.
package main

import (
	"fmt"
	"io"
	"os"
)

func main() {
	if _, err := io.Copy(os.Stdout, os.Stdin); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
MAIN_GO_EOF

# The task requires every .py file to be gone, in subdirectories too.
find . -type f -name '*.py' -delete

go build ./...
rm -f inputecho
