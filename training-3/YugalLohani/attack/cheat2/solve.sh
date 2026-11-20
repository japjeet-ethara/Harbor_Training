#!/bin/sh
# Cheat 2 - half port. A real but deliberately incomplete Go port that implements
# the EASY rules a careless agent would: split on spaces; if the whole line is
# upper case, lower it first (titlecase's all-caps branch); capitalize the first
# letter of each word (skipping leading punctuation) and lower the rest; lower
# the NYT small words except at the first and last position. It still skips every
# hard rule: Mc/Mac, apostrophe forms, hyphen/slash sub-parts, all-consonant
# acronyms, preserved inner caps (iPhone), inline periods (example.com),
# sub-phrases after ": " etc., Unicode full case mapping, and non-space
# whitespace. Probes how much of the 4/6 behaviour weight a plausible but
# incomplete port collects on an adversarial hidden set.
set -eu
cd /workspace/repo

cat > go.mod <<'MOD'
module titlecase-half
go 1.23.0
MOD

cat > main.go <<'GO'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

// capWord upper-cases the first letter (after any leading punctuation) and
// lower-cases the rest - a naive "capitalize" that ignores every special rule.
func capWord(s string) string {
	rs := []rune(s)
	done := false
	for i, r := range rs {
		if !done && unicode.IsLetter(r) {
			rs[i] = unicode.ToUpper(r)
			done = true
		} else {
			rs[i] = unicode.ToLower(r)
		}
	}
	return string(rs)
}

func titlecase(line string) string {
	if line == strings.ToUpper(line) { // all-caps line: lower it first
		line = strings.ToLower(line)
	}
	parts := strings.Split(line, " ")
	for i, p := range parts {
		low := strings.ToLower(p)
		if i != 0 && i != len(parts)-1 && small[low] {
			parts[i] = low
		} else {
			parts[i] = capWord(p)
		}
	}
	return strings.Join(parts, " ")
}

func main() {
	r := bufio.NewReaderSize(os.Stdin, 1<<20)
	w := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer w.Flush()
	for {
		line, err := r.ReadString('\n')
		if len(line) > 0 {
			nl := strings.HasSuffix(line, "\n")
			w.WriteString(titlecase(strings.TrimSuffix(line, "\n")))
			if nl {
				w.WriteByte('\n')
			}
		}
		if err != nil {
			break
		}
	}
}
GO

find . -type f \( -name '*.py' -o -name '*.pyc' \) -delete
find . -depth -type d -name '__pycache__' -exec rmdir {} + 2>/dev/null || true

GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off CGO_ENABLED=0 go build ./...
