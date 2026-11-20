// titlecase: a Go rewrite of python-titlecase 2.4.1 (titlecase(text) with default
// arguments, `regex` package available).
//
// Reads lines from stdin, writes one titlecased line per input line to stdout.
//
// The original leans on regular expression features Go does not have (look-ahead,
// back-references, Unicode-aware \b, ordered alternation with backtracking). Every
// pattern is therefore re-implemented as plain rune scanning below, each function
// named after the pattern it stands in for.
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

// PUNCT from the original: the characters that may sit in front of a word's first letter.
const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// Characters that may open a sub-phrase when followed by a plain space (SUBPHRASE).
const subphraseOpeners = ":.;?!-–‒—―"

// Alternatives of SMALL in the order the regex tries them. A trailing "." marks an
// optional dot (v\.? and vs\.?); the dotted form is tried first, like a greedy "?".
var smallAlternatives = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or",
	"the", "to", "v.", "via", "vs.",
}

// Code points whose Python str.upper() is more than one character. Go's unicode.ToUpper
// leaves them unchanged, so they are listed here (from Python's Unicode database).
var multiUpper = map[rune]string{
	'ß': "SS", 'ŉ': "ʼN", 'ǰ': "J̌", 'ΐ': "Ϊ́", 'ΰ': "Ϋ́", 'և': "ԵՒ",
	'ẖ': "H̱", 'ẗ': "T̈", 'ẘ': "W̊", 'ẙ': "Y̊", 'ẚ': "Aʾ",
	'ﬀ': "FF", 'ﬁ': "FI", 'ﬂ': "FL", 'ﬃ': "FFI", 'ﬄ': "FFL", 'ﬅ': "ST", 'ﬆ': "ST",
	'ﬓ': "ՄՆ", 'ﬔ': "ՄԵ", 'ﬕ': "ՄԻ", 'ﬖ': "ՎՆ", 'ﬗ': "ՄԽ",
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) == 0 && err != nil {
			return
		}
		line = strings.TrimSuffix(line, "\n")
		out.WriteString(titlecase(line, true))
		out.WriteByte('\n')
		if err != nil {
			return
		}
	}
}

// ---- character classes -----------------------------------------------------------------

func isPunct(r rune) bool       { return strings.ContainsRune(punctChars, r) }
func isLetter(r rune) bool      { return unicode.IsLetter(r) }
func isUpperLetter(r rune) bool { return unicode.Is(unicode.Lu, r) }

// isWordChar stands in for \w of the regex module: letters, marks, decimal digits,
// connector punctuation, letter numbers, other alphabetic symbols and the two joiners.
func isWordChar(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsMark(r) || unicode.Is(unicode.Nd, r) ||
		unicode.Is(unicode.Pc, r) || unicode.Is(unicode.Nl, r) ||
		unicode.Is(unicode.Other_Alphabetic, r) || r == 0x200C || r == 0x200D
}

func isConsonant(r rune) bool {
	return strings.ContainsRune("bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ", r)
}

// ---- Python string methods -------------------------------------------------------------

func upperRune(r rune) string {
	if s, ok := multiUpper[r]; ok {
		return s
	}
	return string(unicode.ToUpper(r))
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		b.WriteString(upperRune(r))
	}
	return b.String()
}

// pyLower is str.lower() for everything but the Greek final sigma rule (see NOTES.md).
func pyLower(s string) string {
	var b strings.Builder
	for _, r := range s {
		if r == 'İ' {
			b.WriteString("i̇")
			continue
		}
		b.WriteRune(unicode.ToLower(r))
	}
	return b.String()
}

// capitalize is str.capitalize(): first rune to title case, the rest to lower case.
func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	return string(unicode.ToTitle(rs[0])) + pyLower(string(rs[1:]))
}

// ---- the line -----------------------------------------------------------------------------

// titlecase is the original titlecase(text, small_first_last=...) for a text without
// line breaks. smallFirstLast is false when called on a piece of a hyphenated or slashed
// word, true for a whole line and for the tail of a "Mc" word.
func titlecase(text string, smallFirstLast bool) string {
	rs := []rune(text)

	// regex.split(r'(\s)', line): words and the single whitespace runes between them.
	var words []string
	var gaps []rune
	start := 0
	for i, r := range rs {
		if unicode.IsSpace(r) {
			words = append(words, string(rs[start:i]))
			gaps = append(gaps, r)
			start = i + 1
		}
	}
	words = append(words, string(rs[start:]))

	allCaps := pyUpper(text) == text

	done := make([]string, len(words))
	for i, w := range words {
		done[i] = titlecaseWord(w, allCaps)
	}

	if smallFirstLast {
		done[0] = smallFirst(done[0])
		done[len(done)-1] = smallLast(done[len(done)-1])
	}

	var b strings.Builder
	for i, w := range done {
		b.WriteString(w)
		if i < len(gaps) {
			b.WriteRune(gaps[i])
		}
	}
	return subphrase(b.String())
}

