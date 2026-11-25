#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Delete all .py files and old python package directory
find /workspace/repo -name "*.py" -type f -delete
rm -rf /workspace/repo/titlecase

# Create go.mod
cat << 'EOF' > go.mod
module titlecase

go 1.23
EOF

# Create main.go
cat << 'EOF' > main.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
	"unicode/utf8"
)

var (
	smallWordsMap = map[string]bool{
		"a":   true,
		"an":  true,
		"and": true,
		"as":  true,
		"at":  true,
		"but": true,
		"by":  true,
		"en":  true,
		"for": true,
		"if":  true,
		"in":  true,
		"of":  true,
		"on":  true,
		"or":  true,
		"the": true,
		"to":  true,
		"v":   true,
		"v.":  true,
		"via": true,
		"vs":  true,
		"vs.": true,
	}

	punctSet = map[rune]bool{
		'!': true, '"': true, '#': true, '$': true, '%': true, '&': true, '\'': true,
		'(': true, ')': true, '*': true, '+': true, ',': true, '-': true, '.': true,
		'/': true, ':': true, ';': true, '?': true, '@': true, '[': true, '\\': true,
		']': true, '_': true, '`': true, '{': true, '|': true, '}': true, '~': true,
		'“': true, '‘': true, '–': true, '‒': true, '—': true, '―': true,
	}

	consonantsSet = map[rune]bool{
		'b': true, 'c': true, 'd': true, 'f': true, 'g': true, 'h': true, 'j': true,
		'k': true, 'l': true, 'm': true, 'n': true, 'p': true, 'q': true, 'r': true,
		's': true, 't': true, 'v': true, 'w': true, 'x': true, 'z': true,
	}

	ucInitialsRe   = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
	inlinePeriodRe = regexp.MustCompile(`[\w]\.[\w]`)
	macMcRe        = regexp.MustCompile(`^([Mm]c|MC)(\w.+)`)
	mrMrsRe        = regexp.MustCompile(`(?i)^((m((rs?)|s))|Dr)$`)
)

func capitalize(s string) string {
	if s == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + strings.ToLower(s[size:])
}

func isSmallWord(w string) bool {
	return smallWordsMap[strings.ToLower(w)]
}

func matchAposSecond(word string) (string, bool) {
	if len(word) < 3 {
		return "", false
	}
	first := word[0]
	if first != 'd' && first != 'D' && first != 'o' && first != 'O' && first != 'l' && first != 'L' {
		return "", false
	}
	secondRune, secondSize := utf8.DecodeRuneInString(word[1:])
	if secondRune != '\'' && secondRune != '‘' {
		return "", false
	}
	rest := word[1+secondSize:]
	if len(rest) == 0 {
		return "", false
	}
	trimmed := rest
	if len(rest) >= 3 {
		end2 := rest[len(rest)-2:]
		c1, c2 := end2[0], end2[1]
		if (c1 == '\'' || c1 == 's' || c1 == 'S') && (c2 == '\'' || c2 == 's' || c2 == 'S') {
			trimmed = rest[:len(rest)-2]
		}
	}
	if len(trimmed) == 0 {
		return "", false
	}
	for _, r := range trimmed {
		if !unicode.IsLetter(r) && !unicode.IsDigit(r) && r != '_' {
			return "", false
		}
	}

	r2, size2 := utf8.DecodeRuneInString(rest)
	rem := rest[size2:]

	var newFirst string
	if first == 'o' || first == 'O' {
		newFirst = string(unicode.ToUpper(rune(first)))
	} else {
		newFirst = string(unicode.ToLower(rune(first)))
	}
	return newFirst + string(secondRune) + string(unicode.ToUpper(r2)) + rem, true
}

func matchUcElsewhere(word string) bool {
	idx := 0
	for idx < len(word) {
		r, size := utf8.DecodeRuneInString(word[idx:])
		if punctSet[r] {
			idx += size
		} else {
			break
		}
	}
	sub := word[idx:]
	hasLetter := false
	for i, r := range sub {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') {
			if hasLetter && (r >= 'A' && r <= 'Z') && i > 0 {
				return true
			}
			hasLetter = true
		} else {
			if !hasLetter {
				return false
			}
			break
		}
	}
	return false
}

