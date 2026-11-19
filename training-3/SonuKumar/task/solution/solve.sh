#!/bin/bash
set -euo pipefail

cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

func isPunctuation(r rune) bool {
	return strings.ContainsRune(punctuation, r)
}

func isWhitespace(r rune) bool {
	return unicode.IsSpace(r)
}

func isUpper(r rune) bool {
	return unicode.IsUpper(r)
}

func isLetter(r rune) bool {
	return unicode.IsLetter(r)
}

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isASCIIUpper(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func isWordRune(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

func allCaps(s string) bool {
	return strings.ToUpper(s) == s
}

func isUpperInitials(s string) bool {
	r := []rune(s)
	if len(r) == 0 {
		return false
	}
	if !isASCIILetter(r[0]) || !isASCIIUpper(r[0]) || len(r) < 2 || r[1] != '.' {
		return false
	}
	return true
}

func hasInlinePeriod(s string) bool {
	r := []rune(s)
	for i := 1; i+1 < len(r); i++ {
		if r[i] == '.' && isWordRune(r[i-1]) && isWordRune(r[i+1]) {
			return true
		}
	}
	return false
}

func hasMixedCase(s string) bool {
	r := []rune(s)
	start := 0
	for start < len(r) && isPunctuation(r[start]) {
		start++
	}
	seenLetter := false
	for _, c := range r[start:] {
		if !isASCIILetter(c) {
			break
		}
		if isASCIIUpper(c) && seenLetter {
			return true
		}
		seenLetter = true
	}
	return false
}

func apostropheWord(s string) bool {
	r := []rune(s)
	if len(r) < 3 || !strings.ContainsRune("dDlLoO", r[0]) ||
		(r[1] != '\'' && r[1] != rune(0x2018)) {
		return false
	}
	i := 2
	for i < len(r) && isWordRune(r[i]) {
		i++
	}
	if i == 2 {
		return false
	}
	if i == len(r) {
		return true
	}
	if len(r)-i != 2 {
		return false
	}
	for _, c := range r[i:] {
		if c != '\'' && c != rune(0x2018) && c != 's' && c != 'S' {
			return false
		}
	}
	return true
}

func capitalizeFirstLetter(s string) string {
	r := []rune(s)
	for i, c := range r {
		if isPunctuation(c) {
			continue
		}
		if isWordRune(c) {
			if !isLetter(c) {
				return s
			}
			upper := []rune(strings.ToUpper(string(c)))
			return string(r[:i]) + string(upper) + string(r[i+1:])
		}
		return s
	}
	return s
}

func isSmall(s string) bool {
	return smallWords[strings.ToLower(s)]
}

func capitalizeSmallPrefix(s string) string {
	r := []rune(s)
	i := 0
	for i < len(r) && isPunctuation(r[i]) {
		i++
	}
	for _, candidate := range []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "via", "vs"} {
		c := []rune(candidate)
		if i+len(c) > len(r) || !strings.EqualFold(string(r[i:i+len(c)]), candidate) {
			continue
		}
		next := i + len(c)
		if next < len(r) && isWordRune(r[next]) {
			continue
		}
		return string(r[:i]) + strings.ToUpper(string(r[i])) +
			strings.ToLower(string(r[i+1:next])) + string(r[next:])
	}
	return s
}

func titleWord(word string, phraseBoundary bool, lineAllCaps bool) string {
	if lineAllCaps && isUpperInitials(word) {
		return word
	}
	if apostropheWord(word) {
		r := []rune(word)
		if len(r) > 2 {
			first := unicode.ToLower(r[0])
			if strings.ContainsRune("aeiouAEIOU", r[0]) {
				first = unicode.ToUpper(r[0])
			}
			r[0] = first
			r[2] = unicode.ToUpper(r[2])
			return string(r)
		}
	}
	r := []rune(word)
	if len(r) >= 4 && ((r[0] == 'M' || r[0] == 'm') && r[1] == 'c' || (r[0] == 'M' && r[1] == 'C')) {
		return "Mc" + titlecase(string(r[2:]), true)
	}
	lower := strings.ToLower(word)
	if lower == "mr" || lower == "mrs" || lower == "ms" || lower == "dr" {
		if len(r) == 0 {
			return word
		}
		r[0] = unicode.ToUpper(r[0])
		return string(r)
	}
	if hasInlinePeriod(word) || (!lineAllCaps && hasMixedCase(word)) {
		return word
	}
	if isSmall(word) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i := range parts {
			parts[i] = titlecase(parts[i], false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i := range parts {
			parts[i] = titlecase(parts[i], false)
		}
		return strings.Join(parts, "-")
	}
	if lineAllCaps {
		word = strings.ToLower(word)
	}
	if allConsonants(word) && utf8.RuneCountInString(word) > 2 {
		return strings.ToUpper(word)
	}
	return capitalizeFirstLetter(word)
}

func allConsonants(s string) bool {
	if s == "" {
		return false
	}
	for _, c := range s {
		if !strings.ContainsRune("bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ", c) {
			return false
		}
	}
	return true
}

func phraseSmallFirst(s string) string {
	return capitalizeSmallPrefix(s)
}

func phraseSmallLast(s string) string {
	r := []rune(s)
	for _, candidate := range []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs"} {
		c := []rune(candidate)
		for suffixLen := 0; suffixLen <= 1; suffixLen++ {
			start := len(r) - len(c) - suffixLen
			if start < 0 || string(r[start:start+len(c)]) != candidate {
				continue
			}
			if suffixLen == 1 && !isPunctuation(r[len(r)-1]) {
				continue
			}
			if start > 0 && isWordRune(r[start-1]) {
				continue
			}
			return string(r[:start]) + strings.Title(strings.ToLower(string(r[start:len(r)-suffixLen]))) + string(r[len(r)-suffixLen:])
		}
	}
	return s
}

func subphraseCap(s string) string {
	r := []rune(s)
	for i := 0; i+2 < len(r); i++ {
		if strings.ContainsRune(":.;?!-–‒—―", r[i]) && r[i+1] == ' ' {
			j := i + 2
			for j < len(r) && (isLetter(r[j]) || r[j] == '.') {
				j++
			}
			for _, candidate := range []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "via", "vs"} {
				c := []rune(candidate)
				end := i + 2 + len(c)
				if end > len(r) || string(r[i+2:end]) != candidate {
					continue
				}
				if end < len(r) && isWordRune(r[end]) {
					continue
				}
				r = append(r[:i+2], append([]rune(strings.Title(candidate)), r[end:]...)...)
				i = i + 1
				break
			}
		}
	}
	return string(r)
}

