package main

import (
	"strings"
	"unicode/utf8"
)

type span struct {
	start, end int
}

type token struct {
	word      span
	separator span
}

func tokenize(line string) []token {
	var tokens []token
	start := 0
	for at, ch := range line {
		if properties(ch)&space != 0 {
			next := afterRune(line, at)
			tokens = append(tokens, token{span{start, at}, span{at, next}})
			start = next
		}
	}
	return append(tokens, token{span{start, len(line)}, span{len(line), len(line)}})
}

func titlecase(text string, capitalizeEdges bool) string {
	if !strings.ContainsAny(text, "\r\n") {
		return formatLine(text, capitalizeEdges)
	}
	var result strings.Builder
	for {
		end := strings.IndexAny(text, "\r\n")
		if end < 0 {
			result.WriteString(formatLine(text, capitalizeEdges))
			return result.String()
		}
		result.WriteString(formatLine(text[:end], capitalizeEdges))
		result.WriteByte('\n')
		text = strings.TrimLeft(text[end:], "\r\n")
	}
}

func formatLine(line string, capitalizeEdges bool) string {
	allCaps := unchangedByUppercase(line)
	tokens := tokenize(line)
	var result strings.Builder
	result.Grow(len(line))
	for i, part := range tokens {
		word := formatWord(line[part.word.start:part.word.end], allCaps)
		if capitalizeEdges && i == 0 {
			word = capitalizeFirstSmall(word)
		}
		if capitalizeEdges && i == len(tokens)-1 {
			word = capitalizeLastSmall(word)
		}
		result.WriteString(word)
		result.WriteString(line[part.separator.start:part.separator.end])
	}
	return capitalizeSubphrases(result.String())
}

func formatWord(word string, allCaps bool) string {
	switch {
	case allCaps && isInitials(word):
		return word
	case startsApostropheName(word):
		return caseApostropheName(word)
	case startsMcName(word):
		return "Mc" + titlecase(word[2:], true)
	case isHonorific(word):
		return upperFirst(word)
	case hasInlinePeriod(word) || !allCaps && hasInternalUppercase(word):
		return word
	case isSmall(word):
		return lowercase(word, false)
	case strings.Contains(word, "/") && !strings.Contains(word, "//"):
		return formatCompound(word, '/')
	case strings.Contains(word, "-"):
		return formatCompound(word, '-')
	}
	if allCaps {
		word = lowercase(word, false)
	}
	if isConsonantAcronym(word) {
		return uppercase(word)
	}
	return capitalizeWord(word)
}

func formatCompound(word string, separator byte) string {
	var result strings.Builder
	result.Grow(len(word))
	for {
		end := strings.IndexByte(word, separator)
		if end < 0 {
			result.WriteString(titlecase(word, false))
			return result.String()
		}
		result.WriteString(titlecase(word[:end], false))
		result.WriteByte(separator)
		word = word[end+1:]
	}
}

func isInitials(word string) bool {
	if word == "" {
		return false
	}
	for at := 0; at < len(word); {
		if at+1 >= len(word) || !asciiUpper(word[at]) || word[at+1] != '.' {
			return false
		}
		at += 2
		if at < len(word) && asciiUpper(word[at]) && (at+1 == len(word) || word[at+1] != '.') {
			at++
		}
	}
	return true
}

func startsApostropheName(word string) bool {
	if len(word) < 3 || !strings.ContainsRune("dol", foldASCII(rune(word[0]))) {
		return false
	}
	apostrophe, width := utf8.DecodeRuneInString(word[1:])
	if apostrophe != '\'' && apostrophe != '‘' {
		return false
	}
	tail := word[1+width:]
	end := 0
	for end < len(tail) && wordAt(tail, end) {
		end = afterRune(tail, end)
	}
	if end == 0 {
		return false
	}
	remaining := utf8.RuneCountInString(tail[end:])
	if remaining == 0 {
		return true
	}
	if remaining > 2 {
		return false
	}
	for _, ch := range tail[end:] {
		if ch != '\'' && foldASCII(ch) != 's' {
			return false
		}
	}
	if remaining == 2 {
		return true
	}
	prev, _ := utf8.DecodeLastRuneInString(tail[:end])
	return end > utf8.RuneLen(prev) && foldASCII(prev) == 's'
}

func caseApostropheName(word string) string {
	end := afterRune(word, 1)
	name := lowercase(word[:1], false)
	if name == "o" {
		name = "O"
	}
	return name + word[1:end] + upperFirst(word[end:])
}

func startsMcName(word string) bool {
	if len(word) < 4 || (word[:2] != "Mc" && word[:2] != "mc" && word[:2] != "MC") {
		return false
	}
	return wordAt(word, 2) && afterRune(word, 2) < len(word)
}

func isHonorific(word string) bool {
	switch asciiFolded(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

func hasInlinePeriod(word string) bool {
	previousWasWord := false
	for at, ch := range word {
		if ch == '.' && previousWasWord && wordAt(word, at+1) {
			return true
		}
		previousWasWord = properties(ch)&wordChar != 0
	}
	return false
}

func hasInternalUppercase(word string) bool {
	at := skipPunctuation(word)
	for next := at; next < len(word) && asciiLetter(word[next]); next++ {
		if next > at && asciiUpper(word[next]) {
			return true
		}
	}
	return false
}

func isConsonantAcronym(word string) bool {
	count := 0
	for _, ch := range word {
		if folded := foldASCII(ch); !strings.ContainsRune("bcdfghjklmnpqrstvwxz", folded) {
			return false
		}
		count++
	}
	return count > 2
}

func capitalizeWord(word string) string {
	for at, ch := range word {
		if properties(ch)&wordChar != 0 {
			return word[:at] + upperFirst(word[at:])
		}
		if !punctuation(ch) {
			break
		}
	}
	return word
}

func punctuation(ch rune) bool {
	return strings.ContainsRune("!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_\x60{|}~", ch)
}

func skipPunctuation(word string) int {
	for at, ch := range word {
		if !punctuation(ch) {
			return at
		}
	}
	return len(word)
}

func wordAt(value string, at int) bool {
	if at == len(value) {
		return false
	}
	ch, _ := utf8.DecodeRuneInString(value[at:])
	return properties(ch)&wordChar != 0
}

func afterRune(value string, at int) int {
	_, width := utf8.DecodeRuneInString(value[at:])
	return at + width
}

func asciiUpper(ch byte) bool { return ch >= 'A' && ch <= 'Z' }

func asciiLetter(ch byte) bool { return asciiUpper(ch) || ch >= 'a' && ch <= 'z' }
