package main

import (
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

// stdlib re path from titlecase/__init__.py (REGEX_AVAILABLE is false).
// Each stdin line is one titlecase() call with the library defaults.

const (
	enDash     = '\u2013'
	figureDash = '\u2012'
	emDash     = '\u2014'
	horizBar   = '\u2015'
	leftSingle = '\u2018'
	leftDouble = '\u201c'
)

type smallAlt struct {
	word   string
	optDot bool
}

// Order matches the SMALL alternation. v\.? is before via and vs\.?.
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

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	if len(data) == 0 {
		return
	}
	text := string(data)
	trailingNL := strings.HasSuffix(text, "\n")
	text = strings.TrimSuffix(text, "\n")
	lines := strings.Split(text, "\n")
	var out strings.Builder
	out.Grow(len(data))
	for i, line := range lines {
		if i > 0 {
			out.WriteByte('\n')
		}
		out.WriteString(titlecase(line, true))
	}
	if trailingNL {
		out.WriteByte('\n')
	}
	_, _ = io.WriteString(os.Stdout, out.String())
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitBreaks(text)
	parts := make([]string, len(lines))
	for i, line := range lines {
		parts[i] = titlecaseLine(line, smallFirstLast)
	}
	return strings.Join(parts, "\n")
}

func splitBreaks(text string) []string {
	var lines []string
	start := 0
	i := 0
	for i < len(text) {
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
	lines = append(lines, text[start:])
	return lines
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitSpaces(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titlecaseWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(joinOriginal(tc, spaces))
}

func titlecaseWord(word string, allCaps bool) string {
	if allCaps && isInitials(word) {
		return word
	}
	if apos, ok := recaseApos(word); ok {
		return apos
	}
	if prefix, rest, ok := splitMac(word); ok {
		return pyCapitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		r, size := utf8.DecodeRuneInString(word)
		if r == utf8.RuneError && size == 0 {
			return word
		}
		return strings.ToUpper(string(r)) + word[size:]
	}
	if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return strings.ToLower(word)
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
		word = strings.ToLower(word)
	}
	if isConsonantAcronym(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func splitSpaces(line string) (words, spaces []string) {
	start := 0
	i := 0
	for i < len(line) {
		r, size := utf8.DecodeRuneInString(line[i:])
		if isPySpace(r) {
			words = append(words, line[start:i])
			spaces = append(spaces, line[i:i+size])
			i += size
			start = i
			continue
		}
		i += size
	}
	words = append(words, line[start:])
	return words, spaces
}

func joinOriginal(words, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func isPySpace(r rune) bool {
	if r >= 0x1c && r <= 0x1f {
		return true
	}
	return unicode.IsSpace(r)
}

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isASCIIUpper(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func foldASCII(r rune) rune {
	if r >= 'A' && r <= 'Z' {
		return r + ('a' - 'A')
	}
	return r
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', leftDouble, '#', '$', '%', '&', '\'', leftSingle,
		'(', ')', '*', '+', ',', '-', enDash, figureDash, emDash, horizBar,
		'.', '/', ':', ';', '?', '@', '[', '\\', ']', '_', '`', '{', '|', '}', '~':
		return true
	default:
		return false
	}
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', enDash, figureDash, emDash, horizBar:
		return true
	default:
		return false
	}
}

func isInitials(word string) bool {
	rs := []rune(word)
	if len(rs) == 0 {
		return false
	}
	return matchInitials(rs, 0)
}

func matchInitials(rs []rune, i int) bool {
	if i == len(rs) {
		return true
	}
	if i+1 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && matchInitials(rs, i+2) {
		return true
	}
	if i+2 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && isASCIIUpper(rs[i+2]) && matchInitials(rs, i+3) {
		return true
	}
	return false
}

func recaseApos(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) || (rs[1] != '\'' && rs[1] != leftSingle) {
		return "", false
	}
	rest := rs[2:]
	if !aposTail(rest) {
		return "", false
	}
	first := strings.ToLower(string(rs[0]))
	if !strings.ContainsRune("aeiouAEIOU", rs[0]) {
		first = strings.ToLower(string(rs[0]))
	} else {
		first = strings.ToUpper(string(rs[0]))
	}
	third := strings.ToUpper(string(rs[2]))
	return first + string(rs[1]) + third + string(rs[3:]), true
}

func isDOL(r rune) bool {
	switch r {
	case 'd', 'D', 'o', 'O', 'l', 'L':
		return true
	default:
		return false
	}
}

func aposTail(rest []rune) bool {
	if len(rest) == 0 {
		return false
	}
	if allWord(rest) {
		return true
	}
	if len(rest) >= 3 && allWord(rest[:len(rest)-2]) && inAposSet(rest[len(rest)-2]) && inAposSet(rest[len(rest)-1]) {
		return true
	}
	return false
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

func inAposSet(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func splitMac(word string) (prefix, rest string, ok bool) {
	if strings.HasPrefix(word, "Mc") || strings.HasPrefix(word, "mc") || strings.HasPrefix(word, "MC") {
		prefix = word[:2]
	} else {
		return "", "", false
	}
	rest = word[2:]
	r, size := utf8.DecodeRuneInString(rest)
	if size == 0 || !isWord(r) || len(rest) == size {
		return "", "", false
	}
	return prefix, rest, true
}

func isHonorific(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func hasInlinePeriod(word string) bool {
	rs := []rune(word)
	for i := 0; i+2 < len(rs); i++ {
		if isWord(rs[i]) && rs[i+1] == '.' && isWord(rs[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE is [%s]*?[a-zA-Z]+[A-Z]+? anchored at the start.
// The second class is ASCII capitals only: IGNORECASE does not turn it into lowercase.
func hasUCElsewhere(word string) bool {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !isASCIILetter(rs[i]) {
		return false
	}
	i++
	for i < len(rs) && isASCIILetter(rs[i]) {
		if isASCIIUpper(rs[i]) {
			return true
		}
		i++
	}
	return false
}

func isSmallWord(word string) bool {
	rs := []rune(word)
	for _, alt := range smallAlts {
		end, ok := matchAlt(rs, 0, alt, true)
		if ok && end == len(rs) {
			return true
		}
	}
	return false
}

func matchAlt(rs []rune, i int, alt smallAlt, fold bool) (int, bool) {
	for _, c := range alt.word {
		if i >= len(rs) {
			return 0, false
		}
		got := rs[i]
		if fold {
			got = foldASCII(got)
		}
		if got != c {
			return 0, false
		}
		i++
	}
	if alt.optDot && i < len(rs) && rs[i] == '.' {
		i++
	}
	return i, true
}

func boundary(rs []rune, i int) bool {
	left := i > 0 && isWord(rs[i-1])
	right := i < len(rs) && isWord(rs[i])
	return left != right
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	for _, alt := range smallAlts {
		for _, end := range altEnds(rs, i, alt, true) {
			if boundary(rs, end) {
				return string(rs[:i]) + pyCapitalize(string(rs[i:end])) + string(rs[end:])
			}
		}
	}
	return word
}

// Greedy optional dot first, then the match without it. SMALL_FIRST needs the
// backtrack because \b fails after a trailing period.
func altEnds(rs []rune, i int, alt smallAlt, fold bool) []int {
	j := i
	for _, c := range alt.word {
		if j >= len(rs) {
			return nil
		}
		got := rs[j]
		if fold {
			got = foldASCII(got)
		}
		if got != c {
			return nil
		}
		j++
	}
	ends := make([]int, 0, 2)
	if alt.optDot && j < len(rs) && rs[j] == '.' {
		ends = append(ends, j+1)
	}
	ends = append(ends, j)
	return ends
}

func applySmallLast(word string) string {
	rs := []rune(word)
	n := len(rs)
	for start := 0; start < n; start++ {
		if !boundary(rs, start) {
			continue
		}
		for _, alt := range smallAlts {
			end, ok := matchAlt(rs, start, alt, true)
			if !ok {
				continue
			}
			if end == n || (end+1 == n && isPunct(rs[end])) {
				return string(rs[:start]) + pyCapitalize(string(rs[start:n]))
			}
		}
	}
	return word
}

func applySubphrase(line string) string {
	rs := []rune(line)
	var b strings.Builder
	b.Grow(len(line))
	i := 0
	for i < len(rs) {
		if i+2 < len(rs) && isSubPunct(rs[i]) && rs[i+1] == ' ' {
			if end, ok := matchSmallPrefix(rs, i+2, false); ok {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2 : end])))
				i = end
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

func matchSmallPrefix(rs []rune, i int, fold bool) (int, bool) {
	for _, alt := range smallAlts {
		if end, ok := matchAlt(rs, i, alt, fold); ok {
			return end, true
		}
	}
	return 0, false
}

func isConsonantAcronym(word string) bool {
	rs := []rune(word)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		if !isASCIILetter(r) {
			return false
		}
		switch foldASCII(r) {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !isWord(rs[i]) {
		return word
	}
	return strings.ToUpper(string(rs[:i+1])) + string(rs[i+1:])
}

func pyCapitalize(s string) string {
	if s == "" {
		return ""
	}
	rs := []rune(s)
	return strings.ToUpper(string(rs[0])) + strings.ToLower(string(rs[1:]))
}
