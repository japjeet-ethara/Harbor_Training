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
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		chunk, err := in.ReadBytes('\n')
		if len(chunk) > 0 {
			if chunk[len(chunk)-1] == '\n' {
				chunk = chunk[:len(chunk)-1]
			}
			if len(chunk) > 0 && chunk[len(chunk)-1] == '\r' {
				chunk = chunk[:len(chunk)-1]
			}
			if _, werr := out.WriteString(titlecase(string(chunk), true)); werr != nil {
				os.Exit(1)
			}
			if werr := out.WriteByte('\n'); werr != nil {
				os.Exit(1)
			}
		}
		if err != nil {
			if err == io.EOF {
				break
			}
			os.Exit(1)
		}
	}
}

// titlecase is the default-argument port of Python titlecase().
// smallFirstLast is the recursive flag; callback, blank-line preservation,
// and space normalisation stay at their defaults (off, off, off).
func titlecase(text string, smallFirstLast bool) string {
	lines := splitRuns(text, func(r rune) bool { return r == '\r' || r == '\n' })
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		allCaps := pyUpper(line) == line
		words, spaces := splitSpaces(line)
		tc := make([]string, len(words))
		for i, word := range words {
			tc[i] = convertWord(word, allCaps)
		}
		if smallFirstLast && len(tc) > 0 {
			tc[0] = applySmallFirst(tc[0])
			tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
		}
		processed = append(processed, applySubphrase(joinWords(tc, spaces)))
	}
	return strings.Join(processed, "\n")
}

func convertWord(word string, allCaps bool) string {
	if allCaps && isUCInitials(word) {
		return word
	}
	if transformed, ok := applyApos(word); ok {
		return transformed
	}
	if prefix, rest, ok := matchMac(word); ok {
		return pyCapitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		r, size := utf8.DecodeRuneInString(word)
		if r == utf8.RuneError && size == 0 {
			return word
		}
		return pyUpper(string(r)) + word[size:]
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
	if allConsonants(word) && utf8.RuneCountInString(word) > 2 {
		return pyUpper(word)
	}
	return capFirst(word)
}

func splitRuns(text string, sep func(rune) bool) []string {
	if text == "" {
		return []string{""}
	}
	var parts []string
	start := 0
	i := 0
	for i < len(text) {
		r, size := utf8.DecodeRuneInString(text[i:])
		if sep(r) {
			parts = append(parts, text[start:i])
			for i < len(text) {
				r, size = utf8.DecodeRuneInString(text[i:])
				if !sep(r) {
					break
				}
				i += size
			}
			start = i
			continue
		}
		i += size
	}
	parts = append(parts, text[start:])
	return parts
}

func splitSpaces(line string) (words, spaces []string) {
	var cur strings.Builder
	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, cur.String())
			cur.Reset()
			spaces = append(spaces, string(r))
			continue
		}
		cur.WriteRune(r)
	}
	words = append(words, cur.String())
	return words, spaces
}

func joinWords(words, spaces []string) string {
	n := len(words) + len(spaces)
	joined := make([]string, n)
	copy(joined, words)
	if len(spaces) > 0 {
		copy(joined[len(words):], spaces)
	}
	wi := 0
	for i := 0; i < n && wi < len(words); i += 2 {
		joined[i] = words[wi]
		wi++
	}
	si := 0
	for i := 1; i < n && si < len(spaces); i += 2 {
		joined[i] = spaces[si]
		si++
	}
	return strings.Join(joined, "")
}

func capFirst(s string) string {
	rs := []rune(s)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return s
	}
	return pyUpper(string(rs[:i+1])) + string(rs[i+1:])
}

func hasInlinePeriod(s string) bool {
	rs := []rune(s)
	for i := 0; i+2 < len(rs); i++ {
		if unicode.IsLetter(rs[i]) && rs[i+1] == '.' && unicode.IsLetter(rs[i+2]) {
			return true
		}
	}
	return false
}

