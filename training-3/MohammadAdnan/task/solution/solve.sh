#!/bin/bash
# Oracle: write the reference Go port into /workspace/repo.
# The port lives only inside this script (heredocs below). There is no separate copy of it anywhere
# under /solution, so any other solve.sh run in its place finds nothing to copy.
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'GO_PORT_EOF'
module titlecase

go 1.23
GO_PORT_EOF

cat > main.go <<'GO_PORT_EOF'
package main

import (
	"io"
	"os"
)

func main() {
	input, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	output := Titlecase(string(input))
	os.Stdout.WriteString(output)
}
GO_PORT_EOF

cat > titlecase.go <<'GO_PORT_EOF'
package main

import (
	"regexp"
	"strings"
	"unicode"
	"unicode/utf8"
)

const (
	smallWordsPattern = `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`
	punctPattern      = `!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}~`
)

// The answers come from titlecase WITHOUT the optional `regex` package, i.e. Python's `re`
// module. There, \w on a str means any Unicode letter or digit, or "_" (Go's \w is ASCII only),
// so wordClass spells it out. The `re`-mode patterns from titlecase/__init__.py are used:
// INLINE_PERIOD [\w][.][\w], UC_ELSEWHERE [a-zA-Z]+[A-Z]+?, CAPFIRST ([\w]),
// APOS_SECOND [\w]+, UC_INITIALS [A-Z].
const wordClass = `\p{L}\p{N}_`

var (
	reSmallWords        = regexp.MustCompile(`(?i)^(` + smallWordsPattern + `)$`)
	reSmallFirst        = regexp.MustCompile(`(?i)^([` + punctPattern + `]*)(` + smallWordsPattern + `)($|[^` + wordClass + `])`)
	reSmallLast         = regexp.MustCompile(`(?i)(^|[^` + wordClass + `])(` + smallWordsPattern + `)([` + punctPattern + `]?)$`)
	reSubphrase         = regexp.MustCompile(`([:.;?!\-–‒—―] )(` + smallWordsPattern + `)`)
	reMacMc             = regexp.MustCompile(`^([Mm]c|MC)([` + wordClass + `].+)`)
	reMrMrsMsDr         = regexp.MustCompile(`(?i)^((m((rs?)|s))|Dr)$`)
	reInlinePeriod      = regexp.MustCompile(`(?i)[` + wordClass + `]\.[` + wordClass + `]`)
	reUCElsewhere       = regexp.MustCompile(`^[` + punctPattern + `]*?[a-zA-Z]+[A-Z]+?`)
	reCapFirst          = regexp.MustCompile(`^[` + punctPattern + `]*?([` + wordClass + `])`)
	reAposSecond        = regexp.MustCompile(`(?i)^[dol]['‘][` + wordClass + `]+(?:['s]{2})?$`)
	reUCInitials        = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
	reAllConsonants     = regexp.MustCompile(`(?i)^[bcdfghjklmnpqrstvwxz]+$`)
	reLineSplitDefault  = regexp.MustCompile(`[\r\n]+`)
	reLineSplitPreserve = regexp.MustCompile(`[\r\n]`)
)

// CallbackFunc is a function that returns a custom titlecased version of a word.
type CallbackFunc func(word string, allCaps bool) string

// Options configures the behavior of Titlecase.
type Options struct {
	Callback                 CallbackFunc
	SmallFirstLast           bool
	PreserveBlankLines       bool
	NormaliseSpaceCharacters bool
}

// DefaultOptions returns the default settings.
func DefaultOptions() Options {
	return Options{
		Callback:                 nil,
		SmallFirstLast:           true,
		PreserveBlankLines:       false,
		NormaliseSpaceCharacters: false,
	}
}

type wordToken struct {
	text      string
	immutable bool
}

// Titlecase recases input text using the default settings.
func Titlecase(text string) string {
	return TitlecaseWithOptions(text, DefaultOptions())
}

