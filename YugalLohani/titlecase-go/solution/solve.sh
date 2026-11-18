#!/bin/bash
# Harbor oracle solution for titlecase-go.
# Writes a correct Go port of python-titlecase into /workspace/repo,
# then removes all .py files.

set -euo pipefail

REPO=/workspace/repo

# ---------------------------------------------------------------------------
# 1. Write go.mod
# ---------------------------------------------------------------------------
cat > "$REPO/go.mod" <<'GOMOD'
module titlecase

go 1.23
GOMOD

# ---------------------------------------------------------------------------
# 2. Write the Go source: main.go
#
# This is a faithful line-by-line port of titlecase/__init__.py.
#
# Key Python→Go translation decisions:
#
#  MAC_MC:      Python r"^([Mm]c|MC)(\w.+)" — NOT case-insensitive; only matches
#               the exact alternatives [Mm]c or MC. We replicate this exactly.
#               The original does NOT match "mac"/"Mac"/"MAC".
#
#  UC_INITIALS: Python r"^(?:[A-Z]\.|[A-Z]\.[A-Z])+$" — matches one or more
#               of (letter+dot) or (letter+dot+letter).  Examples: A. A.B D.C.
#               We replicate with a single RE2-compatible pattern.
#
#  APOS_SECOND: Python uses character indices 0/1/2/3 on the matched word.
#               We replicate that directly after matching the regex.
#
#  all_caps:    Python uses line.upper()==line, which is true even for
#               whitespace-only or digit-only lines.  We replicate that.
#
#  consonants:  Python uses regex.search(r'\A[CONSONANTS]+\Z', word) on the
#               word AFTER the all_caps→lower step, with no stripping of
#               punctuation.  We replicate that (no TrimFunc).
#
#  SUBPHRASE:   Python r'([:.;?!\-–‒—―][ ])(%s)' — the hyphen and four dashes.
#               Capitalizes the following small word.
# ---------------------------------------------------------------------------
cat > "$REPO/main.go" <<'GOEOF'
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
	"unicode/utf8"
)

// smallWordRaw is the Python SMALL constant, used to build regexps.
const smallWordRaw = `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`

// punctClass is the content of a character class [...] matching Python's PUNCT set.
// Python PUNCT = r"""!""#$%&''()*+,\-–‒—―./:;?@[\\\]_`{|}~"""
// Written as a Go raw-string safe for use inside regexp [...].
// Hyphen is placed at the start to avoid range interpretation.
// Backslash is doubled. Brackets are escaped.
const punctClass = `\-!"#$%&` + `''` + `()*+,–‒—―./:;?@\[\\\]_` + "`" + `{|}~`

var (
	// reSmallWords: ^(small_word)$  case-insensitive
	reSmallWords = regexp.MustCompile(`(?i)^(` + smallWordRaw + `)$`)

	// reSubphrase: ([:.;?!-–‒—―] )(small_word)  — note: NOT case-insensitive
	// Python: SUBPHRASE = regex.compile(r'([:.;?!\-–‒—―][ ])(%s)' % SMALL)
	// The SMALL match in SUBPHRASE is NOT case-insensitive in Python (no regex.I).
	reSubphrase = regexp.MustCompile(`([:.;?!\x2D\x{2013}\x{2014}\x{2012}\x{2015}] )(` + smallWordRaw + `)`)

	// reMacMc: Python r"^([Mm]c|MC)(\w.+)"  — exact alternatives, no (?i)
	// Matches: Mc, mc, MC  — does NOT match mac, Mac, MAC, mAc, mC, etc.
	reMacMc = regexp.MustCompile(`^([Mm]c|MC)(\w.+)`)

	// reMrMrsMsDr: Python r"^((m((rs?)|s))|Dr)$"  case-insensitive
	reMrMrsMsDr = regexp.MustCompile(`(?i)^((m((rs?)|s))|Dr)$`)

	// reInlinePeriod: letter . letter  (uses \w in Python re fallback)
	reInlinePeriod = regexp.MustCompile(`(?i)\w[.]\w`)

	// reUCElsewhere: Python (re fallback) r'[PUNCT]*?[a-zA-Z]+[A-Z]+?'
	// Used with .match() so anchored at start.
	// Matches words that already contain an uppercase letter after the first.
	reUCElsewhere = regexp.MustCompile(`^[` + punctClass + `]*[a-zA-Z]+[A-Z]+`)

	// reUCInitials: Python (re fallback) r"^(?:[A-Z]\.|[A-Z]\.[A-Z])+$"
	// Matches one or more occurrences of (A.) or (A.B) — e.g. A. A.B D.C. A.B.
	reUCInitials = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)

	// reAposSecond: Python (re fallback) r"^[dol][''][\w]+(?:['s]{2})?$"  case-insensitive
	// We capture group 1 = first char, to check vowel status.
	reAposSecond = regexp.MustCompile(`(?i)^([dol])([''])(\w+(?:['s]{2})?)$`)

	// reCapFirst: Python (re fallback) r"^[PUNCT]*?([\w])"
	// Finds the first word character after optional leading punctuation.
	reCapFirst = regexp.MustCompile(`^[` + punctClass + `]*(\w)`)

	// reSmallFirst: Python r'^([PUNCT]*)(%s)\b'  case-insensitive
	reSmallFirst = regexp.MustCompile(`(?i)^([` + punctClass + `]*)(` + smallWordRaw + `)\b`)

	// reSmallLast: Python r'\b(%s)[PUNCT]?$'  case-insensitive
	reSmallLast = regexp.MustCompile(`(?i)\b(` + smallWordRaw + `)[` + punctClass + `]?$`)

	// reConsonants: Python r'\A[CONSONANTS]+\Z'  case-insensitive
	// Python CONSONANTS = ascii_lowercase - {a,e,i,o,u,y}
	reConsonants = regexp.MustCompile(`(?i)^[bcdfghjklmnpqrstvwxz]+$`)
)

