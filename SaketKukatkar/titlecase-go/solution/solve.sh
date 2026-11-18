#!/bin/bash
# Oracle: a Go port of python-titlecase, standard library only.
# Writes go.mod + main.go into /workspace/repo, removes every .py file (and the
# directories that leaves empty), and checks the result builds.
set -euo pipefail

cd /workspace/repo

# The Python implementation must be gone.
find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -type d -name '__pycache__' -prune -exec rm -rf {} +
find /workspace/repo -mindepth 1 -type d -empty -delete

# Module name differs from the old Python package directory name on purpose:
# `go build ./...` names its executable after the module.
cat > go.mod <<'GO_PORT_EOF'
module titlecasego

go 1.23
GO_PORT_EOF

cat > main.go <<'GO_PORT_EOF'
// Go port of python-titlecase 2.4.1 (regex-package code path).
// Standard library only; the look-around / backtracking regexes of the
// original are replaced by explicit character-level checks.
package main

import (
	"bufio"
	"os"
	"regexp"
	"strings"
	"unicode"
	"unicode/utf8"
)

const punctChars = "!\"\u201c#$%&'\u2018()*+,-\u2013\u2012\u2014\u2015./:;?@[\\]_`{|}~"
const subphrasePunct = ":.;?!-\u2013\u2012\u2014\u2015"
const consonants = "bcdfghjklmnpqrstvwxz"

// SMALL alternatives in the order of the original alternation, with the
// optional-dot variants expanded greedy-first.
var smallAlts = []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs"}

var smallSet = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true, "by": true,
	"en": true, "for": true, "if": true, "in": true, "of": true, "on": true, "or": true,
	"the": true, "to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

var newlineRun = regexp.MustCompile("[\r\n]+")

func isPunct(r rune) bool { return strings.ContainsRune(punctChars, r) }

func isWordRune(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.IsMark(r) || r == '_' || unicode.Is(unicode.Pc, r)
}

// boundary reports whether a regex \b matches at rune index j.
func boundary(r []rune, j int) bool {
	before := j > 0 && isWordRune(r[j-1])
	after := j < len(r) && isWordRune(r[j])
	return before != after
}

func capitalize(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return s
	}
	out := []rune{unicode.ToUpper(r[0])}
	for _, c := range r[1:] {
		out = append(out, unicode.ToLower(c))
	}
	return string(out)
}

func allLetters(r []rune) bool {
	if len(r) == 0 {
		return false
	}
	for _, c := range r {
		if !unicode.IsLetter(c) {
			return false
		}
	}
	return true
}

// ^([PUNCT]*)(SMALL)\b  (case-insensitive) -> capitalise group 2
func smallFirst(s string) string {
	r := []rune(s)
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	for _, alt := range smallAlts {
		k := utf8.RuneCountInString(alt)
		if i+k > len(r) {
			continue
		}
		seg := string(r[i : i+k])
		if strings.ToLower(seg) != alt {
			continue
		}
		if boundary(r, i+k) {
			return string(r[:i]) + capitalize(seg) + string(r[i+k:])
		}
	}
	return s
}

// \b(SMALL)[PUNCT]?$  (case-insensitive), leftmost match -> capitalise it
func smallLast(s string) string {
	r := []rune(s)
	for i := range r {
		if !boundary(r, i) {
			continue
		}
		tail := string(r[i:])
		low := strings.ToLower(tail)
		for alt := range smallSet {
			if low == alt {
				return string(r[:i]) + capitalize(tail)
			}
			if strings.HasPrefix(low, alt) {
				rest := []rune(low[len(alt):])
				if len(rest) == 1 && isPunct(rest[0]) {
					return string(r[:i]) + capitalize(tail)
				}
			}
		}
	}
	return s
}

func isSubPunct(r rune) bool { return strings.ContainsRune(subphrasePunct, r) }

// first alternative (in regex order, case-sensitive) that is a prefix of t
func smallPrefixLen(t []rune) int {
	for _, alt := range smallAlts {
		ar := []rune(alt)
		if len(t) >= len(ar) && string(t[:len(ar)]) == alt {
			return len(ar)
		}
	}
	return 0
}

// ([:.;?!-...][ ])(SMALL) -> group1 + group2.capitalize(), left to right, non-overlapping
func subphrase(s string) string {
	r := []rune(s)
	out := make([]rune, 0, len(r))
	p := 0
	for p < len(r) {
		if isSubPunct(r[p]) && p+1 < len(r) && r[p+1] == ' ' {
			k := smallPrefixLen(r[p+2:])
			if k > 0 {
				out = append(out, r[p], ' ')
				out = append(out, []rune(capitalize(string(r[p+2:p+2+k])))...)
				p += 2 + k
				continue
			}
		}
		out = append(out, r[p])
		p++
	}
	return string(out)
}