func isAllConsonants(word string) bool {
	if len(word) <= 2 {
		return false
	}
	for _, r := range strings.ToLower(word) {
		if !consonantsSet[r] {
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	idx := 0
	for idx < len(word) {
		r, size := utf8.DecodeRuneInString(word[idx:])
		if punctSet[r] {
			idx += size
		} else {
			break
		}
	}
	if idx >= len(word) {
		return word
	}
	r, size := utf8.DecodeRuneInString(word[idx:])
	if unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_' {
		return word[:idx] + string(unicode.ToUpper(r)) + word[idx+size:]
	}
	return word
}

func applySmallFirst(word string) string {
	idx := 0
	for idx < len(word) {
		r, size := utf8.DecodeRuneInString(word[idx:])
		if punctSet[r] {
			idx += size
		} else {
			break
		}
	}
	prefix := word[:idx]
	rest := word[idx:]
	for sw := range smallWordsMap {
		if strings.HasPrefix(strings.ToLower(rest), sw) {
			after := rest[len(sw):]
			if len(after) == 0 {
				return prefix + capitalize(sw)
			}
			r, _ := utf8.DecodeRuneInString(after)
			if !unicode.IsLetter(r) && !unicode.IsDigit(r) && r != '_' {
				return prefix + capitalize(sw) + after
			}
		}
	}
	return word
}

func applySmallLast(word string) string {
	punctSuffix := ""
	rest := word
	if len(word) > 0 {
		r, size := utf8.DecodeLastRuneInString(word)
		if punctSet[r] {
			punctSuffix = string(r)
			rest = word[:len(word)-size]
		}
	}

	for sw := range smallWordsMap {
		if strings.HasSuffix(strings.ToLower(rest), sw) {
			before := rest[:len(rest)-len(sw)]
			if len(before) == 0 {
				return capitalize(sw) + punctSuffix
			}
			r, _ := utf8.DecodeLastRuneInString(before)
			if !unicode.IsLetter(r) && !unicode.IsDigit(r) && r != '_' {
				return before + capitalize(sw) + punctSuffix
			}
		}
	}
	return word
}

func applySubphrase(text string) string {
	delims := []string{": ", "; ", ". ", "? ", "! ", "- ", "– ", "— ", "― "}
	for _, delim := range delims {
		for sw := range smallWordsMap {
			pattern := delim + sw
			start := 0
			for {
				idx := strings.Index(text[start:], pattern)
				if idx == -1 {
					break
				}
				matchPos := start + idx
				afterPos := matchPos + len(pattern)
				isBoundary := false
				if afterPos == len(text) {
					isBoundary = true
				} else {
					r, _ := utf8.DecodeRuneInString(text[afterPos:])
					if !unicode.IsLetter(r) && !unicode.IsDigit(r) && r != '_' {
						isBoundary = true
					}
				}
				if isBoundary {
					replacement := delim + capitalize(sw)
					text = text[:matchPos] + replacement + text[afterPos:]
					start = matchPos + len(replacement)
				} else {
					start = matchPos + 1
				}
			}
		}
	}
	return text
}

func splitWhitespace(line string) ([]string, []string) {
	var words []string
	var spaces []string
	start := 0
	inSpace := false
	currentWordStart := 0

	for i, r := range line {
		if unicode.IsSpace(r) {
			if !inSpace {
				words = append(words, line[currentWordStart:i])
				start = i
				inSpace = true
			} else {
				spaces = append(spaces, line[start:i])
				words = append(words, "")
				start = i
			}
		} else {
			if inSpace {
				spaces = append(spaces, line[start:i])
				currentWordStart = i
				inSpace = false
			}
		}
	}
	if inSpace {
		spaces = append(spaces, line[start:])
		words = append(words, "")
	} else {
		words = append(words, line[currentWordStart:])
	}
	return words, spaces
}

func Titlecase(text string, smallFirstLast bool) string {
	if text == "" {
		return ""
	}
	lines := strings.Split(text, "\n")
	var processed []string

	for _, line := range lines {
		allCaps := (line == strings.ToUpper(line))
		words, spaces := splitWhitespace(line)

		var tcLine []string
		for _, word := range words {
			if word == "" {
				tcLine = append(tcLine, "")
				continue
			}

			if allCaps && ucInitialsRe.MatchString(word) {
				tcLine = append(tcLine, word)
				continue
			}

			if aposWord, matched := matchAposSecond(word); matched {
				tcLine = append(tcLine, aposWord)
				continue
			}

			if macMcMatch := macMcRe.FindStringSubmatch(word); macMcMatch != nil {
				prefix := capitalize(macMcMatch[1])
				rest := Titlecase(macMcMatch[2], true)
				tcLine = append(tcLine, prefix+rest)
				continue
			}

			if mrMrsRe.MatchString(word) {
				r, size := utf8.DecodeRuneInString(word)
				word = string(unicode.ToUpper(r)) + word[size:]
				tcLine = append(tcLine, word)
				continue
			}

			if inlinePeriodRe.MatchString(word) || (!allCaps && matchUcElsewhere(word)) {
				tcLine = append(tcLine, word)
				continue
			}

			if isSmallWord(word) {
				tcLine = append(tcLine, strings.ToLower(word))
				continue
			}

			if strings.Contains(word, "/") && !strings.Contains(word, "//") {
				parts := strings.Split(word, "/")
				for i, p := range parts {
					parts[i] = Titlecase(p, false)
				}
				tcLine = append(tcLine, strings.Join(parts, "/"))
				continue
			}

			if strings.Contains(word, "-") {
				parts := strings.Split(word, "-")
				for i, p := range parts {
					parts[i] = Titlecase(p, false)
				}
				tcLine = append(tcLine, strings.Join(parts, "-"))
				continue
			}

			if allCaps {
				word = strings.ToLower(word)
			}

			if isAllConsonants(word) {
				tcLine = append(tcLine, strings.ToUpper(word))
				continue
			}

			tcLine = append(tcLine, capFirst(word))
		}

		if smallFirstLast && len(tcLine) > 0 {
			tcLine[0] = applySmallFirst(tcLine[0])
			tcLine[len(tcLine)-1] = applySmallLast(tcLine[len(tcLine)-1])
		}

		var sb strings.Builder
		for i := 0; i < len(tcLine); i++ {
			sb.WriteString(tcLine[i])
			if i < len(spaces) {
				sb.WriteString(spaces[i])
			}
		}
		result := sb.String()
		result = applySubphrase(result)
		processed = append(processed, result)
	}

	return strings.Join(processed, "\n")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		fmt.Println(Titlecase(scanner.Text(), true))
	}
}
EOF

# Build to verify compilation
go build ./...
