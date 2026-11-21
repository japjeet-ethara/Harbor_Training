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
	"bufio"
	"os"
	"strings"
	"unicode"
)

// Punctuation matched by the original character class.
const punctSet = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// Sub-phrase marks are the narrower set used after a space.
const subPunctSet = ":.;?!-–‒—―"

var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to",
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	out := bufio.NewWriter(os.Stdout)
	for in.Scan() {
		out.WriteString(titlecaseLine(in.Text(), true))
		out.WriteByte('\n')
	}
	out.Flush()
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitWS(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titleWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(joinWS(tc, spaces))
}

func titleWord(word string, allCaps bool) string {
	if word == "" {
		return ""
	}
	if allCaps && isUCInitials(word) {
		return word
	}
	if next, ok := aposSecond(word); ok {
		return next
	}
	if pre, rest, ok := macMC(word); ok {
		return capitalize(pre) + titlecaseLine(rest, true)
	}
	if isHonorific(word) {
		return upperFirst(word)
	}
	if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
		return word
	}
	if isExactSmall(word) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = titlecaseLine(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = titlecaseLine(part, false)
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

func isUCInitials(word string) bool {
	return ucInitials(word, false)
}

func ucInitials(s string, matched bool) bool {
	if s == "" {
		return matched
	}
	if len(s) >= 2 && s[0] >= 'A' && s[0] <= 'Z' && s[1] == '.' {
		if ucInitials(s[2:], true) {
			return true
		}
	}
	if len(s) >= 3 && s[0] >= 'A' && s[0] <= 'Z' && s[1] == '.' && s[2] >= 'A' && s[2] <= 'Z' {
		if ucInitials(s[3:], true) {
			return true
		}
	}
	return false
}

func aposSecond(word string) (string, bool) {
	rs := []rune(word)
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
	i := 2
	words := 0
	for i < len(rs) && isWord(rs[i]) {
		i++
		words++
	}
	if words < 1 {
		return "", false
	}
	if i != len(rs) {
		if len(rs)-i != 2 || !isAposTail(rs[i]) || !isAposTail(rs[i+1]) {
			return "", false
		}
	}
	var b strings.Builder
	if !isAposVowel(rs[0]) {
		b.WriteString(strings.ToLower(string(rs[0])))
	} else {
		b.WriteString(strings.ToUpper(string(rs[0])))
	}
	b.WriteRune(rs[1])
	b.WriteString(strings.ToUpper(string(rs[2])))
	b.WriteString(string(rs[3:]))
	return b.String(), true
}

func isAposTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func isAposVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func macMC(word string) (pre, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 || !isWord(rs[2]) {
		return "", "", false
	}
	if (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c' {
		return string(rs[:2]), string(rs[2:]), true
	}
	if rs[0] == 'M' && rs[1] == 'C' {
		return string(rs[:2]), string(rs[2:]), true
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
		if isWord(rs[i]) && rs[i+1] == '.' && isWord(rs[i+2]) {
			return true
		}
	}
	return false
}

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
		if rs[i] >= 'A' && rs[i] <= 'Z' {
			return true
		}
		i++
	}
	return false
}

func isExactSmall(word string) bool {
	return exactSmall([]rune(strings.ToLower(word)))
}