// vowelSet is the Python 'aeiouAEIOU' set.
const vowelSet = "aeiouAEIOU"

// isVowel reports whether r is in the Python vowel set.
func isVowel(r rune) bool {
	return strings.ContainsRune(vowelSet, r)
}

// pyAllCaps replicates Python's  all_caps = line.upper() == line
// A line is all-caps if its Unicode upper-case form equals itself.
// This is true for whitespace-only, digit-only, punctuation-only, and
// genuinely all-uppercase strings.
func pyAllCaps(s string) bool {
	return strings.ToUpper(s) == s
}

// capitalize replicates Python's str.capitalize(): upper first char, lower rest.
func capitalize(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + strings.ToLower(s[size:])
}

// ucFirst uppercases only the very first rune, leaving the rest unchanged.
// Used for Mr/Mrs/Ms/Dr rule: word[0].upper() + word[1:]
func ucFirst(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + s[size:]
}

// capFirstWordChar replicates Python's CAPFIRST.sub(lambda m: m.group(0).upper(), word).
// It uppercases the first \w character, leaving leading punctuation intact.
func capFirstWordChar(s string) string {
	sub := reCapFirst.FindStringSubmatchIndex(s)
	if sub == nil {
		return s
	}
	// sub[2]..sub[3] is the captured (\w) group — the first word character.
	g1s, g1e := sub[2], sub[3]
	r, _ := utf8.DecodeRuneInString(s[g1s:])
	return s[:g1s] + string(unicode.ToUpper(r)) + s[g1e:]
}

// splitPreservingSep splits s on whitespace, returning alternating
// [word, sep, word, sep, ...] in the same style as Python's
//   regex.split(r'(\s)', line)
// which returns [word0, sep0, word1, sep1, ..., wordN].
func splitPreservingSep(line string) (words []string, spaces []string) {
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
	// len(words) == len(spaces)+1, matching Python's split behaviour.
	return words, spaces
}

// titlecaseWord processes a single non-whitespace token.
// allCaps: whether the entire source line was all-caps (Python's all_caps).
// This function does NOT apply the small-first / small-last line rules.
func titlecaseWord(word string, allCaps bool) string {
	// --- APOS_SECOND ---
	// Python: if APOS_SECOND.match(word):
	//             if word[0] not in 'aeiouAEIOU':
	//                 word = word[0].lower() + word[1] + word[2].upper() + word[3:]
	//             else:
	//                 word = word[0].upper() + word[1] + word[2].upper() + word[3:]
	// Indices 0=first_char, 1=apostrophe, 2=first_name_letter, 3+=rest
	if m := reAposSecond.FindStringSubmatch(word); m != nil {
		// m[1]=first_char  m[2]=apostrophe  m[3]=rest_after_apostrophe
		firstChar := rune(m[1][0]) // ASCII d/o/l (the regex only matches ASCII)
		apos := m[2]
		rest := m[3]
		// word[2] = first rune of rest; word[3:] = rest[1 rune:]
		r2, r2size := utf8.DecodeRuneInString(rest)
		restTail := rest[r2size:]
		if isVowel(firstChar) {
			return string(unicode.ToUpper(firstChar)) + apos + string(unicode.ToUpper(r2)) + restTail
		}
		return string(unicode.ToLower(firstChar)) + apos + string(unicode.ToUpper(r2)) + restTail
	}

	// --- MAC_MC ---
	// Python: MAC_MC = regex.compile(r"^([Mm]c|MC)(\w.+)")
	// capitalize() on group(1), then titlecase(group(2)) recursively with small_first_last=True
	if m := reMacMc.FindStringSubmatch(word); m != nil {
		prefix := capitalize(m[1])            // Mc or MC→Mc
		suffix := titlecaseLine(m[2], true)   // recursive, small_first_last=True
		return prefix + suffix
	}

	// --- MR_MRS_MS_DR ---
	// Python: word = word[0].upper() + word[1:]
	if reMrMrsMsDr.MatchString(word) {
		return ucFirst(word)
	}

	// --- INLINE_PERIOD ---
	if reInlinePeriod.MatchString(word) {
		return word
	}

	// --- UC_ELSEWHERE (only when NOT all_caps) ---
	if !allCaps && reUCElsewhere.MatchString(word) {
		return word
	}

	// --- SMALL_WORDS ---
	if reSmallWords.MatchString(word) {
		return strings.ToLower(word)
	}

	// --- SLASH (single slash, not //) ---
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, p := range parts {
			parts[i] = titlecaseLine(p, false)
		}
		return strings.Join(parts, "/")
	}

	// --- HYPHEN ---
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts {
			parts[i] = titlecaseLine(p, false)
		}
		return strings.Join(parts, "-")
	}

	// --- ALL CAPS: lowercase the word first ---
	if allCaps {
		word = strings.ToLower(word)
	}

	// --- ALL CONSONANTS acronym (len > 2) ---
	// Python: regex.search(r'\A[CONSONANTS]+\Z', word)  on word after lowercasing
	// then:   len(word) > 2
	if reConsonants.MatchString(word) && utf8.RuneCountInString(word) > 2 {
		return strings.ToUpper(word)
	}

	// --- Default: capitalise first letter ---
	return capFirstWordChar(word)
}

