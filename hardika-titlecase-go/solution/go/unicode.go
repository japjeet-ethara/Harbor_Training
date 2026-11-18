package main

import (
	"sort"
	"strings"
)

type property uint8

const (
	letter property = 1 << iota
	uppercaseLetter
	wordCharacter
	spaceCharacter
	consonant
	sigmaIgnorable
	sigmaCased
)

type propertyRange struct {
	first, last rune
	flags       property
	fold        byte
}

type caseMapping struct {
	upper, lower, title string
}

func properties(ch rune) propertyRange {
	index := sort.Search(len(pythonProperties), func(i int) bool {
		return pythonProperties[i].last >= ch
	})
	if index < len(pythonProperties) && pythonProperties[index].first <= ch {
		return pythonProperties[index]
	}
	return propertyRange{}
}

func has(ch rune, mask property) bool {
	return properties(ch).flags&mask != 0
}

func asciiFold(ch rune) byte {
	return properties(ch).fold
}

func charUpper(ch rune) string {
	if value := pythonCases[ch].upper; value != "" {
		return value
	}
	return string(ch)
}

func allUpper(text string) bool {
	for _, ch := range text {
		if pythonCases[ch].upper != "" {
			return false
		}
	}
	return true
}

func upper(text string) string {
	var result strings.Builder
	for _, ch := range text {
		result.WriteString(charUpper(ch))
	}
	return result.String()
}

func adjacentCased(chars []rune, index, step int) bool {
	for index += step; index >= 0 && index < len(chars); index += step {
		flags := properties(chars[index]).flags
		if flags&sigmaIgnorable == 0 {
			return flags&sigmaCased != 0
		}
	}
	return false
}

func lowerChar(chars []rune, index int) string {
	ch := chars[index]
	if ch == 'Σ' && adjacentCased(chars, index, -1) && !adjacentCased(chars, index, 1) {
		return "ς"
	}
	if value := pythonCases[ch].lower; value != "" {
		return value
	}
	return string(ch)
}

func lower(text string) string {
	chars := []rune(text)
	var result strings.Builder
	for i := range chars {
		result.WriteString(lowerChar(chars, i))
	}
	return result.String()
}

func capitalize(text string) string {
	chars := []rune(text)
	if len(chars) == 0 {
		return ""
	}
	var result strings.Builder
	if first := pythonCases[chars[0]].title; first != "" {
		result.WriteString(first)
	} else {
		result.WriteRune(chars[0])
	}
	for i := 1; i < len(chars); i++ {
		result.WriteString(lowerChar(chars, i))
	}
	return result.String()
}
