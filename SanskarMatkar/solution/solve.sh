#!/bin/bash
# Oracle solution: write a standard-library-only Go port of python-titlecase
# 2.4.1 into /workspace/repo, delete every .py file, and check it builds.
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'GOMOD'
module titlecase

go 1.23
GOMOD

cat > main.go <<'GOEOF'
// Command titlecase is a byte-for-byte Go port of python-titlecase 2.4.1
// (stdlib-`re` code path, default arguments). It reads one title per line on
// stdin and writes the titlecased title per line on stdout.
//
// Go's regexp has no look-around/back-references and its \w, \s, \b are
// ASCII-only, so every Python pattern is re-implemented as hand-written rune
// scanning that follows Python's matching rules (alternation order,
// greedy/lazy quantifiers, Unicode \w and \s, IGNORECASE folding).
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

// ---------------------------------------------------------------- char classes

// PUNCT = !"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~
func isPunct(r rune) bool {
	switch r {
	case '!', '"', '“', '#', '$', '%', '&', '\'', '‘', '(', ')', '*',
		'+', ',', '-', '–', '‒', '—', '―', '.', '/', ':',
		';', '?', '@', '[', '\\', ']', '_', '`', '{', '|', '}', '~':
		return true
	}
	return false
}

// Python 3 `\s` for str patterns (== str.isspace()).
func isSpace(r rune) bool {
	switch {
	case r >= 0x09 && r <= 0x0d, r >= 0x1c && r <= 0x20:
		return true
	case r == 0x85, r == 0xa0, r == 0x1680, r >= 0x2000 && r <= 0x200a,
		r == 0x2028, r == 0x2029, r == 0x202f, r == 0x205f, r == 0x3000:
		return true
	}
	return false
}

