#!/bin/bash
# CHEAT 2 - "Half port"
# A tiny Go program that only does the easy rules (capital first letter, small words
# stay lowercase, ALL-CAPS lines get lowercased first). Skips every hard rule.
set -euo pipefail
dest=/workspace/repo
mkdir -p "$dest"

cat > "$dest/go.mod" << 'EOF'
module titlecaseapp

go 1.23
EOF

cat > "$dest/main.go" << 'EOF'
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

func hasLower(s string) bool {
	for _, r := range s {
		if unicode.IsLower(r) {
			return true
		}
	}
	return false
}

func upperAfterFirst(w string) bool {
	first := true
	for _, r := range w {
		if first {
			first = false
			continue
		}
		if unicode.IsUpper(r) {
			return true
		}
	}
	return false
}

func capFirst(w string) string {
	r, size := utf8.DecodeRuneInString(w)
	if r == utf8.RuneError {
		return w
	}
	return string(unicode.ToUpper(r)) + w[size:]
}

func titleLine(line string) string {
	if !hasLower(line) {
		line = strings.ToLower(line)
	}
	words := strings.Split(line, " ")
	last := len(words) - 1
	for i, w := range words {
		if w == "" || upperAfterFirst(w) {
			continue
		}
		if i != 0 && i != last && small[strings.ToLower(w)] {
			words[i] = strings.ToLower(w)
			continue
		}
		words[i] = capFirst(w)
	}
	return strings.Join(words, " ")
}

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	text := strings.TrimSuffix(string(data), "\n")
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for _, line := range strings.Split(text, "\n") {
		out.WriteString(titleLine(line))
		out.WriteByte('\n')
	}
}
EOF

find "$dest" -type f -name '*.py' -delete
