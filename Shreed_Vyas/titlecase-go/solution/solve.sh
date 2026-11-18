#!/bin/sh
set -eu
cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase-go

go 1.23.4
EOF

cat > main.go <<'EOF'
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

var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
}

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
const subphrasePunctuation = ":.;?!-–‒—―"

var allCapsInitials = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

func hasInlinePeriod(word string) bool {
	runes := []rune(word)
	for i := 1; i+1 < len(runes); i++ {
		if runes[i] == '.' && isWord(runes[i-1]) && isWord(runes[i+1]) {
			return true
		}
	}
	return false
}

func hasUppercaseElsewhere(word string) bool {
	runes := []rune(word)
	start := 0
	for start < len(runes) && strings.ContainsRune(punctuation, runes[start]) {
		start++
	}
	seenLetter := false
	for _, r := range runes[start:] {
		if !unicode.IsLetter(r) {
			break
		}
		if seenLetter && unicode.IsUpper(r) {
			return true
		}
		seenLetter = true
	}
	return false
}

func titleFirst(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return strings.ToUpper(string(r)) + strings.ToLower(s[size:])
}

func uppercaseFirst(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return strings.ToUpper(string(r)) + s[size:]
}

func lowercaseFirst(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return strings.ToLower(string(r)) + s[size:]
}

func isSmall(word string) bool {
	word = strings.ToLower(word)
	for _, small := range smallWords {
		if word == small {
			return true
		}
	}
	return false
}

func isAllCapsInitials(word string) bool {
	return allCapsInitials.MatchString(word)
}

func hasAllConsonants(word string) bool {
	if len([]rune(word)) <= 2 {
		return false
	}
	for _, r := range word {
		r = unicode.ToLower(r)
		if !strings.ContainsRune("bcdfghjklmnpqrstvwxz", r) {
			return false
		}
	}
	return true
}

func apostropheSecond(word string) (string, bool) {
	runes := []rune(word)
	if len(runes) < 3 || !strings.ContainsRune("dol", unicode.ToLower(runes[0])) {
		return "", false
	}
	if runes[1] != '\'' && runes[1] != '‘' {
		return "", false
	}
	end := 2
	for end < len(runes) && isWord(runes[end]) {
		end++
	}
	if end == 2 {
		return "", false
	}
	suffix := runes[end:]
	if len(suffix) != 0 && len(suffix) != 2 {
		return "", false
	}
	for _, r := range suffix {
		if !strings.ContainsRune("'s", r) {
			return "", false
		}
	}
	if runes[0] != 'o' && runes[0] != 'O' {
		runes[0] = unicode.ToLower(runes[0])
	} else {
		runes[0] = unicode.ToUpper(runes[0])
	}
	runes[2] = unicode.ToUpper(runes[2])
	return string(runes), true
}

func titleWord(word string, allCaps bool) string {
	if allCaps && isAllCapsInitials(word) {
		return word
	}

	if changed, ok := apostropheSecond(word); ok {
		return changed
	}

	runes := []rune(word)
	if len(runes) >= 4 &&
		((runes[0] == 'M' || runes[0] == 'm') && runes[1] == 'c' ||
			runes[0] == 'M' && runes[1] == 'C') &&
		isWord(runes[2]) && len(runes) > 3 {
		prefix := titleFirst(string(runes[:2]))
		return prefix + titlecaseText(string(runes[2:]), true)
	}

	lowerWord := strings.ToLower(word)
	if lowerWord == "mr" || lowerWord == "mrs" || lowerWord == "ms" || lowerWord == "dr" {
		return uppercaseFirst(word)
	}

	if hasInlinePeriod(word) || (!allCaps && hasUppercaseElsewhere(word)) {
		return word
	}
	if isSmall(word) {
		return lowerWord
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i := range parts {
			parts[i] = titlecaseText(parts[i], false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i := range parts {
			parts[i] = titlecaseText(parts[i], false)
		}
		return strings.Join(parts, "-")
	}

	if allCaps {
		word = strings.ToLower(word)
	}
	if hasAllConsonants(word) {
		return strings.ToUpper(word)
	}

	runes = []rune(word)
	for i, r := range runes {
		if !strings.ContainsRune(punctuation, r) {
			runes[i] = unicode.ToUpper(r)
			break
		}
	}
	return string(runes)
}

func capitalizeSmallFirst(word string) string {
	runes := []rune(word)
	end := 0
	for end < len(runes) && strings.ContainsRune(punctuation, runes[end]) {
		end++
	}
	for _, small := range smallWords {
		smallRunes := []rune(small)
		if end+len(smallRunes) > len(runes) {
			continue
		}
		if !strings.EqualFold(string(runes[end:end+len(smallRunes)]), small) {
			continue
		}
		next := end + len(smallRunes)
		if next < len(runes) && isWord(runes[next]) {
			continue
		}
		copy(runes[end:next], []rune(titleFirst(string(runes[end:next]))))
		break
	}
	return string(runes)
}

func capitalizeSmallLast(word string) string {
	runes := []rune(word)
	end := len(runes)
	if end > 0 && strings.ContainsRune(punctuation, runes[end-1]) {
		end--
	}
	for _, small := range smallWords {
		smallRunes := []rune(small)
		start := end - len(smallRunes)
		if start < 0 || !strings.EqualFold(string(runes[start:end]), small) {
			continue
		}
		if start > 0 && isWord(runes[start-1]) {
			continue
		}
		copy(runes[start:end], []rune(titleFirst(string(runes[start:end]))))
		break
	}
	return string(runes)
}

func capitalizeSubphrases(text string) string {
	runes := []rune(text)
	for i := 0; i+2 < len(runes); i++ {
		if !strings.ContainsRune(subphrasePunctuation, runes[i]) || runes[i+1] != ' ' {
			continue
		}
		for _, small := range smallWords {
			smallRunes := []rune(small)
			start := i + 2
			if start+len(smallRunes) > len(runes) {
				continue
			}
			if string(runes[start:start+len(smallRunes)]) == small {
				copy(runes[start:start+len(smallRunes)], []rune(titleFirst(small)))
				break
			}
		}
	}
	return string(runes)
}

func titlecaseText(text string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(text) == text
	words := []string{""}
	spaces := make([]string, 0)
	for _, r := range text {
		if unicode.IsSpace(r) {
			spaces = append(spaces, string(r))
			words = append(words, "")
		} else {
			words[len(words)-1] += string(r)
		}
	}
	for i := range words {
		words[i] = titleWord(words[i], allCaps)
	}

	if smallFirstLast && len(words) > 0 {
		words[0] = capitalizeSmallFirst(words[0])
		words[len(words)-1] = capitalizeSmallLast(words[len(words)-1])
	}

	var result strings.Builder
	for i, word := range words {
		result.WriteString(word)
		if i < len(spaces) {
			result.WriteString(spaces[i])
		}
	}
	return capitalizeSubphrases(result.String())
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 4096), 16*1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		fmt.Fprintln(writer, titlecaseText(scanner.Text(), true))
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
EOF

find . -type f -name '*.py' -delete