func hasUCElsewhere(s string) bool {
	rs := []rune(s)
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for p := 0; p <= maxPunct; p++ {
		if p >= len(rs) || !unicode.IsLetter(rs[p]) {
			continue
		}
		for j := p + 1; j < len(rs); j++ {
			if !unicode.IsLetter(rs[j]) {
				break
			}
			if unicode.IsUpper(rs[j]) {
				return true
			}
		}
	}
	return false
}

func isUCInitials(s string) bool {
	if s == "" {
		return false
	}
	return initialsFrom(s, 0)
}

func initialsFrom(s string, i int) bool {
	if i == len(s) {
		return true
	}
	r, size := utf8.DecodeRuneInString(s[i:])
	if !unicode.IsUpper(r) {
		return false
	}
	j := i + size
	if j >= len(s) || s[j] != '.' {
		return false
	}
	j++
	if initialsFrom(s, j) {
		return true
	}
	if j >= len(s) {
		return false
	}
	r2, size2 := utf8.DecodeRuneInString(s[j:])
	if !unicode.IsUpper(r2) {
		return false
	}
	return initialsFrom(s, j+size2)
}

func applyApos(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) || (rs[1] != '\'' && rs[1] != '\u2018') {
		return "", false
	}
	i := 2
	if !unicode.IsLetter(rs[i]) {
		return "", false
	}
	for i < len(rs) && unicode.IsLetter(rs[i]) {
		i++
	}
	if i != len(rs) {
		if len(rs)-i != 2 || !isAposTail(rs[i]) || !isAposTail(rs[i+1]) {
			return "", false
		}
	}
	var b strings.Builder
	if isASCIIVowel(rs[0]) {
		b.WriteString(pyUpper(string(rs[0])))
	} else {
		b.WriteString(pyLower(string(rs[0])))
	}
	b.WriteRune(rs[1])
	b.WriteString(pyUpper(string(rs[2])))
	for _, r := range rs[3:] {
		b.WriteRune(r)
	}
	return b.String(), true
}

func isDOL(r rune) bool {
	switch r {
	case 'd', 'D', 'o', 'O', 'l', 'L':
		return true
	default:
		return false
	}
}

func isASCIIVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func isAposTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func matchMac(s string) (prefix, rest string, ok bool) {
	rs := []rune(s)
	if len(rs) < 4 {
		return "", "", false
	}
	mc := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c'
	MC := rs[0] == 'M' && rs[1] == 'C'
	if !mc && !MC {
		return "", "", false
	}
	if !isWord(rs[2]) {
		return "", "", false
	}
	end := len(rs)
	for i := 2; i < len(rs); i++ {
		if rs[i] == '\n' {
			end = i
			break
		}
	}
	if end < 4 {
		return "", "", false
	}
	return string(rs[:2]), string(rs[2:end]), true
}

