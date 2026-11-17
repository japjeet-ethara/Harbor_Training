#!/bin/bash
set -euo pipefail

REPO=/workspace/repo
mkdir -p "$REPO"

cat > "$REPO/go.mod" <<'GOMOD'
module titlecase

go 1.23
GOMOD

cat > "$REPO/main.go" <<'GO'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
)

var punctChars = []rune{
	'!', '"', '\u201c', '#', '$', '%', '&', '\'', '\u2018', '(', ')', '*', '+', ',',
	'\\', '-', '\u2013', '\u2012', '\u2014', '\u2015', '.', '/', ':', ';', '?', '@',
	'[', ']', '_', '`', '{', '|', '}', '~',
}

var punctSet = func() map[rune]bool {
	m := make(map[rune]bool, len(punctChars))
	for _, r := range punctChars {
		m[r] = true
	}
	return m
}()

func isPunct(r rune) bool { return punctSet[r] }

// Python's str whitespace: Unicode White_Space plus the control characters
// whose bidirectional class is B (0x1c-0x1f).
func isSpaceRune(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

// Python's \w for str: alphanumeric characters and underscore.
func isWordRune(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

var smallAlts = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
	"on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

func foldRune(r rune) rune {
	if r >= 'A' && r <= 'Z' {
		return r + ('a' - 'A')
	}
	return r
}

func altAt(rs []rune, i int, alt string, fold bool) bool {
	ar := []rune(alt)
	if i < 0 || i+len(ar) > len(rs) {
		return false
	}
	for k, a := range ar {
		c := rs[i+k]
		if fold {
			c = foldRune(c)
			a = foldRune(a)
		}
		if c != a {
			return false
		}
	}
	return true
}

func matchSmallAt(rs []rune, i int, fold bool) (int, bool) {
	for _, alt := range smallAlts {
		if altAt(rs, i, alt, fold) {
			return len([]rune(alt)), true
		}
	}
	return 0, false
}

func isBoundary(rs []rune, i int) bool {
	before := i > 0 && isWordRune(rs[i-1])
	after := i < len(rs) && isWordRune(rs[i])
	return before != after
}

func pyCapitalize(s string) string {
	if s == "" {
		return s
	}
	rs := []rune(s)
	return strings.ToUpper(string(rs[0])) + strings.ToLower(string(rs[1:]))
}

func isSmallWord(word string) bool {
	rs := []rune(word)
	for _, alt := range smallAlts {
		if len([]rune(alt)) == len(rs) && altAt(rs, 0, alt, true) {
			return true
		}
	}
	return false
}

func smallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	for _, alt := range smallAlts {
		n := len([]rune(alt))
		if altAt(rs, i, alt, true) && isBoundary(rs, i+n) {
			return string(rs[:i]) + pyCapitalize(string(rs[i:i+n])) + string(rs[i+n:])
		}
	}
	return word
}

func isSuffixRune(r rune) bool {
	return r == '\'' || foldRune(r) == 's'
}

func smallLast(word string) string {
	rs := []rune(word)
	for p := 0; p < len(rs); p++ {
		if !isBoundary(rs, p) {
			continue
		}
		for _, alt := range smallAlts {
			n := len([]rune(alt))
			if !altAt(rs, p, alt, true) {
				continue
			}
			q := p + n
			end := -1
			if q == len(rs) {
				end = q
			} else if q+1 == len(rs) && isPunct(rs[q]) {
				end = q + 1
			}
			if end >= 0 {
				return string(rs[:p]) + pyCapitalize(string(rs[p:end])) + string(rs[end:])
			}
		}
	}
	return word
}

func aposSecond(word string) (bool, string) {
	rs := []rune(word)
	if len(rs) < 3 {
		return false, ""
	}
	c := foldRune(rs[0])
	if c != 'd' && c != 'o' && c != 'l' {
		return false, ""
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return false, ""
	}
	l := 2
	if !isWordRune(rs[l]) {
		return false, ""
	}
	end := l
	for end < len(rs) && isWordRune(rs[end]) {
		end++
	}
	valid := false
	if end == len(rs) {
		valid = true
	} else if len(rs)-l >= 3 {
		sufStart := len(rs) - 2
		if sufStart >= l+1 && isSuffixRune(rs[sufStart]) && isSuffixRune(rs[sufStart+1]) {
			valid = true
			for k := l; k < sufStart; k++ {
				if !isWordRune(rs[k]) {
					valid = false
					break
				}
			}
		}
	}
	if !valid {
		return false, ""
	}
	var first string
	if !strings.ContainsRune("aeiouAEIOU", rs[0]) {
		first = strings.ToLower(string(rs[0]))
	} else {
		first = strings.ToUpper(string(rs[0]))
	}
	return true, first + string(rs[1]) + strings.ToUpper(string(rs[2])) + string(rs[3:])
}

func macMc(word string) (bool, string) {
	rs := []rune(word)
	if len(rs) < 4 {
		return false, ""
	}
	prefix := string(rs[:2])
	if prefix != "Mc" && prefix != "mc" && prefix != "MC" {
		return false, ""
	}
	rest := rs[2:]
	if !isWordRune(rest[0]) {
		return false, ""
	}
	return true, pyCapitalize(prefix) + titlecase(string(rest), true)
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
		if isWordRune(rs[i]) && rs[i+1] == '.' && isWordRune(rs[i+2]) {
			return true
		}
	}
	return false
}

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func hasUppercaseElsewhere(word string) bool {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	j := i
	for j < len(rs) && isASCIILetter(rs[j]) {
		j++
	}
	if j == i {
		return false
	}
	for k := i + 1; k < j; k++ {
		if rs[k] >= 'A' && rs[k] <= 'Z' {
			return true
		}
	}
	return false
}

