#!/bin/bash
set -euo pipefail
cd /workspace/repo
find /workspace/repo -type f -name "*.py" -delete
rm -rf titlecase
cat << 'GOMOD' > go.mod
module titlecase-naive

go 1.23
GOMOD
cat << 'MAIN' > main.go
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

func titleNaive(line string) string {
	words := strings.Split(line, " ")
	for i, w := range words {
		if w == "" {
			continue
		}
		lw := strings.ToLower(w)
		if i > 0 && i < len(words)-1 && small[lw] {
			words[i] = lw
			continue
		}
		runes := []rune(lw)
		for j, r := range runes {
			if unicode.IsLetter(r) {
				runes[j] = unicode.ToUpper(r)
				break
			}
		}
		words[i] = string(runes)
	}
	return strings.Join(words, " ")
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	for sc.Scan() {
		fmt.Println(titleNaive(sc.Text()))
	}
}
MAIN
go build ./...
