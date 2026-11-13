package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
)

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

type smallWord struct {
	text string
	dot  bool
}

var smallWords = []smallWord{
	{"a", false}, {"an", false}, {"and", false}, {"as", false}, {"at", false},
	{"but", false}, {"by", false}, {"en", false}, {"for", false}, {"if", false},
	{"in", false}, {"of", false}, {"on", false}, {"or", false}, {"the", false},
	{"to", false}, {"v", true}, {"via", false}, {"vs", true},
}

func belongs(table []rune, r rune) bool {
	i := sort.Search(len(table)/2, func(i int) bool { return table[2*i+1] >= r })
	return i < len(table)/2 && table[2*i] <= r
}

func mapped(r rune, table map[rune]string) string {
	if value, ok := table[r]; ok {
		return value
	}
	return string(r)
}

func fold(r rune) rune {
	if value, ok := foldMap[r]; ok {
		return []rune(value)[0]
	}
	return r
}

func upper(s string) string {
	var out strings.Builder
	for _, r := range s {
		out.WriteString(mapped(r, upperMap))
	}
	return out.String()
}

func lowerAt(text []rune, i int) string {
	if text[i] != 'Σ' {
		return mapped(text[i], lowerMap)
	}
	before, after := i-1, i+1
	for before >= 0 && belongs(ignorableChars, text[before]) {
		before--
	}
	for after < len(text) && belongs(ignorableChars, text[after]) {
		after++
	}
	if before >= 0 && belongs(casedChars, text[before]) && (after == len(text) || !belongs(casedChars, text[after])) {
		return "ς"
	}
	return "σ"
}

func lower(s string) string {
	text := []rune(s)
	var out strings.Builder
	for i := range text {
		out.WriteString(lowerAt(text, i))
	}
	return out.String()
}

func capitalize(s string) string {
	text := []rune(s)
	if len(text) == 0 {
		return s
	}
	var out strings.Builder
	out.WriteString(mapped(text[0], titleMap))
	for i := 1; i < len(text); i++ {
		out.WriteString(lowerAt(text, i))
	}
	return out.String()
}

func boundary(text []rune, i int) bool {
	left := i > 0 && belongs(wordChars, text[i-1])
	right := i < len(text) && belongs(wordChars, text[i])
	return left != right
}

func endings(text []rune, start int, word smallWord, insensitive bool) []int {
	letters := []rune(word.text)
	if start+len(letters) > len(text) {
		return nil
	}
	for i, want := range letters {
		got := text[start+i]
		if insensitive {
			got = fold(got)
		}
		if got != want {
			return nil
		}
	}
	end := start + len(letters)
	if word.dot && end < len(text) && text[end] == '.' {
		return []int{end + 1, end}
	}
	return []int{end}
}

func isSmall(s string) bool {
	text := []rune(s)
	for _, word := range smallWords {
		for _, end := range endings(text, 0, word, true) {
			if end == len(text) {
				return true
			}
		}
	}
	return false
}

func firstSmall(s string) string {
	text := []rune(s)
	start := 0
	for start < len(text) && strings.ContainsRune(punctuation, text[start]) {
		start++
	}
	for ; start >= 0; start-- {
		for _, word := range smallWords {
			for _, end := range endings(text, start, word, true) {
				if boundary(text, end) {
					return string(text[:start]) + capitalize(string(text[start:end])) + string(text[end:])
				}
			}
		}
	}
	return s
}

func lastSmall(s string) string {
	text := []rune(s)
	for start := 0; start < len(text); start++ {
		if !boundary(text, start) {
			continue
		}
		for _, word := range smallWords {
			for _, end := range endings(text, start, word, true) {
				if end == len(text) || (end+1 == len(text) && strings.ContainsRune(punctuation, text[end])) {
					return string(text[:start]) + capitalize(string(text[start:]))
				}
			}
		}
	}
	return s
}

