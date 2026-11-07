// Command titlecase is a Go port of python-titlecase 2.4.1
// (https://github.com/ppannuto/python-titlecase, commit 42f43e2), matching the
// behaviour of titlecase() when the optional `regex` package is installed.
//
// It reads one title per line from stdin and writes the titlecased result, one
// per line, to stdout.
//
// Go's regexp package has no look-ahead, look-behind, back-references or \b
// with Unicode word characters, so every pattern of the original is rebuilt
// here as plain rune-by-rune code.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

// smallAlt is one alternative of the original SMALL pattern:
//
//	a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?
//
// The order matters: the regex engine tries the alternatives left to right.
type smallAlt struct {
	word   string
	optDot bool // the alternative ends in `\.?`
}

var smallAlts = []smallAlt{
	{"a", false}, {"an", false}, {"and", false}, {"as", false}, {"at", false},
	{"but", false}, {"by", false}, {"en", false}, {"for", false}, {"if", false},
	{"in", false}, {"of", false}, {"on", false}, {"or", false}, {"the", false},
	{"to", false}, {"v", true}, {"via", false}, {"vs", true},
}

// punctChars is the original PUNCT character class.
const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// subphraseChars is the leading class of the original SUBPHRASE pattern.
const subphraseChars = ":.;?!-–‒—―"

func isPunct(r rune) bool { return strings.ContainsRune(punctChars, r) }

func isLetter(r rune) bool { return unicode.IsLetter(r) }

func isUpperLetter(r rune) bool { return unicode.Is(unicode.Lu, r) }

// isWord mirrors \w of the `regex` module for the characters titles contain.
func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_' || unicode.Is(unicode.M, r)
}

// fold mirrors case-insensitive matching against an ASCII letter.
func fold(r rune) rune {
	switch {
	case r >= 'A' && r <= 'Z':
		return r + ('a' - 'A')
	case r == 0x017F: // LATIN SMALL LETTER LONG S folds to s
		return 's'
	case r == 0x212A: // KELVIN SIGN folds to k
		return 'k'
	case r == 0x0130: // LATIN CAPITAL LETTER I WITH DOT ABOVE matches i
		return 'i'
	}
	return r
}

// specialUpper holds the characters whose Python str.upper() result is longer
// than one character, which strings.ToUpper does not produce.
var specialUpper = map[rune]string{
	'ß': "SS", 'ŉ': "ʼN", 'ǰ': "J̌",
	'ẖ': "H̱", 'ẗ': "T̈", 'ẘ': "W̊", 'ẙ': "Y̊", 'ẚ': "Aʾ",
	'ﬀ': "FF", 'ﬁ': "FI", 'ﬂ': "FL", 'ﬃ': "FFI", 'ﬄ': "FFL", 'ﬅ': "ST", 'ﬆ': "ST",
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		if u, ok := specialUpper[r]; ok {
			b.WriteString(u)
		} else {
			b.WriteRune(unicode.ToUpper(r))
		}
	}
	return b.String()
}

func pyLower(s string) string {
	var b strings.Builder
	for _, r := range s {
		if r == 'İ' {
			b.WriteString("i̇")
		} else {
			b.WriteRune(unicode.ToLower(r))
		}
	}
	return b.String()
}

// pyCapitalize mirrors str.capitalize(): first character upper, rest lower.
func pyCapitalize(r []rune) string {
	if len(r) == 0 {
		return ""
	}
	return pyUpper(string(r[:1])) + pyLower(string(r[1:]))
}

// boundary reports whether the regex \b assertion holds at position p.
func boundary(r []rune, p int) bool {
	before := p > 0 && isWord(r[p-1])
	after := p < len(r) && isWord(r[p])
	return before != after
}

// matchSmall tries one alternative at position p and returns every end
// position the regex engine would try, in order (greedy `\.?` first).
func matchSmall(r []rune, p int, alt smallAlt, ignoreCase bool) []int {
	w := []rune(alt.word)
	if p+len(w) > len(r) {
		return nil
	}
	for i, c := range w {
		got := r[p+i]
		if ignoreCase {
			got = fold(got)
		}
		if got != c {
			return nil
		}
	}
	end := p + len(w)
	if alt.optDot && end < len(r) && r[end] == '.' {
		return []int{end + 1, end}
	}
	return []int{end}
}

