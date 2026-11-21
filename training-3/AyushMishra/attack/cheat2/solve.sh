#!/bin/sh
set -eu
cd /workspace/repo

if [ ! -f go.mod ]; then
    go mod init titlecase
fi

cat > main.go <<'GO'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
)

func isSmall(word string) bool {
	switch word {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	}
	return false
}

func capitalize(word string) string {
	for i, r := range word {
		if unicode.IsLetter(r) {
			return word[:i] + string(unicode.ToUpper(r)) + word[i+len(string(r)):]
		}
	}
	return word
}

func title(line string) string {
	words := strings.Fields(line)
	var result strings.Builder
	result.Grow(len(line))
	pos := 0
	for i, word := range words {
		start := pos + strings.Index(line[pos:], word)
		result.WriteString(line[pos:start])
		pos = start + len(word)
		lower := strings.ToLower(word)
		if i > 0 && i < len(words)-1 && isSmall(lower) {
			result.WriteString(lower)
		} else {
			result.WriteString(capitalize(word))
		}
	}
	result.WriteString(line[pos:])
	return result.String()
}

func main() {
	input := bufio.NewScanner(os.Stdin)
	input.Buffer(make([]byte, 4096), 1024*1024)
	output := bufio.NewWriter(os.Stdout)
	for input.Scan() {
		fmt.Fprintln(output, title(input.Text()))
	}
	if err := output.Flush(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := input.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
GO

gofmt -w main.go
go build ./...
find . -type f -name '*.py' -delete
