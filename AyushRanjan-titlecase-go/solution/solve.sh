#!/bin/bash
# Harbor Day 3 — Titlecase in Go
# Writes a complete Go implementation to /workspace/repo.
# Run from any working directory.
#
# Verifier commands (from tests/criteria/build.py and behaviour.py):
#   go build ./...                        (build check — no output file needed)
#   go build -o /tmp/titlecase ./...      (behaviour check — produces executable)
#
# Both commands run with cwd=/workspace/repo.
# Both require exactly one package: package main.
# All Go source lives in /workspace/repo/*.go (no subdirectories).

set -euo pipefail

REPO=/workspace/repo

# ── 1. Create repo directory ──────────────────────────────────────────────────
mkdir -p "$REPO"

# ── 2. go.mod ─────────────────────────────────────────────────────────────────
cat > "$REPO/go.mod" << 'GOMOD'
module titlecase

go 1.23
GOMOD

# ── 3. titlecase.go — all logic in package main ───────────────────────────────
# Everything is in a single package (main) so that:
#   go build ./...                   compiles the package (no conflict)
#   go build -o /tmp/titlecase ./...  links main() into an executable
#
# Unicode dashes are written as \uXXXX escape sequences inside raw string
# literals where possible, or as explicit rune constants, to avoid any
# encoding corruption in the heredoc.
cat > "$REPO/titlecase.go" << 'GOEOF'
package main

import (
	"strings"
	"unicode"
)

// smallWords is the exact set from the Python SMALL constant.
// v and vs match with or without a trailing period.
var smallWords = map[string]bool{
	"a": true, "an": true, "and": true, "as": true, "at": true,
	"but": true, "by": true, "en": true, "for": true, "if": true,
	"in": true, "of": true, "on": true, "or": true, "the": true,
	"to": true, "v": true, "v.": true, "via": true, "vs": true, "vs.": true,
}

func isSmall(word string) bool {
	return smallWords[strings.ToLower(word)]
}

// PUNCT characters from the Python source.
// Written as individual runes to avoid encoding issues in the heredoc.
var punctRunes = []rune{
	'!', '"', '#', '$', '%', '&', '\'', '\u2018', '\u2019', '(', ')', '*',
	'+', ',', '\\', '-', '\u2013', '\u2012', '\u2014', '\u2015',
	'.', '/', ':', ';', '?', '@', '[', '\\', ']', '_', '`', '{', '|', '}', '~',
}

func isPunct(r rune) bool {
	for _, p := range punctRunes {
		if r == p {
			return true
		}
	}
	return false
}

// Subphrase-opening punctuation: colon, period, semicolon, ?, !, dashes.
func isSubphrasePunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-',
		'\u2013', // en dash
		'\u2012', // figure dash
		'\u2014', // em dash
		'\u2015': // horizontal bar
		return true
	}
	return false
}

func isLetter(r rune) bool { return unicode.IsLetter(r) }
func isUpper(r rune) bool  { return unicode.IsUpper(r) }

func isVowel(r rune) bool {
	switch unicode.ToLower(r) {
	case 'a', 'e', 'i', 'o', 'u':
		return true
	}
	return false
}

// isAllCaps: strings.ToUpper(line) == line (Python: line.upper() == line).
func isAllCaps(line string) bool {
	return strings.ToUpper(line) == line
}

// hasInlinePeriod: word contains letter.letter (domain / initials guard).
func hasInlinePeriod(word string) bool {
	runes := []rune(word)
	for i := 1; i < len(runes)-1; i++ {
		if runes[i] == '.' && isLetter(runes[i-1]) && isLetter(runes[i+1]) {
			return true
		}
	}
	return false
}

// hasUCElsewhere: word (non-all-caps) already contains an internal capital,
// e.g. "iTunes", "OmniFocus".  Mirrors Python UC_ELSEWHERE pattern.
func hasUCElsewhere(word string) bool {
	runes := []rune(word)
	i := 0
	for i < len(runes) && isPunct(runes[i]) {
		i++
	}
	seenLetter := false
	for ; i < len(runes); i++ {
		r := runes[i]
		if isLetter(r) {
			if seenLetter && isUpper(r) {
				return true
			}
			seenLetter = true
		} else {
			// Python UC_ELSEWHERE: [Letter]+ stops at the first non-letter.
			// Once the continuous letter-run ends, the pattern cannot match
			// further — stop entirely rather than resetting and continuing.
			break
		}
	}
	return false
}

