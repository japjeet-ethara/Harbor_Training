#!/bin/bash
# Reference solution: writes a Go port of titlecase(), then removes the Python.
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'GO_SOURCE'
module titlecaseport

go 1.23
GO_SOURCE

cat > main.go <<'GO_SOURCE'
// Command titlecaseport reads one title per line from stdin and prints each
// one titlecased. It is a port of titlecase() from python-titlecase 2.4.1, as
// it behaves on Python 3.11 with the re fallback.
//
// It does not use package regexp. Go's \w, \s and \b are ASCII-only, while
// Python's follow Unicode, so every pattern is matched by hand on runes.
package main

import (
	"bufio"
	"bytes"
	"io"
	"os"
	"strings"
	"unicode"
)

const punct = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

const subphraseMarks = ":.;?!-–‒—―"

// smallWords lists the alternatives of SMALL in the order Python tries them.
// A greedy `v\.?` tries "v." before "v".
var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
	"on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

func isPunct(r rune) bool { return strings.ContainsRune(punct, r) }

func inRanges(ranges [][2]rune, r rune) bool {
	for _, span := range ranges {
		if r >= span[0] && r <= span[1] {
			return true
		}
	}
	return false
}

func baseWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func baseCased(r rune) bool {
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r) ||
		unicode.Is(unicode.Other_Lowercase, r) ||
		unicode.Is(unicode.Other_Uppercase, r)
}

func baseIgnorable(r rune) bool {
	if unicode.In(r, unicode.Mn, unicode.Me, unicode.Cf, unicode.Lm, unicode.Sk) {
		return true
	}
	switch r {
	case '\'', '.', ':', 0xB7, 0x387, 0x55F, 0x5F4, 0x2018, 0x2019, 0x2024,
		0x2027, 0xFE13, 0xFE52, 0xFE55, 0xFF07, 0xFF0E, 0xFF1A:
		return true
	}
	return false
}

// isWord matches Python's \w.
func isWord(r rune) bool { return baseWord(r) != inRanges(wordFlips, r) }

func isCased(r rune) bool { return baseCased(r) != inRanges(casedFlips, r) }

func isIgnorable(r rune) bool {
	return baseIgnorable(r) != inRanges(ignorableFlips, r)
}

// isSpace matches Python's \s, which is wider than unicode.IsSpace.
func isSpace(r rune) bool {
	switch {
	case r >= 0x09 && r <= 0x0D, r >= 0x1C && r <= 0x20, r == 0x85, r == 0xA0,
		r == 0x1680, r >= 0x2000 && r <= 0x200A, r == 0x2028, r == 0x2029,
		r == 0x202F, r == 0x205F, r == 0x3000:
		return true
	}
	return false
}

func upperRune(r rune) []rune {
	if s, ok := upperSpecial[r]; ok {
		return []rune(s)
	}
	return []rune{unicode.ToUpper(r)}
}

func titleRune(r rune) []rune {
	if s, ok := titleSpecial[r]; ok {
		return []rune(s)
	}
	return []rune{unicode.ToTitle(r)}
}

// upper matches str.upper().
func upper(text []rune) []rune {
	out := make([]rune, 0, len(text))
	for _, r := range text {
		out = append(out, upperRune(r)...)
	}
	return out
}

// finalSigma reports whether the capital sigma at i lowers to a final sigma.
func finalSigma(text []rune, i int) bool {
	j := i - 1
	for j >= 0 && isIgnorable(text[j]) {
		j--
	}
	if j < 0 || !isCased(text[j]) {
		return false
	}
	j = i + 1
	for j < len(text) && isIgnorable(text[j]) {
		j++
	}
	return j == len(text) || !isCased(text[j])
}

func lowerAt(text []rune, i int) []rune {
	r := text[i]
	if r == 0x3A3 {
		if finalSigma(text, i) {
			return []rune{0x3C2}
		}
		return []rune{0x3C3}
	}
	if s, ok := lowerSpecial[r]; ok {
		return []rune(s)
	}
	return []rune{unicode.ToLower(r)}
}

// lower matches str.lower().
func lower(text []rune) []rune {
	out := make([]rune, 0, len(text))
	for i := range text {
		out = append(out, lowerAt(text, i)...)
	}
	return out
}

