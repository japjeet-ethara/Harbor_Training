#!/bin/bash
set -euo pipefail
cd /workspace/repo

find . -type f -name '*.py' -delete

cat > go.mod << 'EOF'
module example.com/cheat3

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode/utf8"
)

func titleLike(line string) string {
	words := strings.Fields(line)
	for i, word := range words {
		word = strings.ToLower(word)
		r, size := utf8.DecodeRuneInString(word)
		if r != utf8.RuneError || size != 0 {
			word = strings.ToUpper(string(r)) + word[size:]
		}
		words[i] = word
	}
	return strings.Join(words, " ")
}

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()

	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			if line[len(line)-1] == '\n' {
				line = line[:len(line)-1]
				if strings.HasSuffix(line, "\r") {
					line = line[:len(line)-1]
				}
			}
			if _, writeErr := out.WriteString(titleLike(line) + "\n"); writeErr != nil {
				os.Exit(1)
			}
		}
		if err != nil {
			if err == io.EOF {
				return
			}
			os.Exit(1)
		}
	}
}
EOF