// ucInitials mirrors ^(?:[\p{Lu}]\.|[\p{Lu}]\.[\p{Lu}])+$
func ucInitials(r []rune) bool {
	var from func(p int, units int) bool
	from = func(p int, units int) bool {
		if p == len(r) {
			return units > 0
		}
		if p+1 < len(r) && isUpperLetter(r[p]) && r[p+1] == '.' {
			if from(p+2, units+1) {
				return true
			}
			if p+2 < len(r) && isUpperLetter(r[p+2]) && from(p+3, units+1) {
				return true
			}
		}
		return false
	}
	return from(0, 0)
}

func allLetters(r []rune) bool {
	if len(r) == 0 {
		return false
	}
	for _, c := range r {
		if !isLetter(c) {
			return false
		}
	}
	return true
}

// aposSecond mirrors ^[dol]['‘][\p{Letter}]+(?:['s]{2})?$ (case-insensitive).
func aposSecond(r []rune) bool {
	if len(r) < 3 {
		return false
	}
	if c := fold(r[0]); c != 'd' && c != 'o' && c != 'l' {
		return false
	}
	if r[1] != '\'' && r[1] != '‘' {
		return false
	}
	rest := r[2:]
	if allLetters(rest) {
		return true
	}
	if len(rest) >= 3 {
		tail := rest[len(rest)-2:]
		ok := func(c rune) bool { return c == '\'' || fold(c) == 's' }
		if ok(tail[0]) && ok(tail[1]) && allLetters(rest[:len(rest)-2]) {
			return true
		}
	}
	return false
}

// macMc mirrors ^([Mm]c|MC)(\w.+)
func macMc(r []rune) bool {
	if len(r) < 4 {
		return false
	}
	p := string(r[:2])
	return (p == "Mc" || p == "mc" || p == "MC") && isWord(r[2])
}

func foldedEquals(r []rune, s string) bool {
	w := []rune(s)
	if len(r) != len(w) {
		return false
	}
	for i := range r {
		if fold(r[i]) != w[i] {
			return false
		}
	}
	return true
}

// mrMrsMsDr mirrors ^((m((rs?)|s))|Dr)$ (case-insensitive).
func mrMrsMsDr(r []rune) bool {
	return foldedEquals(r, "mr") || foldedEquals(r, "mrs") || foldedEquals(r, "ms") || foldedEquals(r, "dr")
}

// inlinePeriod mirrors a search for [\p{Letter}][.][\p{Letter}]
func inlinePeriod(r []rune) bool {
	for i := 0; i+2 < len(r); i++ {
		if isLetter(r[i]) && r[i+1] == '.' && isLetter(r[i+2]) {
			return true
		}
	}
	return false
}

func skipPunct(r []rune) int {
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	return i
}

// ucElsewhere mirrors a match of [PUNCT]*?[\p{Letter}]+[\p{Uppercase_Letter}]+?
func ucElsewhere(r []rune) bool {
	i := skipPunct(r)
	if i >= len(r) || !isLetter(r[i]) {
		return false
	}
	for j := i + 1; j < len(r) && isLetter(r[j]); j++ {
		if isUpperLetter(r[j]) {
			return true
		}
	}
	return false
}

// smallWord mirrors ^(SMALL)$ (case-insensitive).
func smallWord(r []rune) bool {
	for _, alt := range smallAlts {
		for _, end := range matchSmall(r, 0, alt, true) {
			if end == len(r) {
				return true
			}
		}
	}
	return false
}

func isConsonant(r rune) bool {
	c := fold(r)
	if c < 'a' || c > 'z' {
		return false
	}
	return !strings.ContainsRune("aeiouy", c)
}

func allConsonants(r []rune) bool {
	if len(r) == 0 {
		return false
	}
	for _, c := range r {
		if !isConsonant(c) {
			return false
		}
	}
	return true
}

// capFirst mirrors CAPFIRST.sub: upper-case the first letter that follows any
// leading punctuation; anything else is left alone.
func capFirst(r []rune) string {
	i := skipPunct(r)
	if i >= len(r) || !isLetter(r[i]) {
		return string(r)
	}
	return string(r[:i]) + pyUpper(string(r[i:i+1])) + string(r[i+1:])
}