// capitalize matches str.capitalize().
func capitalize(text []rune) []rune {
	if len(text) == 0 {
		return nil
	}
	out := titleRune(text[0])
	for i := 1; i < len(text); i++ {
		out = append(out, lowerAt(text, i)...)
	}
	return out
}

func equal(a, b []rune) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func concat(parts ...[]rune) []rune {
	var out []rune
	for _, part := range parts {
		out = append(out, part...)
	}
	return out
}

// foldMatches compares a rune with a lowercase ASCII pattern character the way
// re.IGNORECASE does, including its extra matches for i and s.
func foldMatches(r, want rune) bool {
	if r == want || r == unicode.ToUpper(want) {
		return true
	}
	switch want {
	case 'i':
		return r == 0x130 || r == 0x131
	case 's':
		return r == 0x17F
	}
	return false
}

func hasFoldPrefix(text []rune, at int, word string) bool {
	pattern := []rune(word)
	if at+len(pattern) > len(text) {
		return false
	}
	for i, want := range pattern {
		if !foldMatches(text[at+i], want) {
			return false
		}
	}
	return true
}

func hasExactPrefix(text []rune, at int, word string) bool {
	pattern := []rune(word)
	if at+len(pattern) > len(text) {
		return false
	}
	return equal(text[at:at+len(pattern)], pattern)
}

// isSmallWord is SMALL_WORDS.
func isSmallWord(word []rune) bool {
	for _, small := range smallWords {
		if len([]rune(small)) == len(word) && hasFoldPrefix(word, 0, small) {
			return true
		}
	}
	return false
}

// isBoundary is \b at position at.
func isBoundary(text []rune, at int) bool {
	left := at > 0 && isWord(text[at-1])
	right := at < len(text) && isWord(text[at])
	return left != right
}

// capitalizeSmallFirst is SMALL_FIRST.
func capitalizeSmallFirst(word []rune) []rune {
	start := 0
	for start < len(word) && isPunct(word[start]) {
		start++
	}
	for _, small := range smallWords {
		end := start + len([]rune(small))
		if hasFoldPrefix(word, start, small) && isBoundary(word, end) {
			return concat(word[:start], capitalize(word[start:end]), word[end:])
		}
	}
	return word
}

// capitalizeSmallLast is SMALL_LAST.
func capitalizeSmallLast(word []rune) []rune {
	for start := range word {
		if !isBoundary(word, start) {
			continue
		}
		for _, small := range smallWords {
			end := start + len([]rune(small))
			if !hasFoldPrefix(word, start, small) {
				continue
			}
			if end == len(word) || (end == len(word)-1 && isPunct(word[end])) {
				return concat(word[:start], capitalize(word[start:]))
			}
		}
	}
	return word
}

// capitalizeSubphrases is SUBPHRASE, which is case-sensitive.
func capitalizeSubphrases(line []rune) []rune {
	out := make([]rune, 0, len(line))
	for i := 0; i < len(line); {
		if i+1 < len(line) && line[i+1] == ' ' &&
			strings.ContainsRune(subphraseMarks, line[i]) {
			matched := false
			for _, small := range smallWords {
				if hasExactPrefix(line, i+2, small) {
					size := len([]rune(small))
					out = append(out, line[i], ' ')
					out = append(out, capitalize(line[i+2:i+2+size])...)
					i += 2 + size
					matched = true
					break
				}
			}
			if matched {
				continue
			}
		}
		out = append(out, line[i])
		i++
	}
	return out
}

func isASCIIUpper(r rune) bool { return r >= 'A' && r <= 'Z' }

// isInitials is UC_INITIALS: one or more of "X." or "X.Y".
func isInitials(word []rune) bool {
	if len(word) == 0 {
		return false
	}
	reachable := make([]bool, len(word)+1)
	reachable[0] = true
	for i := 0; i < len(word); i++ {
		if !reachable[i] || !isASCIIUpper(word[i]) {
			continue
		}
		if i+1 < len(word) && word[i+1] == '.' {
			reachable[i+2] = true
			if i+2 < len(word) && isASCIIUpper(word[i+2]) {
				reachable[i+3] = true
			}
		}
	}
	return reachable[len(word)]
}

func allWord(text []rune) bool {
	for _, r := range text {
		if !isWord(r) {
			return false
		}
	}
	return len(text) > 0
}

