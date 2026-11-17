package main

// Small helpers that behave exactly like the Python string functions the original relies on.

import "strings"

// isSpace reports what Python's str.isspace(), str.strip() and the regex class \s treat as whitespace.
func isSpace(r rune) bool {
	switch {
	case r >= 0x09 && r <= 0x0d, r >= 0x1c && r <= 0x1f, r == 0x20, r == 0x85, r == 0xa0,
		r == 0x1680, r >= 0x2000 && r <= 0x200a, r == 0x2028, r == 0x2029, r == 0x202f,
		r == 0x205f, r == 0x3000:
		return true
	}
	return false
}

func allSpace(rs []rune) bool {
	for _, r := range rs {
		if !isSpace(r) {
			return false
		}
	}
	return true
}

// strip is Python's str.strip() with no argument.
func strip(s string) string {
	rs := []rune(s)
	i, j := 0, len(rs)
	for i < j && isSpace(rs[i]) {
		i++
	}
	for j > i && isSpace(rs[j-1]) {
		j--
	}
	return string(rs[i:j])
}

// rstrip is Python's str.rstrip() with no argument.
func rstrip(s string) string {
	rs := []rune(s)
	j := len(rs)
	for j > 0 && isSpace(rs[j-1]) {
		j--
	}
	return string(rs[:j])
}

// fields is Python's str.split() with no argument.
func fields(s string) []string {
	return strings.FieldsFunc(s, isSpace)
}

// splitLines is Python's str.splitlines(): it breaks at \n, \r, \r\n, \v, \f, \x1c, \x1d, \x1e,
// \x85, U+2028 and U+2029, and gives no empty last piece.
func splitLines(s string) []string {
	var lines []string
	rs := []rune(s)
	start := 0
	for i := 0; i < len(rs); i++ {
		switch rs[i] {
		case '\n', '\v', '\f', 0x1c, 0x1d, 0x1e, 0x85, 0x2028, 0x2029:
			lines = append(lines, string(rs[start:i]))
			start = i + 1
		case '\r':
			lines = append(lines, string(rs[start:i]))
			if i+1 < len(rs) && rs[i+1] == '\n' {
				i++
			}
			start = i + 1
		}
	}
	if start < len(rs) {
		lines = append(lines, string(rs[start:]))
	}
	return lines
}

// decodeUTF8Replace is Python's bytes.decode('UTF-8', 'replace'): every faulty byte sequence
// becomes one U+FFFD, where a sequence ends at the first byte that cannot continue it.
func decodeUTF8Replace(b []byte) string {
	var sb strings.Builder
	i := 0
	for i < len(b) {
		c := b[i]
		if c < 0x80 {
			sb.WriteByte(c)
			i++
			continue
		}
		need := 0
		lo, hi := byte(0x80), byte(0xbf) // allowed range of the second byte
		switch {
		case c >= 0xc2 && c <= 0xdf:
			need = 1
		case c == 0xe0:
			need, lo = 2, 0xa0
		case c == 0xed:
			need, hi = 2, 0x9f
		case c >= 0xe1 && c <= 0xef:
			need = 2
		case c == 0xf0:
			need, lo = 3, 0x90
		case c == 0xf4:
			need, hi = 3, 0x8f
		case c >= 0xf1 && c <= 0xf3:
			need = 3
		default: // not a valid first byte
			sb.WriteRune(0xfffd)
			i++
			continue
		}
		j, ok := i+1, true
		for k := 0; k < need; k++ {
			l, h := byte(0x80), byte(0xbf)
			if k == 0 {
				l, h = lo, hi
			}
			if j >= len(b) || b[j] < l || b[j] > h {
				ok = false
				break
			}
			j++
		}
		if ok {
			sb.Write(b[i:j])
		} else {
			sb.WriteRune(0xfffd)
		}
		i = j
	}
	return sb.String()
}

// translate is Python's str.translate() with a 256-character table: only characters below 256
// can change, and only the ones listed in the table differ from themselves.
func translate(s string, table map[rune]rune) string {
	rs := []rune(s)
	for i, r := range rs {
		if t, ok := table[r]; ok {
			rs[i] = t
		}
	}
	return string(rs)
}

func reverseRunes(s string) string {
	rs := []rune(s)
	for i, j := 0, len(rs)-1; i < j; i, j = i+1, j-1 {
		rs[i], rs[j] = rs[j], rs[i]
	}
	return string(rs)
}
