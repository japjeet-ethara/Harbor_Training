package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
const phraseBreaks = ":.;?!-–‒—―"

var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v", "via", "vs",
}

var uppercaseExpansions = map[rune]string{
	'ß': "SS", 'ŉ': "ʼN", 'ǰ': "J̌",
	'ẖ': "H̱", 'ẗ': "T̈", 'ẘ': "W̊", 'ẙ': "Y̊", 'ẚ': "Aʾ",
	'ﬀ': "FF", 'ﬁ': "FI", 'ﬂ': "FL", 'ﬃ': "FFI", 'ﬄ': "FFL",
	'ﬅ': "ST", 'ﬆ': "ST",
}

func pythonUpper(text string) string {
	var out strings.Builder
	for _, r := range text {
		if expanded, ok := uppercaseExpansions[r]; ok {
			out.WriteString(expanded)
			continue
		}
		out.WriteRune(unicode.ToUpper(r))
	}
	return out.String()
}

func pythonLower(text string) string {
	var out strings.Builder
	for _, r := range text {
		if r == 'İ' {
			out.WriteString("i̇")
			continue
		}
		out.WriteRune(unicode.ToLower(r))
	}
	return out.String()
}

func firstUpperRestLower(text string) string {
	runes := []rune(text)
	if len(runes) == 0 {
		return ""
	}
	return pythonUpper(string(runes[:1])) + pythonLower(string(runes[1:]))
}

func isPunct(r rune) bool {
	return strings.ContainsRune(punctuation, r)
}

func isTitleWordRune(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) ||
		unicode.IsMark(r) || unicode.Is(unicode.Pc, r)
}

func isWordBoundary(runes []rune, index int) bool {
	left := index > 0 && isTitleWordRune(runes[index-1])
	right := index < len(runes) && isTitleWordRune(runes[index])
	return left != right
}

func foldedRune(r rune) rune {
	switch {
	case r >= 'A' && r <= 'Z':
		return r + ('a' - 'A')
	case r == 'ſ':
		return 's'
	case r == 'K':
		return 'k'
	case r == 'İ':
		return 'i'
	default:
		return r
	}
}

func matchSmall(runes []rune, start int, word string, ignoreCase bool) []int {
	letters := []rune(word)
	if start < 0 || start+len(letters) > len(runes) {
		return nil
	}
	for i, expected := range letters {
		found := runes[start+i]
		if ignoreCase {
			found = foldedRune(found)
		}
		if found != expected {
			return nil
		}
	}

	end := start + len(letters)
	if (word == "v" || word == "vs") && end < len(runes) && runes[end] == '.' {
		return []int{end + 1, end}
	}
	return []int{end}
}

func isSmallToken(runes []rune) bool {
	for _, word := range smallWords {
		for _, end := range matchSmall(runes, 0, word, true) {
			if end == len(runes) {
				return true
			}
		}
	}
	return false
}

func isInitialism(runes []rune) bool {
	reachable := make([]bool, len(runes)+1)
	reachable[len(runes)] = true
	for i := len(runes) - 1; i >= 0; i-- {
		if !unicode.Is(unicode.Lu, runes[i]) || i+1 >= len(runes) || runes[i+1] != '.' {
			continue
		}
		reachable[i] = reachable[i+2]
		if i+2 < len(runes) && unicode.Is(unicode.Lu, runes[i+2]) {
			reachable[i] = reachable[i] || reachable[i+3]
		}
	}
	return len(runes) > 0 && reachable[0]
}

