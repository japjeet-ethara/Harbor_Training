#!/bin/bash
# Reference solution (oracle): write a Go port of python-titlecase into
# /workspace/repo (go.mod + main.go, standard library only), then delete every
# .py file. Python regex look-arounds etc. are re-implemented as hand-written
# character checks (Go's regexp has none of them).
set -euo pipefail
REPO="${REPO:-/workspace/repo}"
cd "$REPO"

cat > go.mod <<'GOMOD'
module titlecase-go

go 1.23
GOMOD

cat > main.go <<'GOSRC'
// Command titlecase is a Go port of python-titlecase 2.4.1 (stdlib `re`
// fallback branch). It reads one title per line from stdin and writes the
// titlecased line to stdout, matching Python's titlecase(line) byte for byte.
//
// Go's regexp has no look-around or back-references and differs from Python's
// re (Unicode \w/\s/\b, case folding, leftmost-alternative priority), so every
// pattern from the Python module is re-implemented here as hand-written
// character checks that reproduce the backtracking result exactly.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

// PUNCT from the Python source: !"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~
const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// SUBPHRASE punctuation: [:.;?!\-–‒—―]
const subphraseChars = ":.;?!-–‒—―"

// SMALL alternation in regex order. `v\.?` and `vs\.?` are greedy, so the
// dotted form is tried before the bare one.
var smallAlts = []string{"a", "an", "and", "as", "at", "but", "by", "en",
	"for", "if", "in", "of", "on", "or", "the", "to", "v.", "v", "via",
	"vs.", "vs"}

var punctSet = runeSet(punctChars)
var subphraseSet = runeSet(subphraseChars)
var consonantSet = runeSet("bcdfghjklmnpqrstvwxz")

func runeSet(s string) map[rune]bool {
	m := map[rune]bool{}
	for _, r := range s {
		m[r] = true
	}
	return m
}

// isWord mirrors Python re's Unicode \w: str.isalnum() or '_'.
func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

// isSpace mirrors Python re's Unicode \s (str.isspace()).
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

func isPunct(r rune) bool { return punctSet[r] }

func isASCIIUpper(r rune) bool { return r >= 'A' && r <= 'Z' }

func isASCIILetter(r rune) bool { return isASCIIUpper(r) || (r >= 'a' && r <= 'z') }

// foldEq reports whether r matches the lower-case ASCII letter t under
// Python's re.IGNORECASE (simple lower-case plus sre's extra equivalences).
func foldEq(r rune, t rune) bool {
	if r == t {
		return true
	}
	l := unicode.ToLower(r)
	if l == t {
		return true
	}
	switch t {
	case 'i':
		return r == 'ı'
	case 's':
		return r == 'ſ'
	}
	return false
}

// foldAt reports whether rs[k:] starts with lit, case-insensitively.
func foldAt(rs []rune, k int, lit string) bool {
	i := k
	for _, t := range lit {
		if i >= len(rs) {
			return false
		}
		if t >= 'a' && t <= 'z' {
			if !foldEq(rs[i], t) {
				return false
			}
		} else if rs[i] != t {
			return false
		}
		i++
	}
	return true
}

func foldEquals(rs []rune, lit string) bool {
	return len(rs) == len([]rune(lit)) && foldAt(rs, 0, lit)
}

func isSmallWord(rs []rune) bool {
	for _, a := range smallAlts {
		if foldEquals(rs, a) {
			return true
		}
	}
	return false
}

func boundary(rs []rune, p int) bool {
	left := p > 0 && p-1 < len(rs) && isWord(rs[p-1])
	right := p < len(rs) && isWord(rs[p])
	return left != right
}

func upper(rs []rune) []rune {
	out := make([]rune, len(rs))
	for i, r := range rs {
		out[i] = unicode.ToUpper(r)
	}
	return out
}

func lower(rs []rune) []rune {
	out := make([]rune, len(rs))
	for i, r := range rs {
		out[i] = unicode.ToLower(r)
	}
	return out
}

// capitalize mirrors str.capitalize(): first char title-cased, rest lower.
func capitalize(rs []rune) []rune {
	if len(rs) == 0 {
		return []rune{}
	}
	out := lower(rs)
	out[0] = unicode.ToTitle(rs[0])
	return out
}

func cat(parts ...[]rune) []rune {
	var out []rune
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}

