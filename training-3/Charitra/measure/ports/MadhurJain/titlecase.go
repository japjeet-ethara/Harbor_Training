package main

import (
	"strings"
	"unicode"
	"unicode/utf8"
)

// titlecase is titlecase(text) from the original Python, called with its
// default arguments. Recursive slash, hyphen, and Mc handling passes the
// same small-word flag the Python function uses.
func titlecase(text string) string {
	return titlecaseRec(text, true)
}

func titlecaseRec(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = titlecaseLine(line, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := pyUpper(line) == line
	words, spaces := splitSpaces(line)
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
	if allCaps && matchInitials(word) {
		return word
	}
	if matchApos(word) {
		return fixApos(word)
	}
	if prefix, rest, ok := splitMac(word); ok {
		return pyCapitalize(prefix) + titlecaseRec(rest, true)
	}
	if isHonorific(word) {
		return upperFirst(word)
	}
	if hasInlinePeriod(word) || (!allCaps && ucElsewhere(word)) {
		return word
	}
	if matchSmallFull(word, true) {
		return pyLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = titlecaseRec(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = titlecaseRec(part, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = pyLower(word)
	}
	if runeLen(word) > 2 && allConsonants(word) {
		return pyUpper(word)
	}
	return capFirst(word)
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		if c, ok := pyCase[r]; ok {
			b.WriteString(c[0])
			continue
		}
		b.WriteRune(unicode.ToUpper(r))
	}
	return b.String()
}

func pyLower(s string) string {
	var b strings.Builder
	for _, r := range s {
		if c, ok := pyCase[r]; ok {
			b.WriteString(c[1])
			continue
		}
		b.WriteRune(unicode.ToLower(r))
	}
	return b.String()
}

// pyCapitalize matches Python str.capitalize: titlecase the first character
// (which may expand, as ß does to "Ss") and lowercase the rest.
func pyCapitalize(s string) string {
	if s == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	first := string(unicode.ToUpper(r))
	if c, ok := pyCase[r]; ok {
		first = c[2]
	}
	return first + pyLower(s[size:])
}

func upperFirst(s string) string {
	r, size := utf8.DecodeRuneInString(s)
	if r == utf8.RuneError && size == 0 {
		return s
	}
	return pyUpper(string(r)) + s[size:]
}

func capFirst(s string) string {
	rs := []rune(s)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !isWord(rs[i]) {
		return s
	}
	return pyUpper(string(rs[:i+1])) + string(rs[i+1:])
}

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isPySpace(r rune) bool {
	switch r {
	case '\t', '\n', '\v', '\f', '\r', 0x1C, 0x1D, 0x1E, 0x1F, 0x85:
		return true
	}
	return unicode.Is(unicode.Zs, r) || unicode.Is(unicode.Zl, r) || unicode.Is(unicode.Zp, r)
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/',
		':', ';', '?', '@', '[', '\\', ']', '_', '`', '{', '|', '}', '~',
		'\u2012', '\u2013', '\u2014', '\u2015', '\u2018', '\u201C':
		return true
	default:
		return false
	}
}

func isSubDelim(r rune) bool {
	switch r {
	case '!', '-', '.', ':', ';', '?', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func isASCIILetter(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z')
}

func isASCIIVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func foldASCII(r rune) rune {
	if r >= 'A' && r <= 'Z' {
		return r + ('a' - 'A')
	}
	return r
}

func runeLen(s string) int {
	return utf8.RuneCountInString(s)
}

func splitNewlines(text string) []string {
	var parts []string
	rs := []rune(text)
	start := 0
	for i := 0; i < len(rs); i++ {
		if rs[i] != '\n' && rs[i] != '\r' {
			continue
		}
		parts = append(parts, string(rs[start:i]))
		for i < len(rs) && (rs[i] == '\n' || rs[i] == '\r') {
			i++
		}
		start = i
		i--
	}
	parts = append(parts, string(rs[start:]))
	return parts
}

func splitSpaces(line string) (words, spaces []string) {
	var b strings.Builder
	for _, r := range line {
		if isPySpace(r) {
			words = append(words, b.String())
			b.Reset()
			spaces = append(spaces, string(r))
			continue
		}
		b.WriteRune(r)
	}
	words = append(words, b.String())
	return words, spaces
}

func joinWords(words, spaces []string) string {
	out := make([]string, len(words)+len(spaces))
	for i, word := range words {
		out[i*2] = word
	}
	for i, space := range spaces {
		out[i*2+1] = space
	}
	return strings.Join(out, "")
}

func matchInitials(s string) bool {
	if s == "" {
		return false
	}
	var rec func(i int) bool
	rec = func(i int) bool {
		if i == len(s) {
			return true
		}
		if i+2 <= len(s) && isAZ(s[i]) && s[i+1] == '.' && rec(i+2) {
			return true
		}
		if i+3 <= len(s) && isAZ(s[i]) && s[i+1] == '.' && isAZ(s[i+2]) && rec(i+3) {
			return true
		}
		return false
	}
	return rec(0)
}

func isAZ(b byte) bool {
	return b >= 'A' && b <= 'Z'
}

func matchApos(s string) bool {
	rs := []rune(s)
	if len(rs) < 3 || !isDOL(rs[0]) {
		return false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return false
	}
	if !isWord(rs[2]) {
		return false
	}
	i := 3
	for i < len(rs) && isWord(rs[i]) {
		i++
	}
	if i == len(rs) {
		return true
	}
	return i+2 == len(rs) && isAposTail(rs[i]) && isAposTail(rs[i+1])
}

func isDOL(r rune) bool {
	switch foldASCII(r) {
	case 'd', 'o', 'l':
		return true
	default:
		return false
	}
}

func isAposTail(r rune) bool {
	return r == '\'' || foldASCII(r) == 's'
}

func fixApos(word string) string {
	rs := []rune(word)
	var first string
	if isASCIIVowel(rs[0]) {
		first = pyUpper(string(rs[0]))
	} else {
		first = pyLower(string(rs[0]))
	}
	return first + string(rs[1]) + pyUpper(string(rs[2])) + string(rs[3:])
}

func splitMac(s string) (prefix, rest string, ok bool) {
	rs := []rune(s)
	if len(rs) < 4 {
		return "", "", false
	}
	prefix = string(rs[:2])
	if prefix != "Mc" && prefix != "mc" && prefix != "MC" {
		return "", "", false
	}
	if !isWord(rs[2]) || strings.ContainsRune(s, '\n') {
		return "", "", false
	}
	return prefix, string(rs[2:]), true
}

func isHonorific(s string) bool {
	switch strings.ToLower(s) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func hasInlinePeriod(s string) bool {
	rs := []rune(s)
	for i := 0; i+2 < len(rs); i++ {
		if isWord(rs[i]) && rs[i+1] == '.' && isWord(rs[i+2]) {
			return true
		}
	}
	return false
}

func ucElsewhere(s string) bool {
	rs := []rune(s)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	j := i
	for j < len(rs) && isASCIILetter(rs[j]) {
		j++
	}
	if j < i+2 {
		return false
	}
	for _, r := range rs[i+1 : j] {
		if r >= 'A' && r <= 'Z' {
			return true
		}
	}
	return false
}

func allConsonants(s string) bool {
	if s == "" {
		return false
	}
	for _, r := range s {
		if !isConsonant(r) {
			return false
		}
	}
	return true
}

func isConsonant(r rune) bool {
	switch foldASCII(r) {
	case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z':
		return true
	default:
		return false
	}
}

type smallAlt struct {
	kind int // 0 literal, 1 "v" plus optional dot, 2 "vs" plus optional dot
	lit  string
}

var smallAlts = []smallAlt{
	{0, "a"}, {0, "an"}, {0, "and"}, {0, "as"}, {0, "at"},
	{0, "but"}, {0, "by"}, {0, "en"}, {0, "for"}, {0, "if"},
	{0, "in"}, {0, "of"}, {0, "on"}, {0, "or"}, {0, "the"},
	{0, "to"}, {1, "v"}, {0, "via"}, {2, "vs"},
}

func matchSmallFull(s string, fold bool) bool {
	rs := []rune(s)
	for _, alt := range smallAlts {
		for _, n := range altLens(alt, rs, 0, fold) {
			if n == len(rs) {
				return true
			}
		}
	}
	return false
}

func altLens(alt smallAlt, rs []rune, i int, fold bool) []int {
	switch alt.kind {
	case 1:
		if i >= len(rs) || !eqRune(rs[i], 'v', fold) {
			return nil
		}
		if i+1 < len(rs) && rs[i+1] == '.' {
			return []int{2, 1}
		}
		return []int{1}
	case 2:
		if i+1 >= len(rs) || !eqRune(rs[i], 'v', fold) || !eqRune(rs[i+1], 's', fold) {
			return nil
		}
		if i+2 < len(rs) && rs[i+2] == '.' {
			return []int{3, 2}
		}
		return []int{2}
	default:
		lit := []rune(alt.lit)
		if i+len(lit) > len(rs) {
			return nil
		}
		for k, want := range lit {
			if !eqRune(rs[i+k], want, fold) {
				return nil
			}
		}
		return []int{len(lit)}
	}
}

func eqRune(got, want rune, fold bool) bool {
	if fold {
		return foldASCII(got) == foldASCII(want)
	}
	return got == want
}

func wordBoundary(rs []rune, i int) bool {
	left, right := false, false
	if i > 0 {
		left = isWord(rs[i-1])
	}
	if i < len(rs) {
		right = isWord(rs[i])
	}
	return left != right
}

func applySmallFirst(s string) string {
	rs := []rune(s)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	for _, alt := range smallAlts {
		for _, n := range altLens(alt, rs, i, true) {
			if wordBoundary(rs, i+n) {
				return string(rs[:i]) + pyCapitalize(string(rs[i:i+n])) + string(rs[i+n:])
			}
		}
	}
	return s
}

func applySmallLast(s string) string {
	rs := []rune(s)
	best := len(rs) + 1
	found := false
	consider := func(start int) {
		if start < best {
			best = start
			found = true
		}
	}
	for _, alt := range smallAlts {
		for _, n := range suffixLens(alt, rs, true) {
			start := len(rs) - n
			if wordBoundary(rs, start) {
				consider(start)
			}
		}
	}
	if len(rs) > 0 && isPunct(rs[len(rs)-1]) {
		head := rs[:len(rs)-1]
		for _, alt := range smallAlts {
			for _, n := range suffixLens(alt, head, true) {
				start := len(head) - n
				if wordBoundary(rs, start) {
					consider(start)
				}
			}
		}
	}
	if !found {
		return s
	}
	return string(rs[:best]) + pyCapitalize(string(rs[best:]))
}

func suffixLens(alt smallAlt, rs []rune, fold bool) []int {
	var lens []int
	max := 4
	if len(rs) < max {
		max = len(rs)
	}
	for n := max; n >= 1; n-- {
		start := len(rs) - n
		for _, got := range altLens(alt, rs, start, fold) {
			if got == n {
				lens = append(lens, n)
			}
		}
	}
	return lens
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := 0; i < len(rs); {
		if i+2 <= len(rs) && isSubDelim(rs[i]) && rs[i+1] == ' ' {
			if n, ok := smallPrefix(rs[i+2:], false); ok {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2 : i+2+n])))
				i += 2 + n
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

func smallPrefix(rs []rune, fold bool) (int, bool) {
	for _, alt := range smallAlts {
		lens := altLens(alt, rs, 0, fold)
		if len(lens) > 0 {
			return lens[0], true
		}
	}
	return 0, false
}