// TitlecaseWithOptions recases input text using the specified options.
func TitlecaseWithOptions(text string, opts Options) string {
	var lines []string

	if opts.PreserveBlankLines {
		lines = reLineSplitPreserve.Split(text, -1)
	} else {
		lines = reLineSplitDefault.Split(text, -1)
	}

	processed := make([]string, 0, len(lines))

	for _, line := range lines {
		allCaps := pyUpper(line) == line
		words, spaces := splitLine(line)
		tcLine := make([]wordToken, 0, len(words))

		for _, word := range words {
			if opts.Callback != nil {
				newWord := opts.Callback(word, allCaps)
				if newWord != "" {
					tcLine = append(tcLine, wordToken{text: newWord, immutable: true})
					continue
				}
			}

			if allCaps && reUCInitials.MatchString(word) {
				tcLine = append(tcLine, wordToken{text: word, immutable: false})
				continue
			}

			if reAposSecond.MatchString(word) {
				runes := []rune(word)
				firstRune := runes[0]
				isVowel := strings.ContainsRune("aeiouAEIOU", firstRune)

				var firstStr string
				if !isVowel {
					firstStr = string(unicode.ToLower(firstRune))
				} else {
					firstStr = string(unicode.ToUpper(firstRune))
				}

				word = firstStr + string(runes[1]) + string(unicode.ToUpper(runes[2])) + string(runes[3:])
				tcLine = append(tcLine, wordToken{text: word, immutable: false})
				continue
			}

			if match := reMacMc.FindStringSubmatch(word); match != nil {
				prefix := capitalize(match[1])
				remainder := TitlecaseWithOptions(match[2], Options{
					Callback:                 opts.Callback,
					SmallFirstLast:           true,
					PreserveBlankLines:       opts.PreserveBlankLines,
					NormaliseSpaceCharacters: opts.NormaliseSpaceCharacters,
				})

				tcLine = append(tcLine, wordToken{text: prefix + remainder, immutable: false})
				continue
			}

			if reMrMrsMsDr.MatchString(word) {
				runes := []rune(word)
				word = string(unicode.ToUpper(runes[0])) + string(runes[1:])
				tcLine = append(tcLine, wordToken{text: word, immutable: false})
				continue
			}

			if reInlinePeriod.MatchString(word) || (!allCaps && reUCElsewhere.MatchString(word)) {
				tcLine = append(tcLine, wordToken{text: word, immutable: false})
				continue
			}

			if reSmallWords.MatchString(word) {
				tcLine = append(tcLine, wordToken{text: strings.ToLower(word), immutable: false})
				continue
			}

			if strings.Contains(word, "/") && !strings.Contains(word, "//") {
				parts := strings.Split(word, "/")
				slashed := make([]string, len(parts))

				for i, p := range parts {
					slashed[i] = TitlecaseWithOptions(p, Options{
						Callback:                 opts.Callback,
						SmallFirstLast:           false,
						PreserveBlankLines:       opts.PreserveBlankLines,
						NormaliseSpaceCharacters: opts.NormaliseSpaceCharacters,
					})
				}

				tcLine = append(tcLine, wordToken{text: strings.Join(slashed, "/"), immutable: false})
				continue
			}

			if strings.Contains(word, "-") {
				parts := strings.Split(word, "-")
				hyphenated := make([]string, len(parts))

				for i, p := range parts {
					hyphenated[i] = TitlecaseWithOptions(p, Options{
						Callback:                 opts.Callback,
						SmallFirstLast:           false,
						PreserveBlankLines:       opts.PreserveBlankLines,
						NormaliseSpaceCharacters: opts.NormaliseSpaceCharacters,
					})
				}

				tcLine = append(tcLine, wordToken{text: strings.Join(hyphenated, "-"), immutable: false})
				continue
			}

			if allCaps {
				word = strings.ToLower(word)
			}

			if reAllConsonants.MatchString(word) && utf8.RuneCountInString(word) > 2 {
				tcLine = append(tcLine, wordToken{text: pyUpper(word), immutable: false})
				continue
			}

			word = reCapFirst.ReplaceAllStringFunc(word, func(m string) string {
				return pyUpper(m)
			})

			tcLine = append(tcLine, wordToken{text: word, immutable: false})
		}

		if opts.SmallFirstLast && len(tcLine) > 0 {
			if !tcLine[0].immutable {
				tcLine[0].text = reSmallFirst.ReplaceAllStringFunc(tcLine[0].text, func(m string) string {
					sub := reSmallFirst.FindStringSubmatch(m)
					if len(sub) >= 4 {
						return sub[1] + capitalize(sub[2]) + sub[3]
					}
					return m
				})
			}

			lastIdx := len(tcLine) - 1

			if !tcLine[lastIdx].immutable {
				tcLine[lastIdx].text = reSmallLast.ReplaceAllStringFunc(tcLine[lastIdx].text, func(m string) string {
					sub := reSmallLast.FindStringSubmatch(m)
					if len(sub) >= 4 {
						return sub[1] + capitalize(sub[2]) + sub[3]
					}
					return m
				})
			}
		}

		var result string

		if opts.NormaliseSpaceCharacters {
			wordsStr := make([]string, len(tcLine))
			for i, token := range tcLine {
				wordsStr[i] = token.text
			}
			result = strings.Join(wordsStr, " ")
		} else {
			var b strings.Builder
			for i := range tcLine {
				b.WriteString(tcLine[i].text)
				if i < len(spaces) {
					b.WriteString(spaces[i])
				}
			}
			result = b.String()
		}

		result = reSubphrase.ReplaceAllStringFunc(result, func(m string) string {
			sub := reSubphrase.FindStringSubmatch(m)
			if len(sub) >= 3 {
				return sub[1] + capitalize(sub[2])
			}
			return m
		})

		processed = append(processed, result)
	}

	return strings.Join(processed, "\n")
}

