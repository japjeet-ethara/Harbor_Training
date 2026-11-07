package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
)

// Patterns copied from the stdlib-re fallback in python-titlecase.
// That path has no look-ahead, look-behind, or back-references.
var (
	smallWords = regexp.MustCompile("(?i)^(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\\.?|via|vs\\.?)$")
	smallFirst = regexp.MustCompile("(?i)^([!\"\u201c#$%&'\u2018()*+,\\-\u2013\u2012\u2014\u2015./:;?@[\\\\\\]_`{|}~]*)(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\\.?|via|vs\\.?)\\b")
	smallLast  = regexp.MustCompile("(?i)\\b(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\\.?|via|vs\\.?)[!\"\u201c#$%&'\u2018()*+,\\-\u2013\u2012\u2014\u2015./:;?@[\\\\\\]_`{|}~]?$")
	subphrase  = regexp.MustCompile("([:.;?!\\-\u2013\u2012\u2014\u2015][ ])(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\\.?|via|vs\\.?)")
	macMC      = regexp.MustCompile("^([Mm]c|MC)(\\w.+)")
	mrMrs      = regexp.MustCompile("(?i)^((m((rs?)|s))|Dr)$")
	inlinePeriod = regexp.MustCompile("(?i)[\\w][.][\\w]")
	ucElsewhere  = regexp.MustCompile("\\A[!\"\u201c#$%&'\u2018()*+,\\-\u2013\u2012\u2014\u2015./:;?@[\\\\\\]_`{|}~]*?[a-zA-Z]+[A-Z]+?")
	capFirst     = regexp.MustCompile("^[!\"\u201c#$%&'\u2018()*+,\\-\u2013\u2012\u2014\u2015./:;?@[\\\\\\]_`{|}~]*?([\\w])")
	aposSecond   = regexp.MustCompile("(?i)^[dol]['\u2018][\\w]+(?:['s]{2})?$")
	ucInitials   = regexp.MustCompile("^(?:[A-Z]\\.|[A-Z]\\.[A-Z])+$")
	consonants   = regexp.MustCompile("(?i)\\A[bcdfghjklmnpqrstvwxz]+\\z")
	lineSep      = regexp.MustCompile(`[\r\n]+`)
	spaceSep     = regexp.MustCompile(`\s`)
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 0, 1024*1024), 10*1024*1024)
	for scanner.Scan() {
		fmt.Println(TitleCase(scanner.Text(), true))
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func TitleCase(text string, smallFirstLast bool) string {
	lines := lineSep.Split(text, -1)
	if len(lines) == 0 {
		lines = []string{""}
	}
	processed := make([]string, len(lines))
	for i, line := range lines {
		processed[i] = processLine(line, smallFirstLast)
	}
	return strings.Join(processed, "\n")
}

func processLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitWS(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = processWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return subphraseReplace(reassemble(tc, spaces))
}

func processWord(word string, allCaps bool) string {
	if allCaps && ucInitials.MatchString(word) {
		return word
	}
	if aposSecond.MatchString(word) {
		r := []rune(word)
		if !isVowel(r[0]) {
			r[0] = unicode.ToLower(r[0])
		} else {
			r[0] = unicode.ToUpper(r[0])
		}
		r[2] = unicode.ToUpper(r[2])
		return string(r)
	}
	if m := macMC.FindStringSubmatch(word); m != nil {
		return capitalize(m[1]) + TitleCase(m[2], true)
	}
	if mrMrs.MatchString(word) {
		r := []rune(word)
		r[0] = unicode.ToUpper(r[0])
		return string(r)
	}
	if inlinePeriod.MatchString(word) || (!allCaps && ucElsewhere.MatchString(word)) {
		return word
	}
	if smallWords.MatchString(word) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = TitleCase(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = TitleCase(part, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if consonants.MatchString(word) && utfLen(word) > 2 {
		return strings.ToUpper(word)
	}
	return applyCapFirst(word)
}

func applyCapFirst(word string) string {
	loc := capFirst.FindStringIndex(word)
	if loc == nil {
		return word
	}
	return strings.ToUpper(word[loc[0]:loc[1]]) + word[loc[1]:]
}

func applySmallFirst(word string) string {
	loc := smallFirst.FindStringSubmatchIndex(word)
	if loc == nil {
		return word
	}
	return word[:loc[0]] + word[loc[2]:loc[3]] + capitalize(word[loc[4]:loc[5]]) + word[loc[1]:]
}

func applySmallLast(word string) string {
	loc := smallLast.FindStringSubmatchIndex(word)
	if loc == nil {
		return word
	}
	return word[:loc[0]] + capitalize(word[loc[0]:loc[1]]) + word[loc[1]:]
}

func subphraseReplace(s string) string {
	locs := subphrase.FindAllStringSubmatchIndex(s, -1)
	if len(locs) == 0 {
		return s
	}
	var b strings.Builder
	last := 0
	for _, loc := range locs {
		b.WriteString(s[last:loc[0]])
		b.WriteString(s[loc[2]:loc[3]])
		b.WriteString(capitalize(s[loc[4]:loc[5]]))
		last = loc[1]
	}
	b.WriteString(s[last:])
	return b.String()
}

func splitWS(s string) (words, spaces []string) {
	idxs := spaceSep.FindAllStringIndex(s, -1)
	if len(idxs) == 0 {
		return []string{s}, nil
	}
	parts := make([]string, 0, len(idxs)*2+1)
	last := 0
	for _, m := range idxs {
		parts = append(parts, s[last:m[0]], s[m[0]:m[1]])
		last = m[1]
	}
	parts = append(parts, s[last:])
	for i, part := range parts {
		if i%2 == 0 {
			words = append(words, part)
		} else {
			spaces = append(spaces, part)
		}
	}
	return words, spaces
}

func reassemble(words, spaces []string) string {
	n := len(words) + len(spaces)
	joined := make([]string, n)
	wi := 0
	for i := 0; i < n; i += 2 {
		joined[i] = words[wi]
		wi++
	}
	si := 0
	for i := 1; i < n; i += 2 {
		joined[i] = spaces[si]
		si++
	}
	return strings.Join(joined, "")
}

func capitalize(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return s
	}
	r[0] = unicode.ToUpper(r[0])
	for i := 1; i < len(r); i++ {
		r[i] = unicode.ToLower(r[i])
	}
	return string(r)
}

func isVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func utfLen(s string) int {
	n := 0
	for range s {
		n++
	}
	return n
}
