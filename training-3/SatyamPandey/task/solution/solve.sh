#!/bin/bash
# Reference solution: a Go port of python-titlecase, written with the standard
# library only (no look-ahead/look-behind regexes; the rules are hand-coded).
set -euo pipefail
cd /workspace/repo
cat > go.mod <<'GO_SOURCE_EOF'
module titlecase

go 1.23
GO_SOURCE_EOF
cat > main.go <<'GO_SOURCE_EOF'
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
)

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()

	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			out.WriteString(titlecase(line, true))
			out.WriteString("\n")
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			os.Exit(1)
		}
	}
}
GO_SOURCE_EOF
cat > titlecase.go <<'GO_SOURCE_EOF'
package main

import (
	"strings"
	"unicode"
)

// PUNCT from the Python source (used inside character classes there).
const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// SMALL alternatives in the exact order of the Python alternation, with the
// greedy optional "." of `v\.?` and `vs\.?` expanded (longest first).
var smallAlts = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
	"on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

var smallWordSet = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

func isPunct(r rune) bool { return strings.ContainsRune(punctChars, r) }

func isLetter(r rune) bool { return unicode.IsLetter(r) }

// isWordRune is \w of the `regex` module (Unicode TR#18):
// [\p{Alphabetic}\p{Mark}\p{Decimal_Number}\p{Connector_Punctuation}\p{Join_Control}]
// where Alphabetic = Letter + Letter_Number + Other_Alphabetic. So "Ⅰ", "Ⓐ",
// "‿" and the zero-width joiner are word characters too.
func isWordRune(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsMark(r) || unicode.IsDigit(r) ||
		unicode.In(r, unicode.Nl, unicode.Pc, unicode.Other_Alphabetic, unicode.Join_Control)
}

// foldASCII reports which ASCII lower-case letter r matches under regex.I.
// The `regex` module matches a letter with its upper/lower case and, beyond
// ASCII, only with 'ſ' (s), 'K' KELVIN SIGN (k) and 'İ' (i).
func foldASCII(r rune) rune {
	switch {
	case r >= 'a' && r <= 'z':
		return r
	case r >= 'A' && r <= 'Z':
		return r + ('a' - 'A')
	case r == 0x017F:
		return 's'
	case r == 0x212A:
		return 'k'
	case r == 0x0130:
		return 'i'
	}
	return -1
}

// foldEq is `regex.I` equality of s with the ASCII pattern text lit.
func foldEq(s []rune, lit string) bool {
	if len(s) != len(lit) {
		return false
	}
	for i := 0; i < len(lit); i++ {
		c := rune(lit[i])
		if c >= 'a' && c <= 'z' {
			if foldASCII(s[i]) != c {
				return false
			}
		} else if s[i] != c {
			return false
		}
	}
	return true
}

// isBoundary reports whether there is a regex \b between rs[pos-1] and rs[pos].
func isBoundary(rs []rune, pos int) bool {
	left := pos-1 >= 0 && pos-1 < len(rs) && isWordRune(rs[pos-1])
	right := pos >= 0 && pos < len(rs) && isWordRune(rs[pos])
	return left != right
}

// capitalize is Python str.capitalize() (full case mapping, see casing.go).
func capitalize(s string) string { return pyCapitalize(s) }

// isSmallWord is SMALL_WORDS.match (regex.I), see foldASCII.
func isSmallWord(s string) bool {
	rs := []rune(s)
	for w := range smallWordSet {
		if foldEq(rs, w) {
			return true
		}
	}
	return false
}

// UC_INITIALS: ^(?:[Lu]\.|[Lu]\.[Lu])+$
func ucInitials(w []rune) bool {
	n := len(w)
	if n == 0 {
		return false
	}
	reach := make([]bool, n+1)
	for i := 0; i < n; i++ {
		if i != 0 && !reach[i] {
			continue
		}
		if i+1 < n && unicode.IsUpper(w[i]) && w[i+1] == '.' {
			reach[i+2] = true
			if i+2 < n && unicode.IsUpper(w[i+2]) {
				reach[i+3] = true
			}
		}
	}
	return reach[n]
}

// APOS_SECOND: ^[dol]['‘][Letter]+(?:['s]{2})?$  (case-insensitive)
func aposSecond(w []rune) bool {
	if len(w) < 3 {
		return false
	}
	switch foldASCII(w[0]) {
	case 'd', 'o', 'l':
	default:
		return false
	}
	if w[1] != '\'' && w[1] != '‘' {
		return false
	}
	inSet := func(r rune) bool { return r == '\'' || foldASCII(r) == 's' }
	rest := w[2:]
	for k := 1; k <= len(rest); k++ {
		if !isLetter(rest[k-1]) {
			break
		}
		if k == len(rest) {
			return true
		}
		if len(rest)-k == 2 && inSet(rest[k]) && inSet(rest[k+1]) {
			return true
		}
	}
	return false
}

