#!/bin/bash
set -eu

repo=/workspace/repo
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module titlecase-go

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
)

var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v", "via", "vs",
}

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
const subphrasePunctuation = ":.;?!-–‒—―"

var fullUpper = map[rune]string{
	'\u00df': "SS",
	'\u0149': "\u02bcN",
	'\u01f0': "J\u030c",
	'\u0390': "\u0399\u0308\u0301",
	'\u03b0': "\u03a5\u0308\u0301",
	'\u0587': "\u0535\u0552",
	'\u1e96': "H\u0331",
	'\u1e97': "T\u0308",
	'\u1e98': "W\u030a",
	'\u1e99': "Y\u030a",
	'\u1e9a': "A\u02be",
	'\u1f50': "\u03a5\u0313",
	'\u1f52': "\u03a5\u0313\u0300",
	'\u1f54': "\u03a5\u0313\u0301",
	'\u1f56': "\u03a5\u0313\u0342",
	'\u1f80': "\u1f08\u0399",
	'\u1f81': "\u1f09\u0399",
	'\u1f82': "\u1f0a\u0399",
	'\u1f83': "\u1f0b\u0399",
	'\u1f84': "\u1f0c\u0399",
	'\u1f85': "\u1f0d\u0399",
	'\u1f86': "\u1f0e\u0399",
	'\u1f87': "\u1f0f\u0399",
	'\u1f88': "\u1f08\u0399",
	'\u1f89': "\u1f09\u0399",
	'\u1f8a': "\u1f0a\u0399",
	'\u1f8b': "\u1f0b\u0399",
	'\u1f8c': "\u1f0c\u0399",
	'\u1f8d': "\u1f0d\u0399",
	'\u1f8e': "\u1f0e\u0399",
	'\u1f8f': "\u1f0f\u0399",
	'\u1f90': "\u1f28\u0399",
	'\u1f91': "\u1f29\u0399",
	'\u1f92': "\u1f2a\u0399",
	'\u1f93': "\u1f2b\u0399",
	'\u1f94': "\u1f2c\u0399",
	'\u1f95': "\u1f2d\u0399",
	'\u1f96': "\u1f2e\u0399",
	'\u1f97': "\u1f2f\u0399",
	'\u1f98': "\u1f28\u0399",
	'\u1f99': "\u1f29\u0399",
	'\u1f9a': "\u1f2a\u0399",
	'\u1f9b': "\u1f2b\u0399",
	'\u1f9c': "\u1f2c\u0399",
	'\u1f9d': "\u1f2d\u0399",
	'\u1f9e': "\u1f2e\u0399",
	'\u1f9f': "\u1f2f\u0399",
	'\u1fa0': "\u1f68\u0399",
	'\u1fa1': "\u1f69\u0399",
	'\u1fa2': "\u1f6a\u0399",
	'\u1fa3': "\u1f6b\u0399",
	'\u1fa4': "\u1f6c\u0399",
	'\u1fa5': "\u1f6d\u0399",
	'\u1fa6': "\u1f6e\u0399",
	'\u1fa7': "\u1f6f\u0399",
	'\u1fa8': "\u1f68\u0399",
	'\u1fa9': "\u1f69\u0399",
	'\u1faa': "\u1f6a\u0399",
	'\u1fab': "\u1f6b\u0399",
	'\u1fac': "\u1f6c\u0399",
	'\u1fad': "\u1f6d\u0399",
	'\u1fae': "\u1f6e\u0399",
	'\u1faf': "\u1f6f\u0399",
	'\u1fb2': "\u1fba\u0399",
	'\u1fb3': "\u0391\u0399",
	'\u1fb4': "\u0386\u0399",
	'\u1fb6': "\u0391\u0342",
	'\u1fb7': "\u0391\u0342\u0399",
	'\u1fbc': "\u0391\u0399",
	'\u1fc2': "\u1fca\u0399",
	'\u1fc3': "\u0397\u0399",
	'\u1fc4': "\u0389\u0399",
	'\u1fc6': "\u0397\u0342",
	'\u1fc7': "\u0397\u0342\u0399",
	'\u1fcc': "\u0397\u0399",
	'\u1fd2': "\u0399\u0308\u0300",
	'\u1fd3': "\u0399\u0308\u0301",
	'\u1fd6': "\u0399\u0342",
	'\u1fd7': "\u0399\u0308\u0342",
	'\u1fe2': "\u03a5\u0308\u0300",
	'\u1fe3': "\u03a5\u0308\u0301",
	'\u1fe4': "\u03a1\u0313",
	'\u1fe6': "\u03a5\u0342",
	'\u1fe7': "\u03a5\u0308\u0342",
	'\u1ff2': "\u1ffa\u0399",
	'\u1ff3': "\u03a9\u0399",
	'\u1ff4': "\u038f\u0399",
	'\u1ff6': "\u03a9\u0342",
	'\u1ff7': "\u03a9\u0342\u0399",
	'\u1ffc': "\u03a9\u0399",
	'\ufb00': "FF",
	'\ufb01': "FI",
	'\ufb02': "FL",
	'\ufb03': "FFI",
	'\ufb04': "FFL",
	'\ufb05': "ST",
	'\ufb06': "ST",
	'\ufb13': "\u0544\u0546",
	'\ufb14': "\u0544\u0535",
	'\ufb15': "\u0544\u053b",
	'\ufb16': "\u054e\u0546",
	'\ufb17': "\u0544\u053d",
}

