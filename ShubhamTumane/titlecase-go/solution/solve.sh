#!/bin/bash
set -euo pipefail

cd /workspace/repo

# 1. Initialize Go module
cat << 'EOF' > go.mod
module titlecase

go 1.22
EOF

# 2. Write Go implementation via python
python3 - << 'PYEOF'
code = r'''package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"os"
	"regexp"
	"strings"
	"unicode"
)

var (
	smallWords = map[string]bool{
		"a": true, "an": true, "and": true, "as": true, "at": true,
		"but": true, "by": true, "en": true, "for": true, "if": true,
		"in": true, "of": true, "on": true, "or": true, "the": true,
		"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
	}

	urlRegex     = regexp.MustCompile(`^(https?://|www\.)[^\s]+$`)
	macMcRegex   = regexp.MustCompile(`^([Mm]c|MC)(.+)`)
	mrMrsRegex   = regexp.MustCompile(`(?i)^((m((rs?)|s))|dr)$`)
	inlinePeriod = regexp.MustCompile(`[a-zA-Z]\.[a-zA-Z]`)
	ucInitials   = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
)

func isAllUpper(s string) bool {
	hasLetter := false
	for _, r := range s {
		if unicode.IsLetter(r) {
			hasLetter = true
			if !unicode.IsUpper(r) {
				return false
			}
		}
	}
	return hasLetter
}

func isAllConsonants(w string) bool {
	letters := ""
	for _, r := range w {
		if unicode.IsLetter(r) {
			letters += string(unicode.ToLower(r))
		}
	}
	if len(letters) <= 2 {
		return false
	}
	for _, r := range letters {
		if strings.ContainsRune("aeiouy", r) {
			return false
		}
	}
	return true
}

func capFirstLetter(s string) string {
	if urlRegex.MatchString(s) {
		return s
	}
	runes := []rune(s)
	for i, r := range runes {
		if unicode.IsLetter(r) {
			runes[i] = unicode.ToUpper(r)
			break
		}
	}
	return string(runes)
}

func hasInternalCap(s string) bool {
	runes := []rune(s)
	seenLower := false
	for _, r := range runes {
		if unicode.IsLower(r) {
			seenLower = true
		} else if seenLower && unicode.IsUpper(r) {
			return true
		}
	}
	return false
}

func isSmallWord(w string) bool {
	clean := strings.ToLower(strings.Trim(w, "!\"#$%&'()*+,-./:;?@[\\]^_`{|}~\u201c\u201d\u2018\u2019\u2013\u2014\u2015"))
	return smallWords[clean]
}

func titlecaseWord(word string, allCaps bool) string {
	if word == "" {
		return ""
	}

	// 1. URLs must remain completely untouched
	if urlRegex.MatchString(word) {
		return word
	}

	// 2. Acronyms / initials
	if allCaps && ucInitials.MatchString(word) {
		return word
	}

	// 3. Contractions: d', o', l'
	lower := strings.ToLower(word)
	if strings.HasPrefix(lower, "o'") || strings.HasPrefix(lower, "o\u2019") ||
		strings.HasPrefix(lower, "d'") || strings.HasPrefix(lower, "d\u2019") ||
		strings.HasPrefix(lower, "l'") || strings.HasPrefix(lower, "l\u2019") {
		runes := []rune(word)
		if len(runes) >= 3 {
			first := unicode.ToLower(runes[0])
			if strings.ContainsRune("aeiou", first) {
				first = unicode.ToUpper(first)
			}
			runes[0] = first
			runes[2] = unicode.ToUpper(runes[2])
			return string(runes)
		}
	}

	// 4. Mc / Mac
	if m := macMcRegex.FindStringSubmatch(word); m != nil {
		prefix := capFirstLetter(strings.ToLower(m[1]))
		return prefix + titlecaseText(m[2])
	}

	// 5. Mr / Mrs / Ms / Dr
	if mrMrsRegex.MatchString(word) {
		return capFirstLetter(strings.ToLower(word))
	}

	// 6. Inline period (e.g. domain.com) or internal uppercase (e.g. iPhone)
	if inlinePeriod.MatchString(word) || (!allCaps && hasInternalCap(word)) {
		return word
	}

	// 7. Small words
	if isSmallWord(word) {
		return strings.ToLower(word)
	}

	// 8. Slashes (only if not a URL / protocol)
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, p := range parts {
			parts[i] = titlecaseWord(p, allCaps)
		}
		return strings.Join(parts, "/")
	}

	// 9. Hyphens
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts {
			parts[i] = titlecaseWord(p, allCaps)
		}
		return strings.Join(parts, "-")
	}

	if allCaps {
		word = strings.ToLower(word)
	}

	if isAllConsonants(word) {
		return strings.ToUpper(word)
	}

	return capFirstLetter(word)
}

func titlecaseLine(line string) string {
	if line == "" {
		return ""
	}

	allCaps := isAllUpper(line)

	var tokens []string
	var isSpace []bool
	runes := []rune(line)
	n := len(runes)
	i := 0
	for i < n {
		start := i
		if unicode.IsSpace(runes[i]) {
			for i < n && unicode.IsSpace(runes[i]) {
				i++
			}
			tokens = append(tokens, string(runes[start:i]))
			isSpace = append(isSpace, true)
		} else {
			for i < n && !unicode.IsSpace(runes[i]) {
				i++
			}
			tokens = append(tokens, string(runes[start:i]))
			isSpace = append(isSpace, false)
		}
	}

	var wordsIndices []int
	for idx, sp := range isSpace {
		if !sp {
			wordsIndices = append(wordsIndices, idx)
		}
	}

	for _, wIdx := range wordsIndices {
		tokens[wIdx] = titlecaseWord(tokens[wIdx], allCaps)
	}

	// Capitalize boundary words (unless they are URLs)
	if len(wordsIndices) > 0 {
		firstIdx := wordsIndices[0]
		if !urlRegex.MatchString(tokens[firstIdx]) {
			tokens[firstIdx] = capFirstLetter(tokens[firstIdx])
		}

		lastIdx := wordsIndices[len(wordsIndices)-1]
		if !urlRegex.MatchString(tokens[lastIdx]) {
			tokens[lastIdx] = capFirstLetter(tokens[lastIdx])
		}
	}

	// Subphrase rule
	for idx := 1; idx < len(wordsIndices); idx++ {
		prevWordIdx := wordsIndices[idx-1]
		currWordIdx := wordsIndices[idx]
		prevWord := tokens[prevWordIdx]

		if strings.HasSuffix(prevWord, ":") || strings.HasSuffix(prevWord, ";") ||
			strings.HasSuffix(prevWord, ".") || strings.HasSuffix(prevWord, "!") ||
			strings.HasSuffix(prevWord, "?") || strings.HasSuffix(prevWord, "-") ||
			strings.HasSuffix(prevWord, "\u2013") || strings.HasSuffix(prevWord, "\u2014") ||
			strings.HasSuffix(prevWord, "\u2015") {
			if !urlRegex.MatchString(tokens[currWordIdx]) {
				tokens[currWordIdx] = capFirstLetter(tokens[currWordIdx])
			}
		}
	}

	return strings.Join(tokens, "")
}

func titlecaseText(text string) string {
	lines := strings.Split(text, "\n")
	for i, l := range lines {
		trimmed := strings.TrimRight(l, "\r")
		lines[i] = titlecaseLine(trimmed)
	}
	return strings.Join(lines, "\n")
}

func main() {
	inputFile := flag.String("f", "", "File to read from")
	flag.String("input-file", "", "File to read from")
	outputFile := flag.String("o", "", "File to write to")
	flag.String("output-file", "", "File to write to")
	flag.String("w", "", "Wordlist")
	flag.String("wordlist", "", "Wordlist")
	flag.Bool("preserve-blank-lines", false, "Preserve blank lines")
	flag.Parse()

	var reader io.Reader = os.Stdin
	if *inputFile != "" && *inputFile != "-" {
		f, err := os.Open(*inputFile)
		if err == nil {
			defer f.Close()
			reader = f
		}
	}

	var writer io.Writer = os.Stdout
	if *outputFile != "" && *outputFile != "-" {
		f, err := os.Create(*outputFile)
		if err == nil {
			defer f.Close()
			writer = f
		}
	}

	args := flag.Args()
	if len(args) > 0 {
		out := titlecaseText(strings.Join(args, " "))
		fmt.Fprintln(writer, out)
		return
	}

	scanner := bufio.NewScanner(reader)
	first := true
	for scanner.Scan() {
		if !first {
			fmt.Fprintln(writer)
		}
		first = false
		fmt.Fprint(writer, titlecaseLine(scanner.Text()))
	}
	fmt.Fprintln(writer)
}
'''
with open("main.go", "w", encoding="utf-8") as f:
    f.write(code)
PYEOF

# 3. Clean python files
find . -name "*.py" -type f -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf tox.ini pyproject.toml setup.cfg setup.py

echo "Oracle solve completed successfully."