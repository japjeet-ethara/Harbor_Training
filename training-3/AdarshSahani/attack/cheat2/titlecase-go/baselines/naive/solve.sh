#!/bin/bash
# NAIVE BASELINE (hand-written, NOT an LLM run): capitalise every word except small words in the middle.
# Ignores acronyms, URLs, hyphens, slashes, Mc/apostrophe names, sub-phrases, all-caps lines, tabs, ...
set -euo pipefail
cd /workspace/repo
printf 'module titlecase\n\ngo 1.23\n' > go.mod
cat > main.go <<'GOSRC'
package main

import (
	"bufio"
	"os"
	"strings"
)

var small = map[string]bool{"a": true, "an": true, "and": true, "as": true, "at": true, "but": true, "by": true,
	"en": true, "for": true, "if": true, "in": true, "of": true, "on": true, "or": true, "the": true, "to": true,
	"v": true, "v.": true, "via": true, "vs": true, "vs.": true}

func cap1(w string) string {
	if w == "" {
		return w
	}
	r := []rune(w)
	return strings.ToUpper(string(r[0])) + string(r[1:])
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<20)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for sc.Scan() {
		ws := strings.Split(sc.Text(), " ")
		for i, w := range ws {
			if i > 0 && i < len(ws)-1 && small[strings.ToLower(w)] {
				ws[i] = strings.ToLower(w)
			} else {
				ws[i] = cap1(w)
			}
		}
		out.WriteString(strings.Join(ws, " ") + "\n")
	}
}
GOSRC
find /workspace/repo -type f -name '*.py' -delete
go build -o /dev/null ./...
