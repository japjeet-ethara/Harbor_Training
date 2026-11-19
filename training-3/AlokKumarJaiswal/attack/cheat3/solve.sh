#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Remove original .py and .pyc files as required by the task
find /workspace/repo -name "*.py" -delete
find /workspace/repo -name "*.pyc" -delete

cat > /workspace/repo/go.mod <<'GO_MOD_EOF'
module combined-titlecase

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

func isUpperASCII(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

// ucInitials replaces UC_INITIALS: ^(?:[A-Z]\.|[A-Z]\.[A-Z])+$
// Checked only when the line is entirely uppercase.
func ucInitials(word string) bool {
	r := []rune(word)
	if len(r) == 0 {
		return false
	}
	var rec func(int) bool
	rec = func(i int) bool {
		if i == len(r) {
			return true
		}
		if i+1 < len(r) && isUpperASCII(r[i]) && r[i+1] == '.' {
			if rec(i + 2) {
				return true
			}
		}
		if i+2 < len(r) && isUpperASCII(r[i]) && r[i+1] == '.' && isUpperASCII(r[i+2]) {
			if rec(i + 3) {
				return true
			}
		}
		return false
	}
	return rec(0)
}

func isAllCaps(s string) bool {
	for _, r := range s {
		if unicode.ToUpper(r) != r {
			return false
		}
	}
	return true
}

func capitalizeSegments(s string) string {
	var sb strings.Builder
	sb.Grow(len(s))
	capNext := true
	for _, r := range s {
		if r == '-' || r == '/' {
			capNext = true
			sb.WriteRune(r)
		} else {
			if capNext {
				sb.WriteRune(unicode.ToUpper(r))
				capNext = false
			} else {
				sb.WriteRune(r)
			}
		}
	}
	return sb.String()
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

	allCaps := isAllCaps(line)

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
			continue
		}

		if allCaps && ucInitials(tok.text) {
			sb.WriteString(tok.text)
			wordIdx++
			continue
		}

		word := tok.text
		if allCaps {
			word = strings.ToLower(word)
		}

		isInterior := wordIdx > 0 && wordIdx < totalWords-1
		isStandalone := !strings.ContainsRune(word, '-') && !strings.ContainsRune(word, '/')

		if isStandalone && isInterior && isSmallWord(word) {
			sb.WriteString(strings.ToLower(word))
		} else {
			sb.WriteString(capitalizeSegments(word))
		}
		wordIdx++
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
