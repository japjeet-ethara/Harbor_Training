#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod << 'END_GO_MOD'
module titlecase

go 1.23
END_GO_MOD

cat > main.go << 'END_MAIN_GO'
package main

import (
	"bufio"
	"bytes"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	if len(data) == 0 {
		return
	}
	ended := data[len(data)-1] == '\n'
	parts := bytes.Split(data, []byte{'\n'})
	if ended {
		parts = parts[:len(parts)-1]
	}
	out := bufio.NewWriter(os.Stdout)
	for i, part := range parts {
		if (ended || i < len(parts)-1) && len(part) > 0 && part[len(part)-1] == '\r' {
			part = part[:len(part)-1]
		}
		if _, err := out.WriteString(titlecase(string(part), true)); err != nil {
			os.Exit(1)
		}
		if err := out.WriteByte('\n'); err != nil {
			os.Exit(1)
		}
	}
	if err := out.Flush(); err != nil {
		os.Exit(1)
	}
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
	processed := make([]string, len(lines))
	for i, line := range lines {
		processed[i] = titlecaseLine(line, smallFirstLast)
	}
	return strings.Join(processed, "\n")
}

func splitNewlines(text string) []string {
	if text == "" {
		return []string{""}
	}
	var lines []string
	var b strings.Builder
	atBreak := false
	anyBreak := false
	for _, r := range text {
		if r == '\n' || r == '\r' {
			if !atBreak {
				lines = append(lines, b.String())
				b.Reset()
				atBreak = true
			}
			anyBreak = true
			continue
		}
		atBreak = false
		b.WriteRune(r)
	}
	if !anyBreak {
		return []string{text}
	}
	if atBreak {
		lines = append(lines, "")
	} else {
		lines = append(lines, b.String())
	}
	return lines
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := pyUpper(line) == line
	words, spaces := splitSpaces(line)
	tc := make([]string, len(words))
	for i, word := range words {
		tc[i] = transformWord(word, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = subSmallFirst(tc[0])
		tc[len(tc)-1] = subSmallLast(tc[len(tc)-1])
	}
	return subSubphrase(interleave(tc, spaces))
}

func splitSpaces(line string) (words, spaces []string) {
	if line == "" {
		return []string{""}, nil
	}
	var cur strings.Builder
	for _, r := range line {
		if isSpace(r) {
			words = append(words, cur.String())
			cur.Reset()
			spaces = append(spaces, string(r))
			continue
		}
		cur.WriteRune(r)
	}
	words = append(words, cur.String())
	return words, spaces
}

func interleave(words, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func transformWord(word string, allCaps bool) string {
	rs := []rune(word)
	if allCaps && matchUCInitials(rs) {
		return word
	}
	if matchApos(rs) {
		return applyApos(rs)
	}
	if pre, rest, ok := splitMac(rs); ok {
		return pyCapitalize(string(pre)) + titlecase(string(rest), true)
	}
	if matchHonorific(word) {
		return pyUpper(string(rs[:1])) + string(rs[1:])
	}
	if hasInlinePeriod(rs) || (!allCaps && matchUCElsewhere(rs)) {
		return word
	}
	if isExactSmall(word) {
		return pyLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = titlecase(part, false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = titlecase(part, false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		word = pyLower(word)
	}
	if utf8.RuneCountInString(word) > 2 && allConsonants(word) {
		return pyUpper(word)
	}
	return capFirst(word)
}

func matchUCInitials(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	var rec func(int) bool
	rec = func(i int) bool {
		if i == len(rs) {
			return true
		}
		if i+1 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' {
			if rec(i + 2) {
				return true
			}
		}
		if i+2 < len(rs) && isASCIIUpper(rs[i]) && rs[i+1] == '.' && isASCIIUpper(rs[i+2]) {
			if rec(i + 3) {
				return true
			}
		}
		return false
	}
	return rec(0)
}

func matchApos(rs []rune) bool {
	if len(rs) < 3 || !isDOL(rs[0]) {
		return false
	}
	if rs[1] != '\'' && rs[1] != '\u2018' {
		return false
	}
	rest := rs[2:]
	max := 0
	for max < len(rest) && isWord(rest[max]) {
		max++
	}
	if max == 0 {
		return false
	}
	for wlen := max; wlen >= 1; wlen-- {
		rem := rest[wlen:]
		if len(rem) == 0 {
			return true
		}
		if len(rem) == 2 && isAposTail(rem[0]) && isAposTail(rem[1]) {
			return true
		}
	}
	return false
}

func applyApos(rs []rune) string {
	var b strings.Builder
	if isVowel(rs[0]) {
		b.WriteString(pyUpper(string(rs[:1])))
	} else {
		b.WriteString(pyLower(string(rs[:1])))
	}
	b.WriteRune(rs[1])
	b.WriteString(pyUpper(string(rs[2:3])))
	b.WriteString(string(rs[3:]))
	return b.String()
}

func splitMac(rs []rune) (pre, rest []rune, ok bool) {
	if len(rs) < 4 {
		return nil, nil, false
	}
	mc := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c'
	upper := rs[0] == 'M' && rs[1] == 'C'
	if !mc && !upper {
		return nil, nil, false
	}
	if !isWord(rs[2]) || rs[3] == '\n' {
		return nil, nil, false
	}
	end := len(rs)
	for i := 3; i < len(rs); i++ {
		if rs[i] == '\n' {
			end = i
			break
		}
	}
	return rs[:2], rs[2:end], true
}

func matchHonorific(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func hasInlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if isWord(rs[i]) && rs[i+1] == '.' && isWord(rs[i+2]) {
			return true
		}
	}
	return false
}

func matchUCElsewhere(rs []rune) bool {
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !isASCIILetter(rs[i]) {
		return false
	}
	for j := i + 1; j < len(rs) && isASCIILetter(rs[j]); j++ {
		if isASCIIUpper(rs[j]) {
			return true
		}
	}
	return false
}

type smallAlt struct {
	lit    string
	optDot bool
}

var smallAlts = []smallAlt{
	{"a", false},
	{"an", false},
	{"and", false},
	{"as", false},
	{"at", false},
	{"but", false},
	{"by", false},
	{"en", false},
	{"for", false},
	{"if", false},
	{"in", false},
	{"of", false},
	{"on", false},
	{"or", false},
	{"the", false},
	{"to", false},
	{"v", true},
	{"via", false},
	{"vs", true},
}

func isExactSmall(word string) bool {
	for _, alt := range smallAlts {
		if strings.EqualFold(word, alt.lit) {
			return true
		}
		if alt.optDot && strings.EqualFold(word, alt.lit+".") {
			return true
		}
	}
	return false
}

func allConsonants(word string) bool {
	if word == "" {
		return false
	}
	for _, r := range word {
		if !isConsonant(r) {
			return false
		}
	}
	return true
}

func isConsonant(r rune) bool {
	switch r {
	case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z',
		'B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Z':
		return true
	default:
		return false
	}
}

func capFirst(word string) string {
	rs := []rune(word)
	i := 0
	for i < len(rs) && !isWord(rs[i]) {
		if !isPunct(rs[i]) {
			return word
		}
		i++
	}
	if i >= len(rs) {
		return word
	}
	return pyUpper(string(rs[:i+1])) + string(rs[i+1:])
}

func subSmallFirst(word string) string {
	rs := []rune(word)
	n := 0
	for n < len(rs) && isPunct(rs[n]) {
		n++
	}
	end, ok := firstSmallWithBoundary(rs, n)
	if !ok {
		return word
	}
	return string(rs[:n]) + pyCapitalize(string(rs[n:end])) + string(rs[end:])
}

func firstSmallWithBoundary(rs []rune, i int) (int, bool) {
	for _, alt := range smallAlts {
		lit := []rune(alt.lit)
		if i+len(lit) > len(rs) || !strings.EqualFold(string(rs[i:i+len(lit)]), alt.lit) {
			continue
		}
		end := i + len(lit)
		if alt.optDot && end < len(rs) && rs[end] == '.' && boundary(rs, end+1) {
			return end + 1, true
		}
		if boundary(rs, end) {
			return end, true
		}
	}
	return 0, false
}

func subSmallLast(word string) string {
	rs := []rune(word)
	if len(rs) == 0 {
		return word
	}
	if isPunct(rs[len(rs)-1]) {
		if start, ok := smallSuffix(rs, len(rs)-1); ok {
			return string(rs[:start]) + pyCapitalize(string(rs[start:]))
		}
	}
	if start, ok := smallSuffix(rs, len(rs)); ok {
		return string(rs[:start]) + pyCapitalize(string(rs[start:]))
	}
	return word
}

func smallSuffix(rs []rune, end int) (int, bool) {
	for _, alt := range smallAlts {
		if alt.optDot {
			if start, ok := matchLitSuffix(rs, end, alt.lit+"."); ok {
				return start, true
			}
		}
		if start, ok := matchLitSuffix(rs, end, alt.lit); ok {
			return start, true
		}
	}
	return 0, false
}

func matchLitSuffix(rs []rune, end int, lit string) (int, bool) {
	l := []rune(lit)
	start := end - len(l)
	if start < 0 {
		return 0, false
	}
	if !strings.EqualFold(string(rs[start:end]), lit) || !boundary(rs, start) {
		return 0, false
	}
	return start, true
}

func subSubphrase(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i := 0; i < len(rs); {
		if i+1 < len(rs) && isSubPunct(rs[i]) && rs[i+1] == ' ' {
			if end, ok := matchSubSmall(rs, i+2); ok {
				b.WriteRune(rs[i])
				b.WriteRune(' ')
				b.WriteString(pyCapitalize(string(rs[i+2 : end])))
				i = end
				continue
			}
		}
		b.WriteRune(rs[i])
		i++
	}
	return b.String()
}

func matchSubSmall(rs []rune, i int) (int, bool) {
	for _, alt := range smallAlts {
		lit := []rune(alt.lit)
		if i+len(lit) > len(rs) {
			continue
		}
		ok := true
		for k := range lit {
			if rs[i+k] != lit[k] {
				ok = false
				break
			}
		}
		if !ok {
			continue
		}
		end := i + len(lit)
		if alt.optDot && end < len(rs) && rs[end] == '.' {
			return end + 1, true
		}
		return end, true
	}
	return 0, false
}

func boundary(rs []rune, i int) bool {
	left := i > 0 && isWord(rs[i-1])
	right := i < len(rs) && isWord(rs[i])
	return left != right
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsNumber(r) || unicode.Is(unicode.Pc, r)
}

func isSpace(r rune) bool {
	return unicode.IsSpace(r)
}

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isASCIIUpper(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func isDOL(r rune) bool {
	switch r {
	case 'd', 'D', 'o', 'O', 'l', 'L':
		return true
	default:
		return false
	}
}

func isVowel(r rune) bool {
	switch r {
	case 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U':
		return true
	default:
		return false
	}
}

func isAposTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '?', '@', '[', '\\', ']', '_', '`', '{', '|', '}', '~',
		'\u201c', '\u2018', '\u2013', '\u2012', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func isSubPunct(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2013', '\u2012', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func pyUpper(s string) string {
	var b strings.Builder
	for _, r := range s {
		if repl, ok := upperExpand[r]; ok {
			b.WriteString(repl)
			continue
		}
		b.WriteRune(unicode.ToUpper(r))
	}
	return b.String()
}

func pyLower(s string) string {
	rs := []rune(s)
	var b strings.Builder
	for i, r := range rs {
		if r == 'Σ' && finalSigma(rs, i) {
			b.WriteRune('ς')
			continue
		}
		if repl, ok := lowerExpand[r]; ok {
			b.WriteString(repl)
			continue
		}
		b.WriteRune(unicode.ToLower(r))
	}
	return b.String()
}

func pyCapitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return ""
	}
	return pyTitle(rs[0]) + pyLower(string(rs[1:]))
}

func pyTitle(r rune) string {
	if repl, ok := titleExpand[r]; ok {
		return repl
	}
	return pyUpper(string(r))
}

func finalSigma(rs []rune, i int) bool {
	casedBefore := false
	for j := i - 1; j >= 0; j-- {
		if isCaseIgnorable(rs[j]) {
			continue
		}
		if isCased(rs[j]) {
			casedBefore = true
		}
		break
	}
	if !casedBefore {
		return false
	}
	for j := i + 1; j < len(rs); j++ {
		if isCaseIgnorable(rs[j]) {
			continue
		}
		if isCased(rs[j]) {
			return false
		}
		break
	}
	return true
}

func isCased(r rune) bool {
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r)
}

