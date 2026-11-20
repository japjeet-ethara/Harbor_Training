// Command titlecase is a Go port of python-titlecase 2.4.1 (titlecase/__init__.py,
// with the `regex` package available). It reads one title per line on stdin
// and prints the titlecased result, one per line.
//
// Go's regexp has no look-ahead, look-behind, lazy-prefix backtracking or
// Unicode case-folding quirks that the Python patterns rely on, so every
// pattern is rebuilt here as plain code that walks the runes by hand.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

// PUNCT from the Python source: !"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~
var punct = runeSet("!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~")

// The separator class of SUBPHRASE: [:.;?!\-–‒—―]
var subphraseSep = runeSet(":.;?!-–‒—―")

// SMALL = a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?
// expanded in the order the regex engine tries them (\.? is greedy, so the
// form with the dot is tried first).
var smallAlts = [][]rune{
	[]rune("a"), []rune("an"), []rune("and"), []rune("as"), []rune("at"),
	[]rune("but"), []rune("by"), []rune("en"), []rune("for"), []rune("if"),
	[]rune("in"), []rune("of"), []rune("on"), []rune("or"), []rune("the"),
	[]rune("to"), []rune("v."), []rune("v"), []rune("via"), []rune("vs."),
	[]rune("vs"),
}

func runeSet(s string) map[rune]bool {
	m := make(map[rune]bool)
	for _, r := range s {
		m[r] = true
	}
	return m
}

// ------------------------------------------------------------ Python string helpers

// Full (multi-character) upper-case mappings that Python's str.upper uses and
// Go's unicode.ToUpper does not.
var specialUpper = map[rune]string{
	'ß': "SS", 'ŉ': "ʼN", 'ǰ': "J̌", 'ﬀ': "FF", 'ﬁ': "FI", 'ﬂ': "FL",
	'ﬃ': "FFI", 'ﬄ': "FFL", 'ﬅ': "ST", 'ﬆ': "ST",
}

// Full title-case mappings used by str.capitalize for the first character.
var specialTitle = map[rune]string{
	'ß': "Ss", 'ŉ': "ʼN", 'ǰ': "J̌", 'ﬀ': "Ff", 'ﬁ': "Fi", 'ﬂ': "Fl",
	'ﬃ': "Ffi", 'ﬄ': "Ffl", 'ﬅ': "St", 'ﬆ': "St",
}

func pyUpperRune(r rune) string {
	if s, ok := specialUpper[r]; ok {
		return s
	}
	return string(unicode.ToUpper(r))
}

func pyLowerRune(r rune) string {
	if r == 'İ' {
		return "i̇"
	}
	return string(unicode.ToLower(r))
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(pyUpperRune(r))
	}
	return b.String()
}

func pyLower(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(pyLowerRune(r))
	}
	return b.String()
}

// pyCapitalize mirrors str.capitalize: first character title-cased, the rest
// lower-cased.
func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	var b strings.Builder
	if t, ok := specialTitle[rs[0]]; ok {
		b.WriteString(t)
	} else {
		b.WriteRune(unicode.ToTitle(rs[0]))
	}
	for _, r := range rs[1:] {
		b.WriteString(pyLowerRune(r))
	}
	return b.String()
}

// ------------------------------------------------------------ character classes

func isLetter(r rune) bool { return unicode.IsLetter(r) } // \p{Letter}
func isUpper(r rune) bool  { return unicode.Is(unicode.Lu, r) } // \p{Uppercase_Letter}

// isWord mirrors \w in the `regex` module: Alphabetic, marks, decimal digits,
// connector punctuation and the join controls.
func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.Is(unicode.Nl, r) ||
		unicode.Is(unicode.Other_Alphabetic, r) || unicode.IsMark(r) ||
		unicode.Is(unicode.Nd, r) || unicode.Is(unicode.Pc, r) ||
		r == 0x200C || r == 0x200D
}

// isSpace mirrors \s (the Unicode White_Space property).
func isSpace(r rune) bool { return unicode.IsSpace(r) }

// foldEq reports whether r matches the pattern character c under the
// IGNORECASE flag (simple case folding, as the `regex` module does by default).
func foldEq(r, c rune) bool {
	if r == c {
		return true
	}
	for f := unicode.SimpleFold(c); f != c; f = unicode.SimpleFold(f) {
		if f == r {
			return true
		}
	}
	return false
}

// matchAt reports whether alt occurs in rs at position i.
func matchAt(rs []rune, i int, alt []rune, ignoreCase bool) bool {
	if i+len(alt) > len(rs) {
		return false
	}
	for k, c := range alt {
		r := rs[i+k]
		if ignoreCase {
			if !foldEq(r, c) {
				return false
			}
		} else if r != c {
			return false
		}
	}
	return true
}

