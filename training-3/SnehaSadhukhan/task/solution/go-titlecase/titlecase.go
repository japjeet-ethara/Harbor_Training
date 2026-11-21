package titlecase

import (
	"bufio"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

// Options controls Titlecase. A zero value does not match Python's defaults;
// use DefaultOptions or set SmallFirstLast explicitly.
type Options struct {
	Callback                 func(word string, allCaps bool) string
	SmallFirstLast           bool
	PreserveBlankLines       bool
	NormaliseSpaceCharacters bool
}

// DefaultOptions matches titlecase() defaults: capitalize small words at the ends.
func DefaultOptions() Options {
	return Options{SmallFirstLast: true}
}

type smallAlt struct {
	base   string
	dotted bool
}

// Order matches the source alternation, including v\.? before via and vs\.?.
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

const consonants = "bcdfghjklmnpqrstvwxz"

// Titlecase is the Go port of titlecase(). A nil opts pointer uses DefaultOptions.
func Titlecase(text string, opts *Options) string {
	if opts == nil {
		defaults := DefaultOptions()
		opts = &defaults
	}
	return titlecase(text, *opts)
}

// NewWordlistCallback preserves spellings listed one per line in path.
// An empty path or a path that is not a file yields a callback that always returns "".
func NewWordlistCallback(path string) func(word string, allCaps bool) string {
	noop := func(string, bool) string { return "" }
	if path == "" {
		return noop
	}
	info, err := os.Stat(path)
	if err != nil || info.IsDir() {
		return noop
	}
	file, err := os.Open(path)
	if err != nil {
		return noop
	}
	defer file.Close()

	abbrevs := map[string]string{}
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		trimmed := strings.TrimSpace(scanner.Text())
		if trimmed == "" {
			continue
		}
		abbrevs[strings.ToUpper(trimmed)] = trimmed
	}
	if err := scanner.Err(); err != nil {
		return noop
	}
	return func(word string, _ bool) string {
		if spelled, ok := abbrevs[strings.ToUpper(word)]; ok {
			return spelled
		}
		return ""
	}
}

func titlecase(text string, opts Options) string {
	lines := splitLines(text, opts.PreserveBlankLines)
	processed := make([]string, len(lines))
	for i, line := range lines {
		processed[i] = titlecaseLine(line, opts)
	}
	return strings.Join(processed, "\n")
}

type token struct {
	text      string
	immutable bool
}

func titlecaseLine(line string, opts Options) string {
	allCaps := strings.ToUpper(line) == line
	words, spaces := splitTokens(line)
	tc := make([]token, len(words))
	for i, word := range words {
		tc[i] = processToken(word, allCaps, opts)
	}

	if opts.SmallFirstLast && len(tc) > 0 {
		if !tc[0].immutable {
			tc[0].text = applySmallFirst(tc[0].text)
		}
		last := len(tc) - 1
		if !tc[last].immutable {
			tc[last].text = applySmallLast(tc[last].text)
		}
	}

	parts := make([]string, len(tc))
	for i, tok := range tc {
		parts[i] = tok.text
	}
	var result string
	if opts.NormaliseSpaceCharacters {
		result = strings.Join(parts, " ")
	} else {
		var b strings.Builder
		for i, part := range parts {
			b.WriteString(part)
			if i < len(spaces) {
				b.WriteString(spaces[i])
			}
		}
		result = b.String()
	}
	return applySubphrase(result)
}

func processToken(word string, allCaps bool, opts Options) token {
	if opts.Callback != nil {
		if replaced := opts.Callback(word, allCaps); replaced != "" {
			return token{text: replaced, immutable: true}
		}
	}

	if allCaps && isInitials(word) {
		return token{text: word}
	}
	if rewritten, ok := rewriteApos(word); ok {
		return token{text: rewritten}
	}
	if prefix, rest, ok := splitMac(word); ok {
		child := Options{Callback: opts.Callback, SmallFirstLast: true}
		return token{text: capitalize(prefix) + titlecase(rest, child)}
	}
	if isHonorific(word) {
		return token{text: upperFirst(word)}
	}
	if hasInlinePeriod(word) || (!allCaps && hasInternalCapital(word)) {
		return token{text: word}
	}
	if isSmallWord(word) {
		return token{text: strings.ToLower(word)}
	}
	if strings.Contains(word, "/") && !strings.Contains(word, "//") {
		return token{text: joinPieces(word, "/", opts)}
	}
	if strings.Contains(word, "-") {
		return token{text: joinPieces(word, "-", opts)}
	}
	if allCaps {
		word = strings.ToLower(word)
	}
	if isAllConsonants(word) {
		return token{text: strings.ToUpper(word)}
	}
	return token{text: capFirst(word)}
}

func joinPieces(word, sep string, opts Options) string {
	child := Options{Callback: opts.Callback, SmallFirstLast: false}
	parts := strings.Split(word, sep)
	for i, part := range parts {
		parts[i] = titlecase(part, child)
	}
	return strings.Join(parts, sep)
}