// isUCInitials: word is a sequence like "A.", "D.C.", "U.S.A" — only
// uppercase letters separated by periods.  Used in all-caps mode to
// leave initials untouched.
func isUCInitials(word string) bool {
	runes := []rune(word)
	if len(runes) == 0 {
		return false
	}
	i := 0
	matched := false
	for i < len(runes) {
		if !unicode.IsLetter(runes[i]) || !isUpper(runes[i]) {
			return false
		}
		i++
		if i >= len(runes) || runes[i] != '.' {
			return false
		}
		i++
		matched = true
		// Optional second uppercase letter before next period.
		if i < len(runes) && unicode.IsLetter(runes[i]) && isUpper(runes[i]) {
			i++
			if i >= len(runes) || runes[i] != '.' {
				return false
			}
			i++
		}
	}
	return matched
}

// isAposSecond: word matches ^[dol][''][letter...]['s]?$  (case-insensitive).
// Examples: o'brien, l'amour, d'artagnan, l'amour's, o'melveny's
func isAposSecond(word string) bool {
	runes := []rune(word)
	if len(runes) < 3 {
		return false
	}
	first := unicode.ToLower(runes[0])
	if first != 'd' && first != 'o' && first != 'l' {
		return false
	}
	if runes[1] != '\'' && runes[1] != '\u2019' {
		return false
	}
	if !isLetter(runes[2]) {
		return false
	}
	// Allow optional trailing 's
	end := len(runes)
	if end >= 2 {
		last2 := string(runes[end-2:])
		if last2 == "'s" || last2 == "\u2019s" {
			end -= 2
		}
	}
	for _, r := range runes[2:end] {
		if !isLetter(r) && !unicode.IsDigit(r) && r != '_' {
			return false
		}
	}
	return true
}

// applyAposSecond: o'brien -> O'Brien, l'amour -> l'Amour, d'artagnan -> d'Artagnan.
// Python: vowel first letter -> uppercase, consonant -> lowercase; then cap after apos.
func applyAposSecond(word string) string {
	runes := []rune(word)
	var sb strings.Builder
	if isVowel(runes[0]) {
		sb.WriteRune(unicode.ToUpper(runes[0]))
	} else {
		sb.WriteRune(unicode.ToLower(runes[0]))
	}
	sb.WriteRune(runes[1]) // apostrophe
	sb.WriteRune(unicode.ToUpper(runes[2]))
	for _, r := range runes[3:] {
		sb.WriteRune(r)
	}
	return sb.String()
}

// matchMacMc returns (prefix, rest) for Mac.../Mc... words, else ("","").
// Minimum length: mc+1=3 chars, mac+1=4 chars.
func matchMacMc(word string) (prefix, rest string) {
    runes := []rune(word)

    if len(runes) < 4 {
        return "", ""
    }

    validPrefix := word[:2] == "Mc" ||
        word[:2] == "mc" ||
        word[:2] == "MC"

    if !validPrefix {
        return "", ""
    }

    // Python's \w.+ requires at least two characters after Mc.
    first := runes[2]
    if !unicode.IsLetter(first) &&
        !unicode.IsDigit(first) &&
        first != '_' {
        return "", ""
    }

    return string(runes[:2]), string(runes[2:])
}

func matchMrMrsMsDr(word string) bool {
	l := strings.ToLower(word)
	return l == "mr" || l == "mrs" || l == "ms" || l == "dr"
}

// capFirst uppercases the first letter in word, skipping leading PUNCT.
func capFirst(word string) string {
	runes := []rune(word)
	for i, r := range runes {
		if isLetter(r) {
			runes[i] = unicode.ToUpper(r)
			return string(runes)
		}
		// Non-PUNCT, non-letter (e.g. a digit) before the first letter means
		// Python's CAPFIRST regex [\p{Letter}] cannot match — return unchanged.
		if !isPunct(r) {
			return word
		}
	}
	return word
}

