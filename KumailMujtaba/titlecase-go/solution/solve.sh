#!/bin/bash
# Reference solution: a standard-library Go port of titlecase, with no regexp.
# tables.go lists where Python 3.12 + regex 2026.9.29 differ from Go's unicode
# package, found by comparing every code point.
set -euo pipefail

cd /workspace/repo

# Not "titlecase": go build ./... would write a binary of that name, and the
# repo has a titlecase/ directory until the cleanup at the end.
cat > go.mod <<'SOLVE_EOF'
module example.com/titlecasego

go 1.23
SOLVE_EOF

cat > main.go <<'SOLVE_EOF'
// Go port of the Python titlecase library, version 2.4.1.
//
// Reads standard input, splits it on \n, drops one trailing \r from each line,
// and writes titlecase(line) followed by \n. Every Python regular expression is
// replaced with a hand-written matcher, named after the pattern it stands for.
package main

import (
	"bufio"
	"io"
	"os"
	"sort"
	"strings"
	"unicode"
)

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	if len(data) == 0 {
		return
	}
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	// A final \n ends the last line instead of starting another one.
	text := strings.TrimSuffix(string(data), "\n")
	for _, line := range strings.Split(text, "\n") {
		line = strings.TrimSuffix(line, "\r")
		out.WriteString(string(titlecase([]rune(line), true)))
		out.WriteByte('\n')
	}
}

// smallWords keeps the order of the Python alternation, which decides the match.
var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
	"on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

const (
	punctuation   = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
	subphraseEnds = ":.;?!-–‒—―"
	consonants    = "bcdfghjklmnpqrstvwxz"
)

func titlecase(text []rune, smallFirstLast bool) []rune {
	var result []rune
	for i, line := range splitLines(text) {
		if i > 0 {
			result = append(result, '\n')
		}
		result = append(result, titlecaseLine(line, smallFirstLast)...)
	}
	return result
}

