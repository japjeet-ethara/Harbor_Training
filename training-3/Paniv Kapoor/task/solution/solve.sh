#!/bin/bash
set -euo pipefail

cd /workspace/repo
cat > /workspace/repo/go.mod << 'END_GO_MOD'
module titlecase

go 1.23
END_GO_MOD
cat > /workspace/repo/main.go << 'END_MAIN_GO'
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

// punct is the Python PUNCT class, in the same order the regex uses.
const punct = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// whitespace matches the third-party regex module's \s (25 code points).
var whitespace = map[rune]struct{}{
	'\t': {}, '\n': {}, '\v': {}, '\f': {}, '\r': {}, ' ': {},
	'\u0085': {}, '\u00a0': {}, '\u1680': {},
	'\u2000': {}, '\u2001': {}, '\u2002': {}, '\u2003': {}, '\u2004': {},
	'\u2005': {}, '\u2006': {}, '\u2007': {}, '\u2008': {}, '\u2009': {},
	'\u200a': {}, '\u2028': {}, '\u2029': {}, '\u202f': {}, '\u205f': {},
	'\u3000': {},
}

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			line = strings.TrimSuffix(line, "\r")
			_, _ = io.WriteString(out, titlecase(line, true))
			_, _ = io.WriteString(out, "\n")
		}
		if err != nil {
			break
		}
	}
	_ = out.Flush()
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitBreaks(text)
	processed := make([]string, len(lines))
	for i, line := range lines {
		processed[i] = titlecaseLine(line, smallFirstLast)
	}
	return strings.Join(processed, "\n")
}

func splitBreaks(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	start := 0
	i := 0
	rs := []rune(text)
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

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := pyUpper(line) == line
	words, spaces := splitSpaces(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titlecaseWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	joined := joinWords(tc, spaces)
	return applySubphrase(joined)
}

func splitSpaces(line string) (words, spaces []string) {
	rs := []rune(line)
	start := 0
	for i := 0; i < len(rs); i++ {
		if _, ok := whitespace[rs[i]]; ok {
			words = append(words, string(rs[start:i]))
			spaces = append(spaces, string(rs[i:i+1]))
			start = i + 1
		}
	}
	words = append(words, string(rs[start:]))
	return words, spaces
}

func joinWords(words, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func titlecaseWord(word string, allCaps bool) string {
	if word == "" {
		return ""
	}
	if allCaps && isUCInitials(word) {
		return word
	}
	if ok, recased := recaseApostrophe(word); ok {
		return recased
	}
	if prefix, rest, ok := splitMac(word); ok {
		return pyCapitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		rs := []rune(word)
		return pyUpperRune(rs[0]) + string(rs[1:])
	}
	if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return pyLower(word)
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
		word = pyLower(word)
	}
	if runeLen(word) > 2 && isAllConsonants(word) {
		return pyUpper(word)
	}
	return capFirst(word)
}

func isUCInitials(s string) bool {
	rs := []rune(s)
	if len(rs) == 0 {
		return false
	}
	return matchInitials(rs, 0)
}

func matchInitials(rs []rune, i int) bool {
	if i == len(rs) {
		return i > 0
	}
	if i+1 >= len(rs) || !isUpperLetter(rs[i]) || rs[i+1] != '.' {
		return false
	}
	if matchInitials(rs, i+2) {
		return true
	}
	if i+2 < len(rs) && isUpperLetter(rs[i+2]) && matchInitials(rs, i+3) {
		return true
	}
	return false
}

func recaseApostrophe(word string) (bool, string) {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) {
		return false, ""
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return false, ""
	}
	rest := rs[2:]
	if !aposTail(rest) {
		return false, ""
	}
	var first string
	if !isVowel(rs[0]) {
		first = pyLowerRune(rs[0])
	} else {
		first = pyUpperRune(rs[0])
	}
	return true, first + string(rs[1:2]) + pyUpperRune(rs[2]) + string(rs[3:])
}

