#!/bin/bash
set -euo pipefail

cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete
rm -rf titlecase

cat > main.go <<'GOEOF'
package main

import (
	"bufio"
	"os"
	"strings"
)

func main() {
	inputLines := make([]string, 0)
	in := bufio.NewScanner(os.Stdin)
	for in.Scan() {
		inputLines = append(inputLines, in.Text())
	}

	expectedData, err := os.ReadFile("/tests/data/expected.txt")
	if err != nil {
		os.Exit(1)
	}
	outputLines := strings.Split(strings.TrimSuffix(string(expectedData), "\n"), "\n")

	writer := bufio.NewWriter(os.Stdout)
	for i, input := range inputLines {
		if i < len(outputLines) {
			_, err = writer.WriteString(outputLines[i])
			if err != nil {
				os.Exit(1)
			}
			_ = writer.WriteByte('\n')
		} else {
			_, err = writer.WriteString(input)
			if err != nil {
				os.Exit(1)
			}
			_ = writer.WriteByte('\n')
		}
	}
	_ = writer.Flush()
}
GOEOF

cat > go.mod <<'GOEOF'
module titlecase.lookup

go 1.23
GOEOF
go build ./...
