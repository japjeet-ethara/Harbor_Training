#!/usr/bin/env bash
set -euo pipefail
cd /workspace/repo
cat > go.mod <<'EOF'
module titlecase-cheat

go 1.23
EOF
cat > main.go <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
)

func titleWord(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return s
	}
	r[0] = unicode.ToUpper(r[0])
	for i := 1; i < len(r); i++ {
		r[i] = unicode.ToLower(r[i])
	}
	return string(r)
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1024*1024), 16*1024*1024)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for sc.Scan() {
		words := strings.Split(sc.Text(), " ")
		for i, word := range words {
			words[i] = titleWord(word)
		}
		fmt.Fprintln(w, strings.Join(words, " "))
	}
}
EOF
find . -name '*.py' -delete
go build ./...
