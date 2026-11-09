
package main

import (
	"regexp"
	"strings"
	"unicode"
)

const (
	smallWordsPattern = `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`
	punctPattern      = `!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_` + "`" + `{|}~`
)

var (
	reSmallWords        = regexp.MustCompile(`(?i)^(` + smallWordsPattern + `)$`)
	reSmallFirst        = regexp.MustCompile(`(?i)^([` + punctPattern + `]*)(` + smallWordsPattern + `)($|[^\p{L}\p{N}_])`)
	reSmallLast         = regexp.MustCompile(`(?i)(^|[^\p{L}\p{N}_])(` + smallWordsPattern + `)([` + punctPattern + `]?)$`)
	reSubphrase         = regexp.MustCompile(`([:.;?!\-–‒—―] )(` + smallWordsPattern + `)`)
	reMacMc             = regexp.MustCompile(`^([Mm]c|MC)(\w.+)`)
	reMrMrsMsDr         = regexp.MustCompile(`(?i)^((m((rs?)|s))|Dr)$`)
	reInlinePeriod      = regexp.MustCompile(`(?i)\w\.\w`)
	reUCElsewhere       = regexp.MustCompile(`^[` + punctPattern + `]*?\p{L}+\p{Lu}+`)
	reCapFirst          = regexp.MustCompile(`^[` + punctPattern + `]*?(\p{L})`)
	reAposSecond        = regexp.MustCompile(`(?i)^[dol]['‘]\w+(?:['s]{2})?$`)
	reUCInitials        = regexp.MustCompile(`^(?:\p{Lu}\.|\p{Lu}\.\p{Lu})+$`)
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
		allCaps := strings.ToUpper(line) == line
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

			if reAllConsonants.MatchString(word) && len(word) > 2 {
				tcLine = append(tcLine, wordToken{text: strings.ToUpper(word), immutable: false})
				continue
			}

			word = reCapFirst.ReplaceAllStringFunc(word, func(m string) string {
				return strings.ToUpper(m)
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
		if unicode.IsSpace(r) {
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
