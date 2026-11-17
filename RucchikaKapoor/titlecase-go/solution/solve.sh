#!/bin/bash
# Oracle: Go port of python-titlecase (stdlib only), then delete every .py file.
# DRAFT - written without access to the original code; iterate with tools/first_diffs.py until 0 diffs.
set -euo pipefail
cd /workspace/repo

printf 'module titlecase-go\n\ngo 1.23\n' > go.mod

cat > main.go <<'GOSRC'
package main

import (
	"bufio"
	"os"
	"regexp"
	"strings"
	"unicode"
)

const small = `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`
const punct = `!"#$%&'‘()*+,\-–‒—―./:;?@\[\\\]_` + "`" + `{|}~`

var (
	smallWords   = regexp.MustCompile(`(?i)^(?:` + small + `)$`)
	inlinePeriod = regexp.MustCompile(`(?i)[a-z][.][a-z]`)
	ucElsewhere  = regexp.MustCompile(`^[` + punct + `]*?[a-zA-Z]+[A-Z]+?`)
	capFirst     = regexp.MustCompile(`^[` + punct + `]*?([A-Za-z])`)
	smallFirst   = regexp.MustCompile(`(?i)^([` + punct + `]*)(` + small + `)\b`)
	smallLast    = regexp.MustCompile(`(?i)\b(?:` + small + `)[` + punct + `]?$`)
	subphrase    = regexp.MustCompile(`([:.;?!\-–‒—―] )(` + small + `)`)
	aposSecond   = regexp.MustCompile(`(?i)^[dol]['‘][a-z]+(?:['s]{2})?$`)
	ucInitials   = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)
	macMc        = regexp.MustCompile(`^([Mm]c|MC)(\w.+)`)
	mrMrs        = regexp.MustCompile(`(?i)^(?:m(?:rs?|s)|dr)$`)
	allCapsRe    = regexp.MustCompile(`^[A-Z\s\d` + punct + `]+$`)
	splitWS      = regexp.MustCompile(`[\t ]`)
	splitNL      = regexp.MustCompile(`[\r\n]+`)
	consonants = regexp.MustCompile(`(?i)^[bcdfghjklmnpqrstvwxz]+$`)
)

func capitalize(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return s
	}
	out := make([]rune, 0, len(r))
	out = append(out, unicode.ToUpper(r[0]))
	for _, c := range r[1:] {
		out = append(out, unicode.ToLower(c))
	}
	return string(out)
}

func sub(re *regexp.Regexp, s string, f func(g []string) string) string {
	var b strings.Builder
	last := 0
	for _, loc := range re.FindAllStringSubmatchIndex(s, -1) {
		g := make([]string, len(loc)/2)
		for i := range g {
			if loc[2*i] >= 0 {
				g[i] = s[loc[2*i]:loc[2*i+1]]
			}
		}
		b.WriteString(s[last:loc[0]])
		b.WriteString(f(g))
		last = loc[1]
	}
	b.WriteString(s[last:])
	return b.String()
}

func splitJoin(word, sep string) string {
        parts := strings.Split(word, sep)
        for i, p := range parts {
                parts[i] = titlecaseMode(p, false)
        }
        return strings.Join(parts, sep)
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
                return capitalize(m[1]) + titlecase(m[2])
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
                return splitJoin(word, "/")
        }

        if strings.Contains(word, "-") {
                return splitJoin(word, "-")
        }

        if allCaps {
                word = strings.ToLower(word)
        }
	if consonants.MatchString(word) && len([]rune(word)) > 2 {
		return strings.ToUpper(word)
	}
        if loc := capFirst.FindStringSubmatchIndex(word); loc != nil {
                word = word[:loc[2]] + strings.ToUpper(word[loc[2]:loc[3]]) + word[loc[3]:]
        }

        return word
}

func titlecase(text string) string {
        return titlecaseMode(text, true)
}

func titlecaseMode(text string, smallFirstLastEnabled bool) string {
        lines := splitNL.Split(text, -1)
        processed := make([]string, 0, len(lines))

        for _, line := range lines {
                allCaps := strings.ToUpper(line) == line
                var result strings.Builder
                runes := []rune(line)

                for i := 0; i < len(runes); {
                        j := i + 1
                        isSpace := unicode.IsSpace(runes[i])

                        for j < len(runes) && unicode.IsSpace(runes[j]) == isSpace {
                                j++
                        }

                        part := string(runes[i:j])
                        if isSpace {
                                result.WriteString(part)
                        } else {
                                result.WriteString(processWord(part, allCaps))
                        }
                        i = j
                }

                output := result.String()

                if smallFirstLastEnabled {
                        if loc := smallFirst.FindStringSubmatchIndex(output); loc != nil {
                                output = output[:loc[3]] + capitalize(output[loc[4]:loc[5]]) + output[loc[5]:]
                        }
                        output = sub(smallLast, output, func(g []string) string {
                                return capitalize(g[0])
                        })
                }

                output = sub(subphrase, output, func(g []string) string {
                        return g[1] + capitalize(g[2])
                })

                processed = append(processed, output)
        }

        return strings.Join(processed, "\n")
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1024*1024), 16*1024*1024)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for sc.Scan() {
		w.WriteString(titlecase(sc.Text()))
		w.WriteByte('\n')
	}
}
GOSRC

find /workspace/repo -name '*.py' -delete
go build ./...
