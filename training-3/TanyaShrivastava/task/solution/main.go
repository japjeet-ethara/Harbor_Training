// Command titlecase is a Go port of python-titlecase (v2.4.1, `regex` module
// semantics). It reads one title per line on stdin and writes the titlecased
// line on stdout.
//
// Go's regexp package has no look-around / Unicode-aware \b, so every pattern
// of the Python original is re-implemented here as explicit rune code.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

// PUNCT from the Python source: the characters of the class
//
//	[!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~]
//
// Note that the curly ’ and ” are NOT part of it.
const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// Characters that may precede a small word in SUBPHRASE: [:.;?!\-–‒—―]
const subphrasePunct = ":.;?!-–‒—―"

// SMALL alternation, in the exact order of the Python pattern
// (`v\.?` and `vs\.?` are greedy, so the dotted form is tried first).
var smallAlts = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
	"on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

// ---------------------------------------------------------------- predicates

func isPunct(r rune) bool { return strings.ContainsRune(punctChars, r) }

// \s of the `regex` module: the Unicode White_Space property.
func isSpace(r rune) bool { return unicode.IsSpace(r) }

// \w: letters, marks, decimal digits, connector punctuation (_).
func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsMark(r) || unicode.Is(unicode.Nd, r) ||
		unicode.Is(unicode.Pc, r)
}

func isLetter(r rune) bool { return unicode.IsLetter(r) }
func isUpper(r rune) bool  { return unicode.Is(unicode.Lu, r) }

// foldIn reports whether r equals (under simple case folding) any rune of set.
func foldIn(r rune, set string) bool {
	for f := unicode.SimpleFold(r); ; f = unicode.SimpleFold(f) {
		if strings.ContainsRune(set, f) {
			return true
		}
		if f == r {
			return false
		}
	}
}

// \b: a boundary lies between a word and a non-word character (or an end).
func boundary(rs []rune, p int) bool {
	left := p > 0 && isWord(rs[p-1])
	right := p < len(rs) && isWord(rs[p])
	return left != right
}

// ------------------------------------------------------------------ casing

func upper(s string) string { return strings.ToUpper(s) }
func lower(s string) string { return strings.ToLower(s) }

// capitalize mirrors Python's str.capitalize(): first rune to title case,
// every other rune to lower case.
func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return ""
	}
	return string(unicode.ToTitle(rs[0])) + lower(string(rs[1:]))
}

// hasFoldPrefix: rs[i:] starts with alt, ignoring case. Returns rune count.
func hasFoldPrefix(rs []rune, i int, alt string) (int, bool) {
	n := len([]rune(alt))
	if i+n > len(rs) {
		return 0, false
	}
	return n, strings.EqualFold(string(rs[i:i+n]), alt)
}

// ---------------------------------------------------------- the regex ports

// SMALL_WORDS: ^(SMALL)$  (case-insensitive)
func isSmallWord(w string) bool {
	for _, a := range smallAlts {
		if strings.EqualFold(w, a) {
			return true
		}
	}
	return false
}

// SMALL_FIRST: ^([PUNCT]*)(SMALL)\b  -> group1 + group2.capitalize()
func smallFirst(w string) string {
	rs := []rune(w)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	for _, a := range smallAlts {
		if n, ok := hasFoldPrefix(rs, i, a); ok && boundary(rs, i+n) {
			return string(rs[:i]) + capitalize(string(rs[i:i+n])) + string(rs[i+n:])
		}
	}
	return w
}

// SMALL_LAST: \b(SMALL)[PUNCT]?$  -> group0.capitalize()
func smallLast(w string) string {
	rs := []rune(w)
	for p := 0; p < len(rs); p++ {
		if !boundary(rs, p) {
			continue
		}
		rest := rs[p:]
		for _, a := range smallAlts {
			n := len([]rune(a))
			ok := false
			if len(rest) == n && strings.EqualFold(string(rest), a) {
				ok = true
			} else if len(rest) == n+1 && isPunct(rest[n]) &&
				strings.EqualFold(string(rest[:n]), a) {
				ok = true
			}
			if ok {
				return string(rs[:p]) + capitalize(string(rest))
			}
		}
	}
	return w
}

