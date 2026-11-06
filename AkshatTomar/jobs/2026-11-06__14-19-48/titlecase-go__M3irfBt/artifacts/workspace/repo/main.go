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
