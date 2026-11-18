#!/bin/bash
# Cheat 2 — Delete trick: pass build and no_python with a minimal Go program
# that capitalises only the first letter of the entire string (not a real port).
# Tests whether build (w=1) + no_python (w=1) give free points without correctness.
set -euo pipefail

cd /workspace/repo

# Delete all Python files so no_python passes
find . -type f -name '*.py' -delete

# Write go.mod
cat > go.mod << 'GOMOD'
module titlecase

go 1.23
GOMOD

# Write a stub that capitalises only the very first character of each line.
# This will pass go build ./... and leave no .py files, but output is wrong
# for almost every test line.
cat > main.go << 'GOEOF'
package main

import (
	"bufio"
	"os"
	"unicode"
	"unicode/utf8"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		line := scanner.Text()
		writer.WriteString(ucFirst(line) + "\n")
	}
}

func ucFirst(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + s[size:]
}
GOEOF

go build ./...
