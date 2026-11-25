#!/bin/bash
# Oracle: a Go port of python-titlecase, written with plain rune-level code
# (no look-ahead / look-behind / back-references anywhere).
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'GOMOD'
module titlecase

go 1.23
GOMOD

cat > main.go <<'GOSRC'
// Go port of python-titlecase (titlecase/__init__.py, v2.4.1, `regex` module flavour).
// Reads one title per line from stdin and prints the titlecased line.
// Go's regexp has no look-around / back-references, so every Python regex is
// re-implemented below as plain rune-level code.
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

// PUNCT from the Python source.
const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// SMALL words in the exact alternation order of the Python regex.
// optDot marks the alternatives written `v\.?` and `vs\.?`.
type alt struct {
	text   string
	optDot bool
}

var smallAlts = []alt{
	{"a", false}, {"an", false}, {"and", false}, {"as", false}, {"at", false},
	{"but", false}, {"by", false}, {"en", false}, {"for", false}, {"if", false},
	{"in", false}, {"of", false}, {"on", false}, {"or", false}, {"the", false},
	{"to", false}, {"v", true}, {"via", false}, {"vs", true},
}

var smallWordSet = map[string]bool{}

func init() {
	for _, a := range smallAlts {
		smallWordSet[a.text] = true
		if a.optDot {
			smallWordSet[a.text+"."] = true
		}
	}
}

func isPunct(r rune) bool  { return strings.ContainsRune(punctChars, r) }
func isLetter(r rune) bool { return unicode.IsLetter(r) }
func isWordRune(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.IsMark(r) || r == '_' || unicode.Is(unicode.Pc, r)
}

func asciiFold(r rune) rune {
	if r >= 'A' && r <= 'Z' {
		return r + 32
	}
	return r
}

// \b
func boundaryAt(rs []rune, i int) bool {
	left := i > 0 && isWordRune(rs[i-1])
	right := i < len(rs) && isWordRune(rs[i])
	return left != right
}

// matches alt text at position p (optionally ASCII case-insensitive)
func hasAt(rs []rune, p int, text string, fold bool) bool {
	n := len(text)
	if p+n > len(rs) {
		return false
	}
	for i := 0; i < n; i++ {
		c := rs[p+i]
		if fold {
			c = asciiFold(c)
		}
		if c != rune(text[i]) {
			return false
		}
	}
	return true
}

// str.capitalize(): first char upper, rest lower.
func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	return strings.ToUpper(string(rs[0])) + strings.ToLower(string(rs[1:]))
}

// ---- SMALL_FIRST: ^([PUNCT]*)(SMALL)\b  (re.I) ----
func smallFirst(w string) string {
	rs := []rune(w)
	p := 0
	for p < len(rs) && isPunct(rs[p]) {
		p++
	}
	for _, a := range smallAlts {
		if !hasAt(rs, p, a.text, true) {
			continue
		}
		end := p + len(a.text)
		var ends []int
		if a.optDot && end < len(rs) && rs[end] == '.' {
			ends = append(ends, end+1)
		}
		ends = append(ends, end)
		for _, e := range ends {
			if boundaryAt(rs, e) {
				return string(rs[:p]) + pyCapitalize(string(rs[p:e])) + string(rs[e:])
			}
		}
	}
	return w
}

// ---- SMALL_LAST: \b(SMALL)[PUNCT]?$  (re.I), sub with group(0).capitalize() ----
func smallLastSuffixOK(s []rune) bool {
	for _, a := range smallAlts {
		if !hasAt(s, 0, a.text, true) {
			continue
		}
		n := len(a.text)
		rems := []int{len(s) - n}
		if a.optDot && n < len(s) && s[n] == '.' {
			rems = append(rems, len(s)-n-1)
		}
		for _, rem := range rems {
			if rem == 0 || (rem == 1 && isPunct(s[len(s)-1])) {
				return true
			}
		}
	}
	return false
}

func smallLast(w string) string {
	rs := []rune(w)
	for i := 0; i < len(rs); i++ {
		if !boundaryAt(rs, i) {
			continue
		}
		if smallLastSuffixOK(rs[i:]) {
			return string(rs[:i]) + pyCapitalize(string(rs[i:]))
		}
	}
	return w
}

// ---- SUBPHRASE: ([:.;?!\-–‒—―][ ])(SMALL)  (case-sensitive, no \b) ----
func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	}
	return false
}

