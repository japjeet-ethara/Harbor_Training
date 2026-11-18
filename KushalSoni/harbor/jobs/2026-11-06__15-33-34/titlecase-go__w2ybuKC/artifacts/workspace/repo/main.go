package main

import (
	"io"
	"os"
	"strings"
	"unicode"
)

const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

func main() {
	in, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	if len(in) == 0 {
		return
	}
	text := string(in)
	parts := strings.Split(text, "\n")
	if strings.HasSuffix(text, "\n") {
		parts = parts[:len(parts)-1]
	}
	for i, line := range parts {
		parts[i] = strings.TrimSuffix(line, "\r")
	}
	var b strings.Builder
	for i, line := range parts {
		if i > 0 {
			b.WriteByte('\n')
		}
		b.WriteString(titlecase(line))
	}
	if strings.HasSuffix(text, "\n") {
		b.WriteByte('\n')
	}
	_, _ = os.Stdout.WriteString(b.String())
}

func titlecase(text string) string {
	lines := splitBreaks(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = processLine(line, true)
	}
	return strings.Join(out, "\n")
}

func splitBreaks(text string) []string {
	rs := []rune(text)
	if len(rs) == 0 {
		return []string{""}
	}
	var lines []string
	var cur []rune
	flush := func() {
		lines = append(lines, string(cur))
		cur = cur[:0]
	}
	for i := 0; i < len(rs); i++ {
		if rs[i] == '\r' || rs[i] == '\n' {
			flush()
			for i+1 < len(rs) && (rs[i+1] == '\r' || rs[i+1] == '\n') {
				i++
			}
			continue
		}
		cur = append(cur, rs[i])
	}
	flush()
	return lines
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitSpaces(line)
	tc := make([][]rune, len(words))
	for i, word := range words {
		tc[i] = processWord([]rune(word), allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	joined := interleave(tc, spaces)
	return string(applySubphrase([]rune(joined)))
}

func processWord(word []rune, allCaps bool) []rune {
	if allCaps && isInitials(word) {
		return word
	}
	if isApostropheName(word) {
		return applyApostrophe(word)
	}
	if pre, rest, ok := splitMac(word); ok {
		body := []rune(titlecase(string(rest)))
		return append(capitalize(pre), body...)
	}
	if isHonorific(word) {
		return append([]rune(strings.ToUpper(string(word[:1]))), word[1:]...)
	}
	if hasInlinePeriod(word) || (!allCaps && hasUpperElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return []rune(strings.ToLower(string(word)))
	}
	if containsRune(word, '/') && !containsString(word, "//") {
		return recasePieces(word, '/', false)
	}
	if containsRune(word, '-') {
		return recasePieces(word, '-', false)
	}
	if allCaps {
		word = []rune(strings.ToLower(string(word)))
	}
	if len(word) > 2 && allConsonants(word) {
		return []rune(strings.ToUpper(string(word)))
	}
	return capFirst(word)
}

func recasePieces(word []rune, sep rune, smallFirstLast bool) []rune {
	parts := strings.Split(string(word), string(sep))
	for i, part := range parts {
		parts[i] = processLine(part, smallFirstLast)
	}
	return []rune(strings.Join(parts, string(sep)))
}

func splitSpaces(line string) ([]string, []string) {
	var parts []string
	var cur []rune
	for _, r := range line {
		if isPySpace(r) {
			parts = append(parts, string(cur), string(r))
			cur = cur[:0]
		} else {
			cur = append(cur, r)
		}
	}
	parts = append(parts, string(cur))
	words := make([]string, 0, (len(parts)+1)/2)
	spaces := make([]string, 0, len(parts)/2)
	for i, part := range parts {
		if i%2 == 0 {
			words = append(words, part)
		} else {
			spaces = append(spaces, part)
		}
	}
	return words, spaces
}

func interleave(words [][]rune, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(string(word))
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func isPySpace(r rune) bool {
	if unicode.Is(unicode.Z, r) {
		return true
	}
	switch r {
	case '\t', '\n', '\v', '\f', '\r', '\u0085', '\u001c', '\u001d', '\u001e', '\u001f':
		return true
	default:
		return false
	}
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

func isPunct(r rune) bool {
	return strings.ContainsRune(punctChars, r)
}

func isSubphraseSep(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	default:
		return false
	}
}

func containsRune(rs []rune, r rune) bool {
	for _, c := range rs {
		if c == r {
			return true
		}
	}
	return false
}

func containsString(rs []rune, s string) bool {
	return strings.Contains(string(rs), s)
}

func capitalize(rs []rune) []rune {
	if len(rs) == 0 {
		return rs
	}
	first := []rune(strings.ToUpper(string(rs[:1])))
	rest := []rune(strings.ToLower(string(rs[1:])))
	return append(first, rest...)
}

func capFirst(rs []rune) []rune {
	for i, r := range rs {
		if isWord(r) {
			head := []rune(strings.ToUpper(string(rs[:i+1])))
			return append(head, rs[i+1:]...)
		}
		if !isPunct(r) {
			return rs
		}
	}
	return rs
}

func hasInlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if isWord(rs[i]) && rs[i+1] == '.' && isWord(rs[i+2]) {
			return true
		}
	}
	return false
}

func hasUpperElsewhere(rs []rune) bool {
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for p := 0; p <= maxPunct; p++ {
		s := rs[p:]
		j := 0
		for j < len(s) && isASCIILetter(s[j]) {
			j++
		}
		for k := 1; k < j; k++ {
			if isASCIIUpper(s[k]) {
				return true
			}
		}
	}
	return false
}

func isInitials(rs []rune) bool {
	var walk func(int) bool
	walk = func(i int) bool {
		if i == len(rs) {
			return i > 0
		}
		if i+1 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && walk(i+2) {
			return true
		}
		if i+2 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && isASCIIUpper(rs[i+2]) && walk(i+3) {
			return true
		}
		return false
	}
	return len(rs) > 0 && walk(0)
}

func isApostropheName(rs []rune) bool {
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
	i := 2
	if !isWord(rs[i]) {
		return false
	}
	for i < len(rs) && isWord(rs[i]) {
		i++
	}
	if i == len(rs) {
		return true
	}
	return len(rs)-i == 2 && isApostropheSuffix(rs[i]) && isApostropheSuffix(rs[i+1])
}

func isApostropheSuffix(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func applyApostrophe(rs []rune) []rune {
	var first []rune
	if strings.ContainsRune("aeiouAEIOU", rs[0]) {
		first = []rune(strings.ToUpper(string(rs[:1])))
	} else {
		first = []rune(strings.ToLower(string(rs[:1])))
	}
	third := []rune(strings.ToUpper(string(rs[2:3])))
	out := append(first, rs[1])
	out = append(out, third...)
	out = append(out, rs[3:]...)
	return out
}

func splitMac(rs []rune) ([]rune, []rune, bool) {
	if len(rs) < 4 {
		return nil, nil, false
	}
	mac := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c'
	upper := rs[0] == 'M' && rs[1] == 'C'
	if !mac && !upper {
		return nil, nil, false
	}
	rest := rs[2:]
	if !isWord(rest[0]) {
		return nil, nil, false
	}
	end := 1
	for end < len(rest) && rest[end] != '\n' {
		end++
	}
	if end < 2 {
		return nil, nil, false
	}
	return rs[:2], rest[:end], true
}

func isHonorific(rs []rune) bool {
	switch strings.ToLower(string(rs)) {
	case "m", "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func isSmallWord(rs []rune) bool {
	for _, end := range smallEnds(rs, 0, true) {
		if end == len(rs) {
			return true
		}
	}
	return false
}

func smallEnds(rs []rune, i int, fold bool) []int {
	words := []struct {
		text string
		dot  bool
	}{
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
	var ends []int
	for _, word := range words {
		w := []rune(word.text)
		if i+len(w) > len(rs) {
			continue
		}
		got := string(rs[i : i+len(w)])
		if fold {
			if !strings.EqualFold(got, word.text) {
				continue
			}
		} else if got != word.text {
			continue
		}
		end := i + len(w)
		if word.dot && end < len(rs) && rs[end] == '.' {
			ends = append(ends, end+1)
		}
		ends = append(ends, end)
	}
	return ends
}

func applySmallFirst(rs []rune) []rune {
	n := 0
	for n < len(rs) && isPunct(rs[n]) {
		n++
	}
	for punct := n; punct >= 0; punct-- {
		for _, end := range smallEnds(rs, punct, true) {
			if isBoundary(rs, end) {
				mid := capitalize(rs[punct:end])
				out := append(append([]rune{}, rs[:punct]...), mid...)
				return append(out, rs[end:]...)
			}
		}
	}
	return rs
}

func applySmallLast(rs []rune) []rune {
	for i := 0; i <= len(rs); i++ {
		if !isBoundary(rs, i) {
			continue
		}
		for _, end := range smallEnds(rs, i, true) {
			if end < len(rs) && isPunct(rs[end]) && end+1 == len(rs) {
				return append(append([]rune{}, rs[:i]...), capitalize(rs[i:])...)
			}
			if end == len(rs) {
				return append(append([]rune{}, rs[:i]...), capitalize(rs[i:])...)
			}
		}
	}
	return rs
}

func isBoundary(rs []rune, i int) bool {
	left, right := false, false
	if i > 0 {
		left = isWord(rs[i-1])
	}
	if i < len(rs) {
		right = isWord(rs[i])
	}
	return left != right
}

func applySubphrase(rs []rune) []rune {
	for i := 0; i+2 <= len(rs); i++ {
		if !isSubphraseSep(rs[i]) || rs[i+1] != ' ' {
			continue
		}
		ends := smallEnds(rs, i+2, false)
		if len(ends) == 0 {
			continue
		}
		end := ends[0]
		mid := capitalize(rs[i+2 : end])
		out := append(append([]rune{}, rs[:i+2]...), mid...)
		rs = append(out, rs[end:]...)
		i = i + 1 + len(mid)
	}
	return rs
}

func allConsonants(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if !isASCIILetter(r) {
			return false
		}
		switch unicode.ToLower(r) {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}