// splitLines is regex.split('[\r\n]+', text).
func splitLines(text []rune) [][]rune {
	var lines [][]rune
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

// splitSpaces is regex.split(r'(\s)', line), returned as words and separators.
func splitSpaces(line []rune) (words [][]rune, spaces []rune) {
	start := 0
	for i, r := range line {
		if isSpace(r) {
			words = append(words, line[start:i])
			spaces = append(spaces, r)
			start = i + 1
		}
	}
	return append(words, line[start:]), spaces
}

func titlecaseLine(line []rune, smallFirstLast bool) []rune {
	allCaps := equal(toUpper(line), line)
	words, spaces := splitSpaces(line)
	titled := make([][]rune, len(words))
	for i, word := range words {
		titled[i] = titlecaseWord(word, allCaps)
	}
	if smallFirstLast {
		titled[0] = capitalizeSmallFirst(titled[0])
		last := len(titled) - 1
		titled[last] = capitalizeSmallLast(titled[last])
	}
	var result []rune
	for i, word := range titled {
		result = append(result, word...)
		if i < len(spaces) {
			result = append(result, spaces[i])
		}
	}
	return capitalizeSubphrases(result)
}

func titlecaseWord(word []rune, allCaps bool) []rune {
	if allCaps && isInitials(word) {
		return word
	}
	if isApostropheName(word) {
		result := toLower(word[:1])
		if strings.ContainsRune("aeiouAEIOU", word[0]) {
			result = toUpper(word[:1])
		}
		result = append(result, word[1])
		result = append(result, toUpper(word[2:3])...)
		return append(result, word[3:]...)
	}
	if isMacName(word) {
		return append([]rune("Mc"), titlecase(word[2:], true)...)
	}
	if isHonorific(word) {
		return append(toUpper(word[:1]), word[1:]...)
	}
	if hasInlinePeriod(word) || (!allCaps && hasCapitalElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return toLower(word)
	}
	if contains(word, '/') && !containsDoubleSlash(word) {
		return titlecaseParts(word, '/')
	}
	if contains(word, '-') {
		return titlecaseParts(word, '-')
	}
	if allCaps {
		word = toLower(word)
	}
	if len(word) > 2 && isAllConsonants(word) {
		return toUpper(word)
	}
	return capitalizeFirstLetter(word)
}

func titlecaseParts(word []rune, separator rune) []rune {
	var result []rune
	start := 0
	for i := 0; i <= len(word); i++ {
		if i == len(word) || word[i] == separator {
			result = append(result, titlecase(word[start:i], false)...)
			if i < len(word) {
				result = append(result, separator)
			}
			start = i + 1
		}
	}
	return result
}

// isInitials is UC_INITIALS: ^(?:X\.|X\.X)+$ where X is an uppercase letter.
// The two branches overlap, so this tracks every position they can reach.
func isInitials(word []rune) bool {
	n := len(word)
	reachable := make([]bool, n+1)
	reachable[0] = true
	for i := 0; i+1 < n; i++ {
		if reachable[i] && isUpperLetter(word[i]) && word[i+1] == '.' {
			reachable[i+2] = true
			if i+2 < n && isUpperLetter(word[i+2]) {
				reachable[i+3] = true
			}
		}
	}
	return n > 0 && reachable[n]
}

// isApostropheName is APOS_SECOND, case-insensitive:
// ^[dol]['‘]LETTER+(?:['s]{2})?$
func isApostropheName(word []rune) bool {
	n := len(word)
	if n < 3 || !strings.ContainsRune("dol", fold(word[0])) {
		return false
	}
	if word[1] != '\'' && word[1] != '‘' {
		return false
	}
	end := 2
	for end < n && isLetterIgnoreCase(word[end]) {
		end++
	}
	if end > 2 && end == n {
		return true
	}
	// The letters can give back up to two characters to the optional suffix.
	return n-2 > 2 && end >= n-2 && isSuffixChar(word[n-2]) && isSuffixChar(word[n-1])
}

func isSuffixChar(r rune) bool {
	return r == '\'' || fold(r) == 's'
}

// isMacName is MAC_MC: ^([Mm]c|MC)(\w.+)
func isMacName(word []rune) bool {
	if len(word) < 4 || !isWordChar(word[2]) {
		return false
	}
	prefix := string(word[:2])
	return prefix == "Mc" || prefix == "mc" || prefix == "MC"
}

// isHonorific is MR_MRS_MS_DR, case-insensitive: mr, mrs, ms or dr.
func isHonorific(word []rune) bool {
	for _, honorific := range []string{"mr", "mrs", "ms", "dr"} {
		if len(word) == len(honorific) && hasPrefixFold(word, 0, honorific) {
			return true
		}
	}
	return false
}

// hasInlinePeriod is INLINE_PERIOD, case-insensitive: LETTER.LETTER anywhere.
func hasInlinePeriod(word []rune) bool {
	for i := 1; i+1 < len(word); i++ {
		if word[i] == '.' && isLetterIgnoreCase(word[i-1]) && isLetterIgnoreCase(word[i+1]) {
			return true
		}
	}
	return false
}

// hasCapitalElsewhere is UC_ELSEWHERE: leading punctuation, then a run of
// letters in which some letter after the first is uppercase.
func hasCapitalElsewhere(word []rune) bool {
	start := punctuationPrefix(word)
	for i := start; i < len(word) && isLetter(word[i]); i++ {
		if i > start && isUpperLetter(word[i]) {
			return true
		}
	}
	return false
}

func isSmallWord(word []rune) bool {
	for _, small := range smallWords {
		if len(word) == len(small) && hasPrefixFold(word, 0, small) {
			return true
		}
	}
	return false
}

func isAllConsonants(word []rune) bool {
	for _, r := range word {
		if !strings.ContainsRune(consonants, fold(r)) {
			return false
		}
	}
	return true
}

// capitalizeFirstLetter is CAPFIRST: uppercase the first letter, if only
// punctuation comes before it.
func capitalizeFirstLetter(word []rune) []rune {
	start := punctuationPrefix(word)
	if start == len(word) || !isLetter(word[start]) {
		return word
	}
	result := append([]rune{}, word[:start]...)
	result = append(result, toUpper(word[start:start+1])...)
	return append(result, word[start+1:]...)
}

// capitalizeSmallFirst is SMALL_FIRST, case-insensitive:
// ^(PUNCT*)(SMALL)\b, tried in alternation order.
func capitalizeSmallFirst(word []rune) []rune {
	start := punctuationPrefix(word)
	for _, small := range smallWords {
		end := start + len(small)
		if hasPrefixFold(word, start, small) && isWordBoundary(word, end) {
			result := append([]rune{}, word[:start]...)
			result = append(result, capitalize(word[start:end])...)
			return append(result, word[end:]...)
		}
	}
	return word
}

// capitalizeSmallLast is SMALL_LAST, case-insensitive: \b(SMALL)PUNCT?$
// The match runs to the end of the word, so only its start matters.
func capitalizeSmallLast(word []rune) []rune {
	n := len(word)
	for start := 0; start < n; start++ {
		if !isWordBoundary(word, start) {
			continue
		}
		for _, small := range smallWords {
			end := start + len(small)
			if !hasPrefixFold(word, start, small) {
				continue
			}
			if end == n || (end == n-1 && isPunctuation(word[end])) {
				return append(append([]rune{}, word[:start]...), capitalize(word[start:])...)
			}
		}
	}
	return word
}

// capitalizeSubphrases is SUBPHRASE, case-sensitive, with no boundary after the
// small word: ([:.;?!-–‒—―] )(SMALL). A matching prefix of a longer word counts.
func capitalizeSubphrases(line []rune) []rune {
	var result []rune
	for i := 0; i < len(line); {
		small := ""
		if strings.ContainsRune(subphraseEnds, line[i]) && i+1 < len(line) && line[i+1] == ' ' {
			small = smallPrefix(line, i+2)
		}
		if small == "" {
			result = append(result, line[i])
			i++
			continue
		}
		result = append(result, line[i], ' ')
		result = append(result, capitalize([]rune(small))...)
		i += 2 + len(small)
	}
	return result
}

func smallPrefix(line []rune, start int) string {
	for _, small := range smallWords {
		end := start + len(small)
		if end <= len(line) && string(line[start:end]) == small {
			return small
		}
	}
	return ""
}

func hasPrefixFold(word []rune, start int, prefix string) bool {
	if start+len(prefix) > len(word) {
		return false
	}
	for i := 0; i < len(prefix); i++ {
		if fold(word[start+i]) != rune(prefix[i]) {
			return false
		}
	}
	return true
}

// fold maps a character to the ASCII letter it equals under regex.I.
func fold(r rune) rune {
	if 'A' <= r && r <= 'Z' {
		return r + ('a' - 'A')
	}
	if letter, ok := foldToASCII[r]; ok {
		return letter
	}
	return r
}

// isWordBoundary is \b at position i.
func isWordBoundary(word []rune, i int) bool {
	before := i > 0 && isWordChar(word[i-1])
	after := i < len(word) && isWordChar(word[i])
	return before != after
}

func punctuationPrefix(word []rune) int {
	i := 0
	for i < len(word) && isPunctuation(word[i]) {
		i++
	}
	return i
}

func isPunctuation(r rune) bool { return strings.ContainsRune(punctuation, r) }

func contains(word []rune, r rune) bool {
	for _, c := range word {
		if c == r {
			return true
		}
	}
	return false
}

func containsDoubleSlash(word []rune) bool {
	for i := 0; i+1 < len(word); i++ {
		if word[i] == '/' && word[i+1] == '/' {
			return true
		}
	}
	return false
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

// toUpper is str.upper(), including mappings to several characters (ß to SS).
func toUpper(s []rune) []rune {
	result := make([]rune, 0, len(s))
	for _, r := range s {
		if mapped, ok := upperExceptions[r]; ok {
			result = append(result, []rune(mapped)...)
		} else {
			result = append(result, unicode.ToUpper(r))
		}
	}
	return result
}

// toLower is str.lower().
func toLower(s []rune) []rune {
	result := make([]rune, 0, len(s))
	for i := range s {
		result = appendLower(result, s, i)
	}
	return result
}

// capitalize is str.capitalize(): titlecase the first character, lower the rest.
func capitalize(s []rune) []rune {
	if len(s) == 0 {
		return s
	}
	var result []rune
	if mapped, ok := titleExceptions[s[0]]; ok {
		result = []rune(mapped)
	} else {
		result = []rune{unicode.ToTitle(s[0])}
	}
	for i := 1; i < len(s); i++ {
		result = appendLower(result, s, i)
	}
	return result
}

func appendLower(result, s []rune, i int) []rune {
	r := s[i]
	if r == 'Σ' {
		if isFinalSigma(s, i) {
			return append(result, 'ς')
		}
		return append(result, 'σ')
	}
	if mapped, ok := lowerExceptions[r]; ok {
		return append(result, []rune(mapped)...)
	}
	return append(result, unicode.ToLower(r))
}

// isFinalSigma is CPython's handle_capital_sigma: looks past case-ignorable
// characters on both sides, needing a cased character before and none after.
func isFinalSigma(s []rune, i int) bool {
	before := i - 1
	for before >= 0 && isCaseIgnorable(s[before]) {
		before--
	}
	if before < 0 || !isCased(s[before]) {
		return false
	}
	after := i + 1
	for after < len(s) && isCaseIgnorable(s[after]) {
		after++
	}
	return after == len(s) || !isCased(s[after])
}

// ranges is a sorted list of inclusive pairs: lo, hi, lo, hi...
type ranges []rune

func (t ranges) has(r rune) bool {
	i := sort.Search(len(t)/2, func(i int) bool { return t[2*i+1] >= r })
	return i < len(t)/2 && t[2*i] <= r
}

func isLetter(r rune) bool           { return baseLetter(r) != letterDiff.has(r) }
func isLetterIgnoreCase(r rune) bool { return baseLetter(r) != letterIgnoreCaseDiff.has(r) }
func isUpperLetter(r rune) bool      { return baseUpperLetter(r) != upperLetterDiff.has(r) }
func isSpace(r rune) bool            { return baseSpace(r) != spaceDiff.has(r) }
func isWordChar(r rune) bool         { return baseWord(r) != wordDiff.has(r) }
func isCased(r rune) bool            { return baseCased(r) != casedDiff.has(r) }
func isCaseIgnorable(r rune) bool    { return baseCaseIgnorable(r) != caseIgnorableDiff.has(r) }
SOLVE_EOF

cat > base.go <<'SOLVE_EOF'
package main

import "unicode"

// Starting points for each character property. tables.go lists the characters
// where the reference implementation disagrees with these.

func baseLetter(r rune) bool      { return unicode.IsLetter(r) }
func baseUpperLetter(r rune) bool { return unicode.Is(unicode.Lu, r) }
func baseSpace(r rune) bool       { return unicode.IsSpace(r) }

func baseWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsMark(r) || unicode.In(r, unicode.Nd, unicode.Pc)
}

func baseCased(r rune) bool {
	return unicode.In(r, unicode.Lu, unicode.Ll, unicode.Lt, unicode.Other_Lowercase, unicode.Other_Uppercase)
}

func baseCaseIgnorable(r rune) bool {
	return unicode.In(r, unicode.Mn, unicode.Me, unicode.Cf, unicode.Lm, unicode.Sk)
}
SOLVE_EOF

cat > tables.go <<'SOLVE_EOF'
package main

// Generated by comparing every code point in Python 3.12 and regex 2026.9.29
// with Go's unicode package. Only the differences are listed.

var letterDiff = ranges{
	0x558, 0x558, 0x58B, 0x58C, 0x88F, 0x88F, 0xC5C, 0xC5C, 0xCDC, 0xCDC, 0x1C89, 0x1C8A,
	0x208F, 0x208F, 0x209D, 0x209F, 0xA7CB, 0xA7CF, 0xA7D2, 0xA7D2, 0xA7D4, 0xA7D4, 0xA7DA, 0xA7DD,
	0xA7E2, 0xA7E2, 0xA7F1, 0xA7F1, 0xAB6C, 0xAB6D, 0x105C0, 0x105F3, 0x107BB, 0x107BF, 0x10940, 0x10959,
	0x10D4A, 0x10D65, 0x10D6F, 0x10D85, 0x10EC2, 0x10EC7, 0x10ED9, 0x10EEE, 0x11380, 0x11389, 0x1138B, 0x1138B,
	0x1138E, 0x1138E, 0x11390, 0x113B5, 0x113B7, 0x113B7, 0x113D1, 0x113D1, 0x113D3, 0x113D3, 0x11B0A, 0x11B0A,
	0x11BC0, 0x11BE0, 0x11DB0, 0x11DDB, 0x11DF1, 0x11DF1, 0x13460, 0x143FA, 0x16100, 0x1611D, 0x16D40, 0x16D6C,
	0x16EA0, 0x16EB8, 0x16EBB, 0x16ED3, 0x16FF2, 0x16FF3, 0x187F8, 0x187FF, 0x18CD6, 0x18CDA, 0x18CFF, 0x18CFF,
	0x18D09, 0x18D20, 0x18D80, 0x18DF2, 0x18E00, 0x19191, 0x191A0, 0x191D2, 0x1B123, 0x1B128, 0x1B168, 0x1B168,
	0x1D6A6, 0x1D6A6, 0x1DF1F, 0x1DF24, 0x1DF2B, 0x1DF81, 0x1DF90, 0x1DF96, 0x1DFCD, 0x1DFFF, 0x1E5D0, 0x1E5ED,
	0x1E5F0, 0x1E5F0, 0x1E6C0, 0x1E6DE, 0x1E6E0, 0x1E6E2, 0x1E6E4, 0x1E6E5, 0x1E6E7, 0x1E6ED, 0x1E6F0, 0x1E6F4,
	0x1E6FE, 0x1E6FF, 0x2B73A, 0x2B73F, 0x2B81E, 0x2B81E, 0x2CEA2, 0x2CEAD, 0x2EBF0, 0x2EE5D, 0x323B0, 0x33479,
	0x3D000, 0x3FC3F,
}

var letterIgnoreCaseDiff = ranges{
	0x558, 0x558, 0x58B, 0x58C, 0x88F, 0x88F, 0xC5C, 0xC5C, 0xCDC, 0xCDC, 0x1C89, 0x1C8A,
	0x208F, 0x208F, 0x209D, 0x209F, 0xA7CB, 0xA7CF, 0xA7D2, 0xA7D2, 0xA7D4, 0xA7D4, 0xA7DA, 0xA7DD,
	0xA7E2, 0xA7E2, 0xA7F1, 0xA7F1, 0xAB6C, 0xAB6D, 0x105C0, 0x105F3, 0x107BB, 0x107BF, 0x10940, 0x10959,
	0x10D4A, 0x10D65, 0x10D6F, 0x10D85, 0x10EC2, 0x10EC7, 0x10ED9, 0x10EEE, 0x11380, 0x11389, 0x1138B, 0x1138B,
	0x1138E, 0x1138E, 0x11390, 0x113B5, 0x113B7, 0x113B7, 0x113D1, 0x113D1, 0x113D3, 0x113D3, 0x11B0A, 0x11B0A,
	0x11BC0, 0x11BE0, 0x11DB0, 0x11DDB, 0x11DF1, 0x11DF1, 0x13460, 0x143FA, 0x16100, 0x1611D, 0x16D40, 0x16D6C,
	0x16EA0, 0x16EB8, 0x16EBB, 0x16ED3, 0x16FF2, 0x16FF3, 0x187F8, 0x187FF, 0x18CD6, 0x18CDA, 0x18CFF, 0x18CFF,
	0x18D09, 0x18D20, 0x18D80, 0x18DF2, 0x18E00, 0x19191, 0x191A0, 0x191D2, 0x1B123, 0x1B128, 0x1B168, 0x1B168,
	0x1D6A6, 0x1D6A6, 0x1DF1F, 0x1DF24, 0x1DF2B, 0x1DF81, 0x1DF90, 0x1DF96, 0x1DFCD, 0x1DFFF, 0x1E5D0, 0x1E5ED,
	0x1E5F0, 0x1E5F0, 0x1E6C0, 0x1E6DE, 0x1E6E0, 0x1E6E2, 0x1E6E4, 0x1E6E5, 0x1E6E7, 0x1E6ED, 0x1E6F0, 0x1E6F4,
	0x1E6FE, 0x1E6FF, 0x2B73A, 0x2B73F, 0x2B81E, 0x2B81E, 0x2CEA2, 0x2CEAD, 0x2EBF0, 0x2EE5D, 0x323B0, 0x33479,
	0x3D000, 0x3FC3F,
}

var upperLetterDiff = ranges{
	0x1C89, 0x1C89, 0xA7CB, 0xA7CC, 0xA7CE, 0xA7CE, 0xA7D2, 0xA7D2, 0xA7D4, 0xA7D4, 0xA7DA, 0xA7DA,
	0xA7DC, 0xA7DD, 0xA7E2, 0xA7E2, 0xAB6C, 0xAB6D, 0x10D50, 0x10D65, 0x16EA0, 0x16EB8, 0x1DF40, 0x1DF40,
	0x1DF48, 0x1DF48, 0x1DF4A, 0x1DF4A, 0x1DF4D, 0x1DF4D, 0x1DF51, 0x1DF51, 0x1DF68, 0x1DF68, 0x1DF6A, 0x1DF6A,
	0x1DF6C, 0x1DF6C, 0x1DF6E, 0x1DF6E, 0x1DF72, 0x1DF72, 0x1DF74, 0x1DF74, 0x1DF76, 0x1DF76, 0x1DF78, 0x1DF78,
	0x1DF7A, 0x1DF7A, 0x1DF7C, 0x1DF7C, 0x1DF7E, 0x1DF7E,
}

var spaceDiff = ranges{}

var wordDiff = ranges{
	0x558, 0x558, 0x58B, 0x58C, 0x5C8, 0x5C9, 0x88F, 0x88F, 0x897, 0x897, 0xB53, 0xB54,
	0xC5C, 0xC5C, 0xCDC, 0xCDC, 0x16EE, 0x16F0, 0x1ACF, 0x1AF0, 0x1C89, 0x1C8A, 0x200C, 0x200D,
	0x208F, 0x208F, 0x209D, 0x209F, 0x2160, 0x2182, 0x2185, 0x2188, 0x24B6, 0x24E9, 0x3007, 0x3007,
	0x3021, 0x3029, 0x3038, 0x303A, 0xA6E6, 0xA6EF, 0xA7CB, 0xA7CF, 0xA7D2, 0xA7D2, 0xA7D4, 0xA7D4,
	0xA7DA, 0xA7DD, 0xA7E2, 0xA7E2, 0xA7F1, 0xA7F1, 0xAB6C, 0xAB6D, 0x10140, 0x10174, 0x10341, 0x10341,
	0x1034A, 0x1034A, 0x103D1, 0x103D5, 0x105C0, 0x105F3, 0x107BB, 0x107BF, 0x10940, 0x10959, 0x10D40, 0x10D65,
	0x10D69, 0x10D6D, 0x10D6F, 0x10D85, 0x10EC2, 0x10EC7, 0x10ECB, 0x10ECF, 0x10ED9, 0x10EEE, 0x10EF0, 0x10EFC,
	0x11380, 0x11389, 0x1138B, 0x1138B, 0x1138E, 0x1138E, 0x11390, 0x113B5, 0x113B7, 0x113C0, 0x113C2, 0x113C2,
	0x113C5, 0x113C5, 0x113C7, 0x113CA, 0x113CC, 0x113D3, 0x113E1, 0x113E2, 0x116D0, 0x116E3, 0x11B0A, 0x11B0A,
	0x11B60, 0x11B67, 0x11BC0, 0x11BE0, 0x11BF0, 0x11BF9, 0x11DB0, 0x11DDB, 0x11DE0, 0x11DE9, 0x11DF0, 0x11DF1,
	0x11F5A, 0x11F5A, 0x12400, 0x1246F, 0x12475, 0x1247F, 0x12550, 0x12686, 0x13460, 0x143FA, 0x16100, 0x16139,
	0x16D40, 0x16D6C, 0x16D70, 0x16D79, 0x16EA0, 0x16EB8, 0x16EBB, 0x16ED3, 0x16FF2, 0x16FF6, 0x187F8, 0x187FF,
	0x18CD6, 0x18CDA, 0x18CFF, 0x18CFF, 0x18D09, 0x18D20, 0x18D80, 0x18DF2, 0x18E00, 0x19191, 0x191A0, 0x191D2,
	0x1B123, 0x1B128, 0x1B168, 0x1B168, 0x1CCF0, 0x1CCF9, 0x1D127, 0x1D128, 0x1D250, 0x1D252, 0x1D25B, 0x1D25C,
	0x1D25F, 0x1D25F, 0x1D280, 0x1D281, 0x1D6A6, 0x1D6A6, 0x1DF1F, 0x1DF24, 0x1DF2B, 0x1DF81, 0x1DF90, 0x1DF96,
	0x1DFCD, 0x1DFFF, 0x1E5D0, 0x1E5FA, 0x1E6C0, 0x1E6DE, 0x1E6E0, 0x1E6F5, 0x1E6FE, 0x1E6FF, 0x1F130, 0x1F149,
	0x1F150, 0x1F169, 0x1F170, 0x1F189, 0x2B73A, 0x2B73F, 0x2B81E, 0x2B81E, 0x2CEA2, 0x2CEAD, 0x2EBF0, 0x2EE5D,
	0x323B0, 0x33479, 0x3D000, 0x3FC3F,
}

var casedDiff = ranges{}

var caseIgnorableDiff = ranges{
	0x27, 0x27, 0x2E, 0x2E, 0x3A, 0x3A, 0xB7, 0xB7, 0x387, 0x387, 0x55F, 0x55F,
	0x5F4, 0x5F4, 0x2018, 0x2019, 0x2024, 0x2024, 0x2027, 0x2027, 0xFE13, 0xFE13, 0xFE52, 0xFE52,
	0xFE55, 0xFE55, 0xFF07, 0xFF07, 0xFF0E, 0xFF0E, 0xFF1A, 0xFF1A,
}

var upperExceptions = map[rune]string{
	0xDF:   "SS",
	0x149:  "\u02BCN",
	0x1F0:  "J\u030C",
	0x390:  "\u0399\u0308\u0301",
	0x3B0:  "\u03A5\u0308\u0301",
	0x587:  "\u0535\u0552",
	0x1E96: "H\u0331",
	0x1E97: "T\u0308",
	0x1E98: "W\u030A",
	0x1E99: "Y\u030A",
	0x1E9A: "A\u02BE",
	0x1F50: "\u03A5\u0313",
	0x1F52: "\u03A5\u0313\u0300",
	0x1F54: "\u03A5\u0313\u0301",
	0x1F56: "\u03A5\u0313\u0342",
	0x1F80: "\u1F08\u0399",
	0x1F81: "\u1F09\u0399",
	0x1F82: "\u1F0A\u0399",
	0x1F83: "\u1F0B\u0399",
	0x1F84: "\u1F0C\u0399",
	0x1F85: "\u1F0D\u0399",
	0x1F86: "\u1F0E\u0399",
	0x1F87: "\u1F0F\u0399",
	0x1F88: "\u1F08\u0399",
	0x1F89: "\u1F09\u0399",
	0x1F8A: "\u1F0A\u0399",
	0x1F8B: "\u1F0B\u0399",
	0x1F8C: "\u1F0C\u0399",
	0x1F8D: "\u1F0D\u0399",
	0x1F8E: "\u1F0E\u0399",
	0x1F8F: "\u1F0F\u0399",
	0x1F90: "\u1F28\u0399",
	0x1F91: "\u1F29\u0399",
	0x1F92: "\u1F2A\u0399",
	0x1F93: "\u1F2B\u0399",
	0x1F94: "\u1F2C\u0399",
	0x1F95: "\u1F2D\u0399",
	0x1F96: "\u1F2E\u0399",
	0x1F97: "\u1F2F\u0399",
	0x1F98: "\u1F28\u0399",
	0x1F99: "\u1F29\u0399",
	0x1F9A: "\u1F2A\u0399",
	0x1F9B: "\u1F2B\u0399",
	0x1F9C: "\u1F2C\u0399",
	0x1F9D: "\u1F2D\u0399",
	0x1F9E: "\u1F2E\u0399",
	0x1F9F: "\u1F2F\u0399",
	0x1FA0: "\u1F68\u0399",
	0x1FA1: "\u1F69\u0399",
	0x1FA2: "\u1F6A\u0399",
	0x1FA3: "\u1F6B\u0399",
	0x1FA4: "\u1F6C\u0399",
	0x1FA5: "\u1F6D\u0399",
	0x1FA6: "\u1F6E\u0399",
	0x1FA7: "\u1F6F\u0399",
	0x1FA8: "\u1F68\u0399",
	0x1FA9: "\u1F69\u0399",
	0x1FAA: "\u1F6A\u0399",
	0x1FAB: "\u1F6B\u0399",
	0x1FAC: "\u1F6C\u0399",
	0x1FAD: "\u1F6D\u0399",
	0x1FAE: "\u1F6E\u0399",
	0x1FAF: "\u1F6F\u0399",
	0x1FB2: "\u1FBA\u0399",
	0x1FB3: "\u0391\u0399",
	0x1FB4: "\u0386\u0399",
	0x1FB6: "\u0391\u0342",
	0x1FB7: "\u0391\u0342\u0399",
	0x1FBC: "\u0391\u0399",
	0x1FC2: "\u1FCA\u0399",
	0x1FC3: "\u0397\u0399",
	0x1FC4: "\u0389\u0399",
	0x1FC6: "\u0397\u0342",
	0x1FC7: "\u0397\u0342\u0399",
	0x1FCC: "\u0397\u0399",
	0x1FD2: "\u0399\u0308\u0300",
	0x1FD3: "\u0399\u0308\u0301",
	0x1FD6: "\u0399\u0342",
	0x1FD7: "\u0399\u0308\u0342",
	0x1FE2: "\u03A5\u0308\u0300",
	0x1FE3: "\u03A5\u0308\u0301",
	0x1FE4: "\u03A1\u0313",
	0x1FE6: "\u03A5\u0342",
	0x1FE7: "\u03A5\u0308\u0342",
	0x1FF2: "\u1FFA\u0399",
	0x1FF3: "\u03A9\u0399",
	0x1FF4: "\u038F\u0399",
	0x1FF6: "\u03A9\u0342",
	0x1FF7: "\u03A9\u0342\u0399",
	0x1FFC: "\u03A9\u0399",
	0xFB00: "FF",
	0xFB01: "FI",
	0xFB02: "FL",
	0xFB03: "FFI",
	0xFB04: "FFL",
	0xFB05: "ST",
	0xFB06: "ST",
	0xFB13: "\u0544\u0546",
	0xFB14: "\u0544\u0535",
	0xFB15: "\u0544\u053B",
	0xFB16: "\u054E\u0546",
	0xFB17: "\u0544\u053D",
}

var lowerExceptions = map[rune]string{
	0x130: "i\u0307",
}

var titleExceptions = map[rune]string{
	0xDF:   "Ss",
	0x149:  "\u02BCN",
	0x1F0:  "J\u030C",
	0x390:  "\u0399\u0308\u0301",
	0x3B0:  "\u03A5\u0308\u0301",
	0x587:  "\u0535\u0582",
	0x1E96: "H\u0331",
	0x1E97: "T\u0308",
	0x1E98: "W\u030A",
	0x1E99: "Y\u030A",
	0x1E9A: "A\u02BE",
	0x1F50: "\u03A5\u0313",
	0x1F52: "\u03A5\u0313\u0300",
	0x1F54: "\u03A5\u0313\u0301",
	0x1F56: "\u03A5\u0313\u0342",
	0x1FB2: "\u1FBA\u0345",
	0x1FB4: "\u0386\u0345",
	0x1FB6: "\u0391\u0342",
	0x1FB7: "\u0391\u0342\u0345",
	0x1FC2: "\u1FCA\u0345",
	0x1FC4: "\u0389\u0345",
	0x1FC6: "\u0397\u0342",
	0x1FC7: "\u0397\u0342\u0345",
	0x1FD2: "\u0399\u0308\u0300",
	0x1FD3: "\u0399\u0308\u0301",
	0x1FD6: "\u0399\u0342",
	0x1FD7: "\u0399\u0308\u0342",
	0x1FE2: "\u03A5\u0308\u0300",
	0x1FE3: "\u03A5\u0308\u0301",
	0x1FE4: "\u03A1\u0313",
	0x1FE6: "\u03A5\u0342",
	0x1FE7: "\u03A5\u0308\u0342",
	0x1FF2: "\u1FFA\u0345",
	0x1FF4: "\u038F\u0345",
	0x1FF6: "\u03A9\u0342",
	0x1FF7: "\u03A9\u0342\u0345",
	0xFB00: "Ff",
	0xFB01: "Fi",
	0xFB02: "Fl",
	0xFB03: "Ffi",
	0xFB04: "Ffl",
	0xFB05: "St",
	0xFB06: "St",
	0xFB13: "\u0544\u0576",
	0xFB14: "\u0544\u0565",
	0xFB15: "\u0544\u056B",
	0xFB16: "\u054E\u0576",
	0xFB17: "\u0544\u056D",
}

var foldToASCII = map[rune]rune{
	0x130:  'i',
	0x17F:  's',
	0x212A: 'k',
}
SOLVE_EOF

find . -name '*.py' -type f -delete
find . -type d -empty -delete
