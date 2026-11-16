#!/bin/bash
# Oracle solution for titlecase-go.
# Writes a Go port of python-titlecase (standard library only) into
# /workspace/repo, then deletes every .py file.
set -euo pipefail
export PATH="$PATH:/usr/local/go/bin"
cd /workspace/repo

cat > go.mod <<'GO_SOURCE_EOF'
module titlecase

go 1.23
GO_SOURCE_EOF

cat > main.go <<'GO_SOURCE_EOF'
// Command titlecase is a Go port of python-titlecase 2.4.1 (titlecase/__init__.py).
//
// It reads lines from stdin and prints titlecase(line) for each, matching the
// original Python byte for byte: default arguments, Python 3 with the stdlib
// `re` module (the optional `regex` module NOT installed).
//
// Go's regexp has no look-around/back-references and its \w, \s, \b are ASCII
// only, so every Python regex is re-implemented as plain character checks,
// using Python's Unicode definitions of \w, \s, \b and IGNORECASE.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Stderr.WriteString("titlecase: reading stdin: " + err.Error() + "\n")
		os.Exit(1)
	}
	if len(data) == 0 {
		return
	}
	lines := strings.Split(string(data), "\n")
	if lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1] // input ended with "\n"
	}
	w := bufio.NewWriterSize(os.Stdout, 1<<16)
	for _, line := range lines {
		w.WriteString(Titlecase(line))
		w.WriteByte('\n')
	}
	if err := w.Flush(); err != nil {
		os.Exit(1)
	}
}

// Titlecase is titlecase(text) with default arguments.
func Titlecase(text string) string { return titlecase(text, true) }

// ---------------------------------------------------------------------------
// Character classes (Python `re` semantics)

// PUNCT = r"""!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~"""  (note: no ” or ’)
const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[]_{|}~" + "`" + "\x5c"

// SUBPHRASE separator class: [:.;?!\-–‒—―]
const subphraseSeps = ":.;?!-–‒—―"

// CONSONANTS (lowercase ASCII minus a e i o u y)
const consonantChars = "bcdfghjklmnpqrstvwxz"

func isPunct(r rune) bool { return strings.ContainsRune(punctChars, r) }

func inRanges(r rune, rs [][2]rune) bool {
	for _, x := range rs {
		if r >= x[0] && r <= x[1] {
			return true
		}
	}
	return false
}

// isWord is Python's \w for str patterns: str.isalnum() or '_'.
func isWord(r rune) bool {
	if r == '_' {
		return true
	}
	if unicode.IsLetter(r) || unicode.IsNumber(r) {
		return !inRanges(r, pyWordDel)
	}
	return inRanges(r, pyWordAdd)
}

// isSpace is Python's \s for str patterns: str.isspace().
func isSpace(r rune) bool { return inRanges(r, pySpace) }

func isUpperASCII(r rune) bool { return r >= 'A' && r <= 'Z' }

func isLetterASCII(r rune) bool { return (r >= 'a' && r <= 'z') || isUpperASCII(r) }

// boundary is Python's \b at position p.
func boundary(rs []rune, p int) bool {
	if len(rs) == 0 {
		return false
	}
	before := p > 0 && isWord(rs[p-1])
	after := p < len(rs) && isWord(rs[p])
	return before != after
}

// ---------------------------------------------------------------------------
// Python str.upper / str.lower / str.capitalize (full Unicode case mapping)

func upperRune(r rune) string {
	if s, ok := pyUpperSpecial[r]; ok {
		return s
	}
	return string(unicode.ToUpper(r))
}

func lowerRune(r rune) string {
	if s, ok := pyLowerSpecial[r]; ok {
		return s
	}
	return string(unicode.ToLower(r))
}

func titleRune(r rune) string {
	if s, ok := pyTitleSpecial[r]; ok {
		return s
	}
	return string(unicode.ToTitle(r))
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(upperRune(r))
	}
	return b.String()
}

// lowerAt lowercases rs[i], applying Python's Final_Sigma rule to U+03A3.
func lowerAt(rs []rune, i int) string {
	if rs[i] == 0x3A3 {
		if finalSigma(rs, i) {
			return "ς"
		}
		return "σ"
	}
	return lowerRune(rs[i])
}

func pyLower(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := range rs {
		b.WriteString(lowerAt(rs, i))
	}
	return b.String()
}

// pyCapitalize: first character to titlecase, the rest to lowercase.
func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return ""
	}
	var b strings.Builder
	b.WriteString(titleRune(rs[0]))
	for i := 1; i < len(rs); i++ {
		b.WriteString(lowerAt(rs, i))
	}
	return b.String()
}

func cased(r rune) bool {
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r) ||
		unicode.Is(unicode.Other_Lowercase, r) || unicode.Is(unicode.Other_Uppercase, r)
}

func caseIgnorable(r rune) bool {
	switch r {
	case '\'', '.', ':', '^', '`', 0xB7, 0x387, 0x55F, 0x5F4, 0x2018, 0x2019,
		0x2024, 0x2027, 0xFE13, 0xFE52, 0xFE55, 0xFF07, 0xFF0E, 0xFF1A:
		return true
	}
	return unicode.In(r, unicode.Mn, unicode.Me, unicode.Cf, unicode.Lm, unicode.Sk)
}

