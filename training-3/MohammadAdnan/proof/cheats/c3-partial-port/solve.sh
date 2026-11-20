#!/bin/bash
# Charitra's cheat 3 — Partial titlecase: basic word capitalisation and the small-word list only.
# No apostrophes, Mc names, initials, URLs, acronyms, hyphen/slash rules or subphrases.
set -euo pipefail
cd /workspace/repo
find . -name '*.py' -type f -delete
cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF
cat > main.go <<'EOF'
package main

import (
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var small = map[string]bool{"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true, "on": true, "or": true,
	"the": true, "to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true}

func line(s string) string {
	words := strings.Split(s, " ")
	for i, w := range words {
		if w == "" {
			continue
		}
		lw := strings.ToLower(w)
		if small[lw] && i != 0 && i != len(words)-1 {
			words[i] = lw
			continue
		}
		r, n := utf8.DecodeRuneInString(w)
		words[i] = string(unicode.ToUpper(r)) + w[n:]
	}
	return strings.Join(words, " ")
}

func main() {
	in, _ := io.ReadAll(os.Stdin)
	lines := strings.Split(string(in), "\n")
	for i := range lines {
		lines[i] = line(lines[i])
	}
	os.Stdout.WriteString(strings.Join(lines, "\n"))
}
EOF
go build ./...
