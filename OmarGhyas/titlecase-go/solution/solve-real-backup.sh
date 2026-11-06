#!/bin/bash
set -euo pipefail
cd /workspace/repo
cat > go.mod << 'TITLECASE_GO_SOURCE'
module titlecase

go 1.23
TITLECASE_GO_SOURCE
cat > main.go << 'TITLECASE_GO_SOURCE'
package main

import (
	"bufio"
	"os"
	"unicode"
	"unicode/utf8"
)

// Title-case port of titlecase 2.4.1 (regex engine). Go's regexp has no
// Unicode-aware \b and no look-around, so word boundaries, small-word
// prefixes, and the apostrophe/initials patterns are checked by hand.

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)
	out := bufio.NewWriter(os.Stdout)
	for in.Scan() {
		out.WriteString(titlecase(in.Text(), true))
		out.WriteByte('\n')
	}
	out.Flush()
}

const punctSet = "!\"“#$%&'‘()*+,-\u2013\u2012\u2014\u2015./:;?@[\\]_`{|}~"

var subphraseStarters = []rune{':', '.', ';', '?', '!', '-', '\u2013', '\u2012', '\u2014', '\u2015'}

func isPunct(r rune) bool {
	for _, p := range punctSet {
		if r == p {
			return true
		}
	}
	return false
}

func isSubphraseStarter(r rune) bool {
	for _, p := range subphraseStarters {
		if r == p {
			return true
		}
	}
	return false
}

func isSpace(r rune) bool {
	switch r {
	case '\t', '\n', '\v', '\f', '\r', ' ', '\u0085', '\u00a0', '\u1680',
		'\u2000', '\u2001', '\u2002', '\u2003', '\u2004', '\u2005', '\u2006',
		'\u2007', '\u2008', '\u2009', '\u200a', '\u2028', '\u2029', '\u202f',
		'\u205f', '\u3000':
		return true
	default:
		return false
	}
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.Is(unicode.Mark, r) || unicode.Is(unicode.Pc, r)
}

func boundaryAt(rs []rune, i int) bool {
	left := i > 0 && isWord(rs[i-1])
	right := i < len(rs) && isWord(rs[i])
	return left != right
}

func pyUpperRune(r rune) string {
	switch r {
	case 'ß':
		return "SS"
	case 'ﬁ':
		return "FI"
	case 'ﬂ':
		return "FL"
	case 'ﬀ':
		return "FF"
	case 'ﬃ':
		return "FFI"
	case 'ﬄ':
		return "FFL"
	case 'ﬅ', 'ﬆ':
		return "ST"
	case 'ŉ':
		return "ʼN"
	case 'ǰ':
		return "J\u030c"
	default:
		return string(unicode.ToUpper(r))
	}
}

func isCased(r rune) bool {
	return unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r)
}

func isCaseIgnorable(r rune) bool {
	return unicode.Is(unicode.Mn, r) || unicode.Is(unicode.Me, r) || unicode.Is(unicode.Cf, r) || unicode.Is(unicode.Lm, r) || unicode.Is(unicode.Sk, r)
}

func isFinalSigma(rs []rune, i int) bool {
	prev := false
	for j := i - 1; j >= 0; j-- {
		if isCaseIgnorable(rs[j]) {
			continue
		}
		prev = isCased(rs[j])
		break
	}
	if !prev {
		return false
	}
	for j := i + 1; j < len(rs); j++ {
		if isCaseIgnorable(rs[j]) {
			continue
		}
		return !isCased(rs[j])
	}
	return true
}

func pyLower(s string) string {
	rs := []rune(s)
	var b []rune
	for i, r := range rs {
		switch r {
		case 'İ':
			b = append(b, 'i', '\u0307')
		case 'ẞ':
			b = append(b, 'ß')
		case 'Σ':
			if isFinalSigma(rs, i) {
				b = append(b, 'ς')
			} else {
				b = append(b, 'σ')
			}
		default:
			b = append(b, unicode.ToLower(r))
		}
	}
	return string(b)
}

