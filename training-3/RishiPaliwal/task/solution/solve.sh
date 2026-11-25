#!/bin/bash
set -euo pipefail

repo=/workspace/repo

cat > "$repo/go.mod" <<'EOF'
module titlecase-go

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
}

var subphraseSmallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v", "via", "vs",
}

func main() {
	input, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	if _, err := os.Stdout.Write([]byte(titlecase(string(input)))); err != nil {
		os.Exit(1)
	}
}

func titlecase(text string) string {
	lines := splitLines(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, titlecaseLine(line, true))
	}
	return strings.Join(processed, "\n")
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := upperString(line) == line
	parts := splitWhitespace(line)
	for i := 0; i < len(parts); i += 2 {
		parts[i] = titlecaseWord(parts[i], allCaps)
	}

	if smallFirstLast && len(parts) != 0 {
		parts[0] = capitalizeSmallFirst(parts[0])
		last := len(parts) - 1
		parts[last] = capitalizeSmallLast(parts[last])
	}

	return applySubphraseCapitalization(strings.Join(parts, ""))
}

func splitLines(text string) []string {
	lines := make([]string, 0, 1)
	start := 0
	for i := 0; i < len(text); {
		if text[i] != '\r' && text[i] != '\n' {
			i++
			continue
		}
		lines = append(lines, text[start:i])
		for i < len(text) && (text[i] == '\r' || text[i] == '\n') {
			i++
		}
		start = i
	}
	return append(lines, text[start:])
}

func splitWhitespace(line string) []string {
	parts := make([]string, 0, 1)
	start := 0
	for i, r := range line {
		if !isSpace(r) {
			continue
		}
		parts = append(parts, line[start:i], string(r))
		start = i + utf8.RuneLen(r)
	}
	return append(parts, line[start:])
}

