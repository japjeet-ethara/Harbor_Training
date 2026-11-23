#!/bin/bash
set -euo pipefail

REPO=/workspace/repo
mkdir -p "$REPO"

cat > "$REPO/go.mod" << 'EOF'
module titlecase

go 1.23
EOF

cat > "$REPO/titlecase.go" << 'EOF'
package main

import (
	"bufio"
	"fmt"
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
	lower := strings.ToLower(word)
	if small[lower] {
		return lower
	}
	runes := []rune(word)
	if len(runes) == 0 {
		return word
	}
	runes[0] = unicode.ToUpper(runes[0])
	for i := 1; i < len(runes); i++ {
		runes[i] = unicode.ToLower(runes[i])
	}
	return string(runes)
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		line := scanner.Text()
		fields := strings.Fields(line)
		for i, field := range fields {
			if i == 0 {
				fields[i] = titleWord(field)
			} else if small[strings.ToLower(field)] {
				fields[i] = strings.ToLower(field)
			} else {
				fields[i] = titleWord(field)
			}
		}
		fmt.Println(strings.Join(fields, " "))
	}
}
EOF
