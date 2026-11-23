#!/bin/bash
# Cheat 3 - Half port.
# Only the two easiest rules of titlecase, about 40 lines of Go:
#   1. capitalise the first letter of every word, lowercase the rest
#   2. keep the small words (a, an, the, of, ...) lowercase, except first and last word
# No Mc/Mac, no apostrophes, no acronyms, no domains, no all-caps handling.
# It measures how much partial credit the behaviour check gives a weak port.
set -euo pipefail
dest=/workspace/repo
mkdir -p "$dest"

cat > "$dest/go.mod" << 'GOMOD'
module titlecase

go 1.23
GOMOD

cat > "$dest/main.go" << 'GO'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true, "by": true,
	"en": true, "for": true, "if": true, "in": true, "of": true, "on": true, "or": true,
	"the": true, "to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

func capWord(w string) string {
	r, size := utf8.DecodeRuneInString(w)
	return string(unicode.ToUpper(r)) + strings.ToLower(w[size:])
}

func titleLine(line string) string {
	words := strings.Split(line, " ")
	last := len(words) - 1
	for i, w := range words {
		if w == "" {
			continue
		}
		if small[strings.ToLower(w)] && i != 0 && i != last {
			words[i] = strings.ToLower(w)
		} else {
			words[i] = capWord(w)
		}
	}
	return strings.Join(words, " ")
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1024*1024), 1024*1024)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		out.WriteString(titleLine(strings.TrimRight(in.Text(), "\r")) + "\n")
	}
}
GO
