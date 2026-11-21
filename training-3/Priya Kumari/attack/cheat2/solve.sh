#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod << 'EOF'
module titlecasego

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
)

var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

func titlecaseWord(w string, isFirst, isLast bool) string {
	lower := strings.ToLower(w)
	if !isFirst && !isLast && smallWords[lower] {
		return lower
	}
	runes := []rune(lower)
	if len(runes) > 0 {
		runes[0] = unicode.ToUpper(runes[0])
	}
	return string(runes)
}

func processLine(line string) string {
	var words []string
	var seps []string

	inWord := false
	var cur strings.Builder

	for _, r := range line {
		if unicode.IsSpace(r) {
			if inWord {
				words = append(words, cur.String())
				cur.Reset()
				inWord = false
			}
			cur.WriteRune(r)
		} else {
			if !inWord {
				if cur.Len() > 0 {
					seps = append(seps, cur.String())
					cur.Reset()
				} else if len(words) == 0 {
					seps = append(seps, "")
				}
				inWord = true
			}
			cur.WriteRune(r)
		}
	}
	if inWord {
		words = append(words, cur.String())
	} else if cur.Len() > 0 {
		seps = append(seps, cur.String())
	}

	if len(words) == 0 {
		return line
	}

	var res strings.Builder
	for i, w := range words {
		if i < len(seps) {
			res.WriteString(seps[i])
		}
		isFirst := (i == 0)
		isLast := (i == len(words)-1)
		res.WriteString(titlecaseWord(w, isFirst, isLast))
	}
	if len(seps) > len(words) {
		res.WriteString(seps[len(seps)-1])
	}
	return res.String()
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	for scanner.Scan() {
		fmt.Println(processLine(scanner.Text()))
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
