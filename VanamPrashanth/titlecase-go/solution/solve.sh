#!/bin/bash
set -euo pipefail

cd /workspace/repo

# 1. Create go.mod
cat << 'EOF' > go.mod
module repo

go 1.23
EOF

# 2. Create main.go with the complete standard-library Go port of titlecase
cat << 'EOF' > main.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
)

// PUNCT punctuation characters as defined in original python-titlecase:
// !"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~
func isPunct(r rune) bool {
	switch r {
	case '!', '"', '“', '#', '$', '%', '&', '\'', '‘', '(', ')', '*', '+', ',',
		'-', '–', '‒', '—', '―', '.', '/', ':', ';', '?', '@', '[', '\\', ']',
		'_', '`', '{', '|', '}', '~':
		return true
	}
	return false
}

// isWordChar checks if r is a Python \w character (letter, digit, or underscore)
func isWordChar(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

// Small words as defined in original python-titlecase:
// a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?
var smallWords = map[string]bool{
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

var smallWordsList = []string{
	"and", "the", "via", "but", "for", "vs.", "vs", "an", "as", "at",
	"by", "en", "if", "in", "of", "on", "or", "to", "v.", "v", "a",
}

var subphraseRegex = regexp.MustCompile(`([:.;?!–‒—―-] )(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)`)

func splitLine(line string) ([]string, []string) {
	var words []string
	var spaces []string
	var curWord []rune

	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, string(curWord))
			spaces = append(spaces, string(r))
			curWord = nil
		} else {
			curWord = append(curWord, r)
		}
	}
	words = append(words, string(curWord))
	return words, spaces
}

func isUCInitials(word string) bool {
	runes := []rune(word)
	if len(runes) < 2 {
		return false
	}
	for i, r := range runes {
		if i%2 == 0 {
			if !unicode.IsUpper(r) || !unicode.IsLetter(r) {
				return false
			}
		} else {
			if r != '.' {
				return false
			}
		}
	}
	return true
}

func matchAposSecond(word string) (string, bool) {
	runes := []rune(word)
	if len(runes) < 3 {
		return "", false
	}
	r0 := unicode.ToLower(runes[0])
	if r0 != 'd' && r0 != 'o' && r0 != 'l' {
		return "", false
	}
	if runes[1] != '\'' && runes[1] != '‘' {
		return "", false
	}
	if !isWordChar(runes[2]) {
		return "", false
	}

	end := len(runes)
	if len(runes) >= 5 {
		c1 := unicode.ToLower(runes[len(runes)-2])
		c2 := unicode.ToLower(runes[len(runes)-1])
		if (c1 == '\'' || c1 == 's') && (c2 == '\'' || c2 == 's') {
			end = len(runes) - 2
		}
	}

	for i := 2; i < end; i++ {
		if !isWordChar(runes[i]) {
			return "", false
		}
	}

	var first rune
	if r0 == 'o' {
		first = 'O'
	} else {
		first = r0
	}
	second := runes[1]
	third := unicode.ToUpper(runes[2])
	rest := string(runes[3:])
	return string(first) + string(second) + string(third) + rest, true
}

func matchMrMrsMsDr(word string) (string, bool) {
	low := strings.ToLower(word)
	if low == "mr" || low == "mrs" || low == "ms" || low == "dr" {
		runes := []rune(word)
		return string(unicode.ToUpper(runes[0])) + string(runes[1:]), true
	}
	return "", false
}

func hasInlinePeriod(word string) bool {
	runes := []rune(word)
	for i := 0; i+2 < len(runes); i++ {
		if isWordChar(runes[i]) && runes[i+1] == '.' && isWordChar(runes[i+2]) {
			return true
		}
	}
	return false
}

func matchUCElsewhere(word string) bool {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	if i >= len(runes) || !unicode.IsLetter(runes[i]) {
		return false
	}
	i++
	for i < len(runes) && unicode.IsLetter(runes[i]) {
		if unicode.IsUpper(runes[i]) {
			return true
		}
		i++
	}
	return false
}

