#!/bin/bash
set -euo pipefail
cd /workspace/repo
cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF
cat > main.go <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		words := strings.Fields(scanner.Text())
		for index, word := range words {
			if index > 0 && index < len(words)-1 {
				switch strings.ToLower(word) {
				case "a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "via":
					words[index] = strings.ToLower(word)
					continue
				}
			}
			first, size := utf8.DecodeRuneInString(word)
			words[index] = string(unicode.ToUpper(first)) + word[size:]
		}
		fmt.Fprintln(writer, strings.Join(words, " "))
	}
}
EOF
find . -type f -name '*.py' -delete