func pyUpper(s string) string {
	var b []byte
	for _, r := range s {
		b = append(b, pyUpperRune(r)...)
	}
	return string(b)
}

func pyCapitalize(s string) string {
	if s == "" {
		return ""
	}
	r, size := utf8.DecodeRuneInString(s)
	up := pyUpperRune(r)
	_, width := utf8.DecodeRuneInString(up)
	rest := pyLower(up[width:] + s[size:])
	first, _ := utf8.DecodeRuneInString(up)
	return string(first) + rest
}

type smallAlt struct {
	text   string
	dotted bool
}

var smallAlts = []smallAlt{
	{"a", false}, {"an", false}, {"and", false}, {"as", false}, {"at", false},
	{"but", false}, {"by", false}, {"en", false}, {"for", false}, {"if", false},
	{"in", false}, {"of", false}, {"on", false}, {"or", false}, {"the", false},
	{"to", false}, {"v", true}, {"via", false}, {"vs", true},
}

func foldEq(rs []rune, i int, lit string) bool {
	lr := []rune(lit)
	if i+len(lr) > len(rs) {
		return false
	}
	for k, want := range lr {
		if unicode.ToLower(rs[i+k]) != unicode.ToLower(want) {
			return false
		}
	}
	return true
}

func exactEq(rs []rune, i int, lit string) bool {
	lr := []rune(lit)
	if i+len(lr) > len(rs) {
		return false
	}
	for k, want := range lr {
		if rs[i+k] != want {
			return false
		}
	}
	return true
}

func altBase(rs []rune, i int, alt smallAlt, fold bool) int {
	ok := exactEq(rs, i, alt.text)
	if fold {
		ok = foldEq(rs, i, alt.text)
	}
	if !ok {
		return -1
	}
	return utf8.RuneCountInString(alt.text)
}

// lengths tries the optional period greedily, then without it. A following
// word-boundary check can reject the longer match, which is the backtrack
// Python does for `\b` after `v\.?` / `vs\.?`.
func altLengths(rs []rune, i int, alt smallAlt, fold bool) []int {
	n := altBase(rs, i, alt, fold)
	if n < 0 {
		return nil
	}
	if alt.dotted && i+n < len(rs) && rs[i+n] == '.' {
		return []int{n + 1, n}
	}
	return []int{n}
}

func matchSmall(rs []rune, i int, fold, boundary bool) int {
	for _, alt := range smallAlts {
		for _, n := range altLengths(rs, i, alt, fold) {
			if boundary && !boundaryAt(rs, i+n) {
				continue
			}
			return n
		}
	}
	return -1
}

func isExactSmall(s string) bool {
	rs := []rune(s)
	for _, alt := range smallAlts {
		for _, n := range altLengths(rs, 0, alt, true) {
			if n == len(rs) {
				return true
			}
		}
	}
	return false
}

func applySmallFirst(s string) string {
	rs := []rune(s)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	n := matchSmall(rs, i, true, true)
	if n < 0 {
		return s
	}
	head := string(rs[:i])
	mid := string(rs[i : i+n])
	tail := string(rs[i+n:])
	return head + pyCapitalize(mid) + tail
}

