package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"regexp"
	"sort"
	"strings"
)

const marks = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

type edgePattern struct {
	leading []*regexp.Regexp
	ending  *regexp.Regexp
}

type formatter struct {
	initials, names, mc, honorific, dotted, capitals, small, consonants, first *regexp.Regexp
	words, breaks, phrases                                                     *regexp.Regexp
	edges                                                                      []edgePattern
}

func runeClass(values []rune) string {
	var pattern strings.Builder
	for i := 0; i < len(values); i += 2 {
		fmt.Fprintf(&pattern, `\x{%x}-\x{%x}`, values[i], values[i+1])
	}
	return pattern.String()
}

func literalClass(text string) string {
	var pattern strings.Builder
	for _, r := range text {
		fmt.Fprintf(&pattern, `\x{%x}`, r)
	}
	return pattern.String()
}

func insensitive(text string) string {
	var pattern strings.Builder
	for _, r := range text {
		matches := []rune{r}
		for code, target := range foldMap {
			if target == string(r) {
				matches = append(matches, code)
			}
		}
		sort.Slice(matches, func(i, j int) bool { return matches[i] < matches[j] })
		pattern.WriteByte('[')
		pattern.WriteString(literalClass(string(matches)))
		pattern.WriteByte(']')
	}
	return pattern.String()
}

func newFormatter() *formatter {
	letter := "[" + runeClass(letters) + "]"
	letterFold := "[" + runeClass(foldedLetters) + "]"
	capital := "[" + runeClass(upperLetters) + "]"
	word := "[" + runeClass(wordChars) + "]"
	punct := "[" + literalClass(marks) + "]"
	small := []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "via", "vs"}
	var folded, plain []string
	f := &formatter{}
	for _, text := range small {
		base := insensitive(text)
		suffix := ""
		var leading []*regexp.Regexp
		if text == "v" || text == "vs" {
			suffix = `\.?`
			leading = append(leading, regexp.MustCompile("^("+punct+"*)("+base+`\.)`+word))
		}
		leading = append(leading, regexp.MustCompile("^("+punct+"*)("+base+")([^"+runeClass(wordChars)+"]|$)"))
		f.edges = append(f.edges, edgePattern{leading, regexp.MustCompile("^(?:" + base + suffix + ")" + punct + "?$")})
		folded = append(folded, base+suffix)
		plain = append(plain, text+suffix)
	}
	f.initials = regexp.MustCompile("^(?:" + capital + `\.|` + capital + `\.` + capital + ")+$")
	f.names = regexp.MustCompile("^(?:" + insensitive("d") + "|" + insensitive("o") + "|" + insensitive("l") + ")['‘]" + letterFold + "+(?:(?:'|" + insensitive("s") + "){2})?$")
	f.mc = regexp.MustCompile("^([Mm]c|MC)(" + word + ".+)")
	f.honorific = regexp.MustCompile("^(?:" + insensitive("mr") + "|" + insensitive("mrs") + "|" + insensitive("ms") + "|" + insensitive("dr") + ")$")
	f.dotted = regexp.MustCompile(letterFold + `\.` + letterFold)
	f.capitals = regexp.MustCompile("^" + punct + "*?" + letter + "+" + capital + "+?")
	f.small = regexp.MustCompile("^(?:" + strings.Join(folded, "|") + ")$")
	var consonants []string
	for _, r := range "bcdfghjklmnpqrstvwxz" {
		consonants = append(consonants, insensitive(string(r)))
	}
	f.consonants = regexp.MustCompile("^(?:" + strings.Join(consonants, "|") + ")+$")
	f.first = regexp.MustCompile("^" + punct + "*?" + letter)
	f.words = regexp.MustCompile("[" + runeClass(spaceChars) + "]")
	f.breaks = regexp.MustCompile(`[\r\n]+`)
	f.phrases = regexp.MustCompile("([" + literalClass(":.;?!-–‒—―") + "] )(" + strings.Join(plain, "|") + ")")
	return f
}

func inRanges(r rune, intervals []rune) bool {
	position := sort.Search(len(intervals)/2, func(i int) bool { return intervals[2*i+1] >= r })
	return position < len(intervals)/2 && intervals[2*position] <= r
}

func hasBoundary(text []rune, position int) bool {
	before := position > 0 && inRanges(text[position-1], wordChars)
	after := position < len(text) && inRanges(text[position], wordChars)
	return before != after
}

func expand(text string, table map[rune]string) string {
	var result strings.Builder
	for _, r := range text {
		if replacement, exists := table[r]; exists {
			result.WriteString(replacement)
		} else {
			result.WriteRune(r)
		}
	}
	return result.String()
}