func subphrase(s string) string {
	rs := []rune(s)
	out := make([]rune, 0, len(rs))
	i := 0
	for i < len(rs) {
		if isSubPunct(rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			matched := false
			for _, a := range smallAlts {
				if !hasAt(rs, i+2, a.text, false) {
					continue
				}
				e := i + 2 + len(a.text)
				if a.optDot && e < len(rs) && rs[e] == '.' {
					e++
				}
				out = append(out, rs[i], rs[i+1])
				out = append(out, []rune(pyCapitalize(string(rs[i+2:e])))...)
				i = e
				matched = true
				break
			}
			if matched {
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

// ---- word-level predicates ----

// SMALL_WORDS: ^(SMALL)$  (re.I)
func isSmallWord(rs []rune) bool {
	b := make([]rune, len(rs))
	for i, r := range rs {
		b[i] = asciiFold(r)
	}
	return smallWordSet[string(b)]
}

// MR_MRS_MS_DR: ^((m((rs?)|s))|Dr)$  (re.I)
func isMrMrsMsDr(rs []rune) bool {
	b := make([]rune, len(rs))
	for i, r := range rs {
		b[i] = asciiFold(r)
	}
	switch string(b) {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

// MAC_MC: ^([Mm]c|MC)(\w.+)
func isMacMc(rs []rune) bool {
	if len(rs) < 4 {
		return false
	}
	ok := (rs[0] == 'M' && rs[1] == 'c') || (rs[0] == 'm' && rs[1] == 'c') || (rs[0] == 'M' && rs[1] == 'C')
	return ok && isWordRune(rs[2])
}

// INLINE_PERIOD: [\p{Letter}][.][\p{Letter}]  (search)
func hasInlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if isLetter(rs[i]) && rs[i+1] == '.' && isLetter(rs[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE: [PUNCT]*?[\p{Letter}]+[\p{Uppercase_Letter}]+?  (match, anchored at start)
func hasUcElsewhere(rs []rune) bool {
	k := 0
	for k < len(rs) && isPunct(rs[k]) {
		k++
	}
	if k >= len(rs) || !isLetter(rs[k]) {
		return false
	}
	e := k
	for e < len(rs) && isLetter(rs[e]) {
		e++
	}
	for j := k + 1; j < e; j++ {
		if unicode.IsUpper(rs[j]) {
			return true
		}
	}
	return false
}

// UC_INITIALS: ^(?:U\.|U\.U)+$
func isUcInitials(rs []rune) bool {
	n := len(rs)
	if n == 0 {
		return false
	}
	memo := make([]int8, n+1) // 0 unknown, 1 yes, 2 no
	var can func(i int) bool
	can = func(i int) bool {
		if i == n {
			return true
		}
		if memo[i] != 0 {
			return memo[i] == 1
		}
		res := false
		if unicode.IsUpper(rs[i]) && i+1 < n && rs[i+1] == '.' {
			if can(i + 2) { // U.
				res = true
			} else if i+2 < n && unicode.IsUpper(rs[i+2]) && can(i+3) { // U.U
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
	return can(0)
}

// APOS_SECOND: ^[dol]['‘][\p{Letter}]+(?:['s]{2})?$  (re.I)
func isAposSecond(rs []rune) bool {
	if len(rs) < 3 {
		return false
	}
	f := asciiFold(rs[0])
	if f != 'd' && f != 'o' && f != 'l' {
		return false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return false
	}
	rest := rs[2:]
	allLetters := func(x []rune) bool {
		if len(x) == 0 {
			return false
		}
		for _, r := range x {
			if !isLetter(r) {
				return false
			}
		}
		return true
	}
	isX := func(r rune) bool { return r == '\'' || r == 's' || r == 'S' }
	if allLetters(rest) {
		return true
	}
	n := len(rest)
	return n >= 3 && allLetters(rest[:n-2]) && isX(rest[n-2]) && isX(rest[n-1])
}

const consonants = "bcdfghjklmnpqrstvwxz"

func isAllConsonants(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if r > unicode.MaxASCII || !strings.ContainsRune(consonants, asciiFold(r)) {
			return false
		}
	}
	return true
}

// CAPFIRST: ^[PUNCT]*?([\p{Letter}])  -> upper() of the match
func capFirst(w string) string {
	rs := []rune(w)
	k := 0
	for k < len(rs) && isPunct(rs[k]) {
		k++
	}
	if k < len(rs) && isLetter(rs[k]) {
		return string(rs[:k]) + strings.ToUpper(string(rs[k])) + string(rs[k+1:])
	}
	return w
}

// regex.split('[\r\n]+', text)
func splitNewlines(text string) []string {
	var parts []string
	var cur []rune
	inRun := false
	for _, r := range text {
		if r == '\r' || r == '\n' {
			if !inRun {
				parts = append(parts, string(cur))
				cur = cur[:0]
				inRun = true
			}
			continue
		}
		inRun = false
		cur = append(cur, r)
	}
	parts = append(parts, string(cur))
	return parts
}

// regex.split(r'(\s)', line) -> words, spaces
func splitSpaces(line string) ([]string, []string) {
	var words, spaces []string
	var cur []rune
	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, string(cur))
			spaces = append(spaces, string(r))
			cur = cur[:0]
			continue
		}
		cur = append(cur, r)
	}
	words = append(words, string(cur))
	return words, spaces
}

func convertWord(word string, allCaps bool) string {
	rs := []rune(word)

	if allCaps && isUcInitials(rs) {
		return word
	}
	if isAposSecond(rs) {
		first := rs[0]
		var f string
		if strings.ContainsRune("aeiouAEIOU", first) {
			f = strings.ToUpper(string(first))
		} else {
			f = strings.ToLower(string(first))
		}
		return f + string(rs[1]) + strings.ToUpper(string(rs[2])) + string(rs[3:])
	}
	if isMacMc(rs) {
		return "Mc" + titlecase(string(rs[2:]), true)
	}
	if isMrMrsMsDr(rs) {
		return strings.ToUpper(string(rs[0])) + string(rs[1:])
	}
	if hasInlinePeriod(rs) || (!allCaps && hasUcElsewhere(rs)) {
		return word
	}
	if isSmallWord(rs) {
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
		rs = []rune(word)
	}
	if len(rs) > 2 && isAllConsonants(rs) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitSpaces(line)
	tc := make([]string, len(words))
	for i, w := range words {
		tc[i] = convertWord(w, allCaps)
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

func titlecase(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
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
		s, err := in.ReadString('\n')
		if len(s) > 0 {
			s = strings.TrimSuffix(s, "\n")
			out.WriteString(titlecase(s, true))
			out.WriteByte('\n')
		}
		if err != nil {
			break
		}
	}
}
GOSRC

# The Python machine is gone; only the Go twin is left.
find /workspace/repo -type f -name '*.py' -delete
go build -o /dev/null ./...