func titlecase(text string, smallFirstLast bool) string {
	lines := strings.FieldsFunc(text, func(r rune) bool { return r == '\r' || r == '\n' })
	if len(lines) == 0 {
		lines = []string{""}
	}
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		lineAllCaps := allCaps(line)
		words := make([]string, 0)
		spaces := make([]string, 0)
		var current strings.Builder
		flush := func() {
			words = append(words, current.String())
			current.Reset()
		}
		for _, c := range line {
			if isWhitespace(c) {
				flush()
				spaces = append(spaces, string(c))
			} else {
				current.WriteRune(c)
			}
		}
		flush()
		tc := make([]string, len(words))
		for i, word := range words {
			tc[i] = titleWord(word, false, lineAllCaps)
		}
		if smallFirstLast && len(tc) > 0 {
			tc[0] = phraseSmallFirst(tc[0])
			tc[len(tc)-1] = phraseSmallLast(tc[len(tc)-1])
		}
		var result strings.Builder
		for i, word := range tc {
			result.WriteString(word)
			if i < len(spaces) {
				result.WriteString(spaces[i])
			}
		}
		processed = append(processed, subphraseCap(result.String()))
	}
	return strings.Join(processed, "\n")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024), 1024*1024*16)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		fmt.Fprintln(writer, titlecase(strings.TrimSuffix(scanner.Text(), "\r"), true))
	}
}
EOF

go build ./...