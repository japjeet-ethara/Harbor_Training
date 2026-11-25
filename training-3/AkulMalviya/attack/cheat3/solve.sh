#!/bin/bash
set -euo pipefail

cd /workspace/repo
cat > go.mod <<'GO_MOD'
module titlecase-baseline

go 1.23
GO_MOD

cat > main.go <<'GO_SOURCE'
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
	input := bufio.NewReader(os.Stdin)
	output := bufio.NewWriter(os.Stdout)
	defer output.Flush()

	for {
		line, err := input.ReadString('\n')
		if len(line) > 0 {
			fmt.Fprintln(output, titlecase(strings.TrimSuffix(line, "\n")))
		}
		if err != nil {
			break
		}
	}
}

// Lowercase common interior small words and capitalize the first rune of other words.
func titlecase(line string) string {
	words := strings.Fields(line)
	for i, word := range words {
		lower := strings.ToLower(word)
		if i > 0 && i < len(words)-1 && isSmallWord(lower) {
			words[i] = lower
			continue
		}
		first, size := utf8.DecodeRuneInString(word)
		words[i] = string(unicode.ToTitle(first)) + word[size:]
	}
	return strings.Join(words, " ")
}

func isSmallWord(word string) bool {
	switch word {
	case "a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "via", "vs":
		return true
	}
	return false
}
GO_SOURCE
