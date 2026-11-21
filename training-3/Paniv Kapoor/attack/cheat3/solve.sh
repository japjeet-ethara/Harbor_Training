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
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
)

// halfTitlecase implements only basic titlecase behavior:
// lowercasing words and capitalizing the first letter.
// Deliberately leaves advanced rules such as acronyms, Mc names,
// punctuation, and hyphen/slash handling incomplete.
func halfTitlecase(line string) string {
	var b strings.Builder
	inWord := false
	for _, r := range line {
		if unicode.IsSpace(r) {
			inWord = false
			b.WriteRune(r)
		} else {
			if !inWord {
				b.WriteRune(unicode.ToUpper(r))
				inWord = true
			} else {
				b.WriteRune(unicode.ToLower(r))
			}
		}
	}
	return b.String()
}

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()

	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimRight(line, "\r\n")
			fmt.Fprintln(out, halfTitlecase(line))
		}
		if err != nil {
			if err != io.EOF {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
			break
		}
	}
}
EOF

# Ensure clean build and no .py files
find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
