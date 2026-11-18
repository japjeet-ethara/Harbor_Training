package main

import (
	"strings"
	"unicode"
)

// TitleCase matches titlecase.titlecase(text) from python-titlecase 2.4.1
// when the optional regex module is installed and the default arguments are used.
func TitleCase(text string) string {
	return titleCase(text, true)
}

func titleCase(text string, smallFirstLast bool) string {
	lines := splitLines(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = titleCaseLine(line, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func splitLines(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	start := 0
	for i := 0; i < len(text); {
		if text[i] != '\r' && text[i] != '\n' {
			i++
			continue
		}
		lines = append(lines, text[start:i])
		for i < len(text) && (text[i] == '\r' || text[i] == '\n') {
			i++
		}
		start = i
	}
	if start <= len(text) {
		lines = append(lines, text[start:])
	}
	return lines
}

func titleCaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitSpaces(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titleWord(word, allCaps, smallFirstLast)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallEdge(tc[0], true)
		tc[len(tc)-1] = applySmallEdge(tc[len(tc)-1], false)
	}
	joined := interleave(tc, spaces)
	return subphrase(joined)
}

func titleWord(word string, allCaps bool, smallFirstLast bool) string {
	rs := []rune(word)
	if len(rs) == 0 {
		return ""
	}
	if allCaps && isInitials(rs) {
		return word
	}
	if apos, ok := aposSecond(rs); ok {
		return string(apos)
	}
	if pre, rest, ok := macPrefix(rs); ok {
		return string(capitalize(pre)) + titleCase(string(rest), true)
	}
	if isHonorific(rs) {
		rs[0] = unicode.ToUpper(rs[0])
		return string(rs)
	}
	if hasInlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}
	if isEntireSmall(rs) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = titleCase(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = titleCase(part, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
		rs = []rune(word)
	}
	if allConsonants(rs) {
		return strings.ToUpper(word)
	}
	return string(capFirst(rs))
}

func splitSpaces(line string) (words, spaces []string) {
	rs := []rune(line)
	var buf []rune
	flushWord := func() {
		words = append(words, string(buf))
		buf = buf[:0]
	}
	for _, r := range rs {
		if unicode.IsSpace(r) {
			flushWord()
			spaces = append(spaces, string(r))
			continue
		}
		buf = append(buf, r)
	}
	flushWord()
	return words, spaces
}

func interleave(words, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

var punct = map[rune]bool{}

func init() {
	for _, r := range []rune("!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~") {
		punct[r] = true
	}
}

func isPunct(r rune) bool { return punct[r] }

var subPunct = map[rune]bool{}

func init() {
	for _, r := range []rune(":.;?!-–‒—―") {
		subPunct[r] = true
	}
}

func isWord(r rune) bool {
	if unicode.IsLetter(r) || unicode.IsDigit(r) {
		return true
	}
	if unicode.Is(unicode.Nl, r) || unicode.Is(unicode.Pc, r) {
		return true
	}
	if unicode.Is(unicode.Mn, r) || unicode.Is(unicode.Mc, r) || unicode.Is(unicode.Me, r) {
		return true
	}
	return false
}

func boundary(rs []rune, i int) bool {
	var left, right bool
	if i > 0 {
		left = isWord(rs[i-1])
	}
	if i < len(rs) {
		right = isWord(rs[i])
	}
	if i == 0 {
		return right
	}
	if i == len(rs) {
		return left
	}
	return left != right
}

type altKind int

const (
	altWord altKind = iota
	altV
	altVS
)

type alt struct {
	kind altKind
	word string
}

var smallAlts = []alt{
	{altWord, "a"},
	{altWord, "an"},
	{altWord, "and"},
	{altWord, "as"},
	{altWord, "at"},
	{altWord, "but"},
	{altWord, "by"},
	{altWord, "en"},
	{altWord, "for"},
	{altWord, "if"},
	{altWord, "in"},
	{altWord, "of"},
	{altWord, "on"},
	{altWord, "or"},
	{altWord, "the"},
	{altWord, "to"},
	{altV, ""},
	{altWord, "via"},
	{altVS, ""},
}

func foldEq(a, b []rune) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if unicode.ToLower(a[i]) != unicode.ToLower(b[i]) {
			return false
		}
	}
	return true
}

// matchAlt reports how many runes an alternative consumes at rs.
// dotted is considered for v / vs. maxDot prefers consuming a following '.'.
func matchAlt(rs []rune, a alt, maxDot bool) int {
	switch a.kind {
	case altWord:
		w := []rune(a.word)
		if len(rs) < len(w) || !foldEq(rs[:len(w)], w) {
			return 0
		}
		return len(w)
	case altV:
		if len(rs) == 0 || unicode.ToLower(rs[0]) != 'v' {
			return 0
		}
		if maxDot && len(rs) >= 2 && rs[1] == '.' {
			return 2
		}
		return 1
	case altVS:
		if len(rs) < 2 || unicode.ToLower(rs[0]) != 'v' || unicode.ToLower(rs[1]) != 's' {
			return 0
		}
		if maxDot && len(rs) >= 3 && rs[2] == '.' {
			return 3
		}
		return 2
	default:
		return 0
	}
}

func isEntireSmall(rs []rune) bool {
	for _, a := range smallAlts {
		n := matchAlt(rs, a, true)
		if n == len(rs) && n > 0 {
			return true
		}
	}
	return false
}

func matchBounded(rs []rune, i int) int {
	rest := rs[i:]
	for _, a := range smallAlts {
		for _, maxDot := range []bool{true, false} {
			n := matchAlt(rest, a, maxDot)
			if n == 0 {
				continue
			}
			if a.kind == altWord && maxDot == false {
				continue
			}
			if boundary(rs, i+n) {
				return n
			}
			if a.kind == altWord {
				break
			}
		}
	}
	return 0
}

func applySmallEdge(word string, first bool) string {
	rs := []rune(word)
	if first {
		i := 0
		for i < len(rs) && isPunct(rs[i]) {
			i++
		}
		n := matchBounded(rs, i)
		if n == 0 {
			return word
		}
		mid := capitalize(rs[i : i+n])
		out := append([]rune{}, rs[:i]...)
		out = append(out, mid...)
		out = append(out, rs[i+n:]...)
		return string(out)
	}
	// Small word, optionally followed by one punctuation character, at the end.
	try := func(end int) (int, int, bool) {
		if end < 0 || end > len(rs) {
			return 0, 0, false
		}
		restEnd := end
		for _, a := range smallAlts {
			for _, maxDot := range []bool{true, false} {
				n := matchAlt(rs[:restEnd], a, maxDot)
				// The alternative must end exactly at restEnd, so try aligning it.
				_ = n
			}
			n := matchAltSuffix(rs[:restEnd], a)
			if n == 0 {
				continue
			}
			start := restEnd - n
			if boundary(rs, start) {
				return start, end, true
			}
		}
		return 0, 0, false
	}
	if len(rs) > 0 && isPunct(rs[len(rs)-1]) {
		if s, e, ok := try(len(rs) - 1); ok {
			// Include the trailing punctuation in the capitalized match.
			cap := capitalize(rs[s:e])
			// try() with end=len-1 does not include the punct. The regex match does.
			cap = capitalize(rs[s:])
			out := append([]rune{}, rs[:s]...)
			out = append(out, cap...)
			return string(out)
		}
	}
	if s, _, ok := try(len(rs)); ok {
		cap := capitalize(rs[s:])
		out := append([]rune{}, rs[:s]...)
		out = append(out, cap...)
		return string(out)
	}
	return word
}

func matchAltSuffix(rs []rune, a alt) int {
	if len(rs) == 0 {
		return 0
	}
	switch a.kind {
	case altWord:
		w := []rune(a.word)
		if len(rs) < len(w) {
			return 0
		}
		if foldEq(rs[len(rs)-len(w):], w) {
			return len(w)
		}
		return 0
	case altV:
		if len(rs) >= 2 && unicode.ToLower(rs[len(rs)-2]) == 'v' && rs[len(rs)-1] == '.' {
			return 2
		}
		if unicode.ToLower(rs[len(rs)-1]) == 'v' {
			return 1
		}
		return 0
	case altVS:
		if len(rs) >= 3 && unicode.ToLower(rs[len(rs)-3]) == 'v' && unicode.ToLower(rs[len(rs)-2]) == 's' && rs[len(rs)-1] == '.' {
			return 3
		}
		if len(rs) >= 2 && unicode.ToLower(rs[len(rs)-2]) == 'v' && unicode.ToLower(rs[len(rs)-1]) == 's' {
			return 2
		}
		return 0
	default:
		return 0
	}
}

func capitalize(rs []rune) []rune {
	if len(rs) == 0 {
		return rs
	}
	out := append([]rune{}, rs...)
	out[0] = unicode.ToUpper(out[0])
	for i := 1; i < len(out); i++ {
		out[i] = unicode.ToLower(out[i])
	}
	return out
}

func capFirst(rs []rune) []rune {
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return rs
	}
	out := append([]rune{}, rs...)
	upper := unicode.ToUpper(out[i])
	out[i] = upper
	return out
}

func hasInlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if unicode.IsLetter(rs[i]) && rs[i+1] == '.' && unicode.IsLetter(rs[i+2]) {
			return true
		}
	}
	return false
}

func ucElsewhere(rs []rune) bool {
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	seen := false
	for _, r := range rs[i:] {
		if !unicode.IsLetter(r) {
			return false
		}
		if seen && unicode.Is(unicode.Lu, r) {
			return true
		}
		seen = true
	}
	return false
}

func isInitials(rs []rune) bool {
	i := 0
	if len(rs) == 0 {
		return false
	}
	for i < len(rs) {
		if !unicode.Is(unicode.Lu, rs[i]) || i+1 >= len(rs) || rs[i+1] != '.' {
			return false
		}
		if i+2 < len(rs) && unicode.Is(unicode.Lu, rs[i+2]) && (i+3 == len(rs) || rs[i+3] == '.') {
			// Prefer Upper.Upper when it is a complete group. Upper.Upper is only
			// valid when the second letter is not itself the start of Upper.
			// The Python expression is (?:Lu\.|Lu\.Lu)+ so "A.B." is two of Lu.
			// and "A.B" is one Lu.Lu. "A.BC." does not match. Take Lu.Lu only
			// when the character after the second letter is not a dot that would
			// let Lu. consume it, except when Lu.Lu reaches the end or is followed
			// by a dot that starts another group... Handled by the scanner below.
		}
		break
	}
	i = 0
	for i < len(rs) {
		if i+3 <= len(rs) && unicode.Is(unicode.Lu, rs[i]) && rs[i+1] == '.' && unicode.Is(unicode.Lu, rs[i+2]) {
			// Use Lu.Lu when the shorter Lu. would leave a trailing uppercase
			// letter that cannot start another Lu. group.
			usePair := false
			if i+3 == len(rs) {
				usePair = true
			} else if rs[i+3] != '.' {
				usePair = true
			}
			if usePair {
				i += 3
				continue
			}
		}
		if i+1 < len(rs) && unicode.Is(unicode.Lu, rs[i]) && rs[i+1] == '.' {
			i += 2
			continue
		}
		return false
	}
	return i == len(rs)
}

