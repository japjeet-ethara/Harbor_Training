package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
const subphrasePunctuation = ":.;?!-–‒—―"

var pythonUpperExpansions = map[rune]string{
	'ß': "SS", 'ŉ': "ʼN", 'ǰ': "J̌",
	'ẖ': "H̱", 'ẗ': "T̈", 'ẘ': "W̊", 'ẙ': "Y̊", 'ẚ': "Aʾ",
	'ﬀ': "FF", 'ﬁ': "FI", 'ﬂ': "FL", 'ﬃ': "FFI", 'ﬄ': "FFL",
	'ﬅ': "ST", 'ﬆ': "ST",
}

func upper(s string) string {
	var out strings.Builder
	for _, r := range s {
		if expanded, ok := pythonUpperExpansions[r]; ok {
			out.WriteString(expanded)
		} else {
			out.WriteRune(unicode.ToUpper(r))
		}
	}
	return out.String()
}

func lower(s string) string {
	var out strings.Builder
	for _, r := range s {
		if r == 'İ' {
			out.WriteString("i̇")
		} else {
			out.WriteRune(unicode.ToLower(r))
		}
	}
	return out.String()
}

func capitalize(s string) string {
	runes := []rune(s)
	if len(runes) == 0 {
		return ""
	}
	return upper(string(runes[:1])) + lower(string(runes[1:]))
}

func isPunctuation(r rune) bool { return strings.ContainsRune(punctuation, r) }

func isWordRune(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.IsMark(r) || unicode.Is(unicode.Pc, r)
}

func hasBoundary(runes []rune, pos int) bool {
	before := pos > 0 && isWordRune(runes[pos-1])
	after := pos < len(runes) && isWordRune(runes[pos])
	return before != after
}

func asciiFold(r rune) rune {
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

func smallAlternatives() []string {
	return []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "via", "vs"}
}

func smallEnds(runes []rune, start int, word string, ignoreCase bool) []int {
	letters := []rune(word)
	if start+len(letters) > len(runes) {
		return nil
	}
	for i, expected := range letters {
		got := runes[start+i]
		if ignoreCase {
			got = asciiFold(got)
		}
		if got != expected {
			return nil
		}
	}
	end := start + len(letters)
	if (word == "v" || word == "vs") && end < len(runes) && runes[end] == '.' {
		return []int{end + 1, end}
	}
	return []int{end}
}

func matchesSmallWord(runes []rune) bool {
	for _, word := range smallAlternatives() {
		for _, end := range smallEnds(runes, 0, word, true) {
			if end == len(runes) {
				return true
			}
		}
	}
	return false
}

func initialism(runes []rune) bool {
	possible := make([]bool, len(runes)+1)
	possible[len(runes)] = true
	for i := len(runes) - 1; i >= 0; i-- {
		if !unicode.Is(unicode.Lu, runes[i]) || i+1 >= len(runes) || runes[i+1] != '.' {
			continue
		}
		possible[i] = possible[i+2]
		if i+2 < len(runes) && unicode.Is(unicode.Lu, runes[i+2]) {
			possible[i] = possible[i] || possible[i+3]
		}
	}
	return len(runes) > 0 && possible[0]
}

func apostropheName(runes []rune) bool {
	if len(runes) < 3 || !strings.ContainsRune("dol", asciiFold(runes[0])) || (runes[1] != '\'' && runes[1] != '‘') {
		return false
	}
	tail := runes[2:]
	if len(tail) >= 2 {
		lastTwo := tail[len(tail)-2:]
		if (lastTwo[0] == '\'' || asciiFold(lastTwo[0]) == 's') &&
			(lastTwo[1] == '\'' || asciiFold(lastTwo[1]) == 's') {
			tail = tail[:len(tail)-2]
		}
	}
	if len(tail) == 0 {
		return false
	}
	for _, r := range tail {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return true
}

func macPrefix(runes []rune) bool {
	if len(runes) < 4 || !((runes[0] == 'M' && (runes[1] == 'c' || runes[1] == 'C')) ||
		(runes[0] == 'm' && runes[1] == 'c')) {
		return false
	}
	return isWordRune(runes[2])
}

func honorific(runes []rune) bool {
	switch strings.ToLower(string(runes)) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func inlinePeriod(runes []rune) bool {
	for i := 0; i+2 < len(runes); i++ {
		if unicode.IsLetter(runes[i]) && runes[i+1] == '.' && unicode.IsLetter(runes[i+2]) {
			return true
		}
	}
	return false
}

func punctuationPrefix(runes []rune) int {
	i := 0
	for i < len(runes) && isPunctuation(runes[i]) {
		i++
	}
	return i
}

func mixedCaseAcronym(runes []rune) bool {
	start := punctuationPrefix(runes)
	if start == len(runes) || !unicode.IsLetter(runes[start]) {
		return false
	}
	for i := start + 1; i < len(runes) && unicode.IsLetter(runes[i]); i++ {
		if unicode.Is(unicode.Lu, runes[i]) {
			return true
		}
	}
	return false
}

func allConsonants(runes []rune) bool {
	if len(runes) == 0 {
		return false
	}
	for _, r := range runes {
		r = asciiFold(r)
		if r < 'a' || r > 'z' || strings.ContainsRune("aeiouy", r) {
			return false
		}
	}
	return true
}

func capFirst(runes []rune) string {
	start := punctuationPrefix(runes)
	if start == len(runes) || !unicode.IsLetter(runes[start]) {
		return string(runes)
	}
	return string(runes[:start]) + upper(string(runes[start:start+1])) + string(runes[start+1:])
}

func slashSeparated(word string) bool {
	return strings.Contains(word, "/") && !strings.Contains(word, "//")
}

func titleLine(line string, adjustEdges bool) string {
	allCaps := upper(line) == line
	words := make([]string, 0, len(line)/2+1)
	spaces := make([]string, 0, len(line)/2)
	var part strings.Builder
	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, part.String())
			spaces = append(spaces, string(r))
			part.Reset()
		} else {
			part.WriteRune(r)
		}
	}
	words = append(words, part.String())

	for i, word := range words {
		words[i] = titleToken(word, allCaps)
	}
	if adjustEdges {
		words[0] = capitalizeSmallPrefix(words[0])
		words[len(words)-1] = capitalizeSmallSuffix(words[len(words)-1])
	}

	var out strings.Builder
	for i, word := range words {
		out.WriteString(word)
		if i < len(spaces) {
			out.WriteString(spaces[i])
		}
	}
	return capitalizeSubphrases(out.String())
}

