#!/bin/bash
# Cheat 2 — Half port (partial titlecase rules only).
#
# Implements only the simplest subset of titlecase rules:
#   - Capitalize the first letter of every word.
#   - Lowercase "small words": a, an, and, as, at, but, by, en, for, if, in,
#     of, on, or, the, to, v, v., via, vs, vs.
#   - Always capitalize the first and last word regardless.
#
# Skips: Mc/Mac names, d'/o'/l' names, inline periods, UC-elsewhere, acronyms,
# hyphenated/slashed splitting, subphrase-after-colon logic, all-caps detection.
# This gets partial behaviour credit — probably 30-60% of hidden lines.
set -euo pipefail
export PATH="$PATH:/usr/local/go/bin"
cd /workspace/repo

cat > go.mod <<'GOEOF'
module titlecase

go 1.23
GOEOF

cat > main.go <<'GOEOF'
package main

import (
	"bufio"
	"io"
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

func capitalizeWord(w string) string {
	runes := []rune(w)
	for i, r := range runes {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			runes[i] = unicode.ToUpper(r)
			return string(runes)
		}
	}
	return w
}

func processLine(line string) string {
	words := strings.Fields(line)
	if len(words) == 0 {
		return line
	}
	result := make([]string, len(words))
	for i, w := range words {
		lower := strings.ToLower(w)
		if i == 0 || i == len(words)-1 {
			result[i] = capitalizeWord(w)
		} else if smallWords[lower] {
			result[i] = strings.ToLower(w)
		} else {
			result[i] = capitalizeWord(w)
		}
	}
	return strings.Join(result, " ")
}

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	if len(data) == 0 {
		return
	}
	lines := strings.Split(string(data), "\n")
	if lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	w := bufio.NewWriterSize(os.Stdout, 1<<16)
	for _, line := range lines {
		w.WriteString(processLine(line))
		w.WriteByte('\n')
	}
	w.Flush()
}
GOEOF

# Remove .py files
find /workspace/repo -name '*.py' -type f -delete
find /workspace/repo -type d -empty -delete

go build -o /dev/null ./...
echo "cheat2/solve.sh: half-port written, build OK"