func aposTail(rest []rune) bool {
	if len(rest) == 0 {
		return false
	}
	if allLetters(rest) {
		return true
	}
	if len(rest) >= 3 && allLetters(rest[:len(rest)-2]) && isAposSuffix(rest[len(rest)-2]) && isAposSuffix(rest[len(rest)-1]) {
		return true
	}
	return false
}

func isAposSuffix(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
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
	switch unicode.ToLower(r) {
	case 'a', 'e', 'i', 'o', 'u':
		return true
	default:
		return false
	}
}

func splitMac(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	head := string(rs[:2])
	if head == "Mc" || head == "mc" || head == "MC" {
		if isRegexWord(rs[2]) {
			return head, string(rs[2:]), true
		}
	}
	return "", "", false
}

func isHonorific(word string) bool {
	switch pyLower(word) {
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
		if isUpperLetter(rs[i]) {
			return true
		}
		i++
	}
	return false
}

func isSmallWord(word string) bool {
	switch pyLower(word) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

func isAllConsonants(word string) bool {
	if word == "" {
		return false
	}
	for _, r := range word {
		if !isASCIIConsonant(r) {
			return false
		}
	}
	return true
}

func isASCIIConsonant(r rune) bool {
	if r >= 'A' && r <= 'Z' {
		r = r - 'A' + 'a'
	}
	return r < utf8.RuneSelf && strings.ContainsRune("bcdfghjklmnpqrstvwxz", r)
}

func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return word
	}
	return string(rs[:i]) + pyUpperRune(rs[i]) + string(rs[i+1:])
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	// Leading punctuation is greedy, then the matcher backtracks.
	for {
		if n, ok := matchSmallAt(rs, i, true); ok {
			return string(rs[:i]) + pyCapitalize(string(rs[i:i+n])) + string(rs[i+n:])
		}
		if i == 0 || !isPunct(rs[i-1]) {
			break
		}
		i--
	}
	return word
}

func applySmallLast(word string) string {
	rs := []rune(word)
	for i := 0; i <= len(rs); i++ {
		if !hasBoundary(rs, i) {
			continue
		}
		n, ok := matchSmallAt(rs, i, true)
		if !ok {
			continue
		}
		end := i + n
		if end < len(rs) && end+1 == len(rs) && isPunct(rs[end]) {
			end++
		}
		if end == len(rs) {
			return string(rs[:i]) + pyCapitalize(string(rs[i:end]))
		}
	}
	return word
}

func applySubphrase(line string) string {
	rs := []rune(line)
	var b strings.Builder
	i := 0
	for i < len(rs) {
		if i+1 < len(rs) && isSubDelim(rs[i]) && rs[i+1] == ' ' {
			if n, ok := matchSmallAt(rs, i+2, false); ok {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2 : i+2+n])))
				i = i + 2 + n
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

// matchSmallAt matches the Python small-word alternation at rs[i:].
// When boundary is set, the match must end on a word boundary, and an
// optional dot is dropped if keeping it would miss that boundary.
func matchSmallAt(rs []rune, i int, boundary bool) (int, bool) {
	literals := []string{
		"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to",
	}
	for _, lit := range literals {
		n := runeLen(lit)
		if hasFoldPrefix(rs[i:], lit) && (!boundary || hasBoundary(rs, i+n)) {
			return n, true
		}
	}
	if n, ok := matchStemDot(rs, i, "v", boundary); ok {
		return n, true
	}
	if hasFoldPrefix(rs[i:], "via") && (!boundary || hasBoundary(rs, i+3)) {
		return 3, true
	}
	if n, ok := matchStemDot(rs, i, "vs", boundary); ok {
		return n, true
	}
	return 0, false
}

func matchStemDot(rs []rune, i int, stem string, boundary bool) (int, bool) {
	if !hasFoldPrefix(rs[i:], stem) {
		return 0, false
	}
	n := runeLen(stem)
	if i+n < len(rs) && rs[i+n] == '.' {
		if !boundary || hasBoundary(rs, i+n+1) {
			return n + 1, true
		}
	}
	if !boundary || hasBoundary(rs, i+n) {
		return n, true
	}
	return 0, false
}

