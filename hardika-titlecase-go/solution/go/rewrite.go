package main

import "strings"

func unchanged(current token, _ span) string { return current.text }

func lowercaseWord(current token, _ span) string { return lower(current.text) }

func uppercaseFirst(current token, _ span) string {
	return charUpper(current.chars[0]) + string(current.chars[1:])
}

func rewriteApostrophe(current token, _ span) string {
	chars := current.chars
	first := lowerChar(chars[:1], 0)
	if strings.ContainsRune("aeiouAEIOU", chars[0]) {
		first = charUpper(chars[0])
	}
	return first + string(chars[1]) + charUpper(chars[2]) + string(chars[3:])
}

func rewriteMc(current token, match span) string {
	return "Mc" + titlecase(string(current.chars[match.start:match.end]), true)
}

func rewriteCompound(text, separator string) string {
	pieces := strings.Split(text, separator)
	for i, piece := range pieces {
		pieces[i] = titlecase(piece, false)
	}
	return strings.Join(pieces, separator)
}

func rewriteSlash(current token, _ span) string {
	return rewriteCompound(current.text, "/")
}

func rewriteHyphen(current token, _ span) string {
	return rewriteCompound(current.text, "-")
}

func rewriteDefault(current token, _ span) string {
	text, chars := current.text, current.chars
	if current.allCaps {
		text = lower(text)
		chars = []rune(text)
	}
	if allConsonants(chars) {
		return upper(text)
	}
	index := skipPunctuation(chars)
	if index < len(chars) && has(chars[index], letter) {
		return string(chars[:index]) + charUpper(chars[index]) + string(chars[index+1:])
	}
	return text
}

func allConsonants(chars []rune) bool {
	if len(chars) <= 2 {
		return false
	}
	for _, ch := range chars {
		if !has(ch, consonant) {
			return false
		}
	}
	return true
}
