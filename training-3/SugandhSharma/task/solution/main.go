// Go port of titlecase() from python-titlecase 2.4.1 (commit 42f43e2de55b), on the code path the
// original takes when the optional "regex" package is not installed (REGEX_AVAILABLE is False).
//
// The program reads titles from standard input, one per line, and writes the title-cased form of
// each line to standard output. Every rule below carries the Python line it was ported from, and
// the rules run in the same order as in the Python code.
package main

import (
	"bufio"
	"io"
	"os"
	"regexp"
	"strings"
	"unicode"
	"unicode/utf8"
)

// SMALL = r'a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?'
const small = `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`

// PUNCT, written as the body of a character class. The Python list holds the left curly quotes
// U+201C and U+2018 and the dashes U+2013, U+2012, U+2014, U+2015. It does not hold < = > ^.
const punct = `!"\x{201C}#$%&'\x{2018}()*+,\-\x{2013}\x{2012}\x{2014}\x{2015}./:;?@\[\\\]_` + "`" + `{|}~`

var (
	// SMALL_WORDS = re.compile(r'^(%s)$' % SMALL, re.I)
	smallWords = regexp.MustCompile(`(?i)^(` + small + `)$`)
	// SMALL_FIRST = re.compile(r'^([%s]*)(%s)\b' % (PUNCT, SMALL), re.I)
	smallFirst = regexp.MustCompile(`(?i)^([` + punct + `]*)(` + small + `)\b`)
	// SMALL_LAST = re.compile(r'\b(%s)[%s]?$' % (SMALL, PUNCT), re.I)
	smallLast = regexp.MustCompile(`(?i)\b(` + small + `)[` + punct + `]?$`)
	// SUBPHRASE = re.compile(r'([:.;?!\-...][ ])(%s)' % SMALL)   case-sensitive, no boundary at the end
	subphrase = regexp.MustCompile(`([:.;?!\-\x{2013}\x{2012}\x{2014}\x{2015}][ ])(` + small + `)`)
	// MAC_MC = re.compile(r"^([Mm]c|MC)(\w.+)")
	macMc = regexp.MustCompile(`^([Mm]c|MC)(\w.+)`)
	// MR_MRS_MS_DR = re.compile(r"^((m((rs?)|s))|Dr)$", re.I)
	mrMrsMsDr = regexp.MustCompile(`(?i)^((m((rs?)|s))|Dr)$`)
	// INLINE_PERIOD = re.compile(r'[\w][.][\w]', re.I)
	inlinePeriod = regexp.MustCompile(`\w[.]\w`)
	// UC_ELSEWHERE = re.compile(r'[%s]*?[a-zA-Z]+[A-Z]+?' % PUNCT)   used with match(): anchored at the start
	ucElsewhere = regexp.MustCompile(`^[` + punct + `]*?[a-zA-Z]+[A-Z]+?`)
	// CAPFIRST = re.compile(r"^[%s]*?([\w])" % PUNCT)
	capFirst = regexp.MustCompile(`^[` + punct + `]*?(\w)`)
	// APOS_SECOND = re.compile(r"^[dol]['‘][\w]+(?:['s]{2})?$", re.I)
	aposSecond = regexp.MustCompile(`(?i)^[dol]['\x{2018}]\w+(?:['s]{2})?$`)
	// UC_INITIALS = re.compile(r"^(?:[A-Z]\.|[A-Z]\.[A-Z])+$")
	ucInitials = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
	// re.search(r'\A[' + CONSONANTS + r']+\Z', word, flags=re.IGNORECASE)   every letter but a e i o u y
	allConsonants = regexp.MustCompile(`(?i)\A[bcdfghjklmnpqrstvwxz]+\z`)
)

// capitalize does what Python's str.capitalize() does: the first character in upper case and
// ALL the others in lower case.
func capitalize(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return strings.ToUpper(string(r)) + strings.ToLower(s[size:])
}