// isApostropheSecond is APOS_SECOND.
func isApostropheSecond(word []rune) bool {
	if len(word) < 3 || !strings.ContainsRune("dolDOL", word[0]) ||
		(word[1] != '\'' && word[1] != 0x2018) {
		return false
	}
	rest := word[2:]
	if allWord(rest) {
		return true
	}
	tail := func(r rune) bool { return r == '\'' || foldMatches(r, 's') }
	n := len(rest)
	return n >= 3 && tail(rest[n-1]) && tail(rest[n-2]) && allWord(rest[:n-2])
}

// isMacMc is MAC_MC.
func isMacMc(word []rune) bool {
	if len(word) < 4 || !isWord(word[2]) {
		return false
	}
	prefix := string(word[:2])
	return prefix == "Mc" || prefix == "mc" || prefix == "MC"
}

// isPersonalTitle is MR_MRS_MS_DR.
func isPersonalTitle(word []rune) bool {
	for _, title := range []string{"mr", "mrs", "ms", "dr"} {
		if len([]rune(title)) == len(word) && hasFoldPrefix(word, 0, title) {
			return true
		}
	}
	return false
}

// hasInlinePeriod is INLINE_PERIOD.
func hasInlinePeriod(word []rune) bool {
	for i := 1; i+1 < len(word); i++ {
		if word[i] == '.' && isWord(word[i-1]) && isWord(word[i+1]) {
			return true
		}
	}
	return false
}

// hasCapitalElsewhere is UC_ELSEWHERE, which is ASCII-only in the re fallback.
func hasCapitalElsewhere(word []rune) bool {
	i := 0
	for i < len(word) && isPunct(word[i]) {
		i++
	}
	for j := i; j < len(word); j++ {
		r := word[j]
		if !isASCIIUpper(r) && (r < 'a' || r > 'z') {
			return false
		}
		if j > i && isASCIIUpper(r) {
			return true
		}
	}
	return false
}

func isAllConsonants(word []rune) bool {
	for _, r := range word {
		if r == 0x17F || r == 0x212A {
			continue
		}
		if r >= 'A' && r <= 'Z' {
			r += 'a' - 'A'
		}
		if r < 'a' || r > 'z' || strings.ContainsRune("aeiouy", r) {
			return false
		}
	}
	return len(word) > 0
}

// capitalizeFirst is CAPFIRST. `_` is both punctuation and \w, and the lazy
// prefix stops at the first \w, so a leading `_` ends the search.
func capitalizeFirst(word []rune) []rune {
	for i, r := range word {
		if isWord(r) {
			return concat(upper(word[:i+1]), word[i+1:])
		}
		if !isPunct(r) {
			break
		}
	}
	return word
}

func splitOn(word []rune, sep rune) [][]rune {
	parts := [][]rune{}
	start := 0
	for i, r := range word {
		if r == sep {
			parts = append(parts, word[start:i])
			start = i + 1
		}
	}
	return append(parts, word[start:])
}

func titlecaseParts(word []rune, sep rune) []rune {
	var out []rune
	for i, part := range splitOn(word, sep) {
		if i > 0 {
			out = append(out, sep)
		}
		out = append(out, titlecase(part, false)...)
	}
	return out
}

func containsDoubleSlash(word []rune) bool {
	for i := 0; i+1 < len(word); i++ {
		if word[i] == '/' && word[i+1] == '/' {
			return true
		}
	}
	return false
}

func containsRune(word []rune, want rune) bool {
	for _, r := range word {
		if r == want {
			return true
		}
	}
	return false
}

// titlecaseWord applies the word rules, in the order of the Python loop.
func titlecaseWord(word []rune, allCaps bool) []rune {
	if allCaps && isInitials(word) {
		return word
	}
	if isApostropheSecond(word) {
		first := upperRune(word[0])
		if !strings.ContainsRune("oO", word[0]) {
			first = lowerAt(word, 0)
		}
		return concat(first, word[1:2], upperRune(word[2]), word[3:])
	}
	if isMacMc(word) {
		return concat([]rune("Mc"), titlecase(word[2:], true))
	}
	if isPersonalTitle(word) {
		return concat(upperRune(word[0]), word[1:])
	}
	if hasInlinePeriod(word) || (!allCaps && hasCapitalElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return lower(word)
	}
	if containsRune(word, '/') && !containsDoubleSlash(word) {
		return titlecaseParts(word, '/')
	}
	if containsRune(word, '-') {
		return titlecaseParts(word, '-')
	}
	if allCaps {
		word = lower(word)
	}
	if isAllConsonants(word) && len(word) > 2 {
		return upper(word)
	}
	return capitalizeFirst(word)
}