func isApostropheName(runes []rune) bool {
	if len(runes) < 3 || !strings.ContainsRune("dol", foldedRune(runes[0])) ||
		(runes[1] != '\'' && runes[1] != '‘') {
		return false
	}

	name := runes[2:]
	if len(name) >= 2 {
		last := name[len(name)-2:]
		if (last[0] == '\'' || foldedRune(last[0]) == 's') &&
			(last[1] == '\'' || foldedRune(last[1]) == 's') {
			name = name[:len(name)-2]
		}
	}
	if len(name) == 0 {
		return false
	}
	for _, r := range name {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return true
}

func isMacName(runes []rune) bool {
	if len(runes) < 4 {
		return false
	}
	prefix := (runes[0] == 'M' && (runes[1] == 'c' || runes[1] == 'C')) ||
		(runes[0] == 'm' && runes[1] == 'c')
	return prefix && isTitleWordRune(runes[2])
}

func isHonorific(runes []rune) bool {
	switch strings.ToLower(string(runes)) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func hasDottedLetters(runes []rune) bool {
	for i := 1; i+1 < len(runes); i++ {
		if unicode.IsLetter(runes[i-1]) && runes[i] == '.' && unicode.IsLetter(runes[i+1]) {
			return true
		}
	}
	return false
}

func leadingPunctuation(runes []rune) int {
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	return i
}

func hasProtectedMixedCase(runes []rune) bool {
	start := leadingPunctuation(runes)
	if start >= len(runes) || !unicode.IsLetter(runes[start]) {
		return false
	}
	for i := start + 1; i < len(runes) && unicode.IsLetter(runes[i]); i++ {
		if unicode.Is(unicode.Lu, runes[i]) {
			return true
		}
	}
	return false
}

func onlyConsonants(runes []rune) bool {
	if len(runes) == 0 {
		return false
	}
	for _, r := range runes {
		r = foldedRune(r)
		if r < 'a' || r > 'z' || strings.ContainsRune("aeiouy", r) {
			return false
		}
	}
	return true
}

func capitalizeAfterPunct(runes []rune) string {
	start := leadingPunctuation(runes)
	if start >= len(runes) || !unicode.IsLetter(runes[start]) {
		return string(runes)
	}
	return string(runes[:start]) + pythonUpper(string(runes[start:start+1])) + string(runes[start+1:])
}

func capitalizeLeadingSmall(text string) string {
	runes := []rune(text)
	start := leadingPunctuation(runes)
	for _, word := range smallWords {
		for _, end := range matchSmall(runes, start, word, true) {
			if isWordBoundary(runes, end) {
				return string(runes[:start]) + firstUpperRestLower(string(runes[start:end])) + string(runes[end:])
			}
		}
	}
	return text
}

func capitalizeTrailingSmall(text string) string {
	runes := []rune(text)
	for start := 0; start < len(runes); start++ {
		if !isWordBoundary(runes, start) {
			continue
		}
		for _, word := range smallWords {
			for _, end := range matchSmall(runes, start, word, true) {
				if end == len(runes) || (end == len(runes)-1 && isPunct(runes[end])) {
					return string(runes[:start]) + firstUpperRestLower(string(runes[start:]))
				}
			}
		}
	}
	return text
}

func fixSubphraseStarts(text string) string {
	runes := []rune(text)
	var out strings.Builder
	for i := 0; i < len(runes); {
		if i+2 < len(runes) && strings.ContainsRune(phraseBreaks, runes[i]) && runes[i+1] == ' ' {
			for _, word := range smallWords {
				ends := matchSmall(runes, i+2, word, false)
				if len(ends) == 0 {
					continue
				}
				end := ends[0]
				out.WriteString(string(runes[i : i+2]))
				out.WriteString(firstUpperRestLower(string(runes[i+2 : end])))
				i = end
				goto nextRune
			}
		}
		out.WriteRune(runes[i])
		i++
	nextRune:
	}
	return out.String()
}

func titlePart(text string, adjustEdges bool) string {
	allUpper := pythonUpper(text) == text
	tokens := make([]string, 0, len(text)/2+1)
	separators := make([]string, 0, len(text)/2)
	var word strings.Builder
	for _, r := range text {
		if unicode.IsSpace(r) {
			tokens = append(tokens, word.String())
			separators = append(separators, string(r))
			word.Reset()
		} else {
			word.WriteRune(r)
		}
	}
	tokens = append(tokens, word.String())

	for i, token := range tokens {
		tokens[i] = titleToken(token, allUpper)
	}
	if adjustEdges {
		tokens[0] = capitalizeLeadingSmall(tokens[0])
		tokens[len(tokens)-1] = capitalizeTrailingSmall(tokens[len(tokens)-1])
	}

	var out strings.Builder
	for i, token := range tokens {
		out.WriteString(token)
		if i < len(separators) {
			out.WriteString(separators[i])
		}
	}
	return fixSubphraseStarts(out.String())
}

func titleToken(token string, allUpper bool) string {
	runes := []rune(token)
	switch {
	case allUpper && isInitialism(runes):
		return token
	case isApostropheName(runes):
		first := pythonUpper(string(runes[:1]))
		if !strings.ContainsRune("aeiouAEIOU", runes[0]) {
			first = pythonLower(string(runes[:1]))
		}
		return first + string(runes[1:2]) + pythonUpper(string(runes[2:3])) + string(runes[3:])
	case isMacName(runes):
		return "Mc" + titlePart(string(runes[2:]), true)
	case isHonorific(runes):
		return pythonUpper(string(runes[:1])) + string(runes[1:])
	case hasDottedLetters(runes) || (!allUpper && hasProtectedMixedCase(runes)):
		return token
	case isSmallToken(runes):
		return pythonLower(token)
	}

	if strings.Contains(token, "/") && !strings.Contains(token, "//") {
		parts := strings.Split(token, "/")
		for i := range parts {
			parts[i] = titlePart(parts[i], false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(token, "-") {
		parts := strings.Split(token, "-")
		for i := range parts {
			parts[i] = titlePart(parts[i], false)
		}
		return strings.Join(parts, "-")
	}
	if allUpper {
		token = pythonLower(token)
		runes = []rune(token)
	}
	if len(runes) > 2 && onlyConsonants(runes) {
		return pythonUpper(token)
	}
	return capitalizeAfterPunct(runes)
}

func main() {
	reader := bufio.NewReaderSize(os.Stdin, 64*1024)
	writer := bufio.NewWriterSize(os.Stdout, 64*1024)
	defer writer.Flush()
	for {
		line, err := reader.ReadString('\n')
		if err != nil && err != io.EOF {
			os.Exit(1)
		}
		if err == io.EOF && line == "" {
			return
		}
		line = strings.TrimSuffix(line, "\n")
		writer.WriteString(titlePart(line, true))
		writer.WriteByte('\n')
		if err == io.EOF {
			return
		}
	}
}