func finalSigma(text []rune, position int) bool {
	casedBefore := false
	for i := position - 1; i >= 0; i-- {
		if inRanges(text[i], ignorableChars) {
			continue
		}
		casedBefore = inRanges(text[i], casedChars)
		break
	}
	if !casedBefore {
		return false
	}
	for _, r := range text[position+1:] {
		if !inRanges(r, ignorableChars) {
			return !inRanges(r, casedChars)
		}
	}
	return true
}

func recase(text string, title bool) string {
	runes := []rune(text)
	var result strings.Builder
	for i, r := range runes {
		table := lowerMap
		if title && i == 0 {
			table = titleMap
		} else if r == 'Σ' {
			if finalSigma(runes, i) {
				result.WriteRune('ς')
			} else {
				result.WriteRune('σ')
			}
			continue
		}
		result.WriteString(expand(string(r), table))
	}
	return result.String()
}

func (f *formatter) leading(text string) string {
	for _, edge := range f.edges {
		for _, pattern := range edge.leading {
			match := pattern.FindStringSubmatchIndex(text)
			if match != nil {
				start, end := match[4], match[5]
				return text[:start] + recase(text[start:end], true) + text[end:]
			}
		}
	}
	return text
}

func (f *formatter) ending(text string) string {
	runes := []rune(text)
	for position := range runes {
		if !hasBoundary(runes, position) {
			continue
		}
		tail := string(runes[position:])
		for _, edge := range f.edges {
			if edge.ending.MatchString(tail) {
				return string(runes[:position]) + recase(tail, true)
			}
		}
	}
	return text
}

func (f *formatter) compound(text, separator string) string {
	parts := strings.Split(text, separator)
	for i, part := range parts {
		parts[i] = f.format(part, false)
	}
	return strings.Join(parts, separator)
}

func (f *formatter) token(text string, shouting bool) string {
	if shouting && f.initials.MatchString(text) {
		return text
	}
	if f.names.MatchString(text) {
		runes := []rune(text)
		head := recase(string(runes[0]), false)
		if strings.ContainsRune("aeiouAEIOU", runes[0]) {
			head = expand(string(runes[0]), upperMap)
		}
		return head + string(runes[1]) + expand(string(runes[2]), upperMap) + string(runes[3:])
	}
	if match := f.mc.FindStringSubmatch(text); match != nil {
		return "Mc" + f.format(match[2], true)
	}
	if f.honorific.MatchString(text) {
		runes := []rune(text)
		return expand(string(runes[0]), upperMap) + string(runes[1:])
	}
	if f.dotted.MatchString(text) || (!shouting && f.capitals.MatchString(text)) {
		return text
	}
	if f.small.MatchString(text) {
		return recase(text, false)
	}
	if strings.Contains(text, "/") && !strings.Contains(text, "//") {
		return f.compound(text, "/")
	}
	if strings.Contains(text, "-") {
		return f.compound(text, "-")
	}
	if shouting {
		text = recase(text, false)
	}
	if len([]rune(text)) > 2 && f.consonants.MatchString(text) {
		return expand(text, upperMap)
	}
	return f.first.ReplaceAllStringFunc(text, func(match string) string { return expand(match, upperMap) })
}

func (f *formatter) line(text string, edges bool) string {
	separators := f.words.FindAllStringIndex(text, -1)
	fields := make([]string, 0, len(separators)+1)
	start := 0
	shouting := expand(text, upperMap) == text
	for _, span := range separators {
		fields = append(fields, f.token(text[start:span[0]], shouting))
		start = span[1]
	}
	fields = append(fields, f.token(text[start:], shouting))
	if edges {
		fields[0] = f.leading(fields[0])
		last := len(fields) - 1
		fields[last] = f.ending(fields[last])
	}
	var result strings.Builder
	for i, field := range fields {
		result.WriteString(field)
		if i < len(separators) {
			result.WriteString(text[separators[i][0]:separators[i][1]])
		}
	}
	return f.phrases.ReplaceAllStringFunc(result.String(), func(match string) string {
		position := strings.IndexByte(match, ' ') + 1
		return match[:position] + recase(match[position:], true)
	})
}

func (f *formatter) format(text string, edges bool) string {
	lines := f.breaks.Split(text, -1)
	for i := range lines {
		lines[i] = f.line(lines[i], edges)
	}
	return strings.Join(lines, "\n")
}

func process(input io.Reader, output io.Writer) error {
	f := newFormatter()
	reader := bufio.NewReaderSize(input, 64*1024)
	writer := bufio.NewWriter(output)
	for {
		record, err := reader.ReadString('\n')
		if record != "" {
			record = strings.TrimSuffix(record, "\n")
			record = strings.TrimSuffix(record, "\r")
			if _, writeErr := fmt.Fprintln(writer, f.format(record, true)); writeErr != nil {
				return writeErr
			}
		}
		if err == io.EOF {
			return writer.Flush()
		}
		if err != nil {
			return err
		}
	}
}

func main() {
	if err := process(os.Stdin, os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
