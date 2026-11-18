#!/bin/bash
set -e

cd /workspace/repo

# ---------------------------------------------------------------------------
# 1. Write go.mod (stdlib only – no require directives)
# ---------------------------------------------------------------------------
cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

# ---------------------------------------------------------------------------
# 2. Write main.go – full Go port of the Python titlecase() function.
#    Rules and constants are taken verbatim from the Python source
#    (environment/python-titlecase/titlecase/__init__.py).
# ---------------------------------------------------------------------------
cat > main.go << 'GOEOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"regexp"
	"strings"
	"unicode"
)

// ---------------------------------------------------------------------------
// Constants mirroring the Python source
// ---------------------------------------------------------------------------

// SMALL words (regex: ^(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)$  IGNORECASE)
var smallWordSet = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

// PUNCT rune set (matches the PUNCT constant in the Python source:
//   !"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~
// Note: only left double quote “ (\u201C) and left single quote ‘ (\u2018)
// are in the Python PUNCT constant.
var punctSet = map[rune]bool{
	'!': true, '"': true, '\u201C': true,
	'#': true, '$': true, '%': true, '&': true,
	'\'': true, '\u2018': true,
	'(': true, ')': true, '*': true, '+': true, ',': true,
	'-': true, '\u2013': true, '\u2012': true, '\u2014': true, '\u2015': true,
	'.': true, '/': true, ':': true, ';': true, '?': true,
	'@': true, '[': true, '\\': true, ']': true, '_': true,
	'`': true, '{': true, '|': true, '}': true, '~': true,
}

// ASCII consonants (set(string.ascii_lowercase) - {a,e,i,o,u,y})
var consonantSet = map[rune]bool{
	'b': true, 'c': true, 'd': true, 'f': true, 'g': true,
	'h': true, 'j': true, 'k': true, 'l': true, 'm': true,
	'n': true, 'p': true, 'q': true, 'r': true, 's': true,
	't': true, 'v': true, 'w': true, 'x': true, 'z': true,
}

// Compiled regexes matching Python's line-level patterns
var (
	smallFirstRegex = regexp.MustCompile(`(?i)^([!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}~]*)(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)\b`)
	smallLastRegex  = regexp.MustCompile(`(?i)\b(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)[!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}~]?$`)
	subphraseRegex  = regexp.MustCompile(`([:.;?!\-–‒—―][ ])(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)`)
)

// Helper: is a rune a word character for \w / \b purposes?
func isWordChar(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}

