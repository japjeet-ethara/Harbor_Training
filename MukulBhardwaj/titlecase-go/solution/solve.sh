#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module example.com/titlecase-go

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
const subphrasePunctuation = ":.;?!-–‒—―"

var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

var upperExpansions = map[rune]string{
	'ß': "SS",
	'ﬀ': "FF",
	'ﬁ': "FI",
	'ﬂ': "FL",
	'ﬃ': "FFI",
	'ﬄ': "FFL",
	'ﬅ': "ST",
	'ﬆ': "ST",
}

func upperRune(r rune) string {
	if expanded, ok := upperExpansions[r]; ok {
		return expanded
	}
	return strings.ToUpper(string(r))
}

func pyUpper(s string) string {
	var out strings.Builder
	for _, r := range s {
		out.WriteString(upperRune(r))
	}
	return out.String()
}

func pyLower(s string) string {
	var out strings.Builder
	for _, r := range s {
		if r == '\u0130' {
			out.WriteString("i\u0307")
		} else {
			out.WriteString(strings.ToLower(string(r)))
		}
	}
	return out.String()
}

func capitalize(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return upperRune(r) + pyLower(s[size:])
}

func isPunctuation(r rune) bool {
	return strings.ContainsRune(punctuation, r)
}

func isSubphrasePunctuation(r rune) bool {
	return strings.ContainsRune(subphrasePunctuation, r)
}

func isWordRune(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsNumber(r) || r == '_'
}

