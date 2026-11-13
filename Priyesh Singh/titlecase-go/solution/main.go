package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
	"unicode"
)

// Port of python-titlecase titlecase() using the stdlib re path
// (the optional `regex` package is not installed). Go's regexp is not used
// for Unicode word characters or word boundaries.

const punctSet = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

var smallAlts = []string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
}

func main() {
	in, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	sc := bufio.NewScanner(strings.NewReader(string(in)))
	sc.Buffer(make([]byte, 1024*1024), 1024*1024)
	for sc.Scan() {
		fmt.Println(TitleCase(sc.Text()))
	}
	if err := sc.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func TitleCase(line string) string {
	return titlecase(line, true)
}

func titlecase(line string, smallFirstLast bool) string {
	allCaps := line == strings.ToUpper(line)
	words, spaces := splitSpaces(line)
	tc := make([]string, 0, len(words))
	for _, word := range words {
		tc = append(tc, titleWord(word, allCaps))
	}
	if smallFirstLast && len(tc) > 0 {
		tc[0] = applySmallFirst(tc[0])
		tc[len(tc)-1] = applySmallLast(tc[len(tc)-1])
	}
	return applySubphrase(interleave(tc, spaces))
}

func titleWord(word string, allCaps bool) string {
	if allCaps && isUCInitials(word) {
		return word
	}
	if matchApos(word) {
		return applyApos(word)
	}
	if prefix, rest, ok := splitMac(word); ok {
		return capitalize(prefix) + titlecase(rest, true)
	}
	if isMr(word) {
		r := []rune(word)
		return strings.ToUpper(string(r[0])) + string(r[1:])
	}
	if hasInlinePeriod(word) || (!allCaps && hasUCElsewhere(word)) {
		return word
	}
	if isSmallWord(word) {
		return strings.ToLower(word)
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
		word = strings.ToLower(word)
	}
	if allConsonants(word) && len([]rune(word)) > 2 {
		return strings.ToUpper(word)
	}
	return capFirst(word)
}

func splitSpaces(line string) (words, spaces []string) {
	var cur strings.Builder
	flush := func() {
		words = append(words, cur.String())
		cur.Reset()
	}
	for _, r := range line {
		if unicode.IsSpace(r) {
			flush()
			spaces = append(spaces, string(r))
		} else {
			cur.WriteRune(r)
		}
	}
	flush()
	return words, spaces
}

func interleave(words, spaces []string) string {
	var b strings.Builder
	for i := 0; i < len(words) || i < len(spaces); i++ {
		if i < len(words) {
			b.WriteString(words[i])
		}
		if i < len(spaces) {
			b.WriteString(spaces[i])
		}
	}
	return b.String()
}

func isPunct(r rune) bool {
	return strings.ContainsRune(punctSet, r)
}

func isASCIILetter(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z')
}

func isASCIIUpper(r rune) bool {
	return r >= 'A' && r <= 'Z'
}

func isWord(r rune) bool {
	return r == '_' || unicode.IsLetter(r) || unicode.IsDigit(r)
}

func boundaryBefore(r []rune, i int) bool {
	left := i > 0 && isWord(r[i-1])
	right := i < len(r) && isWord(r[i])
	if i == 0 {
		return right
	}
	if i == len(r) {
		return left
	}
	return left != right
}

func isSmallWord(word string) bool {
	for _, alt := range smallAlts {
		if strings.EqualFold(word, alt) {
			return true
		}
	}
	return false
}

func applySmallFirst(word string) string {
	r := []rune(word)
	i := 0
	for i < len(r) && isPunct(r[i]) {
		i++
	}
	for _, alt := range smallAlts {
		ar := []rune(alt)
		end := i + len(ar)
		if end > len(r) {
			continue
		}
		if strings.EqualFold(string(r[i:end]), alt) && boundaryBefore(r, end) {
			return string(r[:i]) + capitalize(string(r[i:end])) + string(r[end:])
		}
	}
	return word
}

func applySmallLast(word string) string {
	r := []rune(word)
	if len(r) == 0 {
		return word
	}
	if isPunct(r[len(r)-1]) {
		if start, ok := smallEndingAt(r, len(r)-1); ok {
			return string(r[:start]) + capitalize(string(r[start:]))
		}
	}
	if start, ok := smallEndingAt(r, len(r)); ok {
		return string(r[:start]) + capitalize(string(r[start:]))
	}
	return word
}

func smallEndingAt(r []rune, end int) (int, bool) {
	for _, alt := range smallAlts {
		ar := []rune(alt)
		start := end - len(ar)
		if start < 0 {
			continue
		}
		if strings.EqualFold(string(r[start:end]), alt) && boundaryBefore(r, start) {
			return start, true
		}
	}
	return 0, false
}

func applySubphrase(s string) string {
	runes := []rune(s)
	var b strings.Builder
	i := 0
	for i < len(runes) {
		if i+2 < len(runes) && isSubPunct(runes[i]) && runes[i+1] == ' ' {
			if n, ok := lowerSmallPrefix(runes[i+2:]); ok {
				b.WriteRune(runes[i])
				b.WriteRune(' ')
				b.WriteString(capitalize(string(runes[i+2 : i+2+n])))
				i += 2 + n
				continue
			}
		}
		b.WriteRune(runes[i])
		i++
	}
	return b.String()
}

func isSubPunct(r rune) bool {
	return strings.ContainsRune(":.;?!-–‒—―", r)
}

func lowerSmallPrefix(r []rune) (int, bool) {
	for _, alt := range smallAlts {
		ar := []rune(alt)
		if len(r) < len(ar) {
			continue
		}
		if string(r[:len(ar)]) == alt {
			return len(ar), true
		}
	}
	return 0, false
}

func capitalize(s string) string {
	r := []rune(s)
	if len(r) == 0 {
		return ""
	}
	return strings.ToUpper(string(r[:1])) + strings.ToLower(string(r[1:]))
}

func isUCInitials(s string) bool {
	r := []rune(s)
	if len(r) == 0 {
		return false
	}
	i := 0
	for i < len(r) {
		if i+2 < len(r) && isASCIIUpper(r[i]) && r[i+1] == '.' && isASCIIUpper(r[i+2]) && (i+3 == len(r) || r[i+3] == '.') {
			if i+3 == len(r) {
				return true
			}
			if r[i+3] == '.' {
				i += 4
				if i == len(r) {
					return true
				}
				continue
			}
		}
		if i+1 < len(r) && isASCIIUpper(r[i]) && r[i+1] == '.' {
			i += 2
			continue
		}
		return false
	}
	return true
}

func matchApos(word string) bool {
	r := []rune(word)
	if len(r) < 3 {
		return false
	}
	if !strings.ContainsRune("dolDOL", r[0]) {
		return false
	}
	if r[1] != '\'' && r[1] != '‘' {
		return false
	}
	if !isWord(r[2]) {
		return false
	}
	i := 3
	for i < len(r) && isWord(r[i]) {
		i++
	}
	if i == len(r) {
		return true
	}
	if len(r)-i == 2 && isAposTail(r[i]) && isAposTail(r[i+1]) {
		return true
	}
	if len(r)-i > 2 && isAposTail(r[len(r)-2]) && isAposTail(r[len(r)-1]) {
		k := i
		for k < len(r)-2 {
			if !isWord(r[k]) {
				return false
			}
			k++
		}
		return true
	}
	return false
}

func isAposTail(r rune) bool {
	return r == '\'' || r == 's' || r == 'S'
}

func applyApos(word string) string {
	r := []rune(word)
	first := string(r[0])
	if !strings.ContainsRune("aeiouAEIOU", r[0]) {
		first = strings.ToLower(first)
	} else {
		first = strings.ToUpper(first)
	}
	third := strings.ToUpper(string(r[2]))
	return first + string(r[1]) + third + string(r[3:])
}

func splitMac(word string) (string, string, bool) {
	for _, prefix := range []string{"Mc", "mc", "MC"} {
		if strings.HasPrefix(word, prefix) {
			rest := word[len(prefix):]
			rr := []rune(rest)
			if len(rr) >= 2 && isWord(rr[0]) {
				return prefix, rest, true
			}
		}
	}
	return "", "", false
}

func isMr(word string) bool {
	switch strings.ToLower(word) {
	case "mr", "mrs", "ms", "dr":
		return true
	default:
		return false
	}
}

func hasInlinePeriod(word string) bool {
	r := []rune(word)
	for i := 0; i+2 < len(r); i++ {
		if isWord(r[i]) && r[i+1] == '.' && isWord(r[i+2]) {
			return true
		}
	}
	return false
}

func hasUCElsewhere(word string) bool {
	r := []rune(word)
	i := 0
	for {
		if leadingUC(r[i:]) {
			return true
		}
		if i < len(r) && isPunct(r[i]) {
			i++
			continue
		}
		return false
	}
}

func leadingUC(r []rune) bool {
	k := 0
	for k < len(r) && isASCIILetter(r[k]) {
		k++
	}
	if k < 2 {
		return false
	}
	for j := 1; j < k; j++ {
		if isASCIIUpper(r[j]) {
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
		if !isASCIILetter(r) {
			return false
		}
		if strings.ContainsRune("aeiouyAEIOUY", r) {
			return false
		}
	}
	return true
}

func capFirst(word string) string {
	r := []rune(word)
	j := 0
	for j < len(r) && isPunct(r[j]) {
		j++
	}
	if j >= len(r) || !isWord(r[j]) {
		return word
	}
	return strings.ToUpper(string(r[:j+1])) + string(r[j+1:])
}