func applySmallLast(s string) string {
	rs := []rune(s)
	for i := 0; i <= len(rs); i++ {
		if !boundaryAt(rs, i) {
			continue
		}
		for _, alt := range smallAlts {
			for _, n := range altLengths(rs, i, alt, true) {
				end := i + n
				if end < len(rs) && end+1 == len(rs) && isPunct(rs[end]) {
					end++
				}
				if end != len(rs) {
					continue
				}
				return string(rs[:i]) + pyCapitalize(string(rs[i:]))
			}
		}
	}
	return s
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var out []rune
	for i := 0; i < len(rs); {
		if i+2 < len(rs) && isSubphraseStarter(rs[i]) && rs[i+1] == ' ' {
			if n := matchSmall(rs, i+2, false, false); n > 0 {
				out = append(out, rs[i], ' ')
				out = append(out, []rune(pyCapitalize(string(rs[i+2:i+2+n])))...)
				i += 2 + n
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

func hasInlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if unicode.IsLetter(rs[i]) && rs[i+1] == '.' && unicode.IsLetter(rs[i+2]) {
			return true
		}
	}
	return false
}

func ucElsewhere(rs []rune) bool {
	maxPunct := 0
	for maxPunct < len(rs) && isPunct(rs[maxPunct]) {
		maxPunct++
	}
	for p := 0; p <= maxPunct; p++ {
		i := p
		if i >= len(rs) || !unicode.IsLetter(rs[i]) {
			continue
		}
		for k := i + 1; k < len(rs) && unicode.IsLetter(rs[k]); k++ {
			if unicode.IsUpper(rs[k]) {
				return true
			}
		}
	}
	return false
}

func matchInitials(rs []rune) bool {
	var rec func(int) bool
	rec = func(i int) bool {
		if i == len(rs) {
			return i > 0
		}
		if i+3 <= len(rs) && unicode.IsUpper(rs[i]) && rs[i+1] == '.' && unicode.IsUpper(rs[i+2]) && rec(i+3) {
			return true
		}
		if i+2 <= len(rs) && unicode.IsUpper(rs[i]) && rs[i+1] == '.' && rec(i+2) {
			return true
		}
		return false
	}
	if len(rs) == 0 {
		return false
	}
	return rec(0)
}

func isAposTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func applyApostrophe(s string) (string, bool) {
	rs := []rune(s)
	if len(rs) < 3 {
		return "", false
	}
	switch unicode.ToLower(rs[0]) {
	case 'd', 'o', 'l':
	default:
		return "", false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return "", false
	}
	rest := rs[2:]
	if !unicode.IsLetter(rest[0]) {
		return "", false
	}
	split := len(rest)
	if len(rest) >= 3 && isAposTail(rest[len(rest)-2]) && isAposTail(rest[len(rest)-1]) {
		body := rest[:len(rest)-2]
		ok := len(body) >= 1
		for _, r := range body {
			if !unicode.IsLetter(r) {
				ok = false
				break
			}
		}
		if ok {
			split = len(rest) - 2
		}
	}
	for _, r := range rest[:split] {
		if !unicode.IsLetter(r) {
			return "", false
		}
	}
	for _, r := range rest[split:] {
		if !isAposTail(r) {
			return "", false
		}
	}
	first := rs[0]
	if first != 'a' && first != 'e' && first != 'i' && first != 'o' && first != 'u' &&
		first != 'A' && first != 'E' && first != 'I' && first != 'O' && first != 'U' {
		first = unicode.ToLower(first)
	} else {
		first = unicode.ToUpper(first)
	}
	third := pyUpper(string(rs[2]))
	var b []rune
	b = append(b, first, rs[1])
	b = append(b, []rune(third)...)
	b = append(b, rs[3:]...)
	return string(b), true
}

func mcRest(rs []rune) (string, bool) {
	if len(rs) < 4 || !isWord(rs[2]) {
		return "", false
	}
	mc := (rs[0] == 'M' || rs[0] == 'm') && rs[1] == 'c'
	mc = mc || (rs[0] == 'M' && rs[1] == 'C')
	if !mc {
		return "", false
	}
	return string(rs[2:]), true
}

func isHonorific(rs []rune) bool {
	switch len(rs) {
	case 2:
		a, b := unicode.ToLower(rs[0]), unicode.ToLower(rs[1])
		return (a == 'm' && b == 'r') || (a == 'm' && b == 's') || (a == 'd' && b == 'r')
	case 3:
		return unicode.ToLower(rs[0]) == 'm' && unicode.ToLower(rs[1]) == 'r' && unicode.ToLower(rs[2]) == 's'
	default:
		return false
	}
}

func isAllConsonants(s string) bool {
	if utf8.RuneCountInString(s) <= 2 {
		return false
	}
	for _, r := range s {
		switch unicode.ToLower(r) {
		case 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z':
		default:
			return false
		}
	}
	return true
}

func capFirst(s string) string {
	rs := []rune(s)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return s
	}
	return pyUpper(string(rs[:i+1])) + string(rs[i+1:])
}

func splitWS(s string) (words, spaces []string) {
	var cur []rune
	for _, r := range s {
		if isSpace(r) {
			words = append(words, string(cur))
			cur = nil
			spaces = append(spaces, string(r))
		} else {
			cur = append(cur, r)
		}
	}
	words = append(words, string(cur))
	return words, spaces
}

func interleave(words, spaces []string) string {
	buf := make([]string, len(words)+len(spaces))
	copy(buf, words)
	copy(buf[len(words):], spaces)
	for i, w := range words {
		buf[i*2] = w
	}
	for i, sp := range spaces {
		buf[i*2+1] = sp
	}
	out := ""
	for _, part := range buf {
		out += part
	}
	return out
}

func processWord(word string, allCaps bool) string {
	rs := []rune(word)
	if allCaps && matchInitials(rs) {
		return word
	}
	if rewritten, ok := applyApostrophe(word); ok {
		return rewritten
	}
	if rest, ok := mcRest(rs); ok {
		return "Mc" + titlecase(rest, true)
	}
	if isHonorific(rs) {
		return pyUpper(string(rs[0])) + string(rs[1:])
	}
	if hasInlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}
	if isExactSmall(word) {
		return pyLower(word)
	}
	if contains(word, "/") && !contains(word, "//") {
		parts := splitKeep(word, '/')
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return join(parts, "/")
	}
	if contains(word, "-") {
		parts := splitKeep(word, '-')
		for i, p := range parts {
			parts[i] = titlecase(p, false)
		}
		return join(parts, "-")
	}
	if allCaps {
		word = pyLower(word)
	}
	if isAllConsonants(word) {
		return pyUpper(word)
	}
	return capFirst(word)
}

