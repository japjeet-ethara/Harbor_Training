#!/bin/bash
set -e
cd /workspace/repo
find . -name "*.py" -delete
cat > go.mod <<'GO_EOF'
module cheat2

go 1.23
GO_EOF
cat > main.go <<'GO_EOF'
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

func capFirst(w string) string {
	r := []rune(w)
	for i, c := range r {
		if unicode.IsLetter(c) {
			r[i] = unicode.ToUpper(c)
			break
		}
	}
	return string(r)
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<20)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for sc.Scan() {
		words := strings.Split(sc.Text(), " ")
		first, last := -1, -1
		for i, w := range words {
			if w != "" {
				if first < 0 {
					first = i
				}
				last = i
			}
		}
		for i, w := range words {
			if w == "" {
				continue
			}
			low := strings.ToLower(w)
			if small[low] && i != first && i != last {
				words[i] = low
			} else {
				words[i] = capFirst(w)
			}
		}
		out.WriteString(strings.Join(words, " "))
		out.WriteString("\n")
	}
}
GO_EOF
go build ./...
echo "cheat2 done"
