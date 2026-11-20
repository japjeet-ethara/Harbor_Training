#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Remove original .py and .pyc files as required by the task
find /workspace/repo -name "*.py" -delete
find /workspace/repo -name "*.pyc" -delete

cat > /workspace/repo/go.mod <<'GO_MOD_EOF'
module small-words-titlecase

go 1.23
GO_MOD_EOF

cat > /workspace/repo/main.go <<'GO_SRC_EOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

var smallWords = map[string]bool{
	"a":   true,
	"an":  true,
	"and": true,
	"as":  true,
	"at":  true,
	"but": true,
	"by":  true,
	"en":  true,
	"for": true,
	"if":  true,
	"in":  true,
	"of":  true,
	"on":  true,
	"or":  true,
	"the": true,
	"to":  true,
	"v":   true,
	"v.":  true,
	"via": true,
	"vs":  true,
	"vs.": true,
}

func isSmallWord(word string) bool {
	return smallWords[strings.ToLower(word)]
}

func capitalizeFirst(s string) string {
	if s == "" {
		return ""
	}
	runes := []rune(s)
	runes[0] = unicode.ToUpper(runes[0])
	return string(runes)
}

type token struct {
	text    string
	isSpace bool
}

func tokenize(line string) []token {
	var tokens []token
	runes := []rune(line)
	n := len(runes)
	if n == 0 {
		return tokens
	}

	start := 0
	inSpace := unicode.IsSpace(runes[0])
	for i := 1; i < n; i++ {
		isSp := unicode.IsSpace(runes[i])
		if isSp != inSpace {
			tokens = append(tokens, token{
				text:    string(runes[start:i]),
				isSpace: inSpace,
			})
			start = i
			inSpace = isSp
		}
	}
	tokens = append(tokens, token{
		text:    string(runes[start:]),
		isSpace: inSpace,
	})
	return tokens
}

func titlecaseLine(line string) string {
	tokens := tokenize(line)
	if len(tokens) == 0 {
		return ""
	}

	totalWords := 0
	for _, tok := range tokens {
		if !tok.isSpace {
			totalWords++
		}
	}

	var sb strings.Builder
	sb.Grow(len(line))

	wordIdx := 0
	for _, tok := range tokens {
		if tok.isSpace {
			sb.WriteString(tok.text)
		} else {
			isInterior := wordIdx > 0 && wordIdx < totalWords-1
			if isInterior && isSmallWord(tok.text) {
				sb.WriteString(strings.ToLower(tok.text))
			} else {
				sb.WriteString(capitalizeFirst(tok.text))
			}
			wordIdx++
		}
	}

	return sb.String()
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	const maxCapacity = 10 * 1024 * 1024
	buf := make([]byte, 64*1024)
	scanner.Buffer(buf, maxCapacity)

	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		line := strings.TrimRight(scanner.Text(), "\r")
		if _, err := writer.WriteString(titlecaseLine(line)); err != nil {
			os.Exit(1)
		}
		if err := writer.WriteByte('\n'); err != nil {
			os.Exit(1)
		}
	}

	if err := scanner.Err(); err != nil {
		os.Exit(1)
	}
}
GO_SRC_EOF

# Run go build ./...
go build ./...
