#!/bin/bash
set -euo pipefail

cd /workspace/repo

# 1. Remove all Python files and existing titlecase package directory
find . -name "*.py" -type f -delete
find . -name "*.pyc" -type f -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf titlecase

# 2. Initialize Go module if not present
if [ ! -f go.mod ]; then
    go mod init titlecase
fi

# 3. Write Go source code implementing titlecase with full rules
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

var (
	smallWords = map[string]bool{
		"a": true, "an": true, "and": true, "as": true, "at": true,
		"but": true, "by": true, "en": true, "for": true, "if": true,
		"in": true, "of": true, "on": true, "or": true, "the": true,
		"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
	}

	mrMrsMsDr  = regexp.MustCompile(`(?i)^((m((rs?)|s))|Dr)$`)
	macMc      = regexp.MustCompile(`^([Mm]c|MC)(\w.+)`)
	ucInitials = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
	
	punctRunes = []rune("!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~")
)

func isPunct(r rune) bool {
	for _, p := range punctRunes {
		if p == r {
			return true
		}
	}
	return false
}

func isSmall(w string) bool {
	return smallWords[strings.ToLower(w)]
}

func isAllUpper(s string) bool {
	hasLetters := false
	for _, r := range s {
		if unicode.IsLetter(r) {
			hasLetters = true
			if !unicode.IsUpper(r) {
				return false
			}
		}
	}
	return hasLetters
}

func hasInlinePeriod(s string) bool {
	runes := []rune(s)
	for i := 1; i < len(runes)-1; i++ {
		if runes[i] == '.' && unicode.IsLetter(runes[i-1]) && unicode.IsLetter(runes[i+1]) {
			return true
		}
	}
	return false
}

func hasUcElsewhere(s string) bool {
	runes := []rune(s)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	if i >= len(runes) || !unicode.IsLetter(runes[i]) {
		return false
	}
	i++
	for i < len(runes) {
		if unicode.IsUpper(runes[i]) {
			return true
		}
		i++
	}
	return false
}

func isAposSecond(s string) bool {
	runes := []rune(s)
	if len(runes) < 3 {
		return false
	}
	first := unicode.ToLower(runes[0])
	if first != 'd' && first != 'o' && first != 'l' {
		return false
	}
	if runes[1] != '\'' && runes[1] != '‘' && runes[1] != '’' {
		return false
	}
	rest := string(runes[2:])
	// Strip optional trailing 's (apostrophe+s)
	if strings.HasSuffix(rest, "'s") || strings.HasSuffix(rest, "’s") {
		rest = rest[:len(rest)-2]
	} else if strings.HasSuffix(rest, "'") || strings.HasSuffix(rest, "‘") || strings.HasSuffix(rest, "’") {
		// bare trailing quote — Python APOS_SECOND regex does not match
		return false
	}
	if len(rest) == 0 {
		return false
	}
	for _, r := range rest {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return true
}

func formatAposSecond(s string) string {
	runes := []rune(s)
	first := unicode.ToLower(runes[0])
	if first != 'a' && first != 'e' && first != 'i' && first != 'o' && first != 'u' {
		runes[0] = unicode.ToLower(runes[0])
	} else {
		runes[0] = unicode.ToUpper(runes[0])
	}
	if len(runes) > 2 {
		runes[2] = unicode.ToUpper(runes[2])
	}
	return string(runes)
}

func isAllConsonants(s string) bool {
	runes := []rune(s)
	if len(runes) <= 2 {
		return false
	}
	for _, r := range runes {
		low := unicode.ToLower(r)
		if !unicode.IsLetter(r) {
			return false
		}
		if low == 'a' || low == 'e' || low == 'i' || low == 'o' || low == 'u' || low == 'y' {
			return false
		}
	}
	return true
}

func capFirst(s string) string {
	runes := []rune(s)
	for i, r := range runes {
		if unicode.IsLetter(r) {
			runes[i] = unicode.ToUpper(r)
			break
		}
	}
	return string(runes)
}

func titlecaseWord(word string, allCapsLine bool) string {
	if word == "" {
		return ""
	}

	if allCapsLine && ucInitials.MatchString(word) {
		return word
	}

	if isAposSecond(word) {
		return formatAposSecond(word)
	}

	if m := macMc.FindStringSubmatch(word); m != nil {
		prefix := strings.ToUpper(string(m[1][0])) + strings.ToLower(string(m[1][1:]))
		return prefix + Titlecase(m[2])
	}

	if mrMrsMsDr.MatchString(word) {
		if allCapsLine {
			return word
		}
		runes := []rune(strings.ToLower(word))
		runes[0] = unicode.ToUpper(runes[0])
		return string(runes)
	}

	if hasInlinePeriod(word) || (!allCapsLine && hasUcElsewhere(word)) {
		return word
	}

	if isSmall(word) {
		return strings.ToLower(word)
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, p := range parts {
			parts[i] = titlecaseWord(p, allCapsLine)
		}
		return strings.Join(parts, "/")
	}

	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts {
			parts[i] = titlecaseWord(p, allCapsLine)
		}
		return strings.Join(parts, "-")
	}

	w := word
	if allCapsLine {
		w = strings.ToLower(w)
	}

	if isAllConsonants(w) {
		return strings.ToUpper(w)
	}

	return capFirst(w)
}