func titlecaseLine(line []rune, smallFirstLast bool) []rune {
	allCaps := equal(upper(line), line)

	var spaces []rune
	words := [][]rune{}
	start := 0
	for i, r := range line {
		if isSpace(r) {
			words = append(words, line[start:i])
			spaces = append(spaces, r)
			start = i + 1
		}
	}
	words = append(words, line[start:])

	cased := make([][]rune, len(words))
	for i, word := range words {
		cased[i] = titlecaseWord(word, allCaps)
	}
	if smallFirstLast {
		cased[0] = capitalizeSmallFirst(cased[0])
		last := len(cased) - 1
		cased[last] = capitalizeSmallLast(cased[last])
	}

	var joined []rune
	for i, word := range cased {
		joined = append(joined, word...)
		if i < len(spaces) {
			joined = append(joined, spaces[i])
		}
	}
	return capitalizeSubphrases(joined)
}

// splitLines is regex.split('[\r\n]+', text).
func splitLines(text []rune) [][]rune {
	lines := [][]rune{}
	start := 0
	for i := 0; i < len(text); {
		if text[i] != '\r' && text[i] != '\n' {
			i++
			continue
		}
		lines = append(lines, text[start:i])
		for i < len(text) && (text[i] == '\r' || text[i] == '\n') {
			i++
		}
		start = i
	}
	return append(lines, text[start:])
}

func titlecase(text []rune, smallFirstLast bool) []rune {
	var out []rune
	for i, line := range splitLines(text) {
		if i > 0 {
			out = append(out, '\n')
		}
		out = append(out, titlecaseLine(line, smallFirstLast)...)
	}
	return out
}

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Stderr.WriteString(err.Error() + "\n")
		os.Exit(1)
	}
	if len(data) == 0 {
		return
	}
	lines := bytes.Split(data, []byte("\n"))
	if len(lines[len(lines)-1]) == 0 {
		lines = lines[:len(lines)-1]
	}
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for _, line := range lines {
		out.WriteString(string(titlecase([]rune(string(line)), true)))
		out.WriteByte('\n')
	}
}
GO_SOURCE

cat > tables.go <<'GO_SOURCE'
// Differences between Go 1.23 (Unicode 15) and Python 3.11 (Unicode 14),
// generated by comparing the two on every code point.

package main

