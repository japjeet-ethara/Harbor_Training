package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

// Small words, in the same order as the original alternation.
// v\.? and vs\.? are expanded so the optional period is tried first.
var smallAlts = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

func main() {
	in := bufio.NewReader(os.Stdin)
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			if strings.HasSuffix(line, "\n") {
				line = line[:len(line)-1]
			}
			if strings.HasSuffix(line, "\r") {
				line = line[:len(line)-1]
			}
			os.Stdout.WriteString(titlecase(line, true))
			os.Stdout.WriteString("\n")
		}
		if err != nil {
			if err != io.EOF {
				os.Exit(1)
			}
			break
		}
	}
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitLines(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = titlecaseLine(line, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func splitLines(text string) []string {
	var lines []string
	start := 0
	for i := 0; i < len(text); i++ {
		if text[i] == '\n' || text[i] == '\r' {
			lines = append(lines, text[start:i])
			for i+1 < len(text) && (text[i+1] == '\n' || text[i+1] == '\r') {
				i++
			}
			start = i + 1
		}
	}
	lines = append(lines, text[start:])
	return lines
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitSpaces(line)
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

func joinWords(words, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func splitSpaces(line string) (words, spaces []string) {
	start := 0
	for i := 0; i < len(line); {
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

func processWord(word string, allCaps bool) string {
	if allCaps && ucInitials(word) {
		return word
	}
	if fixed, ok := aposFix(word); ok {
		return fixed
	}
	if rest, ok := macRest(word); ok {
		return "Mc" + titlecase(rest, true)
	}
	if isHonorific(word) {
		r, size := utf8.DecodeRuneInString(word)
		return string(unicode.ToUpper(r)) + word[size:]
	}
	if hasInlinePeriod(word) || (!allCaps && ucElsewhere(word)) {
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
	if isAllConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func isHonorific(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func isSmallWord(word string) bool {
	for _, alt := range smallAlts {
		if strings.EqualFold(word, alt) {
			return true
		}
	}
	return false
}

func ucInitials(s string) bool {
	if s == "" {
		return false
	}
	return matchInitials(s, 0)
}

func matchInitials(s string, i int) bool {
	if i == len(s) {
		return true
	}
	if i+2 <= len(s) && isAZ(s[i]) && s[i+1] == '.' && matchInitials(s, i+2) {
		return true
	}
	if i+3 <= len(s) && isAZ(s[i]) && s[i+1] == '.' && isAZ(s[i+2]) && matchInitials(s, i+3) {
		return true
	}
	return false
}

func isAZ(b byte) bool {
	return b >= 'A' && b <= 'Z'
}

func aposFix(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 {
		return "", false
	}
	switch rs[0] {
	case 'd', 'o', 'l', 'D', 'O', 'L':
	default:
		return "", false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return "", false
	}
	body := rs[2:]
	if allWord(body) || (len(body) >= 3 && aposTail(body[len(body)-2]) && aposTail(body[len(body)-1]) && allWord(body[:len(body)-2])) {
		if !allWord(body) && len(body[:len(body)-2]) == 0 {
			return "", false
		}
		out := make([]rune, len(rs))
		copy(out, rs)
		if isAposVowel(rs[0]) {
			out[0] = unicode.ToUpper(rs[0])
		} else {
			out[0] = unicode.ToLower(rs[0])
		}
		out[2] = unicode.ToUpper(rs[2])
		return string(out), true
	}
	return "", false
}

func isAposVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func aposTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
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

func macRest(word string) (string, bool) {
	var rest string
	switch {
	case strings.HasPrefix(word, "MC"):
		rest = word[2:]
	case len(word) >= 2 && (word[0] == 'M' || word[0] == 'm') && word[1] == 'c':
		rest = word[2:]
	default:
		return "", false
	}
	r, size := utf8.DecodeRuneInString(rest)
	if size == 0 || !isWord(r) || len(rest) == size {
		return "", false
	}
	return rest, true
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

func ucElsewhere(word string) bool {
	i := 0
	for i < len(word) {
		r, size := utf8.DecodeRuneInString(word[i:])
		if !isPunct(r) {
			break
		}
		i += size
	}
	n := 0
	for i+n < len(word) {
		c := word[i+n]
		if (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') {
			if n >= 1 && c >= 'A' && c <= 'Z' {
				return true
			}
			n++
			continue
		}
		break
	}
	return false
}

func isAllConsonants(word string) bool {
	if word == "" || utf8.RuneCountInString(word) <= 2 {
		return false
	}
	for i := 0; i < len(word); i++ {
		c := word[i]
		if c >= utf8.RuneSelf {
			return false
		}
		if c >= 'A' && c <= 'Z' {
			c += 'a' - 'A'
		}
		switch c {
		case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z':
		default:
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	i := 0
	for i < len(word) {
		r, size := utf8.DecodeRuneInString(word[i:])
		if !isPunct(r) {
			break
		}
		i += size
	}
	if i >= len(word) {
		return word
	}
	r, size := utf8.DecodeRuneInString(word[i:])
	if !isWord(r) {
		return word
	}
	return strings.ToUpper(word[:i+size]) + word[i+size:]
}

func applySmallFirst(word string) string {
	i := 0
	for i < len(word) {
		r, size := utf8.DecodeRuneInString(word[i:])
		if !isPunct(r) {
			break
		}
		i += size
	}
	rest := word[i:]
	for _, alt := range smallAlts {
		if len(rest) >= len(alt) && strings.EqualFold(rest[:len(alt)], alt) && boundaryAt(rest, len(alt)) {
			return word[:i] + capitalize(rest[:len(alt)]) + rest[len(alt):]
		}
	}
	return word
}

func applySmallLast(word string) string {
	for i := 0; i <= len(word); {
		if boundaryAt(word, i) {
			rest := word[i:]
			for _, alt := range smallAlts {
				if len(rest) < len(alt) || !strings.EqualFold(rest[:len(alt)], alt) {
					continue
				}
				tail := rest[len(alt):]
				if tail == "" {
					return word[:i] + capitalize(rest)
				}
				tr, tsize := utf8.DecodeRuneInString(tail)
				if tsize == len(tail) && isPunct(tr) {
					return word[:i] + capitalize(rest)
				}
			}
		}
		if i == len(word) {
			break
		}
		_, size := utf8.DecodeRuneInString(word[i:])
		i += size
	}
	return word
}

func applySubphrase(line string) string {
	var b strings.Builder
	for i := 0; i < len(line); {
		r, size := utf8.DecodeRuneInString(line[i:])
		if isSubPunct(r) && i+size < len(line) && line[i+size] == ' ' {
			rest := line[i+size+1:]
			if n, ok := matchLowerSmall(rest); ok {
				b.WriteRune(r)
				b.WriteByte(' ')
				b.WriteString(capitalize(rest[:n]))
				i += size + 1 + n
				continue
			}
		}
		b.WriteRune(r)
		i += size
	}
	return b.String()
}

func matchLowerSmall(s string) (int, bool) {
	for _, alt := range smallAlts {
		if strings.HasPrefix(s, alt) {
			return len(alt), true
		}
	}
	return 0, false
}

func capitalize(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + strings.ToLower(s[size:])
}

func boundaryAt(s string, i int) bool {
	var prev, next rune
	prevWord, nextWord := false, false
	if i > 0 {
		prev, _ = utf8.DecodeLastRuneInString(s[:i])
		prevWord = isWord(prev)
	}
	if i < len(s) {
		next, _ = utf8.DecodeRuneInString(s[i:])
		nextWord = isWord(next)
	}
	return prevWord != nextWord
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsNumber(r) || unicode.Is(unicode.Pc, r)
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/',
		':', ';', '?', '@', '[', '\\', ']', '_', '`', '{', '|', '}', '~',
		'\u2012', '\u2013', '\u2014', '\u2015', '\u2018', '\u201c':
		return true
	default:
		return false
	}
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func isPySpace(r rune) bool {
	switch r {
	case '\t', '\n', '\v', '\f', '\r', 0x1c, 0x1d, 0x1e, 0x1f, ' ',
		0x85, 0xa0, 0x1680,
		0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200a,
		0x2028, 0x2029, 0x202f, 0x205f, 0x3000:
		return true
	default:
		return false
	}
}