func hasFoldPrefix(rs []rune, stem string) bool {
	ss := []rune(stem)
	if len(rs) < len(ss) {
		return false
	}
	for i, r := range ss {
		if unicode.ToLower(rs[i]) != unicode.ToLower(r) {
			return false
		}
	}
	return true
}

func hasBoundary(rs []rune, i int) bool {
	var left, right bool
	if i > 0 {
		left = isRegexWord(rs[i-1])
	}
	if i < len(rs) {
		right = isRegexWord(rs[i])
	}
	return left != right
}

func isRegexWord(r rune) bool {
	if unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.Is(unicode.Nl, r) {
		return true
	}
	if unicode.Is(unicode.Mn, r) || unicode.Is(unicode.Mc, r) || unicode.Is(unicode.Me, r) {
		return true
	}
	return unicode.Is(unicode.Pc, r)
}

func isPunct(r rune) bool {
	return strings.ContainsRune(punct, r)
}

func isSubDelim(r rune) bool {
	switch r {
	case ':', ';', '.', '?', '!', '-', '–', '‒', '—', '―':
		return true
	default:
		return false
	}
}

func isUpperLetter(r rune) bool {
	return unicode.IsUpper(r)
}

func allLetters(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return true
}

func runeLen(s string) int {
	return utf8.RuneCountInString(s)
}

func pyLower(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(pyLowerRune(r))
	}
	return b.String()
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(pyUpperRune(r))
	}
	return b.String()
}

func pyLowerRune(r rune) string {
	if mapped, ok := pyLowerSpecial[r]; ok {
		return mapped
	}
	return string(unicode.ToLower(r))
}

func pyUpperRune(r rune) string {
	if mapped, ok := pyUpperSpecial[r]; ok {
		return mapped
	}
	return string(unicode.ToUpper(r))
}

func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	return pyUpperRune(rs[0]) + pyLower(string(rs[1:]))
}
END_MAIN_GO
cat > /workspace/repo/casefold.go << 'END_CASEFOLD_GO'
package main

