#!/bin/bash
# Oracle: writes a Go port of pyfiglet (standard library only) into
# /workspace/repo, moves the .flf fonts into fonts/ (embedded with go:embed),
# deletes every .py file, and checks that both build commands pass.
set -euo pipefail
cd /workspace/repo

mkdir -p fonts
cp pyfiglet/fonts/*.flf fonts/
find . -name '*.py' -delete

cat > go.mod <<'EOF'
module figlet

go 1.23
EOF

cat > main.go <<'EOF'
// Command figlet is a byte-for-byte Go port of pyfiglet's command-line
// renderer (pyfiglet commit 255827efbc09d662875dad50fa0edc1e1263bf45).
//
// Every rule below mirrors pyfiglet/__init__.py, including its quirks:
// the "/" + "\" big-X smush gives "|", the font header is split on any
// whitespace, glyph rows are trimmed with Python's regular expressions,
// and justification pads with the -w width.
package main

import (
	"archive/zip"
	"bytes"
	"embed"
	"errors"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
	"unicode"
	"unicode/utf8"
)

//go:embed fonts
var fontFS embed.FS

// ---------------------------------------------------------------------------
// Python string helpers
// ---------------------------------------------------------------------------

// isPySpace matches Python's str.isspace() and the re module's \s.
func isPySpace(r rune) bool {
	if r >= 0x1c && r <= 0x1f {
		return true
	}
	return unicode.IsSpace(r)
}

// pyDecode decodes bytes like bytes.decode("utf-8", "replace"): every
// maximal invalid subpart becomes one U+FFFD.
func pyDecode(b []byte) []rune {
	out := make([]rune, 0, len(b))
	i := 0
	for i < len(b) {
		c := b[i]
		if c < 0x80 {
			out = append(out, rune(c))
			i++
			continue
		}
		n := 0
		lo, hi := byte(0x80), byte(0xBF)
		switch {
		case c >= 0xC2 && c <= 0xDF:
			n = 1
		case c == 0xE0:
			n, lo = 2, 0xA0
		case c == 0xED:
			n, hi = 2, 0x9F
		case c >= 0xE1 && c <= 0xEF:
			n = 2
		case c == 0xF0:
			n, lo = 3, 0x90
		case c >= 0xF1 && c <= 0xF3:
			n = 3
		case c == 0xF4:
			n, hi = 3, 0x8F
		default:
			out = append(out, utf8.RuneError)
			i++
			continue
		}
		j := 1
		ok := true
		for ; j <= n; j++ {
			if i+j >= len(b) {
				ok = false
				break
			}
			l, h := byte(0x80), byte(0xBF)
			if j == 1 {
				l, h = lo, hi
			}
			if b[i+j] < l || b[i+j] > h {
				ok = false
				break
			}
		}
		if ok {
			r, _ := utf8.DecodeRune(b[i : i+n+1])
			out = append(out, r)
			i += n + 1
		} else {
			out = append(out, utf8.RuneError)
			i += j
		}
	}
	return out
}

// pySplitlines matches str.splitlines() (no keepends).
func pySplitlines(s []rune) [][]rune {
	var out [][]rune
	start, i := 0, 0
	for i < len(s) {
		eol := 0
		switch s[i] {
		case '\n', '\v', '\f', 0x1c, 0x1d, 0x1e, 0x85, 0x2028, 0x2029:
			eol = 1
		case '\r':
			eol = 1
			if i+1 < len(s) && s[i+1] == '\n' {
				eol = 2
			}
		}
		if eol > 0 {
			out = append(out, s[start:i])
			i += eol
			start = i
		} else {
			i++
		}
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}

// pyStrip matches str.strip() with no arguments.
func pyStrip(s []rune) []rune {
	a, b := 0, len(s)
	for a < b && isPySpace(s[a]) {
		a++
	}
	for b > a && isPySpace(s[b-1]) {
		b--
	}
	return s[a:b]
}

// pyRstrip matches str.rstrip() with no arguments.
func pyRstrip(s []rune) []rune {
	b := len(s)
	for b > 0 && isPySpace(s[b-1]) {
		b--
	}
	return s[:b]
}

// pyFields matches str.split() with no arguments.
func pyFields(s []rune) []string {
	var out []string
	i := 0
	for i < len(s) {
		for i < len(s) && isPySpace(s[i]) {
			i++
		}
		if i >= len(s) {
			break
		}
		j := i
		for j < len(s) && !isPySpace(s[j]) {
			j++
		}
		out = append(out, string(s[i:j]))
		i = j
	}
	return out
}

// pyDigits parses digits in the given base with Python's underscore rules.
func pyDigits(s string, base int) (int64, bool) {
	if s == "" || s[0] == '_' || s[len(s)-1] == '_' || strings.Contains(s, "__") {
		return 0, false
	}
	v, err := strconv.ParseInt(strings.ReplaceAll(s, "_", ""), base, 64)
	if errors.Is(err, strconv.ErrRange) {
		// Python ints are unbounded; such a code can never match a rune.
		return -1, true
	}
	if err != nil {
		return 0, false
	}
	return v, true
}

// pyInt matches int(s) for a base-10 string.
func pyInt(s string) (int64, bool) {
	t := strings.TrimFunc(s, isPySpace)
	neg := false
	if strings.HasPrefix(t, "+") || strings.HasPrefix(t, "-") {
		neg = t[0] == '-'
		t = t[1:]
	}
	v, ok := pyDigits(t, 10)
	if neg {
		v = -v
	}
	return v, ok
}

// pyHexInt matches int(s, 16) for a string that starts with "0x".
func pyHexInt(s string) (int64, bool) {
	t := strings.TrimFunc(s, isPySpace)
	if len(t) < 2 || t[0] != '0' || (t[1] != 'x' && t[1] != 'X') {
		return 0, false
	}
	t = t[2:]
	if strings.HasPrefix(t, "_") {
		t = t[1:]
	}
	return pyDigits(t, 16)
}

// ---------------------------------------------------------------------------
// Font
// ---------------------------------------------------------------------------

type font struct {
	height    int
	hardBlank string
	hasDir    bool
	printDir  int64
	smushMode int64
	chars     map[int64][][]rune
	width     map[int64]int
}

type fontError struct{ msg string }

func (e fontError) Error() string { return e.msg }

func readFontData(name string) ([]byte, bool) {
	for _, ext := range []string{"tlf", "flf"} {
		data, err := fontFS.ReadFile("fonts/" + name + "." + ext)
		if err != nil {
			continue
		}
		if zr, zerr := zip.NewReader(bytes.NewReader(data), int64(len(data))); zerr == nil && len(zr.File) > 0 {
			f, err := zr.File[0].Open()
			if err != nil {
				return nil, false
			}
			defer f.Close()
			data, err = io.ReadAll(f)
			if err != nil {
				return nil, false
			}
		}
		if len(data) == 0 {
			return nil, false
		}
		return data, true
	}
	return nil, false
}

// endMarker returns the character found by the regex (.)\s*$ .
func endMarker(line []rune) (rune, bool) {
	if len(line) == 0 {
		return 0, false
	}
	for k := len(line) - 1; k >= 0; k-- {
		if !isPySpace(line[k]) {
			return line[k], true
		}
	}
	return line[0], true
}

func allSpace(s []rune) bool {
	for _, r := range s {
		if !isPySpace(r) {
			return false
		}
	}
	return true
}

// stripEnd removes the regex escape(end){1,2}\s*$ from line, like
// pyfiglet's re.sub with an empty replacement.
func stripEnd(line []rune, end rune) []rune {
	for p := 0; p < len(line); p++ {
		if line[p] != end {
			continue
		}
		if p+1 < len(line) && line[p+1] == end && allSpace(line[p+2:]) {
			return line[:p]
		}
		if allSpace(line[p+1:]) {
			return line[:p]
		}
	}
	return line
}

func loadFont(name string, data []byte) (*font, error) {
	text := pyDecode(data)
	for i, r := range text {
		if r == 0x85 || r == 0x2028 || r == 0x2029 {
			text[i] = ' '
		}
	}
	lines := pySplitlines(text)
	fail := func(msg string) (*font, error) {
		return nil, fontError{"problem parsing " + name + " font: " + msg}
	}
	pop := func() ([]rune, bool) {
		if len(lines) == 0 {
			return nil, false
		}
		l := lines[0]
		lines = lines[1:]
		return l, true
	}

	header, ok := pop()
	if !ok {
		return fail("pop from empty list")
	}
	if len(header) < 5 || (header[0] != 't' && header[0] != 'f') || header[1] != 'l' || header[2] != 'f' || header[3] != '2' {
		return fail(name + " is not a valid figlet font")
	}
	fields := pyFields(header[5:])
	if len(fields) < 6 {
		return fail("malformed header for " + name)
	}
	f := &font{chars: map[int64][][]rune{}, width: map[int64]int{}}
	f.hardBlank = fields[0]
	var nums [5]int64
	for k := 0; k < 5; k++ {
		v, ok := pyInt(fields[1+k])
		if !ok {
			return fail("invalid literal for int()")
		}
		nums[k] = v
	}
	height, oldLayout, commentLines := nums[0], nums[3], nums[4]
	hasFull := false
	var fullLayout int64
	if len(fields) > 6 {
		v, ok := pyInt(fields[6])
		if !ok {
			return fail("invalid literal for int()")
		}
		f.hasDir, f.printDir = true, v
	}
	if len(fields) > 7 {
		v, ok := pyInt(fields[7])
		if !ok {
			return fail("invalid literal for int()")
		}
		hasFull, fullLayout = true, v
	}
	if !hasFull {
		switch {
		case oldLayout == 0:
			fullLayout = 64
		case oldLayout < 0:
			fullLayout = 0
		default:
			fullLayout = (oldLayout & 31) | 128
		}
	}
	f.height = int(height)
	f.smushMode = fullLayout
	for i := int64(0); i < commentLines; i++ {
		if _, ok := pop(); !ok {
			return fail("pop from empty list")
		}
	}

	readChar := func() (int, [][]rune, error) {
		var end rune
		haveEnd := false
		width := 0
		var rows [][]rune
		for k := 0; k < f.height; k++ {
			line, ok := pop()
			if !ok {
				return 0, nil, fontError{"problem parsing " + name + " font: pop from empty list"}
			}
			if !haveEnd {
				e, ok := endMarker(line)
				if !ok {
					return 0, nil, fontError{"problem parsing " + name + " font: no end marker"}
				}
				end, haveEnd = e, true
			}
			line = stripEnd(line, end)
			if len(line) > width {
				width = len(line)
			}
			rows = append(rows, line)
		}
		return width, rows, nil
	}
	nonEmpty := func(rows [][]rune) bool {
		for _, r := range rows {
			if len(r) > 0 {
				return true
			}
		}
		return false
	}

	for i := int64(32); i < 127; i++ {
		w, rows, err := readChar()
		if err != nil {
			return nil, err
		}
		if i == 32 || nonEmpty(rows) {
			f.chars[i], f.width[i] = rows, w
		}
	}
	if len(lines) > 0 {
		for _, c := range "ÄÖÜäöüß" {
			w, rows, err := readChar()
			if err != nil {
				return nil, err
			}
			if nonEmpty(rows) {
				f.chars[int64(c)], f.width[int64(c)] = rows, w
			}
		}
	}
	for len(lines) > 0 {
		line, _ := pop()
		line = pyStrip(line)
		tag := string(line)
		if k := strings.IndexByte(tag, ' '); k >= 0 {
			tag = tag[:k]
		}
		if tag == "" {
			continue
		}
		if len(tag) >= 2 && tag[0] == '0' && (tag[1] == 'x' || tag[1] == 'X') {
			code, ok := pyHexInt(tag)
			if !ok {
				return fail("invalid literal for int() with base 16")
			}
			w, rows, err := readChar()
			if err != nil {
				return nil, err
			}
			if nonEmpty(rows) {
				f.chars[code], f.width[code] = rows, w
			}
		}
	}
	return f, nil
}

// ---------------------------------------------------------------------------
// Rendering (FigletBuilder)
// ---------------------------------------------------------------------------

const (
	smEqual     = 1
	smLowline   = 2
	smHierarchy = 4
	smPair      = 8
	smBigX      = 16
	smHardblank = 32
	smKern      = 64
	smSmush     = 128
)

type marker struct {
	buffer   [][]rune
	iterator int
}

type builder struct {
	text      []rune
	rtl       bool
	width     int
	font      *font
	justify   string
	iterator  int
	maxSmush  int
	curWidth  int
	prevWidth int
	total     int
	blanks    []marker
	queue     [][][]rune
	buffer    [][]rune
}

type renderError struct{ msg string }

func (e renderError) Error() string { return e.msg }

func newBuffer(h int) [][]rune {
	b := make([][]rune, h)
	for i := range b {
		b[i] = []rune{}
	}
	return b
}

func copyBuffer(b [][]rune) [][]rune {
	c := make([][]rune, len(b))
	copy(c, b)
	return c
}

func (b *builder) charAt(i int) ([][]rune, bool) {
	if i < 0 || i >= len(b.text) {
		return nil, false
	}
	g, ok := b.font.chars[int64(b.text[i])]
	return g, ok
}

func (b *builder) addCharToProduct() error {
	cur, ok := b.charAt(b.iterator)
	if b.text[b.iterator] == '\n' {
		b.blanks = append(b.blanks, marker{copyBuffer(b.buffer), b.iterator})
		b.handleNewLine()
		return nil
	}
	if !ok {
		return nil
	}
	w := b.font.width[int64(b.text[b.iterator])]
	if b.width < w {
		return renderError{"Width is not enough to print this character"}
	}
	b.curWidth = w
	b.maxSmush = b.smushAmount(b.buffer, cur)
	b.total = len(b.buffer[0]) + b.curWidth - b.maxSmush
	if b.text[b.iterator] == ' ' {
		b.blanks = append(b.blanks, marker{copyBuffer(b.buffer), b.iterator})
	}
	if b.total >= b.width {
		b.handleNewLine()
	} else {
		for row := 0; row < b.font.height; row++ {
			if err := b.addRow(cur, row); err != nil {
				return err
			}
		}
	}
	b.prevWidth = b.curWidth
	return nil
}

func (b *builder) addRow(cur [][]rune, row int) error {
	addLeft, addRight := b.buffer[row], cur[row]
	if b.rtl {
		addLeft, addRight = addRight, addLeft
	}
	for i := 0; i < b.maxSmush; i++ {
		idx := len(addLeft) - b.maxSmush + i
		left := ""
		if idx >= 0 && idx < len(addLeft) {
			left = string(addLeft[idx])
		}
		if i >= len(addRight) {
			return renderError{"string index out of range"}
		}
		right := string(addRight[i])
		smushed, ok := b.smushChars(left, right)
		if idx < 0 || idx > len(addLeft) {
			continue
		}
		if !ok {
			return renderError{"sequence item: expected str instance, NoneType found"}
		}
		next := make([]rune, 0, len(addLeft))
		next = append(next, addLeft[:idx]...)
		next = append(next, []rune(smushed)...)
		next = append(next, addLeft[idx+1:]...)
		addLeft = next
	}
	out := make([]rune, 0, len(addLeft)+len(addRight))
	out = append(out, addLeft...)
	if b.maxSmush < len(addRight) {
		out = append(out, addRight[b.maxSmush:]...)
	}
	b.buffer[row] = out
	return nil
}

func (b *builder) cutBufferCommon() {
	b.total = 0
	b.buffer = newBuffer(b.font.height)
	b.blanks = nil
	b.prevWidth = 0
	cur, ok := b.charAt(b.iterator)
	if !ok {
		return
	}
	b.maxSmush = b.smushAmount(b.buffer, cur)
}

func (b *builder) handleNewLine() {
	if n := len(b.blanks); n > 0 {
		m := b.blanks[n-1]
		b.blanks = b.blanks[:n-1]
		b.queue = append(b.queue, m.buffer)
		b.iterator = m.iterator
	} else {
		b.queue = append(b.queue, b.buffer)
		b.iterator--
	}
	b.cutBufferCommon()
}

func rstripASCIISpace(s []rune) []rune {
	n := len(s)
	for n > 0 && s[n-1] == ' ' {
		n--
	}
	return s[:n]
}

func leadingASCIISpaces(s []rune) int {
	n := 0
	for n < len(s) && s[n] == ' ' {
		n++
	}
	return n
}

func (b *builder) smushAmount(buffer, cur [][]rune) int {
	if b.font.smushMode&(smSmush|smKern) == 0 {
		return 0
	}
	maxSmush := b.curWidth
	for row := 0; row < b.font.height; row++ {
		lineLeft, lineRight := buffer[row], cur[row]
		if b.rtl {
			lineLeft, lineRight = lineRight, lineLeft
		}
		linebd := len(rstripASCIISpace(lineLeft)) - 1
		if linebd < 0 {
			linebd = 0
		}
		ch1 := ""
		if linebd < len(lineLeft) {
			ch1 = string(lineLeft[linebd])
		} else {
			linebd = 0
		}
		charbd := leadingASCIISpaces(lineRight)
		ch2 := ""
		if charbd < len(lineRight) {
			ch2 = string(lineRight[charbd])
		} else {
			charbd = len(lineRight)
		}
		amt := charbd + len(lineLeft) - 1 - linebd
		if ch1 == "" || ch1 == " " {
			amt++
		} else if ch2 != "" {
			if _, ok := b.smushChars(ch1, ch2); ok {
				amt++
			}
		}
		if amt < maxSmush {
			maxSmush = amt
		}
	}
	return maxSmush
}

type smushPair struct{ a, b string }

// smushChars returns the merged character, or ok=false where pyfiglet
// returns None.
func (b *builder) smushChars(left, right string) (string, bool) {
	if left == " " {
		return right, true
	}
	if right == " " {
		return left, true
	}
	if b.prevWidth < 2 || b.curWidth < 2 {
		return "", false
	}
	mode := b.font.smushMode
	if mode&smSmush == 0 {
		return "", false
	}
	hb := b.font.hardBlank
	if mode&63 == 0 {
		if left == hb {
			return right, true
		}
		if right == hb {
			return left, true
		}
		if b.rtl {
			return left, true
		}
		return right, true
	}
	if mode&smHardblank != 0 && left == hb && right == hb {
		return left, true
	}
	if left == hb || right == hb {
		return "", false
	}
	if mode&smEqual != 0 && left == right {
		return left, true
	}
	var smushes []smushPair
	if mode&smLowline != 0 {
		smushes = append(smushes, smushPair{"_", `|/\[]{}()<>`})
	}
	if mode&smHierarchy != 0 {
		smushes = append(smushes,
			smushPair{"|", `/\[]{}()<>`},
			smushPair{`\/`, "[]{}()<>"},
			smushPair{"[]", "{}()<>"},
			smushPair{"{}", "()<>"},
			smushPair{"()", "<>"},
		)
	}
	for _, p := range smushes {
		if strings.Contains(p.a, left) && strings.Contains(p.b, right) {
			return right, true
		}
		if strings.Contains(p.a, right) && strings.Contains(p.b, left) {
			return left, true
		}
	}
	if mode&smPair != 0 {
		for _, pr := range []string{left + right, right + left} {
			if pr == "[]" || pr == "{}" || pr == "()" {
				return "|", true
			}
		}
	}
	if mode&smBigX != 0 {
		if left == "/" && right == `\` {
			return "|", true
		}
		if right == "/" && left == `\` {
			return "Y", true
		}
		if left == ">" && right == "<" {
			return "X", true
		}
	}
	return "", false
}

func (b *builder) justifyRows(buf [][]rune) {
	for row := 0; row < b.font.height; row++ {
		pad := 0
		switch b.justify {
		case "right":
			pad = b.width - len(buf[row]) - 1
		case "center":
			pad = (b.width - len(buf[row])) / 2
		default:
			return
		}
		if pad > 0 {
			buf[row] = append([]rune(strings.Repeat(" ", pad)), buf[row]...)
		}
	}
}

func (b *builder) render() (string, error) {
	for b.iterator < len(b.text) {
		if err := b.addCharToProduct(); err != nil {
			return "", err
		}
		b.iterator++
	}
	if len(b.buffer[0]) != 0 {
		b.queue = append(b.queue, b.buffer)
	}
	var sb strings.Builder
	for _, buf := range b.queue {
		b.justifyRows(buf)
		var part strings.Builder
		for k, row := range buf {
			if k > 0 {
				part.WriteByte('\n')
			}
			part.WriteString(string(row))
		}
		part.WriteByte('\n')
		sb.WriteString(strings.ReplaceAll(part.String(), b.font.hardBlank, " "))
	}
	return sb.String(), nil
}

// ---------------------------------------------------------------------------
// FigletString transforms
// ---------------------------------------------------------------------------

var reverseSwap = map[rune]rune{
	'(': ')', ')': '(', '/': '\\', '\\': '/', '<': '>', '>': '<',
	'[': ']', ']': '[', '{': '}', '}': '{',
}

var flipSwap = map[rune]rune{
	'/': '\\', '\\': '/', 'A': 'V', 'V': 'A', 'M': 'W', 'W': 'M',
	'P': 'b', 'R': 'b', 'b': 'P', 'm': 'w', 'w': 'm', 'v': '^', '^': 'v',
	'_': '-',
}

func translate(row []rune, table map[rune]rune) []rune {
	out := make([]rune, len(row))
	for i, r := range row {
		if t, ok := table[r]; ok {
			out[i] = t
		} else {
			out[i] = r
		}
	}
	return out
}

func fromList(rows [][]rune) string {
	parts := make([]string, len(rows))
	for i, r := range rows {
		parts[i] = string(r)
	}
	return strings.Join(parts, "\n") + "\n"
}

func reverseText(s string) string {
	var out [][]rune
	for _, row := range pySplitlines([]rune(s)) {
		t := translate(row, reverseSwap)
		for i, j := 0, len(t)-1; i < j; i, j = i+1, j-1 {
			t[i], t[j] = t[j], t[i]
		}
		out = append(out, t)
	}
	return fromList(out)
}

func flipText(s string) string {
	rows := pySplitlines([]rune(s))
	var out [][]rune
	for i := len(rows) - 1; i >= 0; i-- {
		out = append(out, translate(rows[i], flipSwap))
	}
	return fromList(out)
}

func stripSurrounding(s string) string {
	var out [][]rune
	seen := false
	for _, row := range pySplitlines([]rune(s)) {
		if len(pyStrip(row)) != 0 || seen {
			seen = true
			out = append(out, row)
		}
	}
	return string(pyRstrip([]rune(fromList(out))))
}

// ---------------------------------------------------------------------------
// Command line (optparse rules)
// ---------------------------------------------------------------------------

type options struct {
	font, direction, justify string
	width                    int
	reverse, flip            bool
	strip, normalize         bool
	text                     []string
}

var longNames = []string{
	"--font", "--direction", "--justify", "--width", "--reverse",
	"--normalize-surrounding-newlines", "--strip-surrounding-newlines",
	"--flip", "--list_fonts", "--info_font", "--load", "--color",
	"--help", "--version",
}

var longToShort = map[string]byte{
	"--font": 'f', "--direction": 'D', "--justify": 'j', "--width": 'w',
	"--reverse": 'r', "--normalize-surrounding-newlines": 'n',
	"--strip-surrounding-newlines": 's', "--flip": 'F', "--list_fonts": 'l',
	"--info_font": 'i', "--load": 'L', "--color": 'c', "--help": 'h',
	"--version": 'V',
}

func takesValue(c byte) bool { return strings.IndexByte("fDjwLc", c) >= 0 }

func usageError(msg string) {
	fmt.Fprintf(os.Stderr, "Usage: figlet [options] [text..]\n\nfiglet: error: %s\n", msg)
	os.Exit(2)
}

// parseNum follows optparse's int parsing (0x, 0b and 0 prefixes).
func parseNum(val string) (int, bool) {
	lower := strings.ToLower(val)
	base := 10
	switch {
	case strings.HasPrefix(lower, "0x"):
		base = 16
		val = val[2:]
	case strings.HasPrefix(lower, "0b"):
		base = 2
		val = val[2:]
		if val == "" {
			val = "0"
		}
	case strings.HasPrefix(val, "0"):
		base = 8
	}
	t := strings.TrimFunc(val, isPySpace)
	neg := false
	if strings.HasPrefix(t, "+") || strings.HasPrefix(t, "-") {
		neg = t[0] == '-'
		t = t[1:]
	}
	if base == 16 && strings.HasPrefix(t, "_") {
		t = t[1:]
	}
	v, ok := pyDigits(t, base)
	if neg {
		v = -v
	}
	return int(v), ok
}

func (o *options) set(c byte, val string) {
	switch c {
	case 'f':
		o.font = val
	case 'D':
		if val != "auto" && val != "left-to-right" && val != "right-to-left" {
			usageError(fmt.Sprintf("option -D: invalid choice: '%s'", val))
		}
		o.direction = val
	case 'j':
		if val != "auto" && val != "left" && val != "center" && val != "right" {
			usageError(fmt.Sprintf("option -j: invalid choice: '%s'", val))
		}
		o.justify = val
	case 'w':
		n, ok := parseNum(val)
		if !ok {
			usageError(fmt.Sprintf("option -w: invalid integer value: '%s'", val))
		}
		o.width = n
	case 'r':
		o.reverse = true
	case 'F':
		o.flip = true
	case 's':
		o.strip = true
	case 'n':
		o.normalize = true
	case 'h':
		fmt.Println("Usage: figlet [options] [text..]")
		os.Exit(0)
	case 'V':
		fmt.Println("1.0.4")
		os.Exit(0)
	}
}

func parseArgs(args []string) options {
	o := options{font: "standard", direction: "auto", justify: "auto", width: 80}
	for i := 0; i < len(args); i++ {
		a := args[i]
		switch {
		case a == "--":
			o.text = append(o.text, args[i+1:]...)
			return o
		case strings.HasPrefix(a, "--"):
			name, val, hasVal := strings.Cut(a, "=")
			full := ""
			for _, n := range longNames {
				if n == name {
					full = n
					break
				}
			}
			if full == "" {
				var hits []string
				for _, n := range longNames {
					if strings.HasPrefix(n, name) {
						hits = append(hits, n)
					}
				}
				if len(hits) != 1 {
					usageError("no such option: " + name)
				}
				full = hits[0]
			}
			c := longToShort[full]
			if takesValue(c) {
				if !hasVal {
					if i+1 >= len(args) {
						usageError(full + " option requires 1 argument")
					}
					i++
					val = args[i]
				}
				o.set(c, val)
			} else {
				if hasVal {
					usageError(full + " option does not take a value")
				}
				o.set(c, "")
			}
		case strings.HasPrefix(a, "-") && len(a) > 1:
			for k := 1; k < len(a); k++ {
				c := a[k]
				if strings.IndexByte("fDjwLcrFsnlih", c) < 0 {
					usageError(fmt.Sprintf("no such option: -%c", c))
				}
				if takesValue(c) {
					val := a[k+1:]
					if val == "" {
						if i+1 >= len(args) {
							usageError(fmt.Sprintf("-%c option requires 1 argument", c))
						}
						i++
						val = args[i]
					}
					o.set(c, val)
					break
				}
				o.set(c, "")
			}
		default:
			o.text = append(o.text, a)
		}
	}
	return o
}

func main() {
	o := parseArgs(os.Args[1:])
	if len(o.text) == 0 {
		fmt.Println("Usage: figlet [options] [text..]")
		os.Exit(1)
	}
	data, ok := readFontData(o.font)
	if !ok {
		fmt.Printf("pyfiglet error: requested font '%s' not found.\n", o.font)
		os.Exit(1)
	}
	f, err := loadFont(o.font, data)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	direction := o.direction
	if direction == "auto" {
		direction = "left-to-right"
		if f.hasDir && f.printDir == 1 {
			direction = "right-to-left"
		}
	}
	justify := o.justify
	if justify == "auto" {
		justify = "left"
		if direction == "right-to-left" {
			justify = "right"
		}
	}

	b := &builder{
		text:    []rune(strings.Join(o.text, " ")),
		rtl:     direction == "right-to-left",
		width:   o.width,
		font:    f,
		justify: justify,
		buffer:  newBuffer(f.height),
	}
	r, err := b.render()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if o.reverse {
		r = reverseText(r)
	}
	if o.flip {
		r = flipText(r)
	}
	if o.strip {
		r = stripSurrounding(r)
	} else if o.normalize {
		r = "\n" + stripSurrounding(r) + "\n"
	}
	os.Stdout.WriteString(r + "\n")
}
EOF

gofmt -l . | (! grep .)
go vet .
go build ./...
go build -o /tmp/figlet .
/tmp/figlet -f slant "done"
