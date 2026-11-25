// Command titlecase reads one title per line on standard input and writes the
// titlecased result on standard output, matching python-titlecase 2.4.1 with
// the optional `regex` package absent (the standard-library `re` fallback).
package main

import (
	"io"
	"os"
	"strings"
	"unicode"
)

// upperExpand holds Python's full (multi-character) uppercase mappings.
// Simple one-rune mappings are handled with unicode.ToUpper.
var upperExpand = map[rune]string{
	0x00DF: "SS",
	0x0149: "\u02bcN",
	0x01F0: "J\u030c",
	0x0390: "\u0399\u0308\u0301",
	0x03B0: "\u03a5\u0308\u0301",
	0x0587: "\u0535\u0552",
	0x1E96: "H\u0331",
	0x1E97: "T\u0308",
	0x1E98: "W\u030a",
	0x1E99: "Y\u030a",
	0x1E9A: "A\u02be",
	0x1F50: "\u03a5\u0313",
	0x1F52: "\u03a5\u0313\u0300",
	0x1F54: "\u03a5\u0313\u0301",
	0x1F56: "\u03a5\u0313\u0342",
	0x1F80: "\u1f08\u0399",
	0x1F81: "\u1f09\u0399",
	0x1F82: "\u1f0a\u0399",
	0x1F83: "\u1f0b\u0399",
	0x1F84: "\u1f0c\u0399",
	0x1F85: "\u1f0d\u0399",
	0x1F86: "\u1f0e\u0399",
	0x1F87: "\u1f0f\u0399",
	0x1F88: "\u1f08\u0399",
	0x1F89: "\u1f09\u0399",
	0x1F8A: "\u1f0a\u0399",
	0x1F8B: "\u1f0b\u0399",
	0x1F8C: "\u1f0c\u0399",
	0x1F8D: "\u1f0d\u0399",
	0x1F8E: "\u1f0e\u0399",
	0x1F8F: "\u1f0f\u0399",
	0x1F90: "\u1f28\u0399",
	0x1F91: "\u1f29\u0399",
	0x1F92: "\u1f2a\u0399",
	0x1F93: "\u1f2b\u0399",
	0x1F94: "\u1f2c\u0399",
	0x1F95: "\u1f2d\u0399",
	0x1F96: "\u1f2e\u0399",
	0x1F97: "\u1f2f\u0399",
	0x1F98: "\u1f28\u0399",
	0x1F99: "\u1f29\u0399",
	0x1F9A: "\u1f2a\u0399",
	0x1F9B: "\u1f2b\u0399",
	0x1F9C: "\u1f2c\u0399",
	0x1F9D: "\u1f2d\u0399",
	0x1F9E: "\u1f2e\u0399",
	0x1F9F: "\u1f2f\u0399",
	0x1FA0: "\u1f68\u0399",
	0x1FA1: "\u1f69\u0399",
	0x1FA2: "\u1f6a\u0399",
	0x1FA3: "\u1f6b\u0399",
	0x1FA4: "\u1f6c\u0399",
	0x1FA5: "\u1f6d\u0399",
	0x1FA6: "\u1f6e\u0399",
	0x1FA7: "\u1f6f\u0399",
	0x1FA8: "\u1f68\u0399",
	0x1FA9: "\u1f69\u0399",
	0x1FAA: "\u1f6a\u0399",
	0x1FAB: "\u1f6b\u0399",
	0x1FAC: "\u1f6c\u0399",
	0x1FAD: "\u1f6d\u0399",
	0x1FAE: "\u1f6e\u0399",
	0x1FAF: "\u1f6f\u0399",
	0x1FB2: "\u1fba\u0399",
	0x1FB3: "\u0391\u0399",
	0x1FB4: "\u0386\u0399",
	0x1FB6: "\u0391\u0342",
	0x1FB7: "\u0391\u0342\u0399",
	0x1FBC: "\u0391\u0399",
	0x1FC2: "\u1fca\u0399",
	0x1FC3: "\u0397\u0399",
	0x1FC4: "\u0389\u0399",
	0x1FC6: "\u0397\u0342",
	0x1FC7: "\u0397\u0342\u0399",
	0x1FCC: "\u0397\u0399",
	0x1FD2: "\u0399\u0308\u0300",
	0x1FD3: "\u0399\u0308\u0301",
	0x1FD6: "\u0399\u0342",
	0x1FD7: "\u0399\u0308\u0342",
	0x1FE2: "\u03a5\u0308\u0300",
	0x1FE3: "\u03a5\u0308\u0301",
	0x1FE4: "\u03a1\u0313",
	0x1FE6: "\u03a5\u0342",
	0x1FE7: "\u03a5\u0308\u0342",
	0x1FF2: "\u1ffa\u0399",
	0x1FF3: "\u03a9\u0399",
	0x1FF4: "\u038f\u0399",
	0x1FF6: "\u03a9\u0342",
	0x1FF7: "\u03a9\u0342\u0399",
	0x1FFC: "\u03a9\u0399",
	0xFB00: "FF",
	0xFB01: "FI",
	0xFB02: "FL",
	0xFB03: "FFI",
	0xFB04: "FFL",
	0xFB05: "ST",
	0xFB06: "ST",
	0xFB13: "\u0544\u0546",
	0xFB14: "\u0544\u0535",
	0xFB15: "\u0544\u053b",
	0xFB16: "\u054e\u0546",
	0xFB17: "\u0544\u053d",
}

