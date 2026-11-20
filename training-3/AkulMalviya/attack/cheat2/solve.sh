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

// Capitalize the first rune of each word and lowercase the remaining runes.
func titlecase(line string) string {
	startOfWord := true
	return strings.Map(func(r rune) rune {
		if unicode.IsSpace(r) {
			startOfWord = true
			return r
		}
		if startOfWord {
			startOfWord = false
			return unicode.ToTitle(r)
		}
		return unicode.ToLower(r)
	}, line)
}
GO_SOURCE