func upper(s string) string {
	var out strings.Builder
	for _, r := range s {
		if expanded, ok := fullUpper[r]; ok {
			out.WriteString(expanded)
		} else {
			out.WriteRune(unicode.ToUpper(r))
		}
	}
	return out.String()
}

func isCaseIgnorable(r rune) bool {
	return unicode.IsMark(r) || unicode.Is(unicode.Cf, r) ||
		unicode.Is(unicode.Pc, r) || r == '\'' || r == '\u2019' ||
		r == '\u02bc' || r == ':' || r == '.' || r == ','
}

func isCased(r rune) bool {
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r)
}

func isFinalSigma(rs []rune, i int) bool {
	before := false
	for j := i - 1; j >= 0; j-- {
		if isCaseIgnorable(rs[j]) {
			continue
		}
		before = isCased(rs[j])
		break
	}
	if !before {
		return false
	}
	for j := i + 1; j < len(rs); j++ {
		if isCaseIgnorable(rs[j]) {
			continue
		}
		return !isCased(rs[j])
	}
	return true
}

func lowerFrom(rs []rune, start int) string {
	var out strings.Builder
	for i := start; i < len(rs); i++ {
		r := rs[i]
		switch r {
		case '\u0130':
			out.WriteString("i\u0307")
		case '\u03a3':
			if isFinalSigma(rs, i) {
				out.WriteRune('\u03c2')
			} else {
				out.WriteRune('\u03c3')
			}
		default:
			out.WriteRune(unicode.ToLower(r))
		}
	}
	return out.String()
}

func lower(s string) string {
	return lowerFrom([]rune(s), 0)
}

func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	return upper(string(rs[0])) + lowerFrom(rs, 1)
}

func isPythonSpace(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsNumber(r) || r == '_'
}

func isPunctuation(r rune) bool {
	return strings.ContainsRune(punctuation, r)
}

func splitLines(s string) []string {
	rs := []rune(s)
	lines := make([]string, 0, 1)
	start := 0
	for i := 0; i < len(rs); {
		if rs[i] != '\r' && rs[i] != '\n' {
			i++
			continue
		}
		lines = append(lines, string(rs[start:i]))
		for i < len(rs) && (rs[i] == '\r' || rs[i] == '\n') {
			i++
		}
		start = i
	}
	return append(lines, string(rs[start:]))
}

func splitSmallPattern(s string, start int, ignoreCase, boundary, requireEnd bool) (int, bool) {
	rs := []rune(s)
	if start < 0 || start > len(rs) {
		return start, false
	}
	for _, word := range smallWords {
		options := []string{word}
		if word == "v" || word == "vs" {
			options = []string{word + ".", word}
		}
		for _, option := range options {
			part := []rune(option)
			if start+len(part) > len(rs) {
				continue
			}
			matches := true
			for j := range part {
				left, right := string(rs[start+j]), string(part[j])
				if ignoreCase {
					if !strings.EqualFold(left, right) {
						matches = false
						break
					}
				} else if rs[start+j] != part[j] {
					matches = false
					break
				}
			}
			end := start + len(part)
			if !matches || (requireEnd && end != len(rs)) ||
				(boundary && end < len(rs) && isWord(rs[end])) {
				continue
			}
			return end, true
		}
	}
	return start, false
}