// isSpace reports what Python's \s matches in a str pattern.
func isSpace(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

// titlecase ports titlecase(text, callback=None, small_first_last) for one line of text.
func titlecase(line string, smallFirstLast bool) string {
	// all_caps = line.upper() == line
	allCaps := strings.ToUpper(line) == line

	// split_line = re.split(r'(\s)', line); words = split_line[::2]; spaces = split_line[1::2]
	var words, spaces []string
	start := 0
	for i, r := range line {
		if isSpace(r) {
			words = append(words, line[start:i])
			spaces = append(spaces, string(r))
			start = i + utf8.RuneLen(r)
		}
	}
	words = append(words, line[start:])

	tcLine := make([]string, len(words))
	for i, word := range words {
		tcLine[i] = titleWord(word, allCaps)
	}

	// if small_first_last and tc_line:
	if smallFirstLast {
		// tc_line[0] = SMALL_FIRST.sub(lambda m: '%s%s' % (m.group(1), m.group(2).capitalize()), tc_line[0])
		if m := smallFirst.FindStringSubmatchIndex(tcLine[0]); m != nil {
			w := tcLine[0]
			tcLine[0] = w[:m[4]] + capitalize(w[m[4]:m[5]]) + w[m[5]:]
		}
		// tc_line[-1] = SMALL_LAST.sub(lambda m: m.group(0).capitalize(), tc_line[-1])
		last := len(tcLine) - 1
		if m := smallLast.FindStringIndex(tcLine[last]); m != nil {
			w := tcLine[last]
			tcLine[last] = w[:m[0]] + capitalize(w[m[0]:m[1]]) + w[m[1]:]
		}
	}

	// result = "".join(words and spaces, in their original order)
	var joined strings.Builder
	for i, w := range tcLine {
		joined.WriteString(w)
		if i < len(spaces) {
			joined.WriteString(spaces[i])
		}
	}
	result := joined.String()

	// result = SUBPHRASE.sub(lambda m: '%s%s' % (m.group(1), m.group(2).capitalize()), result)
	matches := subphrase.FindAllStringSubmatchIndex(result, -1)
	if matches == nil {
		return result
	}
	var out strings.Builder
	pos := 0
	for _, m := range matches {
		out.WriteString(result[pos:m[4]])
		out.WriteString(capitalize(result[m[4]:m[5]]))
		pos = m[5]
	}
	out.WriteString(result[pos:])
	return out.String()
}

// titleWord applies the word rules of the loop "for word in words:" in the Python order.
func titleWord(word string, allCaps bool) string {
	// if all_caps: if UC_INITIALS.match(word): keep the word
	if allCaps && ucInitials.MatchString(word) {
		return word
	}

	// if APOS_SECOND.match(word): d'Artagnan, l'Amour, O'Brien; the rest of the word is left as typed
	if aposSecond.MatchString(word) {
		r := []rune(word)
		first := string(r[0])
		if strings.ContainsRune("aeiouAEIOU", r[0]) {
			first = strings.ToUpper(first)
		} else {
			first = strings.ToLower(first)
		}
		return first + string(r[1]) + strings.ToUpper(string(r[2])) + string(r[3:])
	}

	// match = MAC_MC.match(word): "%s%s" % (match.group(1).capitalize(), titlecase(match.group(2), callback, True))
	if m := macMc.FindStringSubmatch(word); m != nil {
		return capitalize(m[1]) + titlecase(m[2], true)
	}

	// match = MR_MRS_MS_DR.match(word): word[0].upper() + word[1:]
	if mrMrsMsDr.MatchString(word) {
		r, size := utf8.DecodeRuneInString(word)
		return strings.ToUpper(string(r)) + word[size:]
	}

	// if INLINE_PERIOD.search(word) or (not all_caps and UC_ELSEWHERE.match(word)): keep the word
	if inlinePeriod.MatchString(word) || (!allCaps && ucElsewhere.MatchString(word)) {
		return word
	}

	// if SMALL_WORDS.match(word): word.lower()
	if smallWords.MatchString(word) {
		return strings.ToLower(word)
	}

	// if "/" in word and "//" not in word: each part is its own title, small_first_last off
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		return titleParts(word, "/")
	}

	// if '-' in word: each part is its own title, small_first_last off
	if strings.Contains(word, "-") {
		return titleParts(word, "-")
	}

	// if all_caps: word = word.lower()
	if allCaps {
		word = strings.ToLower(word)
	}

	// if is_all_consonants and len(word) > 2: word.upper()
	if utf8.RuneCountInString(word) > 2 && allConsonants.MatchString(word) {
		return strings.ToUpper(word)
	}

	// CAPFIRST.sub(lambda m: m.group(0).upper(), word)
	if m := capFirst.FindStringIndex(word); m != nil {
		return strings.ToUpper(word[:m[1]]) + word[m[1]:]
	}
	return word
}

// titleParts ports  sep.join(titlecase(t, callback, False) for t in word.split(sep)).
func titleParts(word, sep string) string {
	parts := strings.Split(word, sep)
	for i, part := range parts {
		parts[i] = titlecase(part, false)
	}
	return strings.Join(parts, sep)
}

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Stderr.WriteString("cannot read standard input: " + err.Error() + "\n")
		os.Exit(1)
	}
	lines := strings.Split(string(data), "\n")
	if n := len(lines); n > 0 && lines[n-1] == "" {
		lines = lines[:n-1] // the text after the last newline is not a line
	}
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for _, line := range lines {
		out.WriteString(titlecase(line, true))
		out.WriteByte('\n')
	}
}