func isWhitespace(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

func equalFoldPythonRe(a, b string) bool {
	if strings.EqualFold(a, b) {
		return true
	}
	left, right := []rune(a), []rune(b)
	if len(left) != len(right) {
		return false
	}
	fold := func(r rune) rune {
		switch r {
		case 'İ', 'ı':
			return 'i'
		case 'ſ':
			return 's'
		case 'K':
			return 'k'
		default:
			return unicode.ToLower(r)
		}
	}
	for i := range left {
		if fold(left[i]) != fold(right[i]) {
			return false
		}
	}
	return true
}

func wordBoundaryAt(runes []rune, index int) bool {
	left := index > 0 && isWordRune(runes[index-1])
	right := index < len(runes) && isWordRune(runes[index])
	return left != right
}

func prefixEqualFold(runes []rune, start int, candidate string) bool {
	candidateRunes := []rune(candidate)
	if start < 0 || start+len(candidateRunes) > len(runes) {
		return false
	}
	return equalFoldPythonRe(string(runes[start:start+len(candidateRunes)]), candidate)
}

func isSmallWord(word string) bool {
	for _, small := range smallWords {
		if equalFoldPythonRe(word, small) {
			return true
		}
	}
	return false
}

func smallMatchCandidates() []string {
	return []string{
		"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
		"in", "of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
	}
}

func capitalizeFirst(s string) string {
	runes := []rune(s)
	for i, r := range runes {
		if isPunctuation(r) {
			continue
		}
		if isWordRune(r) {
			return string(runes[:i]) + upperRune(r) + string(runes[i+1:])
		}
		return s
	}
	return s
}

func capitalizeSmallFirst(s string) string {
	runes := []rune(s)
	prefixEnd := 0
	for prefixEnd < len(runes) && isPunctuation(runes[prefixEnd]) {
		prefixEnd++
	}
	for _, candidate := range smallMatchCandidates() {
		if !prefixEqualFold(runes, prefixEnd, candidate) {
			continue
		}
		end := prefixEnd + len([]rune(candidate))
		if !wordBoundaryAt(runes, end) {
			continue
		}
		return string(runes[:prefixEnd]) +
			capitalize(string(runes[prefixEnd:end])) +
			string(runes[end:])
	}
	return s
}

func capitalizeSmallLast(s string) string {
	runes := []rune(s)
	if len(runes) == 0 {
		return s
	}
	end := len(runes)
	if isPunctuation(runes[end-1]) {
		end--
	}
	for start := 0; start < end; start++ {
		if !wordBoundaryAt(runes, start) {
			continue
		}
		for _, candidate := range smallMatchCandidates() {
			if start+len([]rune(candidate)) != end ||
				!prefixEqualFold(runes, start, candidate) {
				continue
			}
			return string(runes[:start]) + capitalize(string(runes[start:]))
		}
	}
	return s
}

func capitalizeSubphrases(s string) string {
	runes := []rune(s)
	var out strings.Builder
	for i := 0; i < len(runes); {
		if i+1 < len(runes) && isSubphrasePunctuation(runes[i]) &&
			runes[i+1] == ' ' {
			start := i + 2
			matched := false
			for _, candidate := range smallMatchCandidates() {
				candidateRunes := []rune(candidate)
				if start+len(candidateRunes) > len(runes) ||
					string(runes[start:start+len(candidateRunes)]) != candidate {
					continue
				}
				out.WriteString(string(runes[i : i+2]))
				out.WriteString(capitalize(string(runes[start : start+len(candidateRunes)])))
				i = start + len(candidateRunes)
				matched = true
				break
			}
			if matched {
				continue
			}
		}
		out.WriteRune(runes[i])
		i++
	}
	return out.String()
}

func hasInlinePeriod(word string) bool {
	runes := []rune(word)
	for i := 1; i+1 < len(runes); i++ {
		if isWordRune(runes[i-1]) && runes[i] == '.' && isWordRune(runes[i+1]) {
			return true
		}
	}
	return false
}

func hasUppercaseElsewhere(word string) bool {
	runes := []rune(word)
	start := 0
	for start < len(runes) && isPunctuation(runes[start]) {
		start++
	}
	seenLetter := false
	for _, r := range runes[start:] {
		if !isASCIIAlpha(r) {
			break
		}
		if seenLetter && r >= 'A' && r <= 'Z' {
			return true
		}
		seenLetter = true
	}
	return false
}

func isASCIIAlpha(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isASCIIUpper(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func isUpperInitialism(word string) bool {
	runes := []rune(word)
	if len(runes) < 2 || !isASCIIUpper(runes[0]) {
		return false
	}
	expectDot := true
	for _, r := range runes[1:] {
		if expectDot {
			if r != '.' {
				return false
			}
		} else if !isASCIIUpper(r) {
			return false
		}
		expectDot = !expectDot
	}
	return true
}

func apostropheWord(word string) (string, bool) {
	runes := []rune(word)
	if len(runes) < 3 || !strings.ContainsRune("dol", unicode.ToLower(runes[0])) ||
		(runes[1] != '\'' && runes[1] != '‘') {
		return "", false
	}
	end := 2
	for end < len(runes) && isWordRune(runes[end]) {
		end++
	}
	if end == 2 {
		return "", false
	}
	suffix := runes[end:]
	if len(suffix) != 0 {
		if len(suffix) != 2 {
			return "", false
		}
		for _, r := range suffix {
			if r != '\'' && !equalFoldPythonRe(string(r), "s") {
				return "", false
			}
		}
	}
	first := string(runes[0])
	if strings.ContainsRune("aeiouAEIOU", runes[0]) {
		first = pyUpper(first)
	} else {
		first = pyLower(first)
	}
	return first + string(runes[1]) + upperRune(runes[2]) + string(runes[3:]), true
}

func isMacMcWordRune(r rune) bool {
	return isWordRune(r)
}

func macMcWord(word string) (string, bool) {
	prefix := ""
	switch {
	case strings.HasPrefix(word, "mc"):
		prefix = "mc"
	case strings.HasPrefix(word, "Mc"):
		prefix = "Mc"
	case strings.HasPrefix(word, "MC"):
		prefix = "MC"
	default:
		return "", false
	}
	remainder := word[len(prefix):]
	runes := []rune(remainder)
	if len(runes) < 2 || !isMacMcWordRune(runes[0]) {
		return "", false
	}
	return capitalize(prefix) + titlecaseText(remainder, true), true
}

func isTitleAbbreviation(word string) bool {
	for _, candidate := range []string{"m", "mr", "mrs", "ms", "dr"} {
		if equalFoldPythonRe(word, candidate) {
			return true
		}
	}
	return false
}

func allConsonants(word string) bool {
	runes := []rune(word)
	if len(runes) <= 2 {
		return false
	}
	for _, r := range runes {
		lower := unicode.ToLower(r)
		if r == 'ſ' {
			lower = 's'
		} else if r == 'K' {
			lower = 'k'
		}
		if lower < 'a' || lower > 'z' || strings.ContainsRune("aeiouy", lower) {
			return false
		}
	}
	return true
}

func titlecaseWord(word string, allCaps bool) string {
	if allCaps && isUpperInitialism(word) {
		return word
	}
	if result, ok := apostropheWord(word); ok {
		return result
	}
	if result, ok := macMcWord(word); ok {
		return result
	}
	if isTitleAbbreviation(word) {
		runes := []rune(word)
		runes[0] = unicode.ToUpper(runes[0])
		return string(runes)
	}
	if hasInlinePeriod(word) || (!allCaps && hasUppercaseElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return pyLower(word)
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
		word = pyLower(word)
	}
	if allConsonants(word) {
		return pyUpper(word)
	}
	return capitalizeFirst(word)
}

func splitWords(line string) ([]string, []string) {
	words := make([]string, 0)
	spaces := make([]string, 0)
	start := 0
	for byteIndex, r := range line {
		if !isWhitespace(r) {
			continue
		}
		words = append(words, line[start:byteIndex])
		size := utf8.RuneLen(r)
		spaces = append(spaces, line[byteIndex:byteIndex+size])
		start = byteIndex + size
	}
	words = append(words, line[start:])
	return words, spaces
}

func titlecaseText(line string, smallFirstLast bool) string {
	allCaps := pyUpper(line) == line
	words, spaces := splitWords(line)
	for i := range words {
		words[i] = titlecaseWord(words[i], allCaps)
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
	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for {
		line, err := reader.ReadString('\n')
		if len(line) > 0 || err == nil {
			line = strings.TrimSuffix(line, "\n")
			line = strings.TrimSuffix(line, "\r")
			fmt.Fprintln(writer, titlecaseText(line, true))
		}
		if err != nil {
			if err != io.EOF {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
			break
		}
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
gofmt -w main.go
go build ./...
