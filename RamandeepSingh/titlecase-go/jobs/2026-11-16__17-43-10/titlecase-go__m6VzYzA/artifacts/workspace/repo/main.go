package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
)

// ---------------------------------------------------------------------------
// Constants mirroring the Python source
// ---------------------------------------------------------------------------

// SMALL words (regex: ^(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)$  IGNORECASE)
var smallWordSet = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

// PUNCT rune set  (matches the PUNCT constant in the Python source)
// !""\u201c\u201d#$%&''\u2018\u2019()*+,\-\u2013\u2012\u2014\u2015./:;?@[\\\]_`{|}~
var punctSet = map[rune]bool{
	'!': true, '"': true, '\u201C': true, '\u201D': true,
	'#': true, '$': true, '%': true, '&': true,
	'\'': true, '\u2018': true, '\u2019': true,
	'(': true, ')': true, '*': true, '+': true, ',': true,
	'-': true, '\u2013': true, '\u2012': true, '\u2014': true, '\u2015': true,
	'.': true, '/': true, ':': true, ';': true, '?': true,
	'@': true, '[': true, '\\': true, ']': true, '_': true,
	'`': true, '{': true, '|': true, '}': true, '~': true,
}

// Subphrase-delimiter runes  ([:.;?!\-–‒—―])
var subphrasePunct = map[rune]bool{
	':': true, '.': true, ';': true, '?': true, '!': true,
	'-': true, '\u2013': true, '\u2012': true, '\u2014': true, '\u2015': true,
}

// ASCII consonants  (set(string.ascii_lowercase) - {a,e,i,o,u,y})
var consonantSet = map[rune]bool{
	'b': true, 'c': true, 'd': true, 'f': true, 'g': true,
	'h': true, 'j': true, 'k': true, 'l': true, 'm': true,
	'n': true, 'p': true, 'q': true, 'r': true, 's': true,
	't': true, 'v': true, 'w': true, 'x': true, 'z': true,
}

