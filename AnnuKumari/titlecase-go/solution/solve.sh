#!/bin/bash
set -euo pipefail

root=/workspace/repo
mkdir -p "$root"

cat > "$root/go.mod" << 'EOF'
module titlecase

go 1.23
EOF

cat > "$root/main.go" << 'EOF'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

// punct is the Python PUNCT set from titlecase, checked by hand because the
// character class is only used next to word-boundary tests Go's regexp cannot
// express the same way as Python's Unicode \b.
const punct = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// smallAlts follows the Python alternation order. Forms inside one group are
// tried longest-first, which is how v\.? and vs\.? backtrack.
var smallAlts = [][]string{
	{"a"},
	{"an"},
	{"and"},
	{"as"},
	{"at"},
	{"but"},
	{"by"},
	{"en"},
	{"for"},
	{"if"},
	{"in"},
	{"of"},
	{"on"},
	{"or"},
	{"the"},
	{"to"},
	{"v.", "v"},
	{"via"},
	{"vs.", "vs"},
}

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimRight(line, "\r\n")
			out.WriteString(titlecase(line))
			out.WriteByte('\n')
		}
		if err != nil {
			break
		}
	}
}

func titlecase(text string) string {
	lines := splitNewlines(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = titlecaseLine(line, true)
	}
	return strings.Join(out, "\n")
}

func splitNewlines(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	start := 0
	runes := []rune(text)
	for i := 0; i < len(runes); i++ {
		if runes[i] != '\r' && runes[i] != '\n' {
			continue
		}
		lines = append(lines, string(runes[start:i]))
		for i < len(runes) && (runes[i] == '\r' || runes[i] == '\n') {
			i++
		}
		start = i
		i--
	}
	lines = append(lines, string(runes[start:]))
	return lines
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitSpaces(line)
	out := make([]string, len(words))
	for i, word := range words {
		out[i] = titleWord(word, allCaps)
	}
	if smallFirstLast && len(out) > 0 {
		out[0] = applySmallFirst(out[0])
		out[len(out)-1] = applySmallLast(out[len(out)-1])
	}
	return applySubphrase(joinParts(out, spaces))
}