func isCaseIgnorable(r rune) bool {
	switch r {
	case '\'', '.', ':', '\u00b7', '\u0387', '\u055f', '\u05f4',
		'\u2018', '\u2019', '\u2024', '\u2027', '\ufe52', '\uff07', '\uff0e',
		'\ufe13', '\ufe55', '\uff1a':
		return true
	}
	return unicode.Is(unicode.Mn, r) || unicode.Is(unicode.Me, r) ||
		unicode.Is(unicode.Cf, r) || unicode.Is(unicode.Lm, r) ||
		unicode.Is(unicode.Sk, r)
}
END_MAIN_GO

cat > casefold.go << 'END_CASEFOLD_GO'
package main

var lowerExpand = map[rune]string{
	'\u0130': "i\u0307",
}

var upperExpand = map[rune]string{
	'\u00df': "SS",
	'\u0149': "\u02bcN",
	'\u01f0': "J\u030c",
	'\u0390': "\u0399\u0308\u0301",
	'\u03b0': "\u03a5\u0308\u0301",
	'\u0587': "\u0535\u0552",
	'\u1e96': "H\u0331",
	'\u1e97': "T\u0308",
	'\u1e98': "W\u030a",
	'\u1e99': "Y\u030a",
	'\u1e9a': "A\u02be",
	'\u1f50': "\u03a5\u0313",
	'\u1f52': "\u03a5\u0313\u0300",
	'\u1f54': "\u03a5\u0313\u0301",
	'\u1f56': "\u03a5\u0313\u0342",
	'\u1f80': "\u1f08\u0399",
	'\u1f81': "\u1f09\u0399",
	'\u1f82': "\u1f0a\u0399",
	'\u1f83': "\u1f0b\u0399",
	'\u1f84': "\u1f0c\u0399",
	'\u1f85': "\u1f0d\u0399",
	'\u1f86': "\u1f0e\u0399",
	'\u1f87': "\u1f0f\u0399",
	'\u1f88': "\u1f08\u0399",
	'\u1f89': "\u1f09\u0399",
	'\u1f8a': "\u1f0a\u0399",
	'\u1f8b': "\u1f0b\u0399",
	'\u1f8c': "\u1f0c\u0399",
	'\u1f8d': "\u1f0d\u0399",
	'\u1f8e': "\u1f0e\u0399",
	'\u1f8f': "\u1f0f\u0399",
	'\u1f90': "\u1f28\u0399",
	'\u1f91': "\u1f29\u0399",
	'\u1f92': "\u1f2a\u0399",
	'\u1f93': "\u1f2b\u0399",
	'\u1f94': "\u1f2c\u0399",
	'\u1f95': "\u1f2d\u0399",
	'\u1f96': "\u1f2e\u0399",
	'\u1f97': "\u1f2f\u0399",
	'\u1f98': "\u1f28\u0399",
	'\u1f99': "\u1f29\u0399",
	'\u1f9a': "\u1f2a\u0399",
	'\u1f9b': "\u1f2b\u0399",
	'\u1f9c': "\u1f2c\u0399",
	'\u1f9d': "\u1f2d\u0399",
	'\u1f9e': "\u1f2e\u0399",
	'\u1f9f': "\u1f2f\u0399",
	'\u1fa0': "\u1f68\u0399",
	'\u1fa1': "\u1f69\u0399",
	'\u1fa2': "\u1f6a\u0399",
	'\u1fa3': "\u1f6b\u0399",
	'\u1fa4': "\u1f6c\u0399",
	'\u1fa5': "\u1f6d\u0399",
	'\u1fa6': "\u1f6e\u0399",
	'\u1fa7': "\u1f6f\u0399",
	'\u1fa8': "\u1f68\u0399",
	'\u1fa9': "\u1f69\u0399",
	'\u1faa': "\u1f6a\u0399",
	'\u1fab': "\u1f6b\u0399",
	'\u1fac': "\u1f6c\u0399",
	'\u1fad': "\u1f6d\u0399",
	'\u1fae': "\u1f6e\u0399",
	'\u1faf': "\u1f6f\u0399",
	'\u1fb2': "\u1fba\u0399",
	'\u1fb3': "\u0391\u0399",
	'\u1fb4': "\u0386\u0399",
	'\u1fb6': "\u0391\u0342",
	'\u1fb7': "\u0391\u0342\u0399",
	'\u1fbc': "\u0391\u0399",
	'\u1fc2': "\u1fca\u0399",
	'\u1fc3': "\u0397\u0399",
	'\u1fc4': "\u0389\u0399",
	'\u1fc6': "\u0397\u0342",
	'\u1fc7': "\u0397\u0342\u0399",
	'\u1fcc': "\u0397\u0399",
	'\u1fd2': "\u0399\u0308\u0300",
	'\u1fd3': "\u0399\u0308\u0301",
	'\u1fd6': "\u0399\u0342",
	'\u1fd7': "\u0399\u0308\u0342",
	'\u1fe2': "\u03a5\u0308\u0300",
	'\u1fe3': "\u03a5\u0308\u0301",
	'\u1fe4': "\u03a1\u0313",
	'\u1fe6': "\u03a5\u0342",
	'\u1fe7': "\u03a5\u0308\u0342",
	'\u1ff2': "\u1ffa\u0399",
	'\u1ff3': "\u03a9\u0399",
	'\u1ff4': "\u038f\u0399",
	'\u1ff6': "\u03a9\u0342",
	'\u1ff7': "\u03a9\u0342\u0399",
	'\u1ffc': "\u03a9\u0399",
	'\ufb00': "FF",
	'\ufb01': "FI",
	'\ufb02': "FL",
	'\ufb03': "FFI",
	'\ufb04': "FFL",
	'\ufb05': "ST",
	'\ufb06': "ST",
	'\ufb13': "\u0544\u0546",
	'\ufb14': "\u0544\u0535",
	'\ufb15': "\u0544\u053b",
	'\ufb16': "\u054e\u0546",
	'\ufb17': "\u0544\u053d",
}

