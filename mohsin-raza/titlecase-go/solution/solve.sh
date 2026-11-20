#!/bin/bash
# Oracle solution: write a Go port of python-titlecase into /workspace/repo,
# then delete every .py file there. Go standard library only.
set -euo pipefail

REPO="${REPO_DIR:-/workspace/repo}"
cd "$REPO"

cat > go.mod <<'GOEOF'
module titlecasego

go 1.21
GOEOF

cat > main.go <<'GOEOF'
// Command titlecase is a Go port of the Python titlecase() function
// (python-titlecase 2.4.1, running without the optional "regex" package).
// It reads one title per line on stdin and prints one titlecased line per input line.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

// Ordered exactly like the alternation in the Python SMALL pattern
// (a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?),
// with the optional "\." expanded greedy-first.
var smallCands = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to",
	"v.", "v", "via", "vs.", "vs",
}

// Characters of the Python PUNCT class.
const punctChars = "!\"\u201c#$%&'\u2018()*+,-\u2013\u2012\u2014\u2015./:;?@[\\]_`{|}~"

// Characters that may open a SUBPHRASE ("[:.;?!\-–‒—―]").
const subphraseChars = ":.;?!-\u2013\u2012\u2014\u2015"

func isPunct(r rune) bool         { return strings.ContainsRune(punctChars, r) }
func isSubphraseOpen(r rune) bool { return strings.ContainsRune(subphraseChars, r) }

// isWord mirrors Python's \w for str patterns: alphanumeric or underscore.
func isWord(r rune) bool { return unicode.IsLetter(r) || unicode.IsNumber(r) || r == '_' }

// isPySpace mirrors Python's \s for str patterns.
func isPySpace(r rune) bool { return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f) }

func isUpperASCII(r rune) bool  { return r >= 'A' && r <= 'Z' }
func isLetterASCII(r rune) bool { return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') }

func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	out := make([]rune, len(rs))
	out[0] = unicode.ToUpper(rs[0])
	for i := 1; i < len(rs); i++ {
		out[i] = unicode.ToLower(rs[i])
	}
	return string(out)
}

// wordBoundary mirrors \b at index i.
func wordBoundary(rs []rune, i int) bool {
	left := i > 0 && isWord(rs[i-1])
	right := i < len(rs) && isWord(rs[i])
	return left != right
}

func runeLen(s string) int { return len([]rune(s)) }

func equalFoldAt(rs []rune, i int, cand string) bool {
	n := runeLen(cand)
	if i < 0 || i+n > len(rs) {
		return false
	}
	return strings.EqualFold(string(rs[i:i+n]), cand)
}

// SMALL_WORDS: ^(SMALL)$ with re.I
func isSmallWord(w string) bool {
	for _, c := range smallCands {
		if strings.EqualFold(w, c) {
			return true
		}
	}
	return false
}

// SMALL_FIRST: ^([PUNCT]*)(SMALL)\b  (re.I)  -> group1 + group2.capitalize()
func smallFirst(w string) string {
	rs := []rune(w)
	p := 0
	for p < len(rs) && isPunct(rs[p]) {
		p++
	}
	for _, c := range smallCands {
		n := runeLen(c)
		if equalFoldAt(rs, p, c) && wordBoundary(rs, p+n) {
			return string(rs[:p]) + capitalize(string(rs[p:p+n])) + string(rs[p+n:])
		}
	}
	return w
}

// SMALL_LAST: \b(SMALL)[PUNCT]?$  (re.I)  -> match.capitalize()
func smallLast(w string) string {
	rs := []rune(w)
	for s := 0; s <= len(rs); s++ {
		if !wordBoundary(rs, s) {
			continue
		}
		for _, c := range smallCands {
			n := runeLen(c)
			if !equalFoldAt(rs, s, c) {
				continue
			}
			e := s + n
			if e == len(rs) || (e+1 == len(rs) && isPunct(rs[e])) {
				return string(rs[:s]) + capitalize(string(rs[s:]))
			}
		}
	}
	return w
}