func subphrases(s string) string {
	text := []rune(s)
	var out strings.Builder
	for i := 0; i < len(text); {
		end := 0
		if i+2 < len(text) && strings.ContainsRune(":.;?!-–‒—―", text[i]) && text[i+1] == ' ' {
			for _, word := range smallWords {
				matches := endings(text, i+2, word, false)
				if len(matches) > 0 {
					end = matches[0]
					break
				}
			}
		}
		if end > 0 {
			out.WriteString(string(text[i : i+2]))
			out.WriteString(capitalize(string(text[i+2 : end])))
			i = end
		} else {
			out.WriteRune(text[i])
			i++
		}
	}
	return out.String()
}

func initials(text []rune) bool {
	if len(text) == 0 {
		return false
	}
	valid := make([]bool, len(text)+1)
	valid[len(text)] = true
	for i := len(text) - 2; i >= 0; i-- {
		if belongs(upperLetters, text[i]) && text[i+1] == '.' {
			valid[i] = valid[i+2] || (i+2 < len(text) && belongs(upperLetters, text[i+2]) && valid[i+3])
		}
	}
	return valid[0]
}

func letterSequence(text []rune) bool {
	if len(text) == 0 {
		return false
	}
	for _, r := range text {
		if !belongs(foldedLetters, r) {
			return false
		}
	}
	return true
}

func apostrophe(text []rune) bool {
	if len(text) < 3 || !strings.ContainsRune("dol", fold(text[0])) || (text[1] != '\'' && text[1] != '‘') {
		return false
	}
	if letterSequence(text[2:]) {
		return true
	}
	return len(text) >= 5 && letterSequence(text[2:len(text)-2]) &&
		(text[len(text)-2] == '\'' || fold(text[len(text)-2]) == 's') &&
		(text[len(text)-1] == '\'' || fold(text[len(text)-1]) == 's')
}

func protected(text []rune, allCaps bool) bool {
	for i := 0; i+2 < len(text); i++ {
		if belongs(foldedLetters, text[i]) && text[i+1] == '.' && belongs(foldedLetters, text[i+2]) {
			return true
		}
	}
	if allCaps {
		return false
	}
	start := 0
	for start < len(text) && strings.ContainsRune(punctuation, text[start]) {
		start++
	}
	for i := start; i < len(text) && belongs(letters, text[i]); i++ {
		if i > start && belongs(upperLetters, text[i]) {
			return true
		}
	}
	return false
}

func consonantWord(text []rune) bool {
	if len(text) < 3 {
		return false
	}
	for _, r := range text {
		if !strings.ContainsRune("bcdfghjklmnpqrstvwxz", fold(r)) {
			return false
		}
	}
	return true
}

type action uint8

const (
	document action = iota
	line
	token
	literal
	assemble
	finishLine
)

type work struct {
	kind       action
	text       string
	edges      bool
	count      int
	separators []string
}

type wordPlan struct {
	value     string
	prefix    string
	children  []string
	separator string
	edges     bool
}

func inspectWord(word string, allCaps bool) wordPlan {
	text := []rune(word)
	done := func(value string) wordPlan { return wordPlan{value: value} }
	if allCaps && initials(text) {
		return done(word)
	}
	if apostrophe(text) {
		head := mapped(text[0], lowerMap)
		if strings.ContainsRune("aeiouAEIOU", text[0]) {
			head = mapped(text[0], upperMap)
		}
		return done(head + string(text[1]) + mapped(text[2], upperMap) + string(text[3:]))
	}
	if len(text) >= 4 && (string(text[:2]) == "Mc" || string(text[:2]) == "mc" || string(text[:2]) == "MC") && belongs(wordChars, text[2]) {
		return wordPlan{prefix: "Mc", children: []string{string(text[2:])}, edges: true}
	}
	var folded strings.Builder
	for _, r := range text {
		folded.WriteRune(fold(r))
	}
	switch folded.String() {
	case "mr", "mrs", "ms", "dr":
		return done(mapped(text[0], upperMap) + string(text[1:]))
	}
	if protected(text, allCaps) {
		return done(word)
	}
	if isSmall(word) {
		return done(lower(word))
	}
	separator := ""
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		separator = "/"
	} else if strings.Contains(word, "-") {
		separator = "-"
	}
	if separator != "" {
		return wordPlan{children: strings.Split(word, separator), separator: separator}
	}
	if allCaps {
		word = lower(word)
		text = []rune(word)
	}
	if consonantWord(text) {
		return done(upper(word))
	}
	for i, r := range text {
		if strings.ContainsRune(punctuation, r) {
			continue
		}
		if belongs(letters, r) {
			return done(string(text[:i]) + mapped(r, upperMap) + string(text[i+1:]))
		}
		break
	}
	return done(word)
}

