#!/bin/sh
# Reference solution: replace the Python tree with a stdlib Go titlecase program.
set -eu
cd /workspace/repo

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 16*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	for in.Scan() {
		fmt.Fprintln(out, titlecase(in.Text(), true))
	}
	if err := in.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := out.Flush(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

type smallAlt struct {
	text   string
	optDot bool
}

var smallAlts = []smallAlt{
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

var punct = map[rune]bool{}

func init() {
	for _, r := range "!\"#$%&'()*+,-./:;?@[\\]_`{|}~‒–—―‘“" {
		punct[r] = true
	}
}

func isPunct(r rune) bool { return punct[r] }

func isSubBreak(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func isPyWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isPySpace(r rune) bool { return unicode.IsSpace(r) }

func isASCIILetter(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z')
}

func pyCapitalize(s string) string {
	if s == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	return strings.ToUpper(string(r)) + strings.ToLower(s[size:])
}

func pyUpperFirst(s string) string {
	if s == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	return strings.ToUpper(string(r)) + s[size:]
}

func boundary(rs []rune, i int) bool {
	prev := i > 0 && isPyWord(rs[i-1])
	next := i < len(rs) && isPyWord(rs[i])
	if i == 0 {
		return next
	}
	if i == len(rs) {
		return prev
	}
	return prev != next
}

func foldPrefix(rs []rune, i int, lit string, sensitive bool) (int, bool) {
	for _, want := range lit {
		if i >= len(rs) {
			return 0, false
		}
		got := rs[i]
		if sensitive {
			if got != want {
				return 0, false
			}
		} else if unicode.ToLower(got) != unicode.ToLower(want) {
			return 0, false
		}
		i++
	}
	return i, true
}

func matchAltEnd(rs []rune, i int, alt smallAlt, boundaryAfter bool, sensitive bool) (int, bool) {
	base, ok := foldPrefix(rs, i, alt.text, sensitive)
	if !ok {
		return 0, false
	}
	if alt.optDot && base < len(rs) && rs[base] == '.' {
		end := base + 1
		if !boundaryAfter || boundary(rs, end) {
			return end, true
		}
	}
	if !boundaryAfter || boundary(rs, base) {
		return base, true
	}
	return 0, false
}

func isSmallWord(word string) bool {
	switch strings.ToLower(word) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for p := maxPunct; p >= 0; p-- {
		for _, alt := range smallAlts {
			end, ok := matchAltEnd(rs, p, alt, true, false)
			if !ok {
				continue
			}
			return string(rs[:p]) + pyCapitalize(string(rs[p:end])) + string(rs[end:])
		}
	}
	return word
}

func reachesEnd(rs []rune, pos int) (int, bool) {
	if pos == len(rs) {
		return pos, true
	}
	if pos+1 == len(rs) && isPunct(rs[pos]) {
		return pos + 1, true
	}
	return 0, false
}

func applySmallLast(word string) string {
	rs := []rune(word)
	for i := 0; i <= len(rs); i++ {
		if !boundary(rs, i) {
			continue
		}
		for _, alt := range smallAlts {
			base, ok := foldPrefix(rs, i, alt.text, false)
			if !ok {
				continue
			}
			if alt.optDot && base < len(rs) && rs[base] == '.' {
				if end, ok := reachesEnd(rs, base+1); ok {
					return string(rs[:i]) + pyCapitalize(string(rs[i:end]))
				}
			}
			if end, ok := reachesEnd(rs, base); ok {
				return string(rs[:i]) + pyCapitalize(string(rs[i:end]))
			}
		}
	}
	return word
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(rs) {
		if i+1 < len(rs) && isSubBreak(rs[i]) && rs[i+1] == ' ' {
			for _, alt := range smallAlts {
				end, ok := matchAltEnd(rs, i+2, alt, false, true)
				if !ok {
					continue
				}
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2 : end])))
				i = end
				goto next
			}
		}
		b.WriteRune(rs[i])
		i++
	next:
	}
	return b.String()
}

func hasInlinePeriod(word string) bool {
	rs := []rune(word)
	for i := 1; i+1 < len(rs); i++ {
		if rs[i] == '.' && isPyWord(rs[i-1]) && isPyWord(rs[i+1]) {
			return true
		}
	}
	return false
}

func hasUCElsewhere(word string) bool {
	rs := []rune(word)
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for p := 0; p <= maxPunct; p++ {
		rest := rs[p:]
		if len(rest) < 2 || !isASCIILetter(rest[0]) {
			continue
		}
		for _, r := range rest[1:] {
			if r >= 'A' && r <= 'Z' {
				return true
			}
			if !isASCIILetter(r) {
				break
			}
		}
	}
	return false
}

