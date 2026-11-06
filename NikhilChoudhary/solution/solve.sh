#!/bin/bash
set -e

cd /workspace/repo

# 1. Delete all Python files and the old python package directory
find /workspace/repo -name "*.py" -type f -delete
rm -rf /workspace/repo/titlecase

# 2. Initialize Go module if not present
if [ ! -f go.mod ]; then
    go mod init titlecase
fi

# 3. Write Go implementation
cat << 'EOF' > main.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
)

const punctRunes = "!\"#$%&'()*+,-./:;?@[\\]^_`{|}~\u201c\u2018\u2019\u2013\u2012\u2014\u2015"

var smallList = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to", "v.", "via", "vs.", "vs", "v",
}

var (
	smallWordsRegex = regexp.MustCompile(`^(?i:a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)$`)
	subphraseRegex  = regexp.MustCompile("([:.;?!\\-\u2013\u2012\u2014\u2015] )(?i:a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\\.?|via|vs\\.?)")
	macMcRegex      = regexp.MustCompile(`^(?i:mc)(\w.+)$`)
	mrMrsMsDrRegex  = regexp.MustCompile(`^(?i:(m(rs?|s))|dr)$`)
	inlinePeriod    = regexp.MustCompile(`(?i:\p{L}\.\p{L})`)
	ucInitialsRegex = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
)

func isPunct(r rune) bool {
	return strings.ContainsRune(punctRunes, r)
}