// MAC_MC: ^([Mm]c|MC)(\w.+)
func macMc(w []rune) (prefix string, rest string, ok bool) {
	if len(w) < 2 {
		return "", "", false
	}
	if !((w[0] == 'M' || w[0] == 'm') && w[1] == 'c') && !(w[0] == 'M' && w[1] == 'C') {
		return "", "", false
	}
	r := w[2:]
	if len(r) >= 2 && isWordRune(r[0]) {
		return string(w[:2]), string(r), true
	}
	return "", "", false
}

// INLINE_PERIOD: [Letter][.][Letter] anywhere.
func inlinePeriod(w []rune) bool {
	for i := 0; i+2 < len(w); i++ {
		if isLetter(w[i]) && w[i+1] == '.' && isLetter(w[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE.match: [PUNCT]*?[Letter]+[Uppercase_Letter]+?
func ucElsewhere(w []rune) bool {
	i := 0
	for i < len(w) && isPunct(w[i]) {
		i++
	}
	j := i
	for j < len(w) && isLetter(w[j]) {
		j++
	}
	for k := i + 1; k < j; k++ {
		if unicode.IsUpper(w[k]) {
			return true
		}
	}
	return false
}

func isAllConsonants(w []rune) bool {
	if len(w) == 0 {
		return false
	}
	// \A[CONSONANTS]+\Z with regex.I, so 'ſ' and the Kelvin sign count too.
	for _, r := range w {
		switch foldASCII(r) {
		case -1, 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

// CAPFIRST.sub(upper): ^[PUNCT]*?([Letter])
func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i < len(rs) && isLetter(rs[i]) {
		// .upper() may turn one rune into several ("ß" -> "SS").
		return string(rs[:i]) + pyUpperRune(rs[i]) + string(rs[i+1:])
	}
	return string(rs)
}

// SMALL_FIRST: ^([PUNCT]*)(SMALL)\b  -> group2.capitalize()
func smallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	for _, cand := range smallAlts {
		n := len([]rune(cand))
		if i+n > len(rs) {
			continue
		}
		if !foldEq(rs[i:i+n], cand) {
			continue
		}
		if !isBoundary(rs, i+n) {
			continue
		}
		return string(rs[:i]) + capitalize(string(rs[i:i+n])) + string(rs[i+n:])
	}
	return word
}

// SMALL_LAST: \b(SMALL)[PUNCT]?$  -> group0.capitalize()
func smallLast(word string) string {
	rs := []rune(word)
	for p := 0; p < len(rs); p++ {
		if !isBoundary(rs, p) {
			continue
		}
		t := string(rs[p:])
		tr := rs[p:]
		if isSmallWord(t) ||
			(len(tr) >= 2 && isPunct(tr[len(tr)-1]) && isSmallWord(string(tr[:len(tr)-1]))) {
			return string(rs[:p]) + capitalize(t)
		}
	}
	return word
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	}
	return false
}

// SUBPHRASE: ([:.;?!\-–‒—―][ ])(SMALL)   (case-sensitive, no \b) -> group2.capitalize()
func subphrase(s string) string {
	rs := []rune(s)
	var out []rune
	i := 0
	for i < len(rs) {
		if isSubPunct(rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			matched := ""
			for _, cand := range smallAlts {
				if strings.HasPrefix(string(rs[i+2:]), cand) {
					matched = cand
					break
				}
			}
			if matched != "" {
				out = append(out, rs[i], ' ')
				out = append(out, []rune(capitalize(matched))...)
				i += 2 + len([]rune(matched))
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

func splitBy(s string, sep string) []string { return strings.Split(s, sep) }

// titlecase mirrors titlecase.titlecase(text, small_first_last=...) for text
// without line breaks (callers split on lines first).
func titlecase(text string, smallFirstLast bool) string {
	// regex.split('[\r\n]+', text)
	lines := splitLines(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, processLine(line, smallFirstLast))
	}
	return strings.Join(processed, "\n")
}

func splitLines(text string) []string {
	var lines []string
	var cur []rune
	inBreak := false
	for _, r := range text {
		if r == '\r' || r == '\n' {
			if !inBreak {
				lines = append(lines, string(cur))
				cur = cur[:0]
				inBreak = true
			}
			continue
		}
		inBreak = false
		cur = append(cur, r)
	}
	lines = append(lines, string(cur))
	return lines
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := pyUpper(line) == line

	// regex.split(r'(\s)', line)
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

	tc := make([]string, 0, len(words))
	for _, word := range words {
		tc = append(tc, processWord(word, allCaps))
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

func processWord(word string, allCaps bool) string {
	rs := []rune(word)

	if allCaps && ucInitials(rs) {
		return word
	}

	if aposSecond(rs) {
		first := rs[0]
		var f rune
		if strings.ContainsRune("aeiouAEIOU", first) {
			f = unicode.ToUpper(first)
		} else {
			f = unicode.ToLower(first)
		}
		return string([]rune{f, rs[1]}) + pyUpperRune(rs[2]) + string(rs[3:])
	}

	if prefix, rest, ok := macMc(rs); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}

	// MR_MRS_MS_DR (regex.I, see foldASCII)
	for _, h := range []string{"mr", "mrs", "ms", "dr"} {
		if foldEq(rs, h) {
			return pyUpperRune(rs[0]) + string(rs[1:])
		}
	}

	if inlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}
	if isSmallWord(word) {
		return pyLower(word)
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := splitBy(word, "/")
		for i, t := range parts {
			parts[i] = titlecase(t, false)
		}
		return strings.Join(parts, "/")
	}

	if strings.Contains(word, "-") {
		parts := splitBy(word, "-")
		for i, t := range parts {
			parts[i] = titlecase(t, false)
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
GO_SOURCE_EOF

cat > casing.go <<'GO_SOURCE_EOF'
package main

import (
	"strings"
	"unicode"
)

// Python's str.upper()/lower()/capitalize() use the FULL Unicode case mappings
// (one rune can become several: "ß".upper() == "SS", "ﬁ".upper() == "FI",
// "İ".lower() == "i̇"), and lower() applies the Final_Sigma rule. Go's
// unicode.ToUpper/ToLower are simple 1:1 mappings, so the differences are kept
// in casetables.go and applied here.

func pyUpperRune(r rune) string {
	if s, ok := pyUpperOverride[r]; ok {
		return s
	}
	return string(unicode.ToUpper(r))
}

func pyTitleRune(r rune) string {
	if s, ok := pyTitleOverride[r]; ok {
		return s
	}
	return string(unicode.ToTitle(r))
}

func pyLowerRune(r rune) string {
	if s, ok := pyLowerOverride[r]; ok {
		return s
	}
	return string(unicode.ToLower(r))
}

// pyUpper is Python str.upper().
func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(pyUpperRune(r))
	}
	return b.String()
}

// isCased is the Unicode Cased property (Lowercase | Uppercase | Lt).
func isCased(r rune) bool {
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r) ||
		unicode.Is(unicode.Other_Lowercase, r) || unicode.Is(unicode.Other_Uppercase, r)
}

// isCaseIgnorable is the Unicode Case_Ignorable property: Mn, Me, Cf, Lm, Sk and
// the Word_Break MidLetter / MidNumLet / Single_Quote characters.
func isCaseIgnorable(r rune) bool {
	switch r {
	case 0x0027, 0x002E, 0x003A, 0x00B7, 0x0387, 0x055F, 0x05F4, 0x2018, 0x2019,
		0x2024, 0x2027, 0xFE13, 0xFE52, 0xFE55, 0xFF07, 0xFF0E, 0xFF1A:
		return true
	}
	return unicode.In(r, unicode.Mn, unicode.Me, unicode.Cf, unicode.Lm, unicode.Sk)
}

// finalSigma mirrors CPython's handle_capital_sigma: a capital sigma at index i
// becomes final 'ς' when a cased letter comes before it and none after it
// (case-ignorable characters are skipped in both directions).
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

func lowerAt(rs []rune, i int) string {
	if rs[i] == 0x03A3 { // GREEK CAPITAL LETTER SIGMA
		if finalSigma(rs, i) {
			return "ς"
		}
		return "σ"
	}
	return pyLowerRune(rs[i])
}

// pyLower is Python str.lower().
func pyLower(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := range rs {
		b.WriteString(lowerAt(rs, i))
	}
	return b.String()
}

// pyCapitalize is Python (3.8+) str.capitalize(): title-case the first
// character, lower-case the rest.
func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	var b strings.Builder
	b.WriteString(pyTitleRune(rs[0]))
	for i := 1; i < len(rs); i++ {
		b.WriteString(lowerAt(rs, i))
	}
	return b.String()
}
GO_SOURCE_EOF
cat > casetables.go <<'GO_SOURCE_EOF'
package main

// Generated from Python 3.14.10 (Unicode 16.0.0) str.upper()/lower()/title().
// Only runes where Python's full case mapping differs from Go's simple
// unicode.ToUpper/ToLower/ToTitle are listed; every other rune uses Go's mapping.

var pyUpperOverride = map[rune]string{
	0x00DF:  "\u0053\u0053",       // LATIN SMALL LETTER SHARP S
	0x0149:  "\u02BC\u004E",       // LATIN SMALL LETTER N PRECEDED BY APOSTROPHE
	0x019B:  "\uA7DC",             // LATIN SMALL LETTER LAMBDA WITH STROKE
	0x01F0:  "\u004A\u030C",       // LATIN SMALL LETTER J WITH CARON
	0x0264:  "\uA7CB",             // LATIN SMALL LETTER RAMS HORN
	0x0390:  "\u0399\u0308\u0301", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND TONOS
	0x03B0:  "\u03A5\u0308\u0301", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND TONOS
	0x0587:  "\u0535\u0552",       // ARMENIAN SMALL LIGATURE ECH YIWN
	0x1C8A:  "\u1C89",             // CYRILLIC SMALL LETTER TJE
	0x1E96:  "\u0048\u0331",       // LATIN SMALL LETTER H WITH LINE BELOW
	0x1E97:  "\u0054\u0308",       // LATIN SMALL LETTER T WITH DIAERESIS
	0x1E98:  "\u0057\u030A",       // LATIN SMALL LETTER W WITH RING ABOVE
	0x1E99:  "\u0059\u030A",       // LATIN SMALL LETTER Y WITH RING ABOVE
	0x1E9A:  "\u0041\u02BE",       // LATIN SMALL LETTER A WITH RIGHT HALF RING
	0x1F50:  "\u03A5\u0313",       // GREEK SMALL LETTER UPSILON WITH PSILI
	0x1F52:  "\u03A5\u0313\u0300", // GREEK SMALL LETTER UPSILON WITH PSILI AND VARIA
	0x1F54:  "\u03A5\u0313\u0301", // GREEK SMALL LETTER UPSILON WITH PSILI AND OXIA
	0x1F56:  "\u03A5\u0313\u0342", // GREEK SMALL LETTER UPSILON WITH PSILI AND PERISPOMENI
	0x1F80:  "\u1F08\u0399",       // GREEK SMALL LETTER ALPHA WITH PSILI AND YPOGEGRAMMENI
	0x1F81:  "\u1F09\u0399",       // GREEK SMALL LETTER ALPHA WITH DASIA AND YPOGEGRAMMENI
	0x1F82:  "\u1F0A\u0399",       // GREEK SMALL LETTER ALPHA WITH PSILI AND VARIA AND YPOGEGRAMMENI
	0x1F83:  "\u1F0B\u0399",       // GREEK SMALL LETTER ALPHA WITH DASIA AND VARIA AND YPOGEGRAMMENI
	0x1F84:  "\u1F0C\u0399",       // GREEK SMALL LETTER ALPHA WITH PSILI AND OXIA AND YPOGEGRAMMENI
	0x1F85:  "\u1F0D\u0399",       // GREEK SMALL LETTER ALPHA WITH DASIA AND OXIA AND YPOGEGRAMMENI
	0x1F86:  "\u1F0E\u0399",       // GREEK SMALL LETTER ALPHA WITH PSILI AND PERISPOMENI AND YPOGEGRAMMENI
	0x1F87:  "\u1F0F\u0399",       // GREEK SMALL LETTER ALPHA WITH DASIA AND PERISPOMENI AND YPOGEGRAMMENI
	0x1F88:  "\u1F08\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PSILI AND PROSGEGRAMMENI
	0x1F89:  "\u1F09\u0399",       // GREEK CAPITAL LETTER ALPHA WITH DASIA AND PROSGEGRAMMENI
	0x1F8A:  "\u1F0A\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PSILI AND VARIA AND PROSGEGRAMMENI
	0x1F8B:  "\u1F0B\u0399",       // GREEK CAPITAL LETTER ALPHA WITH DASIA AND VARIA AND PROSGEGRAMMENI
	0x1F8C:  "\u1F0C\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PSILI AND OXIA AND PROSGEGRAMMENI
	0x1F8D:  "\u1F0D\u0399",       // GREEK CAPITAL LETTER ALPHA WITH DASIA AND OXIA AND PROSGEGRAMMENI
	0x1F8E:  "\u1F0E\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PSILI AND PERISPOMENI AND PROSGEGRAMMENI
	0x1F8F:  "\u1F0F\u0399",       // GREEK CAPITAL LETTER ALPHA WITH DASIA AND PERISPOMENI AND PROSGEGRAMMENI
	0x1F90:  "\u1F28\u0399",       // GREEK SMALL LETTER ETA WITH PSILI AND YPOGEGRAMMENI
	0x1F91:  "\u1F29\u0399",       // GREEK SMALL LETTER ETA WITH DASIA AND YPOGEGRAMMENI
	0x1F92:  "\u1F2A\u0399",       // GREEK SMALL LETTER ETA WITH PSILI AND VARIA AND YPOGEGRAMMENI
	0x1F93:  "\u1F2B\u0399",       // GREEK SMALL LETTER ETA WITH DASIA AND VARIA AND YPOGEGRAMMENI
	0x1F94:  "\u1F2C\u0399",       // GREEK SMALL LETTER ETA WITH PSILI AND OXIA AND YPOGEGRAMMENI
	0x1F95:  "\u1F2D\u0399",       // GREEK SMALL LETTER ETA WITH DASIA AND OXIA AND YPOGEGRAMMENI
	0x1F96:  "\u1F2E\u0399",       // GREEK SMALL LETTER ETA WITH PSILI AND PERISPOMENI AND YPOGEGRAMMENI
	0x1F97:  "\u1F2F\u0399",       // GREEK SMALL LETTER ETA WITH DASIA AND PERISPOMENI AND YPOGEGRAMMENI
	0x1F98:  "\u1F28\u0399",       // GREEK CAPITAL LETTER ETA WITH PSILI AND PROSGEGRAMMENI
	0x1F99:  "\u1F29\u0399",       // GREEK CAPITAL LETTER ETA WITH DASIA AND PROSGEGRAMMENI
	0x1F9A:  "\u1F2A\u0399",       // GREEK CAPITAL LETTER ETA WITH PSILI AND VARIA AND PROSGEGRAMMENI
	0x1F9B:  "\u1F2B\u0399",       // GREEK CAPITAL LETTER ETA WITH DASIA AND VARIA AND PROSGEGRAMMENI
	0x1F9C:  "\u1F2C\u0399",       // GREEK CAPITAL LETTER ETA WITH PSILI AND OXIA AND PROSGEGRAMMENI
	0x1F9D:  "\u1F2D\u0399",       // GREEK CAPITAL LETTER ETA WITH DASIA AND OXIA AND PROSGEGRAMMENI
	0x1F9E:  "\u1F2E\u0399",       // GREEK CAPITAL LETTER ETA WITH PSILI AND PERISPOMENI AND PROSGEGRAMMENI
	0x1F9F:  "\u1F2F\u0399",       // GREEK CAPITAL LETTER ETA WITH DASIA AND PERISPOMENI AND PROSGEGRAMMENI
	0x1FA0:  "\u1F68\u0399",       // GREEK SMALL LETTER OMEGA WITH PSILI AND YPOGEGRAMMENI
	0x1FA1:  "\u1F69\u0399",       // GREEK SMALL LETTER OMEGA WITH DASIA AND YPOGEGRAMMENI
	0x1FA2:  "\u1F6A\u0399",       // GREEK SMALL LETTER OMEGA WITH PSILI AND VARIA AND YPOGEGRAMMENI
	0x1FA3:  "\u1F6B\u0399",       // GREEK SMALL LETTER OMEGA WITH DASIA AND VARIA AND YPOGEGRAMMENI
	0x1FA4:  "\u1F6C\u0399",       // GREEK SMALL LETTER OMEGA WITH PSILI AND OXIA AND YPOGEGRAMMENI
	0x1FA5:  "\u1F6D\u0399",       // GREEK SMALL LETTER OMEGA WITH DASIA AND OXIA AND YPOGEGRAMMENI
	0x1FA6:  "\u1F6E\u0399",       // GREEK SMALL LETTER OMEGA WITH PSILI AND PERISPOMENI AND YPOGEGRAMMENI
	0x1FA7:  "\u1F6F\u0399",       // GREEK SMALL LETTER OMEGA WITH DASIA AND PERISPOMENI AND YPOGEGRAMMENI
	0x1FA8:  "\u1F68\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PSILI AND PROSGEGRAMMENI
	0x1FA9:  "\u1F69\u0399",       // GREEK CAPITAL LETTER OMEGA WITH DASIA AND PROSGEGRAMMENI
	0x1FAA:  "\u1F6A\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PSILI AND VARIA AND PROSGEGRAMMENI
	0x1FAB:  "\u1F6B\u0399",       // GREEK CAPITAL LETTER OMEGA WITH DASIA AND VARIA AND PROSGEGRAMMENI
	0x1FAC:  "\u1F6C\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PSILI AND OXIA AND PROSGEGRAMMENI
	0x1FAD:  "\u1F6D\u0399",       // GREEK CAPITAL LETTER OMEGA WITH DASIA AND OXIA AND PROSGEGRAMMENI
	0x1FAE:  "\u1F6E\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PSILI AND PERISPOMENI AND PROSGEGRAMMENI
	0x1FAF:  "\u1F6F\u0399",       // GREEK CAPITAL LETTER OMEGA WITH DASIA AND PERISPOMENI AND PROSGEGRAMMENI
	0x1FB2:  "\u1FBA\u0399",       // GREEK SMALL LETTER ALPHA WITH VARIA AND YPOGEGRAMMENI
	0x1FB3:  "\u0391\u0399",       // GREEK SMALL LETTER ALPHA WITH YPOGEGRAMMENI
	0x1FB4:  "\u0386\u0399",       // GREEK SMALL LETTER ALPHA WITH OXIA AND YPOGEGRAMMENI
	0x1FB6:  "\u0391\u0342",       // GREEK SMALL LETTER ALPHA WITH PERISPOMENI
	0x1FB7:  "\u0391\u0342\u0399", // GREEK SMALL LETTER ALPHA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1FBC:  "\u0391\u0399",       // GREEK CAPITAL LETTER ALPHA WITH PROSGEGRAMMENI
	0x1FC2:  "\u1FCA\u0399",       // GREEK SMALL LETTER ETA WITH VARIA AND YPOGEGRAMMENI
	0x1FC3:  "\u0397\u0399",       // GREEK SMALL LETTER ETA WITH YPOGEGRAMMENI
	0x1FC4:  "\u0389\u0399",       // GREEK SMALL LETTER ETA WITH OXIA AND YPOGEGRAMMENI
	0x1FC6:  "\u0397\u0342",       // GREEK SMALL LETTER ETA WITH PERISPOMENI
	0x1FC7:  "\u0397\u0342\u0399", // GREEK SMALL LETTER ETA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1FCC:  "\u0397\u0399",       // GREEK CAPITAL LETTER ETA WITH PROSGEGRAMMENI
	0x1FD2:  "\u0399\u0308\u0300", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND VARIA
	0x1FD3:  "\u0399\u0308\u0301", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND OXIA
	0x1FD6:  "\u0399\u0342",       // GREEK SMALL LETTER IOTA WITH PERISPOMENI
	0x1FD7:  "\u0399\u0308\u0342", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND PERISPOMENI
	0x1FE2:  "\u03A5\u0308\u0300", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND VARIA
	0x1FE3:  "\u03A5\u0308\u0301", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND OXIA
	0x1FE4:  "\u03A1\u0313",       // GREEK SMALL LETTER RHO WITH PSILI
	0x1FE6:  "\u03A5\u0342",       // GREEK SMALL LETTER UPSILON WITH PERISPOMENI
	0x1FE7:  "\u03A5\u0308\u0342", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND PERISPOMENI
	0x1FF2:  "\u1FFA\u0399",       // GREEK SMALL LETTER OMEGA WITH VARIA AND YPOGEGRAMMENI
	0x1FF3:  "\u03A9\u0399",       // GREEK SMALL LETTER OMEGA WITH YPOGEGRAMMENI
	0x1FF4:  "\u038F\u0399",       // GREEK SMALL LETTER OMEGA WITH OXIA AND YPOGEGRAMMENI
	0x1FF6:  "\u03A9\u0342",       // GREEK SMALL LETTER OMEGA WITH PERISPOMENI
	0x1FF7:  "\u03A9\u0342\u0399", // GREEK SMALL LETTER OMEGA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1FFC:  "\u03A9\u0399",       // GREEK CAPITAL LETTER OMEGA WITH PROSGEGRAMMENI
	0xA7CD:  "\uA7CC",             // LATIN SMALL LETTER S WITH DIAGONAL STROKE
	0xA7DB:  "\uA7DA",             // LATIN SMALL LETTER LAMBDA
	0xFB00:  "\u0046\u0046",       // LATIN SMALL LIGATURE FF
	0xFB01:  "\u0046\u0049",       // LATIN SMALL LIGATURE FI
	0xFB02:  "\u0046\u004C",       // LATIN SMALL LIGATURE FL
	0xFB03:  "\u0046\u0046\u0049", // LATIN SMALL LIGATURE FFI
	0xFB04:  "\u0046\u0046\u004C", // LATIN SMALL LIGATURE FFL
	0xFB05:  "\u0053\u0054",       // LATIN SMALL LIGATURE LONG S T
	0xFB06:  "\u0053\u0054",       // LATIN SMALL LIGATURE ST
	0xFB13:  "\u0544\u0546",       // ARMENIAN SMALL LIGATURE MEN NOW
	0xFB14:  "\u0544\u0535",       // ARMENIAN SMALL LIGATURE MEN ECH
	0xFB15:  "\u0544\u053B",       // ARMENIAN SMALL LIGATURE MEN INI
	0xFB16:  "\u054E\u0546",       // ARMENIAN SMALL LIGATURE VEW NOW
	0xFB17:  "\u0544\u053D",       // ARMENIAN SMALL LIGATURE MEN XEH
	0x10D70: "\U00010D50",         // GARAY SMALL LETTER A
	0x10D71: "\U00010D51",         // GARAY SMALL LETTER CA
	0x10D72: "\U00010D52",         // GARAY SMALL LETTER MA
	0x10D73: "\U00010D53",         // GARAY SMALL LETTER KA
	0x10D74: "\U00010D54",         // GARAY SMALL LETTER BA
	0x10D75: "\U00010D55",         // GARAY SMALL LETTER JA
	0x10D76: "\U00010D56",         // GARAY SMALL LETTER SA
	0x10D77: "\U00010D57",         // GARAY SMALL LETTER WA
	0x10D78: "\U00010D58",         // GARAY SMALL LETTER LA
	0x10D79: "\U00010D59",         // GARAY SMALL LETTER GA
	0x10D7A: "\U00010D5A",         // GARAY SMALL LETTER DA
	0x10D7B: "\U00010D5B",         // GARAY SMALL LETTER XA
	0x10D7C: "\U00010D5C",         // GARAY SMALL LETTER YA
	0x10D7D: "\U00010D5D",         // GARAY SMALL LETTER TA
	0x10D7E: "\U00010D5E",         // GARAY SMALL LETTER RA
	0x10D7F: "\U00010D5F",         // GARAY SMALL LETTER NYA
	0x10D80: "\U00010D60",         // GARAY SMALL LETTER FA
	0x10D81: "\U00010D61",         // GARAY SMALL LETTER NA
	0x10D82: "\U00010D62",         // GARAY SMALL LETTER PA
	0x10D83: "\U00010D63",         // GARAY SMALL LETTER HA
	0x10D84: "\U00010D64",         // GARAY SMALL LETTER OLD KA
	0x10D85: "\U00010D65",         // GARAY SMALL LETTER OLD NA
}

var pyLowerOverride = map[rune]string{
	0x0130:  "\u0069\u0307", // LATIN CAPITAL LETTER I WITH DOT ABOVE
	0x1C89:  "\u1C8A",       // CYRILLIC CAPITAL LETTER TJE
	0xA7CB:  "\u0264",       // LATIN CAPITAL LETTER RAMS HORN
	0xA7CC:  "\uA7CD",       // LATIN CAPITAL LETTER S WITH DIAGONAL STROKE
	0xA7DA:  "\uA7DB",       // LATIN CAPITAL LETTER LAMBDA
	0xA7DC:  "\u019B",       // LATIN CAPITAL LETTER LAMBDA WITH STROKE
	0x10D50: "\U00010D70",   // GARAY CAPITAL LETTER A
	0x10D51: "\U00010D71",   // GARAY CAPITAL LETTER CA
	0x10D52: "\U00010D72",   // GARAY CAPITAL LETTER MA
	0x10D53: "\U00010D73",   // GARAY CAPITAL LETTER KA
	0x10D54: "\U00010D74",   // GARAY CAPITAL LETTER BA
	0x10D55: "\U00010D75",   // GARAY CAPITAL LETTER JA
	0x10D56: "\U00010D76",   // GARAY CAPITAL LETTER SA
	0x10D57: "\U00010D77",   // GARAY CAPITAL LETTER WA
	0x10D58: "\U00010D78",   // GARAY CAPITAL LETTER LA
	0x10D59: "\U00010D79",   // GARAY CAPITAL LETTER GA
	0x10D5A: "\U00010D7A",   // GARAY CAPITAL LETTER DA
	0x10D5B: "\U00010D7B",   // GARAY CAPITAL LETTER XA
	0x10D5C: "\U00010D7C",   // GARAY CAPITAL LETTER YA
	0x10D5D: "\U00010D7D",   // GARAY CAPITAL LETTER TA
	0x10D5E: "\U00010D7E",   // GARAY CAPITAL LETTER RA
	0x10D5F: "\U00010D7F",   // GARAY CAPITAL LETTER NYA
	0x10D60: "\U00010D80",   // GARAY CAPITAL LETTER FA
	0x10D61: "\U00010D81",   // GARAY CAPITAL LETTER NA
	0x10D62: "\U00010D82",   // GARAY CAPITAL LETTER PA
	0x10D63: "\U00010D83",   // GARAY CAPITAL LETTER HA
	0x10D64: "\U00010D84",   // GARAY CAPITAL LETTER OLD KA
	0x10D65: "\U00010D85",   // GARAY CAPITAL LETTER OLD NA
}

var pyTitleOverride = map[rune]string{
	0x00DF:  "\u0053\u0073",       // LATIN SMALL LETTER SHARP S
	0x0149:  "\u02BC\u004E",       // LATIN SMALL LETTER N PRECEDED BY APOSTROPHE
	0x019B:  "\uA7DC",             // LATIN SMALL LETTER LAMBDA WITH STROKE
	0x01F0:  "\u004A\u030C",       // LATIN SMALL LETTER J WITH CARON
	0x0264:  "\uA7CB",             // LATIN SMALL LETTER RAMS HORN
	0x0390:  "\u0399\u0308\u0301", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND TONOS
	0x03B0:  "\u03A5\u0308\u0301", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND TONOS
	0x0587:  "\u0535\u0582",       // ARMENIAN SMALL LIGATURE ECH YIWN
	0x1C8A:  "\u1C89",             // CYRILLIC SMALL LETTER TJE
	0x1E96:  "\u0048\u0331",       // LATIN SMALL LETTER H WITH LINE BELOW
	0x1E97:  "\u0054\u0308",       // LATIN SMALL LETTER T WITH DIAERESIS
	0x1E98:  "\u0057\u030A",       // LATIN SMALL LETTER W WITH RING ABOVE
	0x1E99:  "\u0059\u030A",       // LATIN SMALL LETTER Y WITH RING ABOVE
	0x1E9A:  "\u0041\u02BE",       // LATIN SMALL LETTER A WITH RIGHT HALF RING
	0x1F50:  "\u03A5\u0313",       // GREEK SMALL LETTER UPSILON WITH PSILI
	0x1F52:  "\u03A5\u0313\u0300", // GREEK SMALL LETTER UPSILON WITH PSILI AND VARIA
	0x1F54:  "\u03A5\u0313\u0301", // GREEK SMALL LETTER UPSILON WITH PSILI AND OXIA
	0x1F56:  "\u03A5\u0313\u0342", // GREEK SMALL LETTER UPSILON WITH PSILI AND PERISPOMENI
	0x1FB2:  "\u1FBA\u0345",       // GREEK SMALL LETTER ALPHA WITH VARIA AND YPOGEGRAMMENI
	0x1FB4:  "\u0386\u0345",       // GREEK SMALL LETTER ALPHA WITH OXIA AND YPOGEGRAMMENI
	0x1FB6:  "\u0391\u0342",       // GREEK SMALL LETTER ALPHA WITH PERISPOMENI
	0x1FB7:  "\u0391\u0342\u0345", // GREEK SMALL LETTER ALPHA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1FC2:  "\u1FCA\u0345",       // GREEK SMALL LETTER ETA WITH VARIA AND YPOGEGRAMMENI
	0x1FC4:  "\u0389\u0345",       // GREEK SMALL LETTER ETA WITH OXIA AND YPOGEGRAMMENI
	0x1FC6:  "\u0397\u0342",       // GREEK SMALL LETTER ETA WITH PERISPOMENI
	0x1FC7:  "\u0397\u0342\u0345", // GREEK SMALL LETTER ETA WITH PERISPOMENI AND YPOGEGRAMMENI
	0x1FD2:  "\u0399\u0308\u0300", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND VARIA
	0x1FD3:  "\u0399\u0308\u0301", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND OXIA
	0x1FD6:  "\u0399\u0342",       // GREEK SMALL LETTER IOTA WITH PERISPOMENI
	0x1FD7:  "\u0399\u0308\u0342", // GREEK SMALL LETTER IOTA WITH DIALYTIKA AND PERISPOMENI
	0x1FE2:  "\u03A5\u0308\u0300", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND VARIA
	0x1FE3:  "\u03A5\u0308\u0301", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND OXIA
	0x1FE4:  "\u03A1\u0313",       // GREEK SMALL LETTER RHO WITH PSILI
	0x1FE6:  "\u03A5\u0342",       // GREEK SMALL LETTER UPSILON WITH PERISPOMENI
	0x1FE7:  "\u03A5\u0308\u0342", // GREEK SMALL LETTER UPSILON WITH DIALYTIKA AND PERISPOMENI
	0x1FF2:  "\u1FFA\u0345",       // GREEK SMALL LETTER OMEGA WITH VARIA AND YPOGEGRAMMENI
	0x1FF4:  "\u038F\u0345",       // GREEK SMALL LETTER OMEGA WITH OXIA AND YPOGEGRAMMENI
	0x1FF6:  "\u03A9\u0342",       // GREEK SMALL LETTER OMEGA WITH PERISPOMENI
	0x1FF7:  "\u03A9\u0342\u0345", // GREEK SMALL LETTER OMEGA WITH PERISPOMENI AND YPOGEGRAMMENI
	0xA7CD:  "\uA7CC",             // LATIN SMALL LETTER S WITH DIAGONAL STROKE
	0xA7DB:  "\uA7DA",             // LATIN SMALL LETTER LAMBDA
	0xFB00:  "\u0046\u0066",       // LATIN SMALL LIGATURE FF
	0xFB01:  "\u0046\u0069",       // LATIN SMALL LIGATURE FI
	0xFB02:  "\u0046\u006C",       // LATIN SMALL LIGATURE FL
	0xFB03:  "\u0046\u0066\u0069", // LATIN SMALL LIGATURE FFI
	0xFB04:  "\u0046\u0066\u006C", // LATIN SMALL LIGATURE FFL
	0xFB05:  "\u0053\u0074",       // LATIN SMALL LIGATURE LONG S T
	0xFB06:  "\u0053\u0074",       // LATIN SMALL LIGATURE ST
	0xFB13:  "\u0544\u0576",       // ARMENIAN SMALL LIGATURE MEN NOW
	0xFB14:  "\u0544\u0565",       // ARMENIAN SMALL LIGATURE MEN ECH
	0xFB15:  "\u0544\u056B",       // ARMENIAN SMALL LIGATURE MEN INI
	0xFB16:  "\u054E\u0576",       // ARMENIAN SMALL LIGATURE VEW NOW
	0xFB17:  "\u0544\u056D",       // ARMENIAN SMALL LIGATURE MEN XEH
	0x10D70: "\U00010D50",         // GARAY SMALL LETTER A
	0x10D71: "\U00010D51",         // GARAY SMALL LETTER CA
	0x10D72: "\U00010D52",         // GARAY SMALL LETTER MA
	0x10D73: "\U00010D53",         // GARAY SMALL LETTER KA
	0x10D74: "\U00010D54",         // GARAY SMALL LETTER BA
	0x10D75: "\U00010D55",         // GARAY SMALL LETTER JA
	0x10D76: "\U00010D56",         // GARAY SMALL LETTER SA
	0x10D77: "\U00010D57",         // GARAY SMALL LETTER WA
	0x10D78: "\U00010D58",         // GARAY SMALL LETTER LA
	0x10D79: "\U00010D59",         // GARAY SMALL LETTER GA
	0x10D7A: "\U00010D5A",         // GARAY SMALL LETTER DA
	0x10D7B: "\U00010D5B",         // GARAY SMALL LETTER XA
	0x10D7C: "\U00010D5C",         // GARAY SMALL LETTER YA
	0x10D7D: "\U00010D5D",         // GARAY SMALL LETTER TA
	0x10D7E: "\U00010D5E",         // GARAY SMALL LETTER RA
	0x10D7F: "\U00010D5F",         // GARAY SMALL LETTER NYA
	0x10D80: "\U00010D60",         // GARAY SMALL LETTER FA
	0x10D81: "\U00010D61",         // GARAY SMALL LETTER NA
	0x10D82: "\U00010D62",         // GARAY SMALL LETTER PA
	0x10D83: "\U00010D63",         // GARAY SMALL LETTER HA
	0x10D84: "\U00010D64",         // GARAY SMALL LETTER OLD KA
	0x10D85: "\U00010D65",         // GARAY SMALL LETTER OLD NA
}
GO_SOURCE_EOF

# Remove the Python implementation: no .py files may remain.
find /workspace/repo -name '*.py' -delete
find /workspace/repo -name '__pycache__' -type d -prune -exec rm -rf {} +

# The emptied titlecase/ folder would clash with the binary name `go build` picks.
find /workspace/repo -type d -empty -delete

cd /workspace/repo
gofmt -l . >/dev/null
go build -o /dev/null ./...
