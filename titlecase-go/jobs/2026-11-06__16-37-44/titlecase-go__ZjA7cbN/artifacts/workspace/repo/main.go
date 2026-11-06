package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

// Port of python-titlecase 2.4.1 titlecase(), using the stdlib `re` patterns
// (the `regex` module is not installed for the frozen answers). Defaults only:
// no callback, small words capitalized at the ends, blank lines dropped,
// original whitespace kept.

const (
	punctSet    = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
	subPunctSet = ":.;?!-–‒—―"
	consonants  = "bcdfghjklmnpqrstvwxz"
)

var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to",
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriter(os.Stdout)
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimRight(line, "\r\n")
			fmt.Fprintln(out, titlecase(line, true))
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	if err := out.Flush(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitLines(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, titlecaseLine(line, smallFirstLast))
	}
	return strings.Join(processed, "\n")
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitSpaces(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titleWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(joinParts(tc, spaces))
}

func titleWord(word string, allCaps bool) string {
	if allCaps && isUCInitials(word) {
		return word
	}
	if isAposSecond(word) {
		return applyApos(word)
	}
	if prefix, rest, ok := splitMac(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		return upperFirst(word)
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
	if isAllConsonants(word) && utf8.RuneCountInString(word) > 2 {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

// splitLines matches re.split(r'[\r\n]+', text), including one empty piece
// when the text starts or ends with a break.
func splitLines(text string) []string {
	rs := []rune(text)
	var lines []string
	var cur []rune
	i := 0
	for i < len(rs) {
		if rs[i] == '\r' || rs[i] == '\n' {
			lines = append(lines, string(cur))
			cur = nil
			for i < len(rs) && (rs[i] == '\r' || rs[i] == '\n') {
				i++
			}
			continue
		}
		cur = append(cur, rs[i])
		i++
	}
	lines = append(lines, string(cur))
	return lines
}

func splitSpaces(line string) (words, spaces []string) {
	var cur []rune
	flush := func() {
		words = append(words, string(cur))
		cur = nil
	}
	for _, r := range line {
		if unicode.IsSpace(r) {
			flush()
			spaces = append(spaces, string(r))
			continue
		}
		cur = append(cur, r)
	}
	flush()
	if len(words) == 0 {
		words = []string{""}
	}
	return words, spaces
}

func joinParts(words, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func isPunct(r rune) bool {
	return strings.ContainsRune(punctSet, r)
}

func isSubPunct(r rune) bool {
	return strings.ContainsRune(subPunctSet, r)
}

func isWordRune(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isASCIILetter(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z')
}

func isASCIIUpper(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func boundaryAt(rs []rune, i int) bool {
	if i < 0 || i > len(rs) {
		return false
	}
	left, right := false, false
	if i > 0 {
		left = isWordRune(rs[i-1])
	}
	if i < len(rs) {
		right = isWordRune(rs[i])
	}
	return left != right
}

func hasFoldPrefix(rs []rune, alt string) bool {
	ar := []rune(alt)
	if len(rs) < len(ar) {
		return false
	}
	for i, r := range ar {
		if unicode.ToLower(rs[i]) != unicode.ToLower(r) {
			return false
		}
	}
	return true
}

func firstSmall(rs []rune, i int, ok func(n int) bool) (int, bool) {
	if i < 0 || i > len(rs) {
		return 0, false
	}
	rest := rs[i:]
	for _, alt := range smallWords {
		n := utf8.RuneCountInString(alt)
		if hasFoldPrefix(rest, alt) && ok(n) {
			return n, true
		}
	}
	if len(rest) > 0 && unicode.ToLower(rest[0]) == 'v' {
		if len(rest) > 1 && rest[1] == '.' && ok(2) {
			return 2, true
		}
		if ok(1) {
			return 1, true
		}
	}
	if hasFoldPrefix(rest, "via") && ok(3) {
		return 3, true
	}
	if len(rest) >= 2 && unicode.ToLower(rest[0]) == 'v' && unicode.ToLower(rest[1]) == 's' {
		if len(rest) >= 3 && rest[2] == '.' && ok(3) {
			return 3, true
		}
		if ok(2) {
			return 2, true
		}
	}
	return 0, false
}

func isSmallWord(word string) bool {
	switch strings.ToLower(word) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	maxP := 0
	for maxP < len(rs) && isPunct(rs[maxP]) {
		maxP++
	}
	for p := maxP; p >= 0; p-- {
		n, ok := firstSmall(rs, p, func(n int) bool {
			return boundaryAt(rs, p+n)
		})
		if !ok {
			continue
		}
		return string(rs[:p]) + capitalize(string(rs[p:p+n])) + string(rs[p+n:])
	}
	return word
}

func applySmallLast(word string) string {
	rs := []rune(word)
	for i := 0; i <= len(rs); i++ {
		if !boundaryAt(rs, i) {
			continue
		}
		_, ok := firstSmall(rs, i, func(n int) bool {
			rest := len(rs) - (i + n)
			if rest == 0 {
				return true
			}
			return rest == 1 && isPunct(rs[i+n])
		})
		if ok {
			return string(rs[:i]) + capitalize(string(rs[i:]))
		}
	}
	return word
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(rs) {
		if isSubPunct(rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			if n, ok := firstSmall(rs, i+2, func(int) bool { return true }); ok {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(capitalize(string(rs[i+2 : i+2+n])))
				i += 2 + n
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return ""
	}
	return string(unicode.ToUpper(rs[0])) + strings.ToLower(string(rs[1:]))
}

func upperFirst(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return ""
	}
	rs[0] = unicode.ToUpper(rs[0])
	return string(rs)
}

func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !isWordRune(rs[i]) {
		return word
	}
	return strings.ToUpper(string(rs[:i+1])) + string(rs[i+1:])
}

func isAposSecond(word string) bool {
	rs := []rune(word)
	if len(rs) < 3 {
		return false
	}
	switch unicode.ToLower(rs[0]) {
	case 'd', 'o', 'l':
	default:
		return false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return false
	}
	rest := rs[2:]
	if len(rest) >= 2 && isAposClass(rest[len(rest)-2]) && isAposClass(rest[len(rest)-1]) {
		body := rest[:len(rest)-2]
		if len(body) >= 1 && allWord(body) {
			return true
		}
	}
	return allWord(rest)
}

func isAposClass(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func allWord(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if !isWordRune(r) {
			return false
		}
	}
	return true
}

func applyApos(word string) string {
	rs := []rune(word)
	var b strings.Builder
	if strings.ContainsRune("aeiouAEIOU", rs[0]) {
		b.WriteRune(unicode.ToUpper(rs[0]))
	} else {
		b.WriteRune(unicode.ToLower(rs[0]))
	}
	b.WriteRune(rs[1])
	b.WriteString(strings.ToUpper(string(rs[2:3])))
	b.WriteString(string(rs[3:]))
	return b.String()
}

func splitMac(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	p := string(rs[:2])
	if p != "Mc" && p != "mc" && p != "MC" {
		return "", "", false
	}
	tail := rs[2:]
	if len(tail) >= 2 && isWordRune(tail[0]) {
		return p, string(tail), true
	}
	return "", "", false
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
		if isWordRune(rs[i]) && rs[i+1] == '.' && isWordRune(rs[i+2]) {
			return true
		}
	}
	return false
}

func hasUCElsewhere(word string) bool {
	rs := []rune(word)
	for p := 0; p <= len(rs); p++ {
		if p > 0 && !isPunct(rs[p-1]) {
			break
		}
		if asciiThenUpper(rs[p:]) {
			return true
		}
	}
	return false
}

func asciiThenUpper(rs []rune) bool {
	n := 0
	for n < len(rs) && isASCIILetter(rs[n]) {
		n++
	}
	for letters := n; letters >= 1; letters-- {
		if letters < len(rs) && isASCIIUpper(rs[letters]) {
			return true
		}
	}
	return false
}

func isUCInitials(word string) bool {
	rs := []rune(word)
	if len(rs) == 0 {
		return false
	}
	var rec func(i int) bool
	rec = func(i int) bool {
		if i == len(rs) {
			return i > 0
		}
		if i+1 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && rec(i+2) {
			return true
		}
		if i+2 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && isASCIIUpper(rs[i+2]) && rec(i+3) {
			return true
		}
		return false
	}
	return rec(0)
}

func isAllConsonants(word string) bool {
	if word == "" {
		return false
	}
	for _, r := range word {
		if !strings.ContainsRune(consonants, unicode.ToLower(r)) {
			return false
		}
	}
	return true
}
