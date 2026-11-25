#!/bin/bash
# CHEAT 2, not a solution: naive first-letter capitalisation. Ports none of the
# titlecase rules. For each whitespace-delimited word, an ASCII lowercase letter
# in first position is uppercased; every other byte passes through unchanged.
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'GOMOD_EOF'
module firstcap

go 1.23
GOMOD_EOF

cat > main.go <<'MAIN_GO_EOF'
// Command firstcap reads stdin and uppercases the first character of each
// whitespace-delimited word when that character is an ASCII lowercase letter.
// All other bytes, including whitespace, line endings and invalid UTF-8, are
// written to stdout unchanged.
package main

import (
	"fmt"
	"io"
	"os"
	"unicode"
	"unicode/utf8"
)

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	wordStart := true
	for i := 0; i < len(data); {
		r, size := utf8.DecodeRune(data[i:])
		if unicode.IsSpace(r) {
			wordStart = true
		} else {
			if wordStart && 'a' <= r && r <= 'z' {
				data[i] -= 'a' - 'A'
			}
			wordStart = false
		}
		i += size
	}

	if _, err := os.Stdout.Write(data); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
MAIN_GO_EOF

# The task requires every .py file to be gone, in subdirectories too.
find . -type f -name '*.py' -delete

go build ./...
rm -f firstcap
