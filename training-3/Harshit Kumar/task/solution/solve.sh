#!/bin/bash
set -euo pipefail

cat > /workspace/repo/go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > /workspace/repo/main.go << 'EOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			if strings.HasSuffix(line, "\n") {
				line = line[:len(line)-1]
			}
			if strings.HasSuffix(line, "\r") {
				line = line[:len(line)-1]
			}
			_, _ = out.WriteString(titlecase(line, true))
			_, _ = out.WriteString("\n")
		}
		if err != nil {
			break
		}
	}
}

func titlecase(text string, smallFirstLast bool) string {
	words, spaces := splitSpace(text)
	allCaps := text == strings.ToUpper(text)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = processWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = smallFirst(tc[0])
		last := len(tc) - 1
		tc[last] = smallLast(tc[last])
	}
	return subphrase(rejoin(tc, spaces))
}

func processWord(word string, allCaps bool) string {
	if allCaps && ucInitials(word) {
		return word
	}
	if out, ok := aposWord(word); ok {
		return out
	}
	if prefix, rest, ok := macPrefix(word); ok {
		return pyCapitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		rs := []rune(word)
		rs[0] = unicode.ToUpper(rs[0])
		return string(rs)
	}
	if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
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
	if isAcronym(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func splitSpace(s string) (words, spaces []string) {
	rs := []rune(s)
	parts := make([]string, 0, len(rs)+1)
	start := 0
	for i := 0; i < len(rs); i++ {
		if !isSpace(rs[i]) {
			continue
		}
		parts = append(parts, string(rs[start:i]), string(rs[i:i+1]))
		start = i + 1
	}
	parts = append(parts, string(rs[start:]))
	for i, part := range parts {
		if i%2 == 0 {
			words = append(words, part)
		} else {
			spaces = append(spaces, part)
		}
	}
	return words, spaces
}

func rejoin(words, spaces []string) string {
	joined := make([]string, 0, len(words)+len(spaces))
	joined = append(joined, words...)
	joined = append(joined, spaces...)
	for i, word := range words {
		joined[i*2] = word
	}
	for i, space := range spaces {
		joined[i*2+1] = space
	}
	return strings.Join(joined, "")
}

func ucInitials(s string) bool {
	rs := []rune(s)
	if len(rs) == 0 {
		return false
	}
	return ucInitialsAt(rs, 0)
}

func ucInitialsAt(rs []rune, i int) bool {
	if i == len(rs) {
		return true
	}
	if isLu(rs[i]) && i+1 < len(rs) && rs[i+1] == '.' && ucInitialsAt(rs, i+2) {
		return true
	}
	if isLu(rs[i]) && i+2 < len(rs) && rs[i+1] == '.' && isLu(rs[i+2]) && ucInitialsAt(rs, i+3) {
		return true
	}
	return false
}

func aposWord(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 {
		return "", false
	}
	switch unicode.ToLower(rs[0]) {
	case 'd', 'o', 'l':
	default:
		return "", false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return "", false
	}
	body := rs[2:]
	n := 0
	for n < len(body) && unicode.IsLetter(body[n]) {
		n++
	}
	if n < 1 {
		return "", false
	}
	if n != len(body) {
		if n+2 != len(body) || !aposSuffix(body[n]) || !aposSuffix(body[n+1]) {
			return "", false
		}
	}
	out := append([]rune(nil), rs...)
	if isASCIIVowel(rs[0]) {
		out[0] = unicode.ToUpper(rs[0])
	} else {
		out[0] = unicode.ToLower(rs[0])
	}
	out[2] = unicode.ToUpper(rs[2])
	return string(out), true
}

func aposSuffix(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func isASCIIVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func macPrefix(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	if (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c' {
		prefix = string(rs[:2])
	} else if rs[0] == 'M' && rs[1] == 'C' {
		prefix = "MC"
	} else {
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
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return false
	}
	i++
	for i < len(rs) && unicode.IsLetter(rs[i]) {
		if isLu(rs[i]) {
			return true
		}
		i++
	}
	return false
}

func isSmallWord(word string) bool {
	switch strings.ToLower(word) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

func isAcronym(word string) bool {
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
	for i, r := range rs {
		if isPunct(r) {
			continue
		}
		if unicode.IsLetter(r) {
			rs[i] = unicode.ToUpper(r)
		}
		break
	}
	return string(rs)
}

func pyCapitalize(s string) string {
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

func smallFirst(word string) string {
	rs := []rune(word)
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for start := maxPunct; start >= 0; start-- {
		n, ok := matchSmallBounded(rs, start)
		if !ok {
			continue
		}
		cap := pyCapitalize(string(rs[start : start+n]))
		return string(rs[:start]) + cap + string(rs[start+n:])
	}
	return word
}

func smallLast(word string) string {
	rs := []rune(word)
	for i := 0; i <= len(rs); i++ {
		if !boundaryBefore(rs, i) {
			continue
		}
		n, ok := matchSmallToEnd(rs, i)
		if !ok {
			continue
		}
		cap := pyCapitalize(string(rs[i : i+n]))
		return string(rs[:i]) + cap
	}
	return word
}

var smallFixed = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to",
}

func matchSmallBounded(rs []rune, i int) (int, bool) {
	rest := rs[i:]
	try := func(lit string) (int, bool) {
		n, ok := foldPrefix(rest, lit)
		if !ok || !boundaryAfter(rs, i+n) {
			return 0, false
		}
		return n, true
	}
	for _, alt := range smallFixed {
		if n, ok := try(alt); ok {
			return n, true
		}
	}
	if len(rest) > 0 && unicode.ToLower(rest[0]) == 'v' {
		if len(rest) > 1 && rest[1] == '.' && boundaryAfter(rs, i+2) {
			return 2, true
		}
		if boundaryAfter(rs, i+1) {
			return 1, true
		}
	}
	if n, ok := try("via"); ok {
		return n, true
	}
	if n, ok := foldPrefix(rest, "vs"); ok {
		if len(rest) > n && rest[n] == '.' && boundaryAfter(rs, i+n+1) {
			return n + 1, true
		}
		if boundaryAfter(rs, i+n) {
			return n, true
		}
	}
	return 0, false
}

func matchSmallToEnd(rs []rune, i int) (int, bool) {
	rest := rs[i:]
	try := func(lit string) (int, bool) {
		n, ok := foldPrefix(rest, lit)
		if !ok {
			return 0, false
		}
		if n == len(rest) {
			return n, true
		}
		if n+1 == len(rest) && isPunct(rest[n]) {
			return n + 1, true
		}
		return 0, false
	}
	for _, alt := range smallFixed {
		if n, ok := try(alt); ok {
			return n, true
		}
	}
	if n, ok := try("v."); ok {
		return n, true
	}
	if n, ok := try("v"); ok {
		return n, true
	}
	if n, ok := try("via"); ok {
		return n, true
	}
	if n, ok := try("vs."); ok {
		return n, true
	}
	if n, ok := try("vs"); ok {
		return n, true
	}
	return 0, false
}

func subphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && isSubPunct(rs[i]) && rs[i+1] == ' ' {
			if n, ok := matchSmallLiteral(rs, i+2); ok {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2 : i+2+n])))
				i += 2 + n
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

func matchSmallLiteral(rs []rune, i int) (int, bool) {
	rest := rs[i:]
	for _, alt := range smallFixed {
		if n, ok := literalPrefix(rest, alt); ok {
			return n, true
		}
	}
	if len(rest) > 0 && rest[0] == 'v' {
		if len(rest) > 1 && rest[1] == '.' {
			return 2, true
		}
		return 1, true
	}
	if n, ok := literalPrefix(rest, "via"); ok {
		return n, true
	}
	if n, ok := literalPrefix(rest, "vs"); ok {
		if len(rest) > n && rest[n] == '.' {
			return n + 1, true
		}
		return n, true
	}
	return 0, false
}

func foldPrefix(rs []rune, lit string) (int, bool) {
	cr := []rune(lit)
	if len(rs) < len(cr) {
		return 0, false
	}
	for i, c := range cr {
		if unicode.ToLower(rs[i]) != unicode.ToLower(c) {
			return 0, false
		}
	}
	return len(cr), true
}

func literalPrefix(rs []rune, lit string) (int, bool) {
	cr := []rune(lit)
	if len(rs) < len(cr) {
		return 0, false
	}
	for i, c := range cr {
		if rs[i] != c {
			return 0, false
		}
	}
	return len(cr), true
}

func boundaryBefore(rs []rune, i int) bool {
	if i < 0 || i > len(rs) {
		return false
	}
	var prev, next bool
	if i > 0 {
		prev = isWord(rs[i-1])
	}
	if i < len(rs) {
		next = isWord(rs[i])
	}
	if i == 0 {
		return next
	}
	if i == len(rs) {
		return prev
	}
	return prev != next
}

func boundaryAfter(rs []rune, i int) bool {
	return boundaryBefore(rs, i)
}

func isLu(r rune) bool {
	return unicode.Is(unicode.Lu, r)
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.Is(unicode.M, r) || unicode.Is(unicode.Pc, r)
}

func isSpace(r rune) bool {
	switch r {
	case '\t', '\n', '\v', '\f', '\r', ' ',
		0x85, 0xa0, 0x1680,
		0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200a,
		0x2028, 0x2029, 0x202f, 0x205f, 0x3000:
		return true
	default:
		return false
	}
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/',
		':', ';', '?', '@', '[', '\\', ']', '_', '`', '{', '|', '}', '~',
		0x2012, 0x2013, 0x2014, 0x2015, 0x2018, 0x201c:
		return true
	default:
		return false
	}
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', 0x2012, 0x2013, 0x2014, 0x2015:
		return true
	default:
		return false
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
find /workspace/repo -depth -type d -name '__pycache__' -exec rm -rf {} +