func splitLines(text string, preserve bool) []string {
	lines := []string{}
	start := 0
	for i := 0; i < len(text); i++ {
		if text[i] != '\r' && text[i] != '\n' {
			continue
		}
		lines = append(lines, text[start:i])
		if preserve {
			start = i + 1
			continue
		}
		for i+1 < len(text) && (text[i+1] == '\r' || text[i+1] == '\n') {
			i++
		}
		start = i + 1
	}
	lines = append(lines, text[start:])
	return lines
}

func splitTokens(line string) (words, spaces []string) {
	if line == "" {
		return []string{""}, nil
	}
	var cur strings.Builder
	inWord := true
	flushSpace := func() {
		spaces = append(spaces, cur.String())
		cur.Reset()
	}
	for _, r := range line {
		if unicode.IsSpace(r) {
			if inWord {
				words = append(words, cur.String())
				cur.Reset()
				inWord = false
			} else {
				flushSpace()
				words = append(words, "")
			}
			cur.WriteRune(r)
			continue
		}
		if !inWord {
			flushSpace()
			inWord = true
		}
		cur.WriteRune(r)
	}
	if inWord {
		words = append(words, cur.String())
	} else {
		flushSpace()
		words = append(words, "")
	}
	return words, spaces
}

func isPunct(r rune) bool {
	switch r {
	case '!', '"', '“', '#', '$', '%', '&', '\'', '‘', '(', ')', '*', '+', ',',
		'-', '–', '‒', '—', '―', '.', '/', ':', ';', '?', '@', '[', '\\', ']',
		'_', '`', '{', '|', '}', '~':
		return true
	default:
		return false
	}
}

func isSubDelim(r rune) bool {
	switch r {
	case ':', '.', ';', '?', '!', '-', '–', '‒', '—', '―':
		return true
	default:
		return false
	}
}

func isWord(r rune) bool {
	if unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.IsMark(r) {
		return true
	}
	return unicode.Is(unicode.Pc, r)
}

func isBoundary(s string, i int) bool {
	var left, right bool
	if i > 0 {
		r, _ := utf8.DecodeLastRuneInString(s[:i])
		left = isWord(r)
	}
	if i < len(s) {
		r, _ := utf8.DecodeRuneInString(s[i:])
		right = isWord(r)
	}
	return left != right
}

func isSmallWord(s string) bool {
	for _, alt := range smallAlts {
		if strings.EqualFold(s, alt.base) {
			return true
		}
		if alt.dotted && strings.EqualFold(s, alt.base+".") {
			return true
		}
	}
	return false
}

func matchSmallPrefix(s string, i int, fold, boundary bool) (int, bool) {
	for _, alt := range smallAlts {
		n := len(alt.base)
		if i+n > len(s) || !eqPrefix(s[i:i+n], alt.base, fold) {
			continue
		}
		if alt.dotted && i+n < len(s) && s[i+n] == '.' {
			end := i + n + 1
			if !boundary || isBoundary(s, end) {
				return end, true
			}
		}
		end := i + n
		if !boundary || isBoundary(s, end) {
			return end, true
		}
	}
	return 0, false
}

func eqPrefix(got, want string, fold bool) bool {
	if fold {
		return strings.EqualFold(got, want)
	}
	return got == want
}

func applySmallFirst(s string) string {
	ends := []int{0}
	pos := 0
	for pos < len(s) {
		r, size := utf8.DecodeRuneInString(s[pos:])
		if !isPunct(r) {
			break
		}
		pos += size
		ends = append(ends, pos)
	}
	for k := len(ends) - 1; k >= 0; k-- {
		start := ends[k]
		end, ok := matchSmallPrefix(s, start, true, true)
		if !ok {
			continue
		}
		return s[:start] + capitalize(s[start:end]) + s[end:]
	}
	return s
}

func applySmallLast(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeLastRuneInString(s)
	if isPunct(r) {
		if start, ok := matchSmallSuffix(s, len(s)-size); ok {
			return s[:start] + capitalize(s[start:])
		}
	}
	if start, ok := matchSmallSuffix(s, len(s)); ok {
		return s[:start] + capitalize(s[start:])
	}
	return s
}

func matchSmallSuffix(s string, end int) (int, bool) {
	for _, alt := range smallAlts {
		lengths := []int{}
		if alt.dotted && end > len(alt.base) && end-1 < len(s) && s[end-1] == '.' {
			lengths = append(lengths, len(alt.base)+1)
		}
		lengths = append(lengths, len(alt.base))
		for _, n := range lengths {
			if n > end {
				continue
			}
			start := end - n
			if start > 0 && !utf8.RuneStart(s[start]) {
				continue
			}
			form := alt.base
			if n == len(alt.base)+1 {
				form = alt.base + "."
			}
			if !strings.EqualFold(s[start:end], form) || !isBoundary(s, start) {
				continue
			}
			return start, true
		}
	}
	return 0, false
}

