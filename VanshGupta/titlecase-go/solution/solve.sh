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
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

func main() {
	in, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	lines := pythonSplitLines(string(in))
	var b strings.Builder
	for _, line := range lines {
		b.WriteString(titlecase(line, true))
		b.WriteByte('\n')
	}
	_, _ = os.Stdout.WriteString(b.String())
}

func pythonSplitLines(text string) []string {
	if text == "" {
		return nil
	}
	var lines []string
	start := 0
	i := 0
	for i < len(text) {
		if text[i] == '\r' || text[i] == '\n' {
			lines = append(lines, text[start:i])
			if text[i] == '\r' && i+1 < len(text) && text[i+1] == '\n' {
				i += 2
			} else {
				i++
			}
			start = i
			continue
		}
		i++
	}
	if start < len(text) {
		lines = append(lines, text[start:])
	}
	return lines
}

func titlecase(text string, smallFirstLast bool) string {
	parts := splitBreaks(text)
	out := make([]string, len(parts))
	for i, part := range parts {
		out[i] = processLine(part, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func splitBreaks(text string) []string {
	var parts []string
	start := 0
	i := 0
	for i < len(text) {
		if text[i] == '\n' || text[i] == '\r' {
			parts = append(parts, text[start:i])
			for i < len(text) && (text[i] == '\n' || text[i] == '\r') {
				i++
			}
			start = i
			continue
		}
		i++
	}
	parts = append(parts, text[start:])
	return parts
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitWords(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = processWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(interleave(tc, spaces))
}

func splitWords(line string) (words, spaces []string) {
	var cur []rune
	flush := func() {
		words = append(words, string(cur))
		cur = nil
	}
	for _, r := range line {
		if pythonIsSpace(r) {
			flush()
			spaces = append(spaces, string(r))
			continue
		}
		cur = append(cur, r)
	}
	flush()
	return words, spaces
}

func interleave(words, spaces []string) string {
	var b strings.Builder
	for i, sp := range spaces {
		b.WriteString(words[i])
		b.WriteString(sp)
	}
	if len(words) > 0 {
		b.WriteString(words[len(words)-1])
	}
	return b.String()
}

func processWord(word string, allCaps bool) string {
	if word == "" {
		return ""
	}
	if allCaps && isInitials(word) {
		return word
	}
	if next, ok := aposSecond(word); ok {
		return next
	}
	if prefix, rest, ok := splitMac(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		rs := []rune(word)
		rs[0] = unicode.ToUpper(rs[0])
		return string(rs)
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
	if allConsonants(word) && utf8.RuneCountInString(word) > 2 {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func aposSecond(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) || (rs[1] != '\'' && rs[1] != '\u2018') {
		return "", false
	}
	if !aposRest(rs[2:]) {
		return "", false
	}
	if !isVowel(rs[0]) {
		rs[0] = unicode.ToLower(rs[0])
	} else {
		rs[0] = unicode.ToUpper(rs[0])
	}
	rs[2] = unicode.ToUpper(rs[2])
	return string(rs), true
}

func aposRest(rest []rune) bool {
	if len(rest) == 0 {
		return false
	}
	if allWord(rest) {
		return true
	}
	if len(rest) >= 3 && allWord(rest[:len(rest)-2]) && aposSuf(rest[len(rest)-2]) && aposSuf(rest[len(rest)-1]) {
		return true
	}
	return false
}

func aposSuf(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func allWord(rs []rune) bool {
	for _, r := range rs {
		if !isWord(r) {
			return false
		}
	}
	return true
}

func splitMac(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	mac := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c'
	mc := rs[0] == 'M' && rs[1] == 'C'
	if !mac && !mc {
		return "", "", false
	}
	if !isWord(rs[2]) {
		return "", "", false
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
	for i := 1; i < len(rs)-1; i++ {
		if rs[i] == '.' && isWord(rs[i-1]) && isWord(rs[i+1]) {
			return true
		}
	}
	return false
}

func ucElsewhere(word string) bool {
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

func isInitials(word string) bool {
	rs := []rune(word)
	if len(rs) == 0 {
		return false
	}
	return initialsAt(rs, 0)
}

func initialsAt(rs []rune, i int) bool {
	if i == len(rs) {
		return true
	}
	if i+1 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && initialsAt(rs, i+2) {
		return true
	}
	if i+2 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && isASCIIUpper(rs[i+2]) && initialsAt(rs, i+3) {
		return true
	}
	return false
}

func allConsonants(word string) bool {
	rs := []rune(word)
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if !isASCIIConsonant(r) {
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	rs := []rune(word)
	for i, r := range rs {
		if isWord(r) {
			rs[i] = unicode.ToUpper(r)
			return string(rs)
		}
	}
	return word
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	tail := rs[i:]
	for _, alt := range smallAlts {
		n, ok := alt(tail, true)
		if !ok {
			continue
		}
		end := i + n
		if end < len(rs) && isWord(rs[end]) {
			continue
		}
		return string(rs[:i]) + capitalize(string(tail[:n])) + string(rs[end:])
	}
	return word
}

func applySmallLast(word string) string {
	rs := []rune(word)
	for i := 0; i <= len(rs); i++ {
		if !boundary(rs, i) {
			continue
		}
		tail := rs[i:]
		for _, alt := range smallAlts {
			n, ok := alt(tail, true)
			if !ok {
				continue
			}
			rest := tail[n:]
			if len(rest) == 0 || (len(rest) == 1 && isPunct(rest[0])) {
				return string(rs[:i]) + capitalize(string(tail))
			}
		}
	}
	return word
}

func applySubphrase(line string) string {
	rs := []rune(line)
	out := make([]rune, 0, len(rs))
	i := 0
	for i < len(rs) {
		if i+1 < len(rs) && isSubMarker(rs[i]) && rs[i+1] == ' ' {
			tail := rs[i+2:]
			for _, alt := range smallAlts {
				n, ok := alt(tail, false)
				if !ok || n == 0 {
					continue
				}
				out = append(out, rs[i], ' ')
				out = append(out, []rune(capitalize(string(tail[:n])))...)
				i += 2 + n
				goto next
			}
		}
		out = append(out, rs[i])
		i++
	next:
	}
	return string(out)
}

func boundary(rs []rune, i int) bool {
	var left, right bool
	if i > 0 {
		left = isWord(rs[i-1])
	}
	if i < len(rs) {
		right = isWord(rs[i])
	}
	return left != right
}

func isSmallWord(word string) bool {
	rs := []rune(word)
	for _, alt := range smallAlts {
		n, ok := alt(rs, true)
		if ok && n == len(rs) {
			return true
		}
	}
	return false
}

type altFunc func(rs []rune, fold bool) (int, bool)

var smallAlts = []altFunc{
	lit("a"), lit("an"), lit("and"), lit("as"), lit("at"), lit("but"), lit("by"),
	lit("en"), lit("for"), lit("if"), lit("in"), lit("of"), lit("on"), lit("or"),
	lit("the"), lit("to"), vOptDot, lit("via"), vsOptDot,
}

func lit(s string) altFunc {
	want := []rune(s)
	return func(rs []rune, fold bool) (int, bool) {
		if len(rs) < len(want) {
			return 0, false
		}
		for i, w := range want {
			a := rs[i]
			if fold {
				a = unicode.ToLower(a)
				w = unicode.ToLower(w)
			}
			if a != w {
				return 0, false
			}
		}
		return len(want), true
	}
}

func vOptDot(rs []rune, fold bool) (int, bool) {
	if len(rs) == 0 {
		return 0, false
	}
	c := rs[0]
	if fold {
		c = unicode.ToLower(c)
	}
	if c != 'v' {
		return 0, false
	}
	if len(rs) > 1 && rs[1] == '.' {
		return 2, true
	}
	return 1, true
}

func vsOptDot(rs []rune, fold bool) (int, bool) {
	if len(rs) < 2 {
		return 0, false
	}
	c0, c1 := rs[0], rs[1]
	if fold {
		c0 = unicode.ToLower(c0)
		c1 = unicode.ToLower(c1)
	}
	if c0 != 'v' || c1 != 's' {
		return 0, false
	}
	if len(rs) > 2 && rs[2] == '.' {
		return 3, true
	}
	return 2, true
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

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func pythonIsSpace(r rune) bool {
	if r == '\t' || r == '\n' || r == '\v' || r == '\f' || r == '\r' {
		return true
	}
	if r >= 0x1c && r <= 0x1f {
		return true
	}
	return unicode.IsSpace(r)
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '\u201c', '#', '$', '%', '&', '\'', '\u2018', '(', ')', '*', '+', ',', '-',
		'\u2013', '\u2012', '\u2014', '\u2015', '.', '/', ':', ';', '?', '@', '[', '\\', ']',
		'_', '`', '{', '|', '}', '~':
		return true
	default:
		return false
	}
}

func isSubMarker(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2013', '\u2012', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func isDOL(r rune) bool {
	switch unicode.ToLower(r) {
	case 'd', 'o', 'l':
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

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isASCIIUpper(r rune) bool {
	return r >= 'A' && r <= 'Z'
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
EOF
find "$dest" -type f -name '*.py' -delete
rm -rf "$dest/titlecase"
