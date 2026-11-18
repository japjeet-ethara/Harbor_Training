package main

import (
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v", "via", "vs",
}

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

var punctuationSet = makePunctuationSet()

func makePunctuationSet() map[rune]bool {
	result := make(map[rune]bool)
	for _, r := range punctuation {
		result[r] = true
	}
	return result
}

func isPythonWhitespace(r rune) bool {
	if r >= 0x1c && r <= 0x1f {
		return true
	}
	return unicode.IsSpace(r)
}

func isWordRune(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsDigit(r) ||
		unicode.Is(unicode.Mn, r) || unicode.Is(unicode.Mc, r) ||
		unicode.Is(unicode.Me, r) || unicode.Is(unicode.Pc, r)
}

func isPythonWordRune(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isUpperLetter(r rune) bool {
	return unicode.IsUpper(r)
}

func isCased(r rune) bool {
	return unicode.IsLower(r) || unicode.IsUpper(r) || unicode.IsTitle(r)
}

func isCaseIgnorable(r rune) bool {
	return unicode.Is(unicode.Mn, r) || unicode.Is(unicode.Me, r) ||
		unicode.Is(unicode.Cf, r) || unicode.Is(unicode.Lm, r) ||
		unicode.Is(unicode.Sk, r)
}

func lowerString(s string) string {
	runes := []rune(s)
	for i, r := range runes {
		if r != '\u03a3' {
			runes[i] = unicode.ToLower(r)
			continue
		}

		beforeCased := false
		for j := i - 1; j >= 0; j-- {
			if isCaseIgnorable(runes[j]) {
				continue
			}
			beforeCased = isCased(runes[j])
			break
		}

		afterCased := false
		for j := i + 1; j < len(runes); j++ {
			if isCaseIgnorable(runes[j]) {
				continue
			}
			afterCased = isCased(runes[j])
			break
		}

		if beforeCased && !afterCased {
			runes[i] = '\u03c2'
		} else {
			runes[i] = '\u03c3'
		}
	}
	return string(runes)
}

func upperString(s string) string {
	return strings.Map(unicode.ToUpper, s)
}

func capitalizeString(s string) string {
	runes := []rune(lowerString(s))
	if len(runes) == 0 {
		return s
	}
	runes[0] = unicode.ToUpper(runes[0])
	return string(runes)
}

func isAllCaps(s string) bool {
	for _, r := range s {
		if unicode.IsLower(r) || unicode.ToUpper(r) != r {
			return false
		}
	}
	return true
}

func splitLines(s string) []string {
	runes := []rune(s)
	lines := make([]string, 0, 1)
	start := 0
	for i := 0; i < len(runes); {
		if runes[i] != '\r' && runes[i] != '\n' {
			i++
			continue
		}
		lines = append(lines, string(runes[start:i]))
		for i < len(runes) && (runes[i] == '\r' || runes[i] == '\n') {
			i++
		}
		start = i
	}
	lines = append(lines, string(runes[start:]))
	return lines
}

func splitWords(line string) ([]string, []string) {
	words := make([]string, 0, 1)
	spaces := make([]string, 0)
	var word strings.Builder
	for _, r := range line {
		if isPythonWhitespace(r) {
			words = append(words, word.String())
			word.Reset()
			spaces = append(spaces, string(r))
		} else {
			word.WriteRune(r)
		}
	}
	words = append(words, word.String())
	return words, spaces
}

func joinWords(words, spaces []string) string {
	var result strings.Builder
	for i, word := range words {
		result.WriteString(word)
		if i < len(spaces) {
			result.WriteString(spaces[i])
		}
	}
	return result.String()
}

func smallWordMatch(s string, caseInsensitive bool) (string, bool) {
	for _, small := range smallWords {
		if small == "v" || small == "vs" {
			for _, candidate := range []string{small, small + "."} {
				if equalWord(s, candidate, caseInsensitive) {
					return candidate, true
				}
			}
			continue
		}
		if equalWord(s, small, caseInsensitive) {
			return small, true
		}
	}
	return "", false
}

func equalWord(a, b string, caseInsensitive bool) bool {
	if caseInsensitive {
		return strings.EqualFold(a, b)
	}
	return a == b
}

func isWordBoundaryBefore(runes []rune, i int) bool {
	return i == 0 || !isWordRune(runes[i-1])
}

func isWordBoundaryAfter(runes []rune, i int) bool {
	return i == len(runes) || !isWordRune(runes[i])
}

func wordStartsWithSmall(word string) (int, bool) {
	runes := []rune(word)
	i := 0
	for i < len(runes) && punctuationSet[runes[i]] {
		i++
	}
	for _, small := range smallWords {
		candidates := []string{small}
		if small == "v" || small == "vs" {
			candidates = append(candidates, small+".")
		}
		for _, candidate := range candidates {
			candidateRunes := []rune(candidate)
			if len(runes[i:]) < len(candidateRunes) ||
				!strings.EqualFold(string(runes[i:i+len(candidateRunes)]), candidate) {
				continue
			}
			if isWordBoundaryAfter(runes, i+len(candidateRunes)) {
				return i + len(candidateRunes), true
			}
		}
	}
	return 0, false
}

func fixFirstSmallWord(word string) string {
	length, ok := wordStartsWithSmall(word)
	if !ok {
		return word
	}
	runes := []rune(word)
	smallStart := 0
	for smallStart < len(runes) && punctuationSet[runes[smallStart]] {
		smallStart++
	}
	return string(runes[:smallStart]) + capitalizeString(string(runes[smallStart:length])) +
		string(runes[length:])
}

func fixLastSmallWord(word string) string {
	runes := []rune(word)
	end := len(runes)
	if end > 0 && punctuationSet[runes[end-1]] {
		end--
	}
	for _, small := range smallWords {
		candidates := []string{small}
		if small == "v" || small == "vs" {
			candidates = append(candidates, small+".")
		}
		for _, candidate := range candidates {
			candidateRunes := []rune(candidate)
			start := end - len(candidateRunes)
			if start < 0 || !strings.EqualFold(string(runes[start:end]), candidate) ||
				!isWordBoundaryBefore(runes, start) {
				continue
			}
			return string(runes[:start]) + capitalizeString(string(runes[start:end])) +
				string(runes[end:])
		}
	}
	return word
}

func hasInlinePeriod(word string) bool {
	runes := []rune(word)
	for i := 1; i+1 < len(runes); i++ {
		if isPythonWordRune(runes[i-1]) && runes[i] == '.' && isPythonWordRune(runes[i+1]) {
			return true
		}
	}
	return false
}

func hasUppercaseAfterLetter(word string) bool {
	runes := []rune(word)
	i := 0
	for i < len(runes) && punctuationSet[runes[i]] {
		i++
	}
	start := i
	for i < len(runes) && unicode.IsLetter(runes[i]) {
		if i > start && isUpperLetter(runes[i]) {
			return true
		}
		i++
	}
	return false
}

func isInitials(word string) bool {
	runes := []rune(word)
	seen := make(map[int]bool)
	var visit func(int) bool
	visit = func(pos int) bool {
		if pos == len(runes) {
			return true
		}
		if seen[pos] {
			return false
		}
		seen[pos] = true
		if pos+1 < len(runes) && isUpperLetter(runes[pos]) && runes[pos+1] == '.' {
			if visit(pos + 2) {
				return true
			}
			if pos+2 < len(runes) && isUpperLetter(runes[pos+2]) &&
				visit(pos+3) {
				return true
			}
		}
		return false
	}
	return len(runes) > 0 && visit(0)
}

func apostropheSecond(word string) (string, bool) {
	runes := []rune(word)
	if len(runes) < 3 || !(strings.EqualFold(string(runes[0]), "d") ||
		strings.EqualFold(string(runes[0]), "o") ||
		strings.EqualFold(string(runes[0]), "l")) ||
		(runes[1] != '\'' && runes[1] != '‘') {
		return "", false
	}

	endLetters := 2
	for endLetters < len(runes) && unicode.IsLetter(runes[endLetters]) {
		endLetters++
	}
	if endLetters == 2 {
		return "", false
	}
	if endLetters != len(runes) {
		if len(runes)-endLetters != 2 {
			return "", false
		}
		for _, r := range runes[endLetters:] {
			if r != '\'' && !strings.EqualFold(string(r), "s") {
				return "", false
			}
		}
	}

	if strings.EqualFold(string(runes[0]), "o") {
		runes[0] = unicode.ToUpper(runes[0])
	} else {
		runes[0] = unicode.ToLower(runes[0])
	}
	runes[2] = unicode.ToUpper(runes[2])
	return string(runes), true
}

func isMcPrefix(word string) (string, bool) {
	runes := []rune(word)
	if len(runes) < 4 || runes[1] != 'c' ||
		!(runes[0] == 'M' || runes[0] == 'm') {
		if len(runes) < 4 || string(runes[:2]) != "MC" {
			return "", false
		}
	}
	if !isWordRune(runes[2]) || len(runes[2:]) < 2 {
		return "", false
	}
	return "Mc" + titlecaseText(string(runes[2:]), true), true
}

func isHonorific(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func splitCompound(word string, sep rune) string {
	parts := strings.Split(word, string(sep))
	for i := range parts {
		parts[i] = titlecaseText(parts[i], false)
	}
	return strings.Join(parts, string(sep))
}

func allConsonants(word string) bool {
	runes := []rune(word)
	if len(runes) <= 2 {
		return false
	}
	for _, r := range runes {
		if r >= 'A' && r <= 'Z' {
			r += 'a' - 'A'
		}
		if r < 'a' || r > 'z' || strings.ContainsRune("aeiouy", r) {
			return false
		}
	}
	return true
}

func capitalizeFirstAfterPunctuation(word string) string {
	runes := []rune(word)
	i := 0
	for i < len(runes) && punctuationSet[runes[i]] {
		i++
	}
	if i < len(runes) && unicode.IsLetter(runes[i]) {
		runes[i] = unicode.ToUpper(runes[i])
		return string(runes)
	}
	return word
}

func titlecaseWord(word string, allCaps bool) string {
	// Rule 4: preserve initials on an all-caps line.
	if allCaps && isInitials(word) {
		return word
	}

	// Rule 5: apply the d', o', and l' apostrophe shape.
	if result, ok := apostropheSecond(word); ok {
		return result
	}

	// Rule 6: normalize an Mc prefix and recursively titlecase its remainder.
	if result, ok := isMcPrefix(word); ok {
		return result
	}

	// Rule 7: capitalize the first character of recognized honorifics only.
	if isHonorific(word) {
		runes := []rune(word)
		runes[0] = unicode.ToUpper(runes[0])
		return string(runes)
	}

	// Rule 8: preserve words containing a Python-word-character.period.word-character sequence.
	// Rule 9: preserve internal capitals except on all-caps lines.
	if hasInlinePeriod(word) || (!allCaps && hasUppercaseAfterLetter(word)) {
		return word
	}

	// Rule 10: lowercase complete small-word matches.
	if _, ok := smallWordMatch(word, true); ok {
		return lowerString(word)
	}

	// Rule 11: split slash compounds unless the word contains a double slash.
	if strings.ContainsRune(word, '/') && !strings.Contains(word, "//") {
		return splitCompound(word, '/')
	}

	// Rule 12: split ASCII-hyphen compounds.
	if strings.ContainsRune(word, '-') {
		return splitCompound(word, '-')
	}

	// Rule 13: lowercase remaining words on an all-caps line.
	if allCaps {
		word = lowerString(word)
	}

	// Rule 14: uppercase long, all-ASCII-consonant acronyms.
	if allConsonants(word) {
		return upperString(word)
	}

	// Rule 15: capitalize only a letter preceded by the source PUNCT set.
	return capitalizeFirstAfterPunctuation(word)
}

func smallWordPrefixLength(runes []rune, start int, caseInsensitive bool) int {
	for _, small := range smallWords {
		candidates := []string{small}
		if small == "v" || small == "vs" {
			candidates = append(candidates, small+".")
		}
		for _, candidate := range candidates {
			candidateRunes := []rune(candidate)
			end := start + len(candidateRunes)
			if end > len(runes) {
				continue
			}
			if equalWord(string(runes[start:end]), candidate, caseInsensitive) {
				return len(candidateRunes)
			}
		}
	}
	return 0
}

func fixSubphrases(line string) string {
	runes := []rune(line)
	var result strings.Builder
	for i := 0; i < len(runes); {
		if i+2 < len(runes) && strings.ContainsRune(":.;?!-–‒—―", runes[i]) &&
			runes[i+1] == ' ' {
			length := smallWordPrefixLength(runes, i+2, false)
			if length > 0 {
				result.WriteString(string(runes[i : i+2]))
				result.WriteString(capitalizeString(string(runes[i+2 : i+2+length])))
				i += 2 + length
				continue
			}
		}
		result.WriteRune(runes[i])
		i++
	}
	return result.String()
}

func titlecaseLine(line string, smallFirstLast bool) string {
	// Rules 1 and 2: line splitting and exact whitespace preservation.
	words, spaces := splitWords(line)
	allCaps := isAllCaps(line)

	// Rule 3: the stdin interface supplies no callback, so this rule is inert.
	for i := range words {
		words[i] = titlecaseWord(words[i], allCaps)
	}

	// Rule 16: capitalize a small word at the start of the line.
	if smallFirstLast && len(words) > 0 {
		words[0] = fixFirstSmallWord(words[0])
	}

	// Rule 17: capitalize a small word at the end of the line.
	if smallFirstLast && len(words) > 0 {
		words[len(words)-1] = fixLastSmallWord(words[len(words)-1])
	}

	// Rule 18: capitalize a small word after a sub-phrase marker.
	return fixSubphrases(joinWords(words, spaces))
}

func titlecaseText(text string, smallFirstLast bool) string {
	lines := splitLines(text)
	for i := range lines {
		lines[i] = titlecaseLine(lines[i], smallFirstLast)
	}
	return strings.Join(lines, "\n")
}

func main() {
	input, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if !utf8.Valid(input) {
		fmt.Fprintln(os.Stderr, "stdin is not valid UTF-8")
		os.Exit(1)
	}
	if _, err := io.WriteString(os.Stdout, titlecaseText(string(input), true)); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
