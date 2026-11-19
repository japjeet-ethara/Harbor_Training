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
	"strings"
	"unicode"
)

var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

func isSubMark(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	}
	return false
}

func isDash(r rune) bool {
	switch r {
	case '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	}
	return false
}

func isApostrophe(r rune) bool {
	return r == '\'' || r == '\u2018' || r == '\u2019'
}

func capSimple(s string) string {
	runes := []rune(s)
	if len(runes) == 0 {
		return ""
	}
	runes[0] = unicode.ToUpper(runes[0])
	for i := 1; i < len(runes); i++ {
		runes[i] = unicode.ToLower(runes[i])
	}
	return string(runes)
}

func titlecaseApostrophe(w string) string {
	lower := strings.ToLower(w)
	if len(lower) > 2 && isApostrophe(rune(lower[1])) {
		rest := lower[2:]
		switch lower[0] {
		case 'o':
			return "O" + string(lower[1]) + capSimple(rest)
		case 'l':
			return "l" + string(lower[1]) + capSimple(rest)
		case 'd':
			return "d" + string(lower[1]) + capSimple(rest)
		}
	}
	if len(lower) > 2 && isApostrophe(rune(lower[len(lower)-2])) && lower[len(lower)-1] == 's' {
		stem := lower[:len(lower)-2]
		return capSimple(stem) + string(lower[len(lower)-2:])
	}
	return capSimple(lower)
}

func titlecasePart(part string, isFirstInLine, isLastInLine, afterSubBreak bool) string {
	lower := strings.ToLower(part)
	if !isFirstInLine && !isLastInLine && !afterSubBreak && smallWords[lower] {
		return lower
	}
	return titlecaseApostrophe(part)
}

func titlecaseWord(w string, isFirst, isLast, afterSubBreak bool) string {
	dashIdx := -1
	for i, r := range w {
		if isDash(r) {
			dashIdx = i
			break
		}
	}
	if dashIdx != -1 {
		var b strings.Builder
		cur := ""
		for _, r := range w {
			if isDash(r) {
				if cur != "" {
					b.WriteString(titlecasePart(cur, isFirst, false, afterSubBreak))
					cur = ""
				}
				b.WriteRune(r)
			} else {
				cur += string(r)
			}
		}
		if cur != "" {
			b.WriteString(titlecasePart(cur, false, isLast, false))
		}
		return b.String()
	}

	return titlecasePart(w, isFirst, isLast, afterSubBreak)
}

func processLine(line string) string {
	if line == "" {
		return ""
	}

	type chunk struct {
		isSpace bool
		text    string
	}
	var chunks []chunk
	inSpace := unicode.IsSpace(rune(line[0]))
	var cur strings.Builder
	for _, r := range line {
		sp := unicode.IsSpace(r)
		if sp != inSpace {
			chunks = append(chunks, chunk{isSpace: inSpace, text: cur.String()})
			cur.Reset()
			inSpace = sp
		}
		cur.WriteRune(r)
	}
	if cur.Len() > 0 {
		chunks = append(chunks, chunk{isSpace: inSpace, text: cur.String()})
	}

	var wordIndices []int
	for i, c := range chunks {
		if !c.isSpace {
			wordIndices = append(wordIndices, i)
		}
	}
	if len(wordIndices) == 0 {
		return line
	}

	afterSubBreak := false
	var res strings.Builder

	for i, c := range chunks {
		if c.isSpace {
			res.WriteString(c.text)
			continue
		}

		pos := -1
		for p, widx := range wordIndices {
			if widx == i {
				pos = p
				break
			}
		}
		isFirst := (pos == 0)
		isLast := (pos == len(wordIndices)-1)

		subBreak := afterSubBreak
		res.WriteString(titlecaseWord(c.text, isFirst, isLast, subBreak))

		runes := []rune(c.text)
		afterSubBreak = false
		if len(runes) > 0 && isSubMark(runes[len(runes)-1]) {
			afterSubBreak = true
		}
	}

	return res.String()
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	for scanner.Scan() {
		fmt.Println(processLine(scanner.Text()))
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