// isAllConsonants: all letters in word are ASCII consonants (no a e i o u y),
// and there are more than 2 letters.  Mirrors Python's consonant-acronym rule.
func isAllConsonants(word string) bool {
	// Python's consonant-acronym regex is \A[consonants]+\Z — it must match
	// the ENTIRE word.  Any non-letter character (digit, hyphen, etc.) makes
	// the whole-word match fail, so return false immediately.
	var letters []rune
	for _, r := range word {
		if !isLetter(r) {
			return false
		}
		letters = append(letters, unicode.ToLower(r))
	}
	if len(letters) <= 2 {
		return false
	}
	for _, r := range letters {
		switch r {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
		if r > 'z' { // non-ASCII letter — not a plain consonant
			return false
		}
	}
	return true
}

// titlecaseWord processes one whitespace-separated token.
// allCaps: the whole line is uppercase.
func titlecaseWord(word string, allCaps bool) string {
	if word == "" {
		return word
	}

	// UC_INITIALS (all-caps only): leave "A.", "D.C.", "U.S.A" unchanged.
	if allCaps && isUCInitials(word) {
		return word
	}

	// APOS_SECOND: o'brien -> O'Brien regardless of all-caps.
	if isAposSecond(word) {
		return applyAposSecond(word)
	}

	// MAC/MC prefix: McTavish, mctavish -> McTavish.
	if prefix, rest := matchMacMc(word); prefix != "" {
		cap := strings.ToUpper(prefix[:1]) + strings.ToLower(string([]rune(prefix)[1:]))
		return cap + titlecase(rest, false)
	}

	// Mr / Mrs / Ms / Dr: capitalize first letter only.
	if matchMrMrsMsDr(word) {
		runes := []rune(word)
		runes[0] = unicode.ToUpper(runes[0])
		return string(runes)
	}

	// INLINE_PERIOD guard: domain names and initials -> leave unchanged.
	if hasInlinePeriod(word) {
		return word
	}

	// UC_ELSEWHERE guard (not all-caps): iTunes, OmniFocus -> unchanged.
	if !allCaps && hasUCElsewhere(word) {
		return word
	}

	// Small word -> lowercase.
	if isSmall(word) {
		return strings.ToLower(word)
	}

	// Slash split (not //): recurse each part.
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return strings.Join(parts, "/")
	}

	// Hyphen split: recurse each part.
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return strings.Join(parts, "-")
	}

	// Normalize all-caps word to lowercase before further checks.
	if allCaps {
		word = strings.ToLower(word)
	}

	// All-consonants acronym (len > 2) -> uppercase.
	if isAllConsonants(word) {
		return strings.ToUpper(word)
	}

	// Default: capitalize first letter.
	return capFirst(word)
}

// splitWords splits a line into alternating (words, spaces) slices,
// preserving the exact whitespace characters between tokens.
func splitWords(line string) (words []string, spaces []string) {
	type seg struct {
		text  string
		space bool
	}
	var segs []seg
	var buf strings.Builder
	inSpace := false
	started := false

	flush := func() {
		if buf.Len() > 0 {
			segs = append(segs, seg{buf.String(), inSpace})
			buf.Reset()
		}
	}

	for _, r := range line {
		sp := unicode.IsSpace(r)
		if !started {
			inSpace = sp
			started = true
		} else if sp != inSpace {
			flush()
			inSpace = sp
		}
		buf.WriteRune(r)
	}
	flush()

	// Ensure pattern starts with a word-segment.
	if len(segs) > 0 && segs[0].space {
		segs = append([]seg{{"", false}}, segs...)
	}
	// Ensure last segment is a space (even if empty) so slices are equal length.
	if len(segs) == 0 || !segs[len(segs)-1].space {
		segs = append(segs, seg{"", true})
	}

	for i, s := range segs {
		if i%2 == 0 {
			words = append(words, s.text)
		} else {
			spaces = append(spaces, s.text)
		}
	}
	for len(spaces) < len(words) {
		spaces = append(spaces, "")
	}
	return
}

func joinWords(words, spaces []string) string {
	var sb strings.Builder
	for i, w := range words {
		sb.WriteString(w)
		if i < len(spaces) {
			sb.WriteString(spaces[i])
		}
	}
	return sb.String()
}

// applySmallFirst: if the first word (after any leading PUNCT) is a small
// word, capitalize it.  Mirrors Python SMALL_FIRST regex.
func applySmallFirst(word string) string {
	runes := []rune(word)
	for i, r := range runes {
		if isLetter(r) {
			rest := string(runes[i:])
			if isSmall(rest) {
				runes[i] = unicode.ToUpper(r)
				return string(runes)
			}
			return word
		}
	}
	return word
}

