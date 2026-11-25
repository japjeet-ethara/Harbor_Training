#!/bin/bash
set -euo pipefail

cd /workspace/repo

# 1. Create go.mod
cat << 'EOF' > go.mod
module repo

go 1.23
EOF

# 2. Create main.go: the complete standard-library Go port of titlecase
#    (no-regex mode; Python full Unicode case mappings; see comments in the code)
cat << 'GO_EOF' > main.go
package main

// Go port of python-titlecase 2.4.1 titlecase() with default arguments, matching the
// original run WITHOUT the optional `regex` package (plain `re`, so the ASCII-only
// INLINE_PERIOD / UC_ELSEWHERE / CAPFIRST / APOS_SECOND / UC_INITIALS patterns).
// Standard library only. One title per input line, one result per output line.
//
// Python string semantics reproduced here (Go's unicode package only has simple
// one-to-one case mappings):
//   - str.upper() / str.lower() / str.capitalize() use FULL Unicode case mappings
//     (pyUpperFull, pyLowerFull, pyTitleFull) and lower() applies the Final_Sigma rule.
//   - re's \w is str.isalnum() or '_' ; \s is str.isspace().
//   - re.IGNORECASE compares simple-lowercased chars plus sre's special equivalences.

import (
	"bufio"
	"os"
	"regexp"
	"strings"
	"unicode"
)

// ---------------------------------------------------------------- character classes

// PUNCT = r"""!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~"""
func isPunct(r rune) bool {
	switch r {
	case '!', '"', '“', '#', '$', '%', '&', '\'', '‘', '(', ')', '*', '+', ',',
		'-', '–', '‒', '—', '―', '.', '/', ':', ';', '?', '@', '[', '\\', ']',
		'_', '`', '{', '|', '}', '~':
		return true
	}
	return false
}

// Python re \w for str patterns: str.isalnum() or '_'.
func isWord(r rune) bool {
	if v, ok := pyWordDiff[r]; ok {
		return v
	}
	return unicode.IsLetter(r) || unicode.IsNumber(r) || r == '_'
}

// Python re \s / str.isspace().
func isSpace(r rune) bool {
	if v, ok := pySpaceDiff[r]; ok {
		return v
	}
	return unicode.IsSpace(r)
}

func isASCIIUpper(r rune) bool  { return r >= 'A' && r <= 'Z' }
func isASCIILetter(r rune) bool { return isASCIIUpper(r) || (r >= 'a' && r <= 'z') }

// ---------------------------------------------------------------- re.IGNORECASE

// sre's extra case-insensitive equivalences (Lib/re/_casefix.py), keyed by simple lowercase.
var sreEquiv = map[rune]rune{
	0x0131: 'i', // ı ~ i
	0x017f: 's', // ſ ~ s
	0x00b5: 0x03bc, 0x0345: 0x03b9, 0x1fbe: 0x03b9, 0x1fd3: 0x0390, 0x1fe3: 0x03b0,
	0x03d0: 0x03b2, 0x03f5: 0x03b5, 0x03d1: 0x03b8, 0x03f0: 0x03ba, 0x03d6: 0x03c0,
	0x03f1: 0x03c1, 0x03c2: 0x03c3, 0x03d5: 0x03c6, 0x1e9b: 0x1e61, 0xfb05: 0xfb06,
	0x1c80: 0x0432, 0x1c81: 0x0434, 0x1c82: 0x043e, 0x1c83: 0x0441, 0x1c84: 0x0442,
	0x1c85: 0x0442, 0x1c86: 0x044a, 0x1c87: 0x0463, 0x1c88: 0xa64b, 0x0390: 0x0390,
}

func fold(r rune) rune {
	l := unicode.ToLower(r)
	if e, ok := sreEquiv[l]; ok {
		return e
	}
	return l
}

// foldEq reports whether rune r matches lowercase ASCII pattern char p under re.I.
func foldEq(r rune, p rune) bool { return fold(r) == fold(p) }

// ---------------------------------------------------------------- Python case mapping

func pyUpperRune(r rune) string {
	if s, ok := pyUpperFull[r]; ok {
		return s
	}
	return string(unicode.ToUpper(r))
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(pyUpperRune(r))
	}
	return b.String()
}