func capFirst(word string) string {
	rs := []rune(word)
	for i, r := range rs {
		if isPyWord(r) {
			for k := 0; k < i; k++ {
				if !isPunct(rs[k]) {
					return word
				}
			}
			return strings.ToUpper(string(rs[:i+1])) + string(rs[i+1:])
		}
		if !isPunct(r) {
			return word
		}
	}
	return word
}

func isAllConsonants(word string) bool {
	rs := []rune(word)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
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

func isInitials(word string) bool {
	if word == "" {
		return false
	}
	var match func(int) bool
	match = func(i int) bool {
		if i == len(word) {
			return true
		}
		if i+2 <= len(word) && word[i] >= 'A' && word[i] <= 'Z' && word[i+1] == '.' {
			if match(i + 2) {
				return true
			}
		}
		if i+3 <= len(word) && word[i] >= 'A' && word[i] <= 'Z' && word[i+1] == '.' && word[i+2] >= 'A' && word[i+2] <= 'Z' {
			if match(i + 3) {
				return true
			}
		}
		return false
	}
	return match(0)
}

func isAposWord(word string) bool {
	rs := []rune(word)
	if len(rs) < 3 {
		return false
	}
	switch rs[0] {
	case 'd', 'D', 'l', 'L', 'o', 'O':
	default:
		return false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return false
	}
	rest := rs[2:]
	if len(rest) == 0 {
		return false
	}
	if allPyWord(rest) {
		return true
	}
	// (?:['s]{2})? can consume two trailing class characters that [\w] would
	// otherwise take, so the word run must give those two characters back.
	if len(rest) >= 3 && allPyWord(rest[:len(rest)-2]) && isAposTail(rest[len(rest)-2]) && isAposTail(rest[len(rest)-1]) {
		return true
	}
	return false
}

func allPyWord(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if !isPyWord(r) {
			return false
		}
	}
	return true
}

func isAposTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func rewriteApos(word string) string {
	rs := []rune(word)
	var first string
	switch rs[0] {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		first = strings.ToUpper(string(rs[0]))
	default:
		first = strings.ToLower(string(rs[0]))
	}
	return first + string(rs[1]) + strings.ToUpper(string(rs[2])) + string(rs[3:])
}

func isHonorific(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func splitMc(word string) (string, string, bool) {
	var prefix string
	switch {
	case strings.HasPrefix(word, "Mc"), strings.HasPrefix(word, "mc"), strings.HasPrefix(word, "MC"):
		prefix = word[:2]
	default:
		return "", "", false
	}
	rest := word[len(prefix):]
	r, _ := utf8.DecodeRuneInString(rest)
	if r == utf8.RuneError && rest == "" {
		return "", "", false
	}
	if !isPyWord(r) || utf8.RuneCountInString(rest) < 2 {
		return "", "", false
	}
	return prefix, rest, true
}

func splitKeepSpace(line string) (words, spaces []string) {
	if line == "" {
		return []string{""}, nil
	}
	rs := []rune(line)
	i := 0
	for {
		j := i
		for j < len(rs) && !isPySpace(rs[j]) {
			j++
		}
		words = append(words, string(rs[i:j]))
		if j >= len(rs) {
			return words, spaces
		}
		spaces = append(spaces, string(rs[j:j+1]))
		i = j + 1
		if i == len(rs) {
			words = append(words, "")
			return words, spaces
		}
	}
}

func joinWords(words, spaces []string) string {
	n := len(words) + len(spaces)
	parts := make([]string, n)
	wi, si := 0, 0
	for i := 0; i < n; i++ {
		if i%2 == 0 {
			parts[i] = words[wi]
			wi++
		} else {
			parts[i] = spaces[si]
			si++
		}
	}
	return strings.Join(parts, "")
}

func splitNewlines(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	start := 0
	for i := 0; i < len(text); i++ {
		if text[i] == '\n' || text[i] == '\r' {
			lines = append(lines, text[start:i])
			for i < len(text) && (text[i] == '\n' || text[i] == '\r') {
				i++
			}
			start = i
			i--
		}
	}
	lines = append(lines, text[start:])
	return lines
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = titlecaseLine(line, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitKeepSpace(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titleWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(joinWords(tc, spaces))
}

func titleWord(word string, allCaps bool) string {
	if allCaps && isInitials(word) {
		return word
	}
	if isAposWord(word) {
		return rewriteApos(word)
	}
	if prefix, rest, ok := splitMc(word); ok {
		return pyCapitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		return pyUpperFirst(word)
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
	if isAllConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}
EOF

find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -mindepth 1 -type d -empty -delete
go build ./...
