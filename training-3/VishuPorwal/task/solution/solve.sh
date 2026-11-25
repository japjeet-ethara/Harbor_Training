#!/bin/bash
set -euo pipefail

cd /workspace/repo
find . -type f -name '*.py' -delete

cat > go.mod << 'EOF'
module titlecase-go

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

const punctSet = "!\"“#$%&'‘()*+,\\-–‒—―./:;?@[]_`{|}~"

func isPunct(r rune) bool {
	return strings.ContainsRune(punctSet, r)
}

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isAZ(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	default:
		return false
	}
}

func boundary(rs []rune, i int) bool {
	var prev, next rune
	hasPrev := i > 0
	hasNext := i < len(rs)
	if hasPrev {
		prev = rs[i-1]
	}
	if hasNext {
		next = rs[i]
	}
	prevWord := hasPrev && isWord(prev)
	nextWord := hasNext && isWord(next)
	return prevWord != nextWord
}

func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return ""
	}
	var b strings.Builder
	b.WriteRune(unicode.ToUpper(rs[0]))
	for _, r := range rs[1:] {
		b.WriteRune(unicode.ToLower(r))
	}
	return b.String()
}

func isExactSmall(rs []rune) bool {
	switch strings.ToLower(string(rs)) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

// matchSmallPrefix returns the end index of the first small-word alternative
// that matches at i. When boundaryAfter is set, the match must end on a word
// boundary, with the same backtracking as v\.? and vs\.?.
func matchSmallPrefix(rs []rune, i int, boundaryAfter bool, caseSensitive bool) int {
	try := func(lit string) int {
		end := i
		for _, want := range lit {
			if end >= len(rs) {
				return -1
			}
			got := rs[end]
			if caseSensitive {
				if got != want {
					return -1
				}
			} else if unicode.ToLower(got) != unicode.ToLower(want) {
				return -1
			}
			end++
		}
		if boundaryAfter && !boundary(rs, end) {
			return -1
		}
		return end
	}
	lits := []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to"}
	for _, lit := range lits {
		if end := try(lit); end >= 0 {
			return end
		}
	}
	// v\.?  — greedy period, then boundary, then backtrack.
	if end := try("v."); end >= 0 {
		return end
	}
	if end := try("v"); end >= 0 {
		return end
	}
	if end := try("via"); end >= 0 {
		return end
	}
	// vs\.?
	if end := try("vs."); end >= 0 {
		return end
	}
	if end := try("vs"); end >= 0 {
		return end
	}
	return -1
}

func applySmallFirst(s string) string {
	rs := []rune(s)
	// Greedy leading punctuation, then backtrack until a small word matches.
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for n := maxPunct; n >= 0; n-- {
		end := matchSmallPrefix(rs, n, true, false)
		if end >= 0 {
			return string(rs[:n]) + pyCapitalize(string(rs[n:end])) + string(rs[end:])
		}
	}
	return s
}

func smallLits() []string {
	return []string{
		"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
	}
}

func applySmallLast(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	tryEnd := func(smallEnd int) (int, bool) {
		for _, lit := range smallLits() {
			litRunes := []rune(lit)
			start := smallEnd - len(litRunes)
			if start < 0 || !boundary(rs, start) {
				continue
			}
			if strings.EqualFold(string(rs[start:smallEnd]), lit) {
				return start, true
			}
		}
		return 0, false
	}
	// Prefer consuming one trailing punctuation mark, then backtrack.
	if isPunct(rs[len(rs)-1]) {
		if start, ok := tryEnd(len(rs) - 1); ok {
			return string(rs[:start]) + pyCapitalize(string(rs[start:]))
		}
	}
	if start, ok := tryEnd(len(rs)); ok {
		return string(rs[:start]) + pyCapitalize(string(rs[start:]))
	}
	return s
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(rs) {
		if i+2 < len(rs) && isSubPunct(rs[i]) && rs[i+1] == ' ' {
			end := matchSmallPrefix(rs, i+2, false, true)
			if end > i+2 {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2:end])))
				i = end
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

func isSmallWord(s string) bool {
	return isExactSmall([]rune(s))
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
	for {
		if i < len(rs) && isASCIILetter(rs[i]) {
			break
		}
		if i < len(rs) && isPunct(rs[i]) {
			i++
			continue
		}
		return false
	}
	first := true
	for i < len(rs) && isASCIILetter(rs[i]) {
		if !first && isAZ(rs[i]) {
			return true
		}
		first = false
		i++
	}
	return false
}

func ucInitials(s string) bool {
	rs := []rune(s)
	if len(rs) == 0 {
		return false
	}
	var rec func(i int) bool
	rec = func(i int) bool {
		if i == len(rs) {
			return true
		}
		if i+1 < len(rs) && isAZ(rs[i]) && rs[i+1] == '.' {
			if rec(i + 2) {
				return true
			}
		}
		if i+2 < len(rs) && isAZ(rs[i]) && rs[i+1] == '.' && isAZ(rs[i+2]) {
			if rec(i + 3) {
				return true
			}
		}
		return false
	}
	return rec(0)
}

func aposSecond(s string) (string, bool) {
	rs := []rune(s)
	if len(rs) < 3 {
		return "", false
	}
	first := unicode.ToLower(rs[0])
	if first != 'd' && first != 'o' && first != 'l' {
		return "", false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return "", false
	}
	rest := rs[2:]
	okRest := func(part []rune) bool {
		if len(part) == 0 {
			return false
		}
		for _, r := range part {
			if !isWord(r) {
				return false
			}
		}
		return true
	}
	isS := func(r rune) bool { return r == '\'' || r == 's' || r == 'S' }
	good := false
	if len(rest) >= 3 && isS(rest[len(rest)-2]) && isS(rest[len(rest)-1]) && okRest(rest[:len(rest)-2]) {
		good = true
	}
	if okRest(rest) {
		good = true
	}
	if !good {
		return "", false
	}
	var b strings.Builder
	vowels := "aeiouAEIOU"
	if !strings.ContainsRune(vowels, rs[0]) {
		b.WriteRune(unicode.ToLower(rs[0]))
	} else {
		b.WriteRune(unicode.ToUpper(rs[0]))
	}
	b.WriteRune(rs[1])
	b.WriteRune(unicode.ToUpper(rs[2]))
	b.WriteString(string(rs[3:]))
	return b.String(), true
}

func macMC(s string) (string, bool) {
	rs := []rune(s)
	if len(rs) < 4 {
		return "", false
	}
	var prefix []rune
	switch {
	case (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c':
		prefix = rs[:2]
	case rs[0] == 'M' && rs[1] == 'C':
		prefix = rs[:2]
	default:
		return "", false
	}
	rest := rs[2:]
	if len(rest) < 2 || !isWord(rest[0]) {
		return "", false
	}
	for _, r := range rest {
		if r == '\n' {
			return "", false
		}
	}
	return pyCapitalize(string(prefix)) + title(string(rest), true), true
}

func mrMrs(s string) (string, bool) {
	switch strings.ToLower(s) {
	case "mr", "mrs", "ms", "dr":
		rs := []rune(s)
		return string(unicode.ToUpper(rs[0])) + string(rs[1:]), true
	default:
		return "", false
	}
}

func capFirst(s string) string {
	rs := []rune(s)
	for i := 0; i <= len(rs); i++ {
		if i < len(rs) && isWord(rs[i]) {
			rs[i] = unicode.ToUpper(rs[i])
			return string(rs)
		}
		if i == len(rs) || !isPunct(rs[i]) {
			return s
		}
	}
	return s
}

func allConsonants(s string) bool {
	rs := []rune(s)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		switch r {
		case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z',
			'B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Z':
		default:
			return false
		}
	}
	return true
}

func splitWS(s string) (words, spaces []string) {
	var word []rune
	for _, r := range s {
		if unicode.IsSpace(r) {
			words = append(words, string(word))
			word = nil
			spaces = append(spaces, string(r))
		} else {
			word = append(word, r)
		}
	}
	words = append(words, string(word))
	return words, spaces
}

func processWord(word string, allCaps bool) string {
	if allCaps && ucInitials(word) {
		return word
	}
	if next, ok := aposSecond(word); ok {
		return next
	}
	if next, ok := macMC(word); ok {
		return next
	}
	if next, ok := mrMrs(word); ok {
		return next
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
			parts[i] = title(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = title(part, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if allConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitWS(line)
	for i, word := range words {
		words[i] = processWord(word, allCaps)
	}
	if smallFirstLast && len(words) > 0 {
		words[0] = applySmallFirst(words[0])
		words[len(words)-1] = applySmallLast(words[len(words)-1])
	}
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return applySubphrase(b.String())
}

func splitLines(text string) []string {
	// re.split(r'[\r\n]+', text), keeping the leading/trailing empty pieces.
	if text == "" {
		return []string{""}
	}
	var lines []string
	var cur []rune
	flush := func() {
		lines = append(lines, string(cur))
		cur = nil
	}
	rs := []rune(text)
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

func title(text string, smallFirstLast bool) string {
	lines := splitLines(text)
	for i, line := range lines {
		lines[i] = processLine(line, smallFirstLast)
	}
	return strings.Join(lines, "\n")
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 10*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	for in.Scan() {
		out.WriteString(title(in.Text(), true))
		out.WriteByte('\n')
	}
	out.Flush()
}
EOF