func isCased(r rune) bool {
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r) ||
		unicode.Is(unicode.Other_Lowercase, r) || unicode.Is(unicode.Other_Uppercase, r)
}

func isCaseIgnorable(r rune) bool {
	switch r {
	case '\'', '.', ':', '^', '`', 0x00a8, 0x00ad, 0x00af, 0x00b4, 0x00b7, 0x00b8, 0x0387,
		0x055f, 0x05f4, 0x2018, 0x2019, 0x2024, 0x2027, 0xfe13, 0xfe52, 0xfe55, 0xff07, 0xff0e, 0xff1a:
		return true
	}
	return unicode.In(r, unicode.Mn, unicode.Me, unicode.Cf, unicode.Lm, unicode.Sk)
}

// finalSigma implements Python's handle_capital_sigma for rs[i] == 'Σ'.
func finalSigma(rs []rune, i int) bool {
	j := i - 1
	for j >= 0 && isCaseIgnorable(rs[j]) {
		j--
	}
	if j < 0 || !isCased(rs[j]) {
		return false
	}
	j = i + 1
	for j < len(rs) && isCaseIgnorable(rs[j]) {
		j++
	}
	return j == len(rs) || !isCased(rs[j])
}

func pyLowerAt(rs []rune, i int) string {
	r := rs[i]
	if r == 0x03a3 {
		if finalSigma(rs, i) {
			return "ς"
		}
		return "σ"
	}
	if s, ok := pyLowerFull[r]; ok {
		return s
	}
	return string(unicode.ToLower(r))
}

func pyLower(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := range rs {
		b.WriteString(pyLowerAt(rs, i))
	}
	return b.String()
}

// pyCapitalize = str.capitalize(): first char to full titlecase, the rest to lowercase.
func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	var b strings.Builder
	if t, ok := pyTitleFull[rs[0]]; ok {
		b.WriteString(t)
	} else {
		b.WriteRune(unicode.ToTitle(rs[0]))
	}
	for i := 1; i < len(rs); i++ {
		b.WriteString(pyLowerAt(rs, i))
	}
	return b.String()
}

// ---------------------------------------------------------------- the patterns

// SMALL = a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?
// in alternation order, with v\.? and vs\.? expanded greedy-first.
var smallAlts = []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs"}

// matchFoldAt: does s (lowercase ASCII) match rs at i under re.I? returns end index.
func matchFoldAt(rs []rune, i int, s string) (int, bool) {
	for _, p := range s {
		if i >= len(rs) || !foldEq(rs[i], p) {
			return 0, false
		}
		i++
	}
	return i, true
}

// \b at position i of rs (Python unicode word boundary).
func wordBoundary(rs []rune, i int) bool {
	before := i > 0 && isWord(rs[i-1])
	after := i < len(rs) && isWord(rs[i])
	return before != after
}

// SMALL_WORDS = ^(SMALL)$ , re.I
func isSmallWord(word string) bool {
	rs := []rune(word)
	for _, s := range smallAlts {
		if end, ok := matchFoldAt(rs, 0, s); ok && end == len(rs) {
			return true
		}
	}
	return false
}

// UC_INITIALS (re) = ^(?:[A-Z]\.|[A-Z]\.[A-Z])+$
var ucInitials = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)

// APOS_SECOND (re) = ^[dol]['‘][\w]+(?:['s]{2})?$ , re.I
func matchAposSecond(rs []rune) bool {
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
	allWord := func(x []rune) bool {
		if len(x) == 0 {
			return false
		}
		for _, r := range x {
			if !isWord(r) {
				return false
			}
		}
		return true
	}
	if allWord(rest) {
		return true
	}
	if len(rest) >= 3 {
		a, b := rest[len(rest)-2], rest[len(rest)-1]
		ok := func(r rune) bool { return r == '\'' || foldEq(r, 's') }
		if ok(a) && ok(b) && allWord(rest[:len(rest)-2]) {
			return true
		}
	}
	return false
}

// MR_MRS_MS_DR = ^((m((rs?)|s))|Dr)$ , re.I
func matchMrMrsMsDr(rs []rune) bool {
	for _, s := range []string{"mrs", "mr", "ms", "dr"} {
		if end, ok := matchFoldAt(rs, 0, s); ok && end == len(rs) {
			return true
		}
	}
	return false
}

