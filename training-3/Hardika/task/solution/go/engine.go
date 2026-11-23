package main

import (
	"regexp"
	"strings"
)

type token struct {
	text    string
	chars   []rune
	allCaps bool
}

type span struct {
	start, end int
}

type matcher func(token) (span, bool)
type rewrite func(token, span) string

type rule struct {
	match matcher
	apply rewrite
}

var lineBreak = regexp.MustCompile("[\r\n]+")

func titlecase(text string, fixEdges bool) string {
	lines := lineBreak.Split(text, -1)
	for i, line := range lines {
		lines[i] = transformLine(line, fixEdges)
	}
	return strings.Join(lines, "\n")
}

func transformLine(line string, fixEdges bool) string {
	caps := allUpper(line)
	var words, separators []string
	start := 0
	for index, ch := range line {
		if has(ch, spaceCharacter) {
			words = append(words, transformWord(line[start:index], caps))
			separators = append(separators, string(ch))
			start = index + len(string(ch))
		}
	}
	words = append(words, transformWord(line[start:], caps))
	if fixEdges {
		words[0] = applyEdge(words[0], firstSmall)
		last := len(words) - 1
		words[last] = applyEdge(words[last], lastSmall)
	}
	var joined strings.Builder
	joined.Grow(len(line))
	for i, separator := range separators {
		joined.WriteString(words[i])
		joined.WriteString(separator)
	}
	joined.WriteString(words[len(words)-1])
	return subphrase.ReplaceAllStringFunc(joined.String(), func(match string) string {
		space := strings.IndexByte(match, ' ') + 1
		return match[:space] + capitalize(match[space:])
	})
}

func transformWord(text string, allCaps bool) string {
	if text == "" {
		return text
	}
	current := token{text: text, chars: []rune(text), allCaps: allCaps}
	for _, candidate := range wordRules() {
		if match, ok := candidate.match(current); ok {
			return candidate.apply(current, match)
		}
	}
	return text
}

func applyEdge(text string, find matcher) string {
	current := token{text: text, chars: []rune(text)}
	if match, ok := find(current); ok {
		return string(current.chars[:match.start]) +
			capitalize(string(current.chars[match.start:match.end])) +
			string(current.chars[match.end:])
	}
	return text
}