// finalSigma: \p{cased}\p{case-ignorable}* U+03A3 !(\p{case-ignorable}*\p{cased})
func finalSigma(rs []rune, i int) bool {
	j := i - 1
	for j >= 0 && caseIgnorable(rs[j]) {
		j--
	}
	if j < 0 || !cased(rs[j]) {
		return false
	}
	k := i + 1
	for k < len(rs) && caseIgnorable(rs[k]) {
		k++
	}
	return k == len(rs) || !cased(rs[k])
}

// simpleLower is the single-character lowercase that Python's IGNORECASE uses.
func simpleLower(r rune) rune {
	for _, x := range lowerRune(r) {
		return x
	}
	return r
}

// foldEq: does input rune c match pattern letter p (lowercase ASCII) under
// re.IGNORECASE? Python compares the simple lowercase and adds the special
// equivalences i <-> ı (U+0131) and s <-> ſ (U+017F).
func foldEq(c, p rune) bool {
	lc := simpleLower(c)
	if c == p || lc == p {
		return true
	}
	switch p {
	case 'i':
		return lc == 0x131
	case 's':
		return lc == 0x17F
	}
	return false
}

// ---------------------------------------------------------------------------
// SMALL = r'a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?'
// Alternatives are tried in this order, like the regex engine does.

type smallAlt struct {
	word   string
	optDot bool // trailing \.?
}

var smallAlts = []smallAlt{
	{"a", false}, {"an", false}, {"and", false}, {"as", false}, {"at", false},
	{"but", false}, {"by", false}, {"en", false}, {"for", false}, {"if", false},
	{"in", false}, {"of", false}, {"on", false}, {"or", false}, {"the", false},
	{"to", false}, {"v", true}, {"via", false}, {"vs", true},
}

// altEnds returns the possible end positions of alternative a matched at pos,
// in the order the regex engine tries them (greedy \.? first).
func altEnds(rs []rune, pos int, a smallAlt, ignoreCase bool) []int {
	if pos+len(a.word) > len(rs) {
		return nil
	}
	for k, p := range a.word {
		c := rs[pos+k]
		if ignoreCase {
			if !foldEq(c, p) {
				return nil
			}
		} else if c != p {
			return nil
		}
	}
	end := pos + len(a.word)
	if a.optDot && end < len(rs) && rs[end] == '.' {
		return []int{end + 1, end}
	}
	return []int{end}
}

// SMALL_WORDS = ^(SMALL)$, IGNORECASE
func isSmallWord(rs []rune) bool {
	for _, a := range smallAlts {
		for _, e := range altEnds(rs, 0, a, true) {
			if e == len(rs) {
				return true
			}
		}
	}
	return false
}

// SMALL_FIRST = ^([PUNCT]*)(SMALL)\b, IGNORECASE; replaced by group1 + group2.capitalize()
func smallFirst(s string) string {
	rs := []rune(s)
	k := 0
	for k < len(rs) && isPunct(rs[k]) {
		k++
	}
	for _, a := range smallAlts {
		for _, e := range altEnds(rs, k, a, true) {
			if boundary(rs, e) {
				return string(rs[:k]) + pyCapitalize(string(rs[k:e])) + string(rs[e:])
			}
		}
	}
	return s
}