// titlecaseLine processes one line of text, applying all rules.
// smallFirstLast controls the first/last-word capitalisation (false when recursing).
func titlecaseLine(line string, smallFirstLast bool) string {
	if line == "" {
		return ""
	}

	allCaps := pyAllCaps(line)

	words, spaces := splitPreservingSep(line)
	processed := make([]string, len(words))

	for i, word := range words {
		if word == "" {
			processed[i] = ""
			continue
		}

		// --- UC_INITIALS guard (only when all_caps line) ---
		// Python: if all_caps: if UC_INITIALS.match(word): tc_line.append(word); continue
		if allCaps && reUCInitials.MatchString(word) {
			processed[i] = word
			continue
		}

		processed[i] = titlecaseWord(word, allCaps)
	}

	// --- small_first_last: capitalise first word if it's a small word ---
	// Python: tc_line[0] = SMALL_FIRST.sub(lambda m: m.group(1)+m.group(2).capitalize(), tc_line[0])
	if smallFirstLast && len(processed) > 0 {
		first := processed[0]
		if m := reSmallFirst.FindStringSubmatchIndex(first); m != nil {
			// m[2]..m[3] = leading punct, m[4]..m[5] = small word
			leadPunct := first[m[2]:m[3]]
			smallWord := first[m[4]:m[5]]
			// Replace only the matched portion (the rest of first stays).
			matchEnd := m[1]
			processed[0] = leadPunct + capitalize(smallWord) + first[matchEnd:]
		}
	}

	// --- small_first_last: capitalise last word if it's a small word ---
	// Python: tc_line[-1] = SMALL_LAST.sub(lambda m: m.group(0).capitalize(), tc_line[-1])
	if smallFirstLast && len(processed) > 0 {
		last := processed[len(processed)-1]
		processed[len(processed)-1] = reSmallLast.ReplaceAllStringFunc(last, func(m string) string {
			return capitalize(m)
		})
	}

	// --- Reassemble preserving original whitespace ---
	var sb strings.Builder
	for i, w := range processed {
		sb.WriteString(w)
		if i < len(spaces) {
			sb.WriteString(spaces[i])
		}
	}
	result := sb.String()

	// --- SUBPHRASE: capitalise small word after [:;.?!-–‒—―] + space ---
	// Python: SUBPHRASE.sub(lambda m: m.group(1)+m.group(2).capitalize(), result)
	result = reSubphrase.ReplaceAllStringFunc(result, func(m string) string {
		sub := reSubphrase.FindStringSubmatch(m)
		if sub == nil {
			return m
		}
		return sub[1] + capitalize(sub[2])
	})

	return result
}

// Titlecase is the top-level entry point for a single input line.
// Each call processes exactly one line (the main loop already splits on \n).
func Titlecase(text string) string {
	return titlecaseLine(text, true)
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		fmt.Fprintln(writer, Titlecase(scanner.Text()))
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, "read error:", err)
		os.Exit(1)
	}
}
GOEOF

# ---------------------------------------------------------------------------
# 3. Remove every .py file from the repo
# ---------------------------------------------------------------------------
find "$REPO" -name "*.py" -delete
echo "All .py files removed."

# ---------------------------------------------------------------------------
# 4. Verify the build passes
# ---------------------------------------------------------------------------
cd "$REPO"
go build ./...
echo "Build succeeded."