// boundary mirrors \b at position i.
func boundary(rs []rune, i int) bool {
	before := i > 0 && isWord(rs[i-1])
	after := i < len(rs) && isWord(rs[i])
	return before != after
}

func skipPunct(rs []rune, i int) int {
	for i < len(rs) && punct[rs[i]] {
		i++
	}
	return i
}

// ------------------------------------------------------------ the patterns

// UC_INITIALS: ^(?:[\p{Lu}]{1}\.{1}|[\p{Lu}]{1}\.{1}[\p{Lu}]{1})+$
func ucInitials(rs []rune) bool {
	n := len(rs)
	memo := make(map[int]bool)
	var rec func(i int) bool
	rec = func(i int) bool {
		if i == n {
			return true
		}
		if v, ok := memo[i]; ok {
			return v
		}
		ok := false
		if i+1 < n && isUpper(rs[i]) && rs[i+1] == '.' {
			ok = rec(i + 2)
			if !ok && i+2 < n && isUpper(rs[i+2]) {
				ok = rec(i + 3)
			}
		}
		memo[i] = ok
		return ok
	}
	return n > 0 && rec(0)
}

// APOS_SECOND (IGNORECASE): ^[dol]{1}['‘]{1}[\p{Letter}]+(?:['s]{2})?$
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
	allLetters := func(xs []rune) bool {
		if len(xs) == 0 {
			return false
		}
		for _, r := range xs {
			if !isLetter(r) {
				return false
			}
		}
		return true
	}
	if allLetters(rest) {
		return true
	}
	isApS := func(r rune) bool { return r == '\'' || foldEq(r, 's') }
	m := len(rest)
	return m >= 3 && isApS(rest[m-1]) && isApS(rest[m-2]) && allLetters(rest[:m-2])
}

// MAC_MC: ^([Mm]c|MC)(\w.+)  -> (group1, group2, ok)
func macMc(rs []rune) (string, string, bool) {
	if len(rs) < 4 {
		return "", "", false
	}
	p := string(rs[:2])
	if p != "Mc" && p != "mc" && p != "MC" {
		return "", "", false
	}
	if !isWord(rs[2]) {
		return "", "", false
	}
	for _, r := range rs[3:] { // '.' matches anything but a newline
		if r == '\n' {
			return "", "", false
		}
	}
	return p, string(rs[2:]), true
}

// MR_MRS_MS_DR (IGNORECASE): ^((m((rs?)|s))|Dr)$
func mrMrsMsDr(rs []rune) bool {
	for _, w := range []string{"mr", "mrs", "ms", "dr"} {
		alt := []rune(w)
		if len(alt) == len(rs) && matchAt(rs, 0, alt, true) {
			return true
		}
	}
	return false
}

