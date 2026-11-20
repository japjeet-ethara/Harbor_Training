package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
)

// In Python:
// SMALL = r'a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.|v|via|vs\.|vs'
// PUNCT = r"""!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~"""

const punct = `!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`{|}~"

var (
	// SMALL_WORDS = regex.compile(r'^(%s)$' % SMALL, regex.I)
	smallWordsRegex = regexp.MustCompile(`^(?i:a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.|v|via|vs\.|vs)$`)

	// SMALL_FIRST = regex.compile(r'^([%s]*)(%s)\b' % (PUNCT, SMALL), regex.I)
	smallFirstRegex = regexp.MustCompile(`^(?i:([!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}\~]*)(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.|v|via|vs\.|vs)\b)`)

	// SMALL_LAST = regex.compile(r'\b(%s)[%s]?$' % (SMALL, PUNCT), regex.I)
	smallLastRegex = regexp.MustCompile(`(?i:\b(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.|v|via|vs\.|vs)[!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}\~]?)$`)

	// SUBPHRASE = regex.compile(r'([:.;?!\-–‒—―][ ])(%s)' % SMALL)
	// Note: in Python, SUBPHRASE does NOT have regex.I flag!
	subphraseRegex = regexp.MustCompile(`([:.;?!\-–‒—―] )(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.|v|via|vs\.|vs)`)

	// MAC_MC = regex.compile(r"^([Mm]c|MC)(\w.+)")
	macMcRegex = regexp.MustCompile(`^([Mm]c|MC)(\w.+)`)

	// MR_MRS_MS_DR = regex.compile(r"^((m((rs?)|s))|Dr)$", regex.I)
	mrMrsMsDrRegex = regexp.MustCompile(`^(?i:(m((rs?)|s))|Dr)$`)

	// INLINE_PERIOD: [\w][.][\w]
	inlinePeriodRegex = regexp.MustCompile(`(?i:[\p{L}0-9_]\.[\p{L}0-9_])`)

	// UC_ELSEWHERE: [%s]*?[a-zA-Z]+[A-Z]+? % PUNCT
	ucElsewhereRegex = regexp.MustCompile(`^[!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}\~]*?[a-zA-Z]+[A-Z]+`)

	// CAPFIRST = regex.compile(r"^[%s]*?([\w])" % PUNCT)
	capfirstRegex = regexp.MustCompile(`^([!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}\~]*?)([\p{L}0-9_])`)

	// APOS_SECOND = regex.compile(r"^[dol]{1}['‘]{1}[\w]+(?:['s]{2})?$", regex.I)
	aposSecondRegex = regexp.MustCompile(`^(?i:[dol]['‘][\p{L}0-9_]+(?:['’]s)?)$`)

	// UC_INITIALS = regex.compile(r"^(?:[\p{Uppercase_Letter}]{1}\.{1}|[\p{Uppercase_Letter}]{1}\.{1}[\p{Uppercase_Letter}]{1})+$")
	ucInitialsRegex = regexp.MustCompile(`^(?:(?:\p{Lu}\.|\p{Lu}\.\p{Lu}))+$`)

	// CONSONANTS: string.ascii_lowercase - {'a','e','i','o','u','y'}
	// \A[consonants]+\Z
	allConsonantsRegex = regexp.MustCompile(`^(?i:[bcdfghjklmnpqrstvwxz]+)$`)

	// whitespace splitter
	whitespaceRegex = regexp.MustCompile(`\s`)
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
	// In Python: lines = regex.split('[\r\n]+', text)
	// On line-by-line input, text has no newlines
	lines := strings.Split(text, "\n")
	var processed []string

	for _, line := range lines {
		allCaps := strings.ToUpper(line) == line

		// split_line = regex.split(r'(\s)', line)
		// We preserve whitespace tokens exactly
		var words []string
		var spaces []string

		runes := []rune(line)
		n := len(runes)
		i := 0
		inSpace := false
		var cur []rune

		for i < n {
			isSp := unicode.IsSpace(runes[i])
			if i == 0 {
				inSpace = isSp
			}
			if isSp == inSpace {
				cur = append(cur, runes[i])
			} else {
				if inSpace {
					spaces = append(spaces, string(cur))
				} else {
					words = append(words, string(cur))
				}
				cur = []rune{runes[i]}
				inSpace = isSp
			}
			i++
		}
		if len(cur) > 0 {
			if inSpace {
				spaces = append(spaces, string(cur))
			} else {
				words = append(words, string(cur))
			}
		}

		// Realign so words is split_line[::2] and spaces is split_line[1::2]
		// In python: regex.split(r'(\s)', line)
		// If line begins with space: words[0] = "", spaces[0] = space_char, words[1] = ...
		var pWords []string
		var pSpaces []string

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
				// space token (single whitespace char in Python's regex.split(r'(\s)', line))
				// Wait! In Python, r'(\s)' splits on EVERY single whitespace character!
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

			// CAPFIRST.sub(lambda m: m.group(0).upper(), word)
			tcLine[wi] = capfirstRegex.ReplaceAllStringFunc(word, func(m string) string {
				sub := capfirstRegex.FindStringSubmatch(m)
				if len(sub) >= 3 {
					return sub[1] + strings.ToUpper(sub[2])
				}
				return strings.ToUpper(m)
			})
		}

		if smallFirstLast && len(tcLine) > 0 {
			if sub := smallFirstRegex.FindStringSubmatchIndex(tcLine[0]); sub != nil {
				g1 := tcLine[0][sub[2]:sub[3]]
				g2 := tcLine[0][sub[4]:sub[5]]
				tcLine[0] = g1 + capitalize(g2) + tcLine[0][sub[1]:]
			}

			lastIdx := len(tcLine) - 1
			if sub := smallLastRegex.FindStringSubmatchIndex(tcLine[lastIdx]); sub != nil {
				g1 := tcLine[lastIdx][sub[2]:sub[3]]
				tcLine[lastIdx] = tcLine[lastIdx][:sub[0]] + capitalize(g1) + tcLine[lastIdx][sub[3]:]
			}
		}

		// Recombine words and spaces
		var sb strings.Builder
		for idx, w := range tcLine {
			sb.WriteString(w)
			if idx < len(pSpaces) {
				sb.WriteString(pSpaces[idx])
			}
		}
		res := sb.String()

		// SUBPHRASE.sub(lambda m: '%s%s' % (m.group(1), m.group(2).capitalize()), result)
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