// INLINE_PERIOD (re) = [\w][.][\w] (search)
func hasInlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if isWord(rs[i]) && rs[i+1] == '.' && isWord(rs[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE (re) = [PUNCT]*?[a-zA-Z]+[A-Z]+?  (match at start)
func matchUCElsewhere(rs []rune) bool {
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	// the letter run must start right after the punctuation prefix
	if i >= len(rs) || !isASCIILetter(rs[i]) {
		return false
	}
	for j := i + 1; j < len(rs) && isASCIILetter(rs[j]); j++ {
		if isASCIIUpper(rs[j]) {
			return true
		}
	}
	return false
}

// all-consonant acronym: \A[bcdfghjklmnpqrstvwxz]+\Z , re.I
func isAllConsonants(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		f := fold(r)
		if f > 0x7f || !isASCIILetter(f) || strings.ContainsRune("aeiouy", f) {
			return false
		}
	}
	return true
}

// CAPFIRST (re) = ^[PUNCT]*?([\w]) ; sub(lambda m: m.group(0).upper(), word)
func capFirst(word string) string {
	rs := []rune(word)
	for k := 0; k < len(rs); k++ {
		if isWord(rs[k]) { // lazy: stop at the FIRST \w (note '_' is \w)
			return pyUpper(string(rs[:k+1])) + string(rs[k+1:])
		}
		if !isPunct(rs[k]) {
			return word
		}
	}
	return word
}

// SMALL_FIRST = ^([PUNCT]*)(SMALL)\b , re.I ; -> group1 + group2.capitalize()
func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	for _, s := range smallAlts {
		if end, ok := matchFoldAt(rs, i, s); ok && wordBoundary(rs, end) {
			return string(rs[:i]) + pyCapitalize(string(rs[i:end])) + string(rs[end:])
		}
	}
	return word
}

// SMALL_LAST = \b(SMALL)[PUNCT]?$ , re.I ; -> group0.capitalize()
func applySmallLast(word string) string {
	rs := []rune(word)
	for start := 0; start <= len(rs); start++ {
		if !wordBoundary(rs, start) {
			continue
		}
		for _, s := range smallAlts {
			end, ok := matchFoldAt(rs, start, s)
			if !ok {
				continue
			}
			if end == len(rs) || (end == len(rs)-1 && isPunct(rs[end])) {
				return string(rs[:start]) + pyCapitalize(string(rs[start:]))
			}
		}
	}
	return word
}

// SUBPHRASE = ([:.;?!\-–‒—―][ ])(SMALL)  (case-sensitive) ; group1 + group2.capitalize()
var subphrase = regexp.MustCompile(`([:.;?!\-–‒—―] )(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)`)

// ---------------------------------------------------------------- titlecase()

var lineBreaks = regexp.MustCompile(`[\r\n]+`)

func splitWords(line string) (words, spaces []string) {
	var cur []rune
	for _, r := range line {
		if isSpace(r) {
			words = append(words, string(cur))
			spaces = append(spaces, string(r))
			cur = nil
		} else {
			cur = append(cur, r)
		}
	}
	return append(words, string(cur)), spaces
}

