package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
)

// Punctuation matching PUNCT in titlecase/__init__.py
// PUNCT = r"""!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~"""
func isPunct(r rune) bool {
	switch r {
	case '!', '"', '“', '#', '$', '%', '&', '\'', '‘', '(', ')', '*', '+', ',',
		'-', '–', '‒', '—', '―', '.', '/', ':', ';', '?', '@', '[', '\\', ']',
		'^', '_', '`', '{', '|', '}', '~':
		return true
	}
	return false
}

// Subphrase punctuation matching:
// SUBPHRASE = regex.compile(r'([:.;?!\-–‒—―][ ])(%s)' % SMALL)
func isSubphrasePunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	}
	return false
}

func isAsciiLetter(b byte) bool {
	return (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z')
}

func isWordChar(b byte) bool {
	return (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z') || (b >= '0' && b <= '9') || b == '_'
}

func isSmallWord(word string) bool {
	w := strings.ToLower(word)
	switch w {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
		"in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	}
	return false
}

// INLINE_PERIOD: r'[\w][.][\w]'
func hasInlinePeriod(word string) bool {
	for i := 1; i < len(word)-1; i++ {
		if word[i] == '.' && isWordChar(word[i-1]) && isWordChar(word[i+1]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE: r'[%s]*?[a-zA-Z]+[A-Z]+?' % PUNCT
// Means after optional punctuation, there is one or more ASCII letters,
// followed by at least one uppercase ASCII letter.
// Essentially: once letters begin, there is an uppercase letter that is not the first letter.
func hasUcElsewhere(word string) bool {
	runes := []rune(word)
	i := 0
	// Skip leading punctuation
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	// Must have at least one ASCII letter
	if i >= len(runes) || !isAsciiLetter(byte(runes[i])) {
		return false
	}
	i++ // skip the first letter
	// Check if any subsequent ASCII letter is uppercase
	hasUpper := false
	for i < len(runes) {
		r := runes[i]
		if isAsciiLetter(byte(r)) {
			if r >= 'A' && r <= 'Z' {
				hasUpper = true
				break
			}
		}
		i++
	}
	return hasUpper
}

// UC_INITIALS: r"^(?:[A-Z]\.|[A-Z]\.[A-Z])+$"
func isUcInitials(word string) bool {
	if len(word) == 0 {
		return false
	}
	i := 0
	n := len(word)
	for i < n {
		// Expect [A-Z]
		if word[i] < 'A' || word[i] > 'Z' {
			return false
		}
		i++
		// Expect '.'
		if i >= n || word[i] != '.' {
			return false
		}
		i++
		// Optionally another [A-Z] before repeat
		if i < n && word[i] >= 'A' && word[i] <= 'Z' {
			// Check if followed by '.' or end
			if i+1 == n {
				// e.g. A.B
				return true
			}
			if i+1 < n && word[i+1] == '.' {
				// Could be A.B. -> handled by next iteration!
			} else {
				i++
			}
		}
	}
	return true
}

// APOS_SECOND: r"^[dol]['‘][\w]+(?:['s]{2})?$" (case-insensitive)
func matchAposSecond(word string) (bool, string) {
	runes := []rune(word)
	if len(runes) < 3 {
		return false, ""
	}
	first := unicode.ToLower(runes[0])
	if first != 'd' && first != 'o' && first != 'l' {
		return false, ""
	}
	if runes[1] != '\'' && runes[1] != '‘' {
		return false, ""
	}
	// Rest must be \w+, optionally ending with 's or ‘s
	// In the python code:
	// if len(word[0]) == 1 and word[0] not in 'aeiouAEIOU':
	//     word = word[0].lower() + word[1] + word[2].upper() + word[3:]
	// else:
	//     word = word[0].upper() + word[1] + word[2].upper() + word[3:]
	// Note: 'o' is in 'aeiou', so 'o' gets capitalized: O'Reilly.
	// 'd' and 'l' are consonants, so they get lowercased: l'Grange.
	
	// Check word validity (\w+)
	for idx := 2; idx < len(runes); idx++ {
		r := runes[idx]
		if r == '\'' || r == '‘' {
			// Optional (?:['s]{2})? at end
			if idx == len(runes)-2 && (runes[idx+1] == 's' || runes[idx+1] == 'S') {
				break
			}
			return false, ""
		}
		if r > 127 || !isWordChar(byte(r)) {
			return false, ""
		}
	}

	var res []rune
	if first == 'o' {
		res = append(res, unicode.ToUpper(runes[0]))
	} else {
		res = append(res, unicode.ToLower(runes[0]))
	}
	res = append(res, runes[1])
	res = append(res, unicode.ToUpper(runes[2]))
	res = append(res, runes[3:]...)
	return true, string(res)
}

// MAC_MC: r"^([Mm]c|MC)(\w.+)"
func matchMacMc(word string) (bool, string, string) {
	if len(word) < 3 {
		return false, "", ""
	}
	prefix := word[:2]
	if prefix == "mc" || prefix == "Mc" || prefix == "MC" {
		return true, "Mc", word[2:]
	}
	return false, "", ""
}

// MR_MRS_MS_DR: r"^((m((rs?)|s))|Dr)$" (regex.I)
func matchMrMrsMsDr(word string) bool {
	w := strings.ToLower(word)
	switch w {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

// CAPFIRST: r"^[%s]*?([\w])" % PUNCT
// Replaces the first word character with uppercase.
func capFirst(word string) string {
	runes := []rune(word)
	for i, r := range runes {
		if isPunct(r) {
			continue
		}
		if isWordChar(byte(r)) || r > 127 {
			runes[i] = unicode.ToUpper(r)
			break
		}
	}
	return string(runes)
}

// All consonants check:
// A term with all consonants should be considered an acronym. But if it's too short (<=2), don't apply.
// CONSONANTS = string.ascii_lowercase - {'a', 'e', 'i', 'o', 'u', 'y'}
func isAllConsonants(word string) bool {
	if len(word) <= 2 {
		return false
	}
	for i := 0; i < len(word); i++ {
		b := word[i]
		if b >= 'A' && b <= 'Z' {
			b += 32
		}
		if b < 'a' || b > 'z' {
			return false
		}
		if b == 'a' || b == 'e' || b == 'i' || b == 'o' || b == 'u' || b == 'y' {
			return false
		}
	}
	return true
}

// SMALL_FIRST: r'^([%s]*)(%s)\b' % (PUNCT, SMALL)
func applySmallFirst(word string) string {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	if i >= len(runes) {
		return word
	}
	// Extract word starting at i until boundary
	j := i
	for j < len(runes) && (isWordChar(byte(runes[j])) || runes[j] == '.') {
		j++
	}
	sub := string(runes[i:j])
	if isSmallWord(sub) {
		// Capitalize sub
		capSub := strings.ToUpper(sub[:1]) + strings.ToLower(sub[1:])
		return string(runes[:i]) + capSub + string(runes[j:])
	}
	return word
}

// SMALL_LAST: r'\b(%s)[%s]?$' % (SMALL, PUNCT)
func applySmallLast(word string) string {
	runes := []rune(word)
	n := len(runes)
	if n == 0 {
		return word
	}
	end := n
	if isPunct(runes[n-1]) {
		end = n - 1
	}
	// Look backwards for word
	start := end
	for start > 0 && (isWordChar(byte(runes[start-1])) || runes[start-1] == '.') {
		start--
	}
	if start < end {
		sub := string(runes[start:end])
		if isSmallWord(sub) {
			capSub := strings.ToUpper(sub[:1]) + strings.ToLower(sub[1:])
			return string(runes[:start]) + capSub + string(runes[end:])
		}
	}
	return word
}

// SUBPHRASE: r'([:.;?!\-–‒—―][ ])(%s)' % SMALL
func applySubphrase(text string) string {
	runes := []rune(text)
	var sb strings.Builder
	n := len(runes)
	i := 0
	for i < n {
		if i+2 < n && isSubphrasePunct(runes[i]) && runes[i+1] == ' ' {
			sb.WriteRune(runes[i])
			sb.WriteRune(runes[i+1])
			i += 2
			// Check if next token is a small word
			k := i
			for k < n && (isWordChar(byte(runes[k])) || runes[k] == '.') {
				k++
			}
			token := string(runes[i:k])
			if isSmallWord(token) {
				sb.WriteString(strings.ToUpper(token[:1]) + strings.ToLower(token[1:]))
				i = k
			}
		} else {
			sb.WriteRune(runes[i])
			i++
		}
	}
	return sb.String()
}

func titlecaseWord(word string, allCaps bool, smallFirstLast bool) string {
	if allCaps && isUcInitials(word) {
		return word
	}

	if ok, replaced := matchAposSecond(word); ok {
		return replaced
	}

	if ok, pfx, sfx := matchMacMc(word); ok {
		return pfx + Titlecase(sfx, true)
	}

	if matchMrMrsMsDr(word) {
		return strings.ToUpper(word[:1]) + word[1:]
	}

	if hasInlinePeriod(word) || (!allCaps && hasUcElsewhere(word)) {
		return word
	}

	if isSmallWord(word) {
		return strings.ToLower(word)
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for idx, part := range parts {
			parts[idx] = Titlecase(part, false)
		}
		return strings.Join(parts, "/")
	}

	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for idx, part := range parts {
			parts[idx] = Titlecase(part, false)
		}
		return strings.Join(parts, "-")
	}

	if allCaps {
		word = strings.ToLower(word)
	}

	if isAllConsonants(word) {
		return strings.ToUpper(word)
	}

	return capFirst(word)
}

// Titlecase applies title-casing to the input text matching python-titlecase.
func Titlecase(text string, smallFirstLast bool) string {
	if len(text) == 0 {
		return ""
	}

	// Split lines
	lines := strings.Split(text, "\n")
	var processedLines []string

	for _, line := range lines {
		allCaps := strings.ToUpper(line) == line

		// Split line into words and whitespace
		var words []string
		var spaces []string
		runes := []rune(line)
		n := len(runes)
		i := 0

		for i < n {
			// Read word
			wStart := i
			for i < n && !unicode.IsSpace(runes[i]) {
				i++
			}
			words = append(words, string(runes[wStart:i]))

			if i >= n {
				break
			}

			// Read spaces
			sStart := i
			for i < n && unicode.IsSpace(runes[i]) {
				i++
			}
			spaces = append(spaces, string(runes[sStart:i]))
		}

		var tcLine []string
		for _, w := range words {
			tcLine = append(tcLine, titlecaseWord(w, allCaps, smallFirstLast))
		}

		if smallFirstLast && len(tcLine) > 0 {
			tcLine[0] = applySmallFirst(tcLine[0])
			tcLine[len(tcLine)-1] = applySmallLast(tcLine[len(tcLine)-1])
		}

		// Rebuild line with preserved original spaces
		var sb strings.Builder
		for idx, w := range tcLine {
			sb.WriteString(w)
			if idx < len(spaces) {
				sb.WriteString(spaces[idx])
			}
		}

		result := sb.String()
		result = applySubphrase(result)
		processedLines = append(processedLines, result)
	}

	return strings.Join(processedLines, "\n")
}

func main() {
	reader := bufio.NewReader(os.Stdin)
	for {
		line, err := reader.ReadString('\n')
		if len(line) > 0 {
			hasCR := strings.HasSuffix(line, "\r\n")
			hasLF := strings.HasSuffix(line, "\n")
			trimmed := strings.TrimRight(line, "\r\n")
			out := Titlecase(trimmed, true)
			if hasCR {
				fmt.Print(out, "\r\n")
			} else if hasLF {
				fmt.Print(out, "\n")
			} else {
				fmt.Print(out)
			}
		}
		if err != nil {
			if err != io.EOF {
				fmt.Fprintln(os.Stderr, "read error:", err)
			}
			break
		}
	}
}