// SMALL_LAST = \b(SMALL)[PUNCT]?$, IGNORECASE (search); replaced by group0.capitalize()
func smallLast(s string) string {
	rs := []rune(s)
	n := len(rs)
	for p := 0; p <= n; p++ {
		if !boundary(rs, p) {
			continue
		}
		for _, a := range smallAlts {
			for _, e := range altEnds(rs, p, a, true) {
				if e == n || (e+1 == n && isPunct(rs[e])) {
					return string(rs[:p]) + pyCapitalize(string(rs[p:]))
				}
			}
		}
	}
	return s
}

// SUBPHRASE = ([:.;?!\-–‒—―][ ])(SMALL), case-sensitive, no \b;
// every match replaced by group1 + group2.capitalize()
func subphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := 0; i < len(rs); {
		if strings.ContainsRune(subphraseSeps, rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			if e := subphraseSmallEnd(rs, i+2); e >= 0 {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2 : e])))
				i = e
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

func subphraseSmallEnd(rs []rune, pos int) int {
	for _, a := range smallAlts {
		if ends := altEnds(rs, pos, a, false); len(ends) > 0 {
			return ends[0]
		}
	}
	return -1
}

// ---------------------------------------------------------------------------
// Per-word regexes (re fallback versions)

// UC_INITIALS = ^(?:[A-Z]\.|[A-Z]\.[A-Z])+$
func ucInitials(rs []rune) bool {
	n := len(rs)
	if n == 0 {
		return false
	}
	memo := make(map[int]bool)
	var from func(i int) bool
	from = func(i int) bool {
		if i == n {
			return true
		}
		if v, ok := memo[i]; ok {
			return v
		}
		ok := false
		if i+1 < n && isUpperASCII(rs[i]) && rs[i+1] == '.' {
			ok = from(i+2) || (i+2 < n && isUpperASCII(rs[i+2]) && from(i+3))
		}
		memo[i] = ok
		return ok
	}
	return from(0)
}

// APOS_SECOND = ^[dol]['‘][\w]+(?:['s]{2})?$, IGNORECASE
func aposSecond(rs []rune) bool {
	if len(rs) < 3 {
		return false
	}
	if !(foldEq(rs[0], 'd') || foldEq(rs[0], 'o') || foldEq(rs[0], 'l')) {
		return false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return false
	}
	rest := rs[2:]
	if allWord(rest) {
		return true
	}
	n := len(rest)
	isApS := func(r rune) bool { return r == '\'' || foldEq(r, 's') }
	return n >= 3 && isApS(rest[n-1]) && isApS(rest[n-2]) && allWord(rest[:n-2])
}

func allWord(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if !isWord(r) {
			return false
		}
	}
	return true
}

// MAC_MC = ^([Mm]c|MC)(\w.+)
func macMc(rs []rune) (string, string, bool) {
	if len(rs) < 4 {
		return "", "", false
	}
	prefix := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c'
	prefix = prefix || (rs[0] == 'M' && rs[1] == 'C')
	if !prefix || !isWord(rs[2]) {
		return "", "", false
	}
	for _, r := range rs[3:] {
		if r == '\n' {
			return "", "", false
		}
	}
	return string(rs[:2]), string(rs[2:]), true
}

// MR_MRS_MS_DR = ^((m((rs?)|s))|Dr)$, IGNORECASE
func mrMrsMsDr(rs []rune) bool {
	switch len(rs) {
	case 2:
		return (foldEq(rs[0], 'm') && (foldEq(rs[1], 'r') || foldEq(rs[1], 's'))) ||
			(foldEq(rs[0], 'd') && foldEq(rs[1], 'r'))
	case 3:
		return foldEq(rs[0], 'm') && foldEq(rs[1], 'r') && foldEq(rs[2], 's')
	}
	return false
}

