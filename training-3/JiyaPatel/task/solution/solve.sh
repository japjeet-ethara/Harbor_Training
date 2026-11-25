#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Remove all Python files and artifacts
find /workspace/repo -type f -name "*.py" -delete
rm -rf titlecase

# Initialize Go module
rm -f go.mod go.sum
go mod init titlecase-cli

cat << 'GOEOF' > main.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"
)

const (
	smallPattern = `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`
	punctClass   = `!"“#$%&'‘()*+,\-–‒—―./:;?@\[\\\]_` + "`" + `{|}~`
	pyWordChar   = `[\p{L}\p{N}_]`
	pyNonWord    = `[^\p{L}\p{N}_]`
)

var (
	reSmallWords   = regexp.MustCompile(`(?i)^(` + smallPattern + `)$`)
	reSmallFirst   = regexp.MustCompile(`(?i)^([` + punctClass + `]*)(` + smallPattern + `)(?:` + pyNonWord + `|$)`)
	reSmallLast    = regexp.MustCompile(`(?i)(?:^|` + pyNonWord + `)(` + smallPattern + `)[` + punctClass + `]?$`)
	reSubphrase    = regexp.MustCompile(`([:.;?!\-–‒—―][ ])(` + smallPattern + `)`)
	reMacMc        = regexp.MustCompile(`^([Mm]c|MC)(` + pyWordChar + `.+)`)
	reMrMrsMsDr    = regexp.MustCompile(`(?i)^((m((rs?)|s))|Dr)$`)
	reInlinePeriod = regexp.MustCompile(`(?i)` + pyWordChar + `[.]` + pyWordChar)
	reUcElsewhere  = regexp.MustCompile(`^[` + punctClass + `]*?[a-zA-Z]+[A-Z]+?`)
	reCapFirst     = regexp.MustCompile(`^[` + punctClass + `]*?(` + pyWordChar + `)`)
	reAposSecond   = regexp.MustCompile(`(?i)^[dol]['‘]` + pyWordChar + `+(?:['s]{2})?$`)
	reUcInitials   = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
	reAllCons      = regexp.MustCompile(`(?i)^[bcdfghjklmnpqrstvwxz]+$`)
)

func capitalizeFirst(s string) string {
	if s == "" {
		return s
	}
	runes := []rune(s)
	runes[0] = unicode.ToUpper(runes[0])
	return string(runes)
}

func isPySpace(r rune) bool {
	switch r {
	case ' ', '\t', '\n', '\r', '\v', '\f',
		'\u00a0', '\u1680', '\u2000', '\u2001', '\u2002', '\u2003',
		'\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u2009',
		'\u200a', '\u2028', '\u2029', '\u202f', '\u205f', '\u3000',
		'\u001c', '\u001d', '\u001e', '\u001f', '\u0085':
		return true
	}
	return false
}

func splitWhitespaceKeep(s string) ([]string, []string) {
	var words []string
	var spaces []string
	var cur strings.Builder
	for _, r := range s {
		if isPySpace(r) {
			words = append(words, cur.String())
			cur.Reset()
			spaces = append(spaces, string(r))
		} else {
			cur.WriteRune(r)
		}
	}
	words = append(words, cur.String())
	return words, spaces
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitWhitespaceKeep(line)
	tcLine := make([]string, 0, len(words))

	for _, word := range words {
		if allCaps && reUcInitials.MatchString(word) {
			tcLine = append(tcLine, word)
			continue
		}

		if reAposSecond.MatchString(word) {
			runes := []rune(word)
			if len(runes) >= 3 {
				firstLower := unicode.ToLower(runes[0])
				if firstLower != 'a' && firstLower != 'e' && firstLower != 'i' && firstLower != 'o' && firstLower != 'u' {
					runes[0] = firstLower
				} else {
					runes[0] = unicode.ToUpper(runes[0])
				}
				runes[2] = unicode.ToUpper(runes[2])
				tcLine = append(tcLine, string(runes))
				continue
			}
		}

		if m := reMacMc.FindStringSubmatch(word); m != nil {
			tcLine = append(tcLine, capitalizeFirst(strings.ToLower(m[1]))+titlecaseLine(m[2], true))
			continue
		}

		if reMrMrsMsDr.MatchString(word) {
			tcLine = append(tcLine, capitalizeFirst(word))
			continue
		}

		if reInlinePeriod.MatchString(word) || (!allCaps && reUcElsewhere.MatchString(word)) {
			tcLine = append(tcLine, word)
			continue
		}

		if reSmallWords.MatchString(word) {
			tcLine = append(tcLine, strings.ToLower(word))
			continue
		}

		if strings.Contains(word, "/") && !strings.Contains(word, "//") {
			parts := strings.Split(word, "/")
			for i, p := range parts {
				parts[i] = titlecaseLine(p, false)
			}
			tcLine = append(tcLine, strings.Join(parts, "/"))
			continue
		}

		if strings.Contains(word, "-") {
			parts := strings.Split(word, "-")
			for i, p := range parts {
				parts[i] = titlecaseLine(p, false)
			}
			tcLine = append(tcLine, strings.Join(parts, "-"))
			continue
		}

		if allCaps {
			word = strings.ToLower(word)
		}

		if reAllCons.MatchString(word) && len([]rune(word)) > 2 {
			tcLine = append(tcLine, strings.ToUpper(word))
			continue
		}

		loc := reCapFirst.FindStringSubmatchIndex(word)
		if loc != nil {
			prefix := word[:loc[2]]
			ch := word[loc[2]:loc[3]]
			suffix := word[loc[3]:]
			tcLine = append(tcLine, prefix+strings.ToUpper(ch)+suffix)
		} else {
			tcLine = append(tcLine, word)
		}
	}

	if smallFirstLast && len(tcLine) > 0 {
		if m := reSmallFirst.FindStringSubmatchIndex(tcLine[0]); m != nil {
			p1 := tcLine[0][m[2]:m[3]]
			p2 := tcLine[0][m[4]:m[5]]
			rest := tcLine[0][m[5]:]
			tcLine[0] = p1 + capitalizeFirst(strings.ToLower(p2)) + rest
		}
		lastIdx := len(tcLine) - 1
		if m := reSmallLast.FindStringSubmatchIndex(tcLine[lastIdx]); m != nil {
			before := tcLine[lastIdx][:m[2]]
			matched := tcLine[lastIdx][m[2]:m[1]]
			tcLine[lastIdx] = before + capitalizeFirst(strings.ToLower(matched))
		}
	}

	var out strings.Builder
	for i := range tcLine {
		out.WriteString(tcLine[i])
		if i < len(spaces) {
			out.WriteString(spaces[i])
		}
	}

	res := out.String()
	res = reSubphrase.ReplaceAllStringFunc(res, func(sub string) string {
		m := reSubphrase.FindStringSubmatch(sub)
		return m[1] + capitalizeFirst(strings.ToLower(m[2]))
	})
	return res
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	buf := make([]byte, 0, 1024*1024)
	scanner.Buffer(buf, 10*1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for scanner.Scan() {
		fmt.Fprintln(writer, titlecaseLine(scanner.Text(), true))
	}
}
GOEOF

go build ./...
