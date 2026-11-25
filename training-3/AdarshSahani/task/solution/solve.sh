#!/usr/bin/env bash
set -euo pipefail

repo="${REPO_ROOT:-/workspace/repo}"
mkdir -p "$repo"

cat > "$repo/go.mod" <<'EOF'
module titlecase

go 1.23
EOF

cat > "$repo/main.go" <<'EOF'
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()

	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			line = strings.TrimSuffix(line, "\r") // Python text stdin uses universal newlines.
			fmt.Fprintln(out, titlecase(line, true))
		}
		if err != nil {
			if err != io.EOF {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
			break
		}
	}
}
EOF

cat > "$repo/titlecase.go" <<'EOF'
package main

import (
	"strings"
	"unicode"
)

const punctuation = `!"“#$%&'‘()*+,-–‒—―./:;?@[\]_` + "`" + `{|}~`
var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

// Python str.upper() performs full Unicode mappings, including expansions.
var upperExpansions = map[rune]string{
	'\u00df': "SS", '\u0149': "ʼN", '\u01f0': "J\u030c",
	'\u0390': "Ι\u0308\u0301", '\u03b0': "Υ\u0308\u0301", '\u0587': "ԵՒ",
	'\u1e96': "H\u0331", '\u1e97': "T\u0308", '\u1e98': "W\u030a",
	'\u1e99': "Y\u030a", '\u1e9a': "A\u02be", '\u1f50': "Υ\u0313",
	'\u1f52': "Υ\u0313\u0300", '\u1f54': "Υ\u0313\u0301", '\u1f56': "Υ\u0313\u0342",
	'\u1f80': "ἈΙ", '\u1f81': "ἉΙ", '\u1f82': "ἊΙ", '\u1f83': "ἋΙ",
	'\u1f84': "ἌΙ", '\u1f85': "ἍΙ", '\u1f86': "ἎΙ", '\u1f87': "ἏΙ",
	'\u1f88': "ἈΙ", '\u1f89': "ἉΙ", '\u1f8a': "ἊΙ", '\u1f8b': "ἋΙ",
	'\u1f8c': "ἌΙ", '\u1f8d': "ἍΙ", '\u1f8e': "ἎΙ", '\u1f8f': "ἏΙ",
	'\u1f90': "ἨΙ", '\u1f91': "ἩΙ", '\u1f92': "ἪΙ", '\u1f93': "ἫΙ",
	'\u1f94': "ἬΙ", '\u1f95': "ἭΙ", '\u1f96': "ἮΙ", '\u1f97': "ἯΙ",
	'\u1f98': "ἨΙ", '\u1f99': "ἩΙ", '\u1f9a': "ἪΙ", '\u1f9b': "ἫΙ",
	'\u1f9c': "ἬΙ", '\u1f9d': "ἭΙ", '\u1f9e': "ἮΙ", '\u1f9f': "ἯΙ",
	'\u1fa0': "ὨΙ", '\u1fa1': "ὩΙ", '\u1fa2': "ὪΙ", '\u1fa3': "ὫΙ",
	'\u1fa4': "ὬΙ", '\u1fa5': "ὭΙ", '\u1fa6': "ὮΙ", '\u1fa7': "ὯΙ",
	'\u1fa8': "ὨΙ", '\u1fa9': "ὩΙ", '\u1faa': "ὪΙ", '\u1fab': "ὫΙ",
	'\u1fac': "ὬΙ", '\u1fad': "ὭΙ", '\u1fae': "ὮΙ", '\u1faf': "ὯΙ",
	'\u1fb2': "ᾺΙ", '\u1fb3': "ΑΙ", '\u1fb4': "ΆΙ", '\u1fb6': "Α\u0342",
	'\u1fb7': "Α\u0342Ι", '\u1fbc': "ΑΙ", '\u1fc2': "ῊΙ", '\u1fc3': "ΗΙ",
	'\u1fc4': "ΉΙ", '\u1fc6': "Η\u0342", '\u1fc7': "Η\u0342Ι", '\u1fcc': "ΗΙ",
	'\u1fd2': "Ι\u0308\u0300", '\u1fd3': "Ι\u0308\u0301", '\u1fd6': "Ι\u0342",
	'\u1fd7': "Ι\u0308\u0342", '\u1fe2': "Υ\u0308\u0300", '\u1fe3': "Υ\u0308\u0301",
	'\u1fe4': "Ρ\u0313", '\u1fe6': "Υ\u0342", '\u1fe7': "Υ\u0308\u0342",
	'\u1ff2': "ῺΙ", '\u1ff3': "ΩΙ", '\u1ff4': "ΏΙ", '\u1ff6': "Ω\u0342",
	'\u1ff7': "Ω\u0342Ι", '\u1ffc': "ΩΙ", '\ufb00': "FF", '\ufb01': "FI",
	'\ufb02': "FL", '\ufb03': "FFI", '\ufb04': "FFL", '\ufb05': "ST",
	'\ufb06': "ST", '\ufb13': "ՄՆ", '\ufb14': "ՄԵ", '\ufb15': "ՄԻ",
	'\ufb16': "ՎՆ", '\ufb17': "ՄԽ",
}