var upperSpecial = map[rune]string{
	0xDF:   "\U00000053\U00000053",
	0x149:  "\U000002BC\U0000004E",
	0x1F0:  "\U0000004A\U0000030C",
	0x390:  "\U00000399\U00000308\U00000301",
	0x3B0:  "\U000003A5\U00000308\U00000301",
	0x587:  "\U00000535\U00000552",
	0x1E96: "\U00000048\U00000331",
	0x1E97: "\U00000054\U00000308",
	0x1E98: "\U00000057\U0000030A",
	0x1E99: "\U00000059\U0000030A",
	0x1E9A: "\U00000041\U000002BE",
	0x1F50: "\U000003A5\U00000313",
	0x1F52: "\U000003A5\U00000313\U00000300",
	0x1F54: "\U000003A5\U00000313\U00000301",
	0x1F56: "\U000003A5\U00000313\U00000342",
	0x1F80: "\U00001F08\U00000399",
	0x1F81: "\U00001F09\U00000399",
	0x1F82: "\U00001F0A\U00000399",
	0x1F83: "\U00001F0B\U00000399",
	0x1F84: "\U00001F0C\U00000399",
	0x1F85: "\U00001F0D\U00000399",
	0x1F86: "\U00001F0E\U00000399",
	0x1F87: "\U00001F0F\U00000399",
	0x1F88: "\U00001F08\U00000399",
	0x1F89: "\U00001F09\U00000399",
	0x1F8A: "\U00001F0A\U00000399",
	0x1F8B: "\U00001F0B\U00000399",
	0x1F8C: "\U00001F0C\U00000399",
	0x1F8D: "\U00001F0D\U00000399",
	0x1F8E: "\U00001F0E\U00000399",
	0x1F8F: "\U00001F0F\U00000399",
	0x1F90: "\U00001F28\U00000399",
	0x1F91: "\U00001F29\U00000399",
	0x1F92: "\U00001F2A\U00000399",
	0x1F93: "\U00001F2B\U00000399",
	0x1F94: "\U00001F2C\U00000399",
	0x1F95: "\U00001F2D\U00000399",
	0x1F96: "\U00001F2E\U00000399",
	0x1F97: "\U00001F2F\U00000399",
	0x1F98: "\U00001F28\U00000399",
	0x1F99: "\U00001F29\U00000399",
	0x1F9A: "\U00001F2A\U00000399",
	0x1F9B: "\U00001F2B\U00000399",
	0x1F9C: "\U00001F2C\U00000399",
	0x1F9D: "\U00001F2D\U00000399",
	0x1F9E: "\U00001F2E\U00000399",
	0x1F9F: "\U00001F2F\U00000399",
	0x1FA0: "\U00001F68\U00000399",
	0x1FA1: "\U00001F69\U00000399",
	0x1FA2: "\U00001F6A\U00000399",
	0x1FA3: "\U00001F6B\U00000399",
	0x1FA4: "\U00001F6C\U00000399",
	0x1FA5: "\U00001F6D\U00000399",
	0x1FA6: "\U00001F6E\U00000399",
	0x1FA7: "\U00001F6F\U00000399",
	0x1FA8: "\U00001F68\U00000399",
	0x1FA9: "\U00001F69\U00000399",
	0x1FAA: "\U00001F6A\U00000399",
	0x1FAB: "\U00001F6B\U00000399",
	0x1FAC: "\U00001F6C\U00000399",
	0x1FAD: "\U00001F6D\U00000399",
	0x1FAE: "\U00001F6E\U00000399",
	0x1FAF: "\U00001F6F\U00000399",
	0x1FB2: "\U00001FBA\U00000399",
	0x1FB3: "\U00000391\U00000399",
	0x1FB4: "\U00000386\U00000399",
	0x1FB6: "\U00000391\U00000342",
	0x1FB7: "\U00000391\U00000342\U00000399",
	0x1FBC: "\U00000391\U00000399",
	0x1FC2: "\U00001FCA\U00000399",
	0x1FC3: "\U00000397\U00000399",
	0x1FC4: "\U00000389\U00000399",
	0x1FC6: "\U00000397\U00000342",
	0x1FC7: "\U00000397\U00000342\U00000399",
	0x1FCC: "\U00000397\U00000399",
	0x1FD2: "\U00000399\U00000308\U00000300",
	0x1FD3: "\U00000399\U00000308\U00000301",
	0x1FD6: "\U00000399\U00000342",
	0x1FD7: "\U00000399\U00000308\U00000342",
	0x1FE2: "\U000003A5\U00000308\U00000300",
	0x1FE3: "\U000003A5\U00000308\U00000301",
	0x1FE4: "\U000003A1\U00000313",
	0x1FE6: "\U000003A5\U00000342",
	0x1FE7: "\U000003A5\U00000308\U00000342",
	0x1FF2: "\U00001FFA\U00000399",
	0x1FF3: "\U000003A9\U00000399",
	0x1FF4: "\U0000038F\U00000399",
	0x1FF6: "\U000003A9\U00000342",
	0x1FF7: "\U000003A9\U00000342\U00000399",
	0x1FFC: "\U000003A9\U00000399",
	0xFB00: "\U00000046\U00000046",
	0xFB01: "\U00000046\U00000049",
	0xFB02: "\U00000046\U0000004C",
	0xFB03: "\U00000046\U00000046\U00000049",
	0xFB04: "\U00000046\U00000046\U0000004C",
	0xFB05: "\U00000053\U00000054",
	0xFB06: "\U00000053\U00000054",
	0xFB13: "\U00000544\U00000546",
	0xFB14: "\U00000544\U00000535",
	0xFB15: "\U00000544\U0000053B",
	0xFB16: "\U0000054E\U00000546",
	0xFB17: "\U00000544\U0000053D",
}

var lowerSpecial = map[rune]string{
	0x130: "\U00000069\U00000307",
}