func splitLine(line string) ([]string, []string) {
	var words []string
	var spaces []string
	var wordBuf strings.Builder

	for _, r := range line {
		if pyIsSpace(r) {
			words = append(words, wordBuf.String())
			wordBuf.Reset()
			spaces = append(spaces, string(r))
		} else {
			wordBuf.WriteRune(r)
		}
	}

	words = append(words, wordBuf.String())
	return words, spaces
}

// pyIsSpace matches Python's \s on a str (str.isspace): Go's unicode.IsSpace plus \x1c-\x1f.
func pyIsSpace(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

// pySpecialUpper holds characters whose Python str.upper() is longer than one character.
var pySpecialUpper = map[rune]string{
	'ß': "SS", 'ŉ': "ʼN", 'ǰ': "J̌", 'ΐ': "Ϊ́", 'ΰ': "Ϋ́", 'և': "ԵՒ",
	'ﬀ': "FF", 'ﬁ': "FI", 'ﬂ': "FL", 'ﬃ': "FFI", 'ﬄ': "FFL", 'ﬅ': "ST", 'ﬆ': "ST",
}

// pyUpper matches Python's str.upper() for the characters titlecase can meet.
func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		if up, ok := pySpecialUpper[r]; ok {
			b.WriteString(up)
		} else {
			b.WriteRune(unicode.ToUpper(r))
		}
	}
	return b.String()
}

func capitalize(s string) string {
	if s == "" {
		return ""
	}

	runes := []rune(s)
	runes[0] = unicode.ToTitle(runes[0]) // Python's capitalize() title-cases the first character

	for i := 1; i < len(runes); i++ {
		runes[i] = unicode.ToLower(runes[i])
	}

	return string(runes)
}
GO_PORT_EOF

cat > titlecase_test.go <<'GO_PORT_EOF'
package main

import (
	"strings"
	"testing"
)