func exactSmall(rs []rune) bool {
	switch string(rs) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

func isAllConsonants(word string) bool {
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

func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	n := smallPrefixLen(rs[i:])
	if n == 0 {
		return word
	}
	return string(rs[:i]) + capitalize(string(rs[i:i+n])) + string(rs[i+n:])
}

func smallPrefixLen(rs []rune) int {
	low := []rune(strings.ToLower(string(rs)))
	for _, lit := range smallWords {
		lr := []rune(lit)
		if hasPrefix(low, lr) && boundaryAt(rs, len(lr)) {
			return len(lr)
		}
	}
	if len(low) > 0 && low[0] == 'v' {
		if len(low) >= 2 && low[1] == '.' && boundaryAt(rs, 2) {
			return 2
		}
		if boundaryAt(rs, 1) {
			return 1
		}
	}
	if hasPrefix(low, []rune("via")) && boundaryAt(rs, 3) {
		return 3
	}
	if len(low) >= 2 && low[0] == 'v' && low[1] == 's' {
		if len(low) >= 3 && low[2] == '.' && boundaryAt(rs, 3) {
			return 3
		}
		if boundaryAt(rs, 2) {
			return 2
		}
	}
	return 0
}

func applySmallLast(word string) string {
	rs := []rune(word)
	for i := 0; i <= len(rs); i++ {
		if suffixMatchesSmall(rs[i:]) && boundaryAt(rs, i) {
			return string(rs[:i]) + capitalize(string(rs[i:]))
		}
	}
	return word
}

func suffixMatchesSmall(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	if isPunct(rs[len(rs)-1]) && exactSmall(lowerRunes(rs[:len(rs)-1])) {
		return true
	}
	return exactSmall(lowerRunes(rs))
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && isSubPunct(rs[i]) && rs[i+1] == ' ' {
			n := subMatchLen(rs[i+2:])
			if n > 0 {
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

func subMatchLen(rs []rune) int {
	for _, lit := range smallWords {
		lr := []rune(lit)
		if hasPrefix(rs, lr) {
			return len(lr)
		}
	}
	if len(rs) > 0 && rs[0] == 'v' {
		if len(rs) > 1 && rs[1] == '.' {
			return 2
		}
		return 1
	}
	if hasPrefix(rs, []rune("via")) {
		return 3
	}
	if len(rs) >= 2 && rs[0] == 'v' && rs[1] == 's' {
		if len(rs) >= 3 && rs[2] == '.' {
			return 3
		}
		return 2
	}
	return 0
}

func splitWS(s string) (words, spaces []string) {
	rs := []rune(s)
	if len(rs) == 0 {
		return []string{""}, nil
	}
	for i := 0; i < len(rs); {
		if unicode.IsSpace(rs[i]) {
			if len(words) == len(spaces) {
				words = append(words, "")
			}
			spaces = append(spaces, string(rs[i:i+1]))
			i++
			if i == len(rs) {
				words = append(words, "")
			}
			continue
		}
		j := i
		for j < len(rs) && !unicode.IsSpace(rs[j]) {
			j++
		}
		words = append(words, string(rs[i:j]))
		i = j
	}
	return words, spaces
}

func joinWS(words, spaces []string) string {
	parts := make([]string, len(words)+len(spaces))
	for i, word := range words {
		parts[i*2] = word
	}
	for i, space := range spaces {
		parts[i*2+1] = space
	}
	return strings.Join(parts, "")
}

func boundaryAt(rs []rune, n int) bool {
	if n < 0 || n > len(rs) {
		return false
	}
	left := n > 0 && isWord(rs[n-1])
	right := n < len(rs) && isWord(rs[n])
	return left != right
}

func hasPrefix(rs, prefix []rune) bool {
	if len(rs) < len(prefix) {
		return false
	}
	for i, r := range prefix {
		if rs[i] != r {
			return false
		}
	}
	return true
}

func lowerRunes(rs []rune) []rune {
	return []rune(strings.ToLower(string(rs)))
}

func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	return strings.ToUpper(string(rs[:1])) + strings.ToLower(string(rs[1:]))
}

func upperFirst(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	return strings.ToUpper(string(rs[:1])) + string(rs[1:])
}

func isPunct(r rune) bool {
	return strings.ContainsRune(punctSet, r)
}

func isSubPunct(r rune) bool {
	return strings.ContainsRune(subPunctSet, r)
}

func isASCIILetter(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z')
}

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func runeLen(s string) int {
	return len([]rune(s))
}
EOF

find /workspace/repo -type f -name '*.py' -delete
if [ -d /workspace/repo/titlecase ]; then
    rmdir /workspace/repo/titlecase
fi
