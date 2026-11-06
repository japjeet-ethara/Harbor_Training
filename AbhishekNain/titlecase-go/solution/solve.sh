#!/bin/bash
set -euo pipefail

mkdir -p /app
cd /app

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"unicode"
)

func main() {
	cfg, err := parseArgs(os.Args[1:])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}

	text, err := cfg.readInput()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	cb := wordCallback(cfg.wordlistPath())
	out := titlecase(text, cb, true, cfg.preserve)
	if err := cfg.writeOutput(out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

type config struct {
	positionals []string
	inputFile   *string
	outputFile  *string
	wordlist    *string
	preserve    bool
}

func parseArgs(args []string) (config, error) {
	var cfg config
	for i := 0; i < len(args); i++ {
		a := args[i]
		if a == "--" {
			cfg.positionals = append(cfg.positionals, args[i+1:]...)
			break
		}
		if a == "--preserve-blank-lines" {
			cfg.preserve = true
			continue
		}
		if strings.HasPrefix(a, "--") {
			name, val, ok := strings.Cut(a, "=")
			name = strings.TrimPrefix(name, "--")
			switch name {
			case "input-file", "output-file", "wordlist":
				if !ok {
					if i+1 >= len(args) {
						return cfg, fmt.Errorf("option --%s requires a value", name)
					}
					i++
					val = args[i]
				}
				switch name {
				case "input-file":
					cfg.inputFile = &val
				case "output-file":
					cfg.outputFile = &val
				case "wordlist":
					cfg.wordlist = &val
				}
			default:
				return cfg, fmt.Errorf("unrecognized option --%s", name)
			}
			continue
		}
		if strings.HasPrefix(a, "-") && a != "-" {
			var name, val string
			var attached bool
			switch {
			case a == "-f" || a == "-o" || a == "-w":
				name = a
			case strings.HasPrefix(a, "-f") || strings.HasPrefix(a, "-o") || strings.HasPrefix(a, "-w"):
				name = a[:2]
				val = a[2:]
				attached = true
			default:
				return cfg, fmt.Errorf("unrecognized option %s", a)
			}
			if !attached {
				if i+1 >= len(args) {
					return cfg, fmt.Errorf("option %s requires a value", name)
				}
				i++
				val = args[i]
			}
			switch name {
			case "-f":
				cfg.inputFile = &val
			case "-o":
				cfg.outputFile = &val
			case "-w":
				cfg.wordlist = &val
			}
			continue
		}
		cfg.positionals = append(cfg.positionals, a)
	}
	if cfg.inputFile != nil && len(cfg.positionals) > 0 {
		return cfg, fmt.Errorf("positional text cannot be combined with --input-file")
	}
	return cfg, nil
}

func (c config) wordlistPath() string {
	if c.wordlist != nil {
		return *c.wordlist
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".titlecase.txt")
}

func (c config) readInput() (string, error) {
	if len(c.positionals) > 0 {
		return strings.Join(c.positionals, " "), nil
	}
	var r io.Reader = os.Stdin
	if c.inputFile != nil && *c.inputFile != "-" {
		f, err := os.Open(*c.inputFile)
		if err != nil {
			return "", err
		}
		defer f.Close()
		r = f
	}
	b, err := io.ReadAll(r)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

func (c config) writeOutput(text string) error {
	if c.outputFile == nil || *c.outputFile == "-" {
		_, err := os.Stdout.Write([]byte(text))
		return err
	}
	return os.WriteFile(*c.outputFile, []byte(text), 0o644)
}

func wordCallback(path string) func(string, bool) (string, bool) {
	if path == "" {
		return nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	list := map[string]string{}
	for _, line := range splitRecordLines(string(data)) {
		if line == "" {
			continue
		}
		abbr := strings.TrimSpace(line)
		list[strings.ToUpper(abbr)] = abbr
	}
	return func(word string, _ bool) (string, bool) {
		value, ok := list[strings.ToUpper(word)]
		if !ok || value == "" {
			return "", false
		}
		return value, true
	}
}

func splitRecordLines(s string) []string {
	if s == "" {
		return nil
	}
	s = strings.ReplaceAll(s, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	parts := strings.Split(s, "\n")
	if len(parts) > 0 && parts[len(parts)-1] == "" {
		parts = parts[:len(parts)-1]
	}
	return parts
}

type wordCB func(string, bool) (string, bool)

func titlecase(text string, cb wordCB, smallFirstLast, preserve bool) string {
	lines := splitTitleLines(text, preserve)
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = processLine(line, cb, smallFirstLast)
	}
	return strings.Join(out, "\n")
}

func splitTitleLines(text string, preserve bool) []string {
	rs := []rune(text)
	var lines []string
	var cur []rune
	newline := func(r rune) bool { return r == '\n' || r == '\r' }
	if preserve {
		for _, r := range rs {
			if newline(r) {
				lines = append(lines, string(cur))
				cur = nil
				continue
			}
			cur = append(cur, r)
		}
		lines = append(lines, string(cur))
		return lines
	}
	for i := 0; i < len(rs); {
		if newline(rs[i]) {
			lines = append(lines, string(cur))
			cur = nil
			for i < len(rs) && newline(rs[i]) {
				i++
			}
			continue
		}
		cur = append(cur, rs[i])
		i++
	}
	lines = append(lines, string(cur))
	return lines
}

type token struct {
	text      string
	immutable bool
}

func processLine(line string, cb wordCB, smallFirstLast bool) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitSpaces(line)
	tokens := make([]token, len(words))
	for i, word := range words {
		tokens[i] = convertWord(word, allCaps, cb, smallFirstLast)
	}
	if smallFirstLast && len(tokens) > 0 {
		last := len(tokens) - 1
		if !tokens[0].immutable {
			tokens[0].text = applySmallFirst(tokens[0].text)
		}
		if !tokens[last].immutable {
			tokens[last].text = applySmallLast(tokens[last].text)
		}
	}
	parts := make([]string, len(tokens))
	for i, tok := range tokens {
		parts[i] = tok.text
	}
	return applySubphrase(joinWords(parts, spaces))
}

func splitSpaces(line string) (words, spaces []string) {
	var cur []rune
	for _, r := range line {
		if unicode.IsSpace(r) {
			words = append(words, string(cur))
			cur = nil
			spaces = append(spaces, string(r))
			continue
		}
		cur = append(cur, r)
	}
	words = append(words, string(cur))
	return words, spaces
}

func joinWords(words, spaces []string) string {
	var b strings.Builder
	for i, word := range words {
		b.WriteString(word)
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func convertWord(word string, allCaps bool, cb wordCB, smallFirstLast bool) token {
	if cb != nil {
		if replaced, ok := cb(word, allCaps); ok {
			return token{text: replaced, immutable: true}
		}
	}
	if allCaps && isUCInitials(word) {
		return token{text: word}
	}
	if isApostropheName(word) {
		return token{text: applyApostrophe(word)}
	}
	if prefix, rest, ok := splitMc(word); ok {
		return token{text: capitalize(prefix) + titlecase(rest, cb, true, false)}
	}
	if isHonorific(word) {
		return token{text: upperFirst(word)}
	}
	if hasInlinePeriod(word) || (!allCaps && hasInteriorUpper(word)) {
		return token{text: word}
	}
	if isSmallWord(word) {
		return token{text: strings.ToLower(word)}
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		parts := strings.Split(word, "/")
		for i, part := range parts {
			parts[i] = titlecase(part, cb, false, false)
		}
		return token{text: strings.Join(parts, "/")}
	}
	if strings.Contains(word, "-") {
		parts := strings.Split(word, "-")
		for i, part := range parts {
			parts[i] = titlecase(part, cb, false, false)
		}
		return token{text: strings.Join(parts, "-")}
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if isConsonantAcronym(word) {
		return token{text: strings.ToUpper(word)}
	}
	return token{text: capFirst(word)}
}

func isUCInitials(word string) bool {
	if word == "" {
		return false
	}
	return matchInitials([]rune(word), 0)
}

func matchInitials(rs []rune, i int) bool {
	if i == len(rs) {
		return true
	}
	if i+1 < len(rs) && unicode.IsUpper(rs[i]) && rs[i+1] == '.' {
		if matchInitials(rs, i+2) {
			return true
		}
	}
	if i+2 < len(rs) && unicode.IsUpper(rs[i]) && rs[i+1] == '.' && unicode.IsUpper(rs[i+2]) {
		if matchInitials(rs, i+3) {
			return true
		}
	}
	return false
}

func isApostropheName(word string) bool {
	rs := []rune(word)
	if len(rs) < 3 || !isDOL(rs[0]) || (rs[1] != '\'' && rs[1] != '\u2018') {
		return false
	}
	rest := rs[2:]
	if len(rest) >= 3 && isApostropheTail(rest[len(rest)-2]) && isApostropheTail(rest[len(rest)-1]) && allLetters(rest[:len(rest)-2]) {
		return true
	}
	return allLetters(rest)
}

func isDOL(r rune) bool {
	switch unicode.ToLower(r) {
	case 'd', 'o', 'l':
		return true
	default:
		return false
	}
}

func isApostropheTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func allLetters(rs []rune) bool {
	if len(rs) == 0 {
		return false
	}
	for _, r := range rs {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return true
}

func applyApostrophe(word string) string {
	rs := []rune(word)
	if isVowel(rs[0]) {
		rs[0] = unicode.ToUpper(rs[0])
	} else {
		rs[0] = unicode.ToLower(rs[0])
	}
	rs[2] = unicode.ToUpper(rs[2])
	return string(rs)
}

func isVowel(r rune) bool {
	switch unicode.ToLower(r) {
	case 'a', 'e', 'i', 'o', 'u':
		return true
	default:
		return false
	}
}

func splitMc(word string) (prefix, rest string, ok bool) {
	rs := []rune(word)
	if len(rs) < 4 {
		return "", "", false
	}
	prefix = string(rs[:2])
	if prefix != "Mc" && prefix != "mc" && prefix != "MC" {
		return "", "", false
	}
	if !isWord(rs[2]) {
		return "", "", false
	}
	return prefix, string(rs[2:]), true
}

func isHonorific(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func upperFirst(word string) string {
	rs := []rune(word)
	if len(rs) == 0 {
		return word
	}
	rs[0] = unicode.ToUpper(rs[0])
	return string(rs)
}

func hasInlinePeriod(word string) bool {
	rs := []rune(word)
	for i := 0; i+2 < len(rs); i++ {
		if unicode.IsLetter(rs[i]) && rs[i+1] == '.' && unicode.IsLetter(rs[i+2]) {
			return true
		}
	}
	return false
}

func hasInteriorUpper(word string) bool {
	rs := []rune(word)
	i := 0
	for i < len(rs) && isPunct(rs[i]) {
		i++
	}
	if i >= len(rs) || !unicode.IsLetter(rs[i]) {
		return false
	}
	for _, r := range rs[i+1:] {
		if !unicode.IsLetter(r) {
			return false
		}
		if unicode.IsUpper(r) {
			return true
		}
	}
	return false
}

func isConsonantAcronym(word string) bool {
	rs := []rune(word)
	if len(rs) <= 2 {
		return false
	}
	for _, r := range rs {
		if r >= 'A' && r <= 'Z' {
			r = r - 'A' + 'a'
		}
		if r < 'a' || r > 'z' {
			return false
		}
		switch r {
		case 'a', 'e', 'i', 'o', 'u', 'y':
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	rs := []rune(word)
	for i, r := range rs {
		if isPunct(r) {
			continue
		}
		if unicode.IsLetter(r) {
			rs[i] = unicode.ToUpper(r)
			return string(rs)
		}
		return word
	}
	return word
}

func capitalize(s string) string {
	rs := []rune(s)
	if len(rs) == 0 {
		return s
	}
	rs[0] = unicode.ToUpper(rs[0])
	for i := 1; i < len(rs); i++ {
		rs[i] = unicode.ToLower(rs[i])
	}
	return string(rs)
}

const punctChars = "!\"#$%&'()*+,-./:;?@[\\]_`{|}~\u2012\u2013\u2014\u2015\u2018\u201c"

func isPunct(r rune) bool {
	return strings.ContainsRune(punctChars, r)
}

type alternative struct {
	lit    string
	optDot bool
}

var smallAlts = []alternative{
	{"a", false}, {"an", false}, {"and", false}, {"as", false}, {"at", false},
	{"but", false}, {"by", false}, {"en", false}, {"for", false}, {"if", false},
	{"in", false}, {"of", false}, {"on", false}, {"or", false}, {"the", false},
	{"to", false}, {"v", true}, {"via", false}, {"vs", true},
}

func isSmallWord(word string) bool {
	rs := []rune(word)
	for _, alt := range smallAlts {
		for _, end := range candidateEnds(rs, 0, alt, true) {
			if end == len(rs) {
				return true
			}
		}
	}
	return false
}

func applySmallFirst(token string) string {
	rs := []rune(token)
	limit := 0
	for limit < len(rs) && isPunct(rs[limit]) {
		limit++
	}
	for p := limit; p >= 0; p-- {
		if end, ok := matchSmall(rs, p, true); ok {
			return string(rs[:p]) + capitalize(string(rs[p:end])) + string(rs[end:])
		}
	}
	return token
}

func applySmallLast(token string) string {
	rs := []rune(token)
	if len(rs) == 0 {
		return token
	}
	if isPunct(rs[len(rs)-1]) {
		if start, ok := matchAltEnding(rs, len(rs)-1, true); ok && isBoundary(rs, start) {
			return string(rs[:start]) + capitalize(string(rs[start:]))
		}
	}
	if start, ok := matchAltEnding(rs, len(rs), true); ok && isBoundary(rs, start) {
		return string(rs[:start]) + capitalize(string(rs[start:]))
	}
	return token
}

func applySubphrase(s string) string {
	rs := []rune(s)
	var out []rune
	for i := 0; i < len(rs); {
		if isSubDelim(rs[i]) && i+1 < len(rs) && rs[i+1] == ' ' {
			if end, ok := matchSmall(rs, i+2, false); ok {
				out = append(out, rs[i], ' ')
				out = append(out, []rune(capitalize(string(rs[i+2:end])))...)
				i = end
				continue
			}
		}
		out = append(out, rs[i])
		i++
	}
	return string(out)
}

func isSubDelim(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '\u2012', '\u2013', '\u2014', '\u2015':
		return true
	default:
		return false
	}
}

func matchSmall(rs []rune, i int, fold bool) (int, bool) {
	for _, alt := range smallAlts {
		for _, end := range candidateEnds(rs, i, alt, fold) {
			if !fold || isBoundary(rs, end) {
				if fold && !isBoundary(rs, end) {
					continue
				}
				if !fold {
					return end, true
				}
				return end, true
			}
		}
	}
	return 0, false
}

func matchAltEnding(rs []rune, end int, fold bool) (int, bool) {
	for _, alt := range smallAlts {
		lit := []rune(alt.lit)
		if alt.optDot && end >= len(lit)+1 && rs[end-1] == '.' && equalRunes(rs[end-len(lit)-1:end-1], lit, fold) {
			return end - len(lit) - 1, true
		}
		if end >= len(lit) && equalRunes(rs[end-len(lit):end], lit, fold) {
			return end - len(lit), true
		}
	}
	return 0, false
}

func candidateEnds(rs []rune, i int, alt alternative, fold bool) []int {
	lit := []rune(alt.lit)
	if i+len(lit) > len(rs) || !equalRunes(rs[i:i+len(lit)], lit, fold) {
		return nil
	}
	base := i + len(lit)
	if alt.optDot && base < len(rs) && rs[base] == '.' {
		return []int{base + 1, base}
	}
	return []int{base}
}

func equalRunes(got, want []rune, fold bool) bool {
	if len(got) != len(want) {
		return false
	}
	for i := range got {
		a, b := got[i], want[i]
		if fold {
			a, b = unicode.ToLower(a), unicode.ToLower(b)
		}
		if a != b {
			return false
		}
	}
	return true
}

func isBoundary(rs []rune, i int) bool {
	left := i > 0 && isWord(rs[i-1])
	right := i < len(rs) && isWord(rs[i])
	return left != right
}

func isWord(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_'
}
EOF

go build -o /app/titlecase .
