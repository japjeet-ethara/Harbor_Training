package main

import (
	"bytes"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	var out strings.Builder
	for _, line := range splitStdin(data) {
		out.WriteString(titlecase(line, true))
		out.WriteByte('\n')
	}
	_, _ = os.Stdout.WriteString(out.String())
}

// A trailing newline ends the last line; it is not an extra empty record.
// A blank line before that final newline is kept.
func splitStdin(data []byte) []string {
	if len(data) == 0 {
		return nil
	}
	parts := bytes.Split(data, []byte{'\n'})
	if len(parts) > 0 && len(parts[len(parts)-1]) == 0 {
		parts = parts[:len(parts)-1]
	}
	lines := make([]string, len(parts))
	for i, part := range parts {
		lines[i] = string(part)
	}
	return lines
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitBreaks(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = titleLine(line, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func splitBreaks(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	start := 0
	for i := 0; i < len(text); {
		r, size := utf8.DecodeRuneInString(text[i:])
		if r != '\n' && r != '\r' {
			i += size
			continue
		}
		lines = append(lines, text[start:i])
		j := i + size
		for j < len(text) {
			rr, sz := utf8.DecodeRuneInString(text[j:])
			if rr != '\n' && rr != '\r' {
				break
			}
			j += sz
		}
		start = j
		i = j
	}
	return append(lines, text[start:])
}

func titleLine(line string, smallFirstLast bool) string {
	allCaps := line == strings.ToUpper(line)
	words, spaces := splitSpaces(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titleWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	var b strings.Builder
	for i, word := range tc {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return applySubphrase(b.String())
}

func splitSpaces(line string) (words, spaces []string) {
	var cur strings.Builder
	flush := func() {
		words = append(words, cur.String())
		cur.Reset()
	}
	for _, r := range line {
		if unicode.IsSpace(r) {
			flush()
			spaces = append(spaces, string(r))
			continue
		}
		cur.WriteRune(r)
	}
	flush()
	return words, spaces
}

func titleWord(word string, allCaps bool) string {
	if allCaps && isInitials(word) {
		return word
	}
	if next, ok := fixApos(word); ok {
		return next
	}
	if prefix, rest, ok := splitMac(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		r, size := utf8.DecodeRuneInString(word)
		return string(unicode.ToUpper(r)) + word[size:]
	}
	if hasInlinePeriod(word) || (!allCaps && hasInnerUpper(word)) {
		return word
	}
	if smallWord(word) {
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
	if utf8.RuneCountInString(word) > 2 && allConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func isInitials(word string) bool {
	rs := []rune(word)
	if len(rs) == 0 {
		return false
	}
	var walk func(int) bool
	walk = func(i int) bool {
		if i == len(rs) {
			return true
		}
		if i+1 < len(rs) && isAZ(rs[i]) && rs[i+1] == '.' && walk(i+2) {
			return true
		}
		if i+2 < len(rs) && isAZ(rs[i]) && rs[i+1] == '.' && isAZ(rs[i+2]) && walk(i+3) {
			return true
		}
		return false
	}
	return walk(0)
}

func isAZ(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func fixApos(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) || (rs[1] != '\'' && rs[1] != '‘') || !isWord(rs[2]) {
		return "", false
	}
	i := 2
	for i < len(rs) && isWord(rs[i]) {
		i++
	}
	if i != len(rs) {
		if i+2 != len(rs) || !isAposTail(rs[i]) || !isAposTail(rs[i+1]) {
			return "", false
		}
	}
	if isVowel(rs[0]) {
		rs[0] = unicode.ToUpper(rs[0])
	} else {
		rs[0] = unicode.ToLower(rs[0])
	}
	rs[2] = unicode.ToUpper(rs[2])
	return string(rs), true
}

func isDOL(r rune) bool {
	switch r {
	case 'd', 'o', 'l', 'D', 'O', 'L':
		return true
	default:
		return false
	}
}

func isVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func isAposTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func splitMac(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	mc := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c'
	upper := rs[0] == 'M' && rs[1] == 'C'
	if !mc && !upper {
		return "", "", false
	}
	if !isWord(rs[2]) {
		return "", "", false
	}
	for _, r := range rs[3:] {
		if r == '\n' {
			return "", "", false
		}
	}
	return string(rs[:2]), string(rs[2:]), true
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

func hasInnerUpper(word string) bool {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !isASCIILetter(rs[i]) {
		return false
	}
	for _, r := range rs[i+1:] {
		if !isASCIILetter(r) {
			break
		}
		if r >= 'A' && r <= 'Z' {
			return true
		}
	}
	return false
}

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func smallWord(word string) bool {
	rs := []rune(word)
	for _, alt := range smallAlts {
		if n := matchAlt(rs, alt); n == len(rs) {
			return true
		}
	}
	return false
}

var smallAlts = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to", "v", "via", "vs",
}

func matchCore(rs []rune, alt string) int {
	want := []rune(alt)
	if len(rs) < len(want) {
		return -1
	}
	for i, r := range want {
		if unicode.ToLower(rs[i]) != r {
			return -1
		}
	}
	return len(want)
}

func matchAlt(rs []rune, alt string) int {
	n := matchCore(rs, alt)
	if n < 0 {
		return -1
	}
	if (alt == "v" || alt == "vs") && n < len(rs) && rs[n] == '.' {
		n++
	}
	return n
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	for _, alt := range smallAlts {
		base := matchCore(rs[i:], alt)
		if base < 0 {
			continue
		}
		// v\.? and vs\.? are greedy, but a following word-boundary can force
		// the optional period to be given back.
		if (alt == "v" || alt == "vs") && i+base < len(rs) && rs[i+base] == '.' && wordBoundary(rs, i+base+1) {
			end := i + base + 1
			return string(rs[:i]) + capitalize(string(rs[i:end])) + string(rs[end:])
		}
		if wordBoundary(rs, i+base) {
			end := i + base
			return string(rs[:i]) + capitalize(string(rs[i:end])) + string(rs[end:])
		}
	}
	return word
}

func applySmallLast(word string) string {
	rs := []rune(word)
	for start := 0; start <= len(rs); start++ {
		if !wordBoundary(rs, start) {
			continue
		}
		for _, alt := range smallAlts {
			n := matchAlt(rs[start:], alt)
			if n < 0 {
				continue
			}
			end := start + n
			if end < len(rs) && isPunct(rs[end]) {
				end++
			}
			if end == len(rs) {
				return string(rs[:start]) + capitalize(string(rs[start:]))
			}
		}
	}
	return word
}

func wordBoundary(rs []rune, i int) bool {
	var left, right bool
	if i > 0 {
		left = isWord(rs[i-1])
	}
	if i < len(rs) {
		right = isWord(rs[i])
	}
	return left != right
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && isSubPunct(rs[i]) && rs[i+1] == ' ' {
			if n, ok := firstSmallPrefix(rs[i+2:]); ok {
				b.WriteRune(rs[i])
				b.WriteByte(' ')
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

func firstSmallPrefix(rs []rune) (int, bool) {
	for _, alt := range smallAlts {
		if n := matchAlt(rs, alt); n >= 0 {
			return n, true
		}
	}
	return 0, false
}

func allConsonants(word string) bool {
	if word == "" {
		return false
	}
	for _, r := range word {
		switch unicode.ToLower(r) {
		case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z':
		default:
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	rs := []rune(word)
	for i := 0; i < len(rs); i++ {
		if isWord(rs[i]) {
			for j := 0; j < i; j++ {
				if !isPunct(rs[j]) {
					return word
				}
			}
			rs[i] = unicode.ToUpper(rs[i])
			return string(rs)
		}
		if !isPunct(rs[i]) {
			return word
		}
	}
	return word
}

func capitalize(s string) string {
	if s == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + strings.ToLower(s[size:])
}

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsDigit(r)
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '“', '#', '$', '%', '&', '\'', '‘', '(', ')', '*', '+', ',',
		'-', '–', '‒', '—', '―', '.', '/', ':', ';', '?', '@', '[', '\\', ']',
		'_', '`', '{', '|', '}', '~':
		return true
	default:
		return false
	}
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	default:
		return false
	}
}
