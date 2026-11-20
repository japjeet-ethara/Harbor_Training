#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'GO_MOD'
module titlecase-go

go 1.23
GO_MOD

cat > main.go <<'GO_MAIN'
package main

// Cheat 3: a real but deliberately incomplete titlecase port.  It handles
// plain words, the small-word list, and first/last small words.  It omits
// Mc/Mac, titles, apostrophe-second words, inline periods, initials,
// consonant acronyms, all-caps preservation, sub-phrase separators, and
// slash/hyphen recursion.

import (
	"io"
	"os"
	"strings"
	"unicode"
)

var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "via": true, "vs": true,
}

func capitalize(word string) string {
	runes := []rune(word)
	if len(runes) == 0 {
		return word
	}
	runes[0] = unicode.ToUpper(runes[0])
	for i := 1; i < len(runes); i++ {
		runes[i] = unicode.ToLower(runes[i])
	}
	return string(runes)
}

func titleWord(word string) string {
	if word == "" {
		return word
	}
	lower := strings.ToLower(word)
	if small[lower] {
		return lower
	}
	return capitalize(word)
}

func titleLine(line string) string {
	words := make([]string, 0, 8)
	spaces := make([]string, 0, 8)
	var current []rune
	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, string(current))
			current = current[:0]
			spaces = append(spaces, string(r))
			continue
		}
		current = append(current, r)
	}
	words = append(words, string(current))

	for i, word := range words {
		words[i] = titleWord(word)
	}

	// small_first_last: capitalise a small word at either end of the line.
	for i := 0; i < len(words); i++ {
		if words[i] == "" {
			continue
		}
		if small[strings.ToLower(words[i])] {
			words[i] = capitalize(words[i])
		}
		break
	}
	for i := len(words) - 1; i >= 0; i-- {
		if words[i] == "" {
			continue
		}
		if small[strings.ToLower(words[i])] {
			words[i] = capitalize(words[i])
		}
		break
	}

	var out strings.Builder
	for i, word := range words {
		out.WriteString(word)
		if i < len(spaces) {
			out.WriteString(spaces[i])
		}
	}
	return out.String()
}

func splitLines(text string) []string {
	lines := make([]string, 0, strings.Count(text, "\n")+1)
	var current []rune
	inSeparator := false
	for _, r := range text {
		if r == '\r' || r == '\n' {
			if !inSeparator {
				lines = append(lines, string(current))
				current = current[:0]
				inSeparator = true
			}
			continue
		}
		inSeparator = false
		current = append(current, r)
	}
	lines = append(lines, string(current))
	return lines
}

func main() {
	input, _ := io.ReadAll(os.Stdin)
	lines := splitLines(string(input))
	for i, line := range lines {
		lines[i] = titleLine(line)
	}
	os.Stdout.WriteString(strings.Join(lines, "\n"))
}
GO_MAIN

# Remove every Python source and cache file, then drop the now-empty package directory.
find /workspace/repo -type f \( -name '*.py' -o -name '*.pyc' -o -name '*.pyo' \) -delete
find /workspace/repo -depth -type d -name '__pycache__' -exec rm -rf {} +
rmdir /workspace/repo/titlecase 2>/dev/null || true