var titleSpecial = map[rune]string{
	0xDF:   "\U00000053\U00000073",
	0x149:  "\U000002BC\U0000004E",
	0x1F0:  "\U0000004A\U0000030C",
	0x390:  "\U00000399\U00000308\U00000301",
	0x3B0:  "\U000003A5\U00000308\U00000301",
	0x587:  "\U00000535\U00000582",
	0x1E96: "\U00000048\U00000331",
	0x1E97: "\U00000054\U00000308",
	0x1E98: "\U00000057\U0000030A",
	0x1E99: "\U00000059\U0000030A",
	0x1E9A: "\U00000041\U000002BE",
	0x1F50: "\U000003A5\U00000313",
	0x1F52: "\U000003A5\U00000313\U00000300",
	0x1F54: "\U000003A5\U00000313\U00000301",
	0x1F56: "\U000003A5\U00000313\U00000342",
	0x1FB2: "\U00001FBA\U00000345",
	0x1FB4: "\U00000386\U00000345",
	0x1FB6: "\U00000391\U00000342",
	0x1FB7: "\U00000391\U00000342\U00000345",
	0x1FC2: "\U00001FCA\U00000345",
	0x1FC4: "\U00000389\U00000345",
	0x1FC6: "\U00000397\U00000342",
	0x1FC7: "\U00000397\U00000342\U00000345",
	0x1FD2: "\U00000399\U00000308\U00000300",
	0x1FD3: "\U00000399\U00000308\U00000301",
	0x1FD6: "\U00000399\U00000342",
	0x1FD7: "\U00000399\U00000308\U00000342",
	0x1FE2: "\U000003A5\U00000308\U00000300",
	0x1FE3: "\U000003A5\U00000308\U00000301",
	0x1FE4: "\U000003A1\U00000313",
	0x1FE6: "\U000003A5\U00000342",
	0x1FE7: "\U000003A5\U00000308\U00000342",
	0x1FF2: "\U00001FFA\U00000345",
	0x1FF4: "\U0000038F\U00000345",
	0x1FF6: "\U000003A9\U00000342",
	0x1FF7: "\U000003A9\U00000342\U00000345",
	0xFB00: "\U00000046\U00000066",
	0xFB01: "\U00000046\U00000069",
	0xFB02: "\U00000046\U0000006C",
	0xFB03: "\U00000046\U00000066\U00000069",
	0xFB04: "\U00000046\U00000066\U0000006C",
	0xFB05: "\U00000053\U00000074",
	0xFB06: "\U00000053\U00000074",
	0xFB13: "\U00000544\U00000576",
	0xFB14: "\U00000544\U00000565",
	0xFB15: "\U00000544\U0000056B",
	0xFB16: "\U0000054E\U00000576",
	0xFB17: "\U00000544\U0000056D",
}

var wordFlips = [][2]rune{
	{0x1123F, 0x11240},
	{0x11F02, 0x11F02},
	{0x11F04, 0x11F10},
	{0x11F12, 0x11F33},
	{0x11F50, 0x11F59},
	{0x1342F, 0x1342F},
	{0x13441, 0x13446},
	{0x1B132, 0x1B132},
	{0x1B155, 0x1B155},
	{0x1D2C0, 0x1D2D3},
	{0x1DF25, 0x1DF2A},
	{0x1E030, 0x1E06D},
	{0x1E4D0, 0x1E4EB},
	{0x1E4F0, 0x1E4F9},
	{0x2B739, 0x2B739},
	{0x31350, 0x323AF},
}

var casedFlips = [][2]rune{
	{0x1DF25, 0x1DF2A},
	{0x1E030, 0x1E06D},
}

var ignorableFlips = [][2]rune{
	{0xECE, 0xECE},
	{0x10EFD, 0x10EFF},
	{0x11241, 0x11241},
	{0x11F00, 0x11F01},
	{0x11F36, 0x11F3A},
	{0x11F40, 0x11F40},
	{0x11F42, 0x11F42},
	{0x13439, 0x13440},
	{0x13447, 0x13455},
	{0x1E030, 0x1E06D},
	{0x1E08F, 0x1E08F},
	{0x1E4EB, 0x1E4EF},
}
GO_SOURCE

find . -type f -name '*.py' -delete
# An empty titlecase/ folder would block `go build ./...` from writing its binary.
find . -type d -empty -delete

go build -o /dev/null ./...
