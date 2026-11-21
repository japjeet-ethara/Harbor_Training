#!/bin/bash
set -e
mkdir -p /workspace/repo
cd /workspace/repo

cat > go.mod <<'GOMOD'
module tcgo

go 1.23
GOMOD

cat > main.go <<'GOEOF'
package main

import (
	"bufio"
	"os"
	"regexp"
	"strings"
	"unicode"
	"unicode/utf8"
)

const small = `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`
const punct = `!"\x{201C}#$%&'\x{2018}()*+,\-\x{2013}\x{2012}\x{2014}\x{2015}./:;?@\[\\\]_` + "`" + `{|}~`

var (
	lineSplit     = regexp.MustCompile(`[\r\n]+`)
	smallWords    = regexp.MustCompile(`(?i)^(` + small + `)$`)
	smallFirst    = regexp.MustCompile(`(?i)^([` + punct + `]*)(` + small + `)\b`)
	smallLast     = regexp.MustCompile(`(?i)\b(` + small + `)[` + punct + `]?$`)
	subphrase     = regexp.MustCompile(`([:.;?!\-\x{2013}\x{2012}\x{2014}\x{2015}][ ])(` + small + `)`)
	macMc         = regexp.MustCompile(`^([Mm]c|MC)(\w.+)`)
	mrMrsMsDr     = regexp.MustCompile(`(?i)^((m((rs?)|s))|Dr)$`)
	inlinePeriod  = regexp.MustCompile(`\p{L}\.\p{L}`)
	ucElsewhere   = regexp.MustCompile(`^[` + punct + `]*\p{L}+\p{Lu}`)
	capFirst      = regexp.MustCompile(`^[` + punct + `]*?(\p{L})`)
	aposSecond    = regexp.MustCompile(`(?i)^[dol]['\x{2018}]\p{L}+(?:['s]{2})?$`)
	ucInitials    = regexp.MustCompile(`^(?:\p{Lu}\.|\p{Lu}\.\p{Lu})+$`)
	allConsonants = regexp.MustCompile(`(?i)^[bcdfghjklmnpqrstvwxz]+$`)
)

func capitalize(s string) string {
	if s == "" {
		return s
	}
	r, n := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + strings.ToLower(s[n:])
}

func isSpace(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

func splitWS(line string) ([]string, []string) {
	words := []string{""}
	var spaces []string
	for _, r := range line {
		if isSpace(r) {
			spaces = append(spaces, string(r))
			words = append(words, "")
		} else {
			words[len(words)-1] += string(r)
		}
	}
	return words, spaces
}

func capFirstSub(word string) string {
	loc := capFirst.FindStringSubmatchIndex(word)
	if loc == nil {
		return word
	}
	return word[:loc[2]] + strings.ToUpper(word[loc[2]:loc[3]]) + word[loc[3]:]
}

func fixFirst(s string) string {
	loc := smallFirst.FindStringSubmatchIndex(s)
	if loc == nil {
		return s
	}
	return s[:loc[0]] + s[loc[2]:loc[3]] + capitalize(s[loc[4]:loc[5]]) + s[loc[1]:]
}

func subSubphrase(s string) string {
	var b strings.Builder
	last := 0
	for _, loc := range subphrase.FindAllStringSubmatchIndex(s, -1) {
		b.WriteString(s[last:loc[0]])
		b.WriteString(s[loc[2]:loc[3]])
		b.WriteString(capitalize(s[loc[4]:loc[5]]))
		last = loc[1]
	}
	b.WriteString(s[last:])
	return b.String()
}

func processWord(word string, allCaps bool) string {
	if allCaps && ucInitials.MatchString(word) {
		return word
	}
	if aposSecond.MatchString(word) {
		r := []rune(word)
		if !strings.ContainsRune("aeiouAEIOU", r[0]) {
			r[0] = unicode.ToLower(r[0])
		} else {
			r[0] = unicode.ToUpper(r[0])
		}
		r[2] = unicode.ToUpper(r[2])
		return string(r)
	}
	if m := macMc.FindStringSubmatch(word); m != nil {
		return capitalize(m[1]) + titlecase(m[2], true)
	}
	if mrMrsMsDr.MatchString(word) {
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
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if utf8.RuneCountInString(word) > 2 && allConsonants.MatchString(word) {
		return strings.ToUpper(word)
	}
	return capFirstSub(word)
}

func titlecase(text string, smallFirstLast bool) string {
	lines := lineSplit.Split(text, -1)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		allCaps := strings.ToUpper(line) == line
		words, spaces := splitWS(line)
		tc := make([]string, 0, len(words))
		for _, w := range words {
			tc = append(tc, processWord(w, allCaps))
		}
		if smallFirstLast && len(tc) > 0 {
			tc[0] = fixFirst(tc[0])
			last := len(tc) - 1
			tc[last] = smallLast.ReplaceAllStringFunc(tc[last], capitalize)
		}
		var b strings.Builder
		b.WriteString(tc[0])
		for i, sp := range spaces {
			b.WriteString(sp)
			b.WriteString(tc[i+1])
		}
		processed = append(processed, subSubphrase(b.String()))
	}
	return strings.Join(processed, "\n")
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<24)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for sc.Scan() {
		w.WriteString(titlecase(sc.Text(), true))
		w.WriteString("\n")
	}
}
GOEOF

find /workspace/repo -name '*.py' -delete
find /workspace/repo -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find /workspace/repo -mindepth 1 -type d -empty -delete
go build -o /dev/null .