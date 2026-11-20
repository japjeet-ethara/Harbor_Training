#!/bin/bash
set -eu

repo=/workspace/repo
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module partial-titlecase

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
)

func partialTitle(line string) string {
	words := strings.Fields(line)
	for i, word := range words {
		runes := []rune(strings.ToLower(word))
		if len(runes) > 0 {
			runes[0] = unicode.ToUpper(runes[0])
		}
		words[i] = string(runes)
	}
	return strings.Join(words, " ")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024), 1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	for scanner.Scan() {
		fmt.Fprintln(writer, partialTitle(scanner.Text()))
	}
	if err := writer.Flush(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
EOF

gofmt -w "$repo/main.go"
find "$repo" \( -type f -o -type l \) -iname '*.py' -delete