func isAllConsonants(word string) bool {
	if len(word) <= 2 {
		return false
	}
	for i := 0; i < len(word); i++ {
		b := word[i]
		if (b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z') {
			lower := b
			if lower >= 'A' && lower <= 'Z' {
				lower += 32
			}
			if lower == 'a' || lower == 'e' || lower == 'i' || lower == 'o' || lower == 'u' || lower == 'y' {
				return false
			}
		} else {
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	runes := []rune(word)
	for i, r := range runes {
		if isPunct(r) {
			continue
		}
		if isWordChar(r) {
			runes[i] = unicode.ToUpper(r)
			return string(runes)
		}
		break
	}
	return word
}

func applySmallFirst(word string) string {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	prefix := string(runes[:i])
	rem := string(runes[i:])
	if len(rem) == 0 {
		return word
	}

	remLow := strings.ToLower(rem)
	remRunes := []rune(rem)
	for _, sm := range smallWordsList {
		checkSm := sm
		if sm == "v." || sm == "vs." {
			checkSm = sm[:len(sm)-1] // "v" or "vs"
		}
		if strings.HasPrefix(remLow, checkSm) {
			checkSmRunes := []rune(checkSm)
			pos := len(checkSmRunes)
			if pos == len(remRunes) || !isWordChar(remRunes[pos]) {
				capSm := string(unicode.ToUpper(checkSmRunes[0])) + string(checkSmRunes[1:])
				return prefix + capSm + string(remRunes[pos:])
			}
		}
	}
	return word
}

func applySmallLast(word string) string {
	if len(word) == 0 {
		return word
	}
	runes := []rune(word)
	endIdx := len(runes)
	if endIdx >= 1 && isPunct(runes[endIdx-1]) {
		endIdx--
	}

	rem := string(runes[:endIdx])
	remLow := strings.ToLower(rem)
	remRunes := []rune(rem)

	for _, sm := range smallWordsList {
		if strings.HasSuffix(remLow, sm) {
			smRunes := []rune(sm)
			startPos := len(remRunes) - len(smRunes)
			if startPos == 0 || !isWordChar(remRunes[startPos-1]) {
				matched := runes[startPos:]
				matched[0] = unicode.ToUpper(matched[0])
				return string(runes[:startPos]) + string(matched)
			}
		}
	}
	return word
}

func Titlecase(text string, smallFirstLast bool) string {
	var lines []string
	var curLine []rune
	runes := []rune(text)
	i := 0
	for i < len(runes) {
		if runes[i] == '\r' || runes[i] == '\n' {
			if len(curLine) > 0 {
				lines = append(lines, string(curLine))
				curLine = nil
			}
			for i < len(runes) && (runes[i] == '\r' || runes[i] == '\n') {
				i++
			}
		} else {
			curLine = append(curLine, runes[i])
			i++
		}
	}
	if len(curLine) > 0 {
		lines = append(lines, string(curLine))
	}
	if len(lines) == 0 {
		return ""
	}

	var processed []string
	for _, line := range lines {
		allCaps := strings.ToUpper(line) == line
		words, spaces := splitLine(line)
		var tcLine []string

		for _, word := range words {
			if allCaps {
				if isUCInitials(word) {
					tcLine = append(tcLine, word)
					continue
				}
			}

			if res, ok := matchAposSecond(word); ok {
				tcLine = append(tcLine, res)
				continue
			}

			wordRunes := []rune(word)
			if len(wordRunes) >= 4 {
				pfx := string(wordRunes[:2])
				if (pfx == "mc" || pfx == "Mc" || pfx == "MC") && isWordChar(wordRunes[2]) {
					tcLine = append(tcLine, "Mc"+Titlecase(string(wordRunes[2:]), true))
					continue
				}
			}

			if res, ok := matchMrMrsMsDr(word); ok {
				tcLine = append(tcLine, res)
				continue
			}

			if hasInlinePeriod(word) || (!allCaps && matchUCElsewhere(word)) {
				tcLine = append(tcLine, word)
				continue
			}

			if smallWords[strings.ToLower(word)] {
				tcLine = append(tcLine, strings.ToLower(word))
				continue
			}

			if strings.Contains(word, "/") && !strings.Contains(word, "//") {
				parts := strings.Split(word, "/")
				for j, part := range parts {
					parts[j] = Titlecase(part, false)
				}
				tcLine = append(tcLine, strings.Join(parts, "/"))
				continue
			}

			if strings.Contains(word, "-") {
				parts := strings.Split(word, "-")
				for j, part := range parts {
					parts[j] = Titlecase(part, false)
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

		var lineParts []string
		for idx := range words {
			lineParts = append(lineParts, tcLine[idx])
			if idx < len(spaces) {
				lineParts = append(lineParts, spaces[idx])
			}
		}
		result := strings.Join(lineParts, "")

		// Subphrase
		result = subphraseRegex.ReplaceAllStringFunc(result, func(m string) string {
			idx := strings.Index(m, " ")
			if idx != -1 && idx+1 < len(m) {
				prefix := m[:idx+1]
				w := m[idx+1:]
				wRunes := []rune(w)
				wRunes[0] = unicode.ToUpper(wRunes[0])
				return prefix + string(wRunes)
			}
			return m
		})

		processed = append(processed, result)
	}

	return strings.Join(processed, "\n")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	const maxCapacity = 10 * 1024 * 1024
	buf := make([]byte, 64*1024)
	scanner.Buffer(buf, maxCapacity)

	for scanner.Scan() {
		line := scanner.Text()
		fmt.Println(Titlecase(line, true))
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, "reading standard input:", err)
		os.Exit(1)
	}
}
EOF

# 3. Build Go program to confirm it passes
go build ./...

# 4. Remove all .py files anywhere under /workspace/repo
find /workspace/repo -type f -name "*.py" -delete
find /workspace/repo -name "*.pyc" -delete 2>/dev/null || true
find /workspace/repo -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