// SUBPHRASE: ([:.;?!\-–‒—―][ ])(SMALL)  (case sensitive) -> group1 + group2.capitalize()
func subphrase(s string) string {
	rs := []rune(s)
	out := make([]rune, 0, len(rs))
	i := 0
	for i < len(rs) {
		if isSubphraseOpen(rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			matched := false
			for _, c := range smallCands {
				n := runeLen(c)
				if i+2+n <= len(rs) && string(rs[i+2:i+2+n]) == c {
					out = append(out, rs[i], rs[i+1])
					out = append(out, []rune(capitalize(c))...)
					i += 2 + n
					matched = true
					break
				}
			}
			if matched {
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

// UC_INITIALS: ^(?:[A-Z]\.|[A-Z]\.[A-Z])+$
func ucInitials(rs []rune) bool {
	n := len(rs)
	if n == 0 {
		return false
	}
	reach := make([]bool, n+4)
	reach[0] = true
	for i := 0; i < n; i++ {
		if !reach[i] {
			continue
		}
		if i+1 < n && isUpperASCII(rs[i]) && rs[i+1] == '.' {
			reach[i+2] = true
			if i+2 < n && isUpperASCII(rs[i+2]) {
				reach[i+3] = true
			}
		}
	}
	return reach[n]
}

// APOS_SECOND: ^[dol]['‘][\w]+(?:['s]{2})?$  (re.I)
func aposSecond(rs []rune) bool {
	if len(rs) < 3 {
		return false
	}
	switch unicode.ToLower(rs[0]) {
	case 'd', 'o', 'l':
	default:
		return false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return false
	}
	rest := rs[2:]
	allWord := func(x []rune) bool {
		for _, r := range x {
			if !isWord(r) {
				return false
			}
		}
		return true
	}
	if len(rest) >= 1 && allWord(rest) {
		return true
	}
	inSet := func(r rune) bool { return r == '\'' || r == 's' || r == 'S' }
	if len(rest) >= 3 && allWord(rest[:len(rest)-2]) && inSet(rest[len(rest)-2]) && inSet(rest[len(rest)-1]) {
		return true
	}
	return false
}

// INLINE_PERIOD: [\w][.][\w]  (search)
func inlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if isWord(rs[i]) && rs[i+1] == '.' && isWord(rs[i+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE: [PUNCT]*?[a-zA-Z]+[A-Z]+?  (match at start)
func ucElsewhere(rs []rune) bool {
	k := 0
	for k < len(rs) && isPunct(rs[k]) {
		k++
	}
	if k >= len(rs) || !isLetterASCII(rs[k]) {
		return false
	}
	for j := k + 1; j < len(rs) && isLetterASCII(rs[j]); j++ {
		if isUpperASCII(rs[j]) {
			return true
		}
	}
	return false
}

// MAC_MC: ^([Mm]c|MC)(\w.+)
func macMc(rs []rune) (prefix, rest string, ok bool) {
	if len(rs) < 4 {
		return "", "", false
	}
	pre := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c'
	pre = pre || (rs[0] == 'M' && rs[1] == 'C')
	if !pre || !isWord(rs[2]) {
		return "", "", false
	}
	return string(rs[:2]), string(rs[2:]), true
}

// MR_MRS_MS_DR: ^((m((rs?)|s))|Dr)$  (re.I)
func isMrMrsMsDr(w string) bool {
	for _, c := range []string{"mr", "mrs", "ms", "dr"} {
		if strings.EqualFold(w, c) {
			return true
		}
	}
	return false
}

// A word of 3+ ASCII consonants (y counts as a vowel) is treated as an acronym.
func isAllConsonants(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		l := unicode.ToLower(r)
		if l < 'a' || l > 'z' || strings.ContainsRune("aeiouy", l) {
			return false
		}
	}
	return true
}

// CAPFIRST: ^[PUNCT]*?([\w])  -> upper-case the first \w character
func capFirst(w string) string {
	rs := []rune(w)
	for k := 0; k < len(rs); k++ {
		if isWord(rs[k]) {
			rs[k] = unicode.ToUpper(rs[k])
			return string(rs)
		}
		if !isPunct(rs[k]) {
			return w
		}
	}
	return w
}

func processWord(word string, allCaps bool) string {
	rs := []rune(word)

	if allCaps && ucInitials(rs) {
		return word
	}

	if aposSecond(rs) {
		first := rs[0]
		if !strings.ContainsRune("aeiouAEIOU", first) {
			return string(unicode.ToLower(first)) + string(rs[1]) + string(unicode.ToUpper(rs[2])) + string(rs[3:])
		}
		return string(unicode.ToUpper(first)) + string(rs[1]) + string(unicode.ToUpper(rs[2])) + string(rs[3:])
	}

	if prefix, rest, ok := macMc(rs); ok {
		return capitalize(prefix) + tcLine(rest, true)
	}

	if isMrMrsMsDr(word) {
		return string(unicode.ToUpper(rs[0])) + string(rs[1:])
	}

	if inlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}
	if isSmallWord(word) {
		return strings.ToLower(word)
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, p := range parts {
			parts[i] = tcLine(p, false)
		}
		return strings.Join(parts, "/")
	}

	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts {
			parts[i] = tcLine(p, false)
		}
		return strings.Join(parts, "-")
	}

	if allCaps {
		word = strings.ToLower(word)
		rs = []rune(word)
	}

	if isAllConsonants(rs) && len(rs) > 2 {
		return strings.ToUpper(word)
	}

	return capFirst(word)
}

// tcLine is titlecase() for a text that contains no \r or \n.
func tcLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line

	var words, spaces []string
	var cur []rune
	for _, r := range line {
		if isPySpace(r) {
			words = append(words, string(cur))
			spaces = append(spaces, string(r))
			cur = nil
		} else {
			cur = append(cur, r)
		}
	}
	words = append(words, string(cur))

	tc := make([]string, len(words))
	for i, w := range words {
		tc[i] = processWord(w, allCaps)
	}

	if smallFirstLast && len(tc) > 0 {
		tc[0] = smallFirst(tc[0])
		tc[len(tc)-1] = smallLast(tc[len(tc)-1])
	}

	var sb strings.Builder
	for i, w := range tc {
		sb.WriteString(w)
		if i < len(spaces) {
			sb.WriteString(spaces[i])
		}
	}
	return subphrase(sb.String())
}

func main() {
	data, err := io.ReadAll(bufio.NewReader(os.Stdin))
	if err != nil {
		os.Exit(1)
	}
	s := string(data)
	if s == "" {
		return
	}
	lines := strings.Split(s, "\n")
	if lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for _, l := range lines {
		w.WriteString(tcLine(l, true))
		w.WriteString("\n")
	}
}
GOEOF

gofmt -l . >/dev/null
find "$REPO" -type f -name '*.py' -delete
go build -o /dev/null ./...
