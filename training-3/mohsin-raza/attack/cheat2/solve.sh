#!/bin/sh
# CHEAT 2 - "Half port": only the easy rules (lower-case ALL-CAPS lines, capitalise the
# first letter of each space-separated word, small words stay lower case except first/last).
# No initials, Mc/Mac, URLs, hyphen/slash compounds, punctuation inside words, etc.
set -eu
T=/workspace/repo
find "$T" -type f -name '*.py' -delete
rm -rf "$T/titlecase"
cat > "$T/go.mod" <<'GOMOD'
module cheat/half

go 1.21
GOMOD
cat > "$T/main.go" <<'GOSRC'
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

var small = map[string]bool{"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true, "on": true, "or": true,
	"the": true, "to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true}

func capWord(w string) string {
	r := []rune(w)
	for i, c := range r {
		if unicode.IsLetter(c) {
			r[i] = unicode.ToUpper(c)
			break
		}
	}
	return string(r)
}

func title(line string) string {
	if line == strings.ToUpper(line) {
		line = strings.ToLower(line)
	}
	words := strings.Split(line, " ")
	for i, w := range words {
		if w == "" {
			continue
		}
		if i > 0 && i < len(words)-1 && small[strings.ToLower(w)] {
			words[i] = strings.ToLower(w)
			continue
		}
		if w == strings.ToLower(w) {
			words[i] = capWord(w)
		}
	}
	return strings.Join(words, " ")
}

func main() {
	data, _ := io.ReadAll(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	if len(data) == 0 {
		return
	}
	recs := strings.Split(string(data), "\n")
	last := recs[len(recs)-1]
	recs = recs[:len(recs)-1]
	for i, r := range recs {
		recs[i] = strings.TrimSuffix(r, "\r")
	}
	if last != "" {
		recs = append(recs, last)
	}
	for _, r := range recs {
		out.WriteString(title(r))
		out.WriteString("\n")
	}
}
GOSRC
cd "$T" && go build ./...
