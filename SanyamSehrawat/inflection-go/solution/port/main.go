// Command inflection is a Go port of the Python library inflection 0.5.1
// (https://github.com/jpvanhal/inflection, commit 88eefaa).
//
// Each input line is "<function>\t<argument>"; each output line is the result
// of that function, exactly as the original returns it. Arguments are
// printable ASCII, so the Unicode parts of the original never come into play.
package main

import (
	"bufio"
	"io"
	"os"
	"regexp"
	"strings"
)

type rule struct {
	re   *regexp.Regexp
	repl string // Go template: ${1} instead of Python's \1
}

func r(pattern, repl string) rule { return rule{regexp.MustCompile(pattern), repl} }

// The tables are copied in the original's order; irregular() then prepends to
// them exactly like the original's _irregular().
var plurals = []rule{
	r(`(?i)(quiz)$`, `${1}zes`),
	r(`(?i)^(oxen)$`, `${1}`),
	r(`(?i)^(ox)$`, `${1}en`),
	r(`(?i)(m|l)ice$`, `${1}ice`),
	r(`(?i)(m|l)ouse$`, `${1}ice`),
	r(`(?i)(passer)s?by$`, `${1}sby`),
	r(`(?i)(matr|vert|ind)(?:ix|ex)$`, `${1}ices`),
	r(`(?i)(x|ch|ss|sh)$`, `${1}es`),
	r(`(?i)([^aeiouy]|qu)y$`, `${1}ies`),
	r(`(?i)(hive)$`, `${1}s`),
	r(`(?i)([lr])f$`, `${1}ves`),
	r(`(?i)([^f])fe$`, `${1}ves`),
	r(`(?i)sis$`, `ses`),
	r(`(?i)([ti])a$`, `${1}a`),
	r(`(?i)([ti])um$`, `${1}a`),
	r(`(?i)(buffal|potat|tomat)o$`, `${1}oes`),
	r(`(?i)(bu)s$`, `${1}ses`),
	r(`(?i)(alias|status)$`, `${1}es`),
	r(`(?i)(octop|vir)i$`, `${1}i`),
	r(`(?i)(octop|vir)us$`, `${1}i`),
	r(`(?i)^(ax|test)is$`, `${1}es`),
	r(`(?i)s$`, `s`),
	r(`$`, `s`),
}

var singulars = []rule{
	r(`(?i)(database)s$`, `${1}`),
	r(`(?i)(quiz)zes$`, `${1}`),
	r(`(?i)(matr)ices$`, `${1}ix`),
	r(`(?i)(vert|ind)ices$`, `${1}ex`),
	r(`(?i)(passer)sby$`, `${1}by`),
	r(`(?i)^(ox)en`, `${1}`),
	r(`(?i)(alias|status)(es)?$`, `${1}`),
	r(`(?i)(octop|vir)(us|i)$`, `${1}us`),
	r(`(?i)^(a)x[ie]s$`, `${1}xis`),
	r(`(?i)(cris|test)(is|es)$`, `${1}is`),
	r(`(?i)(shoe)s$`, `${1}`),
	r(`(?i)(o)es$`, `${1}`),
	r(`(?i)(bus)(es)?$`, `${1}`),
	r(`(?i)(m|l)ice$`, `${1}ouse`),
	r(`(?i)(x|ch|ss|sh)es$`, `${1}`),
	r(`(?i)(m)ovies$`, `${1}ovie`),
	r(`(?i)(s)eries$`, `${1}eries`),
	r(`(?i)([^aeiouy]|qu)ies$`, `${1}y`),
	r(`(?i)([lr])ves$`, `${1}f`),
	r(`(?i)(tive)s$`, `${1}`),
	r(`(?i)(hive)s$`, `${1}`),
	r(`(?i)([^f])ves$`, `${1}fe`),
	r(`(?i)(t)he(sis|ses)$`, `${1}hesis`),
	r(`(?i)(s)ynop(sis|ses)$`, `${1}ynopsis`),
	r(`(?i)(p)rogno(sis|ses)$`, `${1}rognosis`),
	r(`(?i)(p)arenthe(sis|ses)$`, `${1}arenthesis`),
	r(`(?i)(d)iagno(sis|ses)$`, `${1}iagnosis`),
	r(`(?i)(b)a(sis|ses)$`, `${1}asis`),
	r(`(?i)(a)naly(sis|ses)$`, `${1}nalysis`),
	r(`(?i)([ti])a$`, `${1}um`),
	r(`(?i)(n)ews$`, `${1}ews`),
	r(`(?i)(ss)$`, `${1}`),
	r(`(?i)s$`, ``),
}

