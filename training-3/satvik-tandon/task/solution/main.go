package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
)

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

// Order matters where a regex may match the prefix of a longer word.
var smallWords = strings.Fields("a an and as at but by en for if in of on or the to v. v via vs. vs")

var (
	initials        = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
	honorific       = regexp.MustCompile(`^(?:[Mm](?:[Rr][Ss]?|[Ss])|[Dd][Rr])$`)
	internalCapital = regexp.MustCompile(`^[a-zA-Z]+[A-Z]`)
	subphrase       = regexp.MustCompile(`([:.;?!\-–‒—―] )(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)`)
)

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isSpace(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

// Python's case-insensitive matching against ASCII also accepts these letters.
func asciiFold(r rune) rune {
	switch r {
	case 'İ', 'ı':
		return 'i'
	case 'ſ':
		return 's'
	case 'K':
		return 'k'
	}
	if r >= 'A' && r <= 'Z' {
		return r + ('a' - 'A')
	}
	return r
}

func upperRune(r rune) string {
	if expanded, ok := upperExpansion[r]; ok {
		return expanded
	}
	return string(unicode.ToUpper(r))
}

func lower(s string) string {
	chars := []rune(s)
	var out strings.Builder
	for i, r := range chars {
		switch {
		case r == 'İ':
			out.WriteString("i\u0307")
		case r == 'Σ' && hasCasedNeighbor(chars, i, -1) && !hasCasedNeighbor(chars, i, 1):
			out.WriteRune('ς')
		default:
			out.WriteRune(unicode.ToLower(r))
		}
	}
	return out.String()
}

func hasCasedNeighbor(chars []rune, start, step int) bool {
	for i := start + step; i >= 0 && i < len(chars); i += step {
		r := chars[i]
		if unicode.Is(unicode.Mn, r) || unicode.Is(unicode.Me, r) || unicode.Is(unicode.Cf, r) ||
			unicode.Is(unicode.Lm, r) || unicode.Is(unicode.Sk, r) || strings.ContainsRune("'.:·’", r) {
			continue
		}
		return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r)
	}
	return false
}

func capitalize(s string) string {
	chars := []rune(s)
	if len(chars) == 0 {
		return ""
	}
	head, ok := titleExpansion[chars[0]]
	if !ok {
		head = string(unicode.ToTitle(chars[0]))
	}
	// Lower the entire token first so a final sigma can see the initial letter.
	tail := []rune(lower(s))
	if chars[0] == 'İ' {
		return head + string(tail[2:])
	}
	return head + string(tail[1:])
}

func isSmall(s string) bool {
	folded := strings.Map(asciiFold, s)
	for _, candidate := range smallWords {
		if folded == candidate {
			return true
		}
	}
	return false
}

func hasInlinePeriod(chars []rune) bool {
	for i := 1; i+1 < len(chars); i++ {
		if chars[i] == '.' && isWord(chars[i-1]) && isWord(chars[i+1]) {
			return true
		}
	}
	return false
}

func hasApostrophePrefix(chars []rune) bool {
	if len(chars) < 3 || !strings.ContainsRune("dol", asciiFold(chars[0])) ||
		(chars[1] != '\'' && chars[1] != '‘') || !isWord(chars[2]) {
		return false
	}
	end := len(chars)
	isSuffixChar := func(r rune) bool { return r == '\'' || asciiFold(r) == 's' }
	if end >= 5 && isSuffixChar(chars[end-2]) && isSuffixChar(chars[end-1]) {
		end -= 2
	}
	for _, r := range chars[3:end] {
		if !isWord(r) {
			return false
		}
	}
	return true
}

func allCaps(s string) bool {
	for _, r := range s {
		if upperRune(r) != string(r) {
			return false
		}
	}
	return true
}