// lowerExpand holds Python's full (multi-character) lowercase mappings.
var lowerExpand = map[rune]string{
	0x0130: "i\u0307",
}

// PUNCT from python-titlecase: `!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~`
const punctChars = "!\"\u201c#$%&'\u2018()*+,\\-–‒—―./:;?@[\\]_`{|}~"

var punctSet = func() map[rune]bool {
	set := make(map[rune]bool, len(punctChars))
	for _, r := range punctChars {
		set[r] = true
	}
	return set
}()

// SMALL alternatives in source order. `v\.?` is expanded greedily as `v.`, `v`
// and `vs\.?` as `vs.`, `vs`.
var smallOrder = func() [][]rune {
	words := []string{
		"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
	}
	out := make([][]rune, len(words))
	for i, word := range words {
		out[i] = []rune(word)
	}
	return out
}()

var smallWordSet = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

var consonantSet = map[rune]bool{
	'b': true, 'c': true, 'd': true, 'f': true, 'g': true, 'h': true,
	'j': true, 'k': true, 'l': true, 'm': true, 'n': true, 'p': true,
	'q': true, 'r': true, 's': true, 't': true, 'v': true, 'w': true,
	'x': true, 'z': true,
}

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	lines := splitLines(string(data))
	processed := make([]string, len(lines))
	for i, line := range lines {
		processed[i] = titlecaseLine(line, true)
	}
	_, _ = os.Stdout.WriteString(strings.Join(processed, "\n"))
}

// splitLines mirrors re.split('[\r\n]+', text): runs of CR/LF separate lines and
// a trailing run leaves one final empty element.
func splitLines(text string) []string {
	var lines []string
	start := 0
	for i := 0; i < len(text); {
		if text[i] == '\n' || text[i] == '\r' {
			lines = append(lines, text[start:i])
			for i < len(text) && (text[i] == '\n' || text[i] == '\r') {
				i++
			}
			start = i
			continue
		}
		i++
	}
	return append(lines, text[start:])
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := pyUpper(line) == line

	var words []string
	var spaces []string
	runes := []rune(line)
	start := 0
	for i, r := range runes {
		if isPythonSpace(r) {
			words = append(words, string(runes[start:i]))
			spaces = append(spaces, string(r))
			start = i + 1
		}
	}
	words = append(words, string(runes[start:]))

	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titlecaseWord(word, allCaps)
	}

	if smallFirstLast && len(tc) > 0 {
		tc[0] = smallFirst(tc[0])
		tc[len(tc)-1] = smallLast(tc[len(tc)-1])
	}

	var joined strings.Builder
	for i := range tc {
		joined.WriteString(tc[i])
		if i < len(spaces) {
			joined.WriteString(spaces[i])
		}
	}
	return subphrase(joined.String())
}