// ^(?:[A-Z]\.|[A-Z]\.[A-Z])+$
func ucInitials(w []rune) bool {
	var f func(i int) bool
	f = func(i int) bool {
		if i == len(w) {
			return true
		}
		if i+1 < len(w) && isASCIIUpper(w[i]) && w[i+1] == '.' {
			if f(i + 2) {
				return true
			}
			if i+2 < len(w) && isASCIIUpper(w[i+2]) && f(i+3) {
				return true
			}
		}
		return false
	}
	return len(w) > 0 && f(0)
}

// ^[dol]['‘][\w]+(?:['s]{2})?$  (re.I)
func aposSecond(w []rune) bool {
	if len(w) < 3 {
		return false
	}
	if !(foldEq(w[0], 'd') || foldEq(w[0], 'o') || foldEq(w[0], 'l')) {
		return false
	}
	if w[1] != '\'' && w[1] != '‘' {
		return false
	}
	rest := w[2:]
	allWord := func(rs []rune) bool {
		for _, r := range rs {
			if !isWord(r) {
				return false
			}
		}
		return len(rs) > 0
	}
	if allWord(rest) {
		return true
	}
	isQS := func(r rune) bool { return r == '\'' || foldEq(r, 's') }
	n := len(rest)
	return n >= 3 && isQS(rest[n-1]) && isQS(rest[n-2]) && allWord(rest[:n-2])
}

// ^([Mm]c|MC)(\w.+)  -> returns (group1, group2, ok)
func macMc(w []rune) ([]rune, []rune, bool) {
	if len(w) < 4 {
		return nil, nil, false
	}
	ok := ((w[0] == 'M' || w[0] == 'm') && w[1] == 'c') || (w[0] == 'M' && w[1] == 'C')
	if !ok || !isWord(w[2]) {
		return nil, nil, false
	}
	for _, r := range w[3:] {
		if r == '\n' {
			return nil, nil, false
		}
	}
	return w[:2], w[2:], true
}

// ^((m((rs?)|s))|Dr)$  (re.I)
func mrMrsMsDr(w []rune) bool {
	return foldEquals(w, "mr") || foldEquals(w, "mrs") || foldEquals(w, "ms") || foldEquals(w, "dr")
}

// [\w][.][\w] searched anywhere
func inlinePeriod(w []rune) bool {
	for i := 0; i+2 < len(w); i++ {
		if isWord(w[i]) && w[i+1] == '.' && isWord(w[i+2]) {
			return true
		}
	}
	return false
}

// ^[PUNCT]*?[a-zA-Z]+[A-Z]+?   (match at start)
func ucElsewhere(w []rune) bool {
	k := 0
	for k < len(w) && isPunct(w[k]) {
		k++
	}
	j := k
	for j < len(w) && isASCIILetter(w[j]) {
		j++
	}
	for t := k + 1; t < j; t++ {
		if isASCIIUpper(w[t]) {
			return true
		}
	}
	return false
}

// \A[bcdfghjklmnpqrstvwxz]+\Z  (re.I)
func allConsonants(w []rune) bool {
	if len(w) == 0 {
		return false
	}
	for _, r := range w {
		l := unicode.ToLower(r)
		if r == 'ſ' {
			l = 's'
		}
		if !consonantSet[l] {
			return false
		}
	}
	return true
}

// CAPFIRST.sub(upper, word) with ^[PUNCT]*?([\w])
func capFirst(w []rune) []rune {
	out := append([]rune{}, w...)
	for i := 0; i < len(w); i++ {
		if isWord(w[i]) {
			out[i] = unicode.ToUpper(w[i])
			return out
		}
		if !isPunct(w[i]) {
			return out
		}
	}
	return out
}

// SMALL_FIRST: ^([PUNCT]*)(SMALL)\b  (re.I) -> group1 + capitalize(group2)
func smallFirst(w []rune) []rune {
	k := 0
	for k < len(w) && isPunct(w[k]) {
		k++
	}
	for _, a := range smallAlts {
		n := len([]rune(a))
		if foldAt(w, k, a) && boundary(w, k+n) {
			return cat(w[:k], capitalize(w[k:k+n]), w[k+n:])
		}
	}
	return w
}

// SMALL_LAST: \b(SMALL)[PUNCT]?$  (re.I) -> capitalize(whole match)
func smallLast(w []rune) []rune {
	for p := 0; p < len(w); p++ {
		if !boundary(w, p) {
			continue
		}
		s := w[p:]
		match := isSmallWord(s)
		if !match && len(s) >= 2 && isPunct(s[len(s)-1]) {
			match = isSmallWord(s[:len(s)-1])
		}
		if match {
			return cat(w[:p], capitalize(s))
		}
	}
	return w
}