func isSmallWord(word string) bool {
	_, ok := splitSmallPattern(word, 0, true, false, true)
	return ok
}

func isAllCaps(line string) bool {
	return upper(line) == line
}

func isUpperInitial(r rune) bool {
	return unicode.IsUpper(r)
}

func isUpperInitials(word string) bool {
	rs := []rune(word)
	if len(rs) == 0 {
		return false
	}
	memo := make(map[int]bool)
	known := make(map[int]bool)
	var matches func(int) bool
	matches = func(i int) bool {
		if i == len(rs) {
			return true
		}
		if i > len(rs)-2 || !isUpperInitial(rs[i]) || rs[i+1] != '.' {
			return false
		}
		if known[i] {
			return memo[i]
		}
		known[i] = true
		memo[i] = matches(i+2)
		if !memo[i] && i+2 < len(rs) && isUpperInitial(rs[i+2]) {
			memo[i] = matches(i + 3)
		}
		return memo[i]
	}
	return matches(0)
}

func isApostropheWord(word string) bool {
	rs := []rune(word)
	if len(rs) < 3 || !(strings.EqualFold(string(rs[0]), "d") ||
		strings.EqualFold(string(rs[0]), "o") || strings.EqualFold(string(rs[0]), "l")) ||
		(rs[1] != '\'' && rs[1] != '\u2018') {
		return false
	}
	end := len(rs)
	if end >= 2 && isApostropheSuffixRune(rs[end-1]) && isApostropheSuffixRune(rs[end-2]) {
		end -= 2
	}
	if end <= 2 {
		return false
	}
	for _, r := range rs[2:end] {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return true
}

func isApostropheSuffixRune(r rune) bool {
	return r == '\'' || strings.EqualFold(string(r), "s")
}

func transformApostropheWord(word string) string {
	rs := []rune(word)
	first := rs[0]
	if first == 'a' || first == 'e' || first == 'i' || first == 'o' || first == 'u' ||
		first == 'A' || first == 'E' || first == 'I' || first == 'O' || first == 'U' {
		rs[0] = unicode.ToUpper(first)
	} else {
		rs[0] = unicode.ToLower(first)
	}
	return upper(string(rs[0])) + string(rs[1]) + upper(string(rs[2])) + string(rs[3:])
}

func mcSuffix(word string) (string, bool) {
	prefix := ""
	switch {
	case strings.HasPrefix(word, "Mc"):
		prefix = "Mc"
	case strings.HasPrefix(word, "mc"):
		prefix = "mc"
	case strings.HasPrefix(word, "MC"):
		prefix = "MC"
	default:
		return "", false
	}
	rs := []rune(word[len(prefix):])
	if len(rs) < 2 || !isWord(rs[0]) {
		return "", false
	}
	return word[len(prefix):], true
}

func hasInlinePeriod(word string) bool {
	rs := []rune(word)
	for i := 0; i+2 < len(rs); i++ {
		if unicode.IsLetter(rs[i]) && rs[i+1] == '.' && unicode.IsLetter(rs[i+2]) {
			return true
		}
	}
	return false
}

func hasInternalCapital(word string) bool {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunctuation(rs[i]) {
		i++
	}
	start := i
	for i < len(rs) && unicode.IsLetter(rs[i]) {
		i++
	}
	if i-start < 2 {
		return false
	}
	for j := start + 1; j < i; j++ {
		if unicode.IsUpper(rs[j]) {
			return true
		}
	}
	return false
}

func isConsonantAcronym(word string) bool {
	rs := []rune(word)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		folded, ok := asciiFold(r)
		if !ok {
			return false
		}
		switch folded {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

func asciiFold(r rune) (rune, bool) {
	current := r
	for {
		if (current >= 'a' && current <= 'z') || (current >= 'A' && current <= 'Z') {
			return unicode.ToLower(current), true
		}
		next := unicode.SimpleFold(current)
		if next == current || next == r {
			return 0, false
		}
		current = next
	}
}

func capitalizeFirstAfterPunctuation(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunctuation(rs[i]) {
		i++
	}
	if i < len(rs) && unicode.IsLetter(rs[i]) {
		return string(rs[:i]) + upper(string(rs[i])) + string(rs[i+1:])
	}
	return word
}

func capitalizeSmallFirst(word string) string {
	rs := []rune(word)
	start := 0
	for start < len(rs) && isPunctuation(rs[start]) {
		start++
	}
	end, ok := splitSmallPattern(word, start, true, true, false)
	if !ok {
		return word
	}
	return string(rs[:start]) + capitalize(string(rs[start:end])) + string(rs[end:])
}

func capitalizeSmallLast(word string) string {
	rs := []rune(word)
	end := len(rs)
	if end > 0 && isPunctuation(rs[end-1]) {
		end--
	}
	for start := 0; start <= end; start++ {
		if start > 0 && isWord(rs[start-1]) {
			continue
		}
		matchEnd, ok := splitSmallPattern(string(rs[:end]), start, true, false, true)
		if ok && matchEnd == end {
			return string(rs[:start]) + capitalize(string(rs[start:]))
		}
	}
	return word
}

func titleCaseWord(word string, allCaps, smallFirstLast bool) string {
	if allCaps && isUpperInitials(word) {
		return word
	}

	if isApostropheWord(word) {
		return transformApostropheWord(word)
	}

	if suffix, ok := mcSuffix(word); ok {
		prefix := capitalize(word[:len(word)-len(suffix)])
		return prefix + titleCaseText(suffix, true)
	}

	for _, title := range []string{"mr", "mrs", "ms", "dr"} {
		if strings.EqualFold(word, title) {
			rs := []rune(word)
			return upper(string(rs[0])) + string(rs[1:])
		}
	}

	if hasInlinePeriod(word) || (!allCaps && hasInternalCapital(word)) {
		return word
	}

	if isSmallWord(word) {
		return lower(word)
	}

	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i := range parts {
			parts[i] = titleCaseText(parts[i], false)
		}
		return strings.Join(parts, "/")
	}

	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i := range parts {
			parts[i] = titleCaseText(parts[i], false)
		}
		return strings.Join(parts, "-")
	}

	if allCaps {
		word = lower(word)
	}

	if isConsonantAcronym(word) {
		return upper(word)
	}

	return capitalizeFirstAfterPunctuation(word)
}

func applySubphrases(line string) string {
	rs := []rune(line)
	var out strings.Builder
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && strings.ContainsRune(subphrasePunctuation, rs[i]) && rs[i+1] == ' ' {
			end, ok := splitSmallPattern(line, i+2, false, false, false)
			if ok {
				out.WriteRune(rs[i])
				out.WriteRune(rs[i+1])
				out.WriteString(capitalize(string(rs[i+2 : end])))
				i = end
				continue
			}
		}
		out.WriteRune(rs[i])
		i++
	}
	return out.String()
}