func splitDocument(text string) []string {
	var parts []string
	start := 0
	for i := 0; i < len(text); {
		if text[i] != '\r' && text[i] != '\n' {
			i++
			continue
		}
		parts = append(parts, text[start:i])
		for i < len(text) && (text[i] == '\r' || text[i] == '\n') {
			i++
		}
		start = i
	}
	return append(parts, text[start:])
}

func splitFields(text string) ([]string, []string) {
	var fields, separators []string
	start := 0
	for offset, r := range text {
		if belongs(spaceChars, r) {
			fields = append(fields, text[start:offset])
			separators = append(separators, string(r))
			start = offset + len(string(r))
		}
	}
	return append(fields, text[start:]), separators
}

func formatTitle(text string) string {
	pending := []work{{kind: document, text: text, edges: true}}
	values := make([]string, 0, 32)
	for len(pending) != 0 {
		current := pending[len(pending)-1]
		pending = pending[:len(pending)-1]
		switch current.kind {
		case document:
			parts := splitDocument(current.text)
			pending = append(pending, work{kind: assemble, text: "\n", count: len(parts)})
			for i := len(parts) - 1; i >= 0; i-- {
				pending = append(pending, work{kind: line, text: parts[i], edges: current.edges})
			}
		case line:
			fields, separators := splitFields(current.text)
			shouting := upper(current.text) == current.text
			pending = append(pending, work{kind: finishLine, edges: current.edges, count: len(fields), separators: separators})
			for i := len(fields) - 1; i >= 0; i-- {
				pending = append(pending, work{kind: token, text: fields[i], edges: shouting})
			}
		case token:
			plan := inspectWord(current.text, current.edges)
			if plan.children == nil {
				values = append(values, plan.value)
				continue
			}
			count := len(plan.children)
			if plan.prefix != "" {
				count++
			}
			pending = append(pending, work{kind: assemble, text: plan.separator, count: count})
			for i := len(plan.children) - 1; i >= 0; i-- {
				pending = append(pending, work{kind: document, text: plan.children[i], edges: plan.edges})
			}
			if plan.prefix != "" {
				pending = append(pending, work{kind: literal, text: plan.prefix})
			}
		case literal:
			values = append(values, current.text)
		case assemble:
			first := len(values) - current.count
			result := strings.Join(values[first:], current.text)
			values = append(values[:first], result)
		case finishLine:
			first := len(values) - current.count
			fields := values[first:]
			if current.edges {
				fields[0] = firstSmall(fields[0])
				last := len(fields) - 1
				fields[last] = lastSmall(fields[last])
			}
			var result strings.Builder
			for i, field := range fields {
				result.WriteString(field)
				if i < len(current.separators) {
					result.WriteString(current.separators[i])
				}
			}
			values = append(values[:first], subphrases(result.String()))
		}
	}
	return values[0]
}

func run(in io.Reader, out io.Writer) error {
	reader := bufio.NewReader(in)
	writer := bufio.NewWriter(out)
	for {
		line, err := reader.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			line = strings.TrimSuffix(line, "\r")
			if _, writeErr := fmt.Fprintln(writer, formatTitle(line)); writeErr != nil {
				return writeErr
			}
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}
	}
	return writer.Flush()
}

func main() {
	if err := run(os.Stdin, os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
