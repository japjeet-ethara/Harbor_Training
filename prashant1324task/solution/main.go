package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
)

var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true,
	"at": true, "but": true, "by": true, "en": true,
	"for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true,
	"v": true, "v.": true, "via": true, "vs": true,
	"vs.": true,
}

var punctuation = `!"“#$%&'‘()*+,-–‒—―./:;?@[\]_` + "`" + `{|}~`

var (
	initialsRE  = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
	inlineRE    = regexp.MustCompile(`[A-Za-z][.][A-Za-z]`)
	mixedRE     = regexp.MustCompile(`^[!"“#$%&'‘()*+,\-–‒—―./:;?@\[\\\]_` + "`" + `{|}~]*?[\p{L}]+[\p{Lu}]`)
	aposRE      = regexp.MustCompile(`(?i)^[dol]['‘][\p{L}]+(?:['s]{2})?$`)
	macRE       = regexp.MustCompile(`^([Mm]c|MC)(\w.+)$`)
	titleRE     = regexp.MustCompile(`(?i)^(mr|mrs|ms|dr)$`)
	subphraseRE = regexp.MustCompile(`([:.;?!\-–‒—―] )(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)`)
)

func upperFirst(s string) string {
	r := []rune(s)
	for i, ch := range r {
		if unicode.IsLetter(ch) {
			r[i] = unicode.ToUpper(ch)
			break
		}
	}
	return string(r)
}

func lowerFirst(s string) string {
	r := []rune(s)
	for i, ch := range r {
		if unicode.IsLetter(ch) {
			r[i] = unicode.ToLower(ch)
			break
		}
	}
	return string(r)
}

func allConsonants(s string) bool {
	if len([]rune(s)) <= 2 {
		return false
	}
	for _, r := range s {
		if !unicode.IsLetter(r) {
			return false
		}
		switch unicode.ToLower(r) {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
		if r > unicode.MaxASCII {
			return false
		}
	}
	return true
}

func isSmall(s string) bool {
	return smallWords[strings.ToLower(s)]
}

func isPunctuation(r rune) bool {
	return strings.ContainsRune(punctuation, r)
}

func capitalizeSmallFirst(s string) string {
	r := []rune(s)

	i := 0
	for i < len(r) && isPunctuation(r[i]) {
		i++
	}

	start := i
	for i < len(r) && unicode.IsLetter(r[i]) {
		i++
	}

	if start == i {
		return s
	}

	word := string(r[start:i])
	if isSmall(word) {
		wordRunes := []rune(word)
		wordRunes[0] = unicode.ToUpper(wordRunes[0])

		for j := 1; j < len(wordRunes); j++ {
			wordRunes[j] = unicode.ToLower(wordRunes[j])
		}

		copy(r[start:i], wordRunes)
	}

	return string(r)
}

func capitalizeSmallLast(s string) string {
	r := []rune(s)
	end := len(r)

	if end > 0 && isPunctuation(r[end-1]) {
		end--
	}

	start := end
	for start > 0 && unicode.IsLetter(r[start-1]) {
		start--
	}

	if start == end {
		return s
	}

	word := string(r[start:end])
	if isSmall(word) {
		word = strings.ToUpper(string([]rune(word)[0])) +
			strings.ToLower(string([]rune(word)[1:]))
		copy(r[start:end], []rune(word))
	}

	return string(r)
}

func splitWhitespace(s string) ([]string, []string) {
	var words, spaces []string
	r := []rune(s)
	i := 0

	for i < len(r) {
		start := i
		for i < len(r) && !unicode.IsSpace(r[i]) {
			i++
		}
		words = append(words, string(r[start:i]))

		start = i
		for i < len(r) && unicode.IsSpace(r[i]) {
			i++
		}
		if i > start {
			spaces = append(spaces, string(r[start:i]))
		}
	}
	return words, spaces
}

func titlecaseWord(word string, allCaps bool, smallFirstLast bool) string {
	if word == "" {
		return word
	}

	if allCaps && initialsRE.MatchString(word) {
		return word
	}

	if aposRE.MatchString(word) {
		r := []rune(word)
		if len(r) >= 3 {
			if !strings.ContainsRune("aeiouAEIOU", r[0]) {
				r[0] = unicode.ToLower(r[0])
			} else {
				r[0] = unicode.ToUpper(r[0])
			}
			r[2] = unicode.ToUpper(r[2])
		}
		return string(r)
	}

	if match := macRE.FindStringSubmatch(word); match != nil {
		prefix := strings.ToUpper(match[1][:1]) + strings.ToLower(match[1][1:])
		return prefix + titlecaseText(match[2], true)
	}

	if titleRE.MatchString(word) {
		return upperFirst(word)
	}

	if inlineRE.MatchString(word) || (!allCaps && mixedRE.MatchString(word)) {
		return word
	}

	if isSmall(word) {
		return strings.ToLower(word)
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i := range parts {
			parts[i] = titlecaseText(parts[i], false)
		}
		return strings.Join(parts, "/")
	}

	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i := range parts {
			parts[i] = titlecaseText(parts[i], false)
		}
		return strings.Join(parts, "-")
	}

	if allCaps {
		word = strings.ToLower(word)
	}

	if allConsonants(word) {
		return strings.ToUpper(word)
	}

	result := upperFirst(word)

	if smallFirstLast {
		result = capitalizeSmallFirst(result)
	}
	return result
}

func titlecaseText(text string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(text) == text

	words, spaces := splitWhitespace(text)
	if len(words) == 0 {
		return text
	}

	processed := make([]string, len(words))
	for i, word := range words {
		processed[i] = titlecaseWord(word, allCaps, false)
	}

	if smallFirstLast {
		processed[0] = capitalizeSmallFirst(processed[0])
		processed[len(processed)-1] = capitalizeSmallLast(processed[len(processed)-1])
	}

	var result strings.Builder
	for i, word := range processed {
		result.WriteString(word)
		if i < len(spaces) {
			result.WriteString(spaces[i])
		}
	}

	output := result.String()
	output = subphraseRE.ReplaceAllStringFunc(output, func(match string) string {
		parts := subphraseRE.FindStringSubmatch(match)
		if len(parts) != 3 {
			return match
		}
		return parts[1] + upperFirst(parts[2])
	})

	return output
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 4096), 10*1024*1024)

	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		line := scanner.Text()
		fmt.Fprintln(writer, titlecaseText(line, true))
	}

	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, "input error:", err)
		os.Exit(1)
	}
}