// titlecaseWord is the body of the per-word loop. The checks run in the original's order;
// the first that applies decides.
func titlecaseWord(word string, allCaps bool) string {
	rs := []rune(word)

	if allCaps && isInitials(rs) {
		return word
	}

	if isAposSecond(rs) {
		var first string
		if strings.ContainsRune("aeiouAEIOU", rs[0]) {
			first = upperRune(rs[0])
		} else {
			first = pyLower(string(rs[0]))
		}
		return first + string(rs[1]) + upperRune(rs[2]) + string(rs[3:])
	}

	if isMacMc(rs) {
		return capitalize(string(rs[:2])) + titlecase(string(rs[2:]), true)
	}

	if isMrMrsMsDr(word) {
		return upperRune(rs[0]) + string(rs[1:])
	}

	if hasInlinePeriod(rs) || (!allCaps && hasUpperElsewhere(rs)) {
		return word
	}

	if isSmallWord(word) {
		return pyLower(word)
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		return rejoin(word, "/")
	}
	if strings.Contains(word, "-") {
		return rejoin(word, "-")
	}

	if allCaps {
		word = pyLower(word)
		rs = []rune(word)
	}

	// Three or more letters, all consonants (y does not count): an acronym.
	if len(rs) > 2 {
		acronym := true
		for _, r := range rs {
			if !isConsonant(r) {
				acronym = false
				break
			}
		}
		if acronym {
			return pyUpper(word)
		}
	}

	return capFirst(rs)
}

// rejoin splits a word on sep and titlecases every piece on its own.
func rejoin(word, sep string) string {
	parts := strings.Split(word, sep)
	for i, p := range parts {
		parts[i] = titlecase(p, false)
	}
	return strings.Join(parts, sep)
}

// ---- the patterns -------------------------------------------------------------------------

// isInitials: UC_INITIALS, ^(?:[Lu]\.|[Lu]\.[Lu])+$
func isInitials(rs []rune) bool {
	return len(rs) > 0 && initialsFrom(rs, 0)
}

func initialsFrom(rs []rune, i int) bool {
	if i == len(rs) {
		return true
	}
	if i+1 < len(rs) && isUpperLetter(rs[i]) && rs[i+1] == '.' {
		if initialsFrom(rs, i+2) {
			return true
		}
		if i+2 < len(rs) && isUpperLetter(rs[i+2]) && initialsFrom(rs, i+3) {
			return true
		}
	}
	return false
}

// isAposSecond: APOS_SECOND, ^[dol]['‘][\p{Letter}]+(?:['s]{2})?$ , case-insensitive.
func isAposSecond(rs []rune) bool {
	if len(rs) < 3 || !strings.ContainsRune("dolDOL", rs[0]) || (rs[1] != '\'' && rs[1] != '‘') {
		return false
	}
	tail := rs[2:]
	if allLetters(tail) {
		return true
	}
	n := len(tail)
	return n >= 3 && allLetters(tail[:n-2]) && isAposTail(tail[n-2]) && isAposTail(tail[n-1])
}

func allLetters(rs []rune) bool {
	for _, r := range rs {
		if !isLetter(r) {
			return false
		}
	}
	return true
}

func isAposTail(r rune) bool { return r == '\'' || r == 's' || r == 'S' }

// isMacMc: MAC_MC, ^([Mm]c|MC)(\w.+)
func isMacMc(rs []rune) bool {
	if len(rs) < 4 {
		return false
	}
	head := string(rs[:2])
	return (head == "Mc" || head == "mc" || head == "MC") && isWordChar(rs[2])
}