func isSpace(r rune) bool {
	// Unicode White_Space plus the four ASCII information separators that
	// Python's Unicode regular-expression \s also recognizes.
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

func isPythonWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
}

func isPunctuation(r rune) bool { return strings.ContainsRune(punctuation, r) }

func upper(s string) string {
	var b strings.Builder
	for _, r := range s {
		if expansion, ok := upperExpansions[r]; ok {
			b.WriteString(expansion)
		} else {
			b.WriteRune(unicode.ToUpper(r))
		}
	}
	return b.String()
}

func lower(s string) string {
	var b strings.Builder
	for _, r := range s {
		if r == '\u0130' { // Python lower expands LATIN CAPITAL I WITH DOT ABOVE.
			b.WriteString("i\u0307")
		} else {
			b.WriteRune(unicode.ToLower(r))
		}
	}
	return b.String()
}

func capitalize(s string) string {
	if s == "" {
		return s
	}
	runes := []rune(s)
	return upper(string(runes[0])) + lower(string(runes[1:]))
}

func equalFold(s, target string) bool {
	return strings.EqualFold(s, target)
}

func isSmall(s string) bool {
	for word := range smallWords {
		if equalFold(s, word) {
			return true
		}
	}
	return false
}

func isBoundaryBefore(s string, i int) bool {
	runes := []rune(s)
	if i <= 0 || i >= len(runes) {
		return true
	}
	return isPythonWord(runes[i-1]) != isPythonWord(runes[i])
}

func isBoundaryAfter(s string, i int) bool {
	runes := []rune(s)
	if i < 0 || i >= len(runes)-1 {
		return true
	}
	return isPythonWord(runes[i]) != isPythonWord(runes[i+1])
}

func splitWordsAndSpaces(line string) ([]string, []string) {
	runes := []rune(line)
	words := make([]string, 0, len(runes)/2+1)
	spaces := make([]string, 0, len(runes)/2)
	start := 0
	for i, r := range runes {
		if isSpace(r) {
			words = append(words, string(runes[start:i]))
			spaces = append(spaces, string(r))
			start = i + 1
		}
	}
	words = append(words, string(runes[start:]))
	return words, spaces
}

func inlinePeriod(word string) bool {
	r := []rune(word)
	for i := 1; i+1 < len(r); i++ {
		if r[i] == '.' && isPythonWord(r[i-1]) && isPythonWord(r[i+1]) {
			return true
		}
	}
	return false
}

func hasUpperElsewhere(word string) bool {
	r := []rune(word)
	i := 0
	for i < len(r) && isPunctuation(r[i]) {
		i++
	}
	start := i
	// Python's pattern is [a-zA-Z]+[A-Z]+? after leading punctuation.
	// At least one ASCII letter must precede an uppercase ASCII letter.
	for i < len(r) && ((r[i] >= 'a' && r[i] <= 'z') || (r[i] >= 'A' && r[i] <= 'Z')) {
		if i > start && r[i] >= 'A' && r[i] <= 'Z' {
			return true
		}
		i++
	}
	return false
}

func uppercaseInitials(word string) bool {
	r := []rune(word)
	if len(r) == 0 {
		return false
	}
	for i := 0; i < len(r); {
		if r[i] < 'A' || r[i] > 'Z' {
			return false
		}
		i++
		if i >= len(r) || r[i] != '.' {
			return false
		}
		i++
		if i < len(r) && r[i] >= 'A' && r[i] <= 'Z' {
			// The alternative [A-Z].[A-Z] consumes the next initial's letter;
			// its following period is consumed by the next loop iteration.
			continue
		}
	}
	return true
}

func apostropheSecond(word string) bool {
	r := []rune(word)
	if len(r) < 3 || !strings.ContainsRune("dDoOlL", r[0]) || (r[1] != '\'' && r[1] != '‘') {
		return false
	}
	end := len(r)
	if end >= 2 {
		a, b := unicode.ToLower(r[end-2]), unicode.ToLower(r[end-1])
		if strings.ContainsRune("'s", a) && strings.ContainsRune("'s", b) {
			end -= 2
		}
	}
	if end < 3 {
		return false
	}
	for _, c := range r[2:end] {
		if !isPythonWord(c) {
			return false
		}
	}
	return true
}

func applyApostropheRule(word string) string {
	r := []rune(word)
	if len(r) < 3 {
		return word
	}
	if strings.ContainsRune("aeiouAEIOU", r[0]) {
		r[0] = []rune(upper(string(r[0])))[0]
	} else {
		r[0] = []rune(lower(string(r[0])))[0]
	}
	r[2] = []rune(upper(string(r[2])))[0]
	return string(r)
}

