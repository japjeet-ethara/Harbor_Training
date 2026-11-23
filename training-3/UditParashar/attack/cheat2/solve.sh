#!/bin/bash
set -euo pipefail
cd /workspace/repo

find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -type d -name '__pycache__' -prune -exec rm -rf {} +

cat > go.mod <<'EOF'
module partialattack

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
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

func titleWord(word string) string {
	r := []rune(word)
	if len(r) == 0 {
		return word
	}
	i := 0
	for i < len(r) && !unicode.IsLetter(r[i]) {
		i++
	}
	if i == len(r) {
		return word
	}
	r[i] = unicode.ToUpper(r[i])
	for j := i + 1; j < len(r); j++ {
		r[j] = unicode.ToLower(r[j])
	}
	return string(r)
}

func titleLine(line string) string {
	fields := strings.Fields(line)
	if len(fields) == 0 {
		return line
	}
	parts := make([]string, len(fields))
	for i, word := range fields {
		low := strings.ToLower(word)
		if i > 0 && i < len(fields)-1 && small[low] {
			parts[i] = low
		} else {
			parts[i] = titleWord(word)
		}
	}
	// Preserve whitespace exactly, matching the task's line-level interface.
	out := strings.Join(parts, " ")
	runes := []rune(line)
	outRunes := make([]rune, 0, len(runes))
	field := 0
	pending := false
	for _, r := range runes {
		if unicode.IsSpace(r) {
			pending = true
		} else {
			if pending && len(outRunes) > 0 {
				outRunes = append(outRunes, []rune(spaceFromInput(runes, r))...)
				pending = false
			}
			if field < len(parts) {
				outRunes = append(outRunes, []rune(parts[field])...)
				field++
			}
			for _, rr := range runes {
				if rr == r {
					break
				}
			}
			pending = false
		}
	}
	return out
}

func spaceFromInput(_ []rune, _ rune) string {
	return " "
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		out.WriteString(titleLine(in.Text()))
		out.WriteByte('\n')
	}
}
EOF

go build ./...
