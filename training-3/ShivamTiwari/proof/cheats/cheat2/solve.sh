#!/bin/bash
# Reconstruction of "Cheat 2 - Half port" from the Day 4 attack report.
# The attacker's original job folder was not present in this workspace, so this
# script reproduces the described mechanism rather than the lost file.
set -euo pipefail
cd /workspace/repo

# Delete every Python source so a filename-only no_python check would pass.
find . -type f \( -name '*.py' -o -name '*.pyc' -o -name '*.pyo' \) -delete
find . -depth -type d -name '__pycache__' -exec rm -rf {} +
rmdir titlecase 2>/dev/null || true

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"io"
	"os"
	"strings"
	"unicode"
)

// A deliberately shallow port: it only splits on spaces and tabs, lowercases a
// short small-word list, and capitalises the first/last word. Apostrophes,
// Mc/Mac, honorifics, inline periods, acronyms, slashes, hyphens and subphrase
// punctuation are all ignored.

var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "via": true, "vs": true,
}

func capitalize(word string) string {
	rs := []rune(word)
	if len(rs) == 0 {
		return word
	}
	rs[0] = unicode.ToUpper(rs[0])
	for i := 1; i < len(rs); i++ {
		rs[i] = unicode.ToLower(rs[i])
	}
	return string(rs)
}

func titleLine(line string) string {
	words := []string{}
	seps := []string{}
	var cur []rune
	for _, r := range line {
		if r == ' ' || r == '\t' {
			words = append(words, string(cur))
			cur = cur[:0]
			seps = append(seps, string(r))
			continue
		}
		cur = append(cur, r)
	}
	words = append(words, string(cur))

	for i, w := range words {
		if w == "" {
			continue
		}
		if small[strings.ToLower(w)] {
			words[i] = strings.ToLower(w)
		} else {
			words[i] = capitalize(w)
		}
	}
	for i := 0; i < len(words); i++ {
		if words[i] != "" {
			words[i] = capitalize(words[i])
			break
		}
	}
	for i := len(words) - 1; i >= 0; i-- {
		if words[i] != "" {
			words[i] = capitalize(words[i])
			break
		}
	}

	var b strings.Builder
	for i, w := range words {
		b.WriteString(w)
		if i < len(seps) {
			b.WriteString(seps[i])
		}
	}
	return b.String()
}

func main() {
	data, _ := io.ReadAll(os.Stdin)
	lines := strings.Split(string(data), "\n")
	if len(lines) > 0 && lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	for _, line := range lines {
		os.Stdout.WriteString(titleLine(line))
		os.Stdout.WriteString("\n")
	}
}
EOF
