// A Go port of python-titlecase at commit
// 42f43e2de55bf003b286c6f8e8d8b2d26676a167, default titlecase(text),
// using CPython 3.12's standard-library re backend.
// Original project copyright (c) 2021 Patrick William Pannuto; MIT.
// See the original LICENSE.txt retained in the repository.
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"regexp"
	"strings"
	"unicode/utf8"
)

type runeRange struct{ lo, hi rune }

func inRanges(ch rune, ranges []runeRange) bool {
	lo, hi := 0, len(ranges)
	for lo < hi {
		mid := lo + (hi-lo)/2
		if ch < ranges[mid].lo {
			hi = mid
		} else if ch > ranges[mid].hi {
			lo = mid + 1
		} else {
			return true
		}
	}
	return false
}

func pyWord(ch rune) bool          { return inRanges(ch, pyWordRanges) }
func pySpace(ch rune) bool         { return inRanges(ch, pySpaceRanges) }
func pyCased(ch rune) bool         { return inRanges(ch, pyCasedRanges) }
func pyCaseIgnorable(ch rune) bool { return inRanges(ch, pyCaseIgnorableRanges) }

func mapped(ch rune, table map[rune]string) string {
	if value, ok := table[ch]; ok {
		return value
	}
	return string(ch)
}

func pyUpper(text string) string {
	var out strings.Builder
	for _, ch := range text {
		out.WriteString(mapped(ch, pyUpperMap))
	}
	return out.String()
}

// Python's lowercase sigma depends on the original string on both sides.
func lowerRuneAt(chars []rune, at int) string {
	ch := chars[at]
	if ch == '\u03a3' {
		before := at - 1
		for before >= 0 && pyCaseIgnorable(chars[before]) {
			before--
		}
		after := at + 1
		for after < len(chars) && pyCaseIgnorable(chars[after]) {
			after++
		}
		if before >= 0 && pyCased(chars[before]) && (after == len(chars) || !pyCased(chars[after])) {
			return "\u03c2"
		}
	}
	return mapped(ch, pyLowerMap)
}

func pyLower(text string) string {
	chars := []rune(text)
	var out strings.Builder
	for at := range chars {
		out.WriteString(lowerRuneAt(chars, at))
	}
	return out.String()
}

func pyCapitalize(text string) string {
	chars := []rune(text)
	if len(chars) == 0 {
		return text
	}
	var out strings.Builder
	out.WriteString(mapped(chars[0], pyTitleMap))
	for at := 1; at < len(chars); at++ {
		out.WriteString(lowerRuneAt(chars, at))
	}
	return out.String()
}

// Python re.I applied to an ASCII letter additionally equates I with dotted
// and dotless I, S with long s, and K with the Kelvin sign.
func asciiFold(ch rune) rune {
	if ch >= 'A' && ch <= 'Z' {
		return ch + ('a' - 'A')
	}
	switch ch {
	case '\u0130', '\u0131':
		return 'i'
	case '\u017f':
		return 's'
	case '\u212a':
		return 'k'
	}
	return ch
}

func equalsASCII(chars []rune, literal string, fold bool) bool {
	if len(chars) != len(literal) {
		return false
	}
	for i, ch := range chars {
		if fold {
			ch = asciiFold(ch)
		}
		if ch != rune(literal[i]) {
			return false
		}
	}
	return true
}

func punct(ch rune) bool {
	switch ch {
	case 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29,
		0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x3A, 0x3B, 0x3F,
		0x40, 0x5B, 0x5C, 0x5D, 0x5F, 0x60, 0x7B, 0x7C, 0x7D,
		0x7E, 0x2012, 0x2013, 0x2014, 0x2015, 0x2018, 0x201C:
		return true
	}
	return false
}

func boundary(chars []rune, at int) bool {
	left, right := false, false
	if at > 0 {
		left = pyWord(chars[at-1])
	}
	if at < len(chars) {
		right = pyWord(chars[at])
	}
	return left != right
}

