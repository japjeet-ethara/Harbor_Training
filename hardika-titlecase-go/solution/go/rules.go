package main

import (
	"regexp"
	"strings"
)

const smallPattern = "a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\\.?|via|vs\\.?"
const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

var (
	smallWords = strings.Split(smallPattern, "|")
	smallToken = regexp.MustCompile("^(?:" + smallPattern + ")$")
	honorific  = regexp.MustCompile("^(?:mr|mrs|ms|dr)$")
	mcPrefix   = regexp.MustCompile("^(?:[Mm]c|MC)")
	subphrase  = regexp.MustCompile("[:.;?!–‒—―-] (?:" + smallPattern + ")")
)

func wordRules() [9]rule {
	return [9]rule{
		{when(isInitials), unchanged},
		{when(isApostropheName), rewriteApostrophe},
		{matchMc, rewriteMc},
		{when(isHonorific), uppercaseFirst},
		{when(keepInternalCase), unchanged},
		{when(isSmall), lowercaseWord},
		{when(isSlashCompound), rewriteSlash},
		{when(isHyphenCompound), rewriteHyphen},
		{when(always), rewriteDefault},
	}
}

func when(predicate func(token) bool) matcher {
	return func(current token) (span, bool) {
		return span{0, len(current.chars)}, predicate(current)
	}
}

func always(token) bool { return true }

func isPunctuation(ch rune) bool {
	return strings.ContainsRune(punctuation, ch)
}

func isInitials(current token) bool {
	if !current.allCaps {
		return false
	}
	chars := current.chars
	for i := 0; i < len(chars); {
		if i+1 >= len(chars) || !has(chars[i], uppercaseLetter) || chars[i+1] != '.' {
			return false
		}
		i += 2
		if i < len(chars) && has(chars[i], uppercaseLetter) &&
			(i+1 == len(chars) || chars[i+1] != '.') {
			i++
		}
	}
	return true
}

func isApostropheName(current token) bool {
	chars := current.chars
	if len(chars) < 3 || !strings.ContainsRune("dol", rune(asciiFold(chars[0]))) ||
		(chars[1] != '\'' && chars[1] != '‘') {
		return false
	}
	index := 2
	for index < len(chars) && has(chars[index], letter) {
		index++
	}
	if index == len(chars) {
		return true
	}
	if index == 2 || len(chars)-index != 2 {
		return false
	}
	for _, ch := range chars[index:] {
		if ch != '\'' && asciiFold(ch) != 's' {
			return false
		}
	}
	return true
}

func matchMc(current token) (span, bool) {
	return span{2, len(current.chars)}, len(current.chars) >= 4 &&
		mcPrefix.MatchString(current.text) && has(current.chars[2], wordCharacter)
}

func asciiForm(chars []rune) string {
	var result strings.Builder
	for _, ch := range chars {
		if folded := asciiFold(ch); folded != 0 {
			result.WriteByte(folded)
		} else if ch == '.' {
			result.WriteByte('.')
		} else {
			return ""
		}
	}
	return result.String()
}

func isHonorific(current token) bool {
	return len(current.chars) <= 3 && honorific.MatchString(asciiForm(current.chars))
}

func keepInternalCase(current token) bool {
	chars := current.chars
	for i := 1; i+1 < len(chars); i++ {
		if chars[i] == '.' && has(chars[i-1], letter) && has(chars[i+1], letter) {
			return true
		}
	}
	if current.allCaps {
		return false
	}
	start := skipPunctuation(chars)
	for i := start; i < len(chars) && has(chars[i], letter); i++ {
		if i > start && has(chars[i], uppercaseLetter) {
			return true
		}
	}
	return false
}

func isSmall(current token) bool {
	return len(current.chars) <= 4 && smallToken.MatchString(asciiForm(current.chars))
}

func isSlashCompound(current token) bool {
	return strings.Contains(current.text, "/") && !strings.Contains(current.text, "//")
}

func isHyphenCompound(current token) bool {
	return strings.Contains(current.text, "-")
}

func skipPunctuation(chars []rune) int {
	index := 0
	for index < len(chars) && isPunctuation(chars[index]) {
		index++
	}
	return index
}

func wordBoundary(chars []rune, index int) bool {
	left := index > 0 && has(chars[index-1], wordCharacter)
	right := index < len(chars) && has(chars[index], wordCharacter)
	return left != right
}

func matchSmallPrefix(chars []rune, start int, acceptEnd func(int) bool) (span, bool) {
	for _, alternative := range smallWords {
		base, optionalDot := strings.CutSuffix(alternative, "\\.?")
		end := start + len(base)
		if end > len(chars) || asciiForm(chars[start:end]) != base {
			continue
		}
		if optionalDot && end < len(chars) && chars[end] == '.' && acceptEnd(end+1) {
			return span{start, end + 1}, true
		}
		if acceptEnd(end) {
			return span{start, end}, true
		}
	}
	return span{}, false
}

func firstSmall(current token) (span, bool) {
	chars := current.chars
	return matchSmallPrefix(chars, skipPunctuation(chars), func(end int) bool {
		return wordBoundary(chars, end)
	})
}

func lastSmall(current token) (span, bool) {
	chars := current.chars
	for start := max(0, len(chars)-5); start < len(chars); start++ {
		if !wordBoundary(chars, start) {
			continue
		}
		match, ok := matchSmallPrefix(chars, start, func(end int) bool {
			return end == len(chars) || (end+1 == len(chars) && isPunctuation(chars[end]))
		})
		if ok {
			match.end = len(chars)
			return match, true
		}
	}
	return span{}, false
}