var uncountables = []string{"equipment", "fish", "information", "jeans", "money", "rice", "series", "sheep", "species"}

var uncountableRes = func() []*regexp.Regexp {
	out := make([]*regexp.Regexp, len(uncountables))
	for i, u := range uncountables {
		out[i] = regexp.MustCompile(`(?i)\b(` + u + `)\z`)
	}
	return out
}()

func prepend(list []rule, x rule) []rule { return append([]rule{x}, list...) }

func caseInsensitive(s string) string {
	var b strings.Builder
	for _, c := range s {
		b.WriteString("[" + string(c) + strings.ToUpper(string(c)) + "]")
	}
	return b.String()
}

// irregular mirrors the original's _irregular(): note the order of the inserts.
func irregular(singular, plural string) {
	up, low := strings.ToUpper, strings.ToLower
	if up(singular[:1]) == up(plural[:1]) {
		plurals = prepend(plurals, r(`(?i)(`+singular[:1]+`)`+singular[1:]+`$`, `${1}`+plural[1:]))
		plurals = prepend(plurals, r(`(?i)(`+plural[:1]+`)`+plural[1:]+`$`, `${1}`+plural[1:]))
		singulars = prepend(singulars, r(`(?i)(`+plural[:1]+`)`+plural[1:]+`$`, `${1}`+singular[1:]))
		return
	}
	lit := func(s string) string { return strings.ReplaceAll(s, "$", "$$") }
	plurals = prepend(plurals, r(up(singular[:1])+caseInsensitive(singular[1:])+`$`, lit(up(plural[:1])+plural[1:])))
	plurals = prepend(plurals, r(low(singular[:1])+caseInsensitive(singular[1:])+`$`, lit(low(plural[:1])+plural[1:])))
	plurals = prepend(plurals, r(up(plural[:1])+caseInsensitive(plural[1:])+`$`, lit(up(plural[:1])+plural[1:])))
	plurals = prepend(plurals, r(low(plural[:1])+caseInsensitive(plural[1:])+`$`, lit(low(plural[:1])+plural[1:])))
	singulars = prepend(singulars, r(up(plural[:1])+caseInsensitive(plural[1:])+`$`, lit(up(singular[:1])+singular[1:])))
	singulars = prepend(singulars, r(low(plural[:1])+caseInsensitive(plural[1:])+`$`, lit(low(singular[:1])+singular[1:])))
}

func init() {
	for _, p := range [][2]string{
		{"person", "people"}, {"man", "men"}, {"human", "humans"}, {"child", "children"},
		{"sex", "sexes"}, {"move", "moves"}, {"cow", "kine"}, {"zombie", "zombies"},
	} {
		irregular(p[0], p[1])
	}
}

func applyRules(rules []rule, word string) string {
	for _, x := range rules {
		if x.re.MatchString(word) {
			return x.re.ReplaceAllString(word, x.repl)
		}
	}
	return word
}

func pluralize(word string) string {
	if word == "" {
		return word
	}
	for _, u := range uncountables {
		if strings.ToLower(word) == u {
			return word
		}
	}
	return applyRules(plurals, word)
}

func singularize(word string) string {
	for _, re := range uncountableRes {
		if re.MatchString(word) {
			return word
		}
	}
	return applyRules(singulars, word)
}

var camelRe = regexp.MustCompile(`(?:^|_)(.)`)

func camelize(s string) string {
	return replaceFunc(camelRe, s, func(m []string) string { return strings.ToUpper(m[1]) })
}

// camelizeLower is camelize(s, False): s[0].lower() + camelize(s)[1:].
func camelizeLower(s string) string {
	c := camelize(s)
	if len(c) > 0 {
		c = c[1:]
	}
	return strings.ToLower(s[:1]) + c
}

func dasherize(s string) string { return strings.ReplaceAll(s, "_", "-") }

var (
	idSuffix   = regexp.MustCompile(`_id$`)
	firstWord  = regexp.MustCompile(`^\w`)
	underA     = regexp.MustCompile(`([A-Z]+)([A-Z][a-z])`)
	underB     = regexp.MustCompile(`([a-z\d])([A-Z])`)
	titleStart = regexp.MustCompile(`\b('?\w)`)
	paramBad   = regexp.MustCompile(`(?i)[^a-z0-9\-_]+`)
)

