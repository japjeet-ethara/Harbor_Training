#!/bin/bash
set -euo pipefail

cd /workspace/repo
cat > go.mod << 'EOF'
module titlecase

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
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "for": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "via": true,
	"v": true, "vs": true,
}

func titleWord(word string, first, last bool) string {
	lower := strings.ToLower(word)
	if small[lower] && !first && !last {
		return lower
	}
	r, size := utf8.DecodeRuneInString(word)
	if r == utf8.RuneError {
		return word
	}
	return string(unicode.ToUpper(r)) + strings.ToLower(word[size:])
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		fields := strings.Fields(in.Text())
		for i, word := range fields {
			fields[i] = titleWord(word, i == 0, i == len(fields)-1)
		}
		_, _ = out.WriteString(strings.Join(fields, " "))
		_, _ = out.WriteString("\n")
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
go build ./...
