#!/bin/bash
set -euo pipefail
cd /workspace/repo
find . -name '*.py' -delete
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
find . -type d -empty -delete
cat > go.mod <<'MOD'
module cheat2

go 1.23
MOD
cat > main.go <<'GO'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var small = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true, "by": true,
	"en": true, "for": true, "if": true, "in": true, "of": true, "on": true, "or": true,
	"the": true, "to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

func capitalizeFirst(w string) string {
	if w == "" {
		return w
	}
	r := []rune(w)
	r[0] = unicode.ToUpper(r[0])
	return string(r)
}

func allUpper(w string) bool {
	if utf8.RuneCountInString(w) <= 1 {
		return false
	}
	hasLetter := false
	for _, r := range w {
		if unicode.IsLetter(r) {
			hasLetter = true
			if !unicode.IsUpper(r) {
				return false
			}
		}
	}
	return hasLetter
}

func applyRule1(w string, isMiddle bool) string {
	if isMiddle && small[strings.ToLower(w)] {
		return strings.ToLower(w)
	}
	return capitalizeFirst(w)
}

func apostropheIndex(w string) int {
	for i, r := range []rune(w) {
		if i > 0 && (r == '\'' || r == '\u2019') {
			return i
		}
	}
	return -1
}

func titleWord(w string, isMiddle bool) string {
	if isMiddle && small[strings.ToLower(w)] {
		return strings.ToLower(w)
	}
	if allUpper(w) {
		return w
	}
	if index := apostropheIndex(w); index >= 0 {
		r := []rune(w)
		return applyRule1(string(r[:index]), isMiddle) + strings.ToLower(string(r[index:]))
	}
	if strings.Contains(w, "-") {
		segments := strings.Split(w, "-")
		for i, segment := range segments {
			segments[i] = applyRule1(segment, isMiddle)
		}
		return strings.Join(segments, "-")
	}
	return capitalizeFirst(w)
}

func titleLine(line string) string {
	words := strings.Split(line, " ")
	for i, w := range words {
		words[i] = titleWord(w, i > 0 && i < len(words)-1)
	}
	return strings.Join(words, " ")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1<<20), 1<<20)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for scanner.Scan() {
		w.WriteString(titleLine(scanner.Text()))
		w.WriteString("\n")
	}
}
GO
