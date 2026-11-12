#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Remove all Python files and empty python package directory
find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase

cat << 'EOF' > /workspace/repo/go.mod
module titlecase-go

go 1.23
EOF

cat << 'EOF' > /workspace/repo/main.go
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"regexp"
	"strings"
	"unicode"
	"unicode/utf8"
)

var smallList = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
	"in", "of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

var smallSet = func() map[string]bool {
	m := make(map[string]bool, len(smallList))
	for _, s := range smallList {
		m[s] = true
	}
	return m
}()

var ucInitialsRe = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)

const punctRunes = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
const subphrasePunct = ":.;?!-–‒—―"
const consonantChars = "bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ"

func isPunct(r rune) bool {
	return strings.ContainsRune(punctRunes, r)
}

func isSubphrasePunct(r rune) bool {
	return strings.ContainsRune(subphrasePunct, r)
}

func isPyWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isAposOrS(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func pyCapitalize(s string) string {
	if s == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	return strings.ToUpper(string(r)) + strings.ToLower(s[size:])
}

func matchAposSecond(word string) (string, bool) {
	runes := []rune(word)
	if len(runes) < 3 {
		return "", false
	}
	r0 := unicode.ToLower(runes[0])
	if r0 != 'd' && r0 != 'o' && r0 != 'l' {
		return "", false
	}
	if runes[1] != '\'' && runes[1] != '‘' {
		return "", false
	}
	tail := runes[2:]
	allWord := func(rs []rune) bool {
		if len(rs) == 0 {
			return false
		}
		for _, r := range rs {
			if !isPyWord(r) {
				return false
			}
		}
		return true
	}
	valid := allWord(tail)
	if !valid && len(tail) >= 3 && isAposOrS(tail[len(tail)-1]) && isAposOrS(tail[len(tail)-2]) {
		valid = allWord(tail[:len(tail)-2])
	}
	if !valid {
		return "", false
	}
	var first string
	if r0 == 'o' {
		first = strings.ToUpper(string(runes[0]))
	} else {
		first = strings.ToLower(string(runes[0]))
	}
	third := strings.ToUpper(string(runes[2]))
	return first + string(runes[1]) + third + string(runes[3:]), true
}

func matchMacMc(word string) (string, bool) {
	runes := []rune(word)
	if len(runes) < 4 {
		return "", false
	}
	prefix := string(runes[:2])
	if prefix != "mc" && prefix != "Mc" && prefix != "MC" {
		return "", false
	}
	if !isPyWord(runes[2]) {
		return "", false
	}
	return "Mc" + titlecase(string(runes[2:]), true), true
}

func matchHonorific(word string) (string, bool) {
	low := strings.ToLower(word)
	if low != "mr" && low != "mrs" && low != "ms" && low != "dr" {
		return "", false
	}
	runes := []rune(word)
	return strings.ToUpper(string(runes[0])) + string(runes[1:]), true
}

func hasInlinePeriod(word string) bool {
	runes := []rune(word)
	for i := 1; i+1 < len(runes); i++ {
		if runes[i] == '.' && isPyWord(runes[i-1]) && isPyWord(runes[i+1]) {
			return true
		}
	}
	return false
}

func hasUCElsewhere(word string) bool {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	count := 0
	hasUpperAfterFirst := false
	for i < len(runes) && isASCIILetter(runes[i]) {
		if count >= 1 && runes[i] >= 'A' && runes[i] <= 'Z' {
			hasUpperAfterFirst = true
		}
		count++
		i++
	}
	return count >= 2 && hasUpperAfterFirst
}

func isAllConsonants(word string) bool {
	runes := []rune(word)
	if len(runes) <= 2 {
		return false
	}
	for _, r := range runes {
		if !strings.ContainsRune(consonantChars, r) {
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	if i < len(runes) && isPyWord(runes[i]) {
		return strings.ToUpper(string(runes[:i+1])) + string(runes[i+1:])
	}
	return word
}

func applySmallFirst(word string) string {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	for _, sw := range smallList {
		swRunes := []rune(sw)
		if len(runes)-i < len(swRunes) {
			continue
		}
		end := i + len(swRunes)
		if strings.ToLower(string(runes[i:end])) != sw {
			continue
		}
		lastIsWord := isPyWord(runes[end-1])
		nextIsWord := end < len(runes) && isPyWord(runes[end])
		if lastIsWord != nextIsWord {
			return string(runes[:i]) + pyCapitalize(string(runes[i:end])) + string(runes[end:])
		}
	}
	return word
}

func applySmallLast(word string) string {
	runes := []rune(word)
	if len(runes) == 0 {
		return word
	}
	ends := []int{len(runes)}
	if isPunct(runes[len(runes)-1]) {
		ends = append(ends, len(runes)-1)
	}
	for _, end := range ends {
		for _, sw := range smallList {
			swRunes := []rune(sw)
			start := end - len(swRunes)
			if start < 0 {
				continue
			}
			if strings.ToLower(string(runes[start:end])) != sw {
				continue
			}
			if start == 0 || !isPyWord(runes[start-1]) {
				return string(runes[:start]) + pyCapitalize(string(runes[start:]))
			}
		}
	}
	return word
}

func applySubphrase(line string) string {
	runes := []rune(line)
	var out strings.Builder
	i := 0
	for i < len(runes) {
		if i+2 < len(runes) && isSubphrasePunct(runes[i]) && runes[i+1] == ' ' {
			matched := false
			for _, sw := range smallList {
				swRunes := []rune(sw)
				if i+2+len(swRunes) <= len(runes) && string(runes[i+2:i+2+len(swRunes)]) == sw {
					out.WriteRune(runes[i])
					out.WriteRune(' ')
					out.WriteString(pyCapitalize(sw))
					i += 2 + len(swRunes)
					matched = true
					break
				}
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

func titlecase(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line

	var words []string
	var spaces []string
	var cur strings.Builder
	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, cur.String())
			cur.Reset()
			spaces = append(spaces, string(r))
		} else {
			cur.WriteRune(r)
		}
	}
	words = append(words, cur.String())

	tcLine := make([]string, 0, len(words))
	for _, word := range words {
		if allCaps && ucInitialsRe.MatchString(word) {
			tcLine = append(tcLine, word)
			continue
		}
		if res, ok := matchAposSecond(word); ok {
			tcLine = append(tcLine, res)
			continue
		}
		if res, ok := matchMacMc(word); ok {
			tcLine = append(tcLine, res)
			continue
		}
		if res, ok := matchHonorific(word); ok {
			tcLine = append(tcLine, res)
			continue
		}
		if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
			tcLine = append(tcLine, word)
			continue
		}
		if smallSet[strings.ToLower(word)] {
			tcLine = append(tcLine, strings.ToLower(word))
			continue
		}
		if strings.Contains(word, "/") && !strings.Contains(word, "//") {
			parts := strings.Split(word, "/")
			for idx, p := range parts {
				parts[idx] = titlecase(p, false)
			}
			tcLine = append(tcLine, strings.Join(parts, "/"))
			continue
		}
		if strings.Contains(word, "-") {
			parts := strings.Split(word, "-")
			for idx, p := range parts {
				parts[idx] = titlecase(p, false)
			}
			tcLine = append(tcLine, strings.Join(parts, "-"))
			continue
		}
		if allCaps {
			word = strings.ToLower(word)
		}
		if isAllConsonants(word) {
			tcLine = append(tcLine, strings.ToUpper(word))
			continue
		}
		tcLine = append(tcLine, capFirst(word))
	}

	if smallFirstLast && len(tcLine) > 0 {
		tcLine[0] = applySmallFirst(tcLine[0])
		tcLine[len(tcLine)-1] = applySmallLast(tcLine[len(tcLine)-1])
	}

	var joined strings.Builder
	for i := range tcLine {
		joined.WriteString(tcLine[i])
		if i < len(spaces) {
			joined.WriteString(spaces[i])
		}
	}
	return applySubphrase(joined.String())
}

func main() {
	reader := bufio.NewReader(os.Stdin)
	for {
		line, err := reader.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimRight(line, "\r\n")
			fmt.Println(titlecase(line, true))
		}
		if err != nil {
			if err == io.EOF {
				break
			}
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
}
EOF

go build ./...
