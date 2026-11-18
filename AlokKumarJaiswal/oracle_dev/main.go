package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

// titlecase replaces Python titlecase() with its default arguments:
// callback=None, small_first_last=True, preserve_blank_lines=False,
// normalise_space_characters=False.
func titlecase(text string) string {
	return titlecaseRec(text, true)
}

// titlecaseRec replaces Python titlecase(). smallFirstLast is the
// small_first_last argument (True on the outer call, False for slash and
// hyphen pieces, True for the Mc/MC remainder).
func titlecaseRec(text string, smallFirstLast bool) string {
	lines := splitBlankCollapsed(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, processLine(line, smallFirstLast))
	}
	return strings.Join(processed, "\n")
}

// splitBlankCollapsed replaces regex.split('[\r\n]+', text), the
// preserve_blank_lines=False branch. A trailing break yields a final empty line.
func splitBlankCollapsed(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	var b strings.Builder
	inBreak := false
	for _, r := range text {
		if r == '\r' || r == '\n' {
			if !inBreak {
				lines = append(lines, b.String())
				b.Reset()
				inBreak = true
			}
			continue
		}
		inBreak = false
		b.WriteRune(r)
	}
	if inBreak {
		lines = append(lines, "")
	} else {
		lines = append(lines, b.String())
	}
	return lines
}

// processLine is the per-line body of Python titlecase().
func processLine(line string, smallFirstLast bool) string {
	allCaps := isAllCaps(line)
	words, spaces := splitKeepSpace(line)
	tc := make([]string, 0, len(words))
	for _, word := range words {
		// Python `if callback` (default callback=None) is not taken.
		// A returned callback value would be marked Immutable and would
		// skip SMALL_FIRST / SMALL_LAST. Nothing is Immutable here.

		if allCaps && ucInitials(word) {
			tc = append(tc, word)
			continue
		}
		if rewritten, ok := aposSecond(word); ok {
			tc = append(tc, rewritten)
			continue
		}
		if rewritten, ok := macMC(word); ok {
			tc = append(tc, rewritten)
			continue
		}
		if isMrMrsMsDr(word) {
			tc = append(tc, upperFirst(word))
			continue
		}
		if hasInlinePeriod(word) || (!allCaps && ucElsewhere(word)) {
			tc = append(tc, word)
			continue
		}
		if isExactSmall(word) {
			tc = append(tc, strings.ToLower(word))
			continue
		}
		if strings.Contains(word, "/") && !strings.Contains(word, "//") {
			parts := strings.Split(word, "/")
			for i, part := range parts {
				parts[i] = titlecaseRec(part, false)
			}
			tc = append(tc, strings.Join(parts, "/"))
			continue
		}
		if strings.Contains(word, "-") {
			parts := strings.Split(word, "-")
			for i, part := range parts {
				parts[i] = titlecaseRec(part, false)
			}
			tc = append(tc, strings.Join(parts, "-"))
			continue
		}
		if allCaps {
			word = strings.ToLower(word)
		}
		if isAllConsonants(word) && len([]rune(word)) > 2 {
			tc = append(tc, strings.ToUpper(word))
			continue
		}
		tc = append(tc, capFirst(word))
	}

	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}

	// normalise_space_characters=False: interleave words and the original
	// whitespace tokens from splitKeepSpace (Python `(\s)` split).
	var b strings.Builder
	for i, w := range tc {
		b.WriteString(w)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return applySubphrase(b.String())
}

// isAllCaps replaces `line.upper() == line`.
func isAllCaps(s string) bool {
	for _, r := range s {
		if unicode.ToUpper(r) != r {
			return false
		}
	}
	return true
}

