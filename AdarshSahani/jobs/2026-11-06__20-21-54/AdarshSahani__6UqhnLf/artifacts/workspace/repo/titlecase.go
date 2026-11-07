package main

import (
	"strings"
	"unicode"
)

// PUNCT from the Python source (used inside character classes there).
const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// SMALL alternatives in the exact order of the Python alternation, with the
// greedy optional "." of `v\.?` and `vs\.?` expanded (longest first).
var smallAlts = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
	"on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

var smallWordSet = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

func isPunct(r rune) bool { return strings.ContainsRune(punctChars, r) }

func isLetter(r rune) bool { return unicode.IsLetter(r) }

func isWordRune(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.IsMark(r) || r == '_'
}

// isBoundary reports whether there is a regex \b between rs[pos-1] and rs[pos].
func isBoundary(rs []rune, pos int) bool {
	left := pos-1 >= 0 && pos-1 < len(rs) && isWordRune(rs[pos-1])
	right := pos >= 0 && pos < len(rs) && isWordRune(rs[pos])
	return left != right
}

// capitalize mimics Python str.capitalize(): first char upper, the rest lower.
func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	out := make([]rune, len(rs))
	out[0] = unicode.ToUpper(rs[0])
	for i := 1; i < len(rs); i++ {
		out[i] = unicode.ToLower(rs[i])
	}
	return string(out)
}

func isSmallWord(s string) bool { return smallWordSet[strings.ToLower(s)] }

// UC_INITIALS: ^(?:[Lu]\.|[Lu]\.[Lu])+$
func ucInitials(w []rune) bool {
	n := len(w)
	if n == 0 {
		return false
	}
	reach := make([]bool, n+1)
	for i := 0; i < n; i++ {
		if i != 0 && !reach[i] {
			continue
		}
		if i+1 < n && unicode.IsUpper(w[i]) && w[i+1] == '.' {
			reach[i+2] = true
			if i+2 < n && unicode.IsUpper(w[i+2]) {
				reach[i+3] = true
			}
		}
	}
	return reach[n]
}

// APOS_SECOND: ^[dol]['‘][Letter]+(?:['s]{2})?$  (case-insensitive)
func aposSecond(w []rune) bool {
	if len(w) < 3 {
		return false
	}
	switch w[0] {
	case 'd', 'o', 'l', 'D', 'O', 'L':
	default:
		return false
	}
	if w[1] != '\'' && w[1] != '‘' {
		return false
	}
	inSet := func(r rune) bool { return r == '\'' || r == 's' || r == 'S' }
	rest := w[2:]
	for k := 1; k <= len(rest); k++ {
		if !isLetter(rest[k-1]) {
			break
		}
		if k == len(rest) {
			return true
		}
		if len(rest)-k == 2 && inSet(rest[k]) && inSet(rest[k+1]) {
			return true
		}
	}
	return false
}

// MAC_MC: ^([Mm]c|MC)(\w.+)
func macMc(w []rune) (prefix string, rest string, ok bool) {
	if len(w) < 2 {
		return "", "", false
	}
	if !((w[0] == 'M' || w[0] == 'm') && w[1] == 'c') && !(w[0] == 'M' && w[1] == 'C') {
		return "", "", false
	}
	r := w[2:]
	if len(r) >= 2 && isWordRune(r[0]) {
		return string(w[:2]), string(r), true
	}
	return "", "", false
}

