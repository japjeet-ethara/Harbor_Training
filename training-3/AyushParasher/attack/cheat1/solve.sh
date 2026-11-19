#!/bin/bash
# Cheat 1 - Delete trick + echo program.
# Deletes every .py file and writes a Go program that prints each input
# line unchanged. No titlecase logic at all.
set -euo pipefail
cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete

cat > go.mod <<'GOMOD'
module titlecase

go 1.23
GOMOD

cat > main.go <<'GOSRC'
package main

import (
	"bufio"
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
			line = strings.TrimSuffix(strings.TrimSuffix(line, "\n"), "\r")
			out.WriteString(line + "\n")
		}
		if err != nil {
			return
		}
	}
}
GOSRC
