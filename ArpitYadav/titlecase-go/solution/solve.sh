#!/usr/bin/env bash
set -euo pipefail

# 1. Generate go.mod
cat << 'EOF' > go.mod
module titlecase

go 1.23
EOF

# 2. Generate casing.go
cat << 'EOF' > casing.go
package main

import (
	"regexp"
	"strings"
	"unicode"
)

var punctRunes = map[rune]bool{
	'!': true, '"': true, '“': true, '#': true, '$': true, '%': true, '&': true,
	'\'': true, '‘': true, '(': true, ')': true, '*': true, '+': true, ',': true,
	'-': true, '–': true, '‒': true, '—': true, '―': true, '.': true, '/': true,
	':': true, ';': true, '?': true, '@': true, '[': true, '\\': true, ']': true,
	'_': true, '`': true, '{': true, '|': true, '}': true, '~': true,
}

var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true, "but": true,
	"by": true, "en": true, "for": true, "if": true, "in": true, "of": true,
	"on": true, "or": true, "the": true, "to": true, "v": true, "v.": true,
	"via": true, "vs": true, "vs.": true,
}

var ucInitialsRegex = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)

func isConsonant(r rune) bool {
	switch r {
	case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z',
		'B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Z':
		return true
	}
	return false
}

func isAllConsonants(w string) bool {
	if len(w) == 0 {
		return false
	}
	for _, r := range w {
		if !isConsonant(r) {
			return false
		}
	}
	return true
}

func isWordChar(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

func hasInlinePeriod(w string) bool {
	runes := []rune(w)
	for i := 1; i < len(runes)-1; i++ {
		if runes[i] == '.' && isWordChar(runes[i-1]) && isWordChar(runes[i+1]) {
			return true
		}
	}
	return false
}

func hasUCElsewhere(w string) bool {
	runes := []rune(w)
	idx := 0
	for idx < len(runes) && punctRunes[runes[idx]] {
		idx++
	}
	if idx >= len(runes) {
		return false
	}
	if !((runes[idx] >= 'a' && runes[idx] <= 'z') || (runes[idx] >= 'A' && runes[idx] <= 'Z')) {
		return false
	}
	idx++
	for ; idx < len(runes); idx++ {
		if runes[idx] >= 'A' && runes[idx] <= 'Z' {
			return true
		}
	}
	return false
}

func matchAposSecond(w string) (bool, string) {
	runes := []rune(w)
	if len(runes) < 3 {
		return false, ""
	}
	firstLower := unicode.ToLower(runes[0])
	if firstLower != 'd' && firstLower != 'o' && firstLower != 'l' {
		return false, ""
	}
	if runes[1] != '\'' && runes[1] != '‘' {
		return false, ""
	}
	if !isWordChar(runes[2]) {
		return false, ""
	}

	i := 2
	for i < len(runes) && isWordChar(runes[i]) {
		i++
	}
	if i < len(runes) {
		rem := runes[i:]
		if len(rem) == 2 {
			c1, c2 := rem[0], rem[1]
			valid := (c1 == '\'' || c1 == 's' || c1 == 'S') && (c2 == '\'' || c2 == 's' || c2 == 'S')
			if !valid {
				return false, ""
			}
		} else {
			return false, ""
		}
	}

	res := make([]rune, len(runes))
	copy(res, runes)
	if firstLower == 'o' {
		res[0] = unicode.ToUpper(runes[0])
	} else {
		res[0] = unicode.ToLower(runes[0])
	}
	res[2] = unicode.ToUpper(runes[2])
	return true, string(res)
}

func matchMacMc(w string) (bool, string) {
	runes := []rune(w)
	if len(runes) < 4 {
		return false, ""
	}
	prefix := string(runes[:2])
	if prefix == "Mc" || prefix == "mc" || prefix == "MC" {
		if isWordChar(runes[2]) {
			rem := TitlecaseLineInternal(string(runes[2:]), true)
			return true, "Mc" + rem
		}
	}
	return false, ""
}

func matchHonorific(w string) (bool, string) {
	lower := strings.ToLower(w)
	if lower == "m" || lower == "mr" || lower == "mrs" || lower == "ms" || lower == "dr" {
		runes := []rune(w)
		runes[0] = unicode.ToUpper(runes[0])
		return true, string(runes)
	}
	return false, ""
}

func capFirst(w string) string {
	runes := []rune(w)
	i := 0
	for i < len(runes) && punctRunes[runes[i]] {
		i++
	}
	if i < len(runes) && unicode.IsLetter(runes[i]) {
		runes[i] = unicode.ToUpper(runes[i])
		return string(runes)
	}
	return w
}

func TitlecaseWord(word string, allCaps bool, allowRecursion bool) string {
	if word == "" {
		return ""
	}

	if allCaps && ucInitialsRegex.MatchString(word) {
		return word
	}

	if ok, res := matchAposSecond(word); ok {
		return res
	}

	if ok, res := matchMacMc(word); ok {
		return res
	}

	if ok, res := matchHonorific(word); ok {
		return res
	}

	if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
		return word
	}

	if smallWords[strings.ToLower(word)] {
		return strings.ToLower(word)
	}

	if allowRecursion {
		if strings.Contains(word, "/") && !strings.Contains(word, "//") {
			parts := strings.Split(word, "/")
			for i, p := range parts {
				parts[i] = TitlecaseLineInternal(p, false)
			}
			return strings.Join(parts, "/")
		}

		if strings.Contains(word, "-") {
			parts := strings.Split(word, "-")
			for i, p := range parts {
				parts[i] = TitlecaseLineInternal(p, false)
			}
			return strings.Join(parts, "-")
		}
	}

	if allCaps {
		word = strings.ToLower(word)
	}

	if isAllConsonants(word) && len(word) > 2 {
		return strings.ToUpper(word)
	}

	return capFirst(word)
}