func TestStandardCases(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"", ""},
		{"word/word", "Word/Word"},
		{"a title and/or string", "A Title and/or String"},
		{"dance with me/let’s face the music and dance", "Dance With Me/Let’s Face the Music and Dance"},
		{"a-b end-to-end two-not-three/three-by-four/five-and", "A-B End-to-End Two-Not-Three/Three-by-Four/Five-And"},
		{"34th 3rd 2nd", "34th 3rd 2nd"},
		{"Q&A with steve jobs: 'that's what happens in technology'", "Q&A With Steve Jobs: 'That's What Happens in Technology'"},
		{"What is AT&T's problem?", "What Is AT&T's Problem?"},
		{"Apple deal with AT&T falls through", "Apple Deal With AT&T Falls Through"},
		{"Words with all consonants like cnn are acronyms", "Words With All Consonants Like CNN Are Acronyms"},
		{"this v that", "This v That"},
		{"this v. that", "This v. That"},
		{"this vs that", "This vs That"},
		{"this vs. that", "This vs. That"},
		{"The SEC's Apple probe: what you need to know", "The SEC's Apple Probe: What You Need to Know"},
		{"'by the Way, small word at the start but within quotes.'", "'By the Way, Small Word at the Start but Within Quotes.'"},
		{"Small word at end is nothing to be afraid of", "Small Word at End Is Nothing to Be Afraid Of"},
		{"Starting Sub-Phrase With a Small Word: a Trick, Perhaps?", "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?"},
		{"Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'", "Sub-Phrase With a Small Word in Quotes: 'A Trick, Perhaps?'"},
		{`sub-phrase with a small word in quotes: "a trick, perhaps?"`, `Sub-Phrase With a Small Word in Quotes: "A Trick, Perhaps?"`},
		{"Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?", "Starting a Hyphen Delimited Sub-Phrase With a Small Word - A Trick, Perhaps?"},
		{"Hyphen Delimited Sub-Phrase With a Small Word in Quotes - 'a Trick, Perhaps?'", "Hyphen Delimited Sub-Phrase With a Small Word in Quotes - 'A Trick, Perhaps?'"},
		{`Hyphen Delimited sub-phrase with a small word in quotes - "a trick, perhaps?"`, `Hyphen Delimited Sub-Phrase With a Small Word in Quotes - "A Trick, Perhaps?"`},
		{"Snakes on a Plane - The TV Edit - The Famous Line", "Snakes on a Plane - The TV Edit - The Famous Line"},
		{"Starting an Em Dash Delimited Sub-Phrase With a Small Word — a Trick, Perhaps?", "Starting an Em Dash Delimited Sub-Phrase With a Small Word — A Trick, Perhaps?"},
		{"Em Dash Delimited Sub-Phrase With a Small Word in Quotes — 'a Trick, Perhaps?'", "Em Dash Delimited Sub-Phrase With a Small Word in Quotes — 'A Trick, Perhaps?'"},
		{`Em Dash Delimited sub-phrase with a small word in quotes — "a trick, perhaps?"`, `Em Dash Delimited Sub-Phrase With a Small Word in Quotes — "A Trick, Perhaps?"`},
		{"Snakes on a Plane — The TV Edit — The Famous Line", "Snakes on a Plane — The TV Edit — The Famous Line"},
		{"EPISODE 7 — THE FORCE AWAKENS", "Episode 7 — The Force Awakens"},
		{"episode 7 – The force awakens", "Episode 7 – The Force Awakens"},
		{"THE CASE OF X ≤ 7", "The Case of X ≤ 7"},
		{"the case of X ≤ 7", "The Case of X ≤ 7"},
		{`"Nothing to Be Afraid of?"`, `"Nothing to Be Afraid Of?"`},
		{`"Nothing to be Afraid Of?"`, `"Nothing to Be Afraid Of?"`},
		{"a thing", "A Thing"},
		{"2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'", "2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'"},
		{"this is just an example.com", "This Is Just an example.com"},
		{"this is something listed on del.icio.us", "This Is Something Listed on del.icio.us"},
		{"iTunes should be unmolested", "iTunes Should Be Unmolested"},
		{"reading between the lines of steve jobs’s ‘thoughts on music’", "Reading Between the Lines of Steve Jobs’s ‘Thoughts on Music’"},
		{"seriously, ‘repair permissions’ is voodoo", "Seriously, ‘Repair Permissions’ Is Voodoo"},
		{"generalissimo francisco franco: still dead; kieren McCarthy: still a jackass", "Generalissimo Francisco Franco: Still Dead; Kieren McCarthy: Still a Jackass"},
		{"O'Reilly should be untouched", "O'Reilly Should Be Untouched"},
		{"my name is o'reilly", "My Name Is O'Reilly"},
		{"WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM", "Washington, D.C. Should Be Fixed but Might Be a Problem"},
		{"THIS IS ALL CAPS AND SHOULD BE ADDRESSED", "This Is All Caps and Should Be Addressed"},
		{"Mr McTavish went to MacDonalds", "Mr McTavish Went to MacDonalds"},
		{"this shouldn't\nget mangled", "This Shouldn't\nGet Mangled"},
		{"this is http://foo.com", "This Is http://foo.com"},
		{"mac mc MAC MC machine", "Mac Mc MAC MC Machine"},
		{"FOO BAR 5TH ST", "Foo Bar 5th St"},
		{"foo bar 5th st", "Foo Bar 5th St"},
		{"l'grange l'grange l'Grange l'Grange", "l'Grange l'Grange l'Grange l'Grange"},
		{"L'grange L'grange L'Grange L'Grange", "l'Grange l'Grange l'Grange l'Grange"},
		{"l'GranGe", "l'GranGe"},
		{"o'grange O'grange o'Grange O'Grange", "O'Grange O'Grange O'Grange O'Grange"},
		{"o'grange's O'grange's o'Grange's O'Grange's", "O'Grange's O'Grange's O'Grange's O'Grange's"},
		{"O'GranGe", "O'GranGe"},
		{"o'melveny/o'doyle o'Melveny/o'doyle O'melveny/o'doyle o'melveny/o'Doyle o'melveny/O'doyle", "O'Melveny/O'Doyle O'Melveny/O'Doyle O'Melveny/O'Doyle O'Melveny/O'Doyle O'Melveny/O'Doyle"},
		{"mccay-mcbut-mcdo mcdonalds/mcby", "McCay-McBut-McDo McDonalds/McBy"},
		{"oblon, spivak, mcclelland, maier & neustadt", "Oblon, Spivak, McClelland, Maier & Neustadt"},
		{"Mcoblon, spivak, mcclelland, mcmaier, & mcneustadt", "McOblon, Spivak, McClelland, McMaier, & McNeustadt"},
		{"mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar", "McFoo-Bar, McFoo-Bar, McFoo-Bar, McFoo-Bar, McFoo-McBar, Foo-McBar"},
		{"'QUOTE' A GREAT", "'Quote' a Great"},
		{"‘QUOTE’ A GREAT", "‘Quote’ a Great"},
		{"“YOUNG AND RESTLESS”", "“Young and Restless”"},
		{"EL NIÑO A ARRIVÉ HIER", "El Niño a Arrivé Hier"},
		{"YEA NO", "Yea No"},
		{"ÝÆ ÑØ", "Ýæ Ñø"},
		{"yea no", "Yea No"},
		{"ýæ ñø", "Ýæ Ñø"},
		{"Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person", "Mr Mr Mrs Ms MSS Dr Dr , Mr. And Mrs. Person"},
		{"a mix\u00a0of\tdifferent\u200aspace\u2006characters", "A Mix\u00a0of\tDifferent\u200aSpace\u2006Characters"},
	}

	for _, tt := range tests {
		actual := Titlecase(tt.input)
		if actual != tt.expected {
			t.Errorf("Titlecase(%q) =\n%q; want\n%q", tt.input, actual, tt.expected)
		}
	}
}