// Split a line into (words, spaces) exactly like Python's regex.split(r'(\s)', line)
func splitOnWhitespace(s string) (words []string, spaces []string) {
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

// UC_INITIALS: ^(?:[\p{Uppercase_Letter}]{1}\.{1}|[\p{Uppercase_Letter}]{1}\.{1}[\p{Uppercase_Letter}]{1})+$
func matchUCInitials(w string) bool {
	runes := []rune(w)
	n := len(runes)
	i := 0
	if n == 0 {
		return false
	}
	for i < n {
		if !unicode.IsUpper(runes[i]) {
			return false
		}
		i++
		if i >= n || runes[i] != '.' {
			return false
		}
		i++
		if i < n && unicode.IsUpper(runes[i]) {
			i++
		}
	}
	return true
}

// APOS_SECOND: ^[dol]{1}['\u2018]{1}[\p{Letter}]+(?:['s]{2})?$  IGNORECASE
func matchAposSecond(w string) bool {
	runes := []rune(w)
	n := len(runes)
	if n < 3 {
		return false
	}
	r0 := unicode.ToLower(runes[0])
	if r0 != 'd' && r0 != 'o' && r0 != 'l' {
		return false
	}
	if runes[1] != '\'' && runes[1] != '\u2018' {
		return false
	}
	i := 2
	if i >= n || !unicode.IsLetter(runes[i]) {
		return false
	}
	for i < n && unicode.IsLetter(runes[i]) {
		i++
	}
	if i < n {
		if i+2 == n && runes[i] == '\'' && unicode.ToLower(runes[i+1]) == 's' {
			i += 2
		} else {
			return false
		}
	}
	return i == n
}

func applyAposSecond(w string) string {
	runes := []rune(w)
	vowels := map[rune]bool{'a': true, 'e': true, 'i': true, 'o': true, 'u': true}
	r0Lower := unicode.ToLower(runes[0])
	if _, isVowel := vowels[r0Lower]; !isVowel {
		runes[0] = unicode.ToLower(runes[0])
	} else {
		runes[0] = unicode.ToUpper(runes[0])
	}
	runes[2] = unicode.ToUpper(runes[2])
	return string(runes)
}

// MAC_MC: ^([Mm]c|MC)(\w.+)
func matchMacMc(w string) (prefix, rest string, ok bool) {
	runes := []rune(w)
	if len(runes) < 3 {
		return
	}
	r0 := runes[0]
	r1 := runes[1]
	isMc := (r0 == 'M' || r0 == 'm') && (r1 == 'c' || r1 == 'C')
	isMC := r0 == 'M' && r1 == 'C'
	if !isMc && !isMC {
		return
	}
	if len(runes) < 4 {
		return
	}
	r2 := runes[2]
	if !isWordChar(r2) {
		return
	}
	prefix = string(runes[:2])
	rest = string(runes[2:])
	ok = true
	return
}

// MR_MRS_MS_DR: ^((m((rs?)|s))|Dr)$  IGNORECASE
func matchMrMrsMsDr(w string) bool {
	lower := strings.ToLower(w)
	switch lower {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

func applyMrMrsMsDr(w string) string {
	runes := []rune(w)
	if len(runes) == 0 {
		return w
	}
	runes[0] = unicode.ToUpper(runes[0])
	return string(runes)
}

// INLINE_PERIOD: [\p{Letter}][.][\p{Letter}]  IGNORECASE
func hasInlinePeriod(w string) bool {
	runes := []rune(w)
	n := len(runes)
	for i := 1; i < n-1; i++ {
		if runes[i] == '.' && unicode.IsLetter(runes[i-1]) && unicode.IsLetter(runes[i+1]) {
			return true
		}
	}
	return false
}

// UC_ELSEWHERE: [PUNCT]*?[\p{Letter}]+[\p{Uppercase_Letter}]+?
func matchUCElsewhere(w string) bool {
	runes := []rune(w)
	n := len(runes)
	i := 0
	for i < n && punctSet[runes[i]] {
		i++
	}
	if i >= n || !unicode.IsLetter(runes[i]) {
		return false
	}
	seenLetter := false
	for i < n && unicode.IsLetter(runes[i]) {
		if seenLetter && unicode.IsUpper(runes[i]) {
			return true
		}
		seenLetter = true
		i++
	}
	return false
}

// SMALL_WORDS: ^(SMALL)$  IGNORECASE
func matchSmallWord(w string) bool {
	return smallWordSet[strings.ToLower(w)]
}

// allASCIIConsonants: regex.search(r'\A[bcdfghjklmnpqrstvwxz]+\Z', word, flags=regex.IGNORECASE)
func allASCIIConsonants(w string) bool {
	runes := []rune(w)
	if len(runes) == 0 {
		return false
	}
	for _, r := range runes {
		if r > 127 {
			return false
		}
		if !consonantSet[unicode.ToLower(r)] {
			return false
		}
	}
	return true
}

// CAPFIRST: ^[PUNCT]*?([\p{Letter}])
func capFirst(w string) string {
	runes := []rune(w)
	for i, r := range runes {
		if unicode.IsLetter(r) {
			runes[i] = unicode.ToUpper(r)
			return string(runes)
		}
		if !punctSet[r] {
			break
		}
	}
	return w
}

// SMALL_FIRST: ^([PUNCT]*)(SMALL)\b  IGNORECASE
func applySmallFirst(w string) string {
	loc := smallFirstRegex.FindStringSubmatchIndex(w)
	if loc == nil {
		return w
	}
	punct := w[loc[2]:loc[3]]
	small := w[loc[4]:loc[5]]
	rSmall := []rune(small)
	cap := strings.ToUpper(string(rSmall[:1])) + strings.ToLower(string(rSmall[1:]))
	return punct + cap + w[loc[5]:]
}

// SMALL_LAST: \b(SMALL)[PUNCT]?$  IGNORECASE
func applySmallLast(w string) string {
	loc := smallLastRegex.FindStringIndex(w)
	if loc == nil {
		return w
	}
	match := w[loc[0]:loc[1]]
	rMatch := []rune(match)
	cap := strings.ToUpper(string(rMatch[:1])) + strings.ToLower(string(rMatch[1:]))
	return w[:loc[0]] + cap + w[loc[1]:]
}

// SUBPHRASE: ([:.;?!\-–‒—―][ ])(SMALL)
func applySubphrase(s string) string {
	return subphraseRegex.ReplaceAllStringFunc(s, func(m string) string {
		sub := subphraseRegex.FindStringSubmatch(m)
		if len(sub) < 3 {
			return m
		}
		r := []rune(sub[2])
		cap := strings.ToUpper(string(r[:1])) + strings.ToLower(string(r[1:]))
		return sub[1] + cap
	})
}

// Core titlecase function
func titlecaseString(text string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(text) == text

	words, spaces := splitOnWhitespace(text)

	tcLine := make([]string, len(words))
	immutable := make([]bool, len(words))

	for idx, word := range words {
		if word == "" {
			tcLine[idx] = word
			continue
		}

		// Rule 1: all_caps + UC_INITIALS
		if allCaps && matchUCInitials(word) {
			tcLine[idx] = word
			immutable[idx] = true
			continue
		}

		// Rule 2: APOS_SECOND
		if matchAposSecond(word) {
			tcLine[idx] = applyAposSecond(word)
			immutable[idx] = true
			continue
		}

		// Rule 3: MAC_MC
		if prefix, rest, ok := matchMacMc(word); ok {
			capPrefix := strings.ToUpper(prefix[:1]) + strings.ToLower(prefix[1:])
			tcLine[idx] = capPrefix + titlecaseString(rest, true)
			immutable[idx] = true
			continue
		}

		// Rule 4: MR_MRS_MS_DR
		if matchMrMrsMsDr(word) {
			tcLine[idx] = applyMrMrsMsDr(word)
			immutable[idx] = true
			continue
		}

		// Rule 5: INLINE_PERIOD or (not all_caps and UC_ELSEWHERE)
		if hasInlinePeriod(word) || (!allCaps && matchUCElsewhere(word)) {
			tcLine[idx] = word
			continue
		}

		// Rule 6: SMALL_WORDS
		if matchSmallWord(word) {
			tcLine[idx] = strings.ToLower(word)
			continue
		}

		// Rule 7: slash splitting
		if strings.Contains(word, "/") && !strings.Contains(word, "//") {
			parts := strings.Split(word, "/")
			for pi, p := range parts {
				parts[pi] = titlecaseString(p, false)
			}
			tcLine[idx] = strings.Join(parts, "/")
			continue
		}

		// Rule 8: hyphen splitting
		if strings.Contains(word, "-") {
			parts := strings.Split(word, "-")
			for pi, p := range parts {
				parts[pi] = titlecaseString(p, false)
			}
			tcLine[idx] = strings.Join(parts, "-")
			continue
		}

		// Pre-processing: if all_caps, lowercase before further rules
		if allCaps {
			word = strings.ToLower(word)
		}

		// Rule 9: all ASCII consonants + len > 2
		if allASCIIConsonants(word) && len([]rune(word)) > 2 {
			tcLine[idx] = strings.ToUpper(word)
			continue
		}

		// Rule 10: capFirst
		tcLine[idx] = capFirst(word)
	}

	// Apply SMALL_FIRST and SMALL_LAST
	if smallFirstLast && len(tcLine) > 0 {
		if !immutable[0] {
			tcLine[0] = applySmallFirst(tcLine[0])
		}
		if !immutable[len(tcLine)-1] {
			tcLine[len(tcLine)-1] = applySmallLast(tcLine[len(tcLine)-1])
		}
	}

	// Reassemble
	var sb strings.Builder
	for i, w := range tcLine {
		sb.WriteString(w)
		if i < len(spaces) {
			sb.WriteString(spaces[i])
		}
	}
	result := sb.String()

	// Apply SUBPHRASE
	result = applySubphrase(result)

	return result
}

// main: read one title per line from stdin, print titlecased output to stdout.
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
					fmt.Fprintln(writer, titlecaseString(line, true))
				}
				break
			}
			fmt.Fprintf(os.Stderr, "read error: %v\n", err)
			os.Exit(1)
		}
		line = strings.TrimRight(line, "\r\n")
		fmt.Fprintln(writer, titlecaseString(line, true))
	}
}
GOEOF

# ---------------------------------------------------------------------------
# 3. Delete every .py file (and compiled .pyc) under /workspace/repo
# ---------------------------------------------------------------------------
find /workspace/repo -type f -name "*.py"  -delete
find /workspace/repo -type f -name "*.pyc" -delete
# Remove leftover python package directory to prevent build collision
rm -rf /workspace/repo/titlecase
# Remove empty __pycache__ directories left behind
find /workspace/repo -type d -name "__pycache__" -empty -delete

# ---------------------------------------------------------------------------
# 4. Verify the build
# ---------------------------------------------------------------------------
go build ./...

echo "solve.sh completed successfully."