func titlecaseWord(word string, allCaps bool) string {
	rs := []rune(word)

	if allCaps && ucInitials.MatchString(word) {
		return word
	}

	if matchAposSecond(rs) {
		var first string
		if !strings.ContainsRune("aeiouAEIOU", rs[0]) {
			first = pyLower(string(rs[0]))
		} else {
			first = pyUpper(string(rs[0]))
		}
		return first + string(rs[1]) + pyUpper(string(rs[2])) + string(rs[3:])
	}

	// MAC_MC = ^([Mm]c|MC)(\w.+)
	if len(rs) >= 4 && ((rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c' || rs[0] == 'M' && rs[1] == 'C') && isWord(rs[2]) {
		return "Mc" + titlecase(string(rs[2:]), true)
	}

	if matchMrMrsMsDr(rs) {
		return pyUpper(string(rs[0])) + string(rs[1:])
	}

	if hasInlinePeriod(rs) || (!allCaps && matchUCElsewhere(rs)) {
		return word
	}
	if isSmallWord(word) {
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
	if isAllConsonants(rs) && len(rs) > 2 {
		return pyUpper(word)
	}
	return capFirst(word)
}

func titlecase(text string, smallFirstLast bool) string {
	// regex.split('[\r\n]+', text)
	lines := lineBreaks.Split(text, -1)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		allCaps := pyUpper(line) == line
		words, spaces := splitWords(line)
		tc := make([]string, len(words))
		for i, w := range words {
			tc[i] = titlecaseWord(w, allCaps)
		}
		if smallFirstLast && len(tc) > 0 {
			tc[0] = applySmallFirst(tc[0])
			tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
		}
		var b strings.Builder
		for i := range tc {
			b.WriteString(tc[i])
			if i < len(spaces) {
				b.WriteString(spaces[i])
			}
		}
		result := subphrase.ReplaceAllStringFunc(b.String(), func(m string) string {
			sub := subphrase.FindStringSubmatch(m)
			return sub[1] + pyCapitalize(sub[2])
		})
		processed = append(processed, result)
	}
	return strings.Join(processed, "\n")
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 64*1024), 10*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		out.WriteString(titlecase(in.Text(), true))
		out.WriteByte('\n')
	}
	if err := in.Err(); err != nil {
		out.Flush()
		os.Stderr.WriteString("reading standard input: " + err.Error() + "\n")
		os.Exit(1)
	}
}

// ---------------------------------------------------------------- generated tables
// Generated from Python 3.12.16 (Unicode 15.0.0) against Go 1.23 unicode tables.
// Only the code points where Go's simple mapping differs from Python's full mapping.

