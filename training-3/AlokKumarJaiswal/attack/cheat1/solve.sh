#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Remove original .py and .pyc files as required by the task
find /workspace/repo -name "*.py" -delete
find /workspace/repo -name "*.pyc" -delete

cat > /workspace/repo/go.mod <<'GO_MOD_EOF'
module compound-titlecase

go 1.23
GO_MOD_EOF

cat > /workspace/repo/main.go <<'GO_SRC_EOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

func titlecaseLine(line string) string {
	var sb strings.Builder
	sb.Grow(len(line))
	capNext := true
	for _, r := range line {
		if unicode.IsSpace(r) {
			capNext = true
			sb.WriteRune(r)
		} else if r == '-' || r == '/' {
			capNext = true
			sb.WriteRune(r)
		} else {
			if capNext {
				sb.WriteRune(unicode.ToUpper(r))
				capNext = false
			} else {
				sb.WriteRune(r)
			}
		}
	}
	return sb.String()
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	const maxCapacity = 10 * 1024 * 1024
	buf := make([]byte, 64*1024)
	scanner.Buffer(buf, maxCapacity)

	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		line := strings.TrimRight(scanner.Text(), "\r")
		if _, err := writer.WriteString(titlecaseLine(line)); err != nil {
			os.Exit(1)
		}
		if err := writer.WriteByte('\n'); err != nil {
			os.Exit(1)
		}
	}

	if err := scanner.Err(); err != nil {
		os.Exit(1)
	}
}
GO_SRC_EOF

# Run go build ./...
go build ./...