func transformWord(word string, lineAllCaps bool) string {
	chars := []rune(word)
	if lineAllCaps && initials.MatchString(word) {
		return word
	}
	if hasApostrophePrefix(chars) {
		first := lower(string(chars[0]))
		if asciiFold(chars[0]) == 'o' {
			first = upperRune(chars[0])
		}
		return first + string(chars[1]) + upperRune(chars[2]) + string(chars[3:])
	}
	if len(chars) >= 4 && (strings.HasPrefix(word, "Mc") || strings.HasPrefix(word, "mc") || strings.HasPrefix(word, "MC")) && isWord(chars[2]) {
		return "Mc" + transformTitle(word[2:], true)
	}
	if honorific.MatchString(word) {
		return upperRune(chars[0]) + word[1:]
	}
	if hasInlinePeriod(chars) || (!lineAllCaps && internalCapital.MatchString(strings.TrimLeft(word, punctuation))) {
		return word
	}
	if isSmall(word) {
		return lower(word)
	}
	for _, delimiter := range []string{"/", "-"} {
		if !strings.Contains(word, delimiter) || (delimiter == "/" && strings.Contains(word, "//")) {
			continue
		}
		parts := strings.Split(word, delimiter)
		for i, part := range parts {
			parts[i] = transformTitle(part, false)
		}
		return strings.Join(parts, delimiter)
	}
	if lineAllCaps {
		word = lower(word)
		chars = []rune(word)
	}
	if len(chars) > 2 && strings.IndexFunc(word, func(r rune) bool {
		return !strings.ContainsRune("bcdfghjklmnpqrstvwxz", asciiFold(r))
	}) == -1 {
		var upper strings.Builder
		for _, r := range word {
			upper.WriteString(upperRune(r))
		}
		return upper.String()
	}
	for i, r := range chars {
		if isWord(r) {
			return string(chars[:i]) + upperRune(r) + string(chars[i+1:])
		}
		if !strings.ContainsRune(punctuation, r) {
			break
		}
	}
	return word
}

func capitalizeFirstSmall(word string) string {
	chars := []rune(word)
	start := 0
	for start < len(chars) && strings.ContainsRune(punctuation, chars[start]) {
		start++
	}
	folded := strings.Map(asciiFold, string(chars[start:]))
	for _, candidate := range smallWords {
		if !strings.HasPrefix(folded, candidate) {
			continue
		}
		end := start + len(candidate)
		if (end == len(chars) && isWord(chars[end-1])) ||
			(end < len(chars) && isWord(chars[end-1]) != isWord(chars[end])) {
			return string(chars[:start]) + capitalize(string(chars[start:end])) + string(chars[end:])
		}
	}
	return word
}

func capitalizeLastSmall(word string) string {
	chars := []rune(word)
	for start, r := range chars {
		if !isWord(r) || (start > 0 && isWord(chars[start-1])) {
			continue
		}
		ending := chars[start:]
		if isSmall(string(ending)) || (len(ending) > 1 &&
			strings.ContainsRune(punctuation, ending[len(ending)-1]) && isSmall(string(ending[:len(ending)-1]))) {
			return string(chars[:start]) + capitalize(string(ending))
		}
	}
	return word
}

func transformTitle(line string, smallAtEdges bool) string {
	caps := allCaps(line)
	words := make([]string, 0, 8)
	separators := make([]rune, 0, 7)
	start := 0
	for i, r := range line {
		if isSpace(r) {
			words = append(words, transformWord(line[start:i], caps))
			separators = append(separators, r)
			start = i + len(string(r))
		}
	}
	words = append(words, transformWord(line[start:], caps))
	if smallAtEdges {
		words[0] = capitalizeFirstSmall(words[0])
		last := len(words) - 1
		words[last] = capitalizeLastSmall(words[last])
	}
	var out strings.Builder
	for i, separator := range separators {
		out.WriteString(words[i])
		out.WriteRune(separator)
	}
	out.WriteString(words[len(words)-1])
	return subphrase.ReplaceAllStringFunc(out.String(), func(match string) string {
		start := strings.IndexByte(match, ' ') + 1
		return match[:start] + capitalize(match[start:])
	})
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 64*1024), 16*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	for in.Scan() {
		fmt.Fprintln(out, transformTitle(in.Text(), true))
	}
	if err := in.Err(); err != nil {
		panic(err)
	}
	if err := out.Flush(); err != nil {
		panic(err)
	}
}