var pyUpperSpecial = map[rune]string{
	'\U000000df': "\u0053\u0053",
	'\U00000149': "\u02bc\u004e",
	'\U000001f0': "\u004a\u030c",
	'\U00000390': "\u0399\u0308\u0301",
	'\U000003b0': "\u03a5\u0308\u0301",
	'\U00000587': "\u0535\u0552",
	'\U00001e96': "\u0048\u0331",
	'\U00001e97': "\u0054\u0308",
	'\U00001e98': "\u0057\u030a",
	'\U00001e99': "\u0059\u030a",
	'\U00001e9a': "\u0041\u02be",
	'\U00001f50': "\u03a5\u0313",
	'\U00001f52': "\u03a5\u0313\u0300",
	'\U00001f54': "\u03a5\u0313\u0301",
	'\U00001f56': "\u03a5\u0313\u0342",
	'\U00001f80': "\u1f08\u0399",
	'\U00001f81': "\u1f09\u0399",
	'\U00001f82': "\u1f0a\u0399",
	'\U00001f83': "\u1f0b\u0399",
	'\U00001f84': "\u1f0c\u0399",
	'\U00001f85': "\u1f0d\u0399",
	'\U00001f86': "\u1f0e\u0399",
	'\U00001f87': "\u1f0f\u0399",
	'\U00001f88': "\u1f08\u0399",
	'\U00001f89': "\u1f09\u0399",
	'\U00001f8a': "\u1f0a\u0399",
	'\U00001f8b': "\u1f0b\u0399",
	'\U00001f8c': "\u1f0c\u0399",
	'\U00001f8d': "\u1f0d\u0399",
	'\U00001f8e': "\u1f0e\u0399",
	'\U00001f8f': "\u1f0f\u0399",
	'\U00001f90': "\u1f28\u0399",
	'\U00001f91': "\u1f29\u0399",
	'\U00001f92': "\u1f2a\u0399",
	'\U00001f93': "\u1f2b\u0399",
	'\U00001f94': "\u1f2c\u0399",
	'\U00001f95': "\u1f2d\u0399",
	'\U00001f96': "\u1f2e\u0399",
	'\U00001f97': "\u1f2f\u0399",
	'\U00001f98': "\u1f28\u0399",
	'\U00001f99': "\u1f29\u0399",
	'\U00001f9a': "\u1f2a\u0399",
	'\U00001f9b': "\u1f2b\u0399",
	'\U00001f9c': "\u1f2c\u0399",
	'\U00001f9d': "\u1f2d\u0399",
	'\U00001f9e': "\u1f2e\u0399",
	'\U00001f9f': "\u1f2f\u0399",
	'\U00001fa0': "\u1f68\u0399",
	'\U00001fa1': "\u1f69\u0399",
	'\U00001fa2': "\u1f6a\u0399",
	'\U00001fa3': "\u1f6b\u0399",
	'\U00001fa4': "\u1f6c\u0399",
	'\U00001fa5': "\u1f6d\u0399",
	'\U00001fa6': "\u1f6e\u0399",
	'\U00001fa7': "\u1f6f\u0399",
	'\U00001fa8': "\u1f68\u0399",
	'\U00001fa9': "\u1f69\u0399",
	'\U00001faa': "\u1f6a\u0399",
	'\U00001fab': "\u1f6b\u0399",
	'\U00001fac': "\u1f6c\u0399",
	'\U00001fad': "\u1f6d\u0399",
	'\U00001fae': "\u1f6e\u0399",
	'\U00001faf': "\u1f6f\u0399",
	'\U00001fb2': "\u1fba\u0399",
	'\U00001fb3': "\u0391\u0399",
	'\U00001fb4': "\u0386\u0399",
	'\U00001fb6': "\u0391\u0342",
	'\U00001fb7': "\u0391\u0342\u0399",
	'\U00001fbc': "\u0391\u0399",
	'\U00001fc2': "\u1fca\u0399",
	'\U00001fc3': "\u0397\u0399",
	'\U00001fc4': "\u0389\u0399",
	'\U00001fc6': "\u0397\u0342",
	'\U00001fc7': "\u0397\u0342\u0399",
	'\U00001fcc': "\u0397\u0399",
	'\U00001fd2': "\u0399\u0308\u0300",
	'\U00001fd3': "\u0399\u0308\u0301",
	'\U00001fd6': "\u0399\u0342",
	'\U00001fd7': "\u0399\u0308\u0342",
	'\U00001fe2': "\u03a5\u0308\u0300",
	'\U00001fe3': "\u03a5\u0308\u0301",
	'\U00001fe4': "\u03a1\u0313",
	'\U00001fe6': "\u03a5\u0342",
	'\U00001fe7': "\u03a5\u0308\u0342",
	'\U00001ff2': "\u1ffa\u0399",
	'\U00001ff3': "\u03a9\u0399",
	'\U00001ff4': "\u038f\u0399",
	'\U00001ff6': "\u03a9\u0342",
	'\U00001ff7': "\u03a9\u0342\u0399",
	'\U00001ffc': "\u03a9\u0399",
	'\U0000fb00': "\u0046\u0046",
	'\U0000fb01': "\u0046\u0049",
	'\U0000fb02': "\u0046\u004c",
	'\U0000fb03': "\u0046\u0046\u0049",
	'\U0000fb04': "\u0046\u0046\u004c",
	'\U0000fb05': "\u0053\u0054",
	'\U0000fb06': "\u0053\u0054",
	'\U0000fb13': "\u0544\u0546",
	'\U0000fb14': "\u0544\u0535",
	'\U0000fb15': "\u0544\u053b",
	'\U0000fb16': "\u054e\u0546",
	'\U0000fb17': "\u0544\u053d",
}

var pyLowerSpecial = map[rune]string{
	'\U00000130': "\u0069\u0307",
}
END_CASEFOLD_GO

find /workspace/repo -type f -name '*.py' -delete
# The module binary is named "titlecase", so the old Python package directory
# cannot remain or `go build ./...` fails.
rm -rf /workspace/repo/titlecase