// smallFirst mirrors SMALL_FIRST.sub: ^([PUNCT]*)(SMALL)\b, capitalising the
// small word.
func smallFirst(s string) string {
	r := []rune(s)
	i := skipPunct(r)
	for _, alt := range smallAlts {
		for _, end := range matchSmall(r, i, alt, true) {
			if boundary(r, end) {
				return string(r[:i]) + pyCapitalize(r[i:end]) + string(r[end:])
			}
		}
	}
	return s
}

// smallLast mirrors SMALL_LAST.sub: \b(SMALL)[PUNCT]?$, capitalising the whole
// match. The leftmost start position wins.
func smallLast(s string) string {
	r := []rune(s)
	for p := 0; p < len(r); p++ {
		if !boundary(r, p) {
			continue
		}
		for _, alt := range smallAlts {
			for _, end := range matchSmall(r, p, alt, true) {
				if end == len(r) || (end == len(r)-1 && isPunct(r[end])) {
					return string(r[:p]) + pyCapitalize(r[p:])
				}
			}
		}
	}
	return s
}

// subphrase mirrors SUBPHRASE.sub: ([:.;?!\-–‒—―][ ])(SMALL), case-sensitive
// and without a word boundary, capitalising the small word. Matches do not
// overlap, so the characters a match consumes are skipped.
func subphrase(s string) string {
	r := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(r) {
		if i+2 < len(r) && strings.ContainsRune(subphraseChars, r[i]) && r[i+1] == ' ' {
			matched := false
			for _, alt := range smallAlts {
				ends := matchSmall(r, i+2, alt, false)
				if len(ends) == 0 {
					continue
				}
				end := ends[0]
				b.WriteString(string(r[i : i+2]))
				b.WriteString(pyCapitalize(r[i+2 : end]))
				i = end
				matched = true
				break
			}
			if matched {
				continue
			}
		}
		b.WriteRune(r[i])
		i++
	}
	return b.String()
}

func titleWord(word string, allCaps bool) string {
	r := []rune(word)

	if allCaps && ucInitials(r) {
		return word
	}

	if aposSecond(r) {
		head := pyUpper(string(r[:1]))
		if !strings.ContainsRune("aeiouAEIOU", r[0]) {
			head = pyLower(string(r[:1]))
		}
		return head + string(r[1:2]) + pyUpper(string(r[2:3])) + string(r[3:])
	}

	if macMc(r) {
		return "Mc" + titlecase(string(r[2:]), true)
	}

	if mrMrsMsDr(r) {
		return pyUpper(string(r[:1])) + string(r[1:])
	}

	if inlinePeriod(r) || (!allCaps && ucElsewhere(r)) {
		return word
	}

	if smallWord(r) {
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
		r = []rune(word)
	}

	if allConsonants(r) && len(r) > 2 {
		return pyUpper(word)
	}

	return capFirst(r)
}

func titleLine(line string, smallFirstLast bool) string {
	allCaps := pyUpper(line) == line

	// regex.split(r'(\s)', line): every whitespace character is a separator
	// and is kept, so empty words appear between adjacent separators.
	var words, spaces []string
	var cur strings.Builder
	for _, c := range line {
		if unicode.IsSpace(c) {
			words = append(words, cur.String())
			spaces = append(spaces, string(c))
			cur.Reset()
		} else {
			cur.WriteRune(c)
		}
	}
	words = append(words, cur.String())

	tc := make([]string, len(words))
	for i, w := range words {
		tc[i] = titleWord(w, allCaps)
	}

	if smallFirstLast {
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

// titlecase mirrors titlecase(text, small_first_last=...) of the original.
func titlecase(text string, smallFirstLast bool) string {
	// regex.split('[\r\n]+', text)
	var lines []string
	var cur strings.Builder
	inBreak := false
	for _, c := range text {
		if c == '\r' || c == '\n' {
			if !inBreak {
				lines = append(lines, cur.String())
				cur.Reset()
				inBreak = true
			}
			continue
		}
		inBreak = false
		cur.WriteRune(c)
	}
	lines = append(lines, cur.String())

	for i, l := range lines {
		lines[i] = titleLine(l, smallFirstLast)
	}
	return strings.Join(lines, "\n")
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if err != nil && err != io.EOF {
			os.Exit(1)
		}
		if err == io.EOF && line == "" {
			return
		}
		line = strings.TrimSuffix(line, "\n")
		out.WriteString(titlecase(line, true))
		out.WriteByte('\n')
		if err == io.EOF {
			return
		}
	}
}
