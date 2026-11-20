#!/bin/bash
# Reference solution (oracle): a Go port of python-titlecase, standard library only.
set -euo pipefail
cd /workspace/repo

cat > go.mod <<'GOEOF'
module titlecasego

go 1.21
GOEOF

cat > main.go <<'GOEOF'
// Go port of python-titlecase (stdlib `re` code path). Standard library only.
package main

import (
	"bufio"
	"io"
	"os"
	"strings"
	"unicode"
)

const punctChars = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"
const subPunctChars = ":.;?!-–‒—―"

type smallAlt struct {
	lit string
	dot bool // trailing optional "."
}

// Order matters: it mirrors the alternation order of the Python SMALL pattern.
var smallAlts = []smallAlt{
	{"a", false}, {"an", false}, {"and", false}, {"as", false}, {"at", false},
	{"but", false}, {"by", false}, {"en", false}, {"for", false}, {"if", false},
	{"in", false}, {"of", false}, {"on", false}, {"or", false}, {"the", false},
	{"to", false}, {"v", true}, {"via", false}, {"vs", true},
}

func isPunct(r rune) bool    { return strings.ContainsRune(punctChars, r) }
func isSubPunct(r rune) bool { return strings.ContainsRune(subPunctChars, r) }
func isWordRune(r rune) bool { return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r) }
func isPySpace(r rune) bool  { return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f) }

func capitalize(rs []rune) string {
	if len(rs) == 0 {
		return ""
	}
	out := make([]rune, len(rs))
	out[0] = unicode.ToUpper(rs[0])
	for i := 1; i < len(rs); i++ {
		out[i] = unicode.ToLower(rs[i])
	}
	return string(out)
}

// smallEnds returns candidate end offsets of a SMALL alternative starting at i,
// in regex backtracking order.
func smallEnds(rs []rune, i int, ci bool) []int {
	var ends []int
	for _, a := range smallAlts {
		l := []rune(a.lit)
		if i+len(l) > len(rs) {
			continue
		}
		ok := true
		for k, c := range l {
			r := rs[i+k]
			if ci {
				r = unicode.ToLower(r)
			}
			if r != c {
				ok = false
				break
			}
		}
		if !ok {
			continue
		}
		e := i + len(l)
		if a.dot && e < len(rs) && rs[e] == '.' {
			ends = append(ends, e+1)
		}
		ends = append(ends, e)
	}
	return ends
}

func boundary(rs []rune, i int) bool {
	left := i > 0 && isWordRune(rs[i-1])
	right := i < len(rs) && isWordRune(rs[i])
	return left != right
}

func smallWordsMatch(word string) bool {
	rs := []rune(word)
	for _, e := range smallEnds(rs, 0, true) {
		if e == len(rs) {
			return true
		}
	}
	return false
}

func smallFirst(word string) string {
	rs := []rune(word)
	p := 0
	for p < len(rs) && isPunct(rs[p]) {
		p++
	}
	for _, e := range smallEnds(rs, p, true) {
		if boundary(rs, e) {
			return string(rs[:p]) + capitalize(rs[p:e]) + string(rs[e:])
		}
	}
	return word
}

func smallLast(word string) string {
	rs := []rune(word)
	n := len(rs)
	for i := 0; i < n; i++ {
		if !boundary(rs, i) {
			continue
		}
		for _, e := range smallEnds(rs, i, true) {
			if e == n || (e == n-1 && isPunct(rs[e])) {
				return string(rs[:i]) + capitalize(rs[i:])
			}
		}
	}
	return word
}

