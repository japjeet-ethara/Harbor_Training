#!/bin/bash
set -euo pipefail
dest=/workspace/repo
mkdir -p "$dest"
cat > "$dest/go.mod" << 'EOF'
module titlecase

go 1.23
EOF
cat > "$dest/main.go" << 'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
)

// smallAlts follows the order Python's regex tries for
// a|an|...|v\.?|via|vs\.? . The optional dots are greedy, so the dotted
// form is tried before the bare one. Go's regexp has no look-around, so
// the word-boundary checks are done on the runes directly.
var smallAlts = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to",
	"v.", "v", "via", "vs.", "vs",
}

var subphrase = regexp.MustCompile("([:.;?!\\-\u2012\u2013\u2014\u2015] )(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\\.?|via|vs\\.?)")

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimRight(line, "\r\n")
			fmt.Fprintln(out, titlecaseLine(line, true))
		}
		if err != nil {
			return
		}
	}
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitWS(line)
	for i, word := range words {
		words[i] = processWord(word, allCaps)
	}
	if smallFirstLast && len(words) > 0 {
		words[0] = applySmallFirst(words[0])
		words[len(words)-1] = applySmallLast(words[len(words)-1])
	}
	return applySubphrase(rejoin(words, spaces))
}

func processWord(word string, allCaps bool) string {
	if word == "" {
		return ""
	}
	if allCaps && ucInitials(word) {
		return word
	}
	if out, ok := applyApos(word); ok {
		return out
	}
	if prefix, rest, ok := matchMac(word); ok {
		return capitalize(prefix) + titlecaseLine(rest, true)
	}
	if isMr(word) {
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
	if allConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func splitWS(line string) (words, spaces []string) {
	rs := []rune(line)
	i := 0
	for i <= len(rs) {
		j := i
		for j < len(rs) && !isSpace(rs[j]) {
			j++
		}
		words = append(words, string(rs[i:j]))
		if j >= len(rs) {
			break
		}
		spaces = append(spaces, string(rs[j:j+1]))
		i = j + 1
	}
	return words, spaces
}

func rejoin(words, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func isSpace(r rune) bool {
	// Python regex \s: Unicode spaces plus the ASCII file-separator controls.
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '\u201c', '#', '$', '%', '&', '\'', '\u2018', '(', ')', '*', '+', ',',
		'-', '\u2013', '\u2012', '\u2014', '\u2015', '.', '/', ':', ';', '?', '@', '[', '\\', ']',
		'_', '`', '{', '|', '}', '~':
		return true
	default:
		return false
	}
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

func hasBoundary(rs []rune, i int) bool {
	left, right := false, false
	if i > 0 {
		left = isWord(rs[i-1])
	}
	if i < len(rs) {
		right = isWord(rs[i])
	}
	return left != right
}

func isExactSmall(word string) bool {
	switch strings.ToLower(word) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

func smallPrefixLen(rs []rune) (int, bool) {
	low := []rune(strings.ToLower(string(rs)))
	for _, alt := range smallAlts {
		a := []rune(alt)
		if len(low) < len(a) || string(low[:len(a)]) != alt {
			continue
		}
		if hasBoundary(rs, len(a)) {
			return len(a), true
		}
	}
	return 0, false
}

func smallSuffixLen(rs []rune) (int, bool) {
	low := []rune(strings.ToLower(string(rs)))
	for _, alt := range smallAlts {
		a := []rune(alt)
		if len(low) < len(a) || string(low[len(low)-len(a):]) != alt {
			continue
		}
		if hasBoundary(rs, len(rs)-len(a)) {
			return len(a), true
		}
	}
	return 0, false
}

func applySmallFirst(s string) string {
	rs := []rune(s)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	n, ok := smallPrefixLen(rs[i:])
	if !ok {
		return s
	}
	return string(rs[:i]) + capitalize(string(rs[i:i+n])) + string(rs[i+n:])
}

func applySmallLast(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	if isPunct(rs[len(rs)-1]) {
		if n, ok := smallSuffixLen(rs[:len(rs)-1]); ok {
			start := len(rs) - 1 - n
			return string(rs[:start]) + capitalize(string(rs[start:]))
		}
	}
	if n, ok := smallSuffixLen(rs); ok {
		start := len(rs) - n
		return string(rs[:start]) + capitalize(string(rs[start:]))
	}
	return s
}

func applySubphrase(s string) string {
	return subphrase.ReplaceAllStringFunc(s, func(match string) string {
		parts := subphrase.FindStringSubmatch(match)
		if parts == nil {
			return match
		}
		return parts[1] + capitalize(parts[2])
	})
}

func applyApos(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) || (rs[1] != '\'' && rs[1] != '\u2018') {
		return "", false
	}
	rest := rs[2:]
	valid := allLetters(rest)
	if !valid && len(rest) >= 3 && isAposClass(rest[len(rest)-1]) && isAposClass(rest[len(rest)-2]) && allLetters(rest[:len(rest)-2]) {
		valid = true
	}
	if !valid {
		return "", false
	}
	var first string
	if !strings.ContainsRune("aeiouAEIOU", rs[0]) {
		first = strings.ToLower(string(rs[0]))
	} else {
		first = strings.ToUpper(string(rs[0]))
	}
	return first + string(rs[1]) + strings.ToUpper(string(rs[2])) + string(rs[3:]), true
}

func isDOL(r rune) bool {
	switch r {
	case 'd', 'D', 'o', 'O', 'l', 'L':
		return true
	default:
		return false
	}
}

func isAposClass(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func allLetters(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return true
}

func matchMac(word string) (string, string, bool) {
	rs := []rune(word)
	if len(rs) < 4 || !isWord(rs[2]) {
		return "", "", false
	}
	if ((rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c') || (rs[0] == 'M' && rs[1] == 'C') {
		return string(rs[:2]), string(rs[2:]), true
	}
	return "", "", false
}

func isMr(word string) bool {
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
		if unicode.IsLetter(rs[i]) && rs[i+1] == '.' && unicode.IsLetter(rs[i+2]) {
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
	sawLetter := false
	for i < len(rs) && unicode.IsLetter(rs[i]) {
		if sawLetter && unicode.IsUpper(rs[i]) {
			return true
		}
		sawLetter = true
		i++
	}
	return false
}

func ucInitials(word string) bool {
	rs := []rune(word)
	if len(rs) == 0 {
		return false
	}
	return consumeInitials(rs)
}

func consumeInitials(rs []rune) bool {
	if len(rs) == 0 {
		return true
	}
	if len(rs) >= 2 && unicode.IsUpper(rs[0]) && rs[1] == '.' && consumeInitials(rs[2:]) {
		return true
	}
	if len(rs) >= 3 && unicode.IsUpper(rs[0]) && rs[1] == '.' && unicode.IsUpper(rs[2]) && consumeInitials(rs[3:]) {
		return true
	}
	return false
}

func allConsonants(word string) bool {
	rs := []rune(word)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		if !isASCIIConsonant(r) {
			return false
		}
	}
	return true
}

func isASCIIConsonant(r rune) bool {
	switch r {
	case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z',
		'B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Z':
		return true
	default:
		return false
	}
}

func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return word
	}
	return strings.ToUpper(string(rs[:i+1])) + string(rs[i+1:])
}

func upperFirst(word string) string {
	rs := []rune(word)
	if len(rs) == 0 {
		return word
	}
	return strings.ToUpper(string(rs[:1])) + string(rs[1:])
}

func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	rs[0] = unicode.ToUpper(rs[0])
	for i := 1; i < len(rs); i++ {
		rs[i] = unicode.ToLower(rs[i])
	}
	return string(rs)
}
EOF
find "$dest" -type f -name "*.py" -delete