func humanize(word string) string {
	word = idSuffix.ReplaceAllString(word, "")
	word = strings.ReplaceAll(word, "_", " ")
	word = strings.ToLower(word) // the original lowercases every [a-z\d]* run
	return firstWord.ReplaceAllStringFunc(word, strings.ToUpper)
}

func underscore(word string) string {
	word = underA.ReplaceAllString(word, `${1}_${2}`)
	word = underB.ReplaceAllString(word, `${1}_${2}`)
	return strings.ToLower(strings.ReplaceAll(word, "-", "_"))
}

func isLetter(c byte) bool { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') }

// pyTitle mirrors str.title() for ASCII: a letter is upper-cased after a
// non-letter and lower-cased after a letter. Digits are not letters.
func pyTitle(s string) string {
	b := []byte(s)
	prevCased := false
	for i, c := range b {
		if isLetter(c) {
			if prevCased {
				b[i] = strings.ToLower(string(c))[0]
			} else {
				b[i] = strings.ToUpper(string(c))[0]
			}
			prevCased = true
		} else {
			prevCased = false
		}
	}
	return string(b)
}

func capitalize(s string) string {
	if s == "" {
		return s
	}
	return strings.ToUpper(s[:1]) + strings.ToLower(s[1:])
}

func titleize(word string) string {
	return replaceFunc(titleStart, pyTitle(humanize(underscore(word))), func(m []string) string { return capitalize(m[1]) })
}

func tableize(word string) string { return pluralize(underscore(word)) }

func parameterize(s, sep string) string {
	s = paramBad.ReplaceAllLiteralString(s, sep)
	q := regexp.QuoteMeta(sep)
	s = regexp.MustCompile(q+`{2,}`).ReplaceAllLiteralString(s, sep)
	s = regexp.MustCompile(`(?i)^`+q+`|`+q+`$`).ReplaceAllLiteralString(s, "")
	return strings.ToLower(s)
}

// ordinalize mirrors "{}{}".format(int(arg), ordinal(int(arg))) for an
// argument of an optional '-' and decimal digits, of any length.
func ordinalize(arg string) string {
	neg := strings.HasPrefix(arg, "-")
	digits := strings.TrimLeft(strings.TrimPrefix(arg, "-"), "0")
	if digits == "" {
		digits, neg = "0", false
	}
	n := len(digits)
	last := digits[n-1]
	tens := byte('0')
	if n >= 2 {
		tens = digits[n-2]
	}
	suffix := "th"
	if tens != '1' {
		switch last {
		case '1':
			suffix = "st"
		case '2':
			suffix = "nd"
		case '3':
			suffix = "rd"
		}
	}
	if neg {
		return "-" + digits + suffix
	}
	return digits + suffix
}

// replaceFunc is re.sub with a function: f gets the match and its groups.
func replaceFunc(re *regexp.Regexp, s string, f func([]string) string) string {
	var b strings.Builder
	last := 0
	for _, loc := range re.FindAllStringSubmatchIndex(s, -1) {
		groups := make([]string, len(loc)/2)
		for i := range groups {
			if loc[2*i] >= 0 {
				groups[i] = s[loc[2*i]:loc[2*i+1]]
			}
		}
		b.WriteString(s[last:loc[0]])
		b.WriteString(f(groups))
		last = loc[1]
	}
	b.WriteString(s[last:])
	return b.String()
}

var functions = map[string]func(string) string{
	"camelize":                camelize,
	"camelize_lower":          camelizeLower,
	"dasherize":               dasherize,
	"humanize":                humanize,
	"ordinalize":              ordinalize,
	"parameterize":            func(s string) string { return parameterize(s, "-") },
	"parameterize_underscore": func(s string) string { return parameterize(s, "_") },
	"pluralize":               pluralize,
	"singularize":             singularize,
	"tableize":                tableize,
	"titleize":                titleize,
	"underscore":              underscore,
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	for {
		line, err := in.ReadString('\n')
		if err != nil && err != io.EOF {
			os.Exit(1)
		}
		if line == "" && err == io.EOF {
			return
		}
		name, arg, _ := strings.Cut(strings.TrimSuffix(line, "\n"), "\t")
		if f, ok := functions[name]; ok {
			out.WriteString(f(arg))
		}
		out.WriteByte('\n')
		if err == io.EOF {
			return
		}
	}
}
