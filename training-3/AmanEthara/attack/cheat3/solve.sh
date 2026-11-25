#!/bin/bash
set -euo pipefail

REPO=/workspace/repo

# Remove all Python files and package directory
find "$REPO" -type f -name '*.py' -delete
rm -rf "$REPO/titlecase"

# Create go.mod
cat << 'EOF' > "$REPO/go.mod"
module isha/titlecase

go 1.23
EOF

# Create naive titlecase main.go
cat << 'EOF' > "$REPO/main.go"
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
)

func naiveTitle(s string) string {
	words := strings.Split(s, " ")
	for i, w := range words {
		if len(w) == 0 {
			continue
		}
		runes := []rune(w)
		runes[0] = unicode.ToUpper(runes[0])
		for j := 1; j < len(runes); j++ {
			runes[j] = unicode.ToLower(runes[j])
		}
		words[i] = string(runes)
	}
	return strings.Join(words, " ")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		fmt.Println(naiveTitle(scanner.Text()))
	}
}
EOF
