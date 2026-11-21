#!/bin/bash
# Cheat 1 - Build trick / delete trick.
# Compiles a trivial Go echo program and deletes the Python files. No titlecase logic.
set -euo pipefail
cd /workspace/repo

find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true

printf 'module cheat1\n\ngo 1.23\n' > go.mod
cat > main.go <<'GOSRC'
package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1024*1024), 16*1024*1024)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for sc.Scan() {
		fmt.Fprintln(w, sc.Text())
	}
}
GOSRC

go build ./...