func aposSecond(rs []rune) ([]rune, bool) {
	if len(rs) < 3 {
		return nil, false
	}
	first := unicode.ToLower(rs[0])
	if first != 'd' && first != 'o' && first != 'l' {
		return nil, false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return nil, false
	}
	i := 2
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return nil, false
	}
	i++
	for i < len(rs) && unicode.IsLetter(rs[i]) {
		i++
	}
	if i < len(rs) {
		if len(rs)-i != 2 {
			return nil, false
		}
		for _, r := range rs[i:] {
			if r != '\'' && unicode.ToLower(r) != 's' {
				return nil, false
			}
		}
	}
	out := append([]rune{}, rs...)
	if !strings.ContainsRune("aeiouAEIOU", rs[0]) {
		out[0] = unicode.ToLower(out[0])
	} else {
		out[0] = unicode.ToUpper(out[0])
	}
	out[2] = unicode.ToUpper(out[2])
	return out, true
}

func macPrefix(rs []rune) (pre, rest []rune, ok bool) {
	if len(rs) < 4 {
		return nil, nil, false
	}
	if ((rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c') || (rs[0] == 'M' && rs[1] == 'C') {
		if isWord(rs[2]) {
			return rs[:2], rs[2:], true
		}
	}
	return nil, nil, false
}

func isHonorific(rs []rune) bool {
	s := strings.ToLower(string(rs))
	switch s {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func allConsonants(rs []rune) bool {
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		if r >= 'A' && r <= 'Z' {
			r = r - 'A' + 'a'
		}
		if r < 'a' || r > 'z' || strings.ContainsRune("aeiouy", r) {
			return false
		}
	}
	return true
}

func subphrase(s string) string {
	rs := []rune(s)
	var out []rune
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && subPunct[rs[i]] && rs[i+1] == ' ' {
			n := subMatch(rs[i+2:])
			if n > 0 {
				out = append(out, rs[i], rs[i+1])
				out = append(out, capitalize(rs[i+2:i+2+n])...)
				i += 2 + n
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

func subMatch(rs []rune) int {
	for _, a := range smallAlts {
		n := matchAlt(rs, a, true)
		if n > 0 {
			return n
		}
	}
	return 0
}