func applySubphrase(s string) string {
	var b strings.Builder
	i := 0
	for i < len(s) {
		r, size := utf8.DecodeRuneInString(s[i:])
		if isSubDelim(r) && i+size < len(s) && s[i+size] == ' ' {
			rest := i + size + 1
			if end, ok := matchSmallPrefix(s, rest, false, false); ok {
				b.WriteString(s[i:rest])
				b.WriteString(capitalize(s[rest:end]))
				i = end
				continue
			}
		}
		b.WriteRune(r)
		i += size
	}
	return b.String()
}

func capitalize(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + strings.ToLower(s[size:])
}

func upperFirst(s string) string {
	r, size := utf8.DecodeRuneInString(s)
	return string(unicode.ToUpper(r)) + s[size:]
}

func capFirst(s string) string {
	i := 0
	for i < len(s) {
		r, size := utf8.DecodeRuneInString(s[i:])
		if !isPunct(r) {
			if unicode.IsLetter(r) {
				return strings.ToUpper(s[:i+size]) + s[i+size:]
			}
			return s
		}
		i += size
	}
	return s
}

func hasInternalCapital(s string) bool {
	i := 0
	for i < len(s) {
		r, size := utf8.DecodeRuneInString(s[i:])
		if !isPunct(r) {
			break
		}
		i += size
	}
	seenLetter := false
	for i < len(s) {
		r, size := utf8.DecodeRuneInString(s[i:])
		if !unicode.IsLetter(r) {
			return false
		}
		if seenLetter && unicode.Is(unicode.Lu, r) {
			return true
		}
		seenLetter = true
		i += size
	}
	return false
}

func hasInlinePeriod(s string) bool {
	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		if unicode.IsLetter(r) && i+size < len(s) && s[i+size] == '.' {
			if i+size+1 < len(s) {
				r2, _ := utf8.DecodeRuneInString(s[i+size+1:])
				if unicode.IsLetter(r2) {
					return true
				}
			}
		}
		i += size
	}
	return false
}

func isInitials(s string) bool {
	if s == "" {
		return false
	}
	var walk func(int) bool
	walk = func(i int) bool {
		if i == len(s) {
			return true
		}
		r, size := utf8.DecodeRuneInString(s[i:])
		if !unicode.Is(unicode.Lu, r) || i+size >= len(s) || s[i+size] != '.' {
			return false
		}
		next := i + size + 1
		if walk(next) {
			return true
		}
		if next >= len(s) {
			return false
		}
		r2, size2 := utf8.DecodeRuneInString(s[next:])
		if !unicode.Is(unicode.Lu, r2) {
			return false
		}
		return walk(next + size2)
	}
	return walk(0)
}

func rewriteApos(s string) (string, bool) {
	rs := []rune(s)
	if len(rs) < 3 {
		return "", false
	}
	switch rs[0] {
	case 'd', 'o', 'l', 'D', 'O', 'L':
	default:
		return "", false
	}
	if rs[1] != '\'' && rs[1] != '‘' {
		return "", false
	}
	i := 2
	if !unicode.IsLetter(rs[i]) {
		return "", false
	}
	i++
	for i < len(rs) && unicode.IsLetter(rs[i]) {
		i++
	}
	if i != len(rs) {
		if len(rs)-i != 2 {
			return "", false
		}
		for _, r := range rs[i:] {
			if r != '\'' && r != 's' {
				return "", false
			}
		}
	}
	if strings.ContainsRune("aeiouAEIOU", rs[0]) {
		rs[0] = unicode.ToUpper(rs[0])
	} else {
		rs[0] = unicode.ToLower(rs[0])
	}
	rs[2] = unicode.ToUpper(rs[2])
	return string(rs), true
}

func splitMac(s string) (prefix, rest string, ok bool) {
	if strings.HasPrefix(s, "Mc") || strings.HasPrefix(s, "mc") || strings.HasPrefix(s, "MC") {
		prefix = s[:2]
		rest = s[2:]
	} else {
		return "", "", false
	}
	r, size := utf8.DecodeRuneInString(rest)
	if r == utf8.RuneError && size == 1 && rest != "\uFFFD" {
		return "", "", false
	}
	if !isWord(r) || len(rest) < size+1 {
		return "", "", false
	}
	if strings.ContainsRune(rest[size:], '\n') {
		return "", "", false
	}
	return prefix, rest, true
}

func isHonorific(s string) bool {
	switch strings.ToLower(s) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func isAllConsonants(s string) bool {
	if s == "" {
		return false
	}
	n := 0
	for _, r := range s {
		n++
		if r > unicode.MaxASCII || !strings.ContainsRune(consonants, unicode.ToLower(r)) {
			return false
		}
	}
	return n > 2
}