func contains(s, sub string) bool {
	return len(sub) > 0 && (len(s) >= len(sub)) && (indexOf(s, sub) >= 0)
}

func indexOf(s, sub string) int {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}

func splitKeep(s string, sep rune) []string {
	var parts []string
	var cur []rune
	for _, r := range s {
		if r == sep {
			parts = append(parts, string(cur))
			cur = nil
		} else {
			cur = append(cur, r)
		}
	}
	parts = append(parts, string(cur))
	return parts
}

func join(parts []string, sep string) string {
	out := ""
	for i, p := range parts {
		if i > 0 {
			out += sep
		}
		out += p
	}
	return out
}

func titlecase(text string, smallFirstLast bool) string {
	lines := splitNewlines(text)
	processed := make([]string, 0, len(lines))
	for _, line := range lines {
		allCaps := pyUpper(line) == line
		words, spaces := splitWS(line)
		tc := make([]string, len(words))
		for i, word := range words {
			tc[i] = processWord(word, allCaps)
		}
		if smallFirstLast && len(tc) > 0 {
			tc[0] = applySmallFirst(tc[0])
			tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
		}
		joined := interleave(tc, spaces)
		processed = append(processed, applySubphrase(joined))
	}
	return join(processed, "\n")
}

func splitNewlines(s string) []string {
	var lines []string
	var cur []rune
	flush := func() {
		lines = append(lines, string(cur))
		cur = nil
	}
	rs := []rune(s)
	for i := 0; i < len(rs); i++ {
		if rs[i] == '\r' || rs[i] == '\n' {
			flush()
			for i+1 < len(rs) && (rs[i+1] == '\r' || rs[i+1] == '\n') {
				i++
			}
			continue
		}
		cur = append(cur, rs[i])
	}
	flush()
	return lines
}
TITLECASE_GO_SOURCE
find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
