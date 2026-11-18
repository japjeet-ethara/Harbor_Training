#!/bin/bash
set -euo pipefail

WORKSPACE="/workspace/repo"
cd "$WORKSPACE"

# ─── Delete all Python files ───
find . -name "*.py" -delete
find . -name "*.pyc" -delete
rm -rf __pycache__ titlecase/__pycache__ titlecase.egg-info .eggs
rm -f setup.cfg MANIFEST.in pytest.ini tox.ini .travis.yml

# ─── Create Go module ───
go mod init titlecase-go

# ─── Write the Go titlecase implementation ───
cat > main.go << 'GOEOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
)

// Regex definitions matching python-titlecase rules without unsupported look-ahead/behind
var (
	// Small words list
	smallWordsRegex = regexp.MustCompile(`^(?i:a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)$`)

	// Small first word regex
	smallFirstRegex = regexp.MustCompile(`^(?i:([!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}\~]*)(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)\b)`)

	// Small last word regex
	smallLastRegex = regexp.MustCompile(`(?i:\b(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)[!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}\~]?)$`)

	// Subphrase punctuation followed by space and small word
	subphraseRegex = regexp.MustCompile(`([:.;?!\-–‒—―] )(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)`)

	// Mc/Mac names
	macMcRegex = regexp.MustCompile(`^([Mm]c|MC)(\w.+)`)

	// Honorifics
	mrMrsMsDrRegex = regexp.MustCompile(`^(?i:(m((rs?)|s))|Dr)$`)

	// Inline period: letter.letter
	inlinePeriodRegex = regexp.MustCompile(`(?i:\p{L}\.\p{L})`)

	// Uppercase elsewhere (e.g. iPhone)
	ucElsewhereRegex = regexp.MustCompile(`^[!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}\~]*\p{L}+\p{Lu}`)

	// Capitalize first letter (skipping leading punctuation)
	capfirstRegex = regexp.MustCompile(`^([!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}\~]*?)(\p{L})`)

	// Apostrophe second (e.g. d'Artagnan, O'Brien)
	aposSecondRegex = regexp.MustCompile(`^(?i:[dol]['‘]\p{L}+(?:['’]s)?)$`)

	// UC initials (e.g. A.B. or A.B.C.)
	ucInitialsRegex = regexp.MustCompile(`^(?:(?:\p{Lu}\.|\p{Lu}\.\p{Lu}))+$`)

	// All consonants > 2 characters
	allConsonantsRegex = regexp.MustCompile(`^(?i:[bcdfghjklmnpqrstvwxz]+)$`)
)

func capitalize(s string) string {
	if s == "" {
		return ""
	}
	runes := []rune(s)
	runes[0] = unicode.ToUpper(runes[0])
	for i := 1; i < len(runes); i++ {
		runes[i] = unicode.ToLower(runes[i])
	}
	return string(runes)
}

func titlecase(text string, smallFirstLast bool) string {
	lines := strings.Split(text, "\n")
	var processed []string

	for _, line := range lines {
		allCaps := strings.ToUpper(line) == line

		var pWords []string
		var pSpaces []string

		runes := []rune(line)
		n := len(runes)
		pos := 0
		expectWord := true

		for pos < n {
			if expectWord {
				if unicode.IsSpace(runes[pos]) {
					pWords = append(pWords, "")
					expectWord = false
				} else {
					start := pos
					for pos < n && !unicode.IsSpace(runes[pos]) {
						pos++
					}
					pWords = append(pWords, string(runes[start:pos]))
					expectWord = false
				}
			} else {
				start := pos
				pos++
				pSpaces = append(pSpaces, string(runes[start:pos]))
				expectWord = true
			}
		}
		if expectWord {
			pWords = append(pWords, "")
		}

		tcLine := make([]string, len(pWords))

		for wi, word := range pWords {
			if word == "" {
				tcLine[wi] = ""
				continue
			}

			if allCaps {
				if ucInitialsRegex.MatchString(word) {
					tcLine[wi] = word
					continue
				}
			}

			if aposSecondRegex.MatchString(word) {
				wRunes := []rune(word)
				first := wRunes[0]
				isVowel := strings.ContainsRune("aeiouAEIOU", first)
				if !isVowel {
					wRunes[0] = unicode.ToLower(wRunes[0])
				} else {
					wRunes[0] = unicode.ToUpper(wRunes[0])
				}
				wRunes[2] = unicode.ToUpper(wRunes[2])
				tcLine[wi] = string(wRunes)
				continue
			}

			if m := macMcRegex.FindStringSubmatch(word); m != nil {
				prefix := capitalize(m[1])
				rest := titlecase(m[2], true)
				tcLine[wi] = prefix + rest
				continue
			}

			if mrMrsMsDrRegex.MatchString(word) {
				wRunes := []rune(word)
				wRunes[0] = unicode.ToUpper(wRunes[0])
				tcLine[wi] = string(wRunes)
				continue
			}

			if inlinePeriodRegex.MatchString(word) || (!allCaps && ucElsewhereRegex.MatchString(word)) {
				tcLine[wi] = word
				continue
			}

			if smallWordsRegex.MatchString(word) {
				tcLine[wi] = strings.ToLower(word)
				continue
			}

			if strings.Contains(word, "/") && !strings.Contains(word, "//") {
				parts := strings.Split(word, "/")
				for pi, p := range parts {
					parts[pi] = titlecase(p, false)
				}
				tcLine[wi] = strings.Join(parts, "/")
				continue
			}

			if strings.Contains(word, "-") {
				parts := strings.Split(word, "-")
				for pi, p := range parts {
					parts[pi] = titlecase(p, false)
				}
				tcLine[wi] = strings.Join(parts, "-")
				continue
			}

			if allCaps {
				word = strings.ToLower(word)
			}

			if len(word) > 2 && allConsonantsRegex.MatchString(word) {
				tcLine[wi] = strings.ToUpper(word)
				continue
			}

			tcLine[wi] = capfirstRegex.ReplaceAllStringFunc(word, func(m string) string {
				return strings.ToUpper(m)
			})
		}

		if smallFirstLast && len(tcLine) > 0 {
			tcLine[0] = smallFirstRegex.ReplaceAllStringFunc(tcLine[0], func(m string) string {
				sub := smallFirstRegex.FindStringSubmatch(m)
				if len(sub) >= 3 {
					return sub[1] + capitalize(sub[2])
				}
				return m
			})

			lastIdx := len(tcLine) - 1
			tcLine[lastIdx] = smallLastRegex.ReplaceAllStringFunc(tcLine[lastIdx], func(m string) string {
				return capitalize(m)
			})
		}

		var sb strings.Builder
		for idx, w := range tcLine {
			sb.WriteString(w)
			if idx < len(pSpaces) {
				sb.WriteString(pSpaces[idx])
			}
		}
		res := sb.String()

		res = subphraseRegex.ReplaceAllStringFunc(res, func(m string) string {
			sub := subphraseRegex.FindStringSubmatch(m)
			if len(sub) >= 3 {
				return sub[1] + capitalize(sub[2])
			}
			return m
		})

		processed = append(processed, res)
	}

	return strings.Join(processed, "\n")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	buf := make([]byte, 0, 1024*1024)
	scanner.Buffer(buf, 1024*1024)

	for scanner.Scan() {
		line := scanner.Text()
		fmt.Println(titlecase(line, true))
	}
}
GOEOF

echo "Building Go module..."
go build -o titlecase-go .
echo "Build complete."