func titleCaseLine(line string, smallFirstLast bool) string {
	allCaps := isAllCaps(line)
	rs := []rune(line)
	words := make([]string, 0)
	spaces := make([]string, 0)
	start := 0
	for i, r := range rs {
		if isPythonSpace(r) {
			words = append(words, string(rs[start:i]))
			spaces = append(spaces, string(r))
			start = i + 1
		}
	}
	words = append(words, string(rs[start:]))

	for i := range words {
		words[i] = titleCaseWord(words[i], allCaps, smallFirstLast)
	}
	if smallFirstLast && len(words) > 0 {
		words[0] = capitalizeSmallFirst(words[0])
		words[len(words)-1] = capitalizeSmallLast(words[len(words)-1])
	}

	var out strings.Builder
	for i, word := range words {
		out.WriteString(word)
		if i < len(spaces) {
			out.WriteString(spaces[i])
		}
	}
	return applySubphrases(out.String())
}

func titleCaseText(text string, smallFirstLast bool) string {
	lines := splitLines(text)
	for i := range lines {
		lines[i] = titleCaseLine(lines[i], smallFirstLast)
	}
	return strings.Join(lines, "\n")
}

func main() {
	input, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if _, err := io.WriteString(os.Stdout, titleCaseText(string(input), true)); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
EOF

gofmt -w "$repo/main.go"
find "$repo" \( -type f -o -type l \) -iname '*.py' -delete
