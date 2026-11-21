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
	"unicode"
)

func simpleTitle(s string) string {
	var b []rune
	inWord := false
	for _, r := range s {
		if unicode.IsSpace(r) {
			b = append(b, r)
			inWord = false
		} else {
			if !inWord {
				b = append(b, unicode.ToUpper(r))
				inWord = true
			} else {
				b = append(b, unicode.ToLower(r))
			}
		}
	}
	return string(b)
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	for scanner.Scan() {
		line := scanner.Text()
		fmt.Println(simpleTitle(line))
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
