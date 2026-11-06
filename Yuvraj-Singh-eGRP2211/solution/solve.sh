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
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()

	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimRight(line, "\r\n")
			fmt.Fprintln(out, titlecase(line, true))
		}
		if err != nil {
			if err != io.EOF {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
			break
		}
	}
}
EOF

cat > titlecase.go << 'EOF'
package main

import (
	"regexp"
	"strings"
	"unicode"
)

// Port of ppannuto/python-titlecase titlecase() using the stdlib `re`
// patterns (the third-party `regex` module is not required). Go's regexp
// engine has no look-around, so the Python expressions are applied by
// scanning runes directly.

const (
	aposASCII = '\''
	aposLeft  = '\u2018' // ‘
)

var (
	ucInitials = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)

	// Longest-first is wrong: Python alternation is left-first.
	// v\.? is tried before via/vs, and the short words before the longer ones.
	smallAlts = []string{
		"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
	}

	punct = map[rune]bool{}

	subphrasePunct = map[rune]bool{
		':': true, '.': true, ';': true, '?': true, '!': true,
		'-': true, '\u2013': true, '\u2012': true, '\u2014': true, '\u2015': true,
	}
)

func init() {
	for _, r := range "!\"\u201c#$%&'\u2018()*+,-\u2013\u2012\u2014\u2015./:;?@[\\]_`{|}~" {
		punct[r] = true
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
	var b strings.Builder
	for i, w := range tc {
		b.WriteString(w)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return applySubphrase(b.String())
}

func titleWord(word string, allCaps bool) string {
	if word == "" {
		return ""
	}
	if allCaps && ucInitials.MatchString(word) {
		return word
	}
	if matchApos(word) {
		return transformApos(word)
	}
	if prefix, rest, ok := splitMac(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isMr(word) {
		rs := []rune(word)
		rs[0] = unicode.ToUpper(rs[0])
		return string(rs)
	}
	if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
		return word
	}
	if isSmallFull(word) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if allConsonants(word) && len([]rune(word)) > 2 {
		return strings.ToUpper(word)
	}
	return capfirst(word)
}

func splitLines(text string) []string {
	rs := []rune(text)
	var lines []string
	var cur []rune
	for i := 0; i < len(rs); {
		if rs[i] == '\r' || rs[i] == '\n' {
			lines = append(lines, string(cur))
			cur = cur[:0]
			for i < len(rs) && (rs[i] == '\r' || rs[i] == '\n') {
				i++
			}
			continue
		}
		cur = append(cur, rs[i])
		i++
	}
	lines = append(lines, string(cur))
	return lines
}

func splitSpaces(line string) (words, spaces []string) {
	var cur []rune
	for _, r := range line {
		if isPySpace(r) {
			words = append(words, string(cur))
			cur = nil
			spaces = append(spaces, string(r))
		} else {
			cur = append(cur, r)
		}
	}
	words = append(words, string(cur))
	return words, spaces
}

func isPySpace(r rune) bool {
	switch r {
	case ' ', '\t', '\n', '\r', '\v', '\f', '\u0085':
		return true
	}
	return unicode.Is(unicode.Zs, r)
}

func isWord(r rune) bool {
	if r == '_' {
		return true
	}
	return unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isPunct(r rune) bool {
	return punct[r]
}

func isAposS(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
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

func capfirst(word string) string {
	// Python CAPFIRST is ^[PUNCT]*?([\w]). *? takes as little punctuation as
	// possible, so a character that is both punctuation and a word character
	// (underscore) is the character that gets uppercased.
	rs := []rune(word)
	for i, r := range rs {
		if isWord(r) {
			rs[i] = unicode.ToUpper(r)
			return string(rs)
		}
		if !isPunct(r) {
			return word
		}
	}
	return word
}

func isSmallFull(word string) bool {
	for _, alt := range []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "via", "v", "v.", "vs", "vs."} {
		if strings.EqualFold(word, alt) {
			return true
		}
	}
	return false
}

func matchSmallPrefix(rs []rune, fold bool) (int, bool) {
	for _, alt := range smallAlts {
		altR := []rune(alt)
		if len(rs) < len(altR) {
			continue
		}
		chunk := string(rs[:len(altR)])
		if fold {
			if strings.EqualFold(chunk, alt) {
				return len(altR), true
			}
			continue
		}
		if chunk == alt {
			return len(altR), true
		}
	}
	return 0, false
}

func boundaryAt(rs []rune, i int) bool {
	var left, right bool
	if i > 0 {
		left = isWord(rs[i-1])
	}
	if i < len(rs) {
		right = isWord(rs[i])
	}
	if i == 0 {
		return len(rs) > 0 && right
	}
	if i == len(rs) {
		return left
	}
	return left != right
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for n := maxPunct; n >= 0; n-- {
		rest := rs[n:]
		for _, alt := range smallAlts {
			altR := []rune(alt)
			if len(rest) < len(altR) {
				continue
			}
			if !strings.EqualFold(string(rest[:len(altR)]), alt) {
				continue
			}
			if !boundaryAt(rest, len(altR)) {
				continue
			}
			matched := string(rest[:len(altR)])
			return string(rs[:n]) + capitalize(matched) + string(rest[len(altR):])
		}
	}
	return word
}

func applySmallLast(word string) string {
	rs := []rune(word)
	ends := make([]int, 0, 2)
	if len(rs) > 0 && isPunct(rs[len(rs)-1]) {
		ends = append(ends, len(rs)-1)
	}
	ends = append(ends, len(rs))
	for _, smallEnd := range ends {
		prefix := rs[:smallEnd]
		for _, alt := range smallAlts {
			altR := []rune(alt)
			if len(prefix) < len(altR) {
				continue
			}
			start := len(prefix) - len(altR)
			if !strings.EqualFold(string(prefix[start:]), alt) {
				continue
			}
			if !boundaryAt(prefix, start) {
				continue
			}
			matched := string(prefix[start:])
			return string(rs[:start]) + capitalize(matched) + string(rs[smallEnd:])
		}
	}
	return word
}

func applySubphrase(s string) string {
	rs := []rune(s)
	out := make([]rune, 0, len(rs))
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && subphrasePunct[rs[i]] && rs[i+1] == ' ' {
			// SUBPHRASE is case-sensitive: only a lowercase small word matches.
			if n, ok := matchSmallPrefix(rs[i+2:], false); ok {
				out = append(out, rs[i], ' ')
				out = append(out, []rune(capitalize(string(rs[i+2:i+2+n])))...)
				i += 2 + n
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

func splitMac(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	p := string(rs[:2])
	if p != "Mc" && p != "mc" && p != "MC" {
		return "", "", false
	}
	if !isWord(rs[2]) {
		return "", "", false
	}
	// `.+` must consume one more character and cannot cross a newline.
	for _, r := range rs[3:] {
		if r == '\n' || r == '\r' {
			return "", "", false
		}
	}
	return p, string(rs[2:]), true
}

func isMr(word string) bool {
	switch strings.ToLower(word) {
		case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

func matchApos(word string) bool {
	rs := []rune(word)
	if len(rs) < 3 {
		return false
	}
	switch unicode.ToLower(rs[0]) {
	case 'd', 'o', 'l':
	default:
		return false
	}
	if rs[1] != aposASCII && rs[1] != aposLeft {
		return false
	}
	body := rs[2:]
	for n := 1; n <= len(body); n++ {
		good := true
		for i := 0; i < n; i++ {
			if !isWord(body[i]) {
				good = false
				break
			}
		}
		if !good {
			break
		}
		rem := body[n:]
		if len(rem) == 0 {
			return true
		}
		if len(rem) == 2 && isAposS(rem[0]) && isAposS(rem[1]) {
			return true
		}
	}
	return false
}

func transformApos(word string) string {
	rs := []rune(word)
	var b strings.Builder
	first := rs[0]
	if !strings.ContainsRune("aeiouAEIOU", first) {
		b.WriteRune(unicode.ToLower(first))
	} else {
		b.WriteRune(unicode.ToUpper(first))
	}
	b.WriteRune(rs[1])
	if len(rs) > 2 {
		b.WriteRune(unicode.ToUpper(rs[2]))
		b.WriteString(string(rs[3:]))
	}
	return b.String()
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

// re.match, not search: an internal capital only counts in the first letter run.
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

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
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
EOF

find /workspace/repo -type f -name '*.py' -delete

# The module path is "titlecase", so `go build ./...` writes a binary of that
# name. The vendored Python package is a directory called titlecase, and Go
# refuses to replace a directory with that binary.
rm -rf /workspace/repo/titlecase