// applySmallLast: if the last word (before any trailing PUNCT) is a small
// word, capitalize it.  Mirrors Python SMALL_LAST regex.
func applySmallLast(word string) string {
	runes := []rune(word)
	end := len(runes)
	// Strip one optional trailing PUNCT char (mirrors [PUNCT]? in SMALL_LAST).
	if end > 0 && isPunct(runes[end-1]) {
		end--
	}
	if end == 0 {
		return word
	}
	// Find the start of the last letter-run by scanning backward.
	// Python's \b fires between a \W char and a \w char (letter/digit/underscore).
	// We only capitalize if the boundary before the run is a genuine \W character
	// (not a digit or underscore, which are \w in Python regex).
	start := end
	for start > 0 && isLetter(runes[start-1]) {
		start--
	}
	if start == end {
		return word // no trailing letter-run found
	}
	// Check the word-boundary: the char immediately before the run must be
	// non-\w (not letter, digit, or underscore) or we must be at string start.
	if start > 0 {
		prev := runes[start-1]
		if isLetter(prev) || unicode.IsDigit(prev) || prev == '_' {
			// No \b here — Python SMALL_LAST would not match.
			return word
		}
	}
	candidate := strings.ToLower(string(runes[start:end]))
	if isSmall(candidate) {
		runes[start] = unicode.ToUpper(runes[start])
		return string(runes)
	}
	return word
}

// applySubphrase: after [:.;?!-–‒—―] + space, capitalize a following small word.
// Mirrors Python SUBPHRASE regex.
func applySubphrase(s string) string {
	runes := []rune(s)
	out := make([]rune, 0, len(runes))
	i := 0
	for i < len(runes) {
		r := runes[i]
		if isSubphrasePunct(r) && i+1 < len(runes) && runes[i+1] == ' ' {
			out = append(out, r, ' ')
			i += 2
			// Find end of next token.
			j := i
			for j < len(runes) && !unicode.IsSpace(runes[j]) {
				j++
			}
			candidate := string(runes[i:j])
			if isSmall(candidate) && len(candidate) > 0 {
				cr := []rune(candidate)
				cr[0] = unicode.ToUpper(cr[0])
				out = append(out, cr...)
				i = j
				continue
			}
			// Not a small word — emit as-is from current position.
		} else {
			out = append(out, r)
			i++
		}
	}
	return string(out)
}

// titlecase is the core recursive function.
// smallFirstLast=true at top level; false when recursing (hyphens/slashes).
func titlecase(line string, smallFirstLast bool) string {
	if line == "" {
		return line
	}

	allCaps := isAllCaps(line)
	words, spaces := splitWords(line)

	processed := make([]string, len(words))
	for i, w := range words {
		processed[i] = titlecaseWord(w, allCaps)
	}

	if smallFirstLast && len(processed) > 0 {
		processed[0] = applySmallFirst(processed[0])
		last := len(processed) - 1
		processed[last] = applySmallLast(processed[last])
	}

	result := joinWords(processed, spaces)
	result = applySubphrase(result)
	return result
}

// TitlecaseLine is the public entry point for one input line.
func TitlecaseLine(line string) string {
	return titlecase(line, true)
}
GOEOF

# ── 4. main.go ────────────────────────────────────────────────────────────────
cat > "$REPO/main.go" << 'GOEOF'
package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	buf := make([]byte, 1024*1024)
	scanner.Buffer(buf, len(buf))

	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()

	for scanner.Scan() {
		fmt.Fprintln(w, TitlecaseLine(scanner.Text()))
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, "read error:", err)
		os.Exit(1)
	}
}
GOEOF

# ── 5. Build check (mirrors build.py exactly) ─────────────────────────────────
cd "$REPO"
rm -rf "$REPO/titlecase"
find "$REPO" -name "*.py" -delete
echo "No .py files in $REPO"
go build ./...
echo "go build ./... passed"

# ── 6. Executable check (mirrors behaviour.py exactly) ────────────────────────
go build -o /tmp/titlecase ./...
echo "go build -o /tmp/titlecase ./... passed"

# ── 7. Remove any .py files from /workspace/repo ─────────────────────────────
echo "No .py files in $REPO"

echo "Done."