// Python 3 `\w` for str patterns (str.isalnum() or '_').
func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isASCIILetter(r rune) bool { return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') }
func isASCIIUpper(r rune) bool  { return r >= 'A' && r <= 'Z' }

// --------------------------------------------------------------- str helpers

func upper(s string) string { return strings.Map(unicode.ToUpper, s) }
func lower(s string) string { return strings.Map(unicode.ToLower, s) }

// Python str.capitalize(): first char title-cased, the rest lower-cased.
func capitalize(s string) string {
	if s == "" {
		return s
	}
	r := []rune(s)
	return string(unicode.ToTitle(r[0])) + lower(string(r[1:]))
}

// foldEq compares runes the way Python's re.IGNORECASE does (simple folding).
func foldEq(a []rune, w string) bool {
	return strings.EqualFold(string(a), w)
}

// ---------------------------------------------------------------- small words

// SMALL alternation in regex order; `v\.?` and `vs\.?` are greedy, so the
// dotted form is tried first.
var smallAlts = []string{"a", "an", "and", "as", "at", "but", "by", "en", "for",
	"if", "in", "of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs"}

// ^(SMALL)$ with re.I
func isSmallWord(r []rune) bool {
	for _, w := range smallAlts {
		if len(r) == len([]rune(w)) && foldEq(r, w) {
			return true
		}
	}
	return false
}

// \b at position i of r (Unicode word chars).
func boundary(r []rune, i int) bool {
	left := i > 0 && isWord(r[i-1])
	right := i < len(r) && isWord(r[i])
	return left != right
}

// ------------------------------------------------------------- word patterns

// UC_INITIALS = ^(?:[A-Z]\.|[A-Z]\.[A-Z])+$
func ucInitials(r []rune) bool {
	n := len(r)
	if n == 0 {
		return false
	}
	reach := make([]bool, n+1)
	reach[0] = true
	for i := 0; i < n; i++ {
		if !reach[i] {
			continue
		}
		if i+1 < n && isASCIIUpper(r[i]) && r[i+1] == '.' {
			reach[i+2] = true
			if i+2 < n && isASCIIUpper(r[i+2]) {
				reach[i+3] = true
			}
		}
	}
	return reach[n]
}

// APOS_SECOND = ^[dol]['‘][\w]+(?:['s]{2})?$  (re.I)
func aposSecond(r []rune) bool {
	if len(r) < 3 {
		return false
	}
	if !foldEq(r[:1], "d") && !foldEq(r[:1], "o") && !foldEq(r[:1], "l") {
		return false
	}
	if r[1] != '\'' && r[1] != '‘' {
		return false
	}
	rest := r[2:]
	allWord := func(s []rune) bool {
		if len(s) == 0 {
			return false
		}
		for _, c := range s {
			if !isWord(c) {
				return false
			}
		}
		return true
	}
	if allWord(rest) {
		return true
	}
	tail := func(c rune) bool { return c == '\'' || foldEq([]rune{c}, "s") }
	m := len(rest)
	return m >= 3 && allWord(rest[:m-2]) && tail(rest[m-2]) && tail(rest[m-1])
}

// MAC_MC = ^([Mm]c|MC)(\w.+)
func macMc(r []rune) (string, string, bool) {
	if len(r) < 4 {
		return "", "", false
	}
	p := string(r[:2])
	if p != "Mc" && p != "mc" && p != "MC" {
		return "", "", false
	}
	if !isWord(r[2]) {
		return "", "", false
	}
	for _, c := range r[3:] {
		if c == '\n' {
			return "", "", false
		}
	}
	return p, string(r[2:]), true
}

// MR_MRS_MS_DR = ^((m((rs?)|s))|Dr)$  (re.I)
func mrMrsMsDr(r []rune) bool {
	for _, w := range []string{"mr", "mrs", "ms", "dr"} {
		if len(r) == len(w) && foldEq(r, w) {
			return true
		}
	}
	return false
}

// INLINE_PERIOD = [\w][.][\w]  (search)
func inlinePeriod(r []rune) bool {
	for i := 0; i+2 < len(r); i++ {
		if isWord(r[i]) && r[i+1] == '.' && isWord(r[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE = [PUNCT]*?[a-zA-Z]+[A-Z]+?  (match at start)
func ucElsewhere(r []rune) bool {
	k := 0
	for k < len(r) && isPunct(r[k]) {
		k++
	}
	if k >= len(r) || !isASCIILetter(r[k]) {
		return false
	}
	for j := k + 1; j < len(r) && isASCIILetter(r[j]); j++ {
		if isASCIIUpper(r[j]) {
			return true
		}
	}
	return false
}

// \A[bcdfghjklmnpqrstvwxz]+\Z  (re.I)
func allConsonants(r []rune) bool {
	if len(r) == 0 {
		return false
	}
	for _, c := range r {
		ok := false
		for _, k := range "bcdfghjklmnpqrstvwxz" {
			if foldEq([]rune{c}, string(k)) {
				ok = true
				break
			}
		}
		if !ok {
			return false
		}
	}
	return true
}

// CAPFIRST.sub(lambda m: m.group(0).upper(), word), CAPFIRST = ^[PUNCT]*?([\w])
func capFirst(word string) string {
	r := []rune(word)
	for k := 0; k < len(r); k++ {
		if isWord(r[k]) {
			return upper(string(r[:k+1])) + string(r[k+1:])
		}
		if !isPunct(r[k]) {
			break
		}
	}
	return word
}

// SMALL_FIRST.sub: ^([PUNCT]*)(SMALL)\b  (re.I) -> group1 + group2.capitalize()
func smallFirst(s string) string {
	r := []rune(s)
	k := 0
	for k < len(r) && isPunct(r[k]) {
		k++
	}
	for _, w := range smallAlts {
		lw := len([]rune(w))
		e := k + lw
		if e <= len(r) && foldEq(r[k:e], w) && boundary(r, e) {
			return string(r[:k]) + capitalize(string(r[k:e])) + string(r[e:])
		}
	}
	return s
}

// SMALL_LAST.sub: \b(SMALL)[PUNCT]?$  (re.I) -> group(0).capitalize()
func smallLast(s string) string {
	r := []rune(s)
	n := len(r)
	for i := 0; i < n; i++ {
		if !boundary(r, i) {
			continue
		}
		for _, w := range smallAlts {
			e := i + len([]rune(w))
			if e > n || !foldEq(r[i:e], w) {
				continue
			}
			if rem := n - e; rem == 0 || (rem == 1 && isPunct(r[n-1])) {
				return string(r[:i]) + capitalize(string(r[i:]))
			}
		}
	}
	return s
}

// SUBPHRASE.sub: ([:.;?!\-–‒—―][ ])(SMALL)  (case-sensitive) -> g1 + g2.capitalize()
func subphrase(s string) string {
	r := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(r) {
		if i+2 < len(r) && isSubPunct(r[i]) && r[i+1] == ' ' {
			for _, w := range smallAlts {
				wr := []rune(w)
				e := i + 2 + len(wr)
				if e <= len(r) && string(r[i+2:e]) == w {
					b.WriteString(string(r[i : i+2]))
					b.WriteString(capitalize(w))
					i = e
					goto next
				}
			}
		}
		b.WriteRune(r[i])
		i++
	next:
	}
	return b.String()
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	}
	return false
}

// ------------------------------------------------------------------ titlecase

func titlecase(text string, smallFirstLast bool) string {
	// regex.split('[\r\n]+', text)
	var lines []string
	cur := []rune{}
	r := []rune(text)
	for i := 0; i < len(r); {
		if r[i] == '\r' || r[i] == '\n' {
			lines = append(lines, string(cur))
			cur = []rune{}
			for i < len(r) && (r[i] == '\r' || r[i] == '\n') {
				i++
			}
			continue
		}
		cur = append(cur, r[i])
		i++
	}
	lines = append(lines, string(cur))

	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, titlecaseLine(line, smallFirstLast))
	}
	return strings.Join(processed, "\n")
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := upper(line) == line

	// regex.split(r'(\s)', line)
	var words, spaces []string
	var cur []rune
	for _, c := range line {
		if isSpace(c) {
			words = append(words, string(cur))
			spaces = append(spaces, string(c))
			cur = cur[:0:0]
		} else {
			cur = append(cur, c)
		}
	}
	words = append(words, string(cur))

	tc := make([]string, 0, len(words))
	for _, word := range words {
		tc = append(tc, titlecaseWord(word, allCaps))
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
	return subphrase(b.String())
}

func titlecaseWord(word string, allCaps bool) string {
	r := []rune(word)

	if allCaps && ucInitials(r) {
		return word
	}

	if aposSecond(r) {
		var first string
		if strings.ContainsRune("aeiouAEIOU", r[0]) {
			first = upper(string(r[0]))
		} else {
			first = lower(string(r[0]))
		}
		return first + string(r[1]) + upper(string(r[2])) + string(r[3:])
	}

	if p, rest, ok := macMc(r); ok {
		return capitalize(p) + titlecase(rest, true)
	}

	if mrMrsMsDr(r) {
		return upper(string(r[0])) + string(r[1:])
	}

	if inlinePeriod(r) || (!allCaps && ucElsewhere(r)) {
		return word
	}

	if isSmallWord(r) {
		return lower(word)
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
		word = lower(word)
		r = []rune(word)
	}

	if allConsonants(r) && len(r) > 2 {
		return upper(word)
	}

	return capFirst(word)
}

// ----------------------------------------------------------------------- main

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<16)
	out := bufio.NewWriterSize(os.Stdout, 1<<16)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			out.WriteString(titlecase(line, true))
			out.WriteByte('\n')
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			os.Exit(1)
		}
	}
}
GOEOF

# The Python implementation is replaced, not kept alongside.
find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -type d -name '__pycache__' -prune -exec rm -rf {} +
rmdir /workspace/repo/titlecase 2>/dev/null || true

gofmt -l . | (! grep .) || { echo "gofmt differences" >&2; exit 1; }
go vet ./...
go build ./...
rm -f titlecase   # binary written by `go build ./...`; not part of the answer
echo "solve.sh: Go port written and built"
