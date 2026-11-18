#!/bin/bash
# Reference solution (the "oracle"): a Go port of python-titlecase.
# Writes go.mod + main.go into /workspace/repo, then removes every .py file.
set -euo pipefail

REPO=/workspace/repo
cd "$REPO"

cat > go.mod <<'GOMOD_EOF'
module titlecase

go 1.21
GOMOD_EOF

cat > main.go <<'GO_EOF'
// Go port of python-titlecase (titlecase/__init__.py, REGEX_AVAILABLE=True branch).
//
// Every regular expression of the original is re-implemented by hand on runes,
// because the original relies on Unicode-aware \b, \w, \p{Letter}, lazy
// quantifiers and ordered alternation, which Go's regexp does not provide.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

// PUNCT from the original: !"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~
const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

var punctSet = func() map[rune]bool {
	m := map[rune]bool{}
	for _, r := range punctChars {
		m[r] = true
	}
	return m
}()

func inPunct(r rune) bool { return punctSet[r] }

// \w of the `regex` module: letters, marks, decimal digits, underscore.
func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsMark(r) || unicode.IsDigit(r) || r == '_'
}

// \b between rs[pos-1] and rs[pos].
func boundary(rs []rune, pos int) bool {
	prev := pos > 0 && isWord(rs[pos-1])
	next := pos < len(rs) && isWord(rs[pos])
	return prev != next
}

func asciiLower(r rune) rune {
	if r >= 'A' && r <= 'Z' {
		return r + ('a' - 'A')
	}
	return r
}

// case-insensitive (ASCII) prefix test: does rs start with s?
func hasPrefixFold(rs []rune, s string) bool {
	if len(rs) < len(s) {
		return false
	}
	for i := 0; i < len(s); i++ {
		if asciiLower(rs[i]) != rune(s[i]) {
			return false
		}
	}
	return true
}

func eqFold(rs []rune, s string) bool { return len(rs) == len(s) && hasPrefixFold(rs, s) }

// Python str.capitalize() for ASCII text: first char upper, the rest lower.
func capitalize(s string) string {
	if s == "" {
		return s
	}
	return strings.ToUpper(s[:1]) + strings.ToLower(s[1:])
}

// The alternatives of SMALL, in the original order. For the two alternatives
// with an optional dot (v\.? and vs\.?) the greedy choice (with dot) is listed first.
type alt struct {
	text string // text to match, without the optional dot
	dot  bool   // followed by an optional "."
}

var smallAlts = []alt{
	{"a", false}, {"an", false}, {"and", false}, {"as", false}, {"at", false},
	{"but", false}, {"by", false}, {"en", false}, {"for", false}, {"if", false},
	{"in", false}, {"of", false}, {"on", false}, {"or", false}, {"the", false},
	{"to", false}, {"v", true}, {"via", false}, {"vs", true},
}

// candidate match lengths of alternative a at the start of rs (greedy first).
func altLens(rs []rune, a alt, fold bool) []int {
	var ok bool
	if fold {
		ok = hasPrefixFold(rs, a.text)
	} else {
		ok = len(rs) >= len(a.text) && string(rs[:len(a.text)]) == a.text
	}
	if !ok {
		return nil
	}
	n := len(a.text)
	if a.dot {
		if len(rs) > n && rs[n] == '.' {
			return []int{n + 1, n}
		}
	}
	return []int{n}
}

// ^(SMALL_WORDS)$  (case-insensitive, whole word)
func isSmallWord(rs []rune) bool {
	for _, a := range smallAlts {
		for _, n := range altLens(rs, a, true) {
			if n == len(rs) {
				return true
			}
		}
	}
	return false
}

// SMALL_FIRST = ^([PUNCT]*)(SMALL)\b   (case-insensitive), replaced by group1 + group2.capitalize()
func smallFirst(s string) string {
	rs := []rune(s)
	i := 0
	for i < len(rs) && inPunct(rs[i]) {
		i++
	}
	rest := rs[i:]
	for _, a := range smallAlts {
		for _, n := range altLens(rest, a, true) {
			if boundary(rs, i+n) {
				return string(rs[:i]) + capitalize(string(rs[i:i+n])) + string(rs[i+n:])
			}
		}
	}
	return s
}