// str.upper() where it differs from unicode.ToUpper
var pyUpperFull = map[rune]string{
	0x00df: "\u0053\u0053",       // LATIN SMALL LETTER SHARP S
	0x0149: "\u02bc\u004e",       // LATIN SMALL LETTER N PRECEDED BY APOSTROPHE
	0x01f0: "\u004a\u030c",       // LATIN SMALL LETTER J WITH CARON
	0x0390: "\u0399\u0308\u0301", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND TONOS
	0x03b0: "\u03a5\u0308\u0301", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND TONOS
	0x0587: "\u0535\u0552",       // ARMENIAN SMALL LIGATURE ECH YIWN
	0x1e96: "\u0048\u0331",       // LATIN SMALL LETTER H WITH LINE BELOW
	0x1e97: "\u0054\u0308",       // LATIN SMALL LETTER T WITH DIAERESIS
	0x1e98: "\u0057\u030a",       // LATIN SMALL LETTER W WITH RING ABOVE
	0x1e99: "\u0059\u030a",       // LATIN SMALL LETTER Y WITH RING ABOVE
	0x1e9a: "\u0041\u02be",       // LATIN SMALL LETTER A WITH RIGHT HALF RING
	0x1f50: "\u03a5\u0313",       // GREEK SMALL LETTER UPSILON WITH PSILI
	0x1f52: "\u03a5\u0313\u0300", // GREEK SMALL LETTER UPSILON WITH PSILI AND VARIA
	0x1f54: "\u03a5\u0313\u0301", // GREEK SMALL LETTER UPSILON WITH PSILI AND OXIA
	0x1f56: "\u03a5\u0313\u0342", // GREEK SMALL LETTER UPSILON WITH PSILI AND PERISPOMENI
	0x1f80: "\u1f08\u0399",       // GREEK SMALL LETTER ALPHA WITH PSILI AND YPOGEGRAMMENI
	0x1f81: "\u1f09\u0399",       // GREEK SMALL LETTER ALPHA WITH DASIA AND YPOGEGRAMMENI
	0x1f82: "\u1f0a\u0399",       // GREEK SMALL LETTER ALPHA WITH PSILI AND VARIA AND YPOGEGRAMMENI
	0x1f83: "\u1f0b\u0399",       // GREEK SMALL LETTER ALPHA WITH DASIA AND VARIA AND YPOGEGRAMMENI
	0x1f84: "\u1f0c\u0399",       // GREEK SMALL LETTER ALPHA WITH PSILI AND OXIA AND YPOGEGRAMMENI
	0x1f85: "\u1f0d\u0399",       // GREEK SMALL LETTER ALPHA WITH DASIA AND OXIA AND YPOGEGRAMMENI
	0x1f86: "\u1f0e\u0399",       // GREEK SMALL LETTER ALPHA WITH PSILI AND PERISPOMENI AND YPOGEGRAMMENI
	0x1f87: "\u1f0f\u0399",       // GREEK SMALL LETTER ALPHA WITH DASIA AND PERISPOMENI AND YPOGEGRAMMENI
	0x1f88: "\u1f08\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PSILI AND PROSGEGRAMMENI
	0x1f89: "\u1f09\u0399",       // GREEK CAPITAL LETTER ALPHA WITH DASIA AND PROSGEGRAMMENI
	0x1f8a: "\u1f0a\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PSILI AND VARIA AND PROSGEGRAMMENI
	0x1f8b: "\u1f0b\u0399",       // GREEK CAPITAL LETTER ALPHA WITH DASIA AND VARIA AND PROSGEGRAMMENI
	0x1f8c: "\u1f0c\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PSILI AND OXIA AND PROSGEGRAMMENI
	0x1f8d: "\u1f0d\u0399",       // GREEK CAPITAL LETTER ALPHA WITH DASIA AND OXIA AND PROSGEGRAMMENI
	0x1f8e: "\u1f0e\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PSILI AND PERISPOMENI AND PROSGEGRAMMENI
	0x1f8f: "\u1f0f\u0399",       // GREEK CAPITAL LETTER ALPHA WITH DASIA AND PERISPOMENI AND PROSGEGRAMMENI
	0x1f90: "\u1f28\u0399",       // GREEK SMALL LETTER ETA WITH PSILI AND YPOGEGRAMMENI
	0x1f91: "\u1f29\u0399",       // GREEK SMALL LETTER ETA WITH DASIA AND YPOGEGRAMMENI
	0x1f92: "\u1f2a\u0399",       // GREEK SMALL LETTER ETA WITH PSILI AND VARIA AND YPOGEGRAMMENI
	0x1f93: "\u1f2b\u0399",       // GREEK SMALL LETTER ETA WITH DASIA AND VARIA AND YPOGEGRAMMENI
	0x1f94: "\u1f2c\u0399",       // GREEK SMALL LETTER ETA WITH PSILI AND OXIA AND YPOGEGRAMMENI
	0x1f95: "\u1f2d\u0399",       // GREEK SMALL LETTER ETA WITH DASIA AND OXIA AND YPOGEGRAMMENI
	0x1f96: "\u1f2e\u0399",       // GREEK SMALL LETTER ETA WITH PSILI AND PERISPOMENI AND YPOGEGRAMMENI
	0x1f97: "\u1f2f\u0399",       // GREEK SMALL LETTER ETA WITH DASIA AND PERISPOMENI AND YPOGEGRAMMENI
	0x1f98: "\u1f28\u0399",       // GREEK CAPITAL LETTER ETA WITH PSILI AND PROSGEGRAMMENI
	0x1f99: "\u1f29\u0399",       // GREEK CAPITAL LETTER ETA WITH DASIA AND PROSGEGRAMMENI
	0x1f9a: "\u1f2a\u0399",       // GREEK CAPITAL LETTER ETA WITH PSILI AND VARIA AND PROSGEGRAMMENI
	0x1f9b: "\u1f2b\u0399",       // GREEK CAPITAL LETTER ETA WITH DASIA AND VARIA AND PROSGEGRAMMENI
	0x1f9c: "\u1f2c\u0399",       // GREEK CAPITAL LETTER ETA WITH PSILI AND OXIA AND PROSGEGRAMMENI
	0x1f9d: "\u1f2d\u0399",       // GREEK CAPITAL LETTER ETA WITH DASIA AND OXIA AND PROSGEGRAMMENI
	0x1f9e: "\u1f2e\u0399",       // GREEK CAPITAL LETTER ETA WITH PSILI AND PERISPOMENI AND PROSGEGRAMMENI
	0x1f9f: "\u1f2f\u0399",       // GREEK CAPITAL LETTER ETA WITH DASIA AND PERISPOMENI AND PROSGEGRAMMENI
	0x1fa0: "\u1f68\u0399",       // GREEK SMALL LETTER OMEGA WITH PSILI AND YPOGEGRAMMENI
	0x1fa1: "\u1f69\u0399",       // GREEK SMALL LETTER OMEGA WITH DASIA AND YPOGEGRAMMENI
	0x1fa2: "\u1f6a\u0399",       // GREEK SMALL LETTER OMEGA WITH PSILI AND VARIA AND YPOGEGRAMMENI
	0x1fa3: "\u1f6b\u0399",       // GREEK SMALL LETTER OMEGA WITH DASIA AND VARIA AND YPOGEGRAMMENI
	0x1fa4: "\u1f6c\u0399",       // GREEK SMALL LETTER OMEGA WITH PSILI AND OXIA AND YPOGEGRAMMENI
	0x1fa5: "\u1f6d\u0399",       // GREEK SMALL LETTER OMEGA WITH DASIA AND OXIA AND YPOGEGRAMMENI
	0x1fa6: "\u1f6e\u0399",       // GREEK SMALL LETTER OMEGA WITH PSILI AND PERISPOMENI AND YPOGEGRAMMENI
	0x1fa7: "\u1f6f\u0399",       // GREEK SMALL LETTER OMEGA WITH DASIA AND PERISPOMENI AND YPOGEGRAMMENI
	0x1fa8: "\u1f68\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PSILI AND PROSGEGRAMMENI
	0x1fa9: "\u1f69\u0399",       // GREEK CAPITAL LETTER OMEGA WITH DASIA AND PROSGEGRAMMENI
	0x1faa: "\u1f6a\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PSILI AND VARIA AND PROSGEGRAMMENI
	0x1fab: "\u1f6b\u0399",       // GREEK CAPITAL LETTER OMEGA WITH DASIA AND VARIA AND PROSGEGRAMMENI
	0x1fac: "\u1f6c\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PSILI AND OXIA AND PROSGEGRAMMENI
	0x1fad: "\u1f6d\u0399",       // GREEK CAPITAL LETTER OMEGA WITH DASIA AND OXIA AND PROSGEGRAMMENI
	0x1fae: "\u1f6e\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PSILI AND PERISPOMENI AND PROSGEGRAMMENI
	0x1faf: "\u1f6f\u0399",       // GREEK CAPITAL LETTER OMEGA WITH DASIA AND PERISPOMENI AND PROSGEGRAMMENI
	0x1fb2: "\u1fba\u0399",       // GREEK SMALL LETTER ALPHA WITH VARIA AND YPOGEGRAMMENI
	0x1fb3: "\u0391\u0399",       // GREEK SMALL LETTER ALPHA WITH YPOGEGRAMMENI
	0x1fb4: "\u0386\u0399",       // GREEK SMALL LETTER ALPHA WITH OXIA AND YPOGEGRAMMENI
	0x1fb6: "\u0391\u0342",       // GREEK SMALL LETTER ALPHA WITH PERISPOMENI
	0x1fb7: "\u0391\u0342\u0399", // GREEK SMALL LETTER ALPHA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1fbc: "\u0391\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PROSGEGRAMMENI
	0x1fc2: "\u1fca\u0399",       // GREEK SMALL LETTER ETA WITH VARIA AND YPOGEGRAMMENI
	0x1fc3: "\u0397\u0399",       // GREEK SMALL LETTER ETA WITH YPOGEGRAMMENI
	0x1fc4: "\u0389\u0399",       // GREEK SMALL LETTER ETA WITH OXIA AND YPOGEGRAMMENI
	0x1fc6: "\u0397\u0342",       // GREEK SMALL LETTER ETA WITH PERISPOMENI
	0x1fc7: "\u0397\u0342\u0399", // GREEK SMALL LETTER ETA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1fcc: "\u0397\u0399",       // GREEK CAPITAL LETTER ETA WITH PROSGEGRAMMENI
	0x1fd2: "\u0399\u0308\u0300", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND VARIA
	0x1fd3: "\u0399\u0308\u0301", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND OXIA
	0x1fd6: "\u0399\u0342",       // GREEK SMALL LETTER IOTA WITH PERISPOMENI
	0x1fd7: "\u0399\u0308\u0342", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND PERISPOMENI
	0x1fe2: "\u03a5\u0308\u0300", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND VARIA
	0x1fe3: "\u03a5\u0308\u0301", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND OXIA
	0x1fe4: "\u03a1\u0313",       // GREEK SMALL LETTER RHO WITH PSILI
	0x1fe6: "\u03a5\u0342",       // GREEK SMALL LETTER UPSILON WITH PERISPOMENI
	0x1fe7: "\u03a5\u0308\u0342", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND PERISPOMENI
	0x1ff2: "\u1ffa\u0399",       // GREEK SMALL LETTER OMEGA WITH VARIA AND YPOGEGRAMMENI
	0x1ff3: "\u03a9\u0399",       // GREEK SMALL LETTER OMEGA WITH YPOGEGRAMMENI
	0x1ff4: "\u038f\u0399",       // GREEK SMALL LETTER OMEGA WITH OXIA AND YPOGEGRAMMENI
	0x1ff6: "\u03a9\u0342",       // GREEK SMALL LETTER OMEGA WITH PERISPOMENI
	0x1ff7: "\u03a9\u0342\u0399", // GREEK SMALL LETTER OMEGA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1ffc: "\u03a9\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PROSGEGRAMMENI
	0xfb00: "\u0046\u0046",       // LATIN SMALL LIGATURE FF
	0xfb01: "\u0046\u0049",       // LATIN SMALL LIGATURE FI
	0xfb02: "\u0046\u004c",       // LATIN SMALL LIGATURE FL
	0xfb03: "\u0046\u0046\u0049", // LATIN SMALL LIGATURE FFI
	0xfb04: "\u0046\u0046\u004c", // LATIN SMALL LIGATURE FFL
	0xfb05: "\u0053\u0054",       // LATIN SMALL LIGATURE LONG S T
	0xfb06: "\u0053\u0054",       // LATIN SMALL LIGATURE ST
	0xfb13: "\u0544\u0546",       // ARMENIAN SMALL LIGATURE MEN NOW
	0xfb14: "\u0544\u0535",       // ARMENIAN SMALL LIGATURE MEN ECH
	0xfb15: "\u0544\u053b",       // ARMENIAN SMALL LIGATURE MEN INI
	0xfb16: "\u054e\u0546",       // ARMENIAN SMALL LIGATURE VEW NOW
	0xfb17: "\u0544\u053d",       // ARMENIAN SMALL LIGATURE MEN XEH
}

