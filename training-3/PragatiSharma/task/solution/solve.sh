#!/bin/sh
# Reference solution: replace the Python tree with a stdlib Go titlecase program.
set -eu
cd /workspace/repo

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode/utf8"
)

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 16*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	for in.Scan() {
		fmt.Fprintln(out, titlecase(in.Text(), true))
	}
	if err := in.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := out.Flush(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

type smallAlt struct {
	text   string
	optDot bool
}

var smallAlts = []smallAlt{
	{"a", false},
	{"an", false},
	{"and", false},
	{"as", false},
	{"at", false},
	{"but", false},
	{"by", false},
	{"en", false},
	{"for", false},
	{"if", false},
	{"in", false},
	{"of", false},
	{"on", false},
	{"or", false},
	{"the", false},
	{"to", false},
	{"v", true},
	{"via", false},
	{"vs", true},
}

var punct = map[rune]bool{}

func init() {
	for _, r := range "!\"#$%&'()*+,-./:;?@[\\]_`{|}~‒–—―‘“" {
		punct[r] = true
	}
}

func isPunct(r rune) bool { return punct[r] }

func isSubBreak(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func isASCIILetter(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z')
}

// pyUpperFirst is Python's word[0].upper() + word[1:].
func pyUpperFirst(s string) string {
	if s == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	return pyUpper(string(r)) + s[size:]
}

func boundary(rs []rune, i int) bool {
	prev := i > 0 && isPyWord(rs[i-1])
	next := i < len(rs) && isPyWord(rs[i])
	if i == 0 {
		return next
	}
	if i == len(rs) {
		return prev
	}
	return prev != next
}

func foldPrefix(rs []rune, i int, lit string, sensitive bool) (int, bool) {
	for _, want := range lit {
		if i >= len(rs) {
			return 0, false
		}
		got := rs[i]
		if sensitive {
			if got != want {
				return 0, false
			}
		} else if reFold(got) != want {
			return 0, false
		}
		i++
	}
	return i, true
}

func matchAltEnd(rs []rune, i int, alt smallAlt, boundaryAfter bool, sensitive bool) (int, bool) {
	base, ok := foldPrefix(rs, i, alt.text, sensitive)
	if !ok {
		return 0, false
	}
	if alt.optDot && base < len(rs) && rs[base] == '.' {
		end := base + 1
		if !boundaryAfter || boundary(rs, end) {
			return end, true
		}
	}
	if !boundaryAfter || boundary(rs, base) {
		return base, true
	}
	return 0, false
}

func isSmallWord(word string) bool {
	switch reFoldString(word) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for p := maxPunct; p >= 0; p-- {
		for _, alt := range smallAlts {
			end, ok := matchAltEnd(rs, p, alt, true, false)
			if !ok {
				continue
			}
			return string(rs[:p]) + pyCapitalize(string(rs[p:end])) + string(rs[end:])
		}
	}
	return word
}

func reachesEnd(rs []rune, pos int) (int, bool) {
	if pos == len(rs) {
		return pos, true
	}
	if pos+1 == len(rs) && isPunct(rs[pos]) {
		return pos + 1, true
	}
	return 0, false
}

func applySmallLast(word string) string {
	rs := []rune(word)
	for i := 0; i <= len(rs); i++ {
		if !boundary(rs, i) {
			continue
		}
		for _, alt := range smallAlts {
			base, ok := foldPrefix(rs, i, alt.text, false)
			if !ok {
				continue
			}
			if alt.optDot && base < len(rs) && rs[base] == '.' {
				if end, ok := reachesEnd(rs, base+1); ok {
					return string(rs[:i]) + pyCapitalize(string(rs[i:end]))
				}
			}
			if end, ok := reachesEnd(rs, base); ok {
				return string(rs[:i]) + pyCapitalize(string(rs[i:end]))
			}
		}
	}
	return word
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(rs) {
		if i+1 < len(rs) && isSubBreak(rs[i]) && rs[i+1] == ' ' {
			for _, alt := range smallAlts {
				end, ok := matchAltEnd(rs, i+2, alt, false, true)
				if !ok {
					continue
				}
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2 : end])))
				i = end
				goto next
			}
		}
		b.WriteRune(rs[i])
		i++
	next:
	}
	return b.String()
}

