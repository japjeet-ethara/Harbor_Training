#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod << 'TITLECASE_GO_EOF'
module titlecase

go 1.23
TITLECASE_GO_EOF

cat > main.go << 'TITLECASE_GO_EOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

// punct matches the character class used by the original Python patterns.
const punctSet = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// subphraseMarks are the delimiters that start a sub-phrase when followed by a space.
const subphraseMarks = ":.;?!-–‒—―"

type callbackFunc func(word string, allCaps bool) string

type smallSpec struct {
	lit string
	dot bool
}

// Same left-to-right order as the Python alternation a|an|...|v\.?|via|vs\.?
var smallSpecs = []smallSpec{
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

func main() {
	reader := bufio.NewReaderSize(os.Stdin, 64*1024)
	writer := bufio.NewWriter(os.Stdout)
	for {
		line, err := reader.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			line = strings.TrimSuffix(line, "\r")
			fmt.Fprintln(writer, titlecase(line))
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	if err := writer.Flush(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func titlecase(text string) string {
	return titlecaseOpt(text, nil, true, false, false)
}

func titlecaseOpt(text string, callback callbackFunc, smallFirstLast, preserveBlank, normaliseSpace bool) string {
	lines := splitLines(text, preserveBlank)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, titlecaseLine(line, callback, smallFirstLast, normaliseSpace))
	}
	return strings.Join(processed, "\n")
}

func splitLines(text string, preserveBlank bool) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	var b strings.Builder
	flush := func() {
		lines = append(lines, b.String())
		b.Reset()
	}
	rs := []rune(text)
	for i := 0; i < len(rs); i++ {
		if rs[i] == '\n' || rs[i] == '\r' {
			flush()
			if !preserveBlank {
				for i+1 < len(rs) && (rs[i+1] == '\n' || rs[i+1] == '\r') {
					i++
				}
			}
			continue
		}
		b.WriteRune(rs[i])
	}
	flush()
	return lines
}

func titlecaseLine(line string, callback callbackFunc, smallFirstLast, normaliseSpace bool) string {
	allCaps := pyUpper(line) == line
	words, spaces := splitSpaces(line)
	out := make([]string, len(words))
	frozen := make([]bool, len(words))
	for i, word := range words {
		if callback != nil {
			if replaced := callback(word, allCaps); replaced != "" {
				out[i] = replaced
				frozen[i] = true
				continue
			}
		}
		out[i] = titlecaseWord(word, callback, allCaps)
	}
	if smallFirstLast && len(out) > 0 {
		if !frozen[0] {
			out[0] = applySmallFirst(out[0])
		}
		last := len(out) - 1
		if !frozen[last] {
			out[last] = applySmallLast(out[last])
		}
	}
	var joined string
	if normaliseSpace {
		joined = strings.Join(out, " ")
	} else {
		joined = joinWords(out, spaces)
	}
	return applySubphrase(joined)
}

func titlecaseWord(word string, callback callbackFunc, allCaps bool) string {
	if allCaps && isInitialism(word) {
		return word
	}
	if replaced, ok := applyApostrophe(word); ok {
		return replaced
	}
	if prefix, rest, ok := splitMac(word); ok {
		return pyCapitalize(prefix) + titlecaseOpt(rest, callback, true, false, false)
	}
	if isHonorific(word) {
		rs := []rune(word)
		return pyUpperRune(rs[0]) + string(rs[1:])
	}
	if hasInlinePeriod(word) || (!allCaps && hasUpperElsewhere(word)) {
		return word
	}
	if isExactSmall(word, true) {
		return pyLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = titlecaseOpt(part, callback, false, false, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = titlecaseOpt(part, callback, false, false, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = pyLower(word)
	}
	if isConsonantAcronym(word) {
		return pyUpper(word)
	}
	return capFirst(word)
}

func splitSpaces(line string) (words, spaces []string) {
	var b strings.Builder
	for _, r := range line {
		if isPySpace(r) {
			words = append(words, b.String())
			b.Reset()
			spaces = append(spaces, string(r))
			continue
		}
		b.WriteRune(r)
	}
	words = append(words, b.String())
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

func isPySpace(r rune) bool {
	// Python 3 re \s. Control separators U+001C..U+001F are not in Zs.
	switch r {
	case '\t', '\n', '\v', '\f', '\r',
		'\u001c', '\u001d', '\u001e', '\u001f', '\u0085':
		return true
	}
	return unicode.Is(unicode.Zs, r) || unicode.Is(unicode.Zl, r) || unicode.Is(unicode.Zp, r)
}

// Letters and numbers added after Go 1.23's Unicode tables. Python 3.14 counts them as \w.
var extraWordRanges = [][2]rune{
	{0x1C89, 0x1C8A},
	{0xA7CB, 0xA7CD},
	{0xA7DA, 0xA7DC},
	{0x105C0, 0x105F3},
	{0x10D40, 0x10D65},
	{0x10D6F, 0x10D85},
	{0x10EC2, 0x10EC4},
	{0x11380, 0x11389},
	{0x1138B, 0x1138B},
	{0x1138E, 0x1138E},
	{0x11390, 0x113B5},
	{0x113B7, 0x113B7},
	{0x113D1, 0x113D1},
	{0x113D3, 0x113D3},
	{0x116D0, 0x116E3},
	{0x11BC0, 0x11BE0},
	{0x11BF0, 0x11BF9},
	{0x13460, 0x143FA},
	{0x16100, 0x1611D},
	{0x16130, 0x16139},
	{0x16D40, 0x16D6C},
	{0x16D70, 0x16D79},
	{0x18CFF, 0x18CFF},
	{0x1CCF0, 0x1CCF9},
	{0x1E5D0, 0x1E5ED},
	{0x1E5F0, 0x1E5FA},
	{0x2EBF0, 0x2EE5D},
}

func isWord(r rune) bool {
	// Python 3 re \w: letters, numbers, and underscore.
	if r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r) {
		return true
	}
	for _, span := range extraWordRanges {
		if r < span[0] {
			return false
		}
		if r <= span[1] {
			return true
		}
	}
	return false
}

func isPunct(r rune) bool {
	return strings.ContainsRune(punctSet, r)
}

func isSubMark(r rune) bool {
	return strings.ContainsRune(subphraseMarks, r)
}

func boundary(rs []rune, i int) bool {
	left := i > 0 && isWord(rs[i-1])
	right := i < len(rs) && isWord(rs[i])
	return left != right
}

func matchLit(rs []rune, i int, lit string, fold bool) bool {
	l := []rune(lit)
	if i+len(l) > len(rs) {
		return false
	}
	got := rs[i : i+len(l)]
	if fold {
		return pyEqFold(got, l)
	}
	return string(got) == lit
}

// pyEqFold matches Python re.IGNORECASE for a literal: Unicode case folding,
// plus the one-character equivalences i/I/İ/ı, s/S/ſ, and k/K/K.
func pyEqFold(got, pat []rune) bool {
	if len(got) != len(pat) {
		return false
	}
	for i := range got {
		if !pyRuneEq(got[i], pat[i]) {
			return false
		}
	}
	return true
}

func pyRuneEq(a, b rune) bool {
	if a == b || strings.EqualFold(string(a), string(b)) {
		return true
	}
	return foldSpecial(a) != 0 && foldSpecial(a) == foldSpecial(b)
}

func foldSpecial(r rune) rune {
	switch r {
	case 'i', 'I', '\u0130', '\u0131':
		return 'i'
	case 's', 'S', '\u017f':
		return 's'
	case 'k', 'K', '\u212a':
		return 'k'
	default:
		return 0
	}
}

// matchSmall tries the Python alternation at i. needBoundary requires \b after the match.
func matchSmall(rs []rune, i int, fold, needBoundary bool) (int, bool) {
	for _, spec := range smallSpecs {
		lit := []rune(spec.lit)
		if !matchLit(rs, i, spec.lit, fold) {
			continue
		}
		base := i + len(lit)
		cands := make([]int, 0, 2)
		if spec.dot && base < len(rs) && rs[base] == '.' {
			cands = append(cands, base+1)
		}
		cands = append(cands, base)
		for _, end := range cands {
			if !needBoundary || boundary(rs, end) {
				return end, true
			}
		}
	}
	return 0, false
}

func isExactSmall(word string, fold bool) bool {
	rs := []rune(word)
	for _, spec := range smallSpecs {
		lit := []rune(spec.lit)
		if spec.dot && len(rs) == len(lit)+1 && rs[len(lit)] == '.' && matchLit(rs, 0, spec.lit, fold) {
			return true
		}
		if len(rs) == len(lit) && matchLit(rs, 0, spec.lit, fold) {
			return true
		}
	}
	return false
}

func applySmallFirst(s string) string {
	rs := []rune(s)
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for punct := maxPunct; punct >= 0; punct-- {
		end, ok := matchSmall(rs, punct, true, true)
		if !ok {
			continue
		}
		return string(rs[:punct]) + pyCapitalize(string(rs[punct:end])) + string(rs[end:])
	}
	return s
}

func applySmallLast(s string) string {
	rs := []rune(s)
	for start := 0; start <= len(rs); start++ {
		if !boundary(rs, start) {
			continue
		}
		for _, spec := range smallSpecs {
			lit := []rune(spec.lit)
			if !matchLit(rs, start, spec.lit, true) {
				continue
			}
			base := start + len(lit)
			cands := make([]int, 0, 2)
			if spec.dot && base < len(rs) && rs[base] == '.' {
				cands = append(cands, base+1)
			}
			cands = append(cands, base)
			for _, end := range cands {
				matchEnd := -1
				if end == len(rs) {
					matchEnd = end
				} else if end == len(rs)-1 && isPunct(rs[end]) {
					matchEnd = len(rs)
				}
				if matchEnd >= 0 {
					return string(rs[:start]) + pyCapitalize(string(rs[start:matchEnd]))
				}
			}
		}
	}
	return s
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var out []rune
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && isSubMark(rs[i]) && rs[i+1] == ' ' {
			if end, ok := matchSmall(rs, i+2, false, false); ok {
				out = append(out, rs[i], rs[i+1])
				out = append(out, []rune(pyCapitalize(string(rs[i+2:end])))...)
				i = end
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

func applyApostrophe(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) {
		return "", false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return "", false
	}
	if !isWord(rs[2]) {
		return "", false
	}
	i := 3
	for i < len(rs) && isWord(rs[i]) {
		i++
	}
	if i != len(rs) {
		if i+2 != len(rs) || !isAposSuffix(rs[i]) || !isAposSuffix(rs[i+1]) {
			return "", false
		}
	}
	var first string
	if strings.ContainsRune("aeiouAEIOU", rs[0]) {
		first = pyUpperRune(rs[0])
	} else {
		first = pyLowerRune(rs[0])
	}
	var b strings.Builder
	b.WriteString(first)
	b.WriteRune(rs[1])
	b.WriteString(pyUpperRune(rs[2]))
	b.WriteString(string(rs[3:]))
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

func isAposSuffix(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func splitMac(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	restRs := rs[2:]
	if !isWord(restRs[0]) || len(restRs) < 2 {
		return "", "", false
	}
	if rs[0] == 'M' && rs[1] == 'C' {
		return "MC", string(restRs), true
	}
	if (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c' {
		return string(rs[:2]), string(restRs), true
	}
	return "", "", false
}

func isHonorific(word string) bool {
	rs := []rune(word)
	return pyEqFold(rs, []rune("mr")) || pyEqFold(rs, []rune("mrs")) ||
		pyEqFold(rs, []rune("ms")) || pyEqFold(rs, []rune("dr"))
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

func hasUpperElsewhere(word string) bool {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) && !isASCIILetter(rs[i]) {
		i++
	}
	if i >= len(rs) || !isASCIILetter(rs[i]) {
		return false
	}
	start := i
	for i < len(rs) && isASCIILetter(rs[i]) {
		i++
	}
	letters := rs[start:i]
	if len(letters) < 2 {
		return false
	}
	for _, r := range letters[1:] {
		if r >= 'A' && r <= 'Z' {
			return true
		}
	}
	return false
}

func isASCIILetter(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z')
}

func isInitialism(word string) bool {
	if word == "" || !utf8.ValidString(word) {
		return false
	}
	for i := 0; i < len(word); i++ {
		if word[i] >= 0x80 {
			return false
		}
	}
	return consumeInitials(word)
}

func consumeInitials(s string) bool {
	if s == "" {
		return true
	}
	if len(s) >= 2 && isAZ(s[0]) && s[1] == '.' && consumeInitials(s[2:]) {
		return true
	}
	if len(s) >= 3 && isAZ(s[0]) && s[1] == '.' && isAZ(s[2]) && consumeInitials(s[3:]) {
		return true
	}
	return false
}

func isAZ(b byte) bool {
	return b >= 'A' && b <= 'Z'
}

func isConsonantAcronym(word string) bool {
	rs := []rune(word)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		if !isASCIIConsonant(r) {
			return false
		}
	}
	return true
}

func isASCIIConsonant(r rune) bool {
	// Python's IGNORECASE consonant class also matches ſ (U+017F) and K (U+212A).
	switch r {
	case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z',
		'B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Z',
		'\u017f', '\u212a':
		return true
	default:
		return false
	}
}

func capFirst(word string) string {
	rs := []rune(word)
	if len(rs) == 0 {
		return word
	}
	if isWord(rs[0]) {
		return pyUpperRune(rs[0]) + string(rs[1:])
	}
	i := 0
	for i < len(rs) && isPunct(rs[i]) && !isWord(rs[i]) {
		i++
	}
	if i < len(rs) && isWord(rs[i]) {
		return pyUpper(string(rs[:i+1])) + string(rs[i+1:])
	}
	return word
}
TITLECASE_GO_EOF

cat > case.go << 'TITLECASE_GO_EOF'
package main

import (
	"strings"
	"unicode"
)

// Full Unicode case mappings used by Python 3.14 where they differ from Go's
// one-to-one mappings.
var upperSpecial = map[rune]string{
	0x00DF:  "SS",
	0x0149:  "\u02BCN",
	0x019B:  "\uA7DC",
	0x01F0:  "J\u030C",
	0x0264:  "\uA7CB",
	0x0390:  "\u0399\u0308\u0301",
	0x03B0:  "\u03A5\u0308\u0301",
	0x0587:  "\u0535\u0552",
	0x1C8A:  "\u1C89",
	0x1E96:  "H\u0331",
	0x1E97:  "T\u0308",
	0x1E98:  "W\u030A",
	0x1E99:  "Y\u030A",
	0x1E9A:  "A\u02BE",
	0x1F50:  "\u03A5\u0313",
	0x1F52:  "\u03A5\u0313\u0300",
	0x1F54:  "\u03A5\u0313\u0301",
	0x1F56:  "\u03A5\u0313\u0342",
	0x1F80:  "\u1F08\u0399",
	0x1F81:  "\u1F09\u0399",
	0x1F82:  "\u1F0A\u0399",
	0x1F83:  "\u1F0B\u0399",
	0x1F84:  "\u1F0C\u0399",
	0x1F85:  "\u1F0D\u0399",
	0x1F86:  "\u1F0E\u0399",
	0x1F87:  "\u1F0F\u0399",
	0x1F88:  "\u1F08\u0399",
	0x1F89:  "\u1F09\u0399",
	0x1F8A:  "\u1F0A\u0399",
	0x1F8B:  "\u1F0B\u0399",
	0x1F8C:  "\u1F0C\u0399",
	0x1F8D:  "\u1F0D\u0399",
	0x1F8E:  "\u1F0E\u0399",
	0x1F8F:  "\u1F0F\u0399",
	0x1F90:  "\u1F28\u0399",
	0x1F91:  "\u1F29\u0399",
	0x1F92:  "\u1F2A\u0399",
	0x1F93:  "\u1F2B\u0399",
	0x1F94:  "\u1F2C\u0399",
	0x1F95:  "\u1F2D\u0399",
	0x1F96:  "\u1F2E\u0399",
	0x1F97:  "\u1F2F\u0399",
	0x1F98:  "\u1F28\u0399",
	0x1F99:  "\u1F29\u0399",
	0x1F9A:  "\u1F2A\u0399",
	0x1F9B:  "\u1F2B\u0399",
	0x1F9C:  "\u1F2C\u0399",
	0x1F9D:  "\u1F2D\u0399",
	0x1F9E:  "\u1F2E\u0399",
	0x1F9F:  "\u1F2F\u0399",
	0x1FA0:  "\u1F68\u0399",
	0x1FA1:  "\u1F69\u0399",
	0x1FA2:  "\u1F6A\u0399",
	0x1FA3:  "\u1F6B\u0399",
	0x1FA4:  "\u1F6C\u0399",
	0x1FA5:  "\u1F6D\u0399",
	0x1FA6:  "\u1F6E\u0399",
	0x1FA7:  "\u1F6F\u0399",
	0x1FA8:  "\u1F68\u0399",
	0x1FA9:  "\u1F69\u0399",
	0x1FAA:  "\u1F6A\u0399",
	0x1FAB:  "\u1F6B\u0399",
	0x1FAC:  "\u1F6C\u0399",
	0x1FAD:  "\u1F6D\u0399",
	0x1FAE:  "\u1F6E\u0399",
	0x1FAF:  "\u1F6F\u0399",
	0x1FB2:  "\u1FBA\u0399",
	0x1FB3:  "\u0391\u0399",
	0x1FB4:  "\u0386\u0399",
	0x1FB6:  "\u0391\u0342",
	0x1FB7:  "\u0391\u0342\u0399",
	0x1FBC:  "\u0391\u0399",
	0x1FC2:  "\u1FCA\u0399",
	0x1FC3:  "\u0397\u0399",
	0x1FC4:  "\u0389\u0399",
	0x1FC6:  "\u0397\u0342",
	0x1FC7:  "\u0397\u0342\u0399",
	0x1FCC:  "\u0397\u0399",
	0x1FD2:  "\u0399\u0308\u0300",
	0x1FD3:  "\u0399\u0308\u0301",
	0x1FD6:  "\u0399\u0342",
	0x1FD7:  "\u0399\u0308\u0342",
	0x1FE2:  "\u03A5\u0308\u0300",
	0x1FE3:  "\u03A5\u0308\u0301",
	0x1FE4:  "\u03A1\u0313",
	0x1FE6:  "\u03A5\u0342",
	0x1FE7:  "\u03A5\u0308\u0342",
	0x1FF2:  "\u1FFA\u0399",
	0x1FF3:  "\u03A9\u0399",
	0x1FF4:  "\u038F\u0399",
	0x1FF6:  "\u03A9\u0342",
	0x1FF7:  "\u03A9\u0342\u0399",
	0x1FFC:  "\u03A9\u0399",
	0xA7CD:  "\uA7CC",
	0xA7DB:  "\uA7DA",
	0xFB00:  "FF",
	0xFB01:  "FI",
	0xFB02:  "FL",
	0xFB03:  "FFI",
	0xFB04:  "FFL",
	0xFB05:  "ST",
	0xFB06:  "ST",
	0xFB13:  "\u0544\u0546",
	0xFB14:  "\u0544\u0535",
	0xFB15:  "\u0544\u053B",
	0xFB16:  "\u054E\u0546",
	0xFB17:  "\u0544\u053D",
	0x10D70: "\U00010D50",
	0x10D71: "\U00010D51",
	0x10D72: "\U00010D52",
	0x10D73: "\U00010D53",
	0x10D74: "\U00010D54",
	0x10D75: "\U00010D55",
	0x10D76: "\U00010D56",
	0x10D77: "\U00010D57",
	0x10D78: "\U00010D58",
	0x10D79: "\U00010D59",
	0x10D7A: "\U00010D5A",
	0x10D7B: "\U00010D5B",
	0x10D7C: "\U00010D5C",
	0x10D7D: "\U00010D5D",
	0x10D7E: "\U00010D5E",
	0x10D7F: "\U00010D5F",
	0x10D80: "\U00010D60",
	0x10D81: "\U00010D61",
	0x10D82: "\U00010D62",
	0x10D83: "\U00010D63",
	0x10D84: "\U00010D64",
	0x10D85: "\U00010D65",
}

var lowerSpecial = map[rune]string{
	0x0130:  "i\u0307",
	0x1C89:  "\u1C8A",
	0xA7CB:  "\u0264",
	0xA7CC:  "\uA7CD",
	0xA7DA:  "\uA7DB",
	0xA7DC:  "\u019B",
	0x10D50: "\U00010D70",
	0x10D51: "\U00010D71",
	0x10D52: "\U00010D72",
	0x10D53: "\U00010D73",
	0x10D54: "\U00010D74",
	0x10D55: "\U00010D75",
	0x10D56: "\U00010D76",
	0x10D57: "\U00010D77",
	0x10D58: "\U00010D78",
	0x10D59: "\U00010D79",
	0x10D5A: "\U00010D7A",
	0x10D5B: "\U00010D7B",
	0x10D5C: "\U00010D7C",
	0x10D5D: "\U00010D7D",
	0x10D5E: "\U00010D7E",
	0x10D5F: "\U00010D7F",
	0x10D60: "\U00010D80",
	0x10D61: "\U00010D81",
	0x10D62: "\U00010D82",
	0x10D63: "\U00010D83",
	0x10D64: "\U00010D84",
	0x10D65: "\U00010D85",
}

var titleSpecial = map[rune]string{
	0x00DF:  "Ss",
	0x0149:  "\u02BCN",
	0x019B:  "\uA7DC",
	0x01F0:  "J\u030C",
	0x0264:  "\uA7CB",
	0x0390:  "\u0399\u0308\u0301",
	0x03B0:  "\u03A5\u0308\u0301",
	0x0587:  "\u0535\u0582",
	0x1C8A:  "\u1C89",
	0x1E96:  "H\u0331",
	0x1E97:  "T\u0308",
	0x1E98:  "W\u030A",
	0x1E99:  "Y\u030A",
	0x1E9A:  "A\u02BE",
	0x1F50:  "\u03A5\u0313",
	0x1F52:  "\u03A5\u0313\u0300",
	0x1F54:  "\u03A5\u0313\u0301",
	0x1F56:  "\u03A5\u0313\u0342",
	0x1FB2:  "\u1FBA\u0345",
	0x1FB4:  "\u0386\u0345",
	0x1FB6:  "\u0391\u0342",
	0x1FB7:  "\u0391\u0342\u0345",
	0x1FC2:  "\u1FCA\u0345",
	0x1FC4:  "\u0389\u0345",
	0x1FC6:  "\u0397\u0342",
	0x1FC7:  "\u0397\u0342\u0345",
	0x1FD2:  "\u0399\u0308\u0300",
	0x1FD3:  "\u0399\u0308\u0301",
	0x1FD6:  "\u0399\u0342",
	0x1FD7:  "\u0399\u0308\u0342",
	0x1FE2:  "\u03A5\u0308\u0300",
	0x1FE3:  "\u03A5\u0308\u0301",
	0x1FE4:  "\u03A1\u0313",
	0x1FE6:  "\u03A5\u0342",
	0x1FE7:  "\u03A5\u0308\u0342",
	0x1FF2:  "\u1FFA\u0345",
	0x1FF4:  "\u038F\u0345",
	0x1FF6:  "\u03A9\u0342",
	0x1FF7:  "\u03A9\u0342\u0345",
	0xA7CD:  "\uA7CC",
	0xA7DB:  "\uA7DA",
	0xFB00:  "Ff",
	0xFB01:  "Fi",
	0xFB02:  "Fl",
	0xFB03:  "Ffi",
	0xFB04:  "Ffl",
	0xFB05:  "St",
	0xFB06:  "St",
	0xFB13:  "\u0544\u0576",
	0xFB14:  "\u0544\u0565",
	0xFB15:  "\u0544\u056B",
	0xFB16:  "\u054E\u0576",
	0xFB17:  "\u0544\u056D",
	0x10D70: "\U00010D50",
	0x10D71: "\U00010D51",
	0x10D72: "\U00010D52",
	0x10D73: "\U00010D53",
	0x10D74: "\U00010D54",
	0x10D75: "\U00010D55",
	0x10D76: "\U00010D56",
	0x10D77: "\U00010D57",
	0x10D78: "\U00010D58",
	0x10D79: "\U00010D59",
	0x10D7A: "\U00010D5A",
	0x10D7B: "\U00010D5B",
	0x10D7C: "\U00010D5C",
	0x10D7D: "\U00010D5D",
	0x10D7E: "\U00010D5E",
	0x10D7F: "\U00010D5F",
	0x10D80: "\U00010D60",
	0x10D81: "\U00010D61",
	0x10D82: "\U00010D62",
	0x10D83: "\U00010D63",
	0x10D84: "\U00010D64",
	0x10D85: "\U00010D65",
}

var extraCased = map[rune]struct{}{
	0x00AA: {}, 0x00BA: {}, 0x1C89: {}, 0x1C8A: {}, 0x2160: {}, 0x2161: {},
	0x2162: {}, 0x2163: {}, 0x2164: {}, 0x2165: {}, 0x2166: {}, 0x2167: {},
	0x2168: {}, 0x2169: {}, 0x216A: {}, 0x216B: {}, 0x216C: {}, 0x216D: {},
	0x216E: {}, 0x216F: {}, 0x2170: {}, 0x2171: {}, 0x2172: {}, 0x2173: {},
	0x2174: {}, 0x2175: {}, 0x2176: {}, 0x2177: {}, 0x2178: {}, 0x2179: {},
	0x217A: {}, 0x217B: {}, 0x217C: {}, 0x217D: {}, 0x217E: {}, 0x217F: {},
	0x24B6: {}, 0x24B7: {}, 0x24B8: {}, 0x24B9: {}, 0x24BA: {}, 0x24BB: {},
	0x24BC: {}, 0x24BD: {}, 0x24BE: {}, 0x24BF: {}, 0x24C0: {}, 0x24C1: {},
	0x24C2: {}, 0x24C3: {}, 0x24C4: {}, 0x24C5: {}, 0x24C6: {}, 0x24C7: {},
	0x24C8: {}, 0x24C9: {}, 0x24CA: {}, 0x24CB: {}, 0x24CC: {}, 0x24CD: {},
	0x24CE: {}, 0x24CF: {}, 0x24D0: {}, 0x24D1: {}, 0x24D2: {}, 0x24D3: {},
	0x24D4: {}, 0x24D5: {}, 0x24D6: {}, 0x24D7: {}, 0x24D8: {}, 0x24D9: {},
	0x24DA: {}, 0x24DB: {}, 0x24DC: {}, 0x24DD: {}, 0x24DE: {}, 0x24DF: {},
	0x24E0: {}, 0x24E1: {}, 0x24E2: {}, 0x24E3: {}, 0x24E4: {}, 0x24E5: {},
	0x24E6: {}, 0x24E7: {}, 0x24E8: {}, 0x24E9: {}, 0xA7CB: {}, 0xA7CC: {},
	0xA7CD: {}, 0xA7DA: {}, 0xA7DB: {}, 0xA7DC: {}, 0x10D50: {}, 0x10D51: {},
	0x10D52: {}, 0x10D53: {}, 0x10D54: {}, 0x10D55: {}, 0x10D56: {}, 0x10D57: {},
	0x10D58: {}, 0x10D59: {}, 0x10D5A: {}, 0x10D5B: {}, 0x10D5C: {}, 0x10D5D: {},
	0x10D5E: {}, 0x10D5F: {}, 0x10D60: {}, 0x10D61: {}, 0x10D62: {}, 0x10D63: {},
	0x10D64: {}, 0x10D65: {}, 0x10D70: {}, 0x10D71: {}, 0x10D72: {}, 0x10D73: {},
	0x10D74: {}, 0x10D75: {}, 0x10D76: {}, 0x10D77: {}, 0x10D78: {}, 0x10D79: {},
	0x10D7A: {}, 0x10D7B: {}, 0x10D7C: {}, 0x10D7D: {}, 0x10D7E: {}, 0x10D7F: {},
	0x10D80: {}, 0x10D81: {}, 0x10D82: {}, 0x10D83: {}, 0x10D84: {}, 0x10D85: {},
	0x1F130: {}, 0x1F131: {}, 0x1F132: {}, 0x1F133: {}, 0x1F134: {}, 0x1F135: {},
	0x1F136: {}, 0x1F137: {}, 0x1F138: {}, 0x1F139: {}, 0x1F13A: {}, 0x1F13B: {},
	0x1F13C: {}, 0x1F13D: {}, 0x1F13E: {}, 0x1F13F: {}, 0x1F140: {}, 0x1F141: {},
	0x1F142: {}, 0x1F143: {}, 0x1F144: {}, 0x1F145: {}, 0x1F146: {}, 0x1F147: {},
	0x1F148: {}, 0x1F149: {}, 0x1F150: {}, 0x1F151: {}, 0x1F152: {}, 0x1F153: {},
	0x1F154: {}, 0x1F155: {}, 0x1F156: {}, 0x1F157: {}, 0x1F158: {}, 0x1F159: {},
	0x1F15A: {}, 0x1F15B: {}, 0x1F15C: {}, 0x1F15D: {}, 0x1F15E: {}, 0x1F15F: {},
	0x1F160: {}, 0x1F161: {}, 0x1F162: {}, 0x1F163: {}, 0x1F164: {}, 0x1F165: {},
	0x1F166: {}, 0x1F167: {}, 0x1F168: {}, 0x1F169: {}, 0x1F170: {}, 0x1F171: {},
	0x1F172: {}, 0x1F173: {}, 0x1F174: {}, 0x1F175: {}, 0x1F176: {}, 0x1F177: {},
	0x1F178: {}, 0x1F179: {}, 0x1F17A: {}, 0x1F17B: {}, 0x1F17C: {}, 0x1F17D: {},
	0x1F17E: {}, 0x1F17F: {}, 0x1F180: {}, 0x1F181: {}, 0x1F182: {}, 0x1F183: {},
	0x1F184: {}, 0x1F185: {}, 0x1F186: {}, 0x1F187: {}, 0x1F188: {}, 0x1F189: {},
}

var extraIgnorable = map[rune]struct{}{
	0x0027: {}, 0x002E: {}, 0x003A: {}, 0x00B7: {}, 0x0387: {}, 0x055F: {},
	0x05F4: {}, 0x0897: {}, 0x2018: {}, 0x2019: {}, 0x2024: {}, 0x2027: {},
	0xFE13: {}, 0xFE52: {}, 0xFE55: {}, 0xFF07: {}, 0xFF0E: {}, 0xFF1A: {},
	0x10D4E: {}, 0x10D69: {}, 0x10D6A: {}, 0x10D6B: {}, 0x10D6C: {}, 0x10D6D: {},
	0x10D6F: {}, 0x10EFC: {}, 0x113BB: {}, 0x113BC: {}, 0x113BD: {}, 0x113BE: {},
	0x113BF: {}, 0x113C0: {}, 0x113CE: {}, 0x113D0: {}, 0x113D2: {}, 0x113E1: {},
	0x113E2: {}, 0x11F5A: {}, 0x1611E: {}, 0x1611F: {}, 0x16120: {}, 0x16121: {},
	0x16122: {}, 0x16123: {}, 0x16124: {}, 0x16125: {}, 0x16126: {}, 0x16127: {},
	0x16128: {}, 0x16129: {}, 0x1612D: {}, 0x1612E: {}, 0x1612F: {}, 0x16D40: {},
	0x16D41: {}, 0x16D42: {}, 0x16D6B: {}, 0x16D6C: {}, 0x1E5EE: {}, 0x1E5EF: {},
}

func pyUpperRune(r rune) string {
	if s, ok := upperSpecial[r]; ok {
		return s
	}
	return string(unicode.ToUpper(r))
}

func pyLowerRune(r rune) string {
	if s, ok := lowerSpecial[r]; ok {
		return s
	}
	return string(unicode.ToLower(r))
}

func pyTitleRune(r rune) string {
	if s, ok := titleSpecial[r]; ok {
		return s
	}
	return string(unicode.ToTitle(r))
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(pyUpperRune(r))
	}
	return b.String()
}

func pyLower(s string) string {
	return pyLowerAt([]rune(s), 0)
}

func pyLowerAt(rs []rune, start int) string {
	var b strings.Builder
	for i := start; i < len(rs); i++ {
		if rs[i] == '\u03A3' && finalSigma(rs, i) {
			b.WriteRune('\u03C2')
			continue
		}
		b.WriteString(pyLowerRune(rs[i]))
	}
	return b.String()
}

// Python str.capitalize titles the first character and lowercases the rest.
func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return ""
	}
	return pyTitleRune(rs[0]) + pyLowerAt(rs, 1)
}

func isCased(r rune) bool {
	if _, ok := extraCased[r]; ok {
		return true
	}
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r)
}

func isCaseIgnorable(r rune) bool {
	if r == 0x1171E {
		return false
	}
	if _, ok := extraIgnorable[r]; ok {
		return true
	}
	return unicode.Is(unicode.Mn, r) || unicode.Is(unicode.Me, r) || unicode.Is(unicode.Cf, r) || unicode.Is(unicode.Lm, r) || unicode.Is(unicode.Sk, r)
}

func finalSigma(rs []rune, i int) bool {
	if i < 0 || i >= len(rs) || rs[i] != '\u03A3' {
		return false
	}
	saw := false
	for j := i - 1; j >= 0; j-- {
		if isCased(rs[j]) {
			saw = true
			break
		}
		if !isCaseIgnorable(rs[j]) {
			break
		}
	}
	if !saw {
		return false
	}
	for j := i + 1; j < len(rs); j++ {
		if isCased(rs[j]) {
			return false
		}
		if !isCaseIgnorable(rs[j]) {
			break
		}
	}
	return true
}
TITLECASE_GO_EOF

find /workspace/repo -name '*.py' -type f -delete
# The module binary is named titlecase. The old package directory would block go build.
rm -rf /workspace/repo/titlecase
