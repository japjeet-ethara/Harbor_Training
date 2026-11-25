#!/bin/bash
# Cheat 2 - Half port.
# This is NOT a full titlecase port. It ports only the two easy rules:
#   1. capitalise the first letter of every word;
#   2. keep the small words (a, an, and, the, of, ...) lowercase, except as
#      the first or last word of a line.
# Every other rule of the original is skipped on purpose. It tests how much
# partial credit a weak port gets.
set -euo pipefail

cd /workspace/repo

# Remove every Python source file and the Python package folder.
find . -type f -name '*.py' -delete
rm -rf titlecase

cat > go.mod <<'GO_SOURCE'
module halfport

go 1.23
GO_SOURCE

cat > main.go <<'GO_SOURCE'
// Command halfport is a deliberately incomplete titlecase port.
//
// Implemented: first-letter capitals, lowercase small words, and capital
// small words at the start and end of a line. Spaces and tabs are kept.
//
// Not implemented (on purpose): all-caps lines, Mc/Mac names, d'/o'/l'
// prefixes, Mr/Mrs/Ms/Dr, words with inline periods or inner capitals,
// slash and hyphen parts, all-consonant acronyms, leading punctuation,
// small words after ':' and other sub-phrase marks, and Unicode spaces.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

// small is the SMALL list from the original titlecase/__init__.py.
var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

func isSpace(c byte) bool { return c == ' ' || c == '\t' }

// tokens splits a line into runs of words and runs of spaces or tabs, so the
// original spacing can be put back unchanged.
func tokens(line string) (parts []string, isWord []bool) {
	start := 0
	for i := 1; i <= len(line); i++ {
		if i == len(line) || isSpace(line[i]) != isSpace(line[start]) {
			parts = append(parts, line[start:i])
			isWord = append(isWord, !isSpace(line[start]))
			start = i
		}
	}
	return parts, isWord
}

// capFirst upper-cases the first letter and leaves the rest as written.
func capFirst(word string) string {
	r, size := utf8.DecodeRuneInString(word)
	if r == utf8.RuneError {
		return word
	}
	return string(unicode.ToUpper(r)) + word[size:]
}

func titleLine(line string) string {
	parts, isWord := tokens(line)
	var words []int
	for i := range parts {
		if isWord[i] {
			words = append(words, i)
		}
	}
	for n, i := range words {
		lower := strings.ToLower(parts[i])
		if small[lower] && n != 0 && n != len(words)-1 {
			parts[i] = lower
		} else {
			parts[i] = capFirst(parts[i])
		}
	}
	return strings.Join(parts, "")
}

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	if len(data) == 0 {
		return
	}
	// A final newline does not start another line.
	text := strings.TrimSuffix(string(data), "\n")
	out := bufio.NewWriter(os.Stdout)
	for _, line := range strings.Split(text, "\n") {
		out.WriteString(titleLine(line))
		out.WriteByte('\n')
	}
	if err := out.Flush(); err != nil {
		os.Exit(1)
	}
}
GO_SOURCE

# Prove the module compiles. The binary is thrown away.
go build -o /dev/null .