func titlecaseWord(word string, allCaps bool) string {
	if allCaps && isUpperInitials(word) {
		return word
	}
	if result, ok := apostropheSecond(word); ok {
		return result
	}
	if prefix, suffix, ok := matchMc(word); ok {
		return capitalize(prefix) + titlecaseLine(suffix, true)
	}
	if isHonorific(word) {
		runes := []rune(word)
		if len(runes) != 0 {
			return upperString(string(runes[0])) + string(runes[1:])
		}
	}
	if hasInlinePeriod(word) || (!allCaps && hasUppercaseElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return lowerString(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = titlecaseLine(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = titlecaseLine(part, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = lowerString(word)
	}
	if isConsonantAcronym(word) {
		return upperString(word)
	}
	return capitalizeFirstLetter(word)
}

func isSpace(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsNumber(r) || unicode.IsMark(r) || r == '_'
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '“', '#', '$', '%', '&', '\'', '‘', '(', ')', '*', '+',
		',', '-', '–', '‒', '—', '―', '.', '/', ':', ';', '?', '@', '[',
		'\\', ']', '_', '`', '{', '|', '}', '~':
		return true
	default:
		return false
	}
}

func upperString(value string) string {
	var out strings.Builder
	for _, r := range value {
		switch r {
		case 'ß':
			out.WriteString("SS")
		case 'ŉ':
			out.WriteString("ʼN")
		case 'ǰ':
			out.WriteString("J̌")
		case 'ﬀ':
			out.WriteString("FF")
		case 'ﬁ':
			out.WriteString("FI")
		case 'ﬂ':
			out.WriteString("FL")
		case 'ﬃ':
			out.WriteString("FFI")
		case 'ﬄ':
			out.WriteString("FFL")
		case 'ﬅ', 'ﬆ':
			out.WriteString("ST")
		default:
			out.WriteRune(unicode.ToUpper(r))
		}
	}
	return out.String()
}

func lowerString(value string) string {
	runes := []rune(value)
	var out strings.Builder
	for i, r := range runes {
		if r == 'İ' {
			out.WriteString("i̇")
			continue
		}
		if r == 'Σ' && isFinalSigma(runes, i) {
			out.WriteRune('ς')
			continue
		}
		out.WriteRune(unicode.ToLower(r))
	}
	return out.String()
}

func isFinalSigma(runes []rune, index int) bool {
	beforeCased := false
	for i := index - 1; i >= 0; i-- {
		if isCaseIgnorable(runes[i]) {
			continue
		}
		beforeCased = isCased(runes[i])
		break
	}
	if !beforeCased {
		return false
	}
	for i := index + 1; i < len(runes); i++ {
		if isCaseIgnorable(runes[i]) {
			continue
		}
		return !isCased(runes[i])
	}
	return true
}

func isCased(r rune) bool {
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r)
}

func isCaseIgnorable(r rune) bool {
	return unicode.IsMark(r) || unicode.IsPunct(r) || unicode.Is(unicode.Cf, r) ||
		unicode.Is(unicode.Lm, r)
}

func capitalize(value string) string {
	runes := []rune(value)
	if len(runes) == 0 {
		return value
	}
	return upperString(string(runes[0])) + lowerString(string(runes[1:]))
}

func capitalizeFirstLetter(word string) string {
	prefixEnd := 0
	for i, r := range word {
		if !isPunct(r) {
			break
		}
		prefixEnd = i + utf8.RuneLen(r)
	}
	if prefixEnd >= len(word) {
		return word
	}
	r, size := utf8.DecodeRuneInString(word[prefixEnd:])
	if !unicode.IsLetter(r) {
		return word
	}
	end := prefixEnd + size
	return upperString(word[:end]) + word[end:]
}

func isSmallWord(word string) bool {
	for _, small := range smallWords {
		if strings.EqualFold(word, small) {
			return true
		}
	}
	return false
}

func wordBoundary(left, right rune, hasLeft, hasRight bool) bool {
	leftWord := hasLeft && isWord(left)
	rightWord := hasRight && isWord(right)
	return leftWord != rightWord
}

func startsWithSmallAtBoundary(value string, start int) (int, bool) {
	tail := value[start:]
	for _, small := range smallWords {
		if len(tail) < len(small) || !strings.EqualFold(tail[:len(small)], small) {
			continue
		}
		end := start + len(small)
		left, hasLeft := runeBefore(value, end)
		right, hasRight := runeAt(value, end)
		if wordBoundary(left, right, hasLeft, hasRight) {
			return end, true
		}
	}
	return 0, false
}

func capitalizeSmallFirst(value string) string {
	prefixEnd := 0
	for i, r := range value {
		if !isPunct(r) {
			break
		}
		prefixEnd = i + utf8.RuneLen(r)
	}
	end, ok := startsWithSmallAtBoundary(value, prefixEnd)
	if !ok {
		return value
	}
	return value[:prefixEnd] + capitalize(value[prefixEnd:end]) + value[end:]
}

func capitalizeSmallLast(value string) string {
	runes := []rune(value)
	for _, trailingPunct := range []bool{false, true} {
		end := len(runes)
		if trailingPunct {
			if end == 0 || !isPunct(runes[end-1]) {
				continue
			}
			end--
		}
		for _, small := range smallWords {
			smallRunes := []rune(small)
			start := end - len(smallRunes)
			if start < 0 || !strings.EqualFold(string(runes[start:end]), small) {
				continue
			}
			left, hasLeft := runeAtIndex(runes, start-1)
			right, hasRight := runeAtIndex(runes, start)
			if !wordBoundary(left, right, hasLeft, hasRight) {
				continue
			}
			matchedEnd := end
			if trailingPunct {
				matchedEnd++
			}
			return string(runes[:start]) + capitalize(string(runes[start:matchedEnd])) +
				string(runes[matchedEnd:])
		}
	}
	return value
}

func runeAt(value string, offset int) (rune, bool) {
	if offset < 0 || offset >= len(value) {
		return 0, false
	}
	r, _ := utf8.DecodeRuneInString(value[offset:])
	return r, true
}

func runeBefore(value string, offset int) (rune, bool) {
	if offset <= 0 || offset > len(value) {
		return 0, false
	}
	r, _ := utf8.DecodeLastRuneInString(value[:offset])
	return r, true
}

func runeAtIndex(runes []rune, index int) (rune, bool) {
	if index < 0 || index >= len(runes) {
		return 0, false
	}
	return runes[index], true
}

func apostropheSecond(word string) (string, bool) {
	runes := []rune(word)
	if len(runes) < 3 || !strings.ContainsRune("dol", unicode.ToLower(runes[0])) ||
		(runes[1] != '\'' && runes[1] != '‘') {
		return "", false
	}
	letterEnd := len(runes)
	if len(runes) >= 5 && isApostropheSuffix(runes[len(runes)-2]) &&
		isApostropheSuffix(runes[len(runes)-1]) {
		letterEnd -= 2
	}
	if letterEnd <= 2 {
		return "", false
	}
	for _, r := range runes[2:letterEnd] {
		if !unicode.IsLetter(r) {
			return "", false
		}
	}

	first := string(runes[0])
	if strings.ContainsRune("aeiou", unicode.ToLower(runes[0])) {
		first = upperString(first)
	} else {
		first = lowerString(first)
	}
	return first + string(runes[1]) + upperString(string(runes[2])) +
		string(runes[3:]), true
}

func isApostropheSuffix(r rune) bool {
	return r == '\'' || unicode.ToLower(r) == 's'
}

func matchMc(word string) (string, string, bool) {
	if len(word) < 4 {
		return "", "", false
	}
	prefix := word[:2]
	if prefix != "Mc" && prefix != "mc" && prefix != "MC" {
		return "", "", false
	}
	suffix := word[2:]
	runes := []rune(suffix)
	if len(runes) < 2 || !isWord(runes[0]) {
		return "", "", false
	}
	return prefix, suffix, true
}

func isHonorific(word string) bool {
	switch lowerString(word) {
	case "m", "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func hasInlinePeriod(word string) bool {
	runes := []rune(word)
	for i := 1; i+1 < len(runes); i++ {
		if runes[i] == '.' && unicode.IsLetter(runes[i-1]) &&
			unicode.IsLetter(runes[i+1]) {
			return true
		}
	}
	return false
}

func hasUppercaseElsewhere(word string) bool {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	start := i
	for i < len(runes) && unicode.IsLetter(runes[i]) {
		i++
	}
	if i-start < 2 {
		return false
	}
	for _, r := range runes[start+1 : i] {
		if unicode.IsUpper(r) {
			return true
		}
	}
	return false
}

func isUpperInitials(word string) bool {
	runes := []rune(word)
	if len(runes) < 2 {
		return false
	}
	for i := 0; i < len(runes); {
		if !unicode.IsUpper(runes[i]) || i+1 >= len(runes) || runes[i+1] != '.' {
			return false
		}
		i += 2
		if i == len(runes) {
			return true
		}
		if !unicode.IsUpper(runes[i]) {
			return false
		}
		if i+1 == len(runes) {
			return true
		}
	}
	return false
}

func isConsonantAcronym(word string) bool {
	runes := []rune(word)
	if len(runes) <= 2 {
		return false
	}
	for _, r := range runes {
		if r > unicode.MaxASCII {
			return false
		}
		lower := byte(r)
		if lower >= 'A' && lower <= 'Z' {
			lower += 'a' - 'A'
		}
		if lower < 'a' || lower > 'z' || strings.ContainsRune("aeiouy", rune(lower)) {
			return false
		}
	}
	return true
}

func applySubphraseCapitalization(value string) string {
	delimiters := ":.;?!-–‒—―"
	var out strings.Builder
	for i := 0; i < len(value); {
		r, size := utf8.DecodeRuneInString(value[i:])
		if !strings.ContainsRune(delimiters, r) || i+size >= len(value) ||
			value[i+size] != ' ' {
			out.WriteString(value[i : i+size])
			i += size
			continue
		}
		start := i + size + 1
		tail := value[start:]
		matched := ""
		for _, small := range subphraseSmallWords {
			if strings.HasPrefix(tail, small) {
				matched = small
				break
			}
			if (small == "v" || small == "vs") && strings.HasPrefix(tail, small+".") {
				matched = small + "."
				break
			}
		}
		out.WriteString(value[i : start])
		if matched == "" {
			i = start
			continue
		}
		out.WriteString(capitalize(matched))
		i = start + len(matched)
	}
	return out.String()
}
EOF

gofmt -w "$repo/main.go"
find "$repo" \( -type f -o -type l \) -name '*.py' -delete