// splitKeepSpace replaces regex.split(r'(\s)', line). Each whitespace
// character is its own separator and empty words are kept.
func splitKeepSpace(line string) (words, spaces []string) {
	if line == "" {
		return []string{""}, nil
	}
	var b strings.Builder
	for _, r := range line {
		if isSpace(r) {
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

// isSpace replaces Python re `\s` for this input alphabet: the ASCII
// whitespace class. The punctuation ‘ ’ “ ” – — is not whitespace.
func isSpace(r rune) bool {
	switch r {
	case ' ', '\t', '\n', '\r', '\f', '\v':
		return true
	default:
		return false
	}
}

// isWord replaces Python re `\w` for this input alphabet: ASCII letters,
// digits, and underscore. ‘ ’ “ ” – — are not word characters.
func isWord(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '_'
}

// isLetter replaces the fallback class [a-zA-Z] (Python re, not \p{Letter}).
func isLetter(r rune) bool {
	return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z')
}

// isUpperASCII replaces the fallback class [A-Z].
func isUpperASCII(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

// isPunct replaces the PUNCT character class after Python re parses escapes.
// '_' is included. Right quotes ’ ” and ^ < = > are not.
func isPunct(r rune) bool {
	switch r {
	case '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/',
		':', ';', '?', '@', '[', '\\', ']', '_', '`', '{', '|', '}', '~',
		'\u2018', // ‘
		'\u201c', // “
		'\u2012', // ‒
		'\u2013', // –
		'\u2014', // —
		'\u2015': // ―
		return true
	default:
		return false
	}
}

// isSubPunct replaces the SUBPHRASE class [:.;?!\-–‒—―].
func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-',
		'\u2012', '\u2013', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

// isBoundary replaces Python re `\b` using isWord (Unicode \w for this alphabet).
func isBoundary(r []rune, j int) bool {
	left := j > 0 && isWord(r[j-1])
	right := j < len(r) && isWord(r[j])
	return left != right
}

// ucInitials replaces UC_INITIALS
// ^(?:[A-Z]\.|[A-Z]\.[A-Z])+$
// Checked only when the line is entirely uppercase.
func ucInitials(word string) bool {
	r := []rune(word)
	if len(r) == 0 {
		return false
	}
	var rec func(int) bool
	rec = func(i int) bool {
		if i == len(r) {
			return true
		}
		if i+1 < len(r) && isUpperASCII(r[i]) && r[i+1] == '.' {
			if rec(i + 2) {
				return true
			}
		}
		if i+2 < len(r) && isUpperASCII(r[i]) && r[i+1] == '.' && isUpperASCII(r[i+2]) {
			if rec(i + 3) {
				return true
			}
		}
		return false
	}
	return rec(0)
}

// aposSecond replaces APOS_SECOND
// ^[dol]['‘][\w]+(?:['s]{2})?$  with IGNORECASE.
// Rules for o' versus d'/l' are the two branches below.
func aposSecond(word string) (string, bool) {
	r := []rune(word)
	if len(r) < 3 {
		return word, false
	}
	switch r[0] {
	case 'd', 'D', 'o', 'O', 'l', 'L':
	default:
		return word, false
	}
	if r[1] != '\'' && r[1] != '\u2018' {
		return word, false
	}
	if !aposRest(r[2:]) {
		return word, false
	}
	out := append([]rune(nil), r...)
	// len(word[0]) == 1 is always true for str. Vowels keep an initial capital;
	// d and l are lowercased. The character after the apostrophe is uppercased.
	if !isAposVowel(out[0]) {
		out[0] = unicode.ToLower(out[0])
	} else {
		out[0] = unicode.ToUpper(out[0])
	}
	out[2] = unicode.ToUpper(out[2])
	return string(out), true
}

// aposRest is the [\w]+(?:['s]{2})?$ part of APOS_SECOND.
func aposRest(rest []rune) bool {
	if len(rest) == 0 {
		return false
	}
	allWord := true
	for _, c := range rest {
		if !isWord(c) {
			allWord = false
			break
		}
	}
	if allWord {
		return true
	}
	if len(rest) < 3 {
		return false
	}
	if !isAposTail(rest[len(rest)-1]) || !isAposTail(rest[len(rest)-2]) {
		return false
	}
	body := rest[:len(rest)-2]
	for _, c := range body {
		if !isWord(c) {
			return false
		}
	}
	return true
}

// isAposTail replaces the class ['s] under IGNORECASE.
func isAposTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

// isAposVowel replaces `word[0] not in 'aeiouAEIOU'`.
func isAposVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

// macMC replaces MAC_MC ^([Mm]c|MC)(\w.+). The prefix is str.capitalize()'d
// and the remainder is titlecase()'d with small_first_last=True.
func macMC(word string) (string, bool) {
	r := []rune(word)
	if len(r) < 4 {
		return word, false
	}
	mc := (r[0] == 'M' || r[0] == 'm') && r[1] == 'c'
	upperMC := r[0] == 'M' && r[1] == 'C'
	if !mc && !upperMC {
		return word, false
	}
	if !isWord(r[2]) {
		return word, false
	}
	prefix := pyCapitalize(string(r[:2]))
	rest := titlecaseRec(string(r[2:]), true)
	return prefix + rest, true
}

// isMrMrsMsDr replaces MR_MRS_MS_DR ^((m((rs?)|s))|Dr)$ with IGNORECASE.
func isMrMrsMsDr(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

// upperFirst replaces `word[0].upper() + word[1:]` (the Mr/Mrs/Ms/Dr rewrite).
func upperFirst(word string) string {
	r := []rune(word)
	if len(r) == 0 {
		return word
	}
	r[0] = unicode.ToUpper(r[0])
	return string(r)
}

// hasInlinePeriod replaces INLINE_PERIOD [\w][.][\w] searched anywhere.
func hasInlinePeriod(word string) bool {
	r := []rune(word)
	for i := 0; i+2 < len(r); i++ {
		if isWord(r[i]) && r[i+1] == '.' && isWord(r[i+2]) {
			return true
		}
	}
	return false
}

// ucElsewhere replaces UC_ELSEWHERE
// [PUNCT]*?[a-zA-Z]+[A-Z]+?
// as a prefix match (.match, not a full match). Used only when the line is
// not entirely uppercase.
func ucElsewhere(word string) bool {
	r := []rune(word)
	// [PUNCT]*? is lazy, but only a letter can start the next class, so every
	// leading punct character (including '_') is consumed.
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	if i >= len(r) || !isLetter(r[i]) {
		return false
	}
	start := i
	for i < len(r) && isLetter(r[i]) {
		i++
	}
	letters := r[start:i]
	if len(letters) < 2 {
		return false
	}
	for _, c := range letters[1:] {
		if isUpperASCII(c) {
			return true
		}
	}
	return false
}

// isExactSmall replaces SMALL_WORDS ^(?:a|an|...|v\.?|via|vs\.?)$ IGNORECASE.
func isExactSmall(word string) bool {
	switch strings.ToLower(word) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

// isAllConsonants replaces
// regex.search(r'\A[' + CONSONANTS + r']+\Z', word, IGNORECASE)
// where CONSONANTS is ascii lowercase minus a, e, i, o, u, y.
func isAllConsonants(word string) bool {
	if word == "" {
		return false
	}
	for _, c := range word {
		if !isLetter(c) {
			return false
		}
		switch unicode.ToLower(c) {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

// capFirst replaces CAPFIRST ^[PUNCT]*?([\w]) substituted with group(0).upper().
// The lazy punct run stops at the first word character, so a leading '_' or
// digit is that word character and the letter after it is not capitalized.
func capFirst(word string) string {
	r := []rune(word)
	for i, c := range r {
		if isWord(c) {
			r[i] = unicode.ToUpper(c)
			return string(r)
		}
		if !isPunct(c) {
			return word
		}
	}
	return word
}

// applySmallFirst replaces SMALL_FIRST ^([PUNCT]*)(SMALL)\b IGNORECASE.
// The matched small word is str.capitalize()'d; the rest of the token stays.
func applySmallFirst(word string) string {
	r := []rune(word)
	maxP := 0
	for maxP < len(r) && isPunct(r[maxP]) {
		maxP++
	}
	for p := maxP; p >= 0; p-- {
		if n := matchSmallBounded(r, p); n > 0 {
			return string(r[:p]) + pyCapitalize(string(r[p:p+n])) + string(r[p+n:])
		}
	}
	return word
}

// applySmallLast replaces SMALL_LAST \b(SMALL)[PUNCT]?$ IGNORECASE.
// The whole match, including one trailing punct character, is str.capitalize()'d.
func applySmallLast(word string) string {
	r := []rune(word)
	for start := 0; start <= len(r); start++ {
		if !isBoundary(r, start) {
			continue
		}
		if matchSmallToEnd(r, start) {
			return string(r[:start]) + pyCapitalize(string(r[start:]))
		}
	}
	return word
}

// applySubphrase replaces SUBPHRASE ([:.;?!\-–‒—―][ ])(SMALL) with no IGNORECASE.
// SMALL is unanchored, so the first alternative that is a prefix wins and
// there is no word-boundary check. That is why ": android" becomes ": Android"
// while ": banana" stays ": banana".
func applySubphrase(s string) string {
	r := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(r) {
		if isSubPunct(r[i]) && i+1 < len(r) && r[i+1] == ' ' {
			if n := matchSmallPrefix(r, i+2); n > 0 {
				b.WriteRune(r[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(r[i+2 : i+2+n])))
				i += 2 + n
				continue
			}
		}
		b.WriteRune(r[i])
		i++
	}
	return b.String()
}

// matchSmallBounded replaces (SMALL)\b under IGNORECASE, alternation order
// a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?
func matchSmallBounded(r []rune, i int) int {
	fixed := []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to"}
	for _, lit := range fixed {
		n := len([]rune(lit))
		if hasPrefixFold(r, i, lit) && isBoundary(r, i+n) {
			return n
		}
	}
	if hasPrefixFold(r, i, "v") {
		if i+1 < len(r) && r[i+1] == '.' && isBoundary(r, i+2) {
			return 2
		}
		if isBoundary(r, i+1) {
			return 1
		}
	}
	if hasPrefixFold(r, i, "via") && isBoundary(r, i+3) {
		return 3
	}
	if hasPrefixFold(r, i, "vs") {
		if i+2 < len(r) && r[i+2] == '.' && isBoundary(r, i+3) {
			return 3
		}
		if isBoundary(r, i+2) {
			return 2
		}
	}
	return 0
}

// matchSmallToEnd replaces (SMALL)[PUNCT]?$ under IGNORECASE.
func matchSmallToEnd(r []rune, i int) bool {
	fixed := []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to"}
	for _, lit := range fixed {
		n := len([]rune(lit))
		if hasPrefixFold(r, i, lit) && restIsOptionalPunct(r, i+n) {
			return true
		}
	}
	if hasPrefixFold(r, i, "v") {
		if i+1 < len(r) && r[i+1] == '.' && restIsOptionalPunct(r, i+2) {
			return true
		}
		if restIsOptionalPunct(r, i+1) {
			return true
		}
	}
	if hasPrefixFold(r, i, "via") && restIsOptionalPunct(r, i+3) {
		return true
	}
	if hasPrefixFold(r, i, "vs") {
		if i+2 < len(r) && r[i+2] == '.' && restIsOptionalPunct(r, i+3) {
			return true
		}
		if restIsOptionalPunct(r, i+2) {
			return true
		}
	}
	return false
}

// matchSmallPrefix replaces the unanchored case-sensitive SMALL alternative
// inside SUBPHRASE. The first successful alternative wins; v\.? therefore
// matches before via and vs\.?.
func matchSmallPrefix(r []rune, i int) int {
	fixed := []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to"}
	for _, lit := range fixed {
		if hasPrefixExact(r, i, lit) {
			return len([]rune(lit))
		}
	}
	if i < len(r) && r[i] == 'v' {
		if i+1 < len(r) && r[i+1] == '.' {
			return 2
		}
		return 1
	}
	if hasPrefixExact(r, i, "via") {
		return 3
	}
	if hasPrefixExact(r, i, "vs") {
		if i+2 < len(r) && r[i+2] == '.' {
			return 3
		}
		return 2
	}
	return 0
}

func restIsOptionalPunct(r []rune, j int) bool {
	if j == len(r) {
		return true
	}
	return j+1 == len(r) && isPunct(r[j])
}

func hasPrefixFold(r []rune, i int, lit string) bool {
	l := []rune(lit)
	if i+len(l) > len(r) {
		return false
	}
	for k, c := range l {
		if unicode.ToLower(r[i+k]) != c {
			return false
		}
	}
	return true
}

func hasPrefixExact(r []rune, i int, lit string) bool {
	l := []rune(lit)
	if i+len(l) > len(r) {
		return false
	}
	for k, c := range l {
		if r[i+k] != c {
			return false
		}
	}
	return true
}

// pyCapitalize replaces str.capitalize: first character upper, the rest lower.
func pyCapitalize(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return s
	}
	r[0] = unicode.ToUpper(r[0])
	for i := 1; i < len(r); i++ {
		r[i] = unicode.ToLower(r[i])
	}
	return string(r)
}

func main() {
	in := bufio.NewReader(os.Stdin)
	data, err := io.ReadAll(in)
	if err != nil {
		os.Exit(1)
	}

	out := bufio.NewWriter(os.Stdout)
	if len(data) > 0 {
		text := string(data)
		if strings.HasSuffix(text, "\n") {
			text = text[:len(text)-1]
		}
		for _, line := range strings.Split(text, "\n") {
			if _, err := out.WriteString(titlecase(line)); err != nil {
				os.Exit(1)
			}
			if err := out.WriteByte('\n'); err != nil {
				os.Exit(1)
			}
		}
	}
	if err := out.Flush(); err != nil {
		os.Exit(1)
	}
}