// Preserve Python's regex alternation order, including greedy optional dots.
var smallWords = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v", "via", "vs",
}

func smallEnds(chars []rune, start int, fold bool) []int {
	var result []int
	for _, small := range smallWords {
		end := start + len(small)
		if end > len(chars) || !equalsASCII(chars[start:end], small, fold) {
			continue
		}
		if (small == "v" || small == "vs") && end < len(chars) && chars[end] == '.' {
			result = append(result, end+1)
		}
		result = append(result, end)
	}
	return result
}

func isSmall(chars []rune) bool {
	for _, end := range smallEnds(chars, 0, true) {
		if end == len(chars) {
			return true
		}
	}
	return false
}

func smallFirst(text string) string {
	chars := []rune(text)
	start := 0
	for start < len(chars) && punct(chars[start]) {
		start++
	}
	for _, end := range smallEnds(chars, start, true) {
		if boundary(chars, end) {
			return string(chars[:start]) + pyCapitalize(string(chars[start:end])) + string(chars[end:])
		}
	}
	return text
}

func smallLast(text string) string {
	chars := []rune(text)
	for start := 0; start < len(chars); start++ {
		if !boundary(chars, start) {
			continue
		}
		for _, end := range smallEnds(chars, start, true) {
			if end == len(chars) || (end+1 == len(chars) && punct(chars[end])) {
				return string(chars[:start]) + pyCapitalize(string(chars[start:]))
			}
		}
	}
	return text
}

func subphrasePunct(ch rune) bool {
	switch ch {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	}
	return false
}

func subphrases(text string) string {
	chars := []rune(text)
	var out strings.Builder
	for at := 0; at < len(chars); {
		if at+2 < len(chars) && subphrasePunct(chars[at]) && chars[at+1] == ' ' {
			ends := smallEnds(chars, at+2, false)
			if len(ends) > 0 {
				end := ends[0]
				out.WriteString(string(chars[at : at+2]))
				out.WriteString(pyCapitalize(string(chars[at+2 : end])))
				at = end
				continue
			}
		}
		out.WriteRune(chars[at])
		at++
	}
	return out.String()
}

var initialsRE = regexp.MustCompile(`^([A-Z]\.|[A-Z]\.[A-Z])+$`)

func allWord(chars []rune) bool {
	if len(chars) == 0 {
		return false
	}
	for _, ch := range chars {
		if !pyWord(ch) {
			return false
		}
	}
	return true
}

func aposSecond(chars []rune) bool {
	if len(chars) < 3 || (chars[1] != '\'' && chars[1] != '\u2018') {
		return false
	}
	first := asciiFold(chars[0])
	if first != 'd' && first != 'o' && first != 'l' {
		return false
	}
	if allWord(chars[2:]) {
		return true
	}
	if len(chars) < 5 || !allWord(chars[2:len(chars)-2]) {
		return false
	}
	for _, ch := range chars[len(chars)-2:] {
		if ch != '\'' && asciiFold(ch) != 's' {
			return false
		}
	}
	return true
}

func inlinePeriod(chars []rune) bool {
	for i := 1; i+1 < len(chars); i++ {
		if chars[i] == '.' && pyWord(chars[i-1]) && pyWord(chars[i+1]) {
			return true
		}
	}
	return false
}

func isASCIILetter(ch rune) bool { return ch >= 'A' && ch <= 'Z' || ch >= 'a' && ch <= 'z' }

func uppercaseElsewhere(chars []rune) bool {
	start := 0
	for start < len(chars) && punct(chars[start]) {
		start++
	}
	for i := start; i < len(chars) && isASCIILetter(chars[i]); i++ {
		if i > start && chars[i] >= 'A' && chars[i] <= 'Z' {
			return true
		}
	}
	return false
}