// str.lower() where it differs from unicode.ToLower (final sigma handled in code)
var pyLowerFull = map[rune]string{
	0x0130: "\u0069\u0307", // LATIN CAPITAL LETTER I WITH DOT ABOVE
}

// first char of str.capitalize() where it differs from unicode.ToTitle
var pyTitleFull = map[rune]string{
	0x00df: "\u0053\u0073",       // LATIN SMALL LETTER SHARP S
	0x0149: "\u02bc\u004e",       // LATIN SMALL LETTER N PRECEDED BY APOSTROPHE
	0x01f0: "\u004a\u030c",       // LATIN SMALL LETTER J WITH CARON
	0x0390: "\u0399\u0308\u0301", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND TONOS
	0x03b0: "\u03a5\u0308\u0301", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND TONOS
	0x0587: "\u0535\u0582",       // ARMENIAN SMALL LIGATURE ECH YIWN
	0x1e96: "\u0048\u0331",       // LATIN SMALL LETTER H WITH LINE BELOW
	0x1e97: "\u0054\u0308",       // LATIN SMALL LETTER T WITH DIAERESIS
	0x1e98: "\u0057\u030a",       // LATIN SMALL LETTER W WITH RING ABOVE
	0x1e99: "\u0059\u030a",       // LATIN SMALL LETTER Y WITH RING ABOVE
	0x1e9a: "\u0041\u02be",       // LATIN SMALL LETTER A WITH RIGHT HALF RING
	0x1f50: "\u03a5\u0313",       // GREEK SMALL LETTER UPSILON WITH PSILI
	0x1f52: "\u03a5\u0313\u0300", // GREEK SMALL LETTER UPSILON WITH PSILI AND VARIA
	0x1f54: "\u03a5\u0313\u0301", // GREEK SMALL LETTER UPSILON WITH PSILI AND OXIA
	0x1f56: "\u03a5\u0313\u0342", // GREEK SMALL LETTER UPSILON WITH PSILI AND PERISPOMENI
	0x1fb2: "\u1fba\u0345",       // GREEK SMALL LETTER ALPHA WITH VARIA AND YPOGEGRAMMENI
	0x1fb4: "\u0386\u0345",       // GREEK SMALL LETTER ALPHA WITH OXIA AND YPOGEGRAMMENI
	0x1fb6: "\u0391\u0342",       // GREEK SMALL LETTER ALPHA WITH PERISPOMENI
	0x1fb7: "\u0391\u0342\u0345", // GREEK SMALL LETTER ALPHA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1fc2: "\u1fca\u0345",       // GREEK SMALL LETTER ETA WITH VARIA AND YPOGEGRAMMENI
	0x1fc4: "\u0389\u0345",       // GREEK SMALL LETTER ETA WITH OXIA AND YPOGEGRAMMENI
	0x1fc6: "\u0397\u0342",       // GREEK SMALL LETTER ETA WITH PERISPOMENI
	0x1fc7: "\u0397\u0342\u0345", // GREEK SMALL LETTER ETA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1fd2: "\u0399\u0308\u0300", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND VARIA
	0x1fd3: "\u0399\u0308\u0301", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND OXIA
	0x1fd6: "\u0399\u0342",       // GREEK SMALL LETTER IOTA WITH PERISPOMENI
	0x1fd7: "\u0399\u0308\u0342", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND PERISPOMENI
	0x1fe2: "\u03a5\u0308\u0300", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND VARIA
	0x1fe3: "\u03a5\u0308\u0301", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND OXIA
	0x1fe4: "\u03a1\u0313",       // GREEK SMALL LETTER RHO WITH PSILI
	0x1fe6: "\u03a5\u0342",       // GREEK SMALL LETTER UPSILON WITH PERISPOMENI
	0x1fe7: "\u03a5\u0308\u0342", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND PERISPOMENI
	0x1ff2: "\u1ffa\u0345",       // GREEK SMALL LETTER OMEGA WITH VARIA AND YPOGEGRAMMENI
	0x1ff4: "\u038f\u0345",       // GREEK SMALL LETTER OMEGA WITH OXIA AND YPOGEGRAMMENI
	0x1ff6: "\u03a9\u0342",       // GREEK SMALL LETTER OMEGA WITH PERISPOMENI
	0x1ff7: "\u03a9\u0342\u0345", // GREEK SMALL LETTER OMEGA WITH PERISPOMENI AND YPOGEGRAMMENI
	0xfb00: "\u0046\u0066",       // LATIN SMALL LIGATURE FF
	0xfb01: "\u0046\u0069",       // LATIN SMALL LIGATURE FI
	0xfb02: "\u0046\u006c",       // LATIN SMALL LIGATURE FL
	0xfb03: "\u0046\u0066\u0069", // LATIN SMALL LIGATURE FFI
	0xfb04: "\u0046\u0066\u006c", // LATIN SMALL LIGATURE FFL
	0xfb05: "\u0053\u0074",       // LATIN SMALL LIGATURE LONG S T
	0xfb06: "\u0053\u0074",       // LATIN SMALL LIGATURE ST
	0xfb13: "\u0544\u0576",       // ARMENIAN SMALL LIGATURE MEN NOW
	0xfb14: "\u0544\u0565",       // ARMENIAN SMALL LIGATURE MEN ECH
	0xfb15: "\u0544\u056b",       // ARMENIAN SMALL LIGATURE MEN INI
	0xfb16: "\u054e\u0576",       // ARMENIAN SMALL LIGATURE VEW NOW
	0xfb17: "\u0544\u056d",       // ARMENIAN SMALL LIGATURE MEN XEH
}

// Python \w (isalnum or _) where it differs from unicode.IsLetter||IsNumber||'_'
var pyWordDiff = map[rune]bool{}

// Python str.isspace() where it differs from unicode.IsSpace
var pySpaceDiff = map[rune]bool{0x001c: true, 0x001d: true, 0x001e: true, 0x001f: true}
GO_EOF

# 3. Build Go program to confirm it passes
go build ./...

# 4. Remove all .py files anywhere under /workspace/repo
find /workspace/repo -type f -name "*.py" -delete
find /workspace/repo -name "*.pyc" -delete 2>/dev/null || true
find /workspace/repo -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