var titleExpand = map[rune]string{
	'\u00df': "Ss",
	'\u01c4': "\u01c5",
	'\u01c5': "\u01c5",
	'\u01c6': "\u01c5",
	'\u01c7': "\u01c8",
	'\u01c8': "\u01c8",
	'\u01c9': "\u01c8",
	'\u01ca': "\u01cb",
	'\u01cb': "\u01cb",
	'\u01cc': "\u01cb",
	'\u01f1': "\u01f2",
	'\u01f2': "\u01f2",
	'\u01f3': "\u01f2",
	'\u0587': "\u0535\u0582",
	'\u10d0': "\u10d0",
	'\u10d1': "\u10d1",
	'\u10d2': "\u10d2",
	'\u10d3': "\u10d3",
	'\u10d4': "\u10d4",
	'\u10d5': "\u10d5",
	'\u10d6': "\u10d6",
	'\u10d7': "\u10d7",
	'\u10d8': "\u10d8",
	'\u10d9': "\u10d9",
	'\u10da': "\u10da",
	'\u10db': "\u10db",
	'\u10dc': "\u10dc",
	'\u10dd': "\u10dd",
	'\u10de': "\u10de",
	'\u10df': "\u10df",
	'\u10e0': "\u10e0",
	'\u10e1': "\u10e1",
	'\u10e2': "\u10e2",
	'\u10e3': "\u10e3",
	'\u10e4': "\u10e4",
	'\u10e5': "\u10e5",
	'\u10e6': "\u10e6",
	'\u10e7': "\u10e7",
	'\u10e8': "\u10e8",
	'\u10e9': "\u10e9",
	'\u10ea': "\u10ea",
	'\u10eb': "\u10eb",
	'\u10ec': "\u10ec",
	'\u10ed': "\u10ed",
	'\u10ee': "\u10ee",
	'\u10ef': "\u10ef",
	'\u10f0': "\u10f0",
	'\u10f1': "\u10f1",
	'\u10f2': "\u10f2",
	'\u10f3': "\u10f3",
	'\u10f4': "\u10f4",
	'\u10f5': "\u10f5",
	'\u10f6': "\u10f6",
	'\u10f7': "\u10f7",
	'\u10f8': "\u10f8",
	'\u10f9': "\u10f9",
	'\u10fa': "\u10fa",
	'\u10fd': "\u10fd",
	'\u10fe': "\u10fe",
	'\u10ff': "\u10ff",
	'\u1f80': "\u1f88",
	'\u1f81': "\u1f89",
	'\u1f82': "\u1f8a",
	'\u1f83': "\u1f8b",
	'\u1f84': "\u1f8c",
	'\u1f85': "\u1f8d",
	'\u1f86': "\u1f8e",
	'\u1f87': "\u1f8f",
	'\u1f88': "\u1f88",
	'\u1f89': "\u1f89",
	'\u1f8a': "\u1f8a",
	'\u1f8b': "\u1f8b",
	'\u1f8c': "\u1f8c",
	'\u1f8d': "\u1f8d",
	'\u1f8e': "\u1f8e",
	'\u1f8f': "\u1f8f",
	'\u1f90': "\u1f98",
	'\u1f91': "\u1f99",
	'\u1f92': "\u1f9a",
	'\u1f93': "\u1f9b",
	'\u1f94': "\u1f9c",
	'\u1f95': "\u1f9d",
	'\u1f96': "\u1f9e",
	'\u1f97': "\u1f9f",
	'\u1f98': "\u1f98",
	'\u1f99': "\u1f99",
	'\u1f9a': "\u1f9a",
	'\u1f9b': "\u1f9b",
	'\u1f9c': "\u1f9c",
	'\u1f9d': "\u1f9d",
	'\u1f9e': "\u1f9e",
	'\u1f9f': "\u1f9f",
	'\u1fa0': "\u1fa8",
	'\u1fa1': "\u1fa9",
	'\u1fa2': "\u1faa",
	'\u1fa3': "\u1fab",
	'\u1fa4': "\u1fac",
	'\u1fa5': "\u1fad",
	'\u1fa6': "\u1fae",
	'\u1fa7': "\u1faf",
	'\u1fa8': "\u1fa8",
	'\u1fa9': "\u1fa9",
	'\u1faa': "\u1faa",
	'\u1fab': "\u1fab",
	'\u1fac': "\u1fac",
	'\u1fad': "\u1fad",
	'\u1fae': "\u1fae",
	'\u1faf': "\u1faf",
	'\u1fb2': "\u1fba\u0345",
	'\u1fb3': "\u1fbc",
	'\u1fb4': "\u0386\u0345",
	'\u1fb7': "\u0391\u0342\u0345",
	'\u1fbc': "\u1fbc",
	'\u1fc2': "\u1fca\u0345",
	'\u1fc3': "\u1fcc",
	'\u1fc4': "\u0389\u0345",
	'\u1fc7': "\u0397\u0342\u0345",
	'\u1fcc': "\u1fcc",
	'\u1ff2': "\u1ffa\u0345",
	'\u1ff3': "\u1ffc",
	'\u1ff4': "\u038f\u0345",
	'\u1ff7': "\u03a9\u0342\u0345",
	'\u1ffc': "\u1ffc",
	'\ufb00': "Ff",
	'\ufb01': "Fi",
	'\ufb02': "Fl",
	'\ufb03': "Ffi",
	'\ufb04': "Ffl",
	'\ufb05': "St",
	'\ufb06': "St",
	'\ufb13': "\u0544\u0576",
	'\ufb14': "\u0544\u0565",
	'\ufb15': "\u0544\u056b",
	'\ufb16': "\u054e\u0576",
	'\ufb17': "\u0544\u056d",
}
END_CASEFOLD_GO

find /workspace/repo -type f -name '*.py' -delete
find /workspace/repo -depth -type d -empty -delete
