package format

import (
	"strings"

	"komal/titlecase/internal/pattern"
	u "komal/titlecase/internal/pyunicode"
)

func matches(name, s string) bool { _, ok := patterns[name].Match(s); return ok }

func word(s string, allCaps bool) string {
	if allCaps && matches("initials", s) {
		return s
	}
	if matches("apostrophe", s) {
		rs := []rune(s)
		first := u.Lower(string(rs[0]))
		if strings.ContainsRune("aeiouAEIOU", rs[0]) {
			first = u.Upper(string(rs[0]))
		}
		return first + string(rs[1]) + u.Upper(string(rs[2])) + string(rs[3:])
	}
	if m, ok := patterns["mc"].Match(s); ok {
		return u.Capitalize(m.Group(1)) + titlecase(m.Group(2), true)
	}
	if matches("honorific", s) {
		rs := []rune(s)
		return u.Upper(string(rs[0])) + string(rs[1:])
	}
	if _, ok := patterns["inline"].Search(s); ok {
		return s
	}
	if !allCaps && matches("internal", s) {
		return s
	}
	if matches("small", s) {
		return u.Lower(s)
	}
	if strings.Contains(s, "/") && !strings.Contains(s, "//") {
		parts := strings.Split(s, "/")
		for i := range parts {
			parts[i] = titlecase(parts[i], false)
		}
		return strings.Join(parts, "/")
	}
	if strings.Contains(s, "-") {
		parts := strings.Split(s, "-")
		for i := range parts {
			parts[i] = titlecase(parts[i], false)
		}
		return strings.Join(parts, "-")
	}
	if allCaps {
		s = u.Lower(s)
	}
	if len([]rune(s)) > 2 && matches("consonants", s) {
		return u.Upper(s)
	}
	return patterns["cap"].Replace(s, func(m pattern.Match) string { return u.Upper(m.Group(0)) })
}

func titlecase(s string, firstLast bool) string {
	lines := patterns["lines"].Split(s, false)
	for i, line := range lines {
		allCaps := u.Upper(line) == line
		parts := patterns["spaces"].Split(line, true)
		for j := 0; j < len(parts); j += 2 {
			parts[j] = word(parts[j], allCaps)
		}
		if firstLast {
			parts[0] = patterns["first"].Replace(parts[0], func(m pattern.Match) string { return m.Group(1) + u.Capitalize(m.Group(2)) })
			last := len(parts) - 1
			parts[last] = patterns["last"].Replace(parts[last], func(m pattern.Match) string { return u.Capitalize(m.Group(0)) })
		}
		lines[i] = patterns["subphrase"].Replace(strings.Join(parts, ""), func(m pattern.Match) string { return m.Group(1) + u.Capitalize(m.Group(2)) })
	}
	return strings.Join(lines, "\n")
}

func Titlecase(s string) string { return titlecase(s, true) }
