#!/bin/bash
set -euo pipefail

cd /workspace/repo

find . -type f -name '*.py' -delete
rm -f setup.py pyproject.toml setup.cfg tox.ini

cat > go.mod <<'EOF'
module titlecasego

go 1.23
EOF

cat > main.go <<'EOF'
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
	"vs": true, "vs.": true, "via": true,
}

func allUpper(w string) bool {
	cased := false
	for _, r := range w {
		if unicode.IsLower(r) {
			return false
		}
		if unicode.IsUpper(r) {
			cased = true
		}
	}
	return cased
}

func fix(line string) string {
	rs := []rune(line)
	var parts []string
	for i := 0; i < len(rs); {
		j := i
		space := unicode.IsSpace(rs[i])
		for j < len(rs) && unicode.IsSpace(rs[j]) == space {
			j++
		}
		parts = append(parts, string(rs[i:j]))
		i = j
	}
	first, last := -1, -1
	for i, p := range parts {
		if !unicode.IsSpace([]rune(p)[0]) {
			if first < 0 {
				first = i
			}
			last = i
		}
	}
	var b strings.Builder
	for i, p := range parts {
		r := []rune(p)
		switch {
		case unicode.IsSpace(r[0]):
			b.WriteString(p)
		case small[strings.ToLower(p)] && i != first && i != last:
			b.WriteString(strings.ToLower(p))
		case allUpper(p) && len(r) > 1:
			b.WriteString(p)
		default:
			b.WriteRune(unicode.ToUpper(r[0]))
			b.WriteString(string(r[1:]))
		}
	}
	return b.String()
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1<<20), 1<<20)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		out.WriteString(fix(in.Text()))
		out.WriteByte('\n')
	}
}
EOF
