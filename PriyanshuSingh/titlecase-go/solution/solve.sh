#!/bin/bash
# Reference solution: a Go port of python-titlecase, then remove the Python.
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'GOMOD_EOF'
module titlecase

go 1.23
GOMOD_EOF

cat > main.go <<'MAIN_GO_EOF'
// Command titlecase reads one title per line from stdin and prints each one
// titlecased. It is a byte-for-byte port of python-titlecase 2.4.1 running on
// its standard library `re` branch.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

// punct is the PUNCT character class from the Python source.
const punct = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// subphraseMarks are the characters that open a sub-phrase when a space follows.
const subphraseMarks = ":.;?!-–‒—―"

const consonants = "bcdfghjklmnpqrstvwxz"

// smallWords lists every way the SMALL alternation can match, in the order
// Python's backtracking engine tries them. `v\.?` tries "v." before "v".
var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
	"on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

func isPunct(r rune) bool { return strings.ContainsRune(punct, r) }

// isSpace matches Python's \s for str patterns, which is wider than
// unicode.IsSpace: it includes the \x1c-\x1f separators.
func isSpace(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

// isWord matches Python's \w for str patterns. Combining marks are not \w.
func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.In(r, unicode.Nd, unicode.Nl, unicode.No)
}

// fold applies the comparison re.IGNORECASE uses: simple lower case, plus the
// two extra equivalences that matter for ASCII patterns (i/dotless i, s/long s).
func fold(r rune) rune {
	switch l := unicode.ToLower(r); l {
	case 0x131:
		return 'i'
	case 0x17f:
		return 's'
	default:
		return l
	}
}

func isCased(r rune) bool {
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r) ||
		unicode.In(r, unicode.Other_Lowercase, unicode.Other_Uppercase)
}

func isCaseIgnorable(r rune) bool {
	return unicode.In(r, unicode.Mn, unicode.Me, unicode.Cf, unicode.Lm, unicode.Sk) ||
		strings.ContainsRune(extraCaseIgnorable, r)
}

// pyUpper is str.upper(): the full mapping, which can change the length.
func pyUpper(s []rune) []rune {
	out := make([]rune, 0, len(s))
	for _, r := range s {
		if full, ok := upperSpecial[r]; ok {
			out = append(out, []rune(full)...)
		} else {
			out = append(out, unicode.ToUpper(r))
		}
	}
	return out
}

// lowerAt is the str.lower() mapping for s[i], which needs the context of the
// whole string to choose between medial and final sigma.
func lowerAt(s []rune, i int) []rune {
	r := s[i]
	if r == 0x130 {
		return []rune{'i', 0x307}
	}
	if r != 0x3a3 {
		return []rune{unicode.ToLower(r)}
	}
	j := i - 1
	for j >= 0 && isCaseIgnorable(s[j]) {
		j--
	}
	final := j >= 0 && isCased(s[j])
	if final {
		j = i + 1
		for j < len(s) && isCaseIgnorable(s[j]) {
			j++
		}
		final = j == len(s) || !isCased(s[j])
	}
	if final {
		return []rune{0x3c2}
	}
	return []rune{0x3c3}
}

func pyLower(s []rune) []rune {
	out := make([]rune, 0, len(s))
	for i := range s {
		out = append(out, lowerAt(s, i)...)
	}
	return out
}