func isHonorific(s string) bool {
	switch strings.ToLower(s) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func isSmallWord(s string) bool {
	switch strings.ToLower(s) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

func allConsonants(s string) bool {
	if s == "" {
		return false
	}
	for _, r := range s {
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

func applySmallFirst(s string) string {
	punct := 0
	for punct < len(s) {
		r, size := utf8.DecodeRuneInString(s[punct:])
		if !isPunct(r) {
			break
		}
		punct += size
	}
	n := matchSmallPrefix(s[punct:])
	if n < 0 {
		return s
	}
	return s[:punct] + pyCapitalize(s[punct:punct+n]) + s[punct+n:]
}

func applySmallLast(s string) string {
	if s == "" {
		return s
	}
	if r, size := utf8.DecodeLastRuneInString(s); isPunct(r) {
		head := s[:len(s)-size]
		if n := matchSmallSuffix(head); n >= 0 {
			start := len(head) - n
			return s[:start] + pyCapitalize(s[start:])
		}
	}
	if n := matchSmallSuffix(s); n >= 0 {
		start := len(s) - n
		return s[:start] + pyCapitalize(s[start:])
	}
	return s
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(rs) {
		if i+1 < len(rs) && isSubphraseMark(rs[i]) && rs[i+1] == ' ' {
			if n := matchSmallExact(rs[i+2:]); n > 0 {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2 : i+2+n])))
				i += 2 + n
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

var smallFixed = []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to"}

func matchSmallPrefix(s string) int {
	for _, alt := range smallFixed {
		if n, ok := foldPrefixLen(s, alt); ok && isBoundary(s, n) {
			return n
		}
	}
	if n := matchVDotPrefix(s, "v"); n >= 0 {
		return n
	}
	if n, ok := foldPrefixLen(s, "via"); ok && isBoundary(s, n) {
		return n
	}
	if n := matchVDotPrefix(s, "vs"); n >= 0 {
		return n
	}
	return -1
}

func matchVDotPrefix(s, base string) int {
	n, ok := foldPrefixLen(s, base)
	if !ok {
		return -1
	}
	if n < len(s) {
		r, size := utf8.DecodeRuneInString(s[n:])
		if r == '.' && isBoundary(s, n+size) {
			return n + size
		}
	}
	if isBoundary(s, n) {
		return n
	}
	return -1
}

func matchSmallSuffix(s string) int {
	try := func(alt string) int {
		n, ok := foldSuffixLen(s, alt)
		if ok && isBoundary(s, len(s)-n) {
			return n
		}
		return -1
	}
	for _, alt := range smallFixed {
		if n := try(alt); n >= 0 {
			return n
		}
	}
	if n, ok := foldSuffixLen(s, "v."); ok && isBoundary(s, len(s)-n) {
		return n
	}
	if n := try("v"); n >= 0 {
		return n
	}
	if n := try("via"); n >= 0 {
		return n
	}
	if n, ok := foldSuffixLen(s, "vs."); ok && isBoundary(s, len(s)-n) {
		return n
	}
	if n := try("vs"); n >= 0 {
		return n
	}
	return -1
}

func matchSmallExact(rs []rune) int {
	try := func(alt string) int {
		ar := []rune(alt)
		if len(rs) < len(ar) {
			return -1
		}
		for i, a := range ar {
			if rs[i] != a {
				return -1
			}
		}
		return len(ar)
	}
	for _, alt := range smallFixed {
		if n := try(alt); n >= 0 {
			return n
		}
	}
	if len(rs) > 0 && rs[0] == 'v' {
		if len(rs) > 1 && rs[1] == '.' {
			return 2
		}
		return 1
	}
	if n := try("via"); n >= 0 {
		return n
	}
	if len(rs) >= 2 && rs[0] == 'v' && rs[1] == 's' {
		if len(rs) >= 3 && rs[2] == '.' {
			return 3
		}
		return 2
	}
	return -1
}

func foldPrefixLen(s, alt string) (int, bool) {
	i := 0
	for _, a := range alt {
		if i >= len(s) {
			return 0, false
		}
		r, size := utf8.DecodeRuneInString(s[i:])
		if unicode.ToLower(r) != unicode.ToLower(a) {
			return 0, false
		}
		i += size
	}
	return i, true
}

func foldSuffixLen(s, alt string) (int, bool) {
	sr := []rune(s)
	ar := []rune(alt)
	if len(sr) < len(ar) {
		return 0, false
	}
	start := len(sr) - len(ar)
	for i, a := range ar {
		if unicode.ToLower(sr[start+i]) != unicode.ToLower(a) {
			return 0, false
		}
	}
	n := 0
	for _, r := range sr[start:] {
		n += utf8.RuneLen(r)
	}
	return n, true
}

func isBoundary(s string, i int) bool {
	prevWord := false
	nextWord := false
	if i > 0 {
		r, _ := utf8.DecodeLastRuneInString(s[:i])
		prevWord = isWord(r)
	}
	if i < len(s) {
		r, _ := utf8.DecodeRuneInString(s[i:])
		nextWord = isWord(r)
	}
	return prevWord != nextWord
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsNumber(r) || r == '_'
}

func isPunct(r rune) bool {
	_, ok := punct[r]
	return ok
}

func isSubphraseMark(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2013', '\u2012', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func pyUpper(s string) string { return mapCase(s, 0) }
func pyLower(s string) string { return mapCase(s, 1) }

func mapCase(s string, which int) string {
	var b strings.Builder
	for _, r := range s {
		if pair, ok := pyCase[r]; ok {
			b.WriteString(pair[which])
			continue
		}
		one := string(r)
		if which == 0 {
			b.WriteString(strings.ToUpper(one))
		} else {
			b.WriteString(strings.ToLower(one))
		}
	}
	return b.String()
}

func pyCapitalize(s string) string {
	if s == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	up := pyUpper(string(r))
	rest := pyLower(s[size:])
	if up == "" {
		return rest
	}
	_, first := utf8.DecodeRuneInString(up)
	return up[:first] + pyLower(up[first:]) + rest
}

var punct = map[rune]struct{}{}

func init() {
	for _, r := range "!\"\u201c#$%&'\u2018()*+,\\-\u2013\u2012\u2014\u2015./:;?@[]_`{|}~" {
		punct[r] = struct{}{}
	}
}
var pyCase = map[rune][2]string{
	0xDF: {"SS", "ß"},
	0x130: {"İ", "i̇"},
	0x149: {"ʼN", "ŉ"},
	0x1F0: {"J̌", "ǰ"},
	0x390: {"Ϊ́", "ΐ"},
	0x3B0: {"Ϋ́", "ΰ"},
	0x587: {"ԵՒ", "և"},
	0x1E96: {"H̱", "ẖ"},
	0x1E97: {"T̈", "ẗ"},
	0x1E98: {"W̊", "ẘ"},
	0x1E99: {"Y̊", "ẙ"},
	0x1E9A: {"Aʾ", "ẚ"},
	0x1F50: {"Υ̓", "ὐ"},
	0x1F52: {"Υ̓̀", "ὒ"},
	0x1F54: {"Υ̓́", "ὔ"},
	0x1F56: {"Υ̓͂", "ὖ"},
	0x1F80: {"ἈΙ", "ᾀ"},
	0x1F81: {"ἉΙ", "ᾁ"},
	0x1F82: {"ἊΙ", "ᾂ"},
	0x1F83: {"ἋΙ", "ᾃ"},
	0x1F84: {"ἌΙ", "ᾄ"},
	0x1F85: {"ἍΙ", "ᾅ"},
	0x1F86: {"ἎΙ", "ᾆ"},
	0x1F87: {"ἏΙ", "ᾇ"},
	0x1F88: {"ἈΙ", "ᾀ"},
	0x1F89: {"ἉΙ", "ᾁ"},
	0x1F8A: {"ἊΙ", "ᾂ"},
	0x1F8B: {"ἋΙ", "ᾃ"},
	0x1F8C: {"ἌΙ", "ᾄ"},
	0x1F8D: {"ἍΙ", "ᾅ"},
	0x1F8E: {"ἎΙ", "ᾆ"},
	0x1F8F: {"ἏΙ", "ᾇ"},
	0x1F90: {"ἨΙ", "ᾐ"},
	0x1F91: {"ἩΙ", "ᾑ"},
	0x1F92: {"ἪΙ", "ᾒ"},
	0x1F93: {"ἫΙ", "ᾓ"},
	0x1F94: {"ἬΙ", "ᾔ"},
	0x1F95: {"ἭΙ", "ᾕ"},
	0x1F96: {"ἮΙ", "ᾖ"},
	0x1F97: {"ἯΙ", "ᾗ"},
	0x1F98: {"ἨΙ", "ᾐ"},
	0x1F99: {"ἩΙ", "ᾑ"},
	0x1F9A: {"ἪΙ", "ᾒ"},
	0x1F9B: {"ἫΙ", "ᾓ"},
	0x1F9C: {"ἬΙ", "ᾔ"},
	0x1F9D: {"ἭΙ", "ᾕ"},
	0x1F9E: {"ἮΙ", "ᾖ"},
	0x1F9F: {"ἯΙ", "ᾗ"},
	0x1FA0: {"ὨΙ", "ᾠ"},
	0x1FA1: {"ὩΙ", "ᾡ"},
	0x1FA2: {"ὪΙ", "ᾢ"},
	0x1FA3: {"ὫΙ", "ᾣ"},
	0x1FA4: {"ὬΙ", "ᾤ"},
	0x1FA5: {"ὭΙ", "ᾥ"},
	0x1FA6: {"ὮΙ", "ᾦ"},
	0x1FA7: {"ὯΙ", "ᾧ"},
	0x1FA8: {"ὨΙ", "ᾠ"},
	0x1FA9: {"ὩΙ", "ᾡ"},
	0x1FAA: {"ὪΙ", "ᾢ"},
	0x1FAB: {"ὫΙ", "ᾣ"},
	0x1FAC: {"ὬΙ", "ᾤ"},
	0x1FAD: {"ὭΙ", "ᾥ"},
	0x1FAE: {"ὮΙ", "ᾦ"},
	0x1FAF: {"ὯΙ", "ᾧ"},
	0x1FB2: {"ᾺΙ", "ᾲ"},
	0x1FB3: {"ΑΙ", "ᾳ"},
	0x1FB4: {"ΆΙ", "ᾴ"},
	0x1FB6: {"Α͂", "ᾶ"},
	0x1FB7: {"Α͂Ι", "ᾷ"},
	0x1FBC: {"ΑΙ", "ᾳ"},
	0x1FC2: {"ῊΙ", "ῂ"},
	0x1FC3: {"ΗΙ", "ῃ"},
	0x1FC4: {"ΉΙ", "ῄ"},
	0x1FC6: {"Η͂", "ῆ"},
	0x1FC7: {"Η͂Ι", "ῇ"},
	0x1FCC: {"ΗΙ", "ῃ"},
	0x1FD2: {"Ϊ̀", "ῒ"},
	0x1FD3: {"Ϊ́", "ΐ"},
	0x1FD6: {"Ι͂", "ῖ"},
	0x1FD7: {"Ϊ͂", "ῗ"},
	0x1FE2: {"Ϋ̀", "ῢ"},
	0x1FE3: {"Ϋ́", "ΰ"},
	0x1FE4: {"Ρ̓", "ῤ"},
	0x1FE6: {"Υ͂", "ῦ"},
	0x1FE7: {"Ϋ͂", "ῧ"},
	0x1FF2: {"ῺΙ", "ῲ"},
	0x1FF3: {"ΩΙ", "ῳ"},
	0x1FF4: {"ΏΙ", "ῴ"},
	0x1FF6: {"Ω͂", "ῶ"},
	0x1FF7: {"Ω͂Ι", "ῷ"},
	0x1FFC: {"ΩΙ", "ῳ"},
	0xFB00: {"FF", "ﬀ"},
	0xFB01: {"FI", "ﬁ"},
	0xFB02: {"FL", "ﬂ"},
	0xFB03: {"FFI", "ﬃ"},
	0xFB04: {"FFL", "ﬄ"},
	0xFB05: {"ST", "ﬅ"},
	0xFB06: {"ST", "ﬆ"},
	0xFB13: {"ՄՆ", "ﬓ"},
	0xFB14: {"ՄԵ", "ﬔ"},
	0xFB15: {"ՄԻ", "ﬕ"},
	0xFB16: {"ՎՆ", "ﬖ"},
	0xFB17: {"ՄԽ", "ﬗ"},
}

EOF
find . -type f -name '*.py' -delete
# The module path's last element is the go build ./... binary name.
# The Python package directory would occupy that name and fail the build.
rm -rf titlecase