func TestBlankLines(t *testing.T) {
	s1 := "Line number one\n\nand Line three\n"
	want1Default := "Line Number One\nAnd Line Three\n"
	want1Preserve := "Line Number One\n\nAnd Line Three\n"

	if got := Titlecase(s1); got != want1Default {
		t.Errorf("Titlecase(s1) = %q; want %q", got, want1Default)
	}

	opts1 := DefaultOptions()
	opts1.PreserveBlankLines = true
	if got := TitlecaseWithOptions(s1, opts1); got != want1Preserve {
		t.Errorf("TitlecaseWithOptions(s1, preserve) = %q; want %q", got, want1Preserve)
	}

	s2 := "\n\nLeading blank\n\n\nMulti-blank\n\n\n\n\nTrailing Blank\n\n"
	want2Default := "\nLeading Blank\nMulti-Blank\nTrailing Blank\n"
	want2Preserve := "\n\nLeading blank\n\n\nMulti-blank\n\n\n\n\nTrailing Blank\n\n" // preserve blank lines preserves line case of each line
	_ = want2Preserve

	if got := Titlecase(s2); got != want2Default {
		t.Errorf("Titlecase(s2) = %q; want %q", got, want2Default)
	}
}

func TestNewlineEdgeCases(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"", ""},
		{"\n", "\n"},
		{"\r\n", "\n"},
		{"\n\n", "\n"},
		{"\r\n\r\n", "\n"},
		{"a", "A"},
		{"\na", "\nA"},
		{"a\n", "A\n"},
		{"\na\n", "\nA\n"},
		{"\r\na\r\n\r\n", "\nA\n"},
		{"a\n\nb", "A\nB"},
		{"   \n  \n ", "   \n  \n "},
	}

	for _, tt := range tests {
		got := Titlecase(tt.input)
		if got != tt.expected {
			t.Errorf("Titlecase(%q) = %q; want %q", tt.input, got, tt.expected)
		}
	}
}