// INLINE_PERIOD = [\w][.][\w] (search)
func inlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if isWord(rs[i]) && rs[i+1] == '.' && isWord(rs[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE = [PUNCT]*?[a-zA-Z]+[A-Z]+? (match at start)
func ucElsewhere(rs []rune) bool {
	k := 0
	for k < len(rs) && isPunct(rs[k]) {
		k++
	}
	for j := k; j < len(rs) && isLetterASCII(rs[j]); j++ {
		if j > k && isUpperASCII(rs[j]) {
			return true
		}
	}
	return false
}

// \A[CONSONANTS]+\Z, IGNORECASE
func allConsonants(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		lc := simpleLower(r)
		if !strings.ContainsRune(consonantChars, lc) && lc != 0x17F {
			return false
		}
	}
	return true
}

// CAPFIRST = ^[PUNCT]*?([\w]); replaced by group0.upper()
func capFirst(rs []rune) string {
	for k := 0; k < len(rs); k++ {
		if isWord(rs[k]) {
			return pyUpper(string(rs[:k+1])) + string(rs[k+1:])
		}
		if !isPunct(rs[k]) {
			break
		}
	}
	return string(rs)
}

// ---------------------------------------------------------------------------
// titlecase()

func titlecase(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
	for i, line := range lines {
		lines[i] = titlecaseLine(line, smallFirstLast)
	}
	return strings.Join(lines, "\n")
}

// splitNewlines is re.split('[\r\n]+', text).
func splitNewlines(s string) []string {
	var parts []string
	start := 0
	for i := 0; i < len(s); {
		if s[i] == '\r' || s[i] == '\n' {
			j := i
			for j < len(s) && (s[j] == '\r' || s[j] == '\n') {
				j++
			}
			parts = append(parts, s[start:i])
			start, i = j, j
			continue
		}
		i++
	}
	return append(parts, s[start:])
}

// splitSpaces is re.split(r'(\s)', line): words and the single separators.
func splitSpaces(line string) (words, spaces []string) {
	var cur strings.Builder
	for _, r := range line {
		if isSpace(r) {
			words = append(words, cur.String())
			spaces = append(spaces, string(r))
			cur.Reset()
		} else {
			cur.WriteRune(r)
		}
	}
	return append(words, cur.String()), spaces
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := pyUpper(line) == line
	words, spaces := splitSpaces(line)
	tc := make([]string, len(words))
	for i, w := range words {
		tc[i] = titlecaseWord(w, allCaps)
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
	rs := []rune(word)

	if allCaps && ucInitials(rs) {
		return word
	}

	if aposSecond(rs) {
		var first string
		if strings.ContainsRune("aeiouAEIOU", rs[0]) {
			first = upperRune(rs[0])
		} else {
			first = lowerRune(rs[0])
		}
		return first + string(rs[1]) + upperRune(rs[2]) + string(rs[3:])
	}

	if g1, g2, ok := macMc(rs); ok {
		return pyCapitalize(g1) + titlecase(g2, true)
	}

	if mrMrsMsDr(rs) {
		return upperRune(rs[0]) + string(rs[1:])
	}

	if inlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}

	if isSmallWord(rs) {
		return pyLower(word)
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
		word = pyLower(word)
		rs = []rune(word)
	}

	// A term with all consonants is an acronym, unless it is too short ("St").
	if allConsonants(rs) && len(rs) > 2 {
		return pyUpper(word)
	}

	return capFirst(rs)
}
GO_SOURCE_EOF

# Generated from Python 3.13 vs Go 1.23: only the Unicode case mappings and
# character classes where the two differ.
cat > tables.go <<'GO_SOURCE_EOF'
package main

// Generated: differences between Python 3.13 str methods / str.isalnum()
// and Go 1.23's unicode package. Everything else uses the unicode package.

var pyUpperSpecial = map[rune]string{0xDF: "SS", 0x149: "\U000002BCN", 0x1F0: "J\U0000030C", 0x390: "\U00000399\U00000308\U00000301", 0x3B0: "\U000003A5\U00000308\U00000301", 0x587: "\U00000535\U00000552", 0x1E96: "H\U00000331", 0x1E97: "T\U00000308", 0x1E98: "W\U0000030A", 0x1E99: "Y\U0000030A", 0x1E9A: "A\U000002BE", 0x1F50: "\U000003A5\U00000313", 0x1F52: "\U000003A5\U00000313\U00000300", 0x1F54: "\U000003A5\U00000313\U00000301", 0x1F56: "\U000003A5\U00000313\U00000342", 0x1F80: "\U00001F08\U00000399", 0x1F81: "\U00001F09\U00000399", 0x1F82: "\U00001F0A\U00000399", 0x1F83: "\U00001F0B\U00000399", 0x1F84: "\U00001F0C\U00000399", 0x1F85: "\U00001F0D\U00000399", 0x1F86: "\U00001F0E\U00000399", 0x1F87: "\U00001F0F\U00000399", 0x1F88: "\U00001F08\U00000399", 0x1F89: "\U00001F09\U00000399", 0x1F8A: "\U00001F0A\U00000399", 0x1F8B: "\U00001F0B\U00000399", 0x1F8C: "\U00001F0C\U00000399", 0x1F8D: "\U00001F0D\U00000399", 0x1F8E: "\U00001F0E\U00000399", 0x1F8F: "\U00001F0F\U00000399", 0x1F90: "\U00001F28\U00000399", 0x1F91: "\U00001F29\U00000399", 0x1F92: "\U00001F2A\U00000399", 0x1F93: "\U00001F2B\U00000399", 0x1F94: "\U00001F2C\U00000399", 0x1F95: "\U00001F2D\U00000399", 0x1F96: "\U00001F2E\U00000399", 0x1F97: "\U00001F2F\U00000399", 0x1F98: "\U00001F28\U00000399", 0x1F99: "\U00001F29\U00000399", 0x1F9A: "\U00001F2A\U00000399", 0x1F9B: "\U00001F2B\U00000399", 0x1F9C: "\U00001F2C\U00000399", 0x1F9D: "\U00001F2D\U00000399", 0x1F9E: "\U00001F2E\U00000399", 0x1F9F: "\U00001F2F\U00000399", 0x1FA0: "\U00001F68\U00000399", 0x1FA1: "\U00001F69\U00000399", 0x1FA2: "\U00001F6A\U00000399", 0x1FA3: "\U00001F6B\U00000399", 0x1FA4: "\U00001F6C\U00000399", 0x1FA5: "\U00001F6D\U00000399", 0x1FA6: "\U00001F6E\U00000399", 0x1FA7: "\U00001F6F\U00000399", 0x1FA8: "\U00001F68\U00000399", 0x1FA9: "\U00001F69\U00000399", 0x1FAA: "\U00001F6A\U00000399", 0x1FAB: "\U00001F6B\U00000399", 0x1FAC: "\U00001F6C\U00000399", 0x1FAD: "\U00001F6D\U00000399", 0x1FAE: "\U00001F6E\U00000399", 0x1FAF: "\U00001F6F\U00000399", 0x1FB2: "\U00001FBA\U00000399", 0x1FB3: "\U00000391\U00000399", 0x1FB4: "\U00000386\U00000399", 0x1FB6: "\U00000391\U00000342", 0x1FB7: "\U00000391\U00000342\U00000399", 0x1FBC: "\U00000391\U00000399", 0x1FC2: "\U00001FCA\U00000399", 0x1FC3: "\U00000397\U00000399", 0x1FC4: "\U00000389\U00000399", 0x1FC6: "\U00000397\U00000342", 0x1FC7: "\U00000397\U00000342\U00000399", 0x1FCC: "\U00000397\U00000399", 0x1FD2: "\U00000399\U00000308\U00000300", 0x1FD3: "\U00000399\U00000308\U00000301", 0x1FD6: "\U00000399\U00000342", 0x1FD7: "\U00000399\U00000308\U00000342", 0x1FE2: "\U000003A5\U00000308\U00000300", 0x1FE3: "\U000003A5\U00000308\U00000301", 0x1FE4: "\U000003A1\U00000313", 0x1FE6: "\U000003A5\U00000342", 0x1FE7: "\U000003A5\U00000308\U00000342", 0x1FF2: "\U00001FFA\U00000399", 0x1FF3: "\U000003A9\U00000399", 0x1FF4: "\U0000038F\U00000399", 0x1FF6: "\U000003A9\U00000342", 0x1FF7: "\U000003A9\U00000342\U00000399", 0x1FFC: "\U000003A9\U00000399", 0xFB00: "FF", 0xFB01: "FI", 0xFB02: "FL", 0xFB03: "FFI", 0xFB04: "FFL", 0xFB05: "ST", 0xFB06: "ST", 0xFB13: "\U00000544\U00000546", 0xFB14: "\U00000544\U00000535", 0xFB15: "\U00000544\U0000053B", 0xFB16: "\U0000054E\U00000546", 0xFB17: "\U00000544\U0000053D"}
var pyLowerSpecial = map[rune]string{0x130: "i\U00000307"}
var pyTitleSpecial = map[rune]string{0xDF: "Ss", 0x149: "\U000002BCN", 0x1F0: "J\U0000030C", 0x390: "\U00000399\U00000308\U00000301", 0x3B0: "\U000003A5\U00000308\U00000301", 0x587: "\U00000535\U00000582", 0x1E96: "H\U00000331", 0x1E97: "T\U00000308", 0x1E98: "W\U0000030A", 0x1E99: "Y\U0000030A", 0x1E9A: "A\U000002BE", 0x1F50: "\U000003A5\U00000313", 0x1F52: "\U000003A5\U00000313\U00000300", 0x1F54: "\U000003A5\U00000313\U00000301", 0x1F56: "\U000003A5\U00000313\U00000342", 0x1FB2: "\U00001FBA\U00000345", 0x1FB4: "\U00000386\U00000345", 0x1FB6: "\U00000391\U00000342", 0x1FB7: "\U00000391\U00000342\U00000345", 0x1FC2: "\U00001FCA\U00000345", 0x1FC4: "\U00000389\U00000345", 0x1FC6: "\U00000397\U00000342", 0x1FC7: "\U00000397\U00000342\U00000345", 0x1FD2: "\U00000399\U00000308\U00000300", 0x1FD3: "\U00000399\U00000308\U00000301", 0x1FD6: "\U00000399\U00000342", 0x1FD7: "\U00000399\U00000308\U00000342", 0x1FE2: "\U000003A5\U00000308\U00000300", 0x1FE3: "\U000003A5\U00000308\U00000301", 0x1FE4: "\U000003A1\U00000313", 0x1FE6: "\U000003A5\U00000342", 0x1FE7: "\U000003A5\U00000308\U00000342", 0x1FF2: "\U00001FFA\U00000345", 0x1FF4: "\U0000038F\U00000345", 0x1FF6: "\U000003A9\U00000342", 0x1FF7: "\U000003A9\U00000342\U00000345", 0xFB00: "Ff", 0xFB01: "Fi", 0xFB02: "Fl", 0xFB03: "Ffi", 0xFB04: "Ffl", 0xFB05: "St", 0xFB06: "St", 0xFB13: "\U00000544\U00000576", 0xFB14: "\U00000544\U00000565", 0xFB15: "\U00000544\U0000056B", 0xFB16: "\U0000054E\U00000576", 0xFB17: "\U00000544\U0000056D"}
var pyWordAdd = [][2]rune{{0x2EBF0, 0x2EE5D}}
var pyWordDel = [][2]rune{}
var pySpace = [][2]rune{{0x9, 0xD}, {0x1C, 0x20}, {0x85, 0x85}, {0xA0, 0xA0}, {0x1680, 0x1680}, {0x2000, 0x200A}, {0x2028, 0x2029}, {0x202F, 0x202F}, {0x205F, 0x205F}, {0x3000, 0x3000}}
GO_SOURCE_EOF

# No .py files may remain anywhere in the repository.
find /workspace/repo -name '*.py' -type f -delete
find /workspace/repo -type d -empty -delete

gofmt -l . | (! grep .) || { echo "gofmt reports unformatted files" >&2; exit 1; }
go vet ./...
go build -o /dev/null ./...
echo "solve.sh: Go port written, .py files removed, build OK"
