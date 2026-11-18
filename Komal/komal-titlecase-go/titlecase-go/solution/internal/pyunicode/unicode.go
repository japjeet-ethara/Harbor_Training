package pyunicode

import (
	_ "embed"
	"encoding/json"
	"sort"
	"strconv"
	"strings"
)

//go:embed tables.json
var raw []byte

type interval [2]rune

var data struct {
	Word, Space, Cased, Ignorable []interval
	Upper, Lower, Title, Fold     map[string]string
}

var upper, lower, title map[rune]string
var fold map[rune]rune

func init() {
	if err := json.Unmarshal(raw, &data); err != nil {
		panic(err)
	}
	convert := func(src map[string]string) map[rune]string {
		dst := make(map[rune]string, len(src))
		for k, v := range src {
			n, err := strconv.Atoi(k)
			if err != nil {
				panic(err)
			}
			dst[rune(n)] = v
		}
		return dst
	}
	upper, lower, title = convert(data.Upper), convert(data.Lower), convert(data.Title)
	fold = make(map[rune]rune)
	for k, v := range convert(data.Fold) {
		fold[k] = []rune(v)[0]
	}
}

func contains(rs []interval, r rune) bool {
	i := sort.Search(len(rs), func(i int) bool { return rs[i][1] >= r })
	return i < len(rs) && rs[i][0] <= r
}

func Word(r rune) bool  { return contains(data.Word, r) }
func Space(r rune) bool { return contains(data.Space, r) }
func Fold(r rune) rune {
	if f, ok := fold[r]; ok {
		return f
	}
	return r
}

func finalSigma(rs []rune, i int) bool {
	j := i - 1
	for j >= 0 && contains(data.Ignorable, rs[j]) {
		j--
	}
	if j < 0 || !contains(data.Cased, rs[j]) {
		return false
	}
	j = i + 1
	for j < len(rs) && contains(data.Ignorable, rs[j]) {
		j++
	}
	return j == len(rs) || !contains(data.Cased, rs[j])
}

func mapString(s string, table map[rune]string, context bool) string {
	var out strings.Builder
	rs := []rune(s)
	for i, r := range rs {
		if context && r == 'Σ' && finalSigma(rs, i) {
			out.WriteRune('ς')
		} else if v, ok := table[r]; ok {
			out.WriteString(v)
		} else {
			out.WriteRune(r)
		}
	}
	return out.String()
}

func Upper(s string) string { return mapString(s, upper, false) }
func Lower(s string) string { return mapString(s, lower, true) }
func Capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	var out strings.Builder
	for i, r := range rs {
		table := lower
		if i == 0 {
			table = title
		}
		if i > 0 && r == 'Σ' && finalSigma(rs, i) {
			out.WriteRune('ς')
		} else if v, ok := table[r]; ok {
			out.WriteString(v)
		} else {
			out.WriteRune(r)
		}
	}
	return out.String()
}