func titlecaseWord(word string, allCaps bool) string {
	runes := []rune(word)

	if allCaps && ucInitials(runes) {
		return word
	}
	if transformed, ok := aposSecond(runes); ok {
		return transformed
	}
	if isMacMc(runes) {
		return "Mc" + titlecaseLine(string(runes[2:]), true)
	}
	if isHonorific(runes) {
		return pyUpperRune(runes[0]) + string(runes[1:])
	}
	if hasInlinePeriod(runes) || (!allCaps && ucElsewhere(runes)) {
		return word
	}
	if isSmallWord(word) {
		return pyLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i := range parts {
			parts[i] = titlecaseLine(parts[i], false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i := range parts {
			parts[i] = titlecaseLine(parts[i], false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = pyLower(word)
		runes = []rune(word)
	}
	if len(runes) > 2 && allConsonants(runes) {
		return pyUpper(word)
	}
	return capFirst(word)
}

// ucInitials implements ^(?:[A-Z]\.|[A-Z]\.[A-Z])+$.
func ucInitials(r []rune) bool {
	n := len(r)
	ok := make([]bool, n+1)
	ok[n] = true
	for i := n - 1; i >= 0; i-- {
		if i+1 < n && isUpperASCII(r[i]) && r[i+1] == '.' && ok[i+2] {
			ok[i] = true
			continue
		}
		if i+2 < n && isUpperASCII(r[i]) && r[i+1] == '.' && isUpperASCII(r[i+2]) && ok[i+3] {
			ok[i] = true
		}
	}
	return ok[0]
}

// aposSecond implements ^[dol]['‘][\w]+(?:['s]{2})?$ with re.I.
func aposSecond(r []rune) (string, bool) {
	n := len(r)
	if n < 3 {
		return "", false
	}
	first := foldASCII(r[0])
	if first != 'd' && first != 'o' && first != 'l' {
		return "", false
	}
	if r[1] != '\'' && r[1] != '\u2018' {
		return "", false
	}
	i := 2
	for i < n && isWord(r[i]) {
		i++
	}
	if i == 2 {
		return "", false
	}
	rest := r[i:]
	if len(rest) != 0 && (len(rest) != 2 || !isAposSuffix(rest)) {
		return "", false
	}

	var b strings.Builder
	if first == 'o' {
		b.WriteString(pyUpperRune(r[0]))
	} else {
		b.WriteString(pyLowerRune(r[0]))
	}
	b.WriteRune(r[1])
	b.WriteString(pyUpperRune(r[2]))
	b.WriteString(string(r[3:]))
	return b.String(), true
}

func isAposSuffix(r []rune) bool {
	for _, c := range r {
		if c != '\'' && foldASCII(c) != 's' {
			return false
		}
	}
	return true
}

// isMacMc implements ^([Mm]c|MC)(\w.+).
func isMacMc(r []rune) bool {
	if len(r) < 4 {
		return false
	}
	if !((r[0] == 'M' || r[0] == 'm') && r[1] == 'c') && !(r[0] == 'M' && r[1] == 'C') {
		return false
	}
	return isWord(r[2])
}

// isHonorific implements ^((m((rs?)|s))|Dr)$ with re.I.
func isHonorific(r []rune) bool {
	var b strings.Builder
	for _, c := range r {
		b.WriteRune(foldASCII(c))
	}
	switch b.String() {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

// hasInlinePeriod implements [\w][.][\w] search.
func hasInlinePeriod(r []rune) bool {
	for i := 0; i+2 < len(r); i++ {
		if isWord(r[i]) && r[i+1] == '.' && isWord(r[i+2]) {
			return true
		}
	}
	return false
}

// ucElsewhere implements [PUNCT]*?[a-zA-Z]+[A-Z]+? at the start of the word.
func ucElsewhere(r []rune) bool {
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	j := i
	for j < len(r) && isASCIILetter(r[j]) {
		j++
	}
	if j-i < 2 {
		return false
	}
	for k := i + 1; k < j; k++ {
		if isUpperASCII(r[k]) {
			return true
		}
	}
	return false
}

func isSmallWord(word string) bool {
	var b strings.Builder
	for _, r := range word {
		b.WriteRune(foldASCII(r))
	}
	return smallWordSet[b.String()]
}

// smallFirst implements ^([PUNCT]*)(small)\b with re.I.
func smallFirst(word string) string {
	r := []rune(word)
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	n := matchSmallBoundary(r, i)
	if n == 0 {
		return word
	}
	return string(r[:i]) + pyCapitalize(string(r[i:i+n])) + string(r[i+n:])
}

// smallLast implements \b(small)[PUNCT]?$ with re.I.
func smallLast(word string) string {
	r := []rune(word)
	for i := range r {
		if !boundaryAt(r, i) {
			continue
		}
		end := matchSmallEnd(r, i)
		if end > i {
			return string(r[:i]) + pyCapitalize(string(r[i:end])) + string(r[end:])
		}
	}
	return word
}

func matchSmallBoundary(r []rune, i int) int {
	for _, alt := range smallOrder {
		if hasPrefixFold(r[i:], alt, true) && boundaryAt(r, i+len(alt)) {
			return len(alt)
		}
	}
	return 0
}

func matchSmallEnd(r []rune, i int) int {
	for _, alt := range smallOrder {
		if !hasPrefixFold(r[i:], alt, true) {
			continue
		}
		end := i + len(alt)
		if end == len(r) {
			return end
		}
		if end == len(r)-1 && isPunct(r[end]) {
			return end + 1
		}
	}
	return -1
}

func matchSmallPrefix(r []rune) int {
	for _, alt := range smallOrder {
		if hasPrefixFold(r, alt, false) {
			return len(alt)
		}
	}
	return 0
}

func boundaryAt(r []rune, k int) bool {
	left := k > 0 && isWord(r[k-1])
	right := k < len(r) && isWord(r[k])
	return left != right
}

// capFirst implements ^[PUNCT]*?([\w]) with the matched text uppercased.
// The prefix is lazy, so a character that is both punctuation and a word
// character (underscore) is captured immediately rather than skipped.
func capFirst(word string) string {
	r := []rune(word)
	i := 0
	if len(r) == 0 || !isWord(r[0]) {
		for i < len(r) && isPunct(r[i]) && !isWord(r[i]) {
			i++
		}
	}
	if i >= len(r) || !isWord(r[i]) {
		return word
	}
	return string(r[:i]) + pyUpperRune(r[i]) + string(r[i+1:])
}

// subphrase implements ([:.;?!\-–‒—―][ ])(small) with re.sub, case-sensitive.
func subphrase(s string) string {
	r := []rune(s)
	var b strings.Builder
	for p := 0; p < len(r); {
		if isSubphrasePunct(r[p]) && p+1 < len(r) && r[p+1] == ' ' {
			if n := matchSmallPrefix(r[p+2:]); n > 0 {
				b.WriteString(string(r[p : p+2]))
				b.WriteString(pyCapitalize(string(r[p+2 : p+2+n])))
				p += 2 + n
				continue
			}
		}
		b.WriteRune(r[p])
		p++
	}
	return b.String()
}

func isSubphrasePunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2013', '\u2012', '\u2014', '\u2015':
		return true
	}
	return false
}

func allConsonants(r []rune) bool {
	for _, c := range r {
		if !consonantSet[foldASCII(c)] {
			return false
		}
	}
	return true
}

// isPythonSpace matches Python's str.isspace(), which also treats the
// information separators U+001C..U+001F as whitespace (unlike unicode.IsSpace).
func isPythonSpace(r rune) bool {
	if r >= 0x1C && r <= 0x1F {
		return true
	}
	return unicode.IsSpace(r)
}

// isWord matches Python's Unicode \w: letters, numbers, and underscore.
func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsNumber(r) || r == '_'
}

func isPunct(r rune) bool {
	return punctSet[r]
}

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isUpperASCII(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func foldASCII(r rune) rune {
	if r >= 'A' && r <= 'Z' {
		return r + ('a' - 'A')
	}
	return r
}

func hasPrefixFold(haystack, prefix []rune, ignoreCase bool) bool {
	if len(haystack) < len(prefix) {
		return false
	}
	for i, p := range prefix {
		h := haystack[i]
		if ignoreCase {
			h = foldASCII(h)
			p = foldASCII(p)
		}
		if h != p {
			return false
		}
	}
	return true
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(pyUpperRune(r))
	}
	return b.String()
}

func pyUpperRune(r rune) string {
	if expanded, ok := upperExpand[r]; ok {
		return expanded
	}
	return string(unicode.ToUpper(r))
}

func pyLower(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(pyLowerRune(r))
	}
	return b.String()
}

func pyLowerRune(r rune) string {
	if expanded, ok := lowerExpand[r]; ok {
		return expanded
	}
	return string(unicode.ToLower(r))
}

// pyCapitalize matches Python's str.capitalize(): first rune uppercased,
// remaining runes lowercased.
func pyCapitalize(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return ""
	}
	return pyUpperRune(r[0]) + pyLower(string(r[1:]))
}
