#!/bin/bash
set -euo pipefail
repo=/workspace/repo
cat > "$repo/go.mod" << 'EOF'
module titlecase

go 1.23
EOF
cat > "$repo/main.go" << 'EOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

// Punctuation from the original Python character class.
const punctSet = "!\"\u201c#$%&'\u2018()*+,\u002d\u2013\u2012\u2014\u2015./:;?@[\\]_\u0060{|}~"

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimRight(line, "\r\n")
			out.WriteString(titlecase(line, true))
			out.WriteByte('\n')
		}
		if err != nil {
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
	if text == "" {
		return []string{""}
	}
	var lines []string
	var cur []rune
	rs := []rune(text)
	for i := 0; i < len(rs); {
		if rs[i] == '\n' || rs[i] == '\r' {
			lines = append(lines, string(cur))
			cur = cur[:0]
			for i < len(rs) && (rs[i] == '\n' || rs[i] == '\r') {
				i++
			}
			if i == len(rs) {
				lines = append(lines, "")
			}
			continue
		}
		cur = append(cur, rs[i])
		i++
	}
	if len(cur) > 0 || len(lines) == 0 {
		lines = append(lines, string(cur))
	}
	return lines
}

func titlecaseLine(line string, smallFirstLast bool) string {
	parts := splitSpaces(line)
	words := make([]string, 0, (len(parts)+1)/2)
	spaces := make([]string, 0, len(parts)/2)
	for i, part := range parts {
		if i%2 == 0 {
			words = append(words, part)
		} else {
			spaces = append(spaces, part)
		}
	}
	allCaps := strings.ToUpper(line) == line
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titleWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	joined := interleave(tc, spaces)
	return applySubphrase(joined)
}

func splitSpaces(line string) []string {
	var parts []string
	var cur []rune
	for _, r := range line {
		if isPySpace(r) {
			parts = append(parts, string(cur), string(r))
			cur = cur[:0]
			continue
		}
		cur = append(cur, r)
	}
	parts = append(parts, string(cur))
	return parts
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
	if word == "" {
		return ""
	}
	if allCaps && isInitials(word) {
		return word
	}
	if isApostropheName(word) {
		return fixApostropheName(word)
	}
	if prefix, rest, ok := splitMac(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		rs := []rune(word)
		rs[0] = unicode.ToUpper(rs[0])
		return string(rs)
	}
	if hasInlinePeriod(word) || (!allCaps && hasInternalCap(word)) {
		return word
	}
	if isExactSmall(word) {
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
	if runeLen(word) > 2 && isAllConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func isPySpace(r rune) bool {
	if r >= 0x0009 && r <= 0x000d {
		return true
	}
	if r >= 0x001c && r <= 0x001f {
		return true
	}
	if r == 0x0085 || r == 0x00a0 {
		return true
	}
	return unicode.Is(unicode.Z, r)
}

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isPunct(r rune) bool {
	return strings.ContainsRune(punctSet, r)
}

func boundary(rs []rune, i int) bool {
	left := i > 0 && isWord(rs[i-1])
	right := i < len(rs) && isWord(rs[i])
	return left != right
}

func runeLen(s string) int {
	return utf8.RuneCountInString(s)
}

func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return ""
	}
	rs[0] = unicode.ToUpper(rs[0])
	for i := 1; i < len(rs); i++ {
		rs[i] = unicode.ToLower(rs[i])
	}
	return string(rs)
}