func titleToken(word string, allCaps bool) string {
	runes := []rune(word)
	if allCaps && initialism(runes) {
		return word
	}
	if apostropheName(runes) {
		first := upper(string(runes[:1]))
		if !strings.ContainsRune("aeiouAEIOU", runes[0]) {
			first = lower(string(runes[:1]))
		}
		return first + string(runes[1:2]) + upper(string(runes[2:3])) + string(runes[3:])
	}
	if macPrefix(runes) {
		return "Mc" + titleLine(string(runes[2:]), true)
	}
	if honorific(runes) {
		return upper(string(runes[:1])) + string(runes[1:])
	}
	if inlinePeriod(runes) || (!allCaps && mixedCaseAcronym(runes)) {
		return word
	}
	if matchesSmallWord(runes) {
		return lower(word)
	}
	if slashSeparated(word) || strings.Contains(word, "-") {
		separator := "/"
		if !slashSeparated(word) {
			separator = "-"
		}
		parts := strings.Split(word, separator)
		for i := range parts {
			parts[i] = titleLine(parts[i], false)
		}
		return strings.Join(parts, separator)
	}
	if allCaps {
		word = lower(word)
		runes = []rune(word)
	}
	if len(runes) > 2 && allConsonants(runes) {
		return upper(word)
	}
	return capFirst(runes)
}

func capitalizeSmallPrefix(s string) string {
	runes := []rune(s)
	start := punctuationPrefix(runes)
	for _, word := range smallAlternatives() {
		for _, end := range smallEnds(runes, start, word, true) {
			if hasBoundary(runes, end) {
				return string(runes[:start]) + capitalize(string(runes[start:end])) + string(runes[end:])
			}
		}
	}
	return s
}

func capitalizeSmallSuffix(s string) string {
	runes := []rune(s)
	for start := 0; start < len(runes); start++ {
		if !hasBoundary(runes, start) {
			continue
		}
		for _, word := range smallAlternatives() {
			for _, end := range smallEnds(runes, start, word, true) {
				if end == len(runes) || (end == len(runes)-1 && isPunctuation(runes[end])) {
					return string(runes[:start]) + capitalize(string(runes[start:]))
				}
			}
		}
	}
	return s
}

func capitalizeSubphrases(s string) string {
	runes := []rune(s)
	var out strings.Builder
	for i := 0; i < len(runes); {
		if i+2 < len(runes) && strings.ContainsRune(subphrasePunctuation, runes[i]) && runes[i+1] == ' ' {
			matched := false
			for _, word := range smallAlternatives() {
				ends := smallEnds(runes, i+2, word, false)
				if len(ends) == 0 {
					continue
				}
				end := ends[0]
				out.WriteString(string(runes[i : i+2]))
				out.WriteString(capitalize(string(runes[i+2 : end])))
				i = end
				matched = true
				break
			}
			if matched {
				continue
			}
		}
		out.WriteRune(runes[i])
		i++
	}
	return out.String()
}

func titlecase(s string) string {
	return titleLine(s, true)
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 64*1024)
	out := bufio.NewWriterSize(os.Stdout, 64*1024)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if err != nil && err != io.EOF {
			os.Exit(1)
		}
		if err == io.EOF && line == "" {
			return
		}
		line = strings.TrimSuffix(line, "\n")
		out.WriteString(titlecase(line))
		out.WriteByte('\n')
		if err == io.EOF {
			return
		}
	}
}
