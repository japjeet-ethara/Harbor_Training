#!/bin/sh
set -eu

repo=/workspace/repo
mkdir -p "$repo"

cat >"$repo/go.mod" <<'EOF'
module titlecase

go 1.20
EOF

cat >"$repo/main.go" <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
)

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '“', '#', '$', '%', '&', '\'', '‘', '(', ')', '*', '+', ',',
		'-', '–', '‒', '—', '―', '.', '/', ':', ';', '?', '@', '[', '\\', ']',
		'^', '_', '`', '{', '|', '}', '~':
		return true
	}
	return false
}

func isSubphrasePunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	}
	return false
}

func isAsciiLetter(b byte) bool {
	return (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z')
}

func isWordChar(b byte) bool {
	return (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z') ||
		(b >= '0' && b <= '9') || b == '_'
}

func isSmallWord(word string) bool {
	switch strings.ToLower(word) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
		"in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	}
	return false
}

func hasInlinePeriod(word string) bool {
	for i := 1; i < len(word)-1; i++ {
		if word[i] == '.' && isWordChar(word[i-1]) && isWordChar(word[i+1]) {
			return true
		}
	}
	return false
}

func hasUcElsewhere(word string) bool {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) && runes[i] != '^' {
		i++
	}
	if i >= len(runes) || !unicode.IsLetter(runes[i]) {
		return false
	}
	start := i
	for i < len(runes) && unicode.IsLetter(runes[i]) {
		if i > start && unicode.IsUpper(runes[i]) {
			return true
		}
		i++
	}
	return false
}

func isUcInitials(word string) bool {
	if word == "" {
		return false
	}
	i := 0
	for i < len(word) {
		if word[i] < 'A' || word[i] > 'Z' {
			return false
		}
		i++
		if i >= len(word) || word[i] != '.' {
			return false
		}
		i++
		if i < len(word) && word[i] >= 'A' && word[i] <= 'Z' {
			if i+1 == len(word) {
				return true
			}
			if word[i+1] != '.' {
				i++
			}
		}
	}
	return true
}

func matchAposSecond(word string) (bool, string) {
	runes := []rune(word)
	if len(runes) < 3 {
		return false, ""
	}
	first := unicode.ToLower(runes[0])
	if first != 'd' && first != 'o' && first != 'l' {
		return false, ""
	}
	if runes[1] != '\'' && runes[1] != '‘' {
		return false, ""
	}
	for idx := 2; idx < len(runes); idx++ {
		r := runes[idx]
		if r == '\'' || r == '‘' {
			if idx == len(runes)-2 && (runes[idx+1] == 's' || runes[idx+1] == 'S') {
				break
			}
			return false, ""
		}
		if r > 127 || !isWordChar(byte(r)) {
			return false, ""
		}
	}
	var result []rune
	if first == 'o' {
		result = append(result, unicode.ToUpper(runes[0]))
	} else {
		result = append(result, unicode.ToLower(runes[0]))
	}
	result = append(result, runes[1], unicode.ToUpper(runes[2]))
	result = append(result, runes[3:]...)
	return true, string(result)
}

func matchMacMc(word string) (bool, string, string) {
	if len(word) < 3 {
		return false, "", ""
	}
	prefix := word[:2]
	if prefix == "mc" || prefix == "Mc" || prefix == "MC" {
		return true, "Mc", word[2:]
	}
	return false, "", ""
}

func matchMrMrsMsDr(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

func capFirst(word string) string {
	runes := []rune(word)
	for i, r := range runes {
		if isPunct(r) {
			continue
		}
		if isWordChar(byte(r)) || r > 127 {
			runes[i] = unicode.ToUpper(r)
			break
		}
	}
	return string(runes)
}

func isAllConsonants(word string) bool {
	if len(word) <= 2 {
		return false
	}
	for i := 0; i < len(word); i++ {
		b := word[i]
		if b >= 'A' && b <= 'Z' {
			b += 32
		}
		if b < 'a' || b > 'z' || b == 'a' || b == 'e' || b == 'i' ||
			b == 'o' || b == 'u' || b == 'y' {
			return false
		}
	}
	return true
}

func applySmallFirst(word string) string {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	if i >= len(runes) {
		return word
	}
	j := i
	for j < len(runes) && (isWordChar(byte(runes[j])) || runes[j] == '.') {
		j++
	}
	sub := string(runes[i:j])
	if isSmallWord(sub) {
		capSub := strings.ToUpper(sub[:1]) + strings.ToLower(sub[1:])
		return string(runes[:i]) + capSub + string(runes[j:])
	}
	return word
}

func applySmallLast(word string) string {
	runes := []rune(word)
	if len(runes) == 0 {
		return word
	}
	end := len(runes)
	if isPunct(runes[end-1]) {
		end--
	}
	start := end
	for start > 0 && (isWordChar(byte(runes[start-1])) || runes[start-1] == '.') {
		start--
	}
	if start < end {
		sub := string(runes[start:end])
		if isSmallWord(sub) {
			capSub := strings.ToUpper(sub[:1]) + strings.ToLower(sub[1:])
			return string(runes[:start]) + capSub + string(runes[end:])
		}
	}
	return word
}

func applySubphrase(text string) string {
	runes := []rune(text)
	var result strings.Builder
	for i := 0; i < len(runes); {
		if i+2 < len(runes) && isSubphrasePunct(runes[i]) && runes[i+1] == ' ' {
			if matched := subphraseSmallPrefix(runes[i+2:]); matched != "" {
				result.WriteRune(runes[i])
				result.WriteRune(runes[i+1])
				result.WriteString(strings.ToUpper(matched[:1]) + strings.ToLower(matched[1:]))
				i += 2 + len([]rune(matched))
				continue
			}
		}
		result.WriteRune(runes[i])
		i++
	}
	return result.String()
}

func subphraseSmallPrefix(text []rune) string {
	for _, alternative := range []string{
		"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
		"in", "of", "on", "or", "the", "to", "v", "via", "vs",
	} {
		candidate := []rune(alternative)
		if len(text) < len(candidate) {
			continue
		}
		matches := true
		for i, r := range candidate {
			if text[i] != r {
				matches = false
				break
			}
		}
		if matches {
			if alternative == "v" && len(text) > 1 && text[1] == '.' {
				return "v."
			}
			return alternative
		}
	}
	return ""
}

func titlecaseWord(word string, allCaps bool, smallFirstLast bool) string {
	if allCaps && isUcInitials(word) {
		return word
	}
	if ok, replaced := matchAposSecond(word); ok {
		return replaced
	}
	if ok, prefix, suffix := matchMacMc(word); ok {
		return prefix + Titlecase(suffix, true)
	}
	if matchMrMrsMsDr(word) {
		return strings.ToUpper(word[:1]) + word[1:]
	}
	if hasInlinePeriod(word) || (!allCaps && hasUcElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = Titlecase(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = Titlecase(part, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if isAllConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func Titlecase(text string, smallFirstLast bool) string {
	if text == "" {
		return ""
	}
	lines := strings.Split(text, "\n")
	processedLines := make([]string, 0, len(lines))
	for _, line := range lines {
		allCaps := strings.ToUpper(line) == line
		var words []string
		var spaces []string
		runes := []rune(line)
		for i := 0; i < len(runes); {
			start := i
			for i < len(runes) && !unicode.IsSpace(runes[i]) {
				i++
			}
			words = append(words, string(runes[start:i]))
			if i >= len(runes) {
				break
			}
			start = i
			for i < len(runes) && unicode.IsSpace(runes[i]) {
				i++
			}
			spaces = append(spaces, string(runes[start:i]))
		}
		titleWords := make([]string, len(words))
		for i, word := range words {
			titleWords[i] = titlecaseWord(word, allCaps, smallFirstLast)
		}
		if smallFirstLast && len(titleWords) > 0 {
			titleWords[0] = applySmallFirst(titleWords[0])
			titleWords[len(titleWords)-1] = applySmallLast(titleWords[len(titleWords)-1])
		}
		var result strings.Builder
		for i, word := range titleWords {
			result.WriteString(word)
			if i < len(spaces) {
				result.WriteString(spaces[i])
			}
		}
		processedLines = append(processedLines, applySubphrase(result.String()))
	}
	return strings.Join(processedLines, "\n")
}

func main() {
	reader := bufio.NewReader(os.Stdin)
	for {
		line, err := reader.ReadString('\n')
		if len(line) > 0 {
			hasCRLF := strings.HasSuffix(line, "\r\n")
			hasLF := strings.HasSuffix(line, "\n")
			text := strings.TrimRight(line, "\r\n")
			output := Titlecase(text, true)
			switch {
			case hasCRLF:
				fmt.Print(output, "\r\n")
			case hasLF:
				fmt.Print(output, "\n")
			default:
				fmt.Print(output)
			}
		}
		if err != nil {
			if err != io.EOF {
				fmt.Fprintln(os.Stderr, "read error:", err)
			}
			return
		}
	}
}
EOF

find "$repo" \( -type f -o -type l \) -name '*.py' -delete