// INLINE_PERIOD.search: [\p{Letter}][.][\p{Letter}]
func inlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if isLetter(rs[i]) && rs[i+1] == '.' && isLetter(rs[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE.match: [PUNCT]*?[\p{Letter}]+[\p{Uppercase_Letter}]+?
// The lazy punctuation prefix can only succeed once it has eaten every leading
// punctuation character; after that we need a letter followed (inside the same
// run of letters) by an upper-case letter.
func ucElsewhere(rs []rune) bool {
	i := skipPunct(rs, 0)
	if i >= len(rs) || !isLetter(rs[i]) {
		return false
	}
	for j := i + 1; j < len(rs) && isLetter(rs[j]); j++ {
		if isUpper(rs[j]) {
			return true
		}
	}
	return false
}

// SMALL_WORDS.match (IGNORECASE): ^(SMALL)$
func smallWord(rs []rune) bool {
	for _, alt := range smallAlts {
		if len(alt) == len(rs) && matchAt(rs, 0, alt, true) {
			return true
		}
	}
	return false
}

// \A[bcdfghjklmnpqrstvwxz]+\Z (IGNORECASE)
func allConsonants(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		ok := false
		for _, c := range "bcdfghjklmnpqrstvwxz" {
			if foldEq(r, c) {
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

// CAPFIRST.sub(upper): ^[PUNCT]*?([\p{Letter}])
func capFirst(word string) string {
	rs := []rune(word)
	i := skipPunct(rs, 0)
	if i >= len(rs) || !isLetter(rs[i]) {
		return word
	}
	return pyUpper(string(rs[:i+1])) + string(rs[i+1:])
}

// SMALL_FIRST.sub (IGNORECASE): ^([PUNCT]*)(SMALL)\b -> group1 + group2.capitalize()
func smallFirst(word string) string {
	rs := []rune(word)
	i := skipPunct(rs, 0)
	for _, alt := range smallAlts {
		if matchAt(rs, i, alt, true) && boundary(rs, i+len(alt)) {
			j := i + len(alt)
			return string(rs[:i]) + pyCapitalize(string(rs[i:j])) + string(rs[j:])
		}
	}
	return word
}

// SMALL_LAST.sub (IGNORECASE): \b(SMALL)[PUNCT]?$ -> match.capitalize()
func smallLast(word string) string {
	rs := []rune(word)
	n := len(rs)
	for i := 0; i < n; i++ {
		if !boundary(rs, i) {
			continue
		}
		for _, alt := range smallAlts {
			if !matchAt(rs, i, alt, true) {
				continue
			}
			j := i + len(alt)
			if j == n || (j+1 == n && punct[rs[j]]) {
				return string(rs[:i]) + pyCapitalize(string(rs[i:]))
			}
		}
	}
	return word
}

// SUBPHRASE.sub (case-sensitive): ([:.;?!\-–‒—―][ ])(SMALL) -> group1 + group2.capitalize()
func subphrase(line string) string {
	rs := []rune(line)
	var b strings.Builder
	for i := 0; i < len(rs); {
		if subphraseSep[rs[i]] && i+1 < len(rs) && rs[i+1] == ' ' {
			matched := false
			for _, alt := range smallAlts {
				if matchAt(rs, i+2, alt, false) {
					b.WriteRune(rs[i])
					b.WriteRune(' ')
					b.WriteString(pyCapitalize(string(alt)))
					i += 2 + len(alt)
					matched = true
					break
				}
			}
			if matched {
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

// ------------------------------------------------------------ titlecase()

func titlecaseWord(word string, allCaps bool) string {
	rs := []rune(word)

	if allCaps && ucInitials(rs) {
		return word
	}

	if aposSecond(rs) {
		var first string
		if !strings.ContainsRune("aeiouAEIOU", rs[0]) {
			first = pyLowerRune(rs[0])
		} else {
			first = pyUpperRune(rs[0])
		}
		return first + string(rs[1]) + pyUpperRune(rs[2]) + string(rs[3:])
	}

	if g1, g2, ok := macMc(rs); ok {
		return pyCapitalize(g1) + titlecase(g2, true)
	}

	if mrMrsMsDr(rs) {
		return pyUpperRune(rs[0]) + string(rs[1:])
	}

	if inlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}

	if smallWord(rs) {
		return pyLower(word)
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for k, p := range parts {
			parts[k] = titlecase(p, false)
		}
		return strings.Join(parts, "/")
	}

	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for k, p := range parts {
			parts[k] = titlecase(p, false)
		}
		return strings.Join(parts, "-")
	}

	if allCaps {
		word = pyLower(word)
		rs = []rune(word)
	}

	if allConsonants(rs) && len(rs) > 2 {
		return pyUpper(word)
	}

	return capFirst(word)
}

// splitLines mirrors regex.split('[\r\n]+', text).
func splitLines(text string) []string {
	var lines []string
	var cur strings.Builder
	inBreak := false
	for _, r := range text {
		if r == '\r' || r == '\n' {
			if !inBreak {
				lines = append(lines, cur.String())
				cur.Reset()
				inBreak = true
			}
			continue
		}
		inBreak = false
		cur.WriteRune(r)
	}
	return append(lines, cur.String())
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitLines(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		allCaps := pyUpper(line) == line

		// regex.split(r'(\s)', line): words at even indexes, single spaces between.
		var words, spaces []string
		var cur strings.Builder
		for _, r := range line {
			if isSpace(r) {
				words = append(words, cur.String())
				cur.Reset()
				spaces = append(spaces, string(r))
				continue
			}
			cur.WriteRune(r)
		}
		words = append(words, cur.String())

		tc := make([]string, len(words))
		for k, w := range words {
			tc[k] = titlecaseWord(w, allCaps)
		}

		if smallFirstLast && len(tc) > 0 {
			tc[0] = smallFirst(tc[0])
			tc[len(tc)-1] = smallLast(tc[len(tc)-1])
		}

		var b strings.Builder
		for k, w := range tc {
			b.WriteString(w)
			if k < len(spaces) {
				b.WriteString(spaces[k])
			}
		}
		processed = append(processed, subphrase(b.String()))
	}
	return strings.Join(processed, "\n")
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<16)
	out := bufio.NewWriterSize(os.Stdout, 1<<16)
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
