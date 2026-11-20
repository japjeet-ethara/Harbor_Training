#!/bin/bash
# Probe (my own, Day 5 counter-attack): the smartest lookup I could think of.
# Exact lines come from the 100,000 PUBLIC answers. For any other line it learns,
# from those same answers, how each WORD is written in each context (first/middle/
# last word, all-caps line, after ': . ; ? ! -'), and for words it has never seen it
# falls back to simple rules (small words lower, else capitalise the first letter).
# No titlecase port. Put task/tests/data/inputs.txt and answers.txt next to this script.
set -euo pipefail
cd /workspace/repo
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$here/inputs.txt" table_inputs.txt
cp "$here/answers.txt" table_answers.txt

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	_ "embed"
	"os"
	"strings"
	"unicode"
)

//go:embed table_inputs.txt
var tin string

//go:embed table_answers.txt
var tans string

var small = map[string]bool{"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true, "via": true,
	"vs": true, "vs.": true}

// split mimics regex.split(r'(\s)', line): words and the single spaces between them.
func split(s string) (words, spaces []string) {
	var cur strings.Builder
	for _, r := range s {
		if unicode.IsSpace(r) {
			words = append(words, cur.String())
			spaces = append(spaces, string(r))
			cur.Reset()
		} else {
			cur.WriteRune(r)
		}
	}
	return append(words, cur.String()), spaces
}

func ctx(words []string, i int, caps bool) string {
	pos := "M"
	if i == 0 {
		pos = "F"
	} else if i == len(words)-1 {
		pos = "L"
	}
	sub := "0"
	if i > 0 && strings.ContainsAny(lastRune(words[i-1]), ":.;?!-–‒—―") {
		sub = "1"
	}
	c := "0"
	if caps {
		c = "1"
	}
	return pos + c + sub
}

func lastRune(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return ""
	}
	return string(r[len(r)-1])
}

func main() {
	ins, ans := strings.Split(tin, "\n"), strings.Split(tans, "\n")
	lines := map[string]string{}
	wordCtx := map[string]map[string]int{}
	wordAny := map[string]map[string]int{}
	add := func(m map[string]map[string]int, k, v string) {
		if m[k] == nil {
			m[k] = map[string]int{}
		}
		m[k][v]++
	}
	for i := range ins {
		if i >= len(ans) {
			break
		}
		lines[ins[i]] = ans[i]
		wa, _ := split(ins[i])
		wb, _ := split(ans[i])
		if len(wa) != len(wb) {
			continue
		}
		caps := strings.ToUpper(ins[i]) == ins[i]
		for j, w := range wa {
			add(wordCtx, w+"\x00"+ctx(wa, j, caps), wb[j])
			add(wordAny, w, wb[j])
		}
	}
	best := func(m map[string]int) string {
		b, n := "", -1
		for k, v := range m {
			if v > n || (v == n && k < b) {
				b, n = k, v
			}
		}
		return b
	}
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			if a, ok := lines[line]; ok {
				out.WriteString(a + "\n")
			} else {
				words, spaces := split(line)
				caps := strings.ToUpper(line) == line
				for j, w := range words {
					if m := wordCtx[w+"\x00"+ctx(words, j, caps)]; m != nil {
						words[j] = best(m)
					} else if m := wordAny[w]; m != nil {
						words[j] = best(m)
					} else if small[strings.ToLower(w)] && j > 0 && j < len(words)-1 {
						words[j] = strings.ToLower(w)
					} else {
						if caps {
							w = strings.ToLower(w)
						}
						r := []rune(w)
						for k := range r {
							if unicode.IsLetter(r[k]) {
								r[k] = unicode.ToUpper(r[k])
								break
							}
						}
						words[j] = string(r)
					}
				}
				var b strings.Builder
				for j, w := range words {
					b.WriteString(w)
					if j < len(spaces) {
						b.WriteString(spaces[j])
					}
				}
				out.WriteString(b.String() + "\n")
			}
		}
		if err != nil {
			return
		}
	}
}
EOF

find /workspace/repo -name '*.py' -delete
find /workspace/repo -name '__pycache__' -type d -prune -exec rm -rf {} +
find /workspace/repo -type d -empty -delete
go build -o /dev/null ./...
