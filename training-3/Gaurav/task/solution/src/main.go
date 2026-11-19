package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
)

// Port of ppannuto/python-titlecase titlecase() with the default arguments:
// no callback, small words capitalized at the ends, blank lines collapsed,
// original whitespace kept. Go's regexp cannot express the Python patterns
// that depend on Unicode word boundaries, so those checks walk the string.

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 64*1024), 2*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	for in.Scan() {
		fmt.Fprintln(out, titlecase(in.Text()))
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

func titlecase(text string) string {
	return titlecaseFlag(text, true)
}

func titlecaseFlag(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = processLine(line, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func splitNewlines(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	var b strings.Builder
	rs := []rune(text)
	for i := 0; i < len(rs); {
		if rs[i] == '\n' || rs[i] == '\r' {
			lines = append(lines, b.String())
			b.Reset()
			for i < len(rs) && (rs[i] == '\n' || rs[i] == '\r') {
				i++
			}
			continue
		}
		b.WriteRune(rs[i])
		i++
	}
	lines = append(lines, b.String())
	return lines
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitWS(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = processWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(joinWords(tc, spaces))
}

func splitWS(s string) (words, spaces []string) {
	var parts []string
	var b strings.Builder
	for _, r := range s {
		if isPySpace(r) {
			parts = append(parts, b.String())
			b.Reset()
			parts = append(parts, string(r))
			continue
		}
		b.WriteRune(r)
	}
	parts = append(parts, b.String())
	for i, p := range parts {
		if i%2 == 0 {
			words = append(words, p)
		} else {
			spaces = append(spaces, p)
		}
	}
	return words, spaces
}

func joinWords(words, spaces []string) string {
	n := len(words) + len(spaces)
	parts := make([]string, n)
	for i, w := range words {
		parts[i*2] = w
	}
	for i, s := range spaces {
		parts[i*2+1] = s
	}
	return strings.Join(parts, "")
}

func processWord(word string, allCaps bool) string {
	if allCaps && ucInitials(word) {
		return word
	}
	if aposMatch(word) {
		return applyApos(word)
	}
	if prefix, rest, ok := matchMac(word); ok {
		return pyCapitalize(prefix) + titlecaseFlag(rest, true)
	}
	if isMrMrs(word) {
		return applyMr(word)
	}
	if hasInlinePeriod(word) || (!allCaps && ucElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, p := range parts {
			parts[i] = titlecaseFlag(p, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts {
			parts[i] = titlecaseFlag(p, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if isConsonantWord(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !isPyWord(rs[i]) {
		return word
	}
	return string(rs[:i]) + pyUpperRune(rs[i]) + string(rs[i+1:])
}

func applyApos(word string) string {
	rs := []rune(word)
	first := pyUpperRune(rs[0])
	if !isVowel(rs[0]) {
		first = pyLowerRune(rs[0])
	}
	return first + string(rs[1:2]) + pyUpperRune(rs[2]) + string(rs[3:])
}

func applyMr(word string) string {
	rs := []rune(word)
	return pyUpperRune(rs[0]) + string(rs[1:])
}

func aposMatch(word string) bool {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) {
		return false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return false
	}
	rest := rs[2:]
	if len(rest) >= 1 && allWord(rest) {
		return true
	}
	if len(rest) >= 3 && isAposSuffix(rest[len(rest)-2:]) && allWord(rest[:len(rest)-2]) {
		return true
	}
	return false
}

func isAposSuffix(rs []rune) bool {
	if len(rs) != 2 {
		return false
	}
	for _, r := range rs {
		if r != '\'' && r != 's' && r != 'S' {
			return false
		}
	}
	return true
}

func matchMac(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	var pref []rune
	if (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c' {
		pref = rs[:2]
	} else if rs[0] == 'M' && rs[1] == 'C' {
		pref = rs[:2]
	} else {
		return "", "", false
	}
	if !isPyWord(rs[2]) {
		return "", "", false
	}
	return string(pref), string(rs[2:]), true
}

func isMrMrs(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
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

func ucElsewhere(word string) bool {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	j := i
	for j < len(rs) && isASCIILetter(rs[j]) {
		j++
	}
	letters := rs[i:j]
	if len(letters) < 2 {
		return false
	}
	for _, r := range letters[1:] {
		if r >= 'A' && r <= 'Z' {
			return true
		}
	}
	return false
}

func ucInitials(word string) bool {
	rs := []rune(word)
	if len(rs) == 0 {
		return false
	}
	var rec func(i int) bool
	rec = func(i int) bool {
		if i == len(rs) {
			return true
		}
		if i+1 < len(rs) && isAZ(rs[i]) && rs[i+1] == '.' && rec(i+2) {
			return true
		}
		if i+2 < len(rs) && isAZ(rs[i]) && rs[i+1] == '.' && isAZ(rs[i+2]) && rec(i+3) {
			return true
		}
		return false
	}
	return rec(0)
}

func isConsonantWord(word string) bool {
	rs := []rune(word)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		if r >= 'A' && r <= 'Z' {
			r = r - 'A' + 'a'
		}
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

func isSmallWord(word string) bool {
	rs := []rune(word)
	for _, cands := range smallCands {
		for _, cand := range cands {
			cr := []rune(cand)
			if len(cr) == len(rs) && equalFold(rs, cr) {
				return true
			}
		}
	}
	return false
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	matched, ok := matchSmallPrefix(rs[i:], true)
	if !ok {
		return word
	}
	n := len([]rune(matched))
	return string(rs[:i]) + pyCapitalize(matched) + string(rs[i+n:])
}

func applySmallLast(word string) string {
	rs := []rune(word)
	for i := 0; i <= len(rs); i++ {
		if !isBoundaryAt(rs, i) {
			continue
		}
		if span, ok := smallThroughEnd(rs[i:]); ok {
			return string(rs[:i]) + pyCapitalize(span)
		}
	}
	return word
}

func smallThroughEnd(rest []rune) (string, bool) {
	for _, cands := range smallCands {
		for _, cand := range cands {
			cr := []rune(cand)
			if len(cr) > len(rest) || !equalFold(rest[:len(cr)], cr) {
				continue
			}
			tail := rest[len(cr):]
			if len(tail) > 1 {
				continue
			}
			if len(tail) == 1 && !isPunct(tail[0]) {
				continue
			}
			return string(rest[:len(cr)+len(tail)]), true
		}
	}
	return "", false
}

func matchSmallPrefix(rs []rune, boundary bool) (string, bool) {
	for _, cands := range smallCands {
		for _, cand := range cands {
			cr := []rune(cand)
			if len(cr) > len(rs) || !equalFold(rs[:len(cr)], cr) {
				continue
			}
			if boundary && !isBoundaryAt(rs, len(cr)) {
				continue
			}
			return string(rs[:len(cr)]), true
		}
	}
	return "", false
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && isSubDelim(rs[i]) && rs[i+1] == ' ' {
			if matched, ok := matchSmallPrefix(rs[i+2:], false); ok {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(matched))
				i += 2 + len([]rune(matched))
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

// smallCands follows Python's left-first alternation. v\.? and vs\.? try the
// dotted form first because the optional dot is greedy.
var smallCands = [][]string{
	{"a"},
	{"an"},
	{"and"},
	{"as"},
	{"at"},
	{"but"},
	{"by"},
	{"en"},
	{"for"},
	{"if"},
	{"in"},
	{"of"},
	{"on"},
	{"or"},
	{"the"},
	{"to"},
	{"v.", "v"},
	{"via"},
	{"vs.", "vs"},
}

func isBoundaryAt(rs []rune, i int) bool {
	left := i > 0 && isPyWord(rs[i-1])
	right := i < len(rs) && isPyWord(rs[i])
	return left != right
}

func equalFold(a, b []rune) bool {
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

func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	var b strings.Builder
	b.WriteString(pyUpperRune(rs[0]))
	for _, r := range rs[1:] {
		b.WriteString(pyLowerRune(r))
	}
	return b.String()
}

func pyUpperRune(r rune) string { return string(unicode.ToUpper(r)) }
func pyLowerRune(r rune) string { return string(unicode.ToLower(r)) }

func isVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func isDOL(r rune) bool {
	switch r {
	case 'd', 'o', 'l', 'D', 'O', 'L':
		return true
	default:
		return false
	}
}

func allWord(rs []rune) bool {
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

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isAZ(r rune) bool { return r >= 'A' && r <= 'Z' }

func isPyWord(r rune) bool {
	if r == '_' {
		return true
	}
	return unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isPySpace(r rune) bool {
	switch r {
	case '\t', '\n', '\v', '\f', '\r', ' ', 0x1c, 0x1d, 0x1e, 0x1f, 0x85:
		return true
	}
	return unicode.Is(unicode.Zs, r) || unicode.Is(unicode.Zl, r) || unicode.Is(unicode.Zp, r)
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '\u201c', '#', '$', '%', '&', '\'', '\u2018', '(', ')', '*', '+', ',', '\\',
		'-', '\u2013', '\u2012', '\u2014', '\u2015', '.', '/', ':', ';', '?', '@', '[', ']',
		'_', '`', '{', '|', '}', '~':
		return true
	default:
		return false
	}
}

func isSubDelim(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2013', '\u2012', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}