func titleWord(word string, allCaps bool) string {
	if allCaps && isInitials(word) {
		return word
	}
	if recased, ok := recaseApostrophe(word); ok {
		return recased
	}
	if prefix, rest, ok := splitMc(word); ok {
		return capitalize(prefix) + titlecaseLine(rest, true)
	}
	if isHonorific(word) {
		r := []rune(word)
		if len(r) > 0 {
			r[0] = unicode.ToUpper(r[0])
		}
		return string(r)
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

func isPunct(r rune) bool {
	return strings.ContainsRune(punct, r)
}

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isPySpace(r rune) bool {
	switch r {
	case '\t', '\n', '\v', '\f', '\r', ' ', '\u0085', '\u00a0',
		'\u001c', '\u001d', '\u001e', '\u001f':
		return true
	}
	return unicode.Is(unicode.Zs, r) || unicode.Is(unicode.Zl, r) || unicode.Is(unicode.Zp, r)
}

func isBoundary(r []rune, i int) bool {
	left, right := false, false
	if i > 0 {
		left = isWord(r[i-1])
	}
	if i < len(r) {
		right = isWord(r[i])
	}
	return left != right
}

func isASCIILetter(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z')
}

func isAZ(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func eqFold(got, want []rune) bool {
	return strings.EqualFold(string(got), string(want))
}

func eqExact(got, want []rune) bool {
	if len(got) != len(want) {
		return false
	}
	for i := range got {
		if got[i] != want[i] {
			return false
		}
	}
	return true
}

func splitSpaces(line string) (words, spaces []string) {
	runes := []rune(line)
	parts := make([]string, 0)
	start := 0
	for i := 0; i < len(runes); i++ {
		if !isPySpace(runes[i]) {
			continue
		}
		parts = append(parts, string(runes[start:i]), string(runes[i:i+1]))
		start = i + 1
	}
	parts = append(parts, string(runes[start:]))
	if len(parts) == 0 {
		parts = []string{""}
	}
	for i, part := range parts {
		if i%2 == 0 {
			words = append(words, part)
		} else {
			spaces = append(spaces, part)
		}
	}
	return words, spaces
}

func joinParts(words, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func isInitials(s string) bool {
	r := []rune(s)
	if len(r) == 0 {
		return false
	}
	var rec func(i int) bool
	rec = func(i int) bool {
		if i == len(r) {
			return true
		}
		if i+1 < len(r) && isAZ(r[i]) && r[i+1] == '.' && rec(i+2) {
			return true
		}
		if i+2 < len(r) && isAZ(r[i]) && r[i+1] == '.' && isAZ(r[i+2]) && rec(i+3) {
			return true
		}
		return false
	}
	return rec(0)
}

func recaseApostrophe(s string) (string, bool) {
	r := []rune(s)
	if len(r) < 3 {
		return "", false
	}
	switch unicode.ToLower(r[0]) {
	case 'd', 'o', 'l':
	default:
		return "", false
	}
	if r[1] != '\'' && r[1] != '‘' {
		return "", false
	}
	body := r[2:]
	if !aposBody(body) {
		return "", false
	}
	if !strings.ContainsRune("aeiouAEIOU", r[0]) {
		r[0] = unicode.ToLower(r[0])
	} else {
		r[0] = unicode.ToUpper(r[0])
	}
	r[2] = unicode.ToUpper(r[2])
	return string(r), true
}

func aposBody(body []rune) bool {
	if len(body) >= 1 && allWord(body) {
		return true
	}
	if len(body) >= 3 && allWord(body[:len(body)-2]) && aposSet(body[len(body)-2]) && aposSet(body[len(body)-1]) {
		return true
	}
	return false
}

func allWord(r []rune) bool {
	if len(r) == 0 {
		return false
	}
	for _, ch := range r {
		if !isWord(ch) {
			return false
		}
	}
	return true
}

func aposSet(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func splitMc(s string) (prefix, rest string, ok bool) {
	var prefLen int
	switch {
	case strings.HasPrefix(s, "MC"):
		prefLen = 2
	case strings.HasPrefix(s, "Mc"), strings.HasPrefix(s, "mc"):
		prefLen = 2
	default:
		return "", "", false
	}
	rest = s[prefLen:]
	rr := []rune(rest)
	if len(rr) < 2 || !isWord(rr[0]) {
		return "", "", false
	}
	return s[:prefLen], rest, true
}

func isHonorific(s string) bool {
	switch strings.ToLower(s) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func hasInlinePeriod(s string) bool {
	r := []rune(s)
	for i := 0; i+2 < len(r); i++ {
		if r[i+1] == '.' && isWord(r[i]) && isWord(r[i+2]) {
			return true
		}
	}
	return false
}

func hasUCElsewhere(s string) bool {
	r := []rune(s)
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	if i >= len(r) || !isASCIILetter(r[i]) {
		return false
	}
	j := i
	for j < len(r) && isASCIILetter(r[j]) {
		j++
	}
	for k := i + 1; k < j; k++ {
		if r[k] >= 'A' && r[k] <= 'Z' {
			return true
		}
	}
	return false
}

func isExactSmall(s string) bool {
	r := []rune(s)
	for _, forms := range smallAlts {
		for _, form := range forms {
			fr := []rune(form)
			if len(fr) == len(r) && eqFold(r, fr) {
				return true
			}
		}
	}
	return false
}

func allConsonants(s string) bool {
	r := []rune(s)
	if len(r) <= 2 {
		return false
	}
	for _, ch := range r {
		if ch >= 'A' && ch <= 'Z' {
			ch = ch - 'A' + 'a'
		}
		if ch < 'a' || ch > 'z' {
			return false
		}
		switch ch {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

func capFirst(s string) string {
	r := []rune(s)
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	if i < len(r) && isWord(r[i]) {
		r[i] = unicode.ToUpper(r[i])
		return string(r)
	}
	return s
}

func capitalize(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return s
	}
	r[0] = unicode.ToUpper(r[0])
	for i := 1; i < len(r); i++ {
		r[i] = unicode.ToLower(r[i])
	}
	return string(r)
}

func applySmallFirst(s string) string {
	r := []rune(s)
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	n := matchSmallWithBoundary(r, i)
	if n == 0 {
		return s
	}
	return string(r[:i]) + capitalize(string(r[i:i+n])) + string(r[i+n:])
}

func matchSmallWithBoundary(r []rune, i int) int {
	rest := r[i:]
	for _, forms := range smallAlts {
		for _, form := range forms {
			fr := []rune(form)
			if len(fr) > len(rest) || !eqFold(rest[:len(fr)], fr) {
				continue
			}
			if isBoundary(r, i+len(fr)) {
				return len(fr)
			}
		}
	}
	return 0
}

func applySmallLast(s string) string {
	r := []rune(s)
	for i := 0; i <= len(r); i++ {
		if !isBoundary(r, i) {
			continue
		}
		rest := r[i:]
		for _, forms := range smallAlts {
			for _, form := range forms {
				fr := []rune(form)
				if len(fr) > len(rest) || !eqFold(rest[:len(fr)], fr) {
					continue
				}
				end := i + len(fr)
				if end == len(r) || (end+1 == len(r) && isPunct(r[end])) {
					return string(r[:i]) + capitalize(string(r[i:]))
				}
			}
		}
	}
	return s
}

func applySubphrase(s string) string {
	r := []rune(s)
	var b strings.Builder
	for i := 0; i < len(r); {
		if i+1 < len(r) && isSubPunct(r[i]) && r[i+1] == ' ' {
			if n := matchSmallPrefix(r[i+2:]); n > 0 {
				b.WriteRune(r[i])
				b.WriteRune(' ')
				b.WriteString(capitalize(string(r[i+2 : i+2+n])))
				i += 2 + n
				continue
			}
		}
		b.WriteRune(r[i])
		i++
	}
	return b.String()
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	default:
		return false
	}
}

func matchSmallPrefix(rest []rune) int {
	for _, forms := range smallAlts {
		for _, form := range forms {
			fr := []rune(form)
			if len(fr) > len(rest) {
				continue
			}
			if eqExact(rest[:len(fr)], fr) {
				return len(fr)
			}
		}
	}
	return 0
}
EOF

find "$root" -type f -name '*.py' -delete
rm -rf "$root/titlecase"