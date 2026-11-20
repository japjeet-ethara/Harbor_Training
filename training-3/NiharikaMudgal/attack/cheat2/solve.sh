#!/bin/bash
set -euo pipefail

cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete
rm -rf titlecase

cat > main.go <<'GOEOF'
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
	"to": true, "v": true, "vs": true,
}

func capitalize(s string) string {
	if s == "" {
		return s
	}
	runes := []rune(s)
	runes[0] = unicode.ToUpper(runes[0])
	return string(runes)
}

func titleWord(word string) string {
	lower := strings.ToLower(word)
	if small[strings.Trim(lower, ".")] {
		return lower
	}
	return capitalize(lower)
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()

	for in.Scan() {
		line := in.Text()
		fields := strings.Fields(line)
		leading := line[:strings.Index(line, fields[0])]
		trailingStart := strings.LastIndex(line, fields[len(fields)-1]) + len(fields[len(fields)-1])
		trailing := line[trailingStart:]

		result := leading
		for i, field := range fields {
			if i > 0 {
				result += " "
			}
			result += titleWord(field)
		}
		result += trailing
		fmt.Fprintln(out, result)
	}
}
GOEOF

cat > go.mod <<'GOEOF'
module titlecase.partial

go 1.23
GOEOF
go build ./...
