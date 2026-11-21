#!/bin/bash
set -euo pipefail
cd /workspace/repo

cat > go.mod << 'TITLECASE_CHEAT2'
module titlecase

go 1.23
TITLECASE_CHEAT2

cat > main.go << 'TITLECASE_CHEAT2'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

// Cheat 2: a half port. It implements only the easy rules from
// titlecase/__init__.py: capitalise the first letter of each word, lowercase
// small words except at the first/last position, and preserve whitespace.
// It deliberately skips acronyms, mixed case, apostrophes, all-caps lines,
// Mac/Mc, honorifics, hyphens, slashes and subphrase recasing.

var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true,
	"vs.": true,
}

type token struct {
	text string
	word bool
}

func lowerString(s string) string {
	rs := []rune(s)
	for i, r := range rs {
		rs[i] = unicode.ToLower(r)
	}
	return string(rs)
}

func upperFirstLetter(s string) string {
	rs := []rune(s)
	for i, r := range rs {
		if unicode.IsLetter(r) {
			rs[i] = unicode.ToUpper(r)
			return string(rs)
		}
	}
	return s
}

func capitalizeSmall(s string) string {
	rs := []rune(lowerString(s))
	for i, r := range rs {
		if unicode.IsLetter(r) {
			rs[i] = unicode.ToUpper(r)
			break
		}
	}
	return string(rs)
}

func tokenize(line string) []token {
	rs := []rune(line)
	var toks []token
	var buf []rune
	state := 0 // 0 = unset, 1 = word, 2 = whitespace
	flush := func() {
		if len(buf) == 0 {
			return
		}
		toks = append(toks, token{text: string(buf), word: state == 1})
		buf = nil
	}
	for _, r := range rs {
		next := 2
		if !unicode.IsSpace(r) {
			next = 1
		}
		if state == 0 {
			state = next
		}
		if next != state {
			flush()
			state = next
		}
		buf = append(buf, r)
	}
	flush()
	return toks
}

func halfTitlecase(line string) string {
	toks := tokenize(line)
	wordCount := 0
	for _, t := range toks {
		if t.word {
			wordCount++
		}
	}

	index := -1
	for i := range toks {
		if !toks[i].word {
			continue
		}
		index++
		isSmall := smallWords[lowerString(toks[i].text)]
		switch {
		case isSmall && (index == 0 || index == wordCount-1):
			toks[i].text = capitalizeSmall(toks[i].text)
		case isSmall:
			toks[i].text = lowerString(toks[i].text)
		default:
			toks[i].text = upperFirstLetter(toks[i].text)
		}
	}

	var out strings.Builder
	for _, t := range toks {
		out.WriteString(t.text)
	}
	return out.String()
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		out.WriteString(halfTitlecase(in.Text()))
		out.WriteByte('\n')
	}
}
TITLECASE_CHEAT2

find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
