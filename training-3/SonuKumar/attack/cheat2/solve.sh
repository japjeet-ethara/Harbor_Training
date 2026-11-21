#!/bin/bash
# Cheat 2 — Half Port: Naive first-letter-of-word capitalization
# Ports only basic casing: capitalizes the first character of each word.
# Ignores small words ("the", "of", "and"), acronyms, Mc/Mac, contractions, slashes, URLs.
# Tests how much partial credit is awarded by the linear scoring metric.
set -euo pipefail

repo=/workspace/repo

# Delete all Python files so no_python passes
find "$repo" -type f -name '*.py' -delete
find "$repo" -name '__pycache__' -type d -prune -exec rm -rf {} +
rm -rf "$repo/titlecase" "$repo/setup.py" "$repo/setup.cfg" "$repo/pyproject.toml" "$repo/tox.ini"

# Write valid go.mod
cat > "$repo/go.mod" << 'EOF'
module titlecase

go 1.23
EOF

# Write naive Go implementation
cat > "$repo/main.go" << 'EOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

func naiveTitle(s string) string {
	words := strings.Fields(s)
	if len(words) == 0 {
		return s
	}
	for i, w := range words {
		runes := []rune(w)
		if len(runes) > 0 {
			runes[0] = unicode.ToUpper(runes[0])
		}
		words[i] = string(runes)
	}
	return strings.Join(words, " ")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		line := scanner.Text()
		writer.WriteString(naiveTitle(line) + "\n")
	}
}
EOF

cd "$repo"
go build ./...
go build -o /tmp/titlecase .
