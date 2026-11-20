#!/bin/sh
set -eu
cd /workspace/repo

cat > go.mod << 'END_GO_MOD'
module titlecase

go 1.23
END_GO_MOD

cat > main.go << 'END_GO_SRC'
package main

import (
	"bufio"
	"os"
	"strings"
	"unicode"
)

// Punctuation from the Python titlecase character class.
const punctSet = "!\"#$%&'()*+,-./:;?@[\\]_`{|}~\u2012\u2013\u2014\u2015\u2018\u201c"

// Sub-phrase openers: colon, period, semicolon, question, exclamation, and dashes.
const subphraseSet = ":.;?!\u002d\u2012\u2013\u2014\u2015"

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 10*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	for in.Scan() {
		out.WriteString(titlecase(in.Text(), true))
		out.WriteByte('\n')
	}
	out.Flush()
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		processed = append(processed, titlecaseLine(line, smallFirstLast))
	}
	return strings.Join(processed, "\n")
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitSpaces(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = titleWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return subphrase(joinWords(tc, spaces))
}

func titleWord(word string, allCaps bool) string {
	if word == "" {
		return ""
	}
	if allCaps && isInitials(word) {
		return word
	}
	if replaced, ok := apostropheWord(word); ok {
		return replaced
	}
	if prefix, rest, ok := macSplit(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isHonorific(word) {
		rs := []rune(word)
		return string(unicode.ToUpper(rs[0])) + string(rs[1:])
	}
	if hasInlinePeriod(word) || (!allCaps && hasInternalCap(word)) {
		return word
	}
	if isSmallWord(word) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = titlecase(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = titlecase(part, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if len([]rune(word)) > 2 && allConsonants(word) {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func splitNewlines(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	var b strings.Builder
	breaking := false
	for _, r := range text {
		if r == '\n' || r == '\r' {
			if !breaking {
				lines = append(lines, b.String())
				b.Reset()
				breaking = true
			}
			continue
		}
		breaking = false
		b.WriteRune(r)
	}
	lines = append(lines, b.String())
	return lines
}

func splitSpaces(s string) (words, spaces []string) {
	var b strings.Builder
	for _, r := range s {
		if unicode.IsSpace(r) {
			words = append(words, b.String())
			b.Reset()
			spaces = append(spaces, string(r))
			continue
		}
		b.WriteRune(r)
	}
	words = append(words, b.String())
	if len(words) == 0 {
		words = []string{""}
	}
	return words, spaces
}

func joinWords(words, spaces []string) string {
	n := len(words) + len(spaces)
	parts := make([]string, n)
	for i, word := range words {
		parts[i*2] = word
	}
	for i, space := range spaces {
		parts[i*2+1] = space
	}
	return strings.Join(parts, "")
}

func isPunct(r rune) bool {
	return strings.ContainsRune(punctSet, r)
}

func isSubphrasePunct(r rune) bool {
	return strings.ContainsRune(subphraseSet, r)
}

func isWord(r rune) bool {
	if r == '_' {
		return true
	}
	return unicode.IsLetter(r) || unicode.IsNumber(r) || unicode.IsMark(r) || unicode.In(r, unicode.Pc)
}

func isInitials(s string) bool {
	rs := []rune(s)
	n := len(rs)
	if n == 0 {
		return false
	}
	ok := make([]bool, n+1)
	ok[n] = true
	for i := n - 1; i >= 0; i-- {
		if i+1 < n && unicode.IsUpper(rs[i]) && rs[i+1] == '.' && ok[i+2] {
			ok[i] = true
			continue
		}
		if i+2 < n && unicode.IsUpper(rs[i]) && rs[i+1] == '.' && unicode.IsUpper(rs[i+2]) && ok[i+3] {
			ok[i] = true
		}
	}
	return ok[0]
}

func apostropheWord(word string) (string, bool) {
	rs := []rune(word)
	if len(rs) < 3 {
		return "", false
	}
	switch rs[0] {
	case 'd', 'o', 'l', 'D', 'O', 'L':
	default:
		return "", false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return "", false
	}
	i := 2
	if !unicode.IsLetter(rs[i]) {
		return "", false
	}
	i++
	for i < len(rs) && unicode.IsLetter(rs[i]) {
		i++
	}
	if i != len(rs) {
		if len(rs)-i != 2 || !isApostropheOrS(rs[i]) || !isApostropheOrS(rs[i+1]) {
			return "", false
		}
	}
	out := make([]rune, len(rs))
	copy(out, rs)
	if !isASCIIVowel(rs[0]) {
		out[0] = unicode.ToLower(rs[0])
	} else {
		out[0] = unicode.ToUpper(rs[0])
	}
	out[2] = unicode.ToUpper(rs[2])
	return string(out), true
}

func isApostropheOrS(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func isASCIIVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func macSplit(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	prefix = string(rs[:2])
	if prefix != "Mc" && prefix != "mc" && prefix != "MC" {
		return "", "", false
	}
	if !isWord(rs[2]) {
		return "", "", false
	}
	return prefix, string(rs[2:]), true
}

func isHonorific(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
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

func hasInternalCap(word string) bool {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return false
	}
	seenLetter := false
	for ; i < len(rs); i++ {
		if !unicode.IsLetter(rs[i]) {
			return false
		}
		if seenLetter && unicode.IsUpper(rs[i]) {
			return true
		}
		seenLetter = true
	}
	return false
}

func isSmallWord(word string) bool {
	switch strings.ToLower(word) {
	case "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
		"of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.":
		return true
	default:
		return false
	}
}

var smallAlts = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

func matchSmallPrefix(rs []rune, i int) (int, bool) {
	for _, alt := range smallAlts {
		altRunes := []rune(alt)
		end := i + len(altRunes)
		if end > len(rs) {
			continue
		}
		if string(rs[i:end]) == alt {
			return end, true
		}
	}
	return 0, false
}

func applySmallFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	for _, alt := range smallAlts {
		altRunes := []rune(alt)
		end := i + len(altRunes)
		if end > len(rs) {
			continue
		}
		if !strings.EqualFold(string(rs[i:end]), alt) {
			continue
		}
		if !boundaryAfter(rs, end) {
			continue
		}
		return string(rs[:i]) + capitalize(string(rs[i:end])) + string(rs[end:])
	}
	return word
}

func applySmallLast(word string) string {
	rs := []rune(word)
	if len(rs) == 0 {
		return word
	}
	if replaced, ok := smallLastAt(rs, true); ok {
		return replaced
	}
	if replaced, ok := smallLastAt(rs, false); ok {
		return replaced
	}
	return word
}

func smallLastAt(rs []rune, punct bool) (string, bool) {
	end := len(rs)
	if punct {
		if !isPunct(rs[len(rs)-1]) {
			return "", false
		}
		end--
	}
	for _, alt := range smallAlts {
		altRunes := []rune(alt)
		start := end - len(altRunes)
		if start < 0 {
			continue
		}
		if !strings.EqualFold(string(rs[start:end]), alt) {
			continue
		}
		if !boundaryBefore(rs, start) {
			continue
		}
		return string(rs[:start]) + capitalize(string(rs[start:])), true
	}
	return "", false
}

func boundaryAfter(rs []rune, end int) bool {
	if end <= 0 {
		return false
	}
	left := isWord(rs[end-1])
	if end >= len(rs) {
		return left
	}
	return left != isWord(rs[end])
}

func boundaryBefore(rs []rune, start int) bool {
	if start < 0 || start > len(rs) {
		return false
	}
	if start == 0 {
		return start < len(rs) && isWord(rs[0])
	}
	if start == len(rs) {
		return isWord(rs[start-1])
	}
	return isWord(rs[start-1]) != isWord(rs[start])
}

func subphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(rs) {
		if i+2 < len(rs) && isSubphrasePunct(rs[i]) && rs[i+1] == ' ' {
			if end, ok := matchSmallPrefix(rs, i+2); ok {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(capitalize(string(rs[i+2 : end])))
				i = end
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

func allConsonants(word string) bool {
	if word == "" {
		return false
	}
	for _, r := range word {
		if r > unicode.MaxASCII {
			return false
		}
		lower := unicode.ToLower(r)
		if lower < 'a' || lower > 'z' {
			return false
		}
		switch lower {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return word
	}
	out := make([]rune, len(rs))
	copy(out, rs)
	out[i] = unicode.ToUpper(rs[i])
	return string(out)
}

func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	out := make([]rune, len(rs))
	out[0] = unicode.ToUpper(rs[0])
	for i := 1; i < len(rs); i++ {
		out[i] = unicode.ToLower(rs[i])
	}
	return string(out)
}
END_GO_SRC

find /workspace/repo -type f -name '*.py' -delete
# go build names the binary after the module (titlecase). The Python
# package directory would make that output path a directory.
rm -rf /workspace/repo/titlecase