func mcPrefix(word string) (string, string, bool) {
	r := []rune(word)
	if len(r) < 4 {
		return "", "", false
	}
	prefix := ""
	switch string(r[:2]) {
	case "Mc", "mc", "MC":
		prefix = string(r[:2])
	default:
		return "", "", false
	}
	if !isPythonWord(r[2]) {
		return "", "", false
	}
	return prefix, string(r[2:]), true
}

func isSpecialTitle(word string) bool {
	return equalFold(word, "mr") || equalFold(word, "mrs") || equalFold(word, "ms") || equalFold(word, "dr")
}

func capFirst(word string) string {
	r := []rune(word)
	i := 0
	for i < len(r) && isPunctuation(r[i]) && !isPythonWord(r[i]) {
		i++
	}
	if i < len(r) && isPythonWord(r[i]) {
		return upper(string(r[:i+1])) + string(r[i+1:])
	}
	return word
}

func smallFirst(word string) string {
	r := []rune(word)
	i := 0
	for i < len(r) && isPunctuation(r[i]) {
		i++
	}
	for _, small := range []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "via", "vs"} {
		part := []rune(small)
		if len(r) < i+len(part) {
			continue
		}
		if !equalFold(string(r[i:i+len(part)]), small) {
			continue
		}
		candidateLengths := []int{len(part)}
		if (small == "v" || small == "vs") && i+len(part) < len(r) && r[i+len(part)] == '.' {
			// Python's optional period is greedy but backtracks when needed for \b.
			candidateLengths = []int{len(part) + 1, len(part)}
		}
		for _, candidateLength := range candidateLengths {
			end := i + candidateLength
			if end < len(r) && isPythonWord(r[end-1]) == isPythonWord(r[end]) {
				continue
			}
			return string(r[:i]) + capitalize(string(r[i:end])) + string(r[end:])
		}
	}
	return word
}

func smallLast(word string) string {
	r := []rune(word)
	for _, small := range []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "via", "vs"} {
		for _, period := range []bool{false, true} {
			candidate := small
			if period && (small == "v" || small == "vs") {
				candidate += "."
			} else if period {
				continue
			}
			end := len(r)
			if end > 0 && isPunctuation(r[end-1]) {
				end--
			}
			c := []rune(candidate)
			start := end - len(c)
			if start < 0 || !equalFold(string(r[start:end]), candidate) {
				continue
			}
			if start > 0 && isPythonWord(r[start-1]) == isPythonWord(r[start]) {
				continue
			}
			return string(r[:start]) + capitalize(string(r[start:]))
		}
	}
	return word
}

func isAllConsonants(word string) bool {
	if len([]rune(word)) <= 2 {
		return false
	}
	for _, r := range word {
		if !((r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')) || strings.ContainsRune("aeiouyAEIOUY", r) {
			return false
		}
	}
	return true
}

func titlecaseWord(word string, allCaps, firstLast bool) string {
	if allCaps && uppercaseInitials(word) {
		return word
	}
	if apostropheSecond(word) {
		return applyApostropheRule(word)
	}
	if prefix, rest, ok := mcPrefix(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isSpecialTitle(word) {
		r := []rune(word)
		r[0] = []rune(upper(string(r[0])))[0]
		return string(r)
	}
	if inlinePeriod(word) || (!allCaps && hasUpperElsewhere(word)) {
		return word
	}
	if isSmall(word) {
		return lower(word)
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
		word = lower(word)
	}
	if isAllConsonants(word) {
		return upper(word)
	}
	return capFirst(word)
}

func subphrase(s string) string {
	r := []rune(s)
	var b strings.Builder
	for i := 0; i < len(r); {
		b.WriteRune(r[i])
		if strings.ContainsRune(":.;?!-–‒—―", r[i]) && i+2 < len(r) && r[i+1] == ' ' {
			start := i + 2
			for _, small := range []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "via", "vs"} {
				part := []rune(small)
				end := start + len(part)
				if end > len(r) || string(r[start:end]) != small {
					continue
				}
				if (small == "v" || small == "vs") && end < len(r) && r[end] == '.' {
					end++
				}
				b.WriteRune(r[i+1])
				b.WriteString(capitalize(string(r[start:end])))
				i = end
				goto next
			}
		}
		i++
	next:
	}
	return b.String()
}

func titlecase(line string, firstLast bool) string {
	allCaps := upper(line) == line
	words, spaces := splitWordsAndSpaces(line)
	for i, word := range words {
		words[i] = titlecaseWord(word, allCaps, false)
	}
	if firstLast && len(words) > 0 {
		words[0] = smallFirst(words[0])
		words[len(words)-1] = smallLast(words[len(words)-1])
	}
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return subphrase(b.String())
}
EOF

find "$repo" -type f -name '*.py' -delete
rm -rf -- "$repo/titlecase"
cd "$repo"
gofmt -w main.go titlecase.go
go build ./...
if [[ -f "$repo/titlecase" ]]; then rm -f "$repo/titlecase"; fi
rm -f titlecase.exe