func allConsonants(chars []rune) bool {
	if len(chars) <= 2 {
		return false
	}
	for _, ch := range chars {
		ch = asciiFold(ch)
		if ch < 'a' || ch > 'z' || strings.ContainsRune("aeiouy", ch) {
			return false
		}
	}
	return true
}

func capitalizeFirstWordCharacter(text string) string {
	chars := []rune(text)
	for at, ch := range chars {
		if pyWord(ch) {
			return pyUpper(string(chars[:at+1])) + string(chars[at+1:])
		}
		if !punct(ch) {
			break
		}
	}
	return text
}

func processWord(word string, allCaps bool) string {
	chars := []rune(word)
	if allCaps && initialsRE.MatchString(word) {
		return word
	}
	if aposSecond(chars) {
		prefix := pyLower(string(chars[0]))
		if strings.ContainsRune("aeiouAEIOU", chars[0]) {
			prefix = pyUpper(string(chars[0]))
		}
		return prefix + string(chars[1]) + pyUpper(string(chars[2])) + string(chars[3:])
	}
	if len(chars) >= 4 && ((chars[0] == 'm' || chars[0] == 'M') && chars[1] == 'c' || chars[0] == 'M' && chars[1] == 'C') && pyWord(chars[2]) {
		return "Mc" + titlecase(string(chars[2:]), true)
	}
	for _, honorific := range []string{"mr", "mrs", "ms", "dr"} {
		if equalsASCII(chars, honorific, true) {
			return pyUpper(string(chars[0])) + string(chars[1:])
		}
	}
	if inlinePeriod(chars) || !allCaps && uppercaseElsewhere(chars) {
		return word
	}
	if isSmall(chars) {
		return pyLower(word)
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
	if allCaps {
		word = pyLower(word)
		chars = []rune(word)
	}
	if allConsonants(chars) {
		return pyUpper(word)
	}
	return capitalizeFirstWordCharacter(word)
}

func titlecaseLine(line string, firstLast bool) string {
	allCaps := pyUpper(line) == line
	var words, separators []string
	start := 0
	for at, ch := range line {
		if pySpace(ch) {
			words = append(words, processWord(line[start:at], allCaps))
			separators = append(separators, string(ch))
			start = at + utf8.RuneLen(ch)
		}
	}
	words = append(words, processWord(line[start:], allCaps))
	if firstLast {
		words[0] = smallFirst(words[0])
		words[len(words)-1] = smallLast(words[len(words)-1])
	}
	var out strings.Builder
	for at, word := range words {
		out.WriteString(word)
		if at < len(separators) {
			out.WriteString(separators[at])
		}
	}
	return subphrases(out.String())
}

// Reproduce regex.split('[\\r\\n]+', text), retaining empty end components.
// Public line-oriented inputs exclude CR/LF, but recursion uses the same API.
func titlecase(text string, firstLast bool) string {
	var result []string
	start := 0
	for at := 0; at < len(text); {
		if text[at] != '\r' && text[at] != '\n' {
			at++
			continue
		}
		result = append(result, titlecaseLine(text[start:at], firstLast))
		for at < len(text) && (text[at] == '\r' || text[at] == '\n') {
			at++
		}
		start = at
	}
	result = append(result, titlecaseLine(text[start:], firstLast))
	return strings.Join(result, "\n")
}

func main() {
	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	for {
		line, err := reader.ReadString('\n')
		if len(line) > 0 {
			if line[len(line)-1] == '\n' {
				line = line[:len(line)-1]
			}
			if !utf8.ValidString(line) {
				fmt.Fprintln(os.Stderr, "input must be valid UTF-8")
				os.Exit(1)
			}
			if _, writeErr := writer.WriteString(titlecase(line, true) + "\n"); writeErr != nil {
				fmt.Fprintln(os.Stderr, writeErr)
				os.Exit(1)
			}
		}
		if err != nil {
			if err != io.EOF {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
			break
		}
	}
	if err := writer.Flush(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