func uppercaseInitials(word string) bool {
	rs := []rune(word)
	n := len(rs)
	if n == 0 {
		return false
	}
	memo := make([]int8, n+1)
	var valid func(int) bool
	valid = func(i int) bool {
		if i == n {
			return true
		}
		if memo[i] != 0 {
			return memo[i] == 1
		}
		ok := false
		if i+1 < n && rs[i] >= 'A' && rs[i] <= 'Z' && rs[i+1] == '.' {
			if valid(i + 2) {
				ok = true
			} else if i+2 < n && rs[i+2] >= 'A' && rs[i+2] <= 'Z' && valid(i+3) {
				ok = true
			}
		}
		if ok {
			memo[i] = 1
		} else {
			memo[i] = 2
		}
		return ok
	}
	return valid(0)
}

var consonantSet = func() map[rune]bool {
	m := map[rune]bool{}
	for r := 'a'; r <= 'z'; r++ {
		if !strings.ContainsRune("aeiouy", r) {
			m[r] = true
		}
	}
	return m
}()

func allConsonants(word string) bool {
	rs := []rune(word)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		if !consonantSet[foldRune(r)] {
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) {
		if isWordRune(rs[i]) {
			break
		}
		if isPunct(rs[i]) {
			i++
			continue
		}
		return word
	}
	if i >= len(rs) {
		return word
	}
	up := strings.ToUpper(string(rs[i]))
	if up == string(rs[i]) {
		return word
	}
	var b strings.Builder
	b.WriteString(string(rs[:i]))
	b.WriteString(up)
	b.WriteString(string(rs[i+1:]))
	return b.String()
}

func splitLine(line string) ([]string, []string) {
	words := make([]string, 0, 4)
	spaces := make([]string, 0, 4)
	var cur []rune
	for _, r := range line {
		if isSpaceRune(r) {
			words = append(words, string(cur))
			cur = cur[:0]
			spaces = append(spaces, string(r))
		} else {
			cur = append(cur, r)
		}
	}
	words = append(words, string(cur))
	return words, spaces
}

func joinWords(words, spaces []string) string {
	var b strings.Builder
	for i, w := range words {
		b.WriteString(w)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func isSubphrasePunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2013', '\u2012', '\u2014', '\u2015':
		return true
	}
	return false
}

func subphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(rs) {
		if isSubphrasePunct(rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			if n, ok := matchSmallAt(rs, i+2, false); ok {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(strings.ToUpper(string(rs[i+2])))
				b.WriteString(string(rs[i+3 : i+2+n]))
				i = i + 2 + n
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitLine(line)
	tc := make([]string, 0, len(words))

	for _, word := range words {
		if allCaps && uppercaseInitials(word) {
			tc = append(tc, word)
			continue
		}

		if ok, w := aposSecond(word); ok {
			tc = append(tc, w)
			continue
		}

		if ok, w := macMc(word); ok {
			tc = append(tc, w)
			continue
		}

		if isHonorific(word) {
			rs := []rune(word)
			tc = append(tc, strings.ToUpper(string(rs[0]))+string(rs[1:]))
			continue
		}

		if hasInlinePeriod(word) || (!allCaps && hasUppercaseElsewhere(word)) {
			tc = append(tc, word)
			continue
		}

		if isSmallWord(word) {
			tc = append(tc, strings.ToLower(word))
			continue
		}

		if strings.Contains(word, "/") && !strings.Contains(word, "//") {
			parts := strings.Split(word, "/")
			for i, p := range parts {
				parts[i] = titlecase(p, false)
			}
			tc = append(tc, strings.Join(parts, "/"))
			continue
		}

		if strings.Contains(word, "-") {
			parts := strings.Split(word, "-")
			for i, p := range parts {
				parts[i] = titlecase(p, false)
			}
			tc = append(tc, strings.Join(parts, "-"))
			continue
		}

		if allCaps {
			word = strings.ToLower(word)
		}

		if allConsonants(word) {
			tc = append(tc, strings.ToUpper(word))
			continue
		}

		tc = append(tc, capFirst(word))
	}

	if smallFirstLast && len(tc) > 0 {
		tc[0] = smallFirst(tc[0])
		tc[len(tc)-1] = smallLast(tc[len(tc)-1])
	}

	return subphrase(joinWords(tc, spaces))
}

func splitLines(text string) []string {
	rs := []rune(text)
	lines := make([]string, 0, 4)
	start := 0
	i := 0
	for i < len(rs) {
		if rs[i] == '\r' || rs[i] == '\n' {
			lines = append(lines, string(rs[start:i]))
			for i < len(rs) && (rs[i] == '\r' || rs[i] == '\n') {
				i++
			}
			start = i
			continue
		}
		i++
	}
	lines = append(lines, string(rs[start:]))
	return lines
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitLines(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, processLine(line, smallFirstLast))
	}
	return strings.Join(processed, "\n")
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 64*1024), 4*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()

	for in.Scan() {
		fmt.Fprintln(out, titlecase(in.Text(), true))
	}
}
GO

# The task forbids Python files anywhere in the repository.
find "$REPO" -type f -name '*.py' -delete
find "$REPO" -type d -name '__pycache__' -prune -exec rm -rf {} +
rm -rf "$REPO/titlecase"