// UC_INITIALS: ^(?:[Lu]\.|[Lu]\.[Lu])+$
func ucInitials(r []rune) bool {
	n := len(r)
	memo := make(map[int]int) // 0 unknown, 1 true, 2 false
	var f func(i int) bool
	f = func(i int) bool {
		if i == n {
			return true
		}
		if v, ok := memo[i]; ok {
			return v == 1
		}
		res := false
		if i+1 < n && unicode.IsUpper(r[i]) && r[i+1] == '.' {
			if f(i + 2) {
				res = true
			} else if i+2 < n && unicode.IsUpper(r[i+2]) && f(i+3) {
				res = true
			}
		}
		if res {
			memo[i] = 1
		} else {
			memo[i] = 2
		}
		return res
	}
	if n == 0 {
		return false
	}
	return f(0)
}

// APOS_SECOND: ^[dol]['\u2018][Letter]+(?:['s]{2})?$  (case-insensitive)
func aposSecond(r []rune) bool {
	if len(r) < 3 {
		return false
	}
	switch unicode.ToLower(r[0]) {
	case 'd', 'o', 'l':
	default:
		return false
	}
	if r[1] != '\'' && r[1] != '\u2018' {
		return false
	}
	rest := r[2:]
	if allLetters(rest) {
		return true
	}
	if len(rest) >= 3 {
		head := rest[:len(rest)-2]
		a, b := rest[len(rest)-2], rest[len(rest)-1]
		ok := func(c rune) bool { return c == '\'' || c == 's' || c == 'S' }
		if allLetters(head) && ok(a) && ok(b) {
			return true
		}
	}
	return false
}

// INLINE_PERIOD: [Letter][.][Letter] anywhere
func inlinePeriod(r []rune) bool {
	for i := 1; i+1 < len(r); i++ {
		if r[i] == '.' && unicode.IsLetter(r[i-1]) && unicode.IsLetter(r[i+1]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE.match: ^[PUNCT]*?[Letter]+[Lu]+?
func ucElsewhere(r []rune) bool {
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	j := i
	for j < len(r) && unicode.IsLetter(r[j]) {
		j++
	}
	if j-i < 2 {
		return false
	}
	for _, c := range r[i+1 : j] {
		if unicode.IsUpper(c) {
			return true
		}
	}
	return false
}

func allConsonants(r []rune) bool {
	if len(r) == 0 {
		return false
	}
	for _, c := range r {
		if !strings.ContainsRune(consonants, unicode.ToLower(c)) {
			return false
		}
	}
	return true
}

func upperFirst(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return s
	}
	r[0] = unicode.ToUpper(r[0])
	return string(r)
}

func processWord(word string, allCaps bool) string {
	r := []rune(word)
	if allCaps && ucInitials(r) {
		return word
	}
	if aposSecond(r) {
		first := r[0]
		var f rune
		if strings.ContainsRune("aeiouAEIOU", first) {
			f = unicode.ToUpper(first)
		} else {
			f = unicode.ToLower(first)
		}
		out := []rune{f, r[1], unicode.ToUpper(r[2])}
		out = append(out, r[3:]...)
		return string(out)
	}
	if len(r) >= 4 {
		p := string(r[:2])
		if (p == "Mc" || p == "mc" || p == "MC") && isWordRune(r[2]) {
			return "Mc" + titlecase(string(r[2:]), true)
		}
	}
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return upperFirst(word)
	}
	if inlinePeriod(r) || (!allCaps && ucElsewhere(r)) {
		return word
	}
	if smallSet[strings.ToLower(word)] {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
		r = []rune(word)
	}
	if len(r) > 2 && allConsonants(r) {
		return strings.ToUpper(word)
	}
	// CAPFIRST
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	if i < len(r) && unicode.IsLetter(r[i]) {
		r[i] = unicode.ToUpper(r[i])
	}
	return string(r)
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	var words []string
	var spaces []rune
	cur := []rune{}
	for _, ch := range line {
		if unicode.IsSpace(ch) {
			words = append(words, string(cur))
			spaces = append(spaces, ch)
			cur = cur[:0]
		} else {
			cur = append(cur, ch)
		}
	}
	words = append(words, string(cur))

	tc := make([]string, len(words))
	for i, w := range words {
		tc[i] = processWord(w, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = smallFirst(tc[0])
		tc[len(tc)-1] = smallLast(tc[len(tc)-1])
	}
	var b strings.Builder
	for i, w := range tc {
		b.WriteString(w)
		if i < len(spaces) {
			b.WriteRune(spaces[i])
		}
	}
	return subphrase(b.String())
}

func titlecase(text string, smallFirstLast bool) string {
	lines := newlineRun.Split(text, -1)
	out := make([]string, len(lines))
	for i, l := range lines {
		out[i] = processLine(l, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 || err == nil {
			hadNL := strings.HasSuffix(line, "\n")
			line = strings.TrimSuffix(line, "\n")
			out.WriteString(titlecase(line, true))
			if hadNL {
				out.WriteByte('\n')
			}
		}
		if err != nil {
			break
		}
	}
}
GO_PORT_EOF

go build ./...
