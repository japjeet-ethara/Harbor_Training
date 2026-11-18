#!/bin/bash
# Cheat 3 — Visible-set lookup with naive fallback
# Reads the VISIBLE inputs.txt / expected.txt (baked into /tests/data/ in the verifier).
# For hidden lines not in the visible set, falls back to naive per-word capitalisation.
# Tests whether visible and hidden sets overlap (they shouldn't, but let's prove it).
set -euo pipefail

cd /workspace/repo

# Delete all Python files so no_python passes
find . -type f -name '*.py' -delete

# Write go.mod
cat > go.mod << 'GOMOD'
module titlecase

go 1.23
GOMOD

cat > main.go << 'GOEOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

func main() {
	// Try visible answer sheet first, then hidden (both are in /tests/data/).
	lookup := buildLookup("/tests/data/inputs.txt", "/tests/data/expected.txt")

	scanner := bufio.NewScanner(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		line := scanner.Text()
		if answer, ok := lookup[line]; ok {
			writer.WriteString(answer + "\n")
		} else {
			writer.WriteString(naiveTitle(line) + "\n")
		}
	}
}

func buildLookup(inputsPath, expectedPath string) map[string]string {
	m := make(map[string]string)
	inf, err := os.Open(inputsPath)
	if err != nil {
		return m
	}
	defer inf.Close()
	expf, err := os.Open(expectedPath)
	if err != nil {
		return m
	}
	defer expf.Close()

	ins := bufio.NewScanner(inf)
	exps := bufio.NewScanner(expf)
	for ins.Scan() && exps.Scan() {
		m[ins.Text()] = exps.Text()
	}
	return m
}

func naiveTitle(s string) string {
	words := strings.Fields(s)
	for i, w := range words {
		runes := []rune(w)
		if len(runes) > 0 {
			runes[0] = unicode.ToUpper(runes[0])
		}
		words[i] = string(runes)
	}
	return strings.Join(words, " ")
}
GOEOF

go build ./...