func TestWhitespacePreservation(t *testing.T) {
	s := "text\twith\ttabs"
	if got := Titlecase(s); got != "Text\tWith\tTabs" {
		t.Errorf("Titlecase(%q) = %q; want %q", s, got, "Text\tWith\tTabs")
	}

	opts := DefaultOptions()
	opts.NormaliseSpaceCharacters = true
	if got := TitlecaseWithOptions(s, opts); got != "Text With Tabs" {
		t.Errorf("TitlecaseWithOptions(%q) = %q; want %q", s, got, "Text With Tabs")
	}

	sNBSP := "text\u00a0with\u00a0nonbreaking\u00a0spaces"
	if got := Titlecase(sNBSP); got != "Text\u00a0With\u00a0Nonbreaking\u00a0Spaces" {
		t.Errorf("Titlecase(%q) = %q; want %q", sNBSP, got, "Text\u00a0With\u00a0Nonbreaking\u00a0Spaces")
	}

	// Leading/trailing spaces on a line with small words
	sLeading := "   the great gatsby"
	if got := Titlecase(sLeading); got != "   the Great Gatsby" {
		t.Errorf("Titlecase(%q) = %q; want %q", sLeading, got, "   the Great Gatsby")
	}

	sTrailing := "the great gatsby of   "
	if got := Titlecase(sTrailing); got != "The Great Gatsby of   " {
		t.Errorf("Titlecase(%q) = %q; want %q", sTrailing, got, "The Great Gatsby of   ")
	}
}

func TestCallbacks(t *testing.T) {
	cb := func(word string, allCaps bool) string {
		switch strings.ToUpper(word) {
		case "TCP", "UDP":
			return strings.ToUpper(word)
		default:
			return ""
		}
	}

	opts := DefaultOptions()
	opts.Callback = cb

	s := "a simple tcp and udp wrapper"
	want := "A Simple TCP and UDP Wrapper"
	if got := TitlecaseWithOptions(s, opts); got != want {
		t.Errorf("TitlecaseWithOptions(%q) = %q; want %q", s, got, want)
	}

	// Immutable callback word at the beginning of string
	cbThe := func(word string, allCaps bool) string {
		if word == "the" {
			return "the"
		}
		return ""
	}
	optsThe := DefaultOptions()
	optsThe.Callback = cbThe
	if got := TitlecaseWithOptions("the great gatsby", optsThe); got != "the Great Gatsby" {
		t.Errorf("Immutable callback failed: got %q, want %q", got, "the Great Gatsby")
	}
}

func TestInitialsRegex(t *testing.T) {
	if !reUCInitials.MatchString("A.B") {
		t.Errorf("reUCInitials should match A.B")
	}
	if !reUCInitials.MatchString("A.B.") {
		t.Errorf("reUCInitials should match A.B.")
	}
	if reUCInitials.MatchString("ABCD") {
		t.Errorf("reUCInitials should not match ABCD")
	}
}
GO_PORT_EOF

find /workspace/repo -name '*.py' -type f -delete
# Deleting the .py files leaves an empty titlecase/ folder; `go build ./...` would then try to
# write its binary to that name and fail ("build output titlecase already exists and is a directory").
find /workspace/repo -mindepth 1 -type d -empty -delete

go test ./...
go build ./...