// SUBPHRASE: ([:.;?!\-–‒—―][ ])(SMALL)  case-sensitive, global, non-overlapping
func subphrase(s []rune) []rune {
	var out []rune
	i := 0
	for i < len(s) {
		if subphraseSet[s[i]] && i+2 < len(s) && s[i+1] == ' ' {
			for _, a := range smallAlts {
				ar := []rune(a)
				if i+2+len(ar) <= len(s) && string(s[i+2:i+2+len(ar)]) == a {
					out = append(out, s[i], s[i+1])
					out = append(out, capitalize(ar)...)
					i += 2 + len(ar)
					goto next
				}
			}
		}
		out = append(out, s[i])
		i++
	next:
	}
	return out
}

func isAllCaps(rs []rune) bool {
	for _, r := range rs {
		if unicode.ToUpper(r) != r {
			return false
		}
	}
	return true
}

func splitJoin(w []rune, sep rune) []rune {
	parts := strings.Split(string(w), string(sep))
	for i, p := range parts {
		parts[i] = titlecase(p, false)
	}
	return []rune(strings.Join(parts, string(sep)))
}

func processWord(w []rune, allCaps bool) []rune {
	if allCaps && ucInitials(w) {
		return w
	}
	if aposSecond(w) {
		first := unicode.ToUpper(w[0])
		if !strings.ContainsRune("aeiouAEIOU", w[0]) {
			first = unicode.ToLower(w[0])
		}
		return cat([]rune{first, w[1], unicode.ToUpper(w[2])}, w[3:])
	}
	if g1, g2, ok := macMc(w); ok {
		return cat(capitalize(g1), []rune(titlecase(string(g2), true)))
	}
	if mrMrsMsDr(w) {
		return cat([]rune{unicode.ToUpper(w[0])}, w[1:])
	}
	if inlinePeriod(w) || (!allCaps && ucElsewhere(w)) {
		return w
	}
	if isSmallWord(w) {
		return lower(w)
	}
	ws := string(w)
	if strings.Contains(ws, "/") && !strings.Contains(ws, "//") {
		return splitJoin(w, '/')
	}
	if strings.Contains(ws, "-") {
		return splitJoin(w, '-')
	}
	if allCaps {
		w = lower(w)
	}
	if allConsonants(w) && len(w) > 2 {
		return upper(w)
	}
	return capFirst(w)
}

func processLine(line []rune, smallFirstLast bool) string {
	allCaps := isAllCaps(line)
	// re.split(r'(\s)', line)
	var words [][]rune
	var spaces []rune
	start := 0
	for i, r := range line {
		if isSpace(r) {
			words = append(words, line[start:i])
			spaces = append(spaces, r)
			start = i + 1
		}
	}
	words = append(words, line[start:])

	tc := make([][]rune, len(words))
	for i, w := range words {
		tc[i] = processWord(w, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = smallFirst(tc[0])
		tc[len(tc)-1] = smallLast(tc[len(tc)-1])
	}
	var joined []rune
	for i, w := range tc {
		joined = append(joined, w...)
		if i < len(spaces) {
			joined = append(joined, spaces[i])
		}
	}
	return string(subphrase(joined))
}

// titlecase mirrors the Python function: split on runs of \r/\n, process
// each line, join with \n.
func titlecase(text string, smallFirstLast bool) string {
	rs := []rune(text)
	var lines [][]rune
	start := 0
	i := 0
	for i < len(rs) {
		if rs[i] == '\r' || rs[i] == '\n' {
			lines = append(lines, rs[start:i])
			for i < len(rs) && (rs[i] == '\r' || rs[i] == '\n') {
				i++
			}
			start = i
			continue
		}
		i++
	}
	lines = append(lines, rs[start:])
	out := make([]string, len(lines))
	for j, l := range lines {
		out[j] = processLine(l, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	text := string(data)
	if text == "" {
		return
	}
	text = strings.TrimSuffix(text, "\n")
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for _, line := range strings.Split(text, "\n") {
		w.WriteString(titlecase(line, true))
		w.WriteString("\n")
	}
}
GOSRC

gofmt -l . >/dev/null 2>&1 || true
find "$REPO" -name '*.py' -type f -delete
find "$REPO" -name '__pycache__' -type d -prune -exec rm -rf {} +

GOTOOLCHAIN=local GOPROXY=off go build ./...
rm -f "$REPO/titlecase-go"   # binary written by go build ./... (single main package)
echo "titlecase Go port written to $REPO"