// pyCapitalize is str.capitalize(): title case the first character, lower the rest.
func pyCapitalize(s []rune) []rune {
	if len(s) == 0 {
		return nil
	}
	out := make([]rune, 0, len(s))
	if full, ok := titleSpecial[s[0]]; ok {
		out = append(out, []rune(full)...)
	} else {
		out = append(out, unicode.ToTitle(s[0]))
	}
	for i := 1; i < len(s); i++ {
		out = append(out, lowerAt(s, i)...)
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

func contains(s []rune, r rune) bool {
	for _, c := range s {
		if c == r {
			return true
		}
	}
	return false
}

func containsDoubleSlash(s []rune) bool {
	for i := 0; i+1 < len(s); i++ {
		if s[i] == '/' && s[i+1] == '/' {
			return true
		}
	}
	return false
}

func split(s []rune, sep rune) [][]rune {
	parts := [][]rune{}
	start := 0
	for i, r := range s {
		if r == sep {
			parts = append(parts, s[start:i])
			start = i + 1
		}
	}
	return append(parts, s[start:])
}

// splitLines is re.split('[\r\n]+', text).
func splitLines(s []rune) [][]rune {
	lines := [][]rune{}
	start := 0
	for i := 0; i < len(s); {
		if s[i] != '\r' && s[i] != '\n' {
			i++
			continue
		}
		lines = append(lines, s[start:i])
		for i < len(s) && (s[i] == '\r' || s[i] == '\n') {
			i++
		}
		start = i
	}
	return append(lines, s[start:])
}

// foldedPrefix reports whether s[at:] starts with the ASCII word, ignoring case
// the way re.IGNORECASE does.
func foldedPrefix(s []rune, at int, word string) bool {
	if at+len(word) > len(s) {
		return false
	}
	for i := 0; i < len(word); i++ {
		if fold(s[at+i]) != rune(word[i]) {
			return false
		}
	}
	return true
}

func foldedEqual(s []rune, word string) bool {
	return len(s) == len(word) && foldedPrefix(s, 0, word)
}

// wordBoundary is \b at position i.
func wordBoundary(s []rune, i int) bool {
	before := i > 0 && isWord(s[i-1])
	after := i < len(s) && isWord(s[i])
	return before != after
}

// ucInitials is ^(?:[A-Z]\.|[A-Z]\.[A-Z])+$.
func ucInitials(s []rune) bool {
	if len(s) == 0 {
		return false
	}
	upper := func(i int) bool { return i < len(s) && s[i] >= 'A' && s[i] <= 'Z' }
	for i := 0; i < len(s); {
		if !upper(i) || i+1 >= len(s) || s[i+1] != '.' {
			return false
		}
		i += 2
		if upper(i) && (i+1 == len(s) || s[i+1] != '.') {
			i++
		}
	}
	return true
}

// aposSecond is ^[dol]['‘][\w]+(?:['s]{2})?$ with re.IGNORECASE.
func aposSecond(s []rune) bool {
	if len(s) < 3 || !strings.ContainsRune("dolDOL", s[0]) || (s[1] != '\'' && s[1] != 0x2018) {
		return false
	}
	rest := s[2:]
	end := 0
	for end < len(rest) && isWord(rest[end]) {
		end++
	}
	if end == len(rest) {
		return true
	}
	// The optional tail must cover the last two characters, and everything
	// before them must be at least one word character.
	tail := func(r rune) bool { return r == '\'' || fold(r) == 's' }
	n := len(rest)
	return n >= 3 && end >= n-2 && tail(rest[n-2]) && tail(rest[n-1])
}

// macPrefix is ^([Mm]c|MC)(\w.+). It returns the length of group 1.
func macPrefix(s []rune) bool {
	if len(s) < 4 {
		return false
	}
	head := string(s[:2])
	if head != "mc" && head != "Mc" && head != "MC" {
		return false
	}
	return isWord(s[2])
}

// honorific is ^((m((rs?)|s))|Dr)$ with re.IGNORECASE.
func honorific(s []rune) bool {
	return foldedEqual(s, "mr") || foldedEqual(s, "mrs") || foldedEqual(s, "ms") || foldedEqual(s, "dr")
}

// inlinePeriod searches for [\w][.][\w].
func inlinePeriod(s []rune) bool {
	for i := 1; i+1 < len(s); i++ {
		if s[i] == '.' && isWord(s[i-1]) && isWord(s[i+1]) {
			return true
		}
	}
	return false
}

// ucElsewhere is a match of [PUNCT]*?[a-zA-Z]+[A-Z]+? at the start of the word.
func ucElsewhere(s []rune) bool {
	i := 0
	for i < len(s) && isPunct(s[i]) {
		i++
	}
	ascii := func(r rune) bool { return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') }
	if i >= len(s) || !ascii(s[i]) {
		return false
	}
	for j := i + 1; j < len(s) && ascii(s[j]); j++ {
		if s[j] >= 'A' && s[j] <= 'Z' {
			return true
		}
	}
	return false
}

func isSmallWord(s []rune) bool {
	for _, word := range smallWords {
		if foldedEqual(s, word) {
			return true
		}
	}
	return false
}

func allConsonants(s []rune) bool {
	if len(s) == 0 {
		return false
	}
	for _, r := range s {
		if !strings.ContainsRune(consonants, fold(r)) {
			return false
		}
	}
	return true
}

// capFirst is CAPFIRST.sub: upper-case everything up to and including the first
// word character, provided only punctuation comes before it.
func capFirst(s []rune) []rune {
	for i, r := range s {
		if isWord(r) {
			return append(pyUpper(s[:i+1]), s[i+1:]...)
		}
		if !isPunct(r) {
			break
		}
	}
	return s
}

// smallFirst is SMALL_FIRST.sub: ^([PUNCT]*)(SMALL)\b.
func smallFirst(s []rune) []rune {
	start := 0
	for start < len(s) && isPunct(s[start]) {
		start++
	}
	for _, word := range smallWords {
		end := start + len(word)
		if foldedPrefix(s, start, word) && wordBoundary(s, end) {
			out := append([]rune{}, s[:start]...)
			out = append(out, pyCapitalize(s[start:end])...)
			return append(out, s[end:]...)
		}
	}
	return s
}

// smallLast is SMALL_LAST.sub: \b(SMALL)[PUNCT]?$, capitalising the whole match.
func smallLast(s []rune) []rune {
	for start := 0; start < len(s); start++ {
		if !wordBoundary(s, start) {
			continue
		}
		for _, word := range smallWords {
			end := start + len(word)
			if !foldedPrefix(s, start, word) {
				continue
			}
			if end == len(s) || (end+1 == len(s) && isPunct(s[end])) {
				out := append([]rune{}, s[:start]...)
				return append(out, pyCapitalize(s[start:])...)
			}
		}
	}
	return s
}

// subphrase is SUBPHRASE.sub: ([:.;?!-...][ ])(SMALL), case sensitive, with no
// word boundary, so the first alternative that matches wins.
func subphrase(s []rune) []rune {
	out := make([]rune, 0, len(s))
	for i := 0; i < len(s); {
		if strings.ContainsRune(subphraseMarks, s[i]) && i+1 < len(s) && s[i+1] == ' ' {
			if n := smallPrefixLen(s[i+2:]); n > 0 {
				out = append(out, s[i], ' ')
				out = append(out, pyCapitalize(s[i+2:i+2+n])...)
				i += 2 + n
				continue
			}
		}
		out = append(out, s[i])
		i++
	}
	return out
}

func smallPrefixLen(s []rune) int {
	for _, word := range smallWords {
		if len(s) >= len(word) && string(s[:len(word)]) == word {
			return len(word)
		}
	}
	return 0
}

func titlecaseWord(word []rune, allCaps bool) []rune {
	if allCaps && ucInitials(word) {
		return word
	}
	if aposSecond(word) {
		first := unicode.ToUpper(word[0])
		if word[0] != 'o' && word[0] != 'O' {
			first = unicode.ToLower(word[0])
		}
		out := []rune{first, word[1]}
		out = append(out, pyUpper(word[2:3])...)
		return append(out, word[3:]...)
	}
	if macPrefix(word) {
		return append([]rune("Mc"), titlecase(word[2:], true)...)
	}
	if honorific(word) {
		return append(pyUpper(word[:1]), word[1:]...)
	}
	if inlinePeriod(word) || (!allCaps && ucElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return pyLower(word)
	}
	if contains(word, '/') && !containsDoubleSlash(word) {
		return titlecaseParts(word, '/')
	}
	if contains(word, '-') {
		return titlecaseParts(word, '-')
	}
	if allCaps {
		word = pyLower(word)
	}
	if allConsonants(word) && len(word) > 2 {
		return pyUpper(word)
	}
	return capFirst(word)
}

func titlecaseParts(word []rune, sep rune) []rune {
	out := []rune{}
	for i, part := range split(word, sep) {
		if i > 0 {
			out = append(out, sep)
		}
		out = append(out, titlecase(part, false)...)
	}
	return out
}

func titlecaseLine(line []rune, smallFirstLast bool) []rune {
	allCaps := equal(pyUpper(line), line)

	words := [][]rune{}
	spaces := []rune{}
	start := 0
	for i, r := range line {
		if isSpace(r) {
			words = append(words, line[start:i])
			spaces = append(spaces, r)
			start = i + 1
		}
	}
	words = append(words, line[start:])

	for i, word := range words {
		words[i] = titlecaseWord(word, allCaps)
	}
	if smallFirstLast {
		words[0] = smallFirst(words[0])
		words[len(words)-1] = smallLast(words[len(words)-1])
	}

	joined := []rune{}
	for i, word := range words {
		joined = append(joined, word...)
		if i < len(spaces) {
			joined = append(joined, spaces[i])
		}
	}
	return subphrase(joined)
}

func titlecase(text []rune, smallFirstLast bool) []rune {
	out := []rune{}
	for i, line := range splitLines(text) {
		if i > 0 {
			out = append(out, '\n')
		}
		out = append(out, titlecaseLine(line, smallFirstLast)...)
	}
	return out
}

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if line == "" && err != nil {
			if err != io.EOF {
				os.Exit(1)
			}
			return
		}
		line = strings.TrimSuffix(line, "\n")
		out.WriteString(string(titlecase([]rune(line), true)))
		out.WriteByte('\n')
	}
}
MAIN_GO_EOF

cat > casing.go <<'CASING_GO_EOF'
package main

// Python's full case mappings where they differ from Go's unicode package.
// Both sides use Unicode 15.0.

// upperSpecial holds the multi-character upper-case mappings.
var upperSpecial = map[rune]string{
	0xdf: "\u0053\u0053",
	0x149: "\u02bc\u004e",
	0x1f0: "\u004a\u030c",
	0x390: "\u0399\u0308\u0301",
	0x3b0: "\u03a5\u0308\u0301",
	0x587: "\u0535\u0552",
	0x1e96: "\u0048\u0331",
	0x1e97: "\u0054\u0308",
	0x1e98: "\u0057\u030a",
	0x1e99: "\u0059\u030a",
	0x1e9a: "\u0041\u02be",
	0x1f50: "\u03a5\u0313",
	0x1f52: "\u03a5\u0313\u0300",
	0x1f54: "\u03a5\u0313\u0301",
	0x1f56: "\u03a5\u0313\u0342",
	0x1f80: "\u1f08\u0399",
	0x1f81: "\u1f09\u0399",
	0x1f82: "\u1f0a\u0399",
	0x1f83: "\u1f0b\u0399",
	0x1f84: "\u1f0c\u0399",
	0x1f85: "\u1f0d\u0399",
	0x1f86: "\u1f0e\u0399",
	0x1f87: "\u1f0f\u0399",
	0x1f88: "\u1f08\u0399",
	0x1f89: "\u1f09\u0399",
	0x1f8a: "\u1f0a\u0399",
	0x1f8b: "\u1f0b\u0399",
	0x1f8c: "\u1f0c\u0399",
	0x1f8d: "\u1f0d\u0399",
	0x1f8e: "\u1f0e\u0399",
	0x1f8f: "\u1f0f\u0399",
	0x1f90: "\u1f28\u0399",
	0x1f91: "\u1f29\u0399",
	0x1f92: "\u1f2a\u0399",
	0x1f93: "\u1f2b\u0399",
	0x1f94: "\u1f2c\u0399",
	0x1f95: "\u1f2d\u0399",
	0x1f96: "\u1f2e\u0399",
	0x1f97: "\u1f2f\u0399",
	0x1f98: "\u1f28\u0399",
	0x1f99: "\u1f29\u0399",
	0x1f9a: "\u1f2a\u0399",
	0x1f9b: "\u1f2b\u0399",
	0x1f9c: "\u1f2c\u0399",
	0x1f9d: "\u1f2d\u0399",
	0x1f9e: "\u1f2e\u0399",
	0x1f9f: "\u1f2f\u0399",
	0x1fa0: "\u1f68\u0399",
	0x1fa1: "\u1f69\u0399",
	0x1fa2: "\u1f6a\u0399",
	0x1fa3: "\u1f6b\u0399",
	0x1fa4: "\u1f6c\u0399",
	0x1fa5: "\u1f6d\u0399",
	0x1fa6: "\u1f6e\u0399",
	0x1fa7: "\u1f6f\u0399",
	0x1fa8: "\u1f68\u0399",
	0x1fa9: "\u1f69\u0399",
	0x1faa: "\u1f6a\u0399",
	0x1fab: "\u1f6b\u0399",
	0x1fac: "\u1f6c\u0399",
	0x1fad: "\u1f6d\u0399",
	0x1fae: "\u1f6e\u0399",
	0x1faf: "\u1f6f\u0399",
	0x1fb2: "\u1fba\u0399",
	0x1fb3: "\u0391\u0399",
	0x1fb4: "\u0386\u0399",
	0x1fb6: "\u0391\u0342",
	0x1fb7: "\u0391\u0342\u0399",
	0x1fbc: "\u0391\u0399",
	0x1fc2: "\u1fca\u0399",
	0x1fc3: "\u0397\u0399",
	0x1fc4: "\u0389\u0399",
	0x1fc6: "\u0397\u0342",
	0x1fc7: "\u0397\u0342\u0399",
	0x1fcc: "\u0397\u0399",
	0x1fd2: "\u0399\u0308\u0300",
	0x1fd3: "\u0399\u0308\u0301",
	0x1fd6: "\u0399\u0342",
	0x1fd7: "\u0399\u0308\u0342",
	0x1fe2: "\u03a5\u0308\u0300",
	0x1fe3: "\u03a5\u0308\u0301",
	0x1fe4: "\u03a1\u0313",
	0x1fe6: "\u03a5\u0342",
	0x1fe7: "\u03a5\u0308\u0342",
	0x1ff2: "\u1ffa\u0399",
	0x1ff3: "\u03a9\u0399",
	0x1ff4: "\u038f\u0399",
	0x1ff6: "\u03a9\u0342",
	0x1ff7: "\u03a9\u0342\u0399",
	0x1ffc: "\u03a9\u0399",
	0xfb00: "\u0046\u0046",
	0xfb01: "\u0046\u0049",
	0xfb02: "\u0046\u004c",
	0xfb03: "\u0046\u0046\u0049",
	0xfb04: "\u0046\u0046\u004c",
	0xfb05: "\u0053\u0054",
	0xfb06: "\u0053\u0054",
	0xfb13: "\u0544\u0546",
	0xfb14: "\u0544\u0535",
	0xfb15: "\u0544\u053b",
	0xfb16: "\u054e\u0546",
	0xfb17: "\u0544\u053d",
}

// titleSpecial holds the multi-character title-case mappings.
var titleSpecial = map[rune]string{
	0xdf: "\u0053\u0073",
	0x149: "\u02bc\u004e",
	0x1f0: "\u004a\u030c",
	0x390: "\u0399\u0308\u0301",
	0x3b0: "\u03a5\u0308\u0301",
	0x587: "\u0535\u0582",
	0x1e96: "\u0048\u0331",
	0x1e97: "\u0054\u0308",
	0x1e98: "\u0057\u030a",
	0x1e99: "\u0059\u030a",
	0x1e9a: "\u0041\u02be",
	0x1f50: "\u03a5\u0313",
	0x1f52: "\u03a5\u0313\u0300",
	0x1f54: "\u03a5\u0313\u0301",
	0x1f56: "\u03a5\u0313\u0342",
	0x1fb2: "\u1fba\u0345",
	0x1fb4: "\u0386\u0345",
	0x1fb6: "\u0391\u0342",
	0x1fb7: "\u0391\u0342\u0345",
	0x1fc2: "\u1fca\u0345",
	0x1fc4: "\u0389\u0345",
	0x1fc6: "\u0397\u0342",
	0x1fc7: "\u0397\u0342\u0345",
	0x1fd2: "\u0399\u0308\u0300",
	0x1fd3: "\u0399\u0308\u0301",
	0x1fd6: "\u0399\u0342",
	0x1fd7: "\u0399\u0308\u0342",
	0x1fe2: "\u03a5\u0308\u0300",
	0x1fe3: "\u03a5\u0308\u0301",
	0x1fe4: "\u03a1\u0313",
	0x1fe6: "\u03a5\u0342",
	0x1fe7: "\u03a5\u0308\u0342",
	0x1ff2: "\u1ffa\u0345",
	0x1ff4: "\u038f\u0345",
	0x1ff6: "\u03a9\u0342",
	0x1ff7: "\u03a9\u0342\u0345",
	0xfb00: "\u0046\u0066",
	0xfb01: "\u0046\u0069",
	0xfb02: "\u0046\u006c",
	0xfb03: "\u0046\u0066\u0069",
	0xfb04: "\u0046\u0066\u006c",
	0xfb05: "\u0053\u0074",
	0xfb06: "\u0053\u0074",
	0xfb13: "\u0544\u0576",
	0xfb14: "\u0544\u0565",
	0xfb15: "\u0544\u056b",
	0xfb16: "\u054e\u0576",
	0xfb17: "\u0544\u056d",
}

// extraCaseIgnorable holds the Case_Ignorable characters outside the Mn, Me,
// Cf, Lm and Sk categories.
const extraCaseIgnorable = "\u0027\u002e\u003a\u00b7\u0387\u055f\u05f4\u2018\u2019\u2024\u2027\ufe13\ufe52\ufe55\uff07\uff0e\uff1a"
CASING_GO_EOF

find . -name '*.py' -delete
find . -type d -name '__pycache__' -prune -exec rm -rf {} +
find . -type d -empty -delete

go build ./...
rm -f titlecase