func splitWordsAndSpaces(line string) ([]string, []string) {
	var words []string
	var spaces []string

	runes := []rune(line)
	n := len(runes)
	i := 0

	for i < n {
		start := i
		for i < n && !unicode.IsSpace(runes[i]) {
			i++
		}
		words = append(words, string(runes[start:i]))

		if i < n {
			sStart := i
			for i < n && unicode.IsSpace(runes[i]) {
				i++
			}
			spaces = append(spaces, string(runes[sStart:i]))
		}
	}

	return words, spaces
}

func capitalize(s string) string {
	runes := []rune(s)
	if len(runes) == 0 {
		return ""
	}
	runes[0] = unicode.ToUpper(runes[0])
	for i := 1; i < len(runes); i++ {
		runes[i] = unicode.ToLower(runes[i])
	}
	return string(runes)
}

func applySmallFirst(word string) string {
	runes := []rune(word)
	idx := 0
	for idx < len(runes) && punctRunes[runes[idx]] {
		idx++
	}
	punctPrefix := string(runes[:idx])
	rem := string(runes[idx:])

	for sw := range smallWords {
		if strings.HasPrefix(strings.ToLower(rem), sw) {
			swLen := len([]rune(sw))
			remRunes := []rune(rem)
			if len(remRunes) == swLen || !isWordChar(remRunes[swLen]) {
				capped := capitalize(sw)
				return punctPrefix + capped + string(remRunes[swLen:])
			}
		}
	}
	return word
}

func applySmallLast(word string) string {
	runes := []rune(word)
	if len(runes) == 0 {
		return word
	}

	lastIdx := len(runes) - 1
	var punctSuffix string
	coreRunes := runes
	if punctRunes[runes[lastIdx]] {
		punctSuffix = string(runes[lastIdx])
		coreRunes = runes[:lastIdx]
	}

	core := string(coreRunes)
	for sw := range smallWords {
		if strings.HasSuffix(strings.ToLower(core), sw) {
			swLen := len([]rune(sw))
			pos := len(coreRunes) - swLen
			if pos == 0 || !isWordChar(coreRunes[pos-1]) {
				matched := string(coreRunes[pos:]) + punctSuffix
				return string(coreRunes[:pos]) + capitalize(matched)
			}
		}
	}
	return word
}

var subphraseRegex = regexp.MustCompile(`([:.;?!\-–‒—―] )(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)`)

func applySubphrase(line string) string {
	return subphraseRegex.ReplaceAllStringFunc(line, func(match string) string {
		sub := subphraseRegex.FindStringSubmatch(match)
		if len(sub) == 3 {
			return sub[1] + capitalize(sub[2])
		}
		return match
	})
}

func TitlecaseLineInternal(line string, smallFirstLast bool) string {
	if line == "" {
		return ""
	}

	allCaps := (strings.ToUpper(line) == line)
	words, spaces := splitWordsAndSpaces(line)

	var tcWords []string
	for _, w := range words {
		tcWords = append(tcWords, TitlecaseWord(w, allCaps, true))
	}

	if smallFirstLast && len(tcWords) > 0 {
		tcWords[0] = applySmallFirst(tcWords[0])
		tcWords[len(tcWords)-1] = applySmallLast(tcWords[len(tcWords)-1])
	}

	var sb strings.Builder
	for i, w := range tcWords {
		sb.WriteString(w)
		if i < len(spaces) {
			sb.WriteString(spaces[i])
		}
	}

	return applySubphrase(sb.String())
}

func Titlecase(text string) string {
	lines := strings.Split(text, "\n")
	var res []string
	for _, l := range lines {
		res = append(res, TitlecaseLineInternal(l, true))
	}
	return strings.Join(res, "\n")
}
EOF

# 3. Generate main.go
cat << 'EOF' > main.go
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for {
		line, err := reader.ReadString('\n')
		if len(line) > 0 {
			trimmed := strings.TrimRight(line, "\r\n")
			result := Titlecase(trimmed)
			fmt.Fprintln(writer, result)
		}
		if err != nil {
			if err == io.EOF {
				break
			}
			fmt.Fprintf(os.Stderr, "Error reading stdin: %v\n", err)
			os.Exit(1)
		}
	}
}
EOF

# 4. Remove all Python files, caches, and leftover directories from repository
find . -name "*.py" -delete
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -rf *.egg-info titlecase

# 5. Verify Go build
go build ./...