// SMALL_LAST = \b(SMALL)[PUNCT]?$   (case-insensitive), sub with group0.capitalize()
func smallLast(s string) string {
	rs := []rune(s)
	for i := 0; i < len(rs); i++ {
		if !boundary(rs, i) {
			continue
		}
		t := rs[i:]
		if smallTail(t) {
			return string(rs[:i]) + capitalize(string(t))
		}
	}
	return s
}

// is t exactly "SMALL" or "SMALL" followed by one PUNCT char?
func smallTail(t []rune) bool {
	for _, a := range smallAlts {
		for _, n := range altLens(t, a, true) {
			if n == len(t) {
				return true
			}
			if n == len(t)-1 && inPunct(t[len(t)-1]) {
				return true
			}
		}
	}
	return false
}

// SUBPHRASE = ([:.;?!\-–‒—―][ ])(SMALL)   (case-SENSITIVE, no \b, first alternative wins)
func isSubSep(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	}
	return false
}

func subphrase(s string) string {
	rs := []rune(s)
	out := make([]rune, 0, len(rs))
	for i := 0; i < len(rs); {
		if isSubSep(rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			matched := 0
			for _, a := range smallAlts {
				if l := altLens(rs[i+2:], a, false); l != nil {
					matched = l[0] // greedy; nothing follows in the pattern, so no backtracking
					break
				}
			}
			if matched > 0 {
				out = append(out, rs[i], ' ')
				out = append(out, []rune(capitalize(string(rs[i+2:i+2+matched])))...)
				i += 2 + matched
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

// UC_INITIALS = ^(?:[Lu]\.|[Lu]\.[Lu])+$
func ucInitials(rs []rune) bool {
	n := len(rs)
	memo := make([]int8, n+1) // 0 unknown, 1 true, 2 false
	var ok func(i int) bool   // can rs[i:] be consumed by one-or-more units?
	var rest func(i int) bool // can rs[i:] be consumed by zero-or-more units?
	rest = func(i int) bool {
		if i == n {
			return true
		}
		if memo[i] != 0 {
			return memo[i] == 1
		}
		r := false
		if i+1 < n && unicode.IsUpper(rs[i]) && rs[i+1] == '.' {
			if rest(i + 2) {
				r = true
			} else if i+2 < n && unicode.IsUpper(rs[i+2]) && rest(i+3) {
				r = true
			}
		}
		if r {
			memo[i] = 1
		} else {
			memo[i] = 2
		}
		return r
	}
	ok = func(i int) bool { return i < n && rest(i) }
	return ok(0)
}

func allLetters(rs []rune) bool {
	for _, r := range rs {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return len(rs) > 0
}

// APOS_SECOND = ^[dol]['‘][Letter]+(?:['s]{2})?$   (case-insensitive)
func aposSecond(rs []rune) bool {
	if len(rs) < 3 {
		return false
	}
	switch asciiLower(rs[0]) {
	case 'd', 'o', 'l':
	default:
		return false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return false
	}
	t := rs[2:]
	if allLetters(t) {
		return true
	}
	n := len(t)
	isAS := func(r rune) bool { r = asciiLower(r); return r == '\'' || r == 's' }
	return n >= 3 && isAS(t[n-2]) && isAS(t[n-1]) && allLetters(t[:n-2])
}

// MAC_MC = ^([Mm]c|MC)(\w.+)
func macMc(rs []rune) ([]rune, bool) {
	if len(rs) < 4 {
		return nil, false
	}
	prefix := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c' || rs[0] == 'M' && rs[1] == 'C'
	if !prefix {
		return nil, false
	}
	rest := rs[2:]
	if len(rest) >= 2 && isWord(rest[0]) {
		return rest, true
	}
	return nil, false
}

// MR_MRS_MS_DR = ^((m((rs?)|s))|Dr)$   (case-insensitive)
func isHonorific(rs []rune) bool {
	return eqFold(rs, "mr") || eqFold(rs, "mrs") || eqFold(rs, "ms") || eqFold(rs, "dr")
}

// INLINE_PERIOD.search: letter "." letter anywhere
func inlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if unicode.IsLetter(rs[i]) && rs[i+1] == '.' && unicode.IsLetter(rs[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE.match = ^[PUNCT]*?[Letter]+[Lu]+?
func ucElsewhere(rs []rune) bool {
	i := 0
	for i < len(rs) && inPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return false
	}
	for j := i + 1; j < len(rs) && unicode.IsLetter(rs[j]); j++ {
		if unicode.IsUpper(rs[j]) {
			return true
		}
	}
	return false
}

// all characters are ASCII consonants (a-z without a e i o u y), case-insensitive
func allConsonants(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		r = asciiLower(r)
		if r < 'a' || r > 'z' || strings.ContainsRune("aeiouy", r) {
			return false
		}
	}
	return true
}

// CAPFIRST.sub: upper-case the first letter after the leading punctuation
func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && inPunct(rs[i]) {
		i++
	}
	if i < len(rs) && unicode.IsLetter(rs[i]) {
		return string(rs[:i]) + strings.ToUpper(string(rs[i])) + string(rs[i+1:])
	}
	return word
}

func titleParts(word, sep string) string {
	parts := strings.Split(word, sep)
	for i, p := range parts {
		parts[i] = titlecase(p, false)
	}
	return strings.Join(parts, sep)
}

func processWord(word string, allCaps bool) string {
	rs := []rune(word)
	if allCaps && ucInitials(rs) {
		return word
	}
	if aposSecond(rs) {
		first := string(rs[0])
		if !strings.ContainsRune("aeiouAEIOU", rs[0]) {
			first = strings.ToLower(first)
		} else {
			first = strings.ToUpper(first)
		}
		return first + string(rs[1]) + strings.ToUpper(string(rs[2])) + string(rs[3:])
	}
	if rest, ok := macMc(rs); ok {
		return "Mc" + titlecase(string(rest), true)
	}
	if isHonorific(rs) {
		return strings.ToUpper(string(rs[0])) + string(rs[1:])
	}
	if inlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}
	if isSmallWord(rs) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		return titleParts(word, "/")
	}
	if strings.Contains(word, "-") {
		return titleParts(word, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
		rs = []rune(word)
	}
	if allConsonants(rs) && len(rs) > 2 {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

// splitLines mimics regex.split('[\r\n]+', text)
func splitLines(text string) []string {
	var out []string
	cur := []rune{}
	rs := []rune(text)
	for i := 0; i < len(rs); {
		if rs[i] == '\r' || rs[i] == '\n' {
			out = append(out, string(cur))
			cur = cur[:0]
			for i < len(rs) && (rs[i] == '\r' || rs[i] == '\n') {
				i++
			}
			continue
		}
		cur = append(cur, rs[i])
		i++
	}
	return append(out, string(cur))
}

// titlecase(text, small_first_last=...) with all other arguments at their defaults.
func titlecase(text string, smallFirstLast bool) string {
	var processed []string
	for _, line := range splitLines(text) {
		allCaps := strings.ToUpper(line) == line
		// regex.split(r'(\s)', line): words and the separating space characters
		var words, spaces []string
		var cur []rune
		for _, r := range line {
			if unicode.IsSpace(r) {
				words = append(words, string(cur))
				spaces = append(spaces, string(r))
				cur = cur[:0]
			} else {
				cur = append(cur, r)
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
				b.WriteString(spaces[i])
			}
		}
		processed = append(processed, subphrase(b.String()))
	}
	return strings.Join(processed, "\n")
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if err != nil && (err != io.EOF || line == "") {
			break
		}
		line = strings.TrimSuffix(line, "\n")
		out.WriteString(titlecase(line, true))
		out.WriteByte('\n')
		if err != nil {
			break
		}
	}
}
GO_EOF

# The Python implementation is gone: no .py file may remain anywhere (hidden dirs included).
find "$REPO" -name '*.py' -type f -delete
# tidy up directories that are now empty (e.g. the old titlecase/ package dir)
find "$REPO" -mindepth 1 -type d -empty -delete

go build -o /dev/null ./...