// ---------------------------------------------------------------------------
// Helper: is a rune a "word character" for \b purposes?
// Python regex \b uses Unicode word chars: Letter | Digit | '_'
// ---------------------------------------------------------------------------
func isWordChar(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

// ---------------------------------------------------------------------------
// Split a line into (words, spaces) the same way Python does:
//   regex.split(r'(\s)', line)
// The result is an alternating slice: word0, space0, word1, space1, ...
// words  = result[0::2]
// spaces = result[1::2]
// ---------------------------------------------------------------------------
func splitOnWhitespace(s string) (words []string, spaces []string) {
	runes := []rune(s)
	n := len(runes)
	start := 0
	for i := 0; i < n; {
		r := runes[i]
		if unicode.IsSpace(r) {
			words = append(words, string(runes[start:i]))
			spaces = append(spaces, string(r))
			i++
			start = i
		} else {
			i++
		}
	}
	words = append(words, string(runes[start:]))
	return
}

// ---------------------------------------------------------------------------
// UC_INITIALS: ^(?:[\p{Uppercase_Letter}]{1}\.{1}|[\p{Uppercase_Letter}]{1}\.{1}[\p{Uppercase_Letter}]{1})+$
// Pattern: one or more groups of  (UpperLetter + '.')  optionally followed by another UpperLetter
// Equivalent: the whole string consists of blocks like "A." or "A.B" (but always ends after a letter or a dot)
// More precisely: (UL . | UL . UL)+ — but since (UL . UL) ends without a dot, that breaks the repeating.
// Re-reading the Python regex:
//   ^(?:[\p{UL}]{1}\.{1}|[\p{UL}]{1}\.{1}[\p{UL}]{1})+$
// Each alternative is  UL.  or  UL.UL  — both start with UL.
// So valid strings: "A.", "A.B", "A.B.", "A.B.C", "U.S.A", "A.B.C.D" etc.
// (trailing letter optional because of the second alternative)
// ---------------------------------------------------------------------------
func matchUCInitials(w string) bool {
	runes := []rune(w)
	n := len(runes)
	i := 0
	if n == 0 {
		return false
	}
	for i < n {
		// expect uppercase letter
		if !unicode.IsUpper(runes[i]) {
			return false
		}
		i++
		// expect '.'
		if i >= n || runes[i] != '.' {
			return false
		}
		i++
		// optional second uppercase letter (second alternative: UL . UL)
		if i < n && unicode.IsUpper(runes[i]) {
			i++
			// if more chars remain, we loop back and expect another UL.
			// if string ends here, that's the second alternative finishing.
		}
		// if string ends, done
	}
	return true
}

// ---------------------------------------------------------------------------
// APOS_SECOND: ^[dol]{1}['\']{1}[\p{Letter}]+(?:['s]{2})?$  IGNORECASE
// First char in {d,o,l} (case-insensitive), second char is ' or ' (U+2019),
// then one or more Unicode letters, optionally followed by "'s".
// Python behaviour on match:
//   if word[0] not in vowels: word = word[0].lower() + word[1] + word[2].upper() + word[3:]
//   else:                      word = word[0].upper() + word[1] + word[2].upper() + word[3:]
// ---------------------------------------------------------------------------
func matchAposSecond(w string) bool {
	runes := []rune(w)
	n := len(runes)
	if n < 3 {
		return false
	}
	r0 := unicode.ToLower(runes[0])
	if r0 != 'd' && r0 != 'o' && r0 != 'l' {
		return false
	}
	if runes[1] != '\'' && runes[1] != '\u2018' && runes[1] != '\u2019' {
		return false
	}
	// rest must match [\p{Letter}]+(?:['s]{2})?
	// i.e., one or more letters, then optionally "'s" (straight apos + s)
	i := 2
	if i >= n || !unicode.IsLetter(runes[i]) {
		return false
	}
	for i < n && unicode.IsLetter(runes[i]) {
		i++
	}
	// optional trailing "'s"
	if i < n {
		if i+2 == n && (runes[i] == '\'' || runes[i] == '\u2019') && unicode.ToLower(runes[i+1]) == 's' {
			i += 2
		} else {
			return false
		}
	}
	return i == n
}

func applyAposSecond(w string) string {
	runes := []rune(w)
	vowels := map[rune]bool{'a': true, 'e': true, 'i': true, 'o': true, 'u': true}
	r0Lower := unicode.ToLower(runes[0])
	if _, isVowel := vowels[r0Lower]; !isVowel {
		runes[0] = unicode.ToLower(runes[0])
	} else {
		runes[0] = unicode.ToUpper(runes[0])
	}
	runes[2] = unicode.ToUpper(runes[2])
	return string(runes)
}

// ---------------------------------------------------------------------------
// MAC_MC: ^([Mm]c|MC)(\w.+)
// Groups: (1) prefix  (2) rest (which must have len >= 1 more char)
// ---------------------------------------------------------------------------
func matchMacMc(w string) (prefix, rest string, ok bool) {
	runes := []rune(w)
	if len(runes) < 3 {
		return
	}
	// Check prefix: "Mc", "mc", "mC", "MC"
	r0 := runes[0]
	r1 := runes[1]
	isMc := (r0 == 'M' || r0 == 'm') && (r1 == 'c' || r1 == 'C')
	isMC := r0 == 'M' && r1 == 'C'
	if !isMc && !isMC {
		return
	}
	// rest = runes[2:] must match \w.+  i.e. start with a word char and have at least one more char
	if len(runes) < 4 {
		return
	}
	r2 := runes[2]
	if !isWordChar(r2) {
		return
	}
	prefix = string(runes[:2])
	rest = string(runes[2:])
	ok = true
	return
}

// ---------------------------------------------------------------------------
// MR_MRS_MS_DR: ^((m((rs?)|s))|Dr)$  IGNORECASE
// Matches: mr, mrs, ms, dr (case-insensitive)
// ---------------------------------------------------------------------------
func matchMrMrsMsDr(w string) bool {
	lower := strings.ToLower(w)
	switch lower {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

func applyMrMrsMsDr(w string) string {
	runes := []rune(w)
	if len(runes) == 0 {
		return w
	}
	runes[0] = unicode.ToUpper(runes[0])
	return string(runes)
}

// ---------------------------------------------------------------------------
// INLINE_PERIOD (Unicode branch): [\p{Letter}][.][\p{Letter}]  IGNORECASE
// Search for letter . letter anywhere in word.
// ---------------------------------------------------------------------------
func hasInlinePeriod(w string) bool {
	runes := []rune(w)
	n := len(runes)
	for i := 1; i < n-1; i++ {
		if runes[i] == '.' && unicode.IsLetter(runes[i-1]) && unicode.IsLetter(runes[i+1]) {
			return true
		}
	}
	return false
}

// ---------------------------------------------------------------------------
// UC_ELSEWHERE (Unicode branch): [PUNCT]*?[\p{Letter}]+[\p{Uppercase_Letter}]+?
// Match (not full-string) from the START of the string.
// Skip leading PUNCT, then find: letter+ then at least one Uppercase letter.
// The pattern means: after punct, see one+ letters, then one+ uppercase letters.
// Because the first group is [\p{Letter}]+ and second is [\p{Uppercase_Letter}]+?,
// this detects CamelCase anywhere in the letter sequence, e.g.:
//   "iPhone"   -> 'i'(letter) seen, then 'P'(upper) seen -> match
//   "MacDonald" -> 'M'(letter+upper) seen as first letter, then 'D'(upper) later -> match
// Algorithm: skip punct; then scan letters one by one — once we have seen at least
// one letter and we encounter an uppercase letter, return true.
// ---------------------------------------------------------------------------
func matchUCElsewhere(w string) bool {
	runes := []rune(w)
	n := len(runes)
	i := 0
	// skip leading punct
	for i < n && punctSet[runes[i]] {
		i++
	}
	// must see at least one letter
	if i >= n || !unicode.IsLetter(runes[i]) {
		return false
	}
	seenLetter := false
	for i < n && unicode.IsLetter(runes[i]) {
		if seenLetter && unicode.IsUpper(runes[i]) {
			return true
		}
		seenLetter = true
		i++
	}
	return false
}

// ---------------------------------------------------------------------------
// SMALL_WORDS: ^(SMALL)$  IGNORECASE
// ---------------------------------------------------------------------------
func matchSmallWord(w string) bool {
	return smallWordSet[strings.ToLower(w)]
}

// ---------------------------------------------------------------------------
// All-consonants check (ASCII only):
//   regex.search(r'\A[CONSONANTS]+\Z', word, flags=regex.IGNORECASE)
//   where CONSONANTS = bcdfghjklmnpqrstvwxz
// Every rune must be in consonantSet (case-insensitively), AND every rune
// must be ASCII (the Python regex only matches ASCII letters here).
// ---------------------------------------------------------------------------
func allASCIIConsonants(w string) bool {
	runes := []rune(w)
	if len(runes) == 0 {
		return false
	}
	for _, r := range runes {
		if r > 127 {
			return false
		}
		if !consonantSet[unicode.ToLower(r)] {
			return false
		}
	}
	return true
}

// ---------------------------------------------------------------------------
// CAPFIRST (Unicode branch): ^[PUNCT]*?([\p{Letter}])
// Uppercase the first Unicode letter found (after any leading PUNCT).
// ---------------------------------------------------------------------------
func capFirst(w string) string {
	runes := []rune(w)
	for i, r := range runes {
		if unicode.IsLetter(r) {
			runes[i] = unicode.ToUpper(r)
			return string(runes)
		}
		if !punctSet[r] {
			// Non-punct, non-letter — stop looking
			break
		}
	}
	return w
}

// ---------------------------------------------------------------------------
// SMALL_FIRST: ^([PUNCT]*)(\bSMALL\b)   IGNORECASE
// If the first word (tc_line[0]) starts with optional PUNCT then a small word
// at a word boundary, capitalize that small word.
// Python: SMALL_FIRST.sub(lambda m: '%s%s' % (m.group(1), m.group(2).capitalize()), tc_line[0])
// We only substitute one occurrence (at the very start).
// ---------------------------------------------------------------------------
func applySmallFirst(w string) string {
	runes := []rune(w)
	n := len(runes)
	i := 0
	// skip leading punct
	for i < n && punctSet[runes[i]] {
		i++
	}
	punctEnd := i
	// try to match a small word
	j := i
	for j < n && !unicode.IsSpace(runes[j]) && !punctSet[runes[j]] {
		j++
	}
	if j == i {
		return w
	}
	candidate := strings.ToLower(string(runes[i:j]))
	if !smallWordSet[candidate] {
		return w
	}
	// word boundary check after j: next char must be non-word or end
	if j < n && isWordChar(runes[j]) {
		return w
	}
	// capitalize the small word (Python's str.capitalize() uppercases first, lowercases rest)
	cap := strings.ToUpper(string(runes[i:i+1])) + strings.ToLower(string(runes[i+1:j]))
	return string(runes[:punctEnd]) + cap + string(runes[j:])
}

// ---------------------------------------------------------------------------
// SMALL_LAST: \b(SMALL)[PUNCT]?$   IGNORECASE
// If the last word (tc_line[-1]) ends with an optional PUNCT then a small word
// preceded by a word boundary, capitalize that small word.
// Python: SMALL_LAST.sub(lambda m: m.group(0).capitalize(), tc_line[-1])
// Note: .capitalize() on the whole match uppercases first char, lowercases rest.
// ---------------------------------------------------------------------------
func applySmallLast(w string) string {
	runes := []rune(w)
	n := len(runes)
	if n == 0 {
		return w
	}
	end := n
	// optional trailing punct
	if end > 0 && punctSet[runes[end-1]] {
		end--
	}
	// find small word ending at end
	j := end
	for j > 0 && !unicode.IsSpace(runes[j-1]) && !punctSet[runes[j-1]] {
		j--
	}
	if j == end {
		return w
	}
	candidate := strings.ToLower(string(runes[j:end]))
	if !smallWordSet[candidate] {
		return w
	}
	// word boundary check before j: prev char must be non-word or start
	if j > 0 && isWordChar(runes[j-1]) {
		return w
	}
	// Python capitalize() on group(0) = small word + optional trailing punct
	matchRunes := runes[j : n] // includes optional trailing punct
	cap := strings.ToUpper(string(matchRunes[0:1])) + strings.ToLower(string(matchRunes[1:]))
	return string(runes[:j]) + cap
}

// ---------------------------------------------------------------------------
// SUBPHRASE: ([:.;?!\-–‒—―][ ])(SMALL)
// In the reassembled result, wherever a subphrase delimiter + space appears
// followed by a small word, capitalize that small word.
// Python: SUBPHRASE.sub(lambda m: '%s%s' % (m.group(1), m.group(2).capitalize()), result)
// ---------------------------------------------------------------------------
func applySubphrase(s string) string {
	runes := []rune(s)
	n := len(runes)
	var out []rune
	i := 0
	for i < n {
		// look for subphrase delimiter followed by space
		if subphrasePunct[runes[i]] && i+1 < n && runes[i+1] == ' ' {
			// try to match a small word after the space
			k := i + 2
			j := k
			for j < n && !unicode.IsSpace(runes[j]) && !punctSet[runes[j]] {
				j++
			}
			candidate := strings.ToLower(string(runes[k:j]))
			if j > k && smallWordSet[candidate] {
				// emit delimiter + space + capitalized small word
				out = append(out, runes[i], runes[i+1])
				// capitalize: upper first, lower rest
				wordRunes := runes[k:j]
				out = append(out, unicode.ToUpper(wordRunes[0]))
				for _, r := range wordRunes[1:] {
					out = append(out, unicode.ToLower(r))
				}
				i = j
				continue
			}
		}
		out = append(out, runes[i])
		i++
	}
	return string(out)
}

// ---------------------------------------------------------------------------
// Core titlecase function.
// text        — the input string (a single line in our main loop)
// smallFirstLast — whether to apply SMALL_FIRST and SMALL_LAST
// ---------------------------------------------------------------------------
func titlecaseString(text string, smallFirstLast bool) string {
	// all_caps: Python does  line.upper() == line
	allCaps := strings.ToUpper(text) == text

	// Split into words and spaces (mimics regex.split(r'(\s)', line))
	words, spaces := splitOnWhitespace(text)

	tcLine := make([]string, len(words))
	immutable := make([]bool, len(words))

	for idx, word := range words {
		if word == "" {
			tcLine[idx] = word
			continue
		}

		// Rule 1: all_caps + UC_INITIALS → keep
		if allCaps && matchUCInitials(word) {
			tcLine[idx] = word
			immutable[idx] = true
			continue
		}

		// Rule 2: APOS_SECOND
		if matchAposSecond(word) {
			tcLine[idx] = applyAposSecond(word)
			immutable[idx] = true
			continue
		}

		// Rule 3: MAC_MC
		if prefix, rest, ok := matchMacMc(word); ok {
			capPrefix := strings.ToUpper(prefix[:1]) + strings.ToLower(prefix[1:])
			tcLine[idx] = capPrefix + titlecaseString(rest, true)
			immutable[idx] = true
			continue
		}

		// Rule 4: MR_MRS_MS_DR
		if matchMrMrsMsDr(word) {
			tcLine[idx] = applyMrMrsMsDr(word)
			immutable[idx] = true
			continue
		}

		// Rule 5: INLINE_PERIOD or (not all_caps and UC_ELSEWHERE)
		if hasInlinePeriod(word) || (!allCaps && matchUCElsewhere(word)) {
			tcLine[idx] = word
			continue
		}

		// Rule 6: SMALL_WORDS → lowercase
		if matchSmallWord(word) {
			tcLine[idx] = strings.ToLower(word)
			continue
		}

		// Rule 7: slash splitting
		if strings.Contains(word, "/") && !strings.Contains(word, "//") {
			parts := strings.Split(word, "/")
			for pi, p := range parts {
				parts[pi] = titlecaseString(p, false)
			}
			tcLine[idx] = strings.Join(parts, "/")
			continue
		}

		// Rule 8: hyphen splitting
		if strings.Contains(word, "-") {
			parts := strings.Split(word, "-")
			for pi, p := range parts {
				parts[pi] = titlecaseString(p, false)
			}
			tcLine[idx] = strings.Join(parts, "-")
			continue
		}

		// Pre-processing: if all_caps, lowercase before further rules
		if allCaps {
			word = strings.ToLower(word)
		}

		// Rule 9: all ASCII consonants + length > 2 → uppercase
		if allASCIIConsonants(word) && len([]rune(word)) > 2 {
			tcLine[idx] = strings.ToUpper(word)
			continue
		}

		// Rule 10: capFirst
		tcLine[idx] = capFirst(word)
	}

	// Apply SMALL_FIRST and SMALL_LAST (only when smallFirstLast=true)
	if smallFirstLast && len(tcLine) > 0 {
		if !immutable[0] {
			tcLine[0] = applySmallFirst(tcLine[0])
		}
		if !immutable[len(tcLine)-1] {
			tcLine[len(tcLine)-1] = applySmallLast(tcLine[len(tcLine)-1])
		}
	}

	// Reassemble: interleave words and spaces
	// Python: line_to_be_joined[::2] = tc_line; line_to_be_joined[1::2] = spaces
	// total length = len(words) + len(spaces)  (== 2*len(words)-1 since len(spaces)==len(words)-1)
	var sb strings.Builder
	for i, w := range tcLine {
		sb.WriteString(w)
		if i < len(spaces) {
			sb.WriteString(spaces[i])
		}
	}
	result := sb.String()

	// Apply SUBPHRASE substitution
	result = applySubphrase(result)

	return result
}

// ---------------------------------------------------------------------------
// main: read one title per line from stdin, print titlecased output to stdout.
// Uses bufio.Reader.ReadString to avoid 64KB scanner limit.
// ---------------------------------------------------------------------------
func main() {
	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for {
		line, err := reader.ReadString('\n')
		// Strip \r\n or \n
		line = strings.TrimRight(line, "\r\n")
		// Process even if err==EOF (handles final line with no trailing newline)
		fmt.Fprintln(writer, titlecaseString(line, true))
		if err != nil {
			if err == io.EOF {
				break
			}
			fmt.Fprintf(os.Stderr, "read error: %v\n", err)
			os.Exit(1)
		}
	}
}
