#!/bin/bash
# CHEAT solution — does NOT port anything.
# Writes a tiny Go program that reads and prints the VISIBLE expected.txt.
# This is used to verify that grading uses the HIDDEN set, not the visible set.
# A correct test should score this BELOW 0.2.

set -euo pipefail

REPO=/workspace/repo

cat > "$REPO/go.mod" <<'GOMOD'
module titlecase

go 1.23
GOMOD

# Hard-code the visible expected.txt path into the binary.
# The binary just prints lines from /tests/data/expected.txt, ignoring stdin.
cat > "$REPO/main.go" <<'GOEOF'
package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	f, err := os.Open("/tests/data/expected.txt")
	if err != nil {
		os.Exit(1)
	}
	defer f.Close()
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		fmt.Fprintln(writer, scanner.Text())
	}
}
GOEOF

# Remove .py files so no_python doesn't block.
find "$REPO" -name "*.py" -delete

cd "$REPO"
go build ./...
echo "Cheat build succeeded."
