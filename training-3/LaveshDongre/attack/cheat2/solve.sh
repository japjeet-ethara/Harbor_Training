#!/bin/bash
set -euo pipefail

mkdir -p /workspace/repo

cat > /workspace/repo/go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > /workspace/repo/main.go <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"unicode"
)

var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true,
	"vs.": true,
}

func capitalizeWord(word string) string {
	runes := []rune(word)
	for i, r := range runes {
		if unicode.IsLetter(r) {
			runes[i] = unicode.ToUpper(r)
			break
		}
	}
	return string(runes)
}

func titleLine(line string) string {
	parts := splitLine(line)
	allCaps := strings.ToUpper(line) == line
	wordIndexes := make([]int, 0, len(parts))
	for i := range parts {
		if parts[i].word {
			wordIndexes = append(wordIndexes, i)
		}
	}

	for position, index := range wordIndexes {
		word := parts[index].text
		prefix, core, suffix := peelPunctuation(word)
		lower := strings.ToLower(core)
		edge := position == 0 || position == len(wordIndexes)-1
		afterSubphrase := position > 0 &&
			parts[index-1].text == " " &&
			index >= 2 && hasSubphrasePunctuation(parts[index-2].text)
		apostrophe, isApostrophe := apostropheName(core, allCaps)
		mac, rest, isMac := macPrefix(core)

		switch {
		case allCaps && isInitialism(core):
		case hasInlinePeriod(core):
		case isApostrophe:
			core = apostrophe
		case isMac:
			if allCaps {
				rest = strings.ToLower(rest)
			}
			core = mac + capitalizeWord(rest)
		case !allCaps && hasInternalCapital(core):
		case isHonorific(lower):
			core = capitalizeWord(lower)
		case isSmallWord(lower):
			if edge || afterSubphrase {
				core = capitalizeWord(lower)
			} else {
				core = lower
			}
		case strings.Contains(core, "/") && !strings.Contains(core, "//"):
			core = titlePieces(core, "/", allCaps)
		case strings.Contains(core, "-"):
			core = titlePieces(core, "-", allCaps)
		case isConsonantWord(core):
			core = strings.ToUpper(core)
		default:
			if allCaps {
				core = strings.ToLower(core)
			}
			core = capitalizeWord(core)
		}
		parts[index].text = prefix + core + suffix
	}

	var result strings.Builder
	for _, part := range parts {
		result.WriteString(part.text)
	}
	return result.String()
}

type linePart struct {
	text string
	word bool
}

func splitLine(line string) []linePart {
	var parts []linePart
	var current strings.Builder
	word := false
	for _, r := range line {
		isSpace := unicode.IsSpace(r)
		if word && isSpace {
			parts = append(parts, linePart{text: current.String(), word: true})
			current.Reset()
			word = false
		} else if !word && !isSpace && current.Len() > 0 {
			parts = append(parts, linePart{text: current.String()})
			current.Reset()
		}
		current.WriteRune(r)
		if isSpace {
			parts = append(parts, linePart{text: current.String()})
			current.Reset()
		} else {
			word = true
		}
	}
	if current.Len() > 0 {
		parts = append(parts, linePart{text: current.String(), word: word})
	}
	return parts
}

func peelPunctuation(word string) (prefix, core, suffix string) {
	runes := []rune(word)
	start, end := 0, len(runes)
	for start < end && unicode.IsPunct(runes[start]) {
		start++
	}
	for end > start && unicode.IsPunct(runes[end-1]) {
		end--
	}
	return string(runes[:start]), string(runes[start:end]), string(runes[end:])
}

func titlePieces(word, separator string, allCaps bool) string {
	pieces := strings.Split(word, separator)
	for i, piece := range pieces {
		pieces[i] = titlePiece(piece, allCaps)
	}
	return strings.Join(pieces, separator)
}

func titlePiece(word string, allCaps bool) string {
	if allCaps {
		word = strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		return titlePieces(word, "/", false)
	}
	if strings.Contains(word, "-") {
		return titlePieces(word, "-", false)
	}
	if isSmallWord(strings.ToLower(word)) {
		return strings.ToLower(word)
	}
	if apostrophe, ok := apostropheName(word, allCaps); ok {
		return apostrophe
	}
	if prefix, rest, ok := macPrefix(word); ok {
		return prefix + capitalizeWord(rest)
	}
	if isHonorific(strings.ToLower(word)) {
		return capitalizeWord(strings.ToLower(word))
	}
	if isConsonantWord(word) {
		return strings.ToUpper(word)
	}
	return capitalizeWord(word)
}

func hasInlinePeriod(word string) bool {
	runes := []rune(word)
	for i := 1; i+1 < len(runes); i++ {
		if unicode.IsLetter(runes[i-1]) && runes[i] == '.' && unicode.IsLetter(runes[i+1]) {
			return true
		}
	}
	return false
}

func hasInternalCapital(word string) bool {
	runes := []rune(word)
	seenLetter := false
	for _, r := range runes {
		if unicode.IsLetter(r) {
			if seenLetter && unicode.IsUpper(r) {
				return true
			}
			seenLetter = true
		}
	}
	return false
}

func isInitialism(word string) bool {
	runes := []rune(word)
	if len(runes) < 3 {
		return false
	}
	for i, r := range runes {
		if i%2 == 0 {
			if !unicode.IsUpper(r) || !unicode.IsLetter(r) {
				return false
			}
		} else if r != '.' {
			return false
		}
	}
	return true
}

func isHonorific(word string) bool {
	switch word {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func apostropheName(word string, allCaps bool) (string, bool) {
	runes := []rune(word)
	if len(runes) < 3 || (runes[1] != '\'' && runes[1] != '\u2018') {
		return "", false
	}
	prefix := unicode.ToLower(runes[0])
	switch prefix {
	case 'd', 'o', 'l':
	default:
		return "", false
	}
	if allCaps {
		for i := 2; i < len(runes); i++ {
			runes[i] = unicode.ToLower(runes[i])
		}
	}
	runes[0] = prefix
	if prefix == 'o' {
		runes[0] = 'O'
	}
	for i := 2; i < len(runes); i++ {
		if unicode.IsLetter(runes[i]) {
			runes[i] = unicode.ToUpper(runes[i])
			return string(runes), true
		}
	}
	return "", false
}

func macPrefix(word string) (string, string, bool) {
	runes := []rune(word)
	if len(runes) < 4 || !((runes[0] == 'M' || runes[0] == 'm') && (runes[1] == 'c' || runes[1] == 'C')) {
		return "", "", false
	}
	return "Mc", string(runes[2:]), true
}

func isConsonantWord(word string) bool {
	runes := []rune(word)
	if len(runes) <= 2 {
		return false
	}
	for _, r := range runes {
		if !unicode.IsLetter(r) {
			return false
		}
		switch unicode.ToLower(r) {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

func isSmallWord(word string) bool {
	return smallWords[word]
}

func hasSubphrasePunctuation(word string) bool {
	runes := []rune(word)
	if len(runes) == 0 {
		return false
	}
	switch runes[len(runes)-1] {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		fmt.Fprintln(writer, titleLine(scanner.Text()))
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