func isExactSmall(s string) bool {
	switch strings.ToLower(s) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

func foldPrefixLen(rs []rune, lit string) int {
	lr := []rune(lit)
	if len(rs) < len(lr) {
		return 0
	}
	if strings.EqualFold(string(rs[:len(lr)]), lit) {
		return len(lr)
	}
	return 0
}

// matchSmall reports the end index of a small word starting at i.
// A word boundary is required after it, matching the Python \b.
func matchSmall(rs []rune, i int) int {
	rest := rs[i:]
	literals := []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to"}
	for _, lit := range literals {
		n := foldPrefixLen(rest, lit)
		if n > 0 && boundary(rs, i+n) {
			return i + n
		}
	}
	if len(rest) > 0 && (rest[0] == 'v' || rest[0] == 'V') {
		if len(rest) > 1 && rest[1] == '.' && boundary(rs, i+2) {
			return i + 2
		}
		if boundary(rs, i+1) {
			return i + 1
		}
	}
	if n := foldPrefixLen(rest, "via"); n > 0 && boundary(rs, i+n) {
		return i + n
	}
	if n := foldPrefixLen(rest, "vs"); n > 0 {
		if len(rest) >= n+1 && rest[n] == '.' && boundary(rs, i+n+1) {
			return i + n + 1
		}
		if boundary(rs, i+n) {
			return i + n
		}
	}
	return -1
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	end := matchSmall(rs, i)
	if end < 0 {
		return word
	}
	return string(rs[:i]) + capitalize(string(rs[i:end])) + string(rs[end:])
}

func applySmallLast(word string) string {
	rs := []rune(word)
	for start := 0; start <= len(rs); start++ {
		if !boundary(rs, start) {
			continue
		}
		if smallLastSuffix(rs[start:]) {
			return string(rs[:start]) + capitalize(string(rs[start:]))
		}
	}
	return word
}

func smallLastSuffix(rs []rune) bool {
	if isExactSmall(string(rs)) {
		return true
	}
	if len(rs) >= 1 && isPunct(rs[len(rs)-1]) && isExactSmall(string(rs[:len(rs)-1])) {
		return true
	}
	return false
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func hasSmallPrefix(rs []rune) bool {
	s := string(rs)
	for _, w := range []string{
		"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to", "v.", "vs.", "via", "v", "vs",
	} {
		if strings.HasPrefix(s, w) {
			return true
		}
	}
	return false
}

func applySubphrase(s string) string {
	rs := []rune(s)
	for i := 0; i+2 < len(rs); i++ {
		if isSubPunct(rs[i]) && rs[i+1] == ' ' && hasSmallPrefix(rs[i+2:]) {
			rs[i+2] = unicode.ToUpper(rs[i+2])
		}
	}
	return string(rs)
}

func isInitials(s string) bool {
	if s == "" {
		return false
	}
	return parseInitials([]rune(s), 0)
}

func parseInitials(rs []rune, i int) bool {
	if i == len(rs) {
		return true
	}
	if i+1 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' {
		if parseInitials(rs, i+2) {
			return true
		}
	}
	if i+2 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && isASCIIUpper(rs[i+2]) {
		if parseInitials(rs, i+3) {
			return true
		}
	}
	return false
}

func isASCIIUpper(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func isApostropheName(word string) bool {
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
		if !isWord(r) {
			return false
		}
	}
	return true
}

func isAposSuffix(rs []rune) bool {
	if len(rs) != 2 {
		return false
	}
	return isAposSuffixChar(rs[0]) && isAposSuffixChar(rs[1])
}

func isAposSuffixChar(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func fixApostropheName(word string) string {
	rs := []rune(word)
	if strings.ContainsRune("aeiouAEIOU", rs[0]) {
		rs[0] = unicode.ToUpper(rs[0])
	} else {
		rs[0] = unicode.ToLower(rs[0])
	}
	rs[2] = unicode.ToUpper(rs[2])
	return string(rs)
}

func splitMac(word string) (string, string, bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	mac := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c'
	upper := rs[0] == 'M' && rs[1] == 'C'
	if !mac && !upper {
		return "", "", false
	}
	rest := rs[2:]
	if len(rest) < 2 || !isWord(rest[0]) {
		return "", "", false
	}
	return string(rs[:2]), string(rest), true
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

func hasInternalCap(word string) bool {
	rs := []rune(word)
	for i := 0; i+1 < len(rs); i++ {
		if isASCIILetter(rs[i]) && isASCIIUpper(rs[i+1]) {
			return true
		}
	}
	return false
}

func isASCIILetter(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z')
}

func isAllConsonants(word string) bool {
	if word == "" {
		return false
	}
	for _, r := range word {
		switch r {
		case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z',
			'B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Z':
		default:
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	rs := []rune(word)
	for i, r := range rs {
		if isWord(r) {
			// Every rune before the first word character must be punctuation.
			for j := 0; j < i; j++ {
				if !isPunct(rs[j]) {
					return word
				}
			}
			rs[i] = unicode.ToUpper(r)
			return string(rs)
		}
	}
	return word
}
EOF
find "$repo" -type f -name '*.py' -delete
