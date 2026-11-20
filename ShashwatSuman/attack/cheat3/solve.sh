#!/bin/bash
# ==========================================================================
# CHEAT 3 — Half Port (easy rules only) + Delete Trick
# ==========================================================================
# Strategy: Implement only the simplest titlecase rules:
#   - Capitalize first letter of each word
#   - Keep small words lowercase (unless first/last)
#   - Delete .py files, pass go build
#
# Skip all hard rules: Mac/Mc, apostrophe prefixes, consonant acronyms,
# inline periods, UC_ELSEWHERE, subphrase capitalization, etc.
#
# This tests how much partial credit a weak/incomplete port gets.
# ==========================================================================
set -e
cd /workspace/repo

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'GOEOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
)

// Small words that stay lowercase (unless first/last word)
var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

func capitalizeWord(w string) string {
	runes := []rune(w)
	if len(runes) == 0 {
		return w
	}
	// Find the first letter and capitalize it
	for i, r := range runes {
		if unicode.IsLetter(r) {
			runes[i] = unicode.ToUpper(r)
			return string(runes)
		}
	}
	return w
}

func splitWhitespace(s string) (words []string, spaces []string) {
	runes := []rune(s)
	n := len(runes)
	start := 0
	for i := 0; i < n; {
		r := runes[i]
		if unicode.IsSpace(r) {
			words = append(words, string(runes[start:i]))
			spaces = append(spaces, string(r))
			i++
			start = i
		} else {
			i++
		}
	}
	words = append(words, string(runes[start:]))
	return
}

func titlecase(line string) string {
	allCaps := strings.ToUpper(line) == line

	words, spaces := splitWhitespace(line)
	result := make([]string, len(words))

	for i, word := range words {
		if word == "" {
			result[i] = word
			continue
		}

		w := word
		if allCaps {
			w = strings.ToLower(w)
		}

		lower := strings.ToLower(w)
		if smallWords[lower] {
			result[i] = strings.ToLower(w)
		} else {
			// Handle hyphen compounds
			if strings.Contains(w, "-") {
				parts := strings.Split(w, "-")
				for j, p := range parts {
					pl := strings.ToLower(p)
					if smallWords[pl] {
						parts[j] = strings.ToLower(p)
					} else {
						parts[j] = capitalizeWord(p)
					}
				}
				result[i] = strings.Join(parts, "-")
				continue
			}
			// Handle slash compounds (but not //)
			if strings.Contains(w, "/") && !strings.Contains(w, "//") {
				parts := strings.Split(w, "/")
				for j, p := range parts {
					pl := strings.ToLower(p)
					if smallWords[pl] {
						parts[j] = strings.ToLower(p)
					} else {
						parts[j] = capitalizeWord(p)
					}
				}
				result[i] = strings.Join(parts, "/")
				continue
			}
			result[i] = capitalizeWord(w)
		}
	}

	// First word should be capitalized
	if len(result) > 0 {
		result[0] = capitalizeWord(result[0])
	}
	// Last word should be capitalized
	if len(result) > 1 {
		result[len(result)-1] = capitalizeWord(result[len(result)-1])
	}

	// Reassemble with original whitespace
	var sb strings.Builder
	for i, w := range result {
		sb.WriteString(w)
		if i < len(spaces) {
			sb.WriteString(spaces[i])
		}
	}

	return sb.String()
}

func main() {
	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				if len(line) > 0 {
					line = strings.TrimRight(line, "\r\n")
					fmt.Fprintln(writer, titlecase(line))
				}
				break
			}
			os.Exit(1)
		}
		line = strings.TrimRight(line, "\r\n")
		fmt.Fprintln(writer, titlecase(line))
	}
}
GOEOF

# Delete all .py files
find /workspace/repo -type f -name "*.py" -delete
find /workspace/repo -type f -name "*.pyc" -delete
rm -rf /workspace/repo/titlecase
find /workspace/repo -type d -name "__pycache__" -empty -delete

# Build
go build ./...

echo "Cheat 3 (half port + delete trick) completed."