// SUBPHRASE: ([:.;?!\-–‒—―][ ])(SMALL)   (case-sensitive, no \b)
// -> group1 + group2.capitalize(), applied to every non-overlapping match.
func subphrase(s string) string {
	rs := []rune(s)
	var out []rune
	i := 0
	for i < len(rs) {
		if strings.ContainsRune(subphrasePunct, rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			matched := false
			for _, a := range smallAlts {
				ar := []rune(a)
				if i+2+len(ar) <= len(rs) && string(rs[i+2:i+2+len(ar)]) == a {
					out = append(out, rs[i], ' ')
					out = append(out, []rune(capitalize(a))...)
					i += 2 + len(ar)
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

// MR_MRS_MS_DR: ^((m((rs?)|s))|Dr)$  (case-insensitive)
func isMrMrsMsDr(w string) bool {
	for _, a := range []string{"mr", "mrs", "ms", "dr"} {
		if strings.EqualFold(w, a) {
			return true
		}
	}
	return false
}

// INLINE_PERIOD: [\p{Letter}][.][\p{Letter}]  (search)
func hasInlinePeriod(rs []rune) bool {
	for k := 0; k+2 < len(rs); k++ {
		if isLetter(rs[k]) && rs[k+1] == '.' && isLetter(rs[k+2]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE: [PUNCT]*?[\p{Letter}]+[\p{Uppercase_Letter}]+?  (match)
// i.e. after leading punctuation comes a run of letters that contains an
// upper-case letter somewhere after its first letter.
func ucElsewhere(rs []rune) bool {
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !isLetter(rs[i]) {
		return false
	}
	for j := i + 1; j < len(rs) && isLetter(rs[j]); j++ {
		if isUpper(rs[j]) {
			return true
		}
	}
	return false
}

// UC_INITIALS: ^(?:[Lu]\.|[Lu]\.[Lu])+$
func isUCInitials(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	memo := map[int]bool{}
	var can func(i int) bool
	can = func(i int) bool {
		if i == len(rs) {
			return true
		}
		if v, ok := memo[i]; ok {
			return v
		}
		res := false
		if isUpper(rs[i]) && i+1 < len(rs) && rs[i+1] == '.' {
			if can(i + 2) {
				res = true
			} else if i+2 < len(rs) && isUpper(rs[i+2]) && can(i+3) {
				res = true
			}
		}
		memo[i] = res
		return res
	}
	return can(0)
}

// APOS_SECOND: ^[dol]['‘][\p{Letter}]+(?:['s]{2})?$  (case-insensitive)
func isAposSecond(rs []rune) bool {
	if len(rs) < 3 || !foldIn(rs[0], "dol") || (rs[1] != '\'' && rs[1] != '‘') {
		return false
	}
	rest := rs[2:]
	for k := 1; k <= len(rest); k++ {
		if !isLetter(rest[k-1]) {
			return false // the letter run is broken; no longer prefix can work
		}
		tail := rest[k:]
		if len(tail) == 0 {
			return true
		}
		if len(tail) == 2 && foldIn(tail[0], "'s") && foldIn(tail[1], "'s") {
			return true
		}
	}
	return false
}

// MAC_MC: ^([Mm]c|MC)(\w.+)
func macMcSplit(rs []rune) (string, string, bool) {
	if len(rs) < 4 {
		return "", "", false
	}
	if !((rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c') && !(rs[0] == 'M' && rs[1] == 'C') {
		return "", "", false
	}
	if !isWord(rs[2]) {
		return "", "", false
	}
	for _, r := range rs[3:] {
		if r == '\n' {
			return "", "", false
		}
	}
	return string(rs[:2]), string(rs[2:]), true
}

// \A[consonants]+\Z (case-insensitive) with len > 2
func isAcronymLike(rs []rune) bool {
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		if !foldIn(r, "bcdfghjklmnpqrstvwxz") {
			return false
		}
	}
	return true
}

// CAPFIRST: ^[PUNCT]*?([\p{Letter}])  -> upper-case that letter
func capFirst(w string) string {
	rs := []rune(w)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i < len(rs) && isLetter(rs[i]) {
		return string(rs[:i]) + upper(string(rs[i])) + string(rs[i+1:])
	}
	return w
}

// ------------------------------------------------------------ the algorithm

func processWord(word string, allCaps bool) string {
	rs := []rune(word)

	if allCaps && isUCInitials(rs) {
		return word
	}

	if isAposSecond(rs) {
		if !strings.ContainsRune("aeiouAEIOU", rs[0]) {
			rs[0] = unicode.ToLower(rs[0])
		} else {
			rs[0] = unicode.ToUpper(rs[0])
		}
		rs[2] = []rune(upper(string(rs[2])))[0]
		return string(rs)
	}

	if g1, g2, ok := macMcSplit(rs); ok {
		return capitalize(g1) + titlecase(g2, true)
	}

	if isMrMrsMsDr(word) {
		return upper(string(rs[0])) + string(rs[1:])
	}

	if hasInlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}
	if isSmallWord(word) {
		return lower(word)
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
		word = lower(word)
		rs = []rune(word)
	}

	if isAcronymLike(rs) {
		return upper(word)
	}

	return capFirst(word)
}

// splitNewlines mirrors regex.split('[\r\n]+', text).
func splitNewlines(text string) []string {
	var out []string
	var cur []rune
	inRun := false
	for _, r := range text {
		if r == '\r' || r == '\n' {
			if !inRun {
				out = append(out, string(cur))
				cur = cur[:0]
				inRun = true
			}
			continue
		}
		inRun = false
		cur = append(cur, r)
	}
	return append(out, string(cur))
}

// titlecase mirrors titlecase(text, callback=None, small_first_last=...).
func titlecase(text string, smallFirstLast bool) string {
	var processed []string
	for _, line := range splitNewlines(text) {
		allCaps := upper(line) == line

		// regex.split(r'(\s)', line)
		var words []string
		var spaces []rune
		var cur []rune
		for _, r := range line {
			if isSpace(r) {
				words = append(words, string(cur))
				spaces = append(spaces, r)
				cur = cur[:0]
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

		var b strings.Builder
		for i, w := range tc {
			b.WriteString(w)
			if i < len(spaces) {
				b.WriteRune(spaces[i])
			}
		}
		processed = append(processed, subphrase(b.String()))
	}
	return strings.Join(processed, "\n")
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			out.WriteString(titlecase(line, true))
			out.WriteByte('\n')
		}
		if err == io.EOF {
			return
		}
		if err != nil {
			os.Exit(1)
		}
	}
}
