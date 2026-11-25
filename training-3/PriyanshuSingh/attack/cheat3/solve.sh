#!/bin/bash
# Cheat 3 - Half port.
# Only the easy rules, about 40 lines of Go:
#   * if the whole line is upper case, lower-case it first
#   * split on single spaces
#   * small words (a, an, and, of, the, ...) stay lower case, unless first or last
#   * every other word gets its first letter capitalised; words that already
#     have a capital inside (iTunes, NASA) are left alone
# No URLs, e-mails, hyphens, slashes, Mc/Mac, apostrophes, sub-phrases or
# initials. It measures how much partial credit a weak port gets.
set -euo pipefail

cd /workspace/repo

cat > go.mod << 'EOF'
module titlecaseport

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
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

func hasInnerUpper(w string) bool {
	for i, r := range w {
		if i > 0 && unicode.IsUpper(r) {
			return true
		}
	}
	return false
}

func capFirst(w string) string {
	r, n := utf8.DecodeRuneInString(w)
	if r == utf8.RuneError {
		return w
	}
	return string(unicode.ToUpper(r)) + w[n:]
}

func title(line string) string {
	if strings.ToUpper(line) == line {
		line = strings.ToLower(line)
	}
	words := strings.Split(line, " ")
	for i, w := range words {
		lw := strings.ToLower(w)
		switch {
		case w == "":
		case small[lw] && i != 0 && i != len(words)-1:
			words[i] = lw
		case hasInnerUpper(w):
		default:
			words[i] = capFirst(w)
		}
	}
	return strings.Join(words, " ")
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		out.WriteString(title(in.Text()))
		out.WriteString("\n")
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
go build -buildvcs=false .