func hasInlinePeriod(word string) bool {
	rs := []rune(word)
	for i := 1; i+1 < len(rs); i++ {
		if rs[i] == '.' && isPyWord(rs[i-1]) && isPyWord(rs[i+1]) {
			return true
		}
	}
	return false
}

func hasUCElsewhere(word string) bool {
	rs := []rune(word)
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for p := 0; p <= maxPunct; p++ {
		rest := rs[p:]
		if len(rest) < 2 || !isASCIILetter(rest[0]) {
			continue
		}
		for _, r := range rest[1:] {
			if r >= 'A' && r <= 'Z' {
				return true
			}
			if !isASCIILetter(r) {
				break
			}
		}
	}
	return false
}

func capFirst(word string) string {
	rs := []rune(word)
	for i, r := range rs {
		if isPyWord(r) {
			for k := 0; k < i; k++ {
				if !isPunct(rs[k]) {
					return word
				}
			}
			return pyUpper(string(rs[:i+1])) + string(rs[i+1:])
		}
		if !isPunct(r) {
			return word
		}
	}
	return word
}

func isAllConsonants(word string) bool {
	rs := []rune(word)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		r = reFold(r)
		if r < 'a' || r > 'z' {
			return false
		}
		switch r {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

func isInitials(word string) bool {
	if word == "" {
		return false
	}
	var match func(int) bool
	match = func(i int) bool {
		if i == len(word) {
			return true
		}
		if i+2 <= len(word) && word[i] >= 'A' && word[i] <= 'Z' && word[i+1] == '.' {
			if match(i + 2) {
				return true
			}
		}
		if i+3 <= len(word) && word[i] >= 'A' && word[i] <= 'Z' && word[i+1] == '.' && word[i+2] >= 'A' && word[i+2] <= 'Z' {
			if match(i + 3) {
				return true
			}
		}
		return false
	}
	return match(0)
}

func isAposWord(word string) bool {
	rs := []rune(word)
	if len(rs) < 3 {
		return false
	}
	switch reFold(rs[0]) {
	case 'd', 'l', 'o':
	default:
		return false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return false
	}
	rest := rs[2:]
	if len(rest) == 0 {
		return false
	}
	if allPyWord(rest) {
		return true
	}
	// (?:['s]{2})? can consume two trailing class characters that [\w] would
	// otherwise take, so the word run must give those two characters back.
	if len(rest) >= 3 && allPyWord(rest[:len(rest)-2]) && isAposTail(rest[len(rest)-2]) && isAposTail(rest[len(rest)-1]) {
		return true
	}
	return false
}

func allPyWord(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if !isPyWord(r) {
			return false
		}
	}
	return true
}

func isAposTail(r rune) bool {
	return r == '\'' || reFold(r) == 's'
}

func rewriteApos(word string) string {
	rs := []rune(word)
	var first string
	switch rs[0] {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		first = pyUpper(string(rs[0]))
	default:
		first = pyLower(string(rs[0]))
	}
	return first + string(rs[1]) + pyUpper(string(rs[2])) + string(rs[3:])
}

func isHonorific(word string) bool {
	switch reFoldString(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func splitMc(word string) (string, string, bool) {
	var prefix string
	switch {
	case strings.HasPrefix(word, "Mc"), strings.HasPrefix(word, "mc"), strings.HasPrefix(word, "MC"):
		prefix = word[:2]
	default:
		return "", "", false
	}
	rest := word[len(prefix):]
	r, _ := utf8.DecodeRuneInString(rest)
	if r == utf8.RuneError && rest == "" {
		return "", "", false
	}
	if !isPyWord(r) || utf8.RuneCountInString(rest) < 2 {
		return "", "", false
	}
	return prefix, rest, true
}

func splitKeepSpace(line string) (words, spaces []string) {
	if line == "" {
		return []string{""}, nil
	}
	rs := []rune(line)
	i := 0
	for {
		j := i
		for j < len(rs) && !isPySpace(rs[j]) {
			j++
		}
		words = append(words, string(rs[i:j]))
		if j >= len(rs) {
			return words, spaces
		}
		spaces = append(spaces, string(rs[j:j+1]))
		i = j + 1
		if i == len(rs) {
			words = append(words, "")
			return words, spaces
		}
	}
}

func joinWords(words, spaces []string) string {
	n := len(words) + len(spaces)
	parts := make([]string, n)
	wi, si := 0, 0
	for i := 0; i < n; i++ {
		if i%2 == 0 {
			parts[i] = words[wi]
			wi++
		} else {
			parts[i] = spaces[si]
			si++
		}
	}
	return strings.Join(parts, "")
}

func splitNewlines(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	start := 0
	for i := 0; i < len(text); i++ {
		if text[i] == '\n' || text[i] == '\r' {
			lines = append(lines, text[start:i])
			for i < len(text) && (text[i] == '\n' || text[i] == '\r') {
				i++
			}
			start = i
			i--
		}
	}
	lines = append(lines, text[start:])
	return lines
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = titlecaseLine(line, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := pyUpper(line) == line
	words, spaces := splitKeepSpace(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titleWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(joinWords(tc, spaces))
}

func titleWord(word string, allCaps bool) string {
	if allCaps && isInitials(word) {
		return word
	}
	if isAposWord(word) {
		return rewriteApos(word)
	}
	if prefix, rest, ok := splitMc(word); ok {
		return pyCapitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		return pyUpperFirst(word)
	}
	if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return pyLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = titlecase(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = titlecase(part, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = pyLower(word)
	}
	if isAllConsonants(word) {
		return pyUpper(word)
	}
	return capFirst(word)
}
EOF

cat > pycase.go << 'EOF'
package main

import (
	"strings"
	"unicode"
)

// Python string casing, as the original titlecase() uses it.
//
// Python's str.upper(), str.lower() and str.capitalize() apply the full Unicode
// case mappings, so one character can become several: "ﬁ".upper() is "FI",
// "ß".upper() is "SS" and "İ".lower() is "i" followed by U+0307 COMBINING DOT
// ABOVE. str.lower() also turns a capital sigma at the end of a word into "ς".
// Go's strings.ToUpper and strings.ToLower only apply the one-to-one simple
// mappings. These helpers use Go's mappings plus the exception tables in
// pycase_tables.go, which are generated from the reference interpreter.

// pyUpper is Python's str.upper().
func pyUpper(s string) string {
	var b strings.Builder
	b.Grow(len(s))
	for _, r := range s {
		if m, ok := pyUpperExceptions[r]; ok {
			b.WriteString(m)
		} else {
			b.WriteRune(unicode.ToUpper(r))
		}
	}
	return b.String()
}

// pyLower is Python's str.lower().
func pyLower(s string) string {
	rs := []rune(s)
	var b strings.Builder
	b.Grow(len(s))
	for i := range rs {
		writePyLower(&b, rs, i)
	}
	return b.String()
}

// pyCapitalize is Python's str.capitalize(): the first character in title
// case and the rest in lower case.
func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return ""
	}
	var b strings.Builder
	b.Grow(len(s))
	if m, ok := pyTitleExceptions[rs[0]]; ok {
		b.WriteString(m)
	} else {
		b.WriteRune(unicode.ToTitle(rs[0]))
	}
	for i := 1; i < len(rs); i++ {
		writePyLower(&b, rs, i)
	}
	return b.String()
}

// writePyLower writes the lower case of rs[i]. A capital sigma depends on the
// characters around it, so the whole string is passed in.
func writePyLower(b *strings.Builder, rs []rune, i int) {
	r := rs[i]
	if r == 'Σ' {
		if finalSigma(rs, i) {
			b.WriteRune('ς')
		} else {
			b.WriteRune('σ')
		}
		return
	}
	if m, ok := pyLowerExceptions[r]; ok {
		b.WriteString(m)
	} else {
		b.WriteRune(unicode.ToLower(r))
	}
}

// finalSigma applies CPython's Final_Sigma test to the capital sigma at rs[i]:
// skipping case-ignorable characters, a cased character comes before it and no
// cased character comes after it.
func finalSigma(rs []rune, i int) bool {
	j := i - 1
	for j >= 0 && sigmaClass(rs[j]) == caseIgnorable {
		j--
	}
	if j < 0 || sigmaClass(rs[j]) != cased {
		return false
	}
	for j = i + 1; j < len(rs) && sigmaClass(rs[j]) == caseIgnorable; j++ {
	}
	return j == len(rs) || sigmaClass(rs[j]) != cased
}

const (
	caseOther uint8 = iota
	cased
	caseIgnorable
)

// wordBreakMid lists the Word_Break MidLetter, MidNumLet and Single_Quote
// characters. Unicode counts them as Case_Ignorable.
const wordBreakMid = "'.:··՟״‘’․‧︓﹒﹕＇．："

// sigmaClass classifies r the way CPython's Final_Sigma test does: it checks
// Case_Ignorable first, then Cased.
func sigmaClass(r rune) uint8 {
	if c, ok := pySigmaClassExceptions[r]; ok {
		return c
	}
	if unicode.In(r, unicode.Mn, unicode.Me, unicode.Cf, unicode.Lm, unicode.Sk) ||
		strings.ContainsRune(wordBreakMid, r) {
		return caseIgnorable
	}
	if unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r) ||
		unicode.In(r, unicode.Other_Lowercase, unicode.Other_Uppercase) {
		return cased
	}
	return caseOther
}
EOF

cat > pycase_tables.go << 'EOF'
// Code generated by mkcasing.py from Python 3.14.2 (Unicode 16.0.0)
// and Go's unicode package (Unicode 15.0.0). DO NOT EDIT.

package main

// pyUpperExceptions: str.upper() of one character, where it differs from unicode.ToUpper.
var pyUpperExceptions = map[rune]string{
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

// pyLowerExceptions: str.lower() of one character, where it differs from unicode.ToLower.
var pyLowerExceptions = map[rune]string{
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

// pyTitleExceptions: the first character of str.capitalize(), where it differs from unicode.ToTitle.
var pyTitleExceptions = map[rune]string{
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

// pySigmaClassExceptions: characters whose Case_Ignorable/Cased class in the
// reference differs from the rule in sigmaClass.
var pySigmaClassExceptions = map[rune]uint8{
	0x0897:  caseIgnorable, // ARABIC PEPET
	0x1C89:  cased,         // CYRILLIC CAPITAL LETTER TJE
	0x1C8A:  cased,         // CYRILLIC SMALL LETTER TJE
	0xA7CB:  cased,         // LATIN CAPITAL LETTER RAMS HORN
	0xA7CC:  cased,         // LATIN CAPITAL LETTER S WITH DIAGONAL STROKE
	0xA7CD:  cased,         // LATIN SMALL LETTER S WITH DIAGONAL STROKE
	0xA7DA:  cased,         // LATIN CAPITAL LETTER LAMBDA
	0xA7DB:  cased,         // LATIN SMALL LETTER LAMBDA
	0xA7DC:  cased,         // LATIN CAPITAL LETTER LAMBDA WITH STROKE
	0x10D4E: caseIgnorable, // GARAY VOWEL LENGTH MARK
	0x10D50: cased,         // GARAY CAPITAL LETTER A
	0x10D51: cased,         // GARAY CAPITAL LETTER CA
	0x10D52: cased,         // GARAY CAPITAL LETTER MA
	0x10D53: cased,         // GARAY CAPITAL LETTER KA
	0x10D54: cased,         // GARAY CAPITAL LETTER BA
	0x10D55: cased,         // GARAY CAPITAL LETTER JA
	0x10D56: cased,         // GARAY CAPITAL LETTER SA
	0x10D57: cased,         // GARAY CAPITAL LETTER WA
	0x10D58: cased,         // GARAY CAPITAL LETTER LA
	0x10D59: cased,         // GARAY CAPITAL LETTER GA
	0x10D5A: cased,         // GARAY CAPITAL LETTER DA
	0x10D5B: cased,         // GARAY CAPITAL LETTER XA
	0x10D5C: cased,         // GARAY CAPITAL LETTER YA
	0x10D5D: cased,         // GARAY CAPITAL LETTER TA
	0x10D5E: cased,         // GARAY CAPITAL LETTER RA
	0x10D5F: cased,         // GARAY CAPITAL LETTER NYA
	0x10D60: cased,         // GARAY CAPITAL LETTER FA
	0x10D61: cased,         // GARAY CAPITAL LETTER NA
	0x10D62: cased,         // GARAY CAPITAL LETTER PA
	0x10D63: cased,         // GARAY CAPITAL LETTER HA
	0x10D64: cased,         // GARAY CAPITAL LETTER OLD KA
	0x10D65: cased,         // GARAY CAPITAL LETTER OLD NA
	0x10D69: caseIgnorable, // GARAY VOWEL SIGN E
	0x10D6A: caseIgnorable, // GARAY CONSONANT GEMINATION MARK
	0x10D6B: caseIgnorable, // GARAY COMBINING DOT ABOVE
	0x10D6C: caseIgnorable, // GARAY COMBINING DOUBLE DOT ABOVE
	0x10D6D: caseIgnorable, // GARAY CONSONANT NASALIZATION MARK
	0x10D6F: caseIgnorable, // GARAY REDUPLICATION MARK
	0x10D70: cased,         // GARAY SMALL LETTER A
	0x10D71: cased,         // GARAY SMALL LETTER CA
	0x10D72: cased,         // GARAY SMALL LETTER MA
	0x10D73: cased,         // GARAY SMALL LETTER KA
	0x10D74: cased,         // GARAY SMALL LETTER BA
	0x10D75: cased,         // GARAY SMALL LETTER JA
	0x10D76: cased,         // GARAY SMALL LETTER SA
	0x10D77: cased,         // GARAY SMALL LETTER WA
	0x10D78: cased,         // GARAY SMALL LETTER LA
	0x10D79: cased,         // GARAY SMALL LETTER GA
	0x10D7A: cased,         // GARAY SMALL LETTER DA
	0x10D7B: cased,         // GARAY SMALL LETTER XA
	0x10D7C: cased,         // GARAY SMALL LETTER YA
	0x10D7D: cased,         // GARAY SMALL LETTER TA
	0x10D7E: cased,         // GARAY SMALL LETTER RA
	0x10D7F: cased,         // GARAY SMALL LETTER NYA
	0x10D80: cased,         // GARAY SMALL LETTER FA
	0x10D81: cased,         // GARAY SMALL LETTER NA
	0x10D82: cased,         // GARAY SMALL LETTER PA
	0x10D83: cased,         // GARAY SMALL LETTER HA
	0x10D84: cased,         // GARAY SMALL LETTER OLD KA
	0x10D85: cased,         // GARAY SMALL LETTER OLD NA
	0x10EFC: caseIgnorable, // ARABIC COMBINING ALEF OVERLAY
	0x113BB: caseIgnorable, // TULU-TIGALARI VOWEL SIGN U
	0x113BC: caseIgnorable, // TULU-TIGALARI VOWEL SIGN UU
	0x113BD: caseIgnorable, // TULU-TIGALARI VOWEL SIGN VOCALIC R
	0x113BE: caseIgnorable, // TULU-TIGALARI VOWEL SIGN VOCALIC RR
	0x113BF: caseIgnorable, // TULU-TIGALARI VOWEL SIGN VOCALIC L
	0x113C0: caseIgnorable, // TULU-TIGALARI VOWEL SIGN VOCALIC LL
	0x113CE: caseIgnorable, // TULU-TIGALARI SIGN VIRAMA
	0x113D0: caseIgnorable, // TULU-TIGALARI CONJOINER
	0x113D2: caseIgnorable, // TULU-TIGALARI GEMINATION MARK
	0x113E1: caseIgnorable, // TULU-TIGALARI VEDIC TONE SVARITA
	0x113E2: caseIgnorable, // TULU-TIGALARI VEDIC TONE ANUDATTA
	0x1171E: caseOther,     // AHOM CONSONANT SIGN MEDIAL RA
	0x11F5A: caseIgnorable, // KAWI SIGN NUKTA
	0x1611E: caseIgnorable, // GURUNG KHEMA VOWEL SIGN AA
	0x1611F: caseIgnorable, // GURUNG KHEMA VOWEL SIGN I
	0x16120: caseIgnorable, // GURUNG KHEMA VOWEL SIGN II
	0x16121: caseIgnorable, // GURUNG KHEMA VOWEL SIGN U
	0x16122: caseIgnorable, // GURUNG KHEMA VOWEL SIGN UU
	0x16123: caseIgnorable, // GURUNG KHEMA VOWEL SIGN E
	0x16124: caseIgnorable, // GURUNG KHEMA VOWEL SIGN EE
	0x16125: caseIgnorable, // GURUNG KHEMA VOWEL SIGN AI
	0x16126: caseIgnorable, // GURUNG KHEMA VOWEL SIGN O
	0x16127: caseIgnorable, // GURUNG KHEMA VOWEL SIGN OO
	0x16128: caseIgnorable, // GURUNG KHEMA VOWEL SIGN AU
	0x16129: caseIgnorable, // GURUNG KHEMA VOWEL LENGTH MARK
	0x1612D: caseIgnorable, // GURUNG KHEMA SIGN ANUSVARA
	0x1612E: caseIgnorable, // GURUNG KHEMA CONSONANT SIGN MEDIAL RA
	0x1612F: caseIgnorable, // GURUNG KHEMA SIGN THOLHOMA
	0x16D40: caseIgnorable, // KIRAT RAI SIGN ANUSVARA
	0x16D41: caseIgnorable, // KIRAT RAI SIGN TONPI
	0x16D42: caseIgnorable, // KIRAT RAI SIGN VISARGA
	0x16D6B: caseIgnorable, // KIRAT RAI SIGN VIRAMA
	0x16D6C: caseIgnorable, // KIRAT RAI SIGN SAAT
	0x1E5EE: caseIgnorable, // OL ONAL SIGN MU
	0x1E5EF: caseIgnorable, // OL ONAL SIGN IKIR
}
EOF

cat > pyregex.go << 'EOF'
package main

import (
	"strings"
	"unicode"
)

// Character classes of Python's re module for str patterns, as the original's
// regexes use them. Python 3.14 uses Unicode 16.0, one version ahead of Go's
// unicode package, and its \s also includes U+001C to U+001F. The generated
// differences are in pyregex_tables.go.

// isPyWord is \w: str.isalnum() or '_'.
func isPyWord(r rune) bool {
	if unicode.Is(pyWordAdded, r) {
		return true
	}
	if unicode.Is(pyWordRemoved, r) {
		return false
	}
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

// isPySpace is \s: str.isspace().
func isPySpace(r rune) bool {
	if unicode.Is(pySpaceAdded, r) {
		return true
	}
	if unicode.Is(pySpaceRemoved, r) {
		return false
	}
	return unicode.IsSpace(r)
}

// reFold returns the lower-case ASCII letter that r matches under
// re.IGNORECASE, or r itself if it matches none. Besides A to Z, this covers
// İ and ı (i), ſ (s) and the Kelvin sign (k).
func reFold(r rune) rune {
	if r >= 'A' && r <= 'Z' {
		return r + ('a' - 'A')
	}
	if f, ok := pyIgnoreCaseASCII[r]; ok {
		return f
	}
	return r
}

// reFoldString applies reFold to every character of s.
func reFoldString(s string) string {
	var b strings.Builder
	b.Grow(len(s))
	for _, r := range s {
		b.WriteRune(reFold(r))
	}
	return b.String()
}
EOF

cat > pyregex_tables.go << 'EOF'
// Code generated by mkclasses.py from Python 3.14.2 (Unicode 16.0.0)
// and Go's unicode package (Unicode 15.0.0). DO NOT EDIT.

package main

import "unicode"

// pyWordAdded: \w in Python but not r == '_' || IsLetter || IsNumber in Go (5004 code points)
var pyWordAdded = &unicode.RangeTable{
	R16: []unicode.Range16{
		{Lo: 0x1C89, Hi: 0x1C8A, Stride: 1},
		{Lo: 0xA7CB, Hi: 0xA7CD, Stride: 1},
		{Lo: 0xA7DA, Hi: 0xA7DC, Stride: 1},
	},
	R32: []unicode.Range32{
		{Lo: 0x105C0, Hi: 0x105F3, Stride: 1},
		{Lo: 0x10D40, Hi: 0x10D65, Stride: 1},
		{Lo: 0x10D6F, Hi: 0x10D85, Stride: 1},
		{Lo: 0x10EC2, Hi: 0x10EC4, Stride: 1},
		{Lo: 0x11380, Hi: 0x11389, Stride: 1},
		{Lo: 0x1138B, Hi: 0x1138B, Stride: 1},
		{Lo: 0x1138E, Hi: 0x1138E, Stride: 1},
		{Lo: 0x11390, Hi: 0x113B5, Stride: 1},
		{Lo: 0x113B7, Hi: 0x113B7, Stride: 1},
		{Lo: 0x113D1, Hi: 0x113D1, Stride: 1},
		{Lo: 0x113D3, Hi: 0x113D3, Stride: 1},
		{Lo: 0x116D0, Hi: 0x116E3, Stride: 1},
		{Lo: 0x11BC0, Hi: 0x11BE0, Stride: 1},
		{Lo: 0x11BF0, Hi: 0x11BF9, Stride: 1},
		{Lo: 0x13460, Hi: 0x143FA, Stride: 1},
		{Lo: 0x16100, Hi: 0x1611D, Stride: 1},
		{Lo: 0x16130, Hi: 0x16139, Stride: 1},
		{Lo: 0x16D40, Hi: 0x16D6C, Stride: 1},
		{Lo: 0x16D70, Hi: 0x16D79, Stride: 1},
		{Lo: 0x18CFF, Hi: 0x18CFF, Stride: 1},
		{Lo: 0x1CCF0, Hi: 0x1CCF9, Stride: 1},
		{Lo: 0x1E5D0, Hi: 0x1E5ED, Stride: 1},
		{Lo: 0x1E5F0, Hi: 0x1E5FA, Stride: 1},
		{Lo: 0x2EBF0, Hi: 0x2EE5D, Stride: 1},
	},
}

// pyWordRemoved: IsLetter or IsNumber in Go but not \w in Python (0 code points)
var pyWordRemoved = &unicode.RangeTable{}

// pySpaceAdded: \s in Python but not unicode.IsSpace in Go (4 code points)
var pySpaceAdded = &unicode.RangeTable{
	R16: []unicode.Range16{
		{Lo: 0x001C, Hi: 0x001F, Stride: 1},
	},
	LatinOffset: 1,
}

// pySpaceRemoved: unicode.IsSpace in Go but not \s in Python (0 code points)
var pySpaceRemoved = &unicode.RangeTable{}

// pyIgnoreCaseASCII: non-ASCII characters that a lower-case ASCII letter in a
// pattern matches under re.IGNORECASE.
var pyIgnoreCaseASCII = map[rune]rune{
	0x0130: 'i', // LATIN CAPITAL LETTER I WITH DOT ABOVE
	0x0131: 'i', // LATIN SMALL LETTER DOTLESS I
	0x017F: 's', // LATIN SMALL LETTER LONG S
	0x212A: 'k', // KELVIN SIGN
}
EOF

find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -mindepth 1 -type d -empty -delete
go build ./...
