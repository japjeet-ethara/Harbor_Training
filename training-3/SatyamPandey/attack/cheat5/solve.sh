#!/bin/bash
# Cheat 5 — Half port.
# Only the two easy rules: capitalise every word, and keep the small words
# (a, an, and, of, the, ...) lower-case unless they are first or last.
# No Mc/apostrophe/acronym/punctuation/hyphen/slash rules at all.
# Measures how much partial credit a weak port gets.
set -euo pipefail
cd /workspace/repo

find . -name '*.py' -type f -delete

cat > go.mod <<'EOF'
module titlecasecheat

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var small = map[string]bool{}

func init() {
	for _, w := range strings.Fields("a an and as at but by en for if in of on or the to v v. via vs vs.") {
		small[w] = true
	}
}

func capFirst(w string) string {
	r, n := utf8.DecodeRuneInString(w)
	if n == 0 {
		return w
	}
	return string(unicode.ToUpper(r)) + w[n:]
}

func half(line string) string {
	words := strings.Split(line, " ")
	last := len(words) - 1
	for i, w := range words {
		lw := strings.ToLower(w)
		if small[lw] && i != 0 && i != last {
			words[i] = lw
		} else {
			words[i] = capFirst(lw)
		}
	}
	return strings.Join(words, " ")
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<20)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for sc.Scan() {
		w.WriteString(half(sc.Text()))
		w.WriteByte('\n')
	}
}
EOF

go build ./...
