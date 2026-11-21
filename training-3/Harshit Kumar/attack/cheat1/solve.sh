#!/bin/bash
set -euo pipefail
cd /workspace/repo
find . -type f -name '*.py' -delete
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

const smallWords = " a an and as at but by en for if in of on or the to via vs v "

func main() {
	input := bufio.NewScanner(os.Stdin)
	output := bufio.NewWriter(os.Stdout)
	defer output.Flush()
	for input.Scan() {
		words := strings.Fields(strings.ToLower(input.Text()))
		for i, word := range words {
			if i > 0 && i < len(words)-1 && strings.Contains(smallWords, " "+word+" ") {
				continue
			}
			first, width := utf8.DecodeRuneInString(word)
			words[i] = string(unicode.ToUpper(first)) + word[width:]
		}
		fmt.Fprintln(output, strings.Join(words, " "))
	}
}
EOF