// INLINE_PERIOD: [Letter][.][Letter] anywhere.
func inlinePeriod(w []rune) bool {
	for i := 0; i+2 < len(w); i++ {
		if isLetter(w[i]) && w[i+1] == '.' && isLetter(w[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE.match: [PUNCT]*?[Letter]+[Uppercase_Letter]+?
func ucElsewhere(w []rune) bool {
	i := 0
	for i < len(w) && isPunct(w[i]) {
		i++
	}
	j := i
	for j < len(w) && isLetter(w[j]) {
		j++
	}
	for k := i + 1; k < j; k++ {
		if unicode.IsUpper(w[k]) {
			return true
		}
	}
	return false
}

func isAllConsonants(w []rune) bool {
	if len(w) == 0 {
		return false
	}
	for _, r := range w {
		switch r {
		case 'a', 'e', 'i', 'o', 'u', 'y', 'A', 'E', 'I', 'O', 'U', 'Y':
			return false
		}
		if !((r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')) {
			return false
		}
	}
	return true
}

// CAPFIRST.sub(upper): ^[PUNCT]*?([Letter])
func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i < len(rs) && isLetter(rs[i]) {
		rs[i] = unicode.ToUpper(rs[i])
	}
	return string(rs)
}

// SMALL_FIRST: ^([PUNCT]*)(SMALL)\b  -> group2.capitalize()
func smallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	for _, cand := range smallAlts {
		n := len([]rune(cand))
		if i+n > len(rs) {
			continue
		}
		if !strings.EqualFold(string(rs[i:i+n]), cand) {
			continue
		}
		if !isBoundary(rs, i+n) {
			continue
		}
		return string(rs[:i]) + capitalize(string(rs[i:i+n])) + string(rs[i+n:])
	}
	return word
}

// SMALL_LAST: \b(SMALL)[PUNCT]?$  -> group0.capitalize()
func smallLast(word string) string {
	rs := []rune(word)
	for p := 0; p < len(rs); p++ {
		if !isBoundary(rs, p) {
			continue
		}
		t := string(rs[p:])
		tr := rs[p:]
		if isSmallWord(t) ||
			(len(tr) >= 2 && isPunct(tr[len(tr)-1]) && isSmallWord(string(tr[:len(tr)-1]))) {
			return string(rs[:p]) + capitalize(t)
		}
	}
	return word
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	}
	return false
}

// SUBPHRASE: ([:.;?!\-–‒—―][ ])(SMALL)   (case-sensitive, no \b) -> group2.capitalize()
func subphrase(s string) string {
	rs := []rune(s)
	var out []rune
	i := 0
	for i < len(rs) {
		if isSubPunct(rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			matched := ""
			for _, cand := range smallAlts {
				if strings.HasPrefix(string(rs[i+2:]), cand) {
					matched = cand
					break
				}
			}
			if matched != "" {
				out = append(out, rs[i], ' ')
				out = append(out, []rune(capitalize(matched))...)
				i += 2 + len([]rune(matched))
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

func splitBy(s string, sep string) []string { return strings.Split(s, sep) }

// titlecase mirrors titlecase.titlecase(text, small_first_last=...) for text
// without line breaks (callers split on lines first).
func titlecase(text string, smallFirstLast bool) string {
	// regex.split('[\r\n]+', text)
	lines := splitLines(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, processLine(line, smallFirstLast))
	}
	return strings.Join(processed, "\n")
}

func splitLines(text string) []string {
	var lines []string
	var cur []rune
	inBreak := false
	for _, r := range text {
		if r == '\r' || r == '\n' {
			if !inBreak {
				lines = append(lines, string(cur))
				cur = cur[:0]
				inBreak = true
			}
			continue
		}
		inBreak = false
		cur = append(cur, r)
	}
	lines = append(lines, string(cur))
	return lines
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line

	// regex.split(r'(\s)', line)
	var words, spaces []string
	var cur []rune
	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, string(cur))
			spaces = append(spaces, string(r))
			cur = cur[:0]
		} else {
			cur = append(cur, r)
		}
	}
	words = append(words, string(cur))

	tc := make([]string, 0, len(words))
	for _, word := range words {
		tc = append(tc, processWord(word, allCaps))
	}

	if smallFirstLast && len(tc) > 0 {
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

func processWord(word string, allCaps bool) string {
	rs := []rune(word)

	if allCaps && ucInitials(rs) {
		return word
	}

	if aposSecond(rs) {
		first := rs[0]
		var f rune
		if strings.ContainsRune("aeiouAEIOU", first) {
			f = unicode.ToUpper(first)
		} else {
			f = unicode.ToLower(first)
		}
		out := []rune{f, rs[1], unicode.ToUpper(rs[2])}
		out = append(out, rs[3:]...)
		return string(out)
	}

	if prefix, rest, ok := macMc(rs); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}

	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return string(unicode.ToUpper(rs[0])) + string(rs[1:])
	}

	if inlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}
	if isSmallWord(word) {
		return strings.ToLower(word)
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := splitBy(word, "/")
		for i, t := range parts {
			parts[i] = titlecase(t, false)
		}
		return strings.Join(parts, "/")
	}

	if strings.Contains(word, "-") {
		parts := splitBy(word, "-")
		for i, t := range parts {
			parts[i] = titlecase(t, false)
		}
		return strings.Join(parts, "-")
	}

	if allCaps {
		word = strings.ToLower(word)
		rs = []rune(word)
	}

	if isAllConsonants(rs) && len(rs) > 2 {
		return strings.ToUpper(word)
	}

	return capFirst(word)
}