// isMrMrsMsDr: MR_MRS_MS_DR, ^((m((rs?)|s))|Dr)$ , case-insensitive.
func isMrMrsMsDr(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

// hasInlinePeriod: INLINE_PERIOD, a letter, a dot and a letter anywhere in the word.
func hasInlinePeriod(rs []rune) bool {
	for i := 1; i+1 < len(rs); i++ {
		if rs[i] == '.' && isLetter(rs[i-1]) && isLetter(rs[i+1]) {
			return true
		}
	}
	return false
}

// hasUpperElsewhere: UC_ELSEWHERE, [PUNCT]*?[\p{Letter}]+[\p{Uppercase_Letter}]+? anchored
// at the start: after any leading punctuation, the first run of letters has an upper-case
// letter somewhere after its first letter.
func hasUpperElsewhere(rs []rune) bool {
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !isLetter(rs[i]) {
		return false
	}
	for j := i + 1; j < len(rs) && isLetter(rs[j]); j++ {
		if isUpperLetter(rs[j]) {
			return true
		}
	}
	return false
}

// isSmallWord: SMALL_WORDS, the whole word is one small word, case-insensitive.
func isSmallWord(word string) bool {
	rs := []rune(word)
	for _, n := range smallMatches(rs, 0, true) {
		if n == len(rs) {
			return true
		}
	}
	return false
}

// capFirst: CAPFIRST, upper-case the first letter that follows any leading punctuation.
func capFirst(rs []rune) string {
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i < len(rs) && isLetter(rs[i]) {
		return string(rs[:i]) + upperRune(rs[i]) + string(rs[i+1:])
	}
	return string(rs)
}

// smallMatches returns the lengths of every SMALL alternative that matches at position i,
// in the order the regex engine would try them (so the caller can take the first one whose
// continuation also matches, exactly like backtracking).
func smallMatches(rs []rune, i int, ignoreCase bool) []int {
	var lengths []int
	for _, alt := range smallAlternatives {
		base := strings.TrimSuffix(alt, ".")
		if !prefixAt(rs, i, base, ignoreCase) {
			continue
		}
		n := len(base)
		if strings.HasSuffix(alt, ".") && i+n < len(rs) && rs[i+n] == '.' {
			lengths = append(lengths, n+1)
		}
		lengths = append(lengths, n)
	}
	return lengths
}

func prefixAt(rs []rune, i int, s string, ignoreCase bool) bool {
	for _, c := range s {
		if i >= len(rs) {
			return false
		}
		r := rs[i]
		if ignoreCase {
			r = unicode.ToLower(r)
		}
		if r != c {
			return false
		}
		i++
	}
	return true
}

// wordBoundary is \b between positions i-1 and i.
func wordBoundary(rs []rune, i int) bool {
	before := i > 0 && isWordChar(rs[i-1])
	after := i < len(rs) && isWordChar(rs[i])
	return before != after
}

// smallFirst: SMALL_FIRST, ^([PUNCT]*)(SMALL)\b , case-insensitive; the small word is
// capitalised. Applied to the first word of a line.
func smallFirst(word string) string {
	rs := []rune(word)
	p := 0
	for p < len(rs) && isPunct(rs[p]) {
		p++
	}
	for _, n := range smallMatches(rs, p, true) {
		if wordBoundary(rs, p+n) {
			return string(rs[:p]) + capitalize(string(rs[p:p+n])) + string(rs[p+n:])
		}
	}
	return word
}

// smallLast: SMALL_LAST, \b(SMALL)[PUNCT]?$ , case-insensitive; the whole match (small
// word plus the optional punctuation) is capitalised. Applied to the last word of a line.
func smallLast(word string) string {
	rs := []rune(word)
	for i := 0; i <= len(rs); i++ {
		if !wordBoundary(rs, i) {
			continue
		}
		for _, n := range smallMatches(rs, i, true) {
			end := i + n
			if end+1 == len(rs) && isPunct(rs[end]) {
				return string(rs[:i]) + capitalize(string(rs[i:]))
			}
			if end == len(rs) {
				return string(rs[:i]) + capitalize(string(rs[i:]))
			}
		}
	}
	return word
}

// subphrase: SUBPHRASE, ([:.;?!\-–‒—―][ ])(SMALL) replaced everywhere, case-sensitive: a
// small word that opens a new sub-phrase is capitalised. Applied to the joined line.
func subphrase(line string) string {
	rs := []rune(line)
	out := make([]rune, 0, len(rs))
	for i := 0; i < len(rs); {
		if i+2 < len(rs) && strings.ContainsRune(subphraseOpeners, rs[i]) && rs[i+1] == ' ' {
			if lengths := smallMatches(rs, i+2, false); len(lengths) > 0 {
				n := lengths[0]
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
