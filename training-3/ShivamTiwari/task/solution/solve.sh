#!/bin/bash
set -euo pipefail
cd /workspace/repo
cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF
cat > main.go << 'EOF'
package main

import (
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

// Small words in the same order as the Python SMALL alternation
// (a|an|and|...|v\.?|via|vs\.?). Python's re module tries alternatives left to
// right and lets \.? backtrack, so "v." and "vs." are listed before "v"/"vs".
var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

func main() {
	in, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	var b strings.Builder
	for _, line := range splitLines(string(in)) {
		b.WriteString(titlecase(line, true))
		b.WriteByte('\n')
	}
	_, _ = os.Stdout.WriteString(b.String())
}

func splitLines(s string) []string {
	if s == "" {
		return nil
	}
	var lines []string
	start := 0
	for i := 0; i < len(s); {
		if n := breakLen(s, i); n > 0 {
			lines = append(lines, s[start:i])
			i += n
			start = i
			continue
		}
		_, size := utf8.DecodeRuneInString(s[i:])
		if size < 1 {
			size = 1
		}
		i += size
	}
	if start < len(s) {
		lines = append(lines, s[start:])
	}
	return lines
}

func breakLen(s string, i int) int {
	if i >= len(s) {
		return 0
	}
	switch s[i] {
	case '\n', '\v', '\f', 0x1c, 0x1d, 0x1e:
		return 1
	case '\r':
		if i+1 < len(s) && s[i+1] == '\n' {
			return 2
		}
		return 1
	}
	r, size := utf8.DecodeRuneInString(s[i:])
	switch r {
	case '\u0085', '\u2028', '\u2029':
		return size
	}
	return 0
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = titlecaseLine(line, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func splitNewlines(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	start := 0
	for i := 0; i < len(text); {
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
		tc[i] = titleWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(interleave(tc, spaces))
}

func splitSpaces(line string) (words, spaces []string) {
	var cur strings.Builder
	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, cur.String())
			cur.Reset()
			spaces = append(spaces, string(r))
			continue
		}
		cur.WriteRune(r)
	}
	words = append(words, cur.String())
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

func titleWord(word string, allCaps bool) string {
	if allCaps && isInitials(word) {
		return word
	}
	if changed, ok := apostrophe(word); ok {
		return changed
	}
	if prefix, rest, ok := macPrefix(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		rs := []rune(word)
		return strings.ToUpper(string(rs[0])) + string(rs[1:])
	}
	if hasInlinePeriod(word) || (!allCaps && hasUpperLater(word)) {
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
	if runeLen(word) > 2 && allConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func isInitials(word string) bool {
	rs := []rune(word)
	if len(rs) == 0 {
		return false
	}
	return matchInitials(rs, 0, false)
}

func matchInitials(rs []rune, i int, matched bool) bool {
	if i == len(rs) {
		return matched
	}
	if i+3 <= len(rs) && isUpperLetter(rs[i]) && rs[i+1] == '.' && isUpperLetter(rs[i+2]) {
		if matchInitials(rs, i+3, true) {
			return true
		}
	}
	if i+2 <= len(rs) && isUpperLetter(rs[i]) && rs[i+1] == '.' {
		if matchInitials(rs, i+2, true) {
			return true
		}
	}
	return false
}

func apostrophe(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) {
		return "", false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return "", false
	}
	i := 2
	if !isLetter(rs[i]) {
		return "", false
	}
	i++
	for i < len(rs) && isLetter(rs[i]) {
		i++
	}
	if i != len(rs) {
		if i+2 != len(rs) || !isApostropheOrS(rs[i]) || !isApostropheOrS(rs[i+1]) {
			return "", false
		}
	}
	var b strings.Builder
	if isVowel(rs[0]) {
		b.WriteString(strings.ToUpper(string(rs[0])))
	} else {
		b.WriteString(strings.ToLower(string(rs[0])))
	}
	b.WriteRune(rs[1])
	b.WriteString(strings.ToUpper(string(rs[2])))
	b.WriteString(string(rs[3:]))
	return b.String(), true
}

func isDOL(r rune) bool {
	switch r {
	case 'd', 'D', 'o', 'O', 'l', 'L':
		return true
	}
	return false
}

func isVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	}
	return false
}

func isApostropheOrS(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func macPrefix(word string) (string, string, bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	prefix := string(rs[:2])
	if prefix != "Mc" && prefix != "mc" && prefix != "MC" {
		return "", "", false
	}
	if !isWord(rs[2]) {
		return "", "", false
	}
	return prefix, string(rs[2:]), true
}

func isHonorific(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

func hasInlinePeriod(word string) bool {
	rs := []rune(word)
	for i := 0; i+2 < len(rs); i++ {
		if isPyWord(rs[i]) && rs[i+1] == '.' && isPyWord(rs[i+2]) {
			return true
		}
	}
	return false
}

// hasUpperLater mirrors Python re's UC_ELSEWHERE = [PUNCT]*?[a-zA-Z]+[A-Z]+?:
// only ASCII letters participate, and the uppercase must appear after at least
// one earlier ASCII letter.
func hasUpperLater(word string) bool {
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
	for _, alt := range smallWords {
		if strings.EqualFold(word, alt) {
			return true
		}
	}
	return false
}

func allConsonants(word string) bool {
	if word == "" {
		return false
	}
	for _, r := range word {
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

// capFirst mirrors Python re's CAPFIRST = ^[PUNCT]*?([\w]). A non-greedy
// punctuation prefix stops at the first word character, and "_" (which is both
// punctuation and \w in Python) counts as that word character.
func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) && !isPyWord(rs[i]) {
		i++
	}
	if i < len(rs) && isPyWord(rs[i]) {
		return string(rs[:i]) + strings.ToUpper(string(rs[i])) + string(rs[i+1:])
	}
	return word
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	n, ok := smallAt(rs, i, true, true)
	if !ok {
		return word
	}
	return string(rs[:i]) + capitalize(string(rs[i:i+n])) + string(rs[i+n:])
}

// smallAt implements the leftmost-first alternation used by Python's re module.
// Alternatives are tried in smallWords order; needBoundary adds the trailing \b
// used by SMALL_FIRST/SMALL_LAST, and fold enables the re.I flag.
func smallAt(rs []rune, i int, fold, needBoundary bool) (int, bool) {
	for _, alt := range smallWords {
		al := []rune(alt)
		n := len(al)
		if i+n > len(rs) {
			continue
		}
		seg := string(rs[i : i+n])
		if fold {
			if !strings.EqualFold(seg, alt) {
				continue
			}
		} else if seg != alt {
			continue
		}
		if needBoundary && !boundary(rs, i+n) {
			continue
		}
		return n, true
	}
	return 0, false
}

func applySmallLast(word string) string {
	rs := []rune(word)
	n := len(rs)
	best := -1
	consider := func(smallEnd int) {
		if smallEnd < 0 || smallEnd > n {
			return
		}
		if smallEnd < n && (n-smallEnd != 1 || !isPunct(rs[smallEnd])) {
			return
		}
		for _, alt := range smallWords {
			al := []rune(alt)
			width := len(al)
			if width > smallEnd {
				continue
			}
			start := smallEnd - width
			if !strings.EqualFold(string(rs[start:smallEnd]), alt) {
				continue
			}
			if !boundary(rs, start) {
				continue
			}
			if best == -1 || start < best {
				best = start
			}
		}
	}
	consider(n)
	consider(n - 1)
	if best < 0 {
		return word
	}
	return string(rs[:best]) + capitalize(string(rs[best:]))
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && isSubPunct(rs[i]) && rs[i+1] == ' ' {
			if n, ok := smallAt(rs[i+2:], 0, false, false); ok {
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
	if s == "" {
		return ""
	}
	rs := []rune(s)
	return strings.ToUpper(string(rs[0])) + strings.ToLower(string(rs[1:]))
}

func runeLen(s string) int {
	return utf8.RuneCountInString(s)
}

func isLetter(r rune) bool { return unicode.IsLetter(r) }

func isUpperLetter(r rune) bool { return unicode.Is(unicode.Lu, r) }

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isASCIIUpper(r rune) bool { return r >= 'A' && r <= 'Z' }

// isPyWord matches Python re's \w for these inputs: letters, digits, underscore.
func isPyWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.IsMark(r) || unicode.Is(unicode.Nl, r) || unicode.Is(unicode.Pc, r)
}

func boundary(rs []rune, i int) bool {
	left := i > 0 && isWord(rs[i-1])
	right := i < len(rs) && isWord(rs[i])
	return left != right
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '?', '@', '[', '\\', ']', '_', '`', '{', '|', '}', '~',
		'\u2012', '\u2013', '\u2014', '\u2015', '\u2018', '\u201c':
		return true
	}
	return false
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	}
	return false
}
EOF
find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