func subphrase(s string) string {
	rs := []rune(s)
	var out []rune
	i := 0
	for i < len(rs) {
		if isSubPunct(rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			ends := smallEnds(rs, i+2, false)
			if len(ends) > 0 {
				e := ends[0]
				out = append(out, rs[i], rs[i+1])
				out = append(out, []rune(capitalize(rs[i+2:e]))...)
				i = e
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

func ucInitials(rs []rune) bool {
	n := len(rs)
	up := func(i int) bool { return i < n && rs[i] >= 'A' && rs[i] <= 'Z' }
	memo := map[int]bool{}
	var ok func(pos int) bool
	ok = func(pos int) bool {
		if pos == n {
			return true
		}
		if v, seen := memo[pos]; seen {
			return v
		}
		res := false
		if up(pos) && pos+1 < n && rs[pos+1] == '.' {
			if ok(pos + 2) {
				res = true
			} else if up(pos+2) && ok(pos+3) {
				res = true
			}
		}
		memo[pos] = res
		return res
	}
	return n > 0 && ok(0)
}

func isAposS(r rune) bool { return r == '\'' || r == 's' || r == 'S' }

func aposSecond(rs []rune) bool {
	if len(rs) < 3 {
		return false
	}
	switch unicode.ToLower(rs[0]) {
	case 'd', 'o', 'l':
	default:
		return false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return false
	}
	rest := rs[2:]
	n := 0
	for n < len(rest) && isWordRune(rest[n]) {
		n++
	}
	for k := n; k >= 1; k-- {
		tail := rest[k:]
		if len(tail) == 0 || (len(tail) == 2 && isAposS(tail[0]) && isAposS(tail[1])) {
			return true
		}
	}
	return false
}

func macMc(rs []rune) bool {
	if len(rs) < 4 {
		return false
	}
	a, b := rs[0], rs[1]
	if !((a == 'M' || a == 'm') && b == 'c') && !(a == 'M' && b == 'C') {
		return false
	}
	return isWordRune(rs[2])
}

func isMrMrsMsDr(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	}
	return false
}

func inlinePeriod(rs []rune) bool {
	for i := 0; i+2 < len(rs); i++ {
		if isWordRune(rs[i]) && rs[i+1] == '.' && isWordRune(rs[i+2]) {
			return true
		}
	}
	return false
}

func ucElsewhere(rs []rune) bool {
	p := 0
	for p < len(rs) && isPunct(rs[p]) {
		p++
	}
	isLetter := func(r rune) bool { return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') }
	q := p
	for q < len(rs) && isLetter(rs[q]) {
		q++
	}
	if q-p < 2 {
		return false
	}
	for i := p + 1; i < q; i++ {
		if rs[i] >= 'A' && rs[i] <= 'Z' {
			return true
		}
	}
	return false
}

func allConsonants(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		l := unicode.ToLower(r)
		if l < 'a' || l > 'z' || strings.ContainsRune("aeiouy", l) {
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	rs := []rune(word)
	for p := 0; p < len(rs); p++ {
		if isWordRune(rs[p]) {
			out := make([]rune, len(rs))
			copy(out, rs)
			for i := 0; i <= p; i++ {
				out[i] = unicode.ToUpper(out[i])
			}
			return string(out)
		}
		if !isPunct(rs[p]) {
			return word
		}
	}
	return word
}

func processWord(word string, allCaps bool) string {
	rs := []rune(word)
	if allCaps && ucInitials(rs) {
		return word
	}
	if aposSecond(rs) {
		out := make([]rune, len(rs))
		copy(out, rs)
		if strings.ContainsRune("aeiouAEIOU", out[0]) {
			out[0] = unicode.ToUpper(out[0])
		} else {
			out[0] = unicode.ToLower(out[0])
		}
		out[2] = unicode.ToUpper(out[2])
		return string(out)
	}
	if macMc(rs) {
		return capitalize(rs[:2]) + titlecaseLine(string(rs[2:]), true)
	}
	if isMrMrsMsDr(word) {
		return string(unicode.ToUpper(rs[0])) + string(rs[1:])
	}
	if inlinePeriod(rs) || (!allCaps && ucElsewhere(rs)) {
		return word
	}
	if smallWordsMatch(word) {
		return strings.ToLower(word)
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		return joinParts(strings.Split(word, "/"), "/")
	}
	if strings.Contains(word, "-") {
		return joinParts(strings.Split(word, "-"), "-")
	}
	if allCaps {
		word = strings.ToLower(word)
		rs = []rune(word)
	}
	if allConsonants(rs) && len(rs) > 2 {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func joinParts(parts []string, sep string) string {
	out := make([]string, len(parts))
	for i, p := range parts {
		out[i] = titlecaseLine(p, false)
	}
	return strings.Join(out, sep)
}

func titlecaseLine(line string, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	var words, spaces []string
	var cur []rune
	for _, r := range line {
		if isPySpace(r) {
			words = append(words, string(cur))
			spaces = append(spaces, string(r))
			cur = cur[:0]
		} else {
			cur = append(cur, r)
		}
	}
	words = append(words, string(cur))
	tc := make([]string, len(words))
	for i, w := range words {
		tc[i] = processWord(w, allCaps)
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = smallFirst(tc[0])
		tc[len(tc)-1] = smallLast(tc[len(tc)-1])
	}
	var sb strings.Builder
	for i, w := range tc {
		sb.WriteString(w)
		if i < len(spaces) {
			sb.WriteString(spaces[i])
		}
	}
	return subphrase(sb.String())
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 || err == nil {
			line = strings.TrimSuffix(line, "\n")
			out.WriteString(titlecaseLine(line, true))
			out.WriteByte('\n')
		}
		if err == io.EOF {
			return
		}
		if err != nil {
			os.Exit(1)
		}
	}
}
GOEOF

gofmt -l . >/dev/null 2>&1 || true
go build ./...

# The Python original must be gone.
find /workspace/repo -name '*.py' -delete
