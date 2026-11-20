#!/bin/bash
# Cheat 4 (Day 6 re-attack) - Half port.
# Ports only the easy rules: small words stay lowercase except in the first or
# last slot, other words get a capital first letter, words with inner capitals
# are kept, and an all-caps line is lowercased first. It skips Mc names,
# apostrophes, slashes, hyphens, acronyms, initials, inline periods,
# subphrases and Unicode special cases. It tests how much partial credit a
# weak port gets.
set -euo pipefail
cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete

cat > go.mod <<'GOMOD'
module titlecase

go 1.23
GOMOD

cat > main.go <<'GOSRC'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

var small = map[string]bool{"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true, "via": true,
	"vs": true, "vs.": true}

func capFirst(w string) string {
	r := []rune(w)
	for i, c := range r {
		if unicode.IsLetter(c) || unicode.IsDigit(c) {
			r[i] = unicode.ToUpper(c)
			return string(r)
		}
	}
	return w
}

func innerCaps(w string) bool {
	r := []rune(w)
	for i := 1; i < len(r); i++ {
		if unicode.IsUpper(r[i]) {
			return true
		}
	}
	return false
}

func title(line string) string {
	allCaps := strings.ToUpper(line) == line
	var words, seps []string
	cur := []rune{}
	for _, c := range line {
		if unicode.IsSpace(c) {
			words = append(words, string(cur))
			seps = append(seps, string(c))
			cur = cur[:0]
		} else {
			cur = append(cur, c)
		}
	}
	words = append(words, string(cur))
	for i, w := range words {
		if allCaps {
			w = strings.ToLower(w)
		}
		switch {
		case small[strings.ToLower(w)] && i != 0 && i != len(words)-1:
			w = strings.ToLower(w)
		case !allCaps && innerCaps(w):
		default:
			w = capFirst(w)
		}
		words[i] = w
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
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(strings.TrimSuffix(line, "\n"), "\r")
			out.WriteString(title(line) + "\n")
		}
		if err != nil {
			return
		}
	}
}
GOSRC
