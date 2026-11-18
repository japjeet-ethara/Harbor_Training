package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
)

const smallWords = "|a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v|v.|via|vs|vs."
const punct = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

func isPunct(r rune) bool { return strings.ContainsRune(punct, r) }
func isWord(r rune) bool  { return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_' }
func isSmall(s string) bool {
	return strings.Contains(smallWords, "|"+strings.ToLower(s)+"|")
}
func pyCap(s string) string {
	r := []rune(s)
	if len(r) == 0 { return s }
	return string(unicode.ToTitle(r[0])) + strings.ToLower(string(r[1:]))
}
func capFirst(s string) string {
	r := []rune(s)
	for i, c := range r {
		if isPunct(c) { continue }
		if isWord(c) { r[i] = unicode.ToUpper(c); break }
		break
	}
	return string(r)
}
func onlyPunctPrefix(s string) (int, bool) {
	r := []rune(s)
	i := 0
	for i < len(r) && isPunct(r[i]) { i++ }
	return i, i < len(r)
}
func smallFirst(s string) string {
	r := []rune(s)
	i, ok := onlyPunctPrefix(s)
	if !ok { return s }
	j := i
	for j < len(r) && isWord(r[j]) { j++ }
	if j == i { return s }
	if !isSmall(string(r[i:j])) { return s }
	if j < len(r) && isWord(r[j]) { return s }
	return string(r[:i]) + pyCap(string(r[i:j])) + string(r[j:])
}
func smallLast(s string) string {
	r := []rune(s)
	end := len(r)
	if end > 0 && isPunct(r[end-1]) { end-- }
	start := end
	for start > 0 && isWord(r[start-1]) { start-- }
	if start == end || !isSmall(string(r[start:end])) { return s }
	if start > 0 && isWord(r[start-1]) { return s }
	return pyCap(string(r[start:]))
}
func ucInitials(s string) bool {
	r := []rune(s)
	var match func(int) bool
	match = func(i int) bool {
		if i == len(r) { return true }
		if i+1 < len(r) && r[i] >= 'A' && r[i] <= 'Z' && r[i+1] == '.' && match(i+2) { return true }
		return i+2 < len(r) && r[i] >= 'A' && r[i] <= 'Z' && r[i+1] == '.' && r[i+2] >= 'A' && r[i+2] <= 'Z' && match(i+3)
	}
	return len(r) >= 2 && match(0)
}
func inlinePeriod(s string) bool {
	r := []rune(s)
	for i := 1; i+1 < len(r); i++ {
		if r[i] == '.' && isWord(r[i-1]) && isWord(r[i+1]) { return true }
	}
	return false
}
func ucElsewhere(s string) bool {
	i, _ := onlyPunctPrefix(s)
	r := []rune(s)
	end := i
	for end < len(r) && (r[end] >= 'a' && r[end] <= 'z' || r[end] >= 'A' && r[end] <= 'Z') { end++ }
	for j := i + 1; j < end; j++ {
		if r[j] >= 'A' && r[j] <= 'Z' { return true }
	}
	return false
}
func aposSecond(s string) (string, bool) {
	r := []rune(s)
	if len(r) < 3 || !strings.ContainsRune("dolDOL", r[0]) || (r[1] != '\'' && r[1] != '‘') { return s, false }
	end := len(r)
	if end >= 2 && (r[end-2] == '\'' || r[end-2] == 's') && (r[end-1] == '\'' || r[end-1] == 's') { end -= 2 }
	if end < 3 { return s, false }
	for _, c := range r[2:end] { if !unicode.IsLetter(c) && !unicode.IsDigit(c) && c != '_' { return s, false } }
	if len(r) > end { for _, c := range r[end:] { if c != '\'' && c != 's' { return s, false } } }
	if strings.ContainsRune("aeiouAEIOU", r[0]) { r[0] = unicode.ToUpper(r[0]) } else { r[0] = unicode.ToLower(r[0]) }
	r[2] = unicode.ToUpper(r[2])
	return string(r), true
}
func mcName(s string) (string, bool) {
	r := []rune(s)
	if len(r) < 4 { return s, false }
	prefix := string(r[:2])
	if prefix != "Mc" && prefix != "mc" && prefix != "MC" { return s, false }
	if !isWord(r[2]) || len(r[3:]) == 0 { return s, false }
	return pyCap(prefix) + titlecase(string(r[2:]), true), true
}
func titlecaseWord(word string, allCaps bool) string {
	if allCaps && ucInitials(word) { return word }
	if v, ok := aposSecond(word); ok { return v }
	if v, ok := mcName(word); ok { return v }
	if strings.EqualFold(word, "m") || strings.EqualFold(word, "mr") || strings.EqualFold(word, "mrs") || strings.EqualFold(word, "ms") || strings.EqualFold(word, "dr") {
		r := []rune(word); r[0] = unicode.ToUpper(r[0]); return string(r)
	}
	if inlinePeriod(word) || (!allCaps && ucElsewhere(word)) { return word }
	if isSmall(word) { return strings.ToLower(word) }
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, p := range parts { parts[i] = titlecase(p, false) }
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts { parts[i] = titlecase(p, false) }
		return strings.Join(parts, "-")
	}
	if allCaps { word = strings.ToLower(word) }
	r := []rune(word)
	consonant := len(r) > 2
	for _, c := range r { if !strings.ContainsRune("bcdfghjklmnpqrstvwxz", unicode.ToLower(c)) { consonant = false; break } }
	if consonant { return strings.ToUpper(word) }
	return capFirst(word)
}
func splitWords(line string) ([]string, []string) {
	r := []rune(line)
	words, spaces := []string{}, []string{}
	start := 0
	for i, c := range r {
		if unicode.IsSpace(c) {
			words = append(words, string(r[start:i]))
			spaces = append(spaces, string(c))
			start = i + 1
		}
	}
	words = append(words, string(r[start:]))
	return words, spaces
}
func subphrase(s string) string {
	r := []rune(s)
	for i := 0; i+2 < len(r); i++ {
		if !strings.ContainsRune(":;.!?-–‒—―", r[i]) || r[i+1] != ' ' { continue }
		start := i+2
		end := start
		for end < len(r) && isWord(r[end]) { end++ }
		if end > start && isSmall(string(r[start:end])) { r[start] = unicode.ToUpper(r[start]) }
	}
	return string(r)
}
func titlecase(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitWords(line)
	tc := make([]string, len(words))
	for i, word := range words { tc[i] = titlecaseWord(word, allCaps) }
	if smallFirstLast && len(tc) > 0 {
		tc[0] = smallFirst(tc[0])
		tc[len(tc)-1] = smallLast(tc[len(tc)-1])
	}
	var b strings.Builder
	for i, word := range tc {
		b.WriteString(word)
		if i < len(spaces) { b.WriteString(spaces[i]) }
	}
	return subphrase(b.String())
}
func main() {
	r := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for {
		line, err := r.ReadString('\n')
		if strings.HasSuffix(line, "\n") {
			line = strings.TrimSuffix(line, "\n")
			line = strings.TrimSuffix(line, "\r")
			fmt.Fprintln(out, titlecase(line, true))
		} else if len(line) > 0 {
			fmt.Fprintln(out, titlecase(line, true))
		}
		if err == io.EOF { break }
		if err != nil { return }
	}
}