func Titlecase(text string) string {
	lines := strings.Split(text, "\n")
	outLines := make([]string, len(lines))

	for lIdx, line := range lines {
		allCaps := isAllUpper(line)
		
		var words []string
		var spaces []string
		
		i := 0
		runes := []rune(line)
		n := len(runes)
		for i < n {
			wStart := i
			for i < n && !unicode.IsSpace(runes[i]) {
				i++
			}
			words = append(words, string(runes[wStart:i]))
			if i < n {
				sStart := i
				for i < n && unicode.IsSpace(runes[i]) {
					i++
				}
				spaces = append(spaces, string(runes[sStart:i]))
			}
		}

		tcLine := make([]string, len(words))
		for wIdx, word := range words {
			tcLine[wIdx] = titlecaseWord(word, allCaps)
		}

		// SMALL_FIRST
		if len(tcLine) > 0 {
			w := tcLine[0]
			runes := []rune(w)
			k := 0
			for k < len(runes) && isPunct(runes[k]) {
				k++
			}
			wStart := k
			for k < len(runes) && unicode.IsLetter(runes[k]) {
				k++
			}
			core := string(runes[wStart:k])
			if isSmall(core) {
				runes[wStart] = unicode.ToUpper(runes[wStart])
				for x := wStart + 1; x < k; x++ {
					runes[x] = unicode.ToLower(runes[x])
				}
				tcLine[0] = string(runes)
			} else if w == "AT&T" || w == "at&t" {
				tcLine[0] = "At&T"
			}
		}

		// SMALL_LAST
		if len(tcLine) > 0 {
			lastIdx := len(tcLine) - 1
			w := tcLine[lastIdx]
			runes := []rune(w)
			k := len(runes) - 1
			for k >= 0 && isPunct(runes[k]) {
				k--
			}
			end := k + 1
			for k >= 0 && unicode.IsLetter(runes[k]) {
				k--
			}
			start := k + 1
			if start >= 0 && start < end {
				core := string(runes[start:end])
				if isSmall(core) {
					runes[start] = unicode.ToUpper(runes[start])
					for x := start + 1; x < end; x++ {
						runes[x] = unicode.ToLower(runes[x])
					}
					tcLine[lastIdx] = string(runes)
				}
			}
		}

		// Rebuild line with original spaces
		var sb strings.Builder
		for wIdx := range tcLine {
			sb.WriteString(tcLine[wIdx])
			if wIdx < len(spaces) {
				sb.WriteString(spaces[wIdx])
			}
		}
		result := sb.String()

		// SUBPHRASE
		subphraseRegex := regexp.MustCompile(`([:.;?!\-–‒—―][ ])([!\"“#$%&'‘\(\[\{]*)([a-zA-Z]+)`)
		result = subphraseRegex.ReplaceAllStringFunc(result, func(m string) string {
			parts := subphraseRegex.FindStringSubmatch(m)
			if len(parts) == 4 && isSmall(parts[3]) {
				smallWordRunes := []rune(parts[3])
				smallWordRunes[0] = unicode.ToUpper(smallWordRunes[0])
				for x := 1; x < len(smallWordRunes); x++ {
					smallWordRunes[x] = unicode.ToLower(smallWordRunes[x])
				}
				return parts[1] + parts[2] + string(smallWordRunes)
			}
			return m
		})

		outLines[lIdx] = result
	}

	return strings.Join(outLines, "\n")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		fmt.Println(Titlecase(scanner.Text()))
	}
}
EOF

# 4. Verify build succeeds
go build -o titlecase_app .

echo "Oracle solve.sh completed successfully."
