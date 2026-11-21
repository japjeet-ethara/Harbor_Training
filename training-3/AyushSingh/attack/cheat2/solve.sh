#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Remove all Python files
find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/python-titlecase

cat << 'EOF' > /workspace/repo/go.mod
module titlecase-go

go 1.23
EOF

cat << 'EOF' > /workspace/repo/main.go
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

func capWord(w string) string {
	if w == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(w)
	return strings.ToUpper(string(r)) + strings.ToLower(w[size:])
}

func halfTitle(line string) string {
	var words []string
	var spaces []string
	var cur strings.Builder

	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, cur.String())
			cur.Reset()
			spaces = append(spaces, string(r))
		} else {
			cur.WriteRune(r)
		}
	}
	words = append(words, cur.String())

	var out []string
	n := len(words)
	for i, w := range words {
		if w == "" {
			out = append(out, "")
			continue
		}
		low := strings.ToLower(w)
		if smallWords[low] && i != 0 && i != n-1 {
			out = append(out, low)
		} else {
			out = append(out, capWord(w))
		}
	}

	var res strings.Builder
	for i := range out {
		res.WriteString(out[i])
		if i < len(spaces) {
			res.WriteString(spaces[i])
		}
	}
	return res.String()
}

func main() {
	reader := bufio.NewReader(os.Stdin)
	for {
		line, err := reader.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimRight(line, "\r\n")
			fmt.Println(halfTitle(line))
		}
		if err != nil {
			if err == io.EOF {
				break
			}
			os.Exit(1)
		}
	}
}
EOF

go build ./...
