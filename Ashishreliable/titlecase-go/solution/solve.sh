#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod << 'EOF'
module titlecaseport

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

// Effective punctuation from python-titlecase's character class after regex escapes.
// '_' is a word character, not punctuation.
const punctChars = "!\"\u201c#$%&'\u2018()*+,-./:;?@[\\]`{|}~\u2012\u2013\u2014\u2015"

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 1024*1024)
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

func titlecase(text string, smallFirstLast bool) string {
	lines := splitCollapsed(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, titlecaseLine(line, smallFirstLast))
	}
	return strings.Join(processed, "\n")
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitWS(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = processWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(joinWords(tc, spaces))
}

func processWord(word string, allCaps bool) string {
	if allCaps && isInitials(word) {
		return word
	}
	if apos, ok := applyApos(word); ok {
		return apos
	}
	if prefix, rest, ok := splitMac(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		return upperFirst(word)
	}
	if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
		return word
	}
	if isWholeSmall(word) {
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
	if utf8.RuneCountInString(word) > 2 && isAllConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func splitCollapsed(s string) []string {
	rs := []rune(s)
	var out []string
	start := 0
	for i := 0; i < len(rs); i++ {
		if rs[i] != '\n' && rs[i] != '\r' {
			continue
		}
		out = append(out, string(rs[start:i]))
		for i < len(rs) && (rs[i] == '\n' || rs[i] == '\r') {
			i++
		}
		start = i
		i--
	}
	out = append(out, string(rs[start:]))
	if len(out) == 0 {
		return []string{""}
	}
	return out
}

func splitWS(s string) (words, spaces []string) {
	var b strings.Builder
	parts := make([]string, 0)
	flush := func() {
		parts = append(parts, b.String())
		b.Reset()
	}
	for _, r := range s {
		if unicode.IsSpace(r) {
			flush()
			parts = append(parts, string(r))
			continue
		}
		b.WriteRune(r)
	}
	flush()
	for i, part := range parts {
		if i%2 == 0 {
			words = append(words, part)
		} else {
			spaces = append(spaces, part)
		}
	}
	return words, spaces
}

func joinWords(words, spaces []string) string {
	var b strings.Builder
	n := len(words)
	if len(spaces) > n {
		n = len(spaces)
	}
	for i := 0; i < n; i++ {
		if i < len(words) {
			b.WriteString(words[i])
		}
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsDigit(r)
}

func isPunct(r rune) bool {
	return strings.ContainsRune(punctChars, r)
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func isAZ(b byte) bool {
	return b >= 'A' && b <= 'Z'
}

func isInitials(s string) bool {
	if s == "" {
		return false
	}
	var rec func(int) bool
	rec = func(i int) bool {
		if i == len(s) {
			return true
		}
		if i+2 <= len(s) && isAZ(s[i]) && s[i+1] == '.' && rec(i+2) {
			return true
		}
		if i+3 <= len(s) && isAZ(s[i]) && s[i+1] == '.' && isAZ(s[i+2]) && rec(i+3) {
			return true
		}
		return false
	}
	return rec(0)
}

func applyApos(word string) (string, bool) {
	r := []rune(word)
	if len(r) < 3 {
		return "", false
	}
	switch unicode.ToLower(r[0]) {
	case 'd', 'o', 'l':
	default:
		return "", false
	}
	if r[1] != '\'' && r[1] != '\u2018' {
		return "", false
	}
	j := 2
	if !isWord(r[j]) {
		return "", false
	}
	for j < len(r) && isWord(r[j]) {
		j++
	}
	rest := len(r) - j
	if rest != 0 {
		if rest != 2 || !isAposSuf(r[j]) || !isAposSuf(r[j+1]) {
			// 's' is a word character, so a trailing suffix of s's was consumed by [\w]+.
			if rest != 0 {
				return "", false
			}
		}
	}
	first := r[0]
	if !strings.ContainsRune("aeiouAEIOU", first) {
		first = unicode.ToLower(first)
	} else {
		first = unicode.ToUpper(first)
	}
	third := unicode.ToUpper(r[2])
	return string(first) + string(r[1]) + string(third) + string(r[3:]), true
}

func isAposSuf(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func splitMac(word string) (prefix, rest string, ok bool) {
	r := []rune(word)
	if len(r) < 4 {
		return "", "", false
	}
	mac := (r[0] == 'M' || r[0] == 'm') && r[1] == 'c'
	upperMC := r[0] == 'M' && r[1] == 'C'
	if !mac && !upperMC {
		return "", "", false
	}
	if !isWord(r[2]) {
		return "", "", false
	}
	return string(r[:2]), string(r[2:]), true
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
	r := []rune(word)
	for i := 1; i+1 < len(r); i++ {
		if r[i] == '.' && isWord(r[i-1]) && isWord(r[i+1]) {
			return true
		}
	}
	return false
}

func hasUCElsewhere(word string) bool {
	prevLetter := false
	for i := 0; i < len(word); i++ {
		c := word[i]
		upper := c >= 'A' && c <= 'Z'
		letter := upper || (c >= 'a' && c <= 'z')
		if upper && prevLetter {
			return true
		}
		prevLetter = letter
	}
	return false
}

func isWholeSmall(word string) bool {
	r := []rune(word)
	for _, m := range matchers {
		for _, n := range m(r, 0, true) {
			if n == len(r) {
				return true
			}
		}
	}
	return false
}

func isAllConsonants(word string) bool {
	if word == "" {
		return false
	}
	for _, r := range word {
		if r > unicode.MaxASCII {
			return false
		}
		c := unicode.ToLower(r)
		if c < 'a' || c > 'z' {
			return false
		}
		switch c {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	r := []rune(word)
	for i, ch := range r {
		if isPunct(ch) {
			continue
		}
		if isWord(ch) {
			r[i] = unicode.ToUpper(ch)
			return string(r)
		}
		return word
	}
	return word
}

func upperFirst(s string) string {
	r, size := utf8.DecodeRuneInString(s)
	if r == utf8.RuneError && size == 0 {
		return s
	}
	return string(unicode.ToUpper(r)) + s[size:]
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

type matcher func(r []rune, i int, fold bool) []int

var matchers = []matcher{
	lit("a"), lit("an"), lit("and"), lit("as"), lit("at"),
	lit("but"), lit("by"), lit("en"), lit("for"), lit("if"),
	lit("in"), lit("of"), lit("on"), lit("or"), lit("the"), lit("to"),
	optDot("v"), lit("via"), optDot("vs"),
}

func lit(s string) matcher {
	want := []rune(s)
	return func(r []rune, i int, fold bool) []int {
		if i+len(want) > len(r) {
			return nil
		}
		for k, ch := range want {
			got := r[i+k]
			if fold {
				got = unicode.ToLower(got)
				ch = unicode.ToLower(ch)
			}
			if got != ch {
				return nil
			}
		}
		return []int{len(want)}
	}
}

func optDot(s string) matcher {
	want := []rune(s)
	return func(r []rune, i int, fold bool) []int {
		if i+len(want) > len(r) {
			return nil
		}
		for k, ch := range want {
			got := r[i+k]
			if fold {
				got = unicode.ToLower(got)
				ch = unicode.ToLower(ch)
			}
			if got != ch {
				return nil
			}
		}
		n := len(want)
		if i+n < len(r) && r[i+n] == '.' {
			return []int{n + 1, n}
		}
		return []int{n}
	}
}

func boundaryAt(r []rune, i int) bool {
	if i < 0 || i > len(r) {
		return false
	}
	var left, right bool
	if i > 0 {
		left = isWord(r[i-1])
	}
	if i < len(r) {
		right = isWord(r[i])
	}
	return left != right
}

func applySmallFirst(s string) string {
	r := []rune(s)
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	for _, m := range matchers {
		for _, n := range m(r, i, true) {
			if boundaryAt(r, i+n) {
				return string(r[:i]) + capitalize(string(r[i:i+n])) + string(r[i+n:])
			}
		}
	}
	return s
}

func applySmallLast(s string) string {
	r := []rune(s)
	for i := 0; i < len(r); i++ {
		if !boundaryAt(r, i) {
			continue
		}
		for _, m := range matchers {
			for _, n := range m(r, i, true) {
				end := i + n
				if end < len(r) && end+1 == len(r) && isPunct(r[end]) {
					end++
				}
				if end == len(r) {
					return string(r[:i]) + capitalize(string(r[i:end]))
				}
			}
		}
	}
	return s
}

func applySubphrase(s string) string {
	r := []rune(s)
	var out []rune
	for i := 0; i < len(r); {
		if isSubPunct(r[i]) && i+1 < len(r) && r[i+1] == ' ' {
			hit := false
			for _, m := range matchers {
				lens := m(r, i+2, false)
				if len(lens) == 0 {
					continue
				}
				n := lens[0]
				out = append(out, r[i], ' ')
				out = append(out, []rune(capitalize(string(r[i+2:i+2+n])))...)
				i += 2 + n
				hit = true
				break
			}
			if hit {
				continue
			}
		}
		out = append(out, r[i])
		i++
	}
	return string(out)
}
EOF

find /workspace/repo -type f -name '*.py' -delete
go fmt main.go
go build -buildvcs=false .