func isWordChar(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

func isAllConsoants(word string) bool {
	if len(word) <= 2 {
		return false
	}
	consonants := "bcdfghjklmnpqrstvwxz"
	for _, r := range strings.ToLower(word) {
		if !strings.ContainsRune(consonants, r) {
			return false
		}
	}
	return true
}

func matchesAposSecond(word string) (matched bool, prefix rune, apos rune, rest string) {
	// APOS_SECOND = ^[dol]['‘][\p{Letter}]+(?:['s]{2})?$ (case-insensitive)
	runes := []rune(word)
	if len(runes) < 3 {
		return false, 0, 0, ""
	}
	first := unicode.ToLower(runes[0])
	if first != 'd' && first != 'o' && first != 'l' {
		return false, 0, 0, ""
	}
	second := runes[1]
	if second != '\'' && second != '\u2018' && second != '\u2019' {
		return false, 0, 0, ""
	}
	rem := string(runes[2:])
	remRunes := []rune(rem)
	n := len(remRunes)
	if n >= 2 {
		last2_0 := remRunes[n-2]
		last2_1 := unicode.ToLower(remRunes[n-1])
		if (last2_0 == '\'' || last2_0 == '\u2018' || last2_0 == '\u2019') && (last2_1 == 's') {
			if n-2 == 0 {
				return false, 0, 0, ""
			}
			for _, r := range remRunes[:n-2] {
				if !unicode.IsLetter(r) {
					return false, 0, 0, ""
				}
			}
			return true, runes[0], second, rem
		}
	}
	for _, r := range remRunes {
		if !unicode.IsLetter(r) {
			return false, 0, 0, ""
		}
	}
	return true, runes[0], second, rem
}

func hasUcElsewhere(word string) bool {
	// UC_ELSEWHERE = ^[%s]*?[\p{Letter}]+[\p{Uppercase_Letter}]+?
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	if i >= len(runes) || !unicode.IsLetter(runes[i]) {
		return false
	}
	for j := i + 1; j < len(runes); j++ {
		if unicode.IsUpper(runes[j]) {
			return true
		}
	}
	return false
}

func capFirst(word string) string {
	// CAPFIRST = ^[%s]*?([\p{Letter}])
	runes := []rune(word)
	for i, r := range runes {
		if isPunct(r) {
			continue
		}
		if unicode.IsLetter(r) {
			runes[i] = unicode.ToUpper(r)
			return string(runes)
		}
		break
	}
	return word
}

func capitalizeWord(s string) string {
	if len(s) == 0 {
		return s
	}
	runes := []rune(s)
	runes[0] = unicode.ToUpper(runes[0])
	for i := 1; i < len(runes); i++ {
		runes[i] = unicode.ToLower(runes[i])
	}
	return string(runes)
}

func matchSmallFirst(word string) (lead string, small string, rest string, matched bool) {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	lead = string(runes[:i])
	rem := string(runes[i:])
	remLower := strings.ToLower(rem)

	for _, sw := range smallList {
		if strings.HasPrefix(remLower, sw) {
			after := rem[len(sw):]
			if len(after) == 0 {
				return lead, rem[:len(sw)], after, true
			}
			firstAfter := []rune(after)[0]
			if !isWordChar(firstAfter) {
				return lead, rem[:len(sw)], after, true
			}
		}
	}
	return "", "", "", false
}

func matchSmallLast(word string) (before string, matchStr string, matched bool) {
	runes := []rune(word)
	n := len(runes)
	if n == 0 {
		return "", "", false
	}

	trailPunct := ""
	coreRunes := runes
	if isPunct(runes[n-1]) {
		trailPunct = string(runes[n-1])
		coreRunes = runes[:n-1]
	}
	core := string(coreRunes)
	coreLower := strings.ToLower(core)

	for _, sw := range smallList {
		if strings.HasSuffix(coreLower, sw) {
			before := core[:len(core)-len(sw)]
			if len(before) == 0 {
				return "", core[len(core)-len(sw):] + trailPunct, true
			}
			lastBefore := []rune(before)[len([]rune(before))-1]
			if !isWordChar(lastBefore) {
				return before, core[len(core)-len(sw):] + trailPunct, true
			}
		}
	}
	return "", "", false
}

func splitSpaces(s string) (words []string, spaces []string) {
	var curWord strings.Builder
	var curSpace strings.Builder
	inSpace := false

	for _, r := range s {
		if unicode.IsSpace(r) {
			if !inSpace {
				words = append(words, curWord.String())
				curWord.Reset()
				inSpace = true
			}
			curSpace.WriteRune(r)
		} else {
			if inSpace {
				spaces = append(spaces, curSpace.String())
				curSpace.Reset()
				inSpace = false
			}
			curWord.WriteRune(r)
		}
	}
	if inSpace {
		words = append(words, "")
		spaces = append(spaces, curSpace.String())
	} else {
		words = append(words, curWord.String())
	}
	return words, spaces
}

func Titlecase(text string, smallFirstLast bool) string {
	lines := strings.Split(text, "\n")
	var processed []string

	for _, line := range lines {
		if len(line) == 0 {
			processed = append(processed, "")
			continue
		}

		allCaps := strings.ToUpper(line) == line
		words, spaces := splitSpaces(line)
		tcLine := make([]string, 0, len(words))

		for _, word := range words {
			if len(word) == 0 {
				tcLine = append(tcLine, "")
				continue
			}

			// 1. All-caps initials
			if allCaps && ucInitialsRegex.MatchString(word) {
				tcLine = append(tcLine, word)
				continue
			}

			// 2. APOS_SECOND: o'reilly, l'grange, etc.
			if matched, p, a, rem := matchesAposSecond(word); matched {
				remRunes := []rune(rem)
				remRunes[0] = unicode.ToUpper(remRunes[0])
				remFormatted := string(remRunes)
				pLower := unicode.ToLower(p)
				if pLower != 'a' && pLower != 'e' && pLower != 'i' && pLower != 'o' && pLower != 'u' {
					tcLine = append(tcLine, string(pLower)+string(a)+remFormatted)
				} else {
					tcLine = append(tcLine, string(unicode.ToUpper(p))+string(a)+remFormatted)
				}
				continue
			}

			// 3. MAC_MC
			if m := macMcRegex.FindStringSubmatch(word); m != nil {
				prefix := m[0][:len(m[0])-len(m[1])]
				prefixCap := capitalizeWord(prefix)
				tcLine = append(tcLine, prefixCap+Titlecase(m[1], true))
				continue
			}

			// 4. MR_MRS_MS_DR
			if mrMrsMsDrRegex.MatchString(word) {
				runes := []rune(word)
				runes[0] = unicode.ToUpper(runes[0])
				tcLine = append(tcLine, string(runes))
				continue
			}

			// 5. INLINE_PERIOD or (not all_caps and UC_ELSEWHERE)
			if inlinePeriod.MatchString(word) || (!allCaps && hasUcElsewhere(word)) {
				tcLine = append(tcLine, word)
				continue
			}

			// 6. SMALL_WORDS
			if smallWordsRegex.MatchString(word) {
				tcLine = append(tcLine, strings.ToLower(word))
				continue
			}

			// 7. Slashes (with no //)
			if strings.Contains(word, "/") && !strings.Contains(word, "//") {
				parts := strings.Split(word, "/")
				slashed := make([]string, len(parts))
				for idx, p := range parts {
					slashed[idx] = Titlecase(p, false)
				}
				tcLine = append(tcLine, strings.Join(slashed, "/"))
				continue
			}

			// 8. Hyphens
			if strings.Contains(word, "-") {
				parts := strings.Split(word, "-")
				hyphenated := make([]string, len(parts))
				for idx, p := range parts {
					hyphenated[idx] = Titlecase(p, false)
				}
				tcLine = append(tcLine, strings.Join(hyphenated, "-"))
				continue
			}

			// 9. If all_caps, lowercase
			if allCaps {
				word = strings.ToLower(word)
			}

			// 10. Acronyms (all consonants > 2)
			if isAllConsoants(word) {
				tcLine = append(tcLine, strings.ToUpper(word))
				continue
			}

			// 11. Normal capitalization
			tcLine = append(tcLine, capFirst(word))
		}

		// Small first and last
		if smallFirstLast && len(tcLine) > 0 {
			// First word
			if lead, small, rest, ok := matchSmallFirst(tcLine[0]); ok {
				tcLine[0] = lead + capitalizeWord(small) + rest
			}

			// Last word
			if before, matchStr, ok := matchSmallLast(tcLine[len(tcLine)-1]); ok {
				tcLine[len(tcLine)-1] = before + capitalizeWord(matchStr)
			}
		}

		// Join words and spaces
		var lineJoined strings.Builder
		for i, w := range tcLine {
			lineJoined.WriteString(w)
			if i < len(spaces) {
				lineJoined.WriteString(spaces[i])
			}
		}
		res := lineJoined.String()

		// Subphrase capitalization
		res = subphraseRegex.ReplaceAllStringFunc(res, func(m string) string {
			runes := []rune(m)
			delimSpace := string(runes[:2])
			smallWord := string(runes[2:])
			return delimSpace + capitalizeWord(smallWord)
		})

		processed = append(processed, res)
	}

	return strings.Join(processed, "\n")
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		line := scanner.Text()
		fmt.Println(Titlecase(line, true))
	}
}
EOF

# 4. Build Go binary to verify compilation
go build -o titlecase .
go build ./...

echo "Solution successfully deployed."
