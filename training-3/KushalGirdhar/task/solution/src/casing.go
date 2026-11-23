package main

import (
	"sort"
	"strings"
	"unicode/utf8"
)

const (
	wordChar uint8 = 1 << iota
	space
	caseIgnorable
	cased
)

type propertyRange struct {
	first, last rune
	flags       uint8
}

func properties(ch rune) uint8 {
	index := sort.Search(len(pythonProperties), func(i int) bool {
		return pythonProperties[i].last >= ch
	})
	if index < len(pythonProperties) && pythonProperties[index].first <= ch {
		return pythonProperties[index].flags
	}
	return 0
}

func foldASCII(ch rune) rune {
	switch ch {
	case 'İ', 'ı':
		return 'i'
	case 'ſ':
		return 's'
	case 'K':
		return 'k'
	}
	if ch >= 'A' && ch <= 'Z' {
		return ch + ('a' - 'A')
	}
	return ch
}

func asciiFolded(s string) string {
	return strings.Map(foldASCII, s)
}

func unchangedByUppercase(value string) bool {
	for _, ch := range value {
		if _, ok := pythonUpper[ch]; ok {
			return false
		}
	}
	return true
}

func appendMapping(result *strings.Builder, lookup map[rune]string, ch rune) {
	if mapped, ok := lookup[ch]; ok {
		result.WriteString(mapped)
	} else {
		result.WriteRune(ch)
	}
}

func upperFirst(value string) string {
	ch, width := utf8.DecodeRuneInString(value)
	if mapped, ok := pythonUpper[ch]; ok {
		return mapped + value[width:]
	}
	return value
}

func uppercase(value string) string {
	var result strings.Builder
	result.Grow(len(value))
	for _, ch := range value {
		appendMapping(&result, pythonUpper, ch)
	}
	return result.String()
}

func lowercase(value string, capitalize bool) string {
	var result strings.Builder
	result.Grow(len(value))
	previousCased := false
	for at, ch := range value {
		flags := properties(ch)
		switch {
		case capitalize && at == 0:
			appendMapping(&result, pythonTitle, ch)
		case ch == 'Σ' && previousCased && !nextIsCased(value[at+utf8.RuneLen(ch):]):
			result.WriteRune('ς')
		default:
			appendMapping(&result, pythonLower, ch)
		}
		if flags&caseIgnorable == 0 {
			previousCased = flags&cased != 0
		}
	}
	return result.String()
}

func nextIsCased(value string) bool {
	for _, ch := range value {
		flags := properties(ch)
		if flags&caseIgnorable == 0 {
			return flags&cased != 0
		}
	}
	return false
}
