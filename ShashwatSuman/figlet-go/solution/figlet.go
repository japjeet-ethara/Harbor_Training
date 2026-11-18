// Command figlet is a Go port of pyfiglet (commit 255827e, pyfiglet/__init__.py).
// It prints the same bytes as `python -m pyfiglet` for the options
// -f -w -j -D -r -F -s -n. Fonts are embedded from ./fonts, so the binary
// works from any working directory.
//
// Where pyfiglet raises an exception (for example CharNotPrinted), this
// program prints nothing to stdout and exits with status 1, as Python does.
package main

import (
	"archive/zip"
	"bytes"
	"embed"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"unicode"
	"unicode/utf8"
)

//go:embed fonts
var fontFS embed.FS

const noChar rune = -1     // Python's empty string '' used as a "character"
const neverChar rune = -3  // a multi-character hardblank never equals one char

var errPython = errors.New("python exception")

// ------------------------------------------------------------------ Python string helpers

// pyIsSpace mirrors str.isspace() (also used by \s, strip() and split()).
func pyIsSpace(r rune) bool {
	return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)
}

// pySplitLines mirrors str.splitlines() without keepends.
func pySplitLines(s []rune) [][]rune {
	var out [][]rune
	start := 0
	for i := 0; i < len(s); i++ {
		switch s[i] {
		case '\n', '\x0b', '\x0c', '\x1c', '\x1d', '\x1e', 0x85, 0x2028, 0x2029:
			out = append(out, s[start:i])
			start = i + 1
		case '\r':
			out = append(out, s[start:i])
			if i+1 < len(s) && s[i+1] == '\n' {
				i++
			}
			start = i + 1
		}
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}

func pyStrip(s []rune) []rune {
	a, b := 0, len(s)
	for a < b && pyIsSpace(s[a]) {
		a++
	}
	for b > a && pyIsSpace(s[b-1]) {
		b--
	}
	return s[a:b]
}

func pyRStrip(s []rune) []rune {
	b := len(s)
	for b > 0 && pyIsSpace(s[b-1]) {
		b--
	}
	return s[:b]
}

// pySplit mirrors str.split() with no arguments.
func pySplit(s []rune) [][]rune {
	var out [][]rune
	i := 0
	for i < len(s) {
		for i < len(s) && pyIsSpace(s[i]) {
			i++
		}
		j := i
		for j < len(s) && !pyIsSpace(s[j]) {
			j++
		}
		if j > i {
			out = append(out, s[i:j])
		}
		i = j
	}
	return out
}

// pyInt mirrors int(s, base) for the plain forms used in font files.
func pyInt(s []rune, base int) (int, error) {
	t := string(pyStrip(s))
	neg := false
	if strings.HasPrefix(t, "+") || strings.HasPrefix(t, "-") {
		neg = t[0] == '-'
		t = t[1:]
	}
	if base == 16 && len(t) >= 2 && (t[:2] == "0x" || t[:2] == "0X") {
		t = t[2:]
		t = strings.TrimPrefix(t, "_")
	}
	if t == "" || strings.HasPrefix(t, "_") || strings.HasSuffix(t, "_") || strings.Contains(t, "__") {
		return 0, errPython
	}
	t = strings.ReplaceAll(t, "_", "")
	v, err := strconv.ParseInt(t, base, 64)
	if err != nil {
		return 0, errPython
	}
	if neg {
		v = -v
	}
	return int(v), nil
}

// decodeUTF8Replace mirrors bytes.decode('UTF-8', 'replace'): one U+FFFD
// per maximal invalid subsequence, as CPython does.
func decodeUTF8Replace(b []byte) []rune {
	out := make([]rune, 0, len(b))
	for i := 0; i < len(b); {
		c := b[i]
		if c < 0x80 {
			out = append(out, rune(c))
			i++
			continue
		}
		if r, n := utf8.DecodeRune(b[i:]); r != utf8.RuneError || n > 1 {
			out = append(out, r)
			i += n
			continue
		}
		need, lo, hi := 0, byte(0x80), byte(0xBF)
		switch {
		case c >= 0xC2 && c <= 0xDF:
			need = 1
		case c == 0xE0:
			need, lo = 2, 0xA0
		case c == 0xED:
			need, hi = 2, 0x9F
		case c >= 0xE1 && c <= 0xEF:
			need = 2
		case c == 0xF0:
			need, lo = 3, 0x90
		case c == 0xF4:
			need, hi = 3, 0x8F
		case c >= 0xF1 && c <= 0xF3:
			need = 3
		}
		j := i + 1
		for k := 0; k < need && j < len(b); k++ {
			x := b[j]
			if k == 0 {
				if x < lo || x > hi {
					break
				}
			} else if x < 0x80 || x > 0xBF {
				break
			}
			j++
		}
		out = append(out, utf8.RuneError)
		i = j
	}
	return out
}

func runesEq(a []rune, s string) bool { return string(a) == s }

// ------------------------------------------------------------------ FigletFont

type font struct {
	name           string
	height         int
	hardBlank      []rune
	hardBlankRune  rune
	printDirection *int
	smushMode      int
	chars          map[int][][]rune
	width          map[int]int
}

var errFontNotFound = errors.New("font not found")

func fileExists(p string) bool {
	st, err := os.Stat(p)
	return err == nil && st.Mode().IsRegular()
}

func embeddedFont(fn string) ([]byte, bool) {
	b, err := fontFS.ReadFile("fonts/" + fn)
	return b, err == nil
}

// preloadFont mirrors FigletFont.preloadFont, including its search order.
func preloadFont(name string) ([]rune, error) {
	var data []byte
	found := false
	var diskPath string
	for _, ext := range []string{"tlf", "flf"} {
		fn := name + "." + ext
		if b, ok := embeddedFont(fn); ok && !strings.ContainsAny(name, "/\\") {
			data, found, diskPath = b, true, ""
			break
		}
		for _, loc := range []string{"./", "/usr/local/share/pyfiglet/", "/usr/local/share/figlet", "/usr/share/figlet"} {
			full := filepath.Join(loc, fn)
			if fileExists(full) {
				diskPath, found = full, true
				break
			}
		}
	}
	if !found {
		return nil, errFontNotFound
	}
	if diskPath != "" {
		b, err := os.ReadFile(diskPath)
		if err != nil {
			return nil, errPython
		}
		data = b
	}
	if zr, err := zip.NewReader(bytes.NewReader(data), int64(len(data))); err == nil && len(zr.File) > 0 {
		f, err := zr.File[0].Open()
		if err != nil {
			return nil, errPython
		}
		data, err = io.ReadAll(f)
		f.Close()
		if err != nil {
			return nil, errPython
		}
	}
	if len(data) == 0 {
		return nil, errFontNotFound
	}
	return decodeUTF8Replace(data), nil
}

func loadFont(name string) (*font, error) {
	raw, err := preloadFont(name)
	if err != nil {
		return nil, err
	}
	for i, r := range raw {
		if r == 0x85 || r == 0x2028 || r == 0x2029 {
			raw[i] = ' '
		}
	}
	data := pySplitLines(raw)
	pop := func() ([]rune, error) {
		if len(data) == 0 {
			return nil, errPython
		}
		l := data[0]
		data = data[1:]
		return l, nil
	}

	header, err := pop()
	if err != nil {
		return nil, err
	}
	// reMagicNumber = ^[tf]lf2.
	if len(header) < 5 || (header[0] != 't' && header[0] != 'f') || header[1] != 'l' ||
		header[2] != 'f' || header[3] != '2' || header[4] == '\n' {
		return nil, errPython
	}
	fields := pySplit(header[5:])
	if len(fields) < 6 {
		return nil, errPython
	}
	f := &font{name: name, chars: map[int][][]rune{}, width: map[int]int{}}
	f.hardBlank = fields[0]
	f.hardBlankRune = neverChar
	if len(f.hardBlank) == 1 {
		f.hardBlankRune = f.hardBlank[0]
	}
	nums := make([]int, 5)
	for k := 0; k < 5; k++ {
		if nums[k], err = pyInt(fields[1+k], 10); err != nil {
			return nil, err
		}
	}
	height, oldLayout, commentLines := nums[0], nums[3], nums[4]
	var fullLayout *int
	if len(fields) > 6 {
		v, err := pyInt(fields[6], 10)
		if err != nil {
			return nil, err
		}
		f.printDirection = &v
	}
	if len(fields) > 7 {
		v, err := pyInt(fields[7], 10)
		if err != nil {
			return nil, err
		}
		fullLayout = &v
	}
	if fullLayout == nil {
		v := 0
		switch {
		case oldLayout == 0:
			v = 64
		case oldLayout < 0:
			v = 0
		default:
			v = (oldLayout & 31) | 128
		}
		fullLayout = &v
	}
	f.height = height
	f.smushMode = *fullLayout

	for i := 0; i < commentLines; i++ {
		if _, err := pop(); err != nil {
			return nil, err
		}
	}

	readChar := func() (int, [][]rune, error) {
		var end rune
		haveEnd := false
		width := 0
		var rows [][]rune
		for k := 0; k < height; k++ {
			line, err := pop()
			if err != nil {
				return 0, nil, err
			}
			if !haveEnd {
				// reEndMarker = (.)\s*$ : the last non-blank character (or
				// the first one, if the whole line is blank).
				if len(line) == 0 {
					return 0, nil, errPython
				}
				p := len(line) - 1
				for p >= 0 && pyIsSpace(line[p]) {
					p--
				}
				if p < 0 {
					p = 0
				}
				end, haveEnd = line[p], true
			}
			// re.sub(escape(end) + '{1,2}\s*$', '', line)
			cut := len(line)
			for i := 0; i < len(line); i++ {
				if line[i] != end {
					continue
				}
				restBlank := func(from int) bool {
					for _, r := range line[from:] {
						if !pyIsSpace(r) {
							return false
						}
					}
					return true
				}
				if (i+1 < len(line) && line[i+1] == end && restBlank(i+2)) || restBlank(i+1) {
					cut = i
					break
				}
			}
			line = line[:cut]
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

	for i := 32; i < 127; i++ {
		w, rows, err := readChar()
		if err != nil {
			return nil, err
		}
		if i == 32 || nonEmpty(rows) {
			f.chars[i], f.width[i] = rows, w
		}
	}
	if len(data) > 0 {
		for _, c := range "ÄÖÜäöüß" {
			w, rows, err := readChar()
			if err != nil {
				return nil, err
			}
			if nonEmpty(rows) {
				f.chars[int(c)], f.width[int(c)] = rows, w
			}
		}
	}
	for len(data) > 0 {
		line, _ := pop()
		line = pyStrip(line)
		tok := line
		for k, r := range line {
			if r == ' ' {
				tok = line[:k]
				break
			}
		}
		if len(tok) == 0 {
			continue
		}
		if len(tok) >= 2 && tok[0] == '0' && (tok[1] == 'x' || tok[1] == 'X') {
			code, err := pyInt(tok, 16)
			if err != nil {
				return nil, err
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

// ------------------------------------------------------------------ FigletBuilder

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

type blankMarker struct {
	buffer   [][]rune
	iterator int
}

type builder struct {
	text      []int
	direction string
	width     int
	font      *font
	justify   string

	iterator          int
	maxSmush          int
	curCharWidth      int
	prevCharWidth     int
	currentTotalWidth int

	blankMarkers []blankMarker
	queue        [][][]rune
	buffer       [][]rune
}

func newBuilder(text []rune, f *font, direction string, width int, justify string) *builder {
	b := &builder{direction: direction, width: width, font: f, justify: justify}
	for _, r := range text {
		b.text = append(b.text, int(r))
	}
	b.buffer = emptyBuffer(f.height)
	return b
}

func emptyBuffer(h int) [][]rune {
	buf := make([][]rune, h)
	for i := range buf {
		buf[i] = []rune{}
	}
	return buf
}

func copyBuffer(buf [][]rune) [][]rune {
	out := make([][]rune, len(buf))
	for i, r := range buf {
		out[i] = append([]rune{}, r...)
	}
	return out
}

func (b *builder) charAt(i int) [][]rune {
	if i < 0 || i >= len(b.text) {
		return nil
	}
	c, ok := b.font.chars[b.text[i]]
	if !ok {
		return nil
	}
	return c
}

func (b *builder) widthAt(i int) int { return b.font.width[b.text[i]] }

func (b *builder) addCharToProduct() error {
	curChar := b.charAt(b.iterator)
	if b.text[b.iterator] == '\n' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{copyBuffer(b.buffer), b.iterator})
		b.handleNewLine()
		return nil
	}
	if curChar == nil {
		return nil
	}
	if b.width < b.widthAt(b.iterator) {
		return errPython // CharNotPrinted
	}
	b.curCharWidth = b.widthAt(b.iterator)
	b.maxSmush = b.smushAmount(b.buffer, curChar)
	b.currentTotalWidth = len(b.buffer[0]) + b.curCharWidth - b.maxSmush

	if b.text[b.iterator] == ' ' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{copyBuffer(b.buffer), b.iterator})
	}
	if b.currentTotalWidth >= b.width {
		b.handleNewLine()
	} else {
		for row := 0; row < b.font.height; row++ {
			if err := b.addCurCharRowToBufferRow(curChar, row); err != nil {
				return err
			}
		}
	}
	b.prevCharWidth = b.curCharWidth
	return nil
}

func (b *builder) addCurCharRowToBufferRow(curChar [][]rune, row int) error {
	addLeft, addRight, err := b.smushRow(curChar, row)
	if err != nil {
		return err
	}
	tail := []rune{}
	if b.maxSmush < len(addRight) {
		tail = addRight[b.maxSmush:]
	}
	b.buffer[row] = append(append([]rune{}, addLeft...), tail...)
	return nil
}

func (b *builder) smushRow(curChar [][]rune, row int) ([]rune, []rune, error) {
	addLeft := append([]rune{}, b.buffer[row]...)
	addRight := curChar[row]
	if b.direction == "right-to-left" {
		addLeft, addRight = append([]rune{}, addRight...), addLeft
	}
	for i := 0; i < b.maxSmush; i++ {
		idx := len(addLeft) - b.maxSmush + i
		left := noChar
		if idx >= 0 && idx < len(addLeft) {
			left = addLeft[idx]
		}
		if i >= len(addRight) {
			return nil, nil, errPython // IndexError
		}
		right := addRight[i]
		smushed, ok := b.smushChars(left, right)
		if idx < 0 || idx > len(addLeft) {
			continue
		}
		if idx == len(addLeft) || !ok {
			return nil, nil, errPython // IndexError / TypeError in ''.join
		}
		if smushed == noChar {
			addLeft = append(addLeft[:idx], addLeft[idx+1:]...)
		} else {
			addLeft[idx] = smushed
		}
	}
	return addLeft, addRight, nil
}

func (b *builder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = emptyBuffer(b.font.height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	curChar := b.charAt(b.iterator)
	if curChar == nil {
		return
	}
	b.maxSmush = b.smushAmount(b.buffer, curChar)
}

func (b *builder) handleNewLine() {
	if n := len(b.blankMarkers); n > 0 {
		m := b.blankMarkers[n-1]
		b.blankMarkers = b.blankMarkers[:n-1]
		b.queue = append(b.queue, m.buffer)
		b.iterator = m.iterator
	} else {
		b.queue = append(b.queue, b.buffer)
		b.iterator--
	}
	b.cutBufferCommon()
}

func (b *builder) smushAmount(buffer [][]rune, curChar [][]rune) int {
	if b.font.smushMode&(smSmush|smKern) == 0 {
		return 0
	}
	maxSmush := b.curCharWidth
	for row := 0; row < b.font.height; row++ {
		lineLeft, lineRight := buffer[row], curChar[row]
		if b.direction == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}
		trimmed := len(lineLeft)
		for trimmed > 0 && lineLeft[trimmed-1] == ' ' {
			trimmed--
		}
		linebd := trimmed - 1
		if linebd < 0 {
			linebd = 0
		}
		ch1 := noChar
		if linebd < len(lineLeft) {
			ch1 = lineLeft[linebd]
		} else {
			linebd = 0
		}
		charbd := 0
		for charbd < len(lineRight) && lineRight[charbd] == ' ' {
			charbd++
		}
		ch2 := noChar
		if charbd < len(lineRight) {
			ch2 = lineRight[charbd]
		} else {
			charbd = len(lineRight)
		}
		amt := charbd + len(lineLeft) - 1 - linebd
		if ch1 == noChar || ch1 == ' ' {
			amt++
		} else if ch2 != noChar {
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

// in mirrors Python's `c in s` for a one-character (or empty) string c.
func in(c rune, s string) bool { return c == noChar || strings.ContainsRune(s, c) }

func (b *builder) smushChars(left, right rune) (rune, bool) {
	if left == ' ' {
		return right, true
	}
	if right == ' ' {
		return left, true
	}
	if b.prevCharWidth < 2 || b.curCharWidth < 2 {
		return 0, false
	}
	mode := b.font.smushMode
	if mode&smSmush == 0 {
		return 0, false
	}
	hb := b.font.hardBlankRune
	if mode&63 == 0 {
		if left == hb {
			return right, true
		}
		if right == hb {
			return left, true
		}
		if b.direction == "right-to-left" {
			return left, true
		}
		return right, true
	}
	if mode&smHardblank != 0 && left == hb && right == hb {
		return left, true
	}
	if left == hb || right == hb {
		return 0, false
	}
	if mode&smEqual != 0 && left == right {
		return left, true
	}
	var smushes [][2]string
	if mode&smLowline != 0 {
		smushes = append(smushes, [2]string{"_", `|/\[]{}()<>`})
	}
	if mode&smHierarchy != 0 {
		smushes = append(smushes,
			[2]string{"|", `/\[]{}()<>`},
			[2]string{`\/`, "[]{}()<>"},
			[2]string{"[]", "{}()<>"},
			[2]string{"{}", "()<>"},
			[2]string{"()", "<>"},
		)
	}
	for _, s := range smushes {
		if in(left, s[0]) && in(right, s[1]) {
			return right, true
		}
		if in(right, s[0]) && in(left, s[1]) {
			return left, true
		}
	}
	if mode&smPair != 0 && left != noChar && right != noChar {
		for _, pair := range []string{string(left) + string(right), string(right) + string(left)} {
			if pair == "[]" || pair == "{}" || pair == "()" {
				return '|', true
			}
		}
	}
	if mode&smBigX != 0 {
		if left == '/' && right == '\\' {
			return '|', true
		}
		if right == '/' && left == '\\' {
			return 'Y', true
		}
		if left == '>' && right == '<' {
			return 'X', true
		}
	}
	return 0, false
}

func (b *builder) render() ([]rune, error) {
	for b.iterator < len(b.text) {
		if err := b.addCharToProduct(); err != nil {
			return nil, err
		}
		b.iterator++
	}
	if len(b.buffer[0]) != 0 {
		b.queue = append(b.queue, b.buffer)
	}
	var out []rune
	hb := string(b.font.hardBlank)
	for _, buf := range b.queue {
		for row := 0; row < b.font.height; row++ {
			pad := 0
			switch b.justify {
			case "right":
				pad = b.width - len(buf[row]) - 1
			case "center":
				pad = (b.width - len(buf[row])) / 2
			}
			if pad > 0 {
				buf[row] = append([]rune(strings.Repeat(" ", pad)), buf[row]...)
			}
		}
		rows := make([]string, len(buf))
		for i, r := range buf {
			rows[i] = string(r)
		}
		s := strings.Join(rows, "\n") + "\n"
		s = strings.ReplaceAll(s, hb, " ")
		out = append(out, []rune(s)...)
	}
	return out, nil
}

// ------------------------------------------------------------------ FigletString

var reverseMap = []rune("\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f" +
	"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f" +
	" !\"#$%&')(*+,-.\\" +
	"0123456789:;>=<?" +
	"@ABCDEFGHIJKLMNO" +
	"PQRSTUVWXYZ]/[^_" +
	"`abcdefghijklmno" +
	"pqrstuvwxyz}|{~\x7f")

var flipMap = []rune("\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f" +
	"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f" +
	" !\"#$%&'()*+,-.\\" +
	"0123456789:;<=>?" +
	"@VBCDEFGHIJKLWNO" +
	"bQbSTUAMXYZ[/]v-" +
	"`aPcdefghijklwno" +
	"pqrstu^mxyz{|}~\x7f")

// translate mirrors str.translate with a 256-entry table; characters
// 0x80-0xFF map to themselves and anything higher is left unchanged.
func translate(row []rune, table []rune) []rune {
	out := make([]rune, len(row))
	for i, r := range row {
		if r >= 0 && int(r) < len(table) {
			out[i] = table[r]
		} else {
			out[i] = r
		}
	}
	return out
}

func newFromList(rows [][]rune) []rune {
	var out []rune
	for i, r := range rows {
		if i > 0 {
			out = append(out, '\n')
		}
		out = append(out, r...)
	}
	return append(out, '\n')
}

func reverseFS(s []rune) []rune {
	var rows [][]rune
	for _, row := range pySplitLines(s) {
		t := translate(row, reverseMap)
		for i, j := 0, len(t)-1; i < j; i, j = i+1, j-1 {
			t[i], t[j] = t[j], t[i]
		}
		rows = append(rows, t)
	}
	return newFromList(rows)
}

func flipFS(s []rune) []rune {
	lines := pySplitLines(s)
	var rows [][]rune
	for i := len(lines) - 1; i >= 0; i-- {
		rows = append(rows, translate(lines[i], flipMap))
	}
	return newFromList(rows)
}

func stripSurroundingNewlines(s []rune) []rune {
	var rows [][]rune
	seen := false
	for _, row := range pySplitLines(s) {
		if len(pyStrip(row)) != 0 || seen {
			seen = true
			rows = append(rows, row)
		}
	}
	return pyRStrip(newFromList(rows))
}

// ------------------------------------------------------------------ command line (optparse)

type options struct {
	font, direction, justify string
	width                    int
	reverse, flip            bool
	strip, normalize         bool
	listFonts, infoFont      bool
	load, color              string
	args                     []string
}

var longOpts = []string{"--font", "--direction", "--justify", "--width", "--reverse",
	"--normalize-surrounding-newlines", "--strip-surrounding-newlines", "--flip",
	"--list_fonts", "--info_font", "--load", "--color", "--help", "--version"}

func takesValue(opt string) bool {
	switch opt {
	case "-f", "-D", "-j", "-w", "-L", "-c", "--font", "--direction", "--justify", "--width", "--load", "--color":
		return true
	}
	return false
}

func parseNum(v string) (int, error) {
	lv := strings.ToLower(v)
	base, t := 10, v
	switch {
	case strings.HasPrefix(lv, "0x"):
		base, t = 16, v[2:]
	case strings.HasPrefix(lv, "0b"):
		base, t = 2, v[2:]
		if t == "" {
			t = "0"
		}
	case strings.HasPrefix(v, "0"):
		base = 8
	}
	n, err := strconv.ParseInt(strings.TrimSpace(t), base, 64)
	return int(n), err
}

func apply(o *options, opt, val string) error {
	switch opt {
	case "-f", "--font":
		o.font = val
	case "-D", "--direction":
		if val != "auto" && val != "left-to-right" && val != "right-to-left" {
			return errPython
		}
		o.direction = val
	case "-j", "--justify":
		if val != "auto" && val != "left" && val != "center" && val != "right" {
			return errPython
		}
		o.justify = val
	case "-w", "--width":
		n, err := parseNum(val)
		if err != nil {
			return errPython
		}
		o.width = n
	case "-r", "--reverse":
		o.reverse = true
	case "-F", "--flip":
		o.flip = true
	case "-s", "--strip-surrounding-newlines":
		o.strip = true
	case "-n", "--normalize-surrounding-newlines":
		o.normalize = true
	case "-l", "--list_fonts":
		o.listFonts = true
	case "-i", "--info_font":
		o.infoFont = true
	case "-L", "--load":
		o.load = val
	case "-c", "--color":
		o.color = val
	default:
		return errPython // includes -h/--help/--version: not in scope
	}
	return nil
}

func parseArgs(argv []string) (*options, error) {
	o := &options{font: "standard", direction: "auto", justify: "auto", width: 80, color: ":"}
	for i := 0; i < len(argv); i++ {
		a := argv[i]
		switch {
		case a == "--":
			o.args = append(o.args, argv[i+1:]...)
			return o, nil
		case strings.HasPrefix(a, "--"):
			name, val, hasVal := strings.Cut(a, "=")
			var match []string
			for _, l := range longOpts {
				if l == name {
					match = []string{l}
					break
				}
				if strings.HasPrefix(l, name) {
					match = append(match, l)
				}
			}
			if len(match) != 1 {
				return nil, errPython
			}
			name = match[0]
			if takesValue(name) {
				if !hasVal {
					if i+1 >= len(argv) {
						return nil, errPython
					}
					i++
					val = argv[i]
				}
			} else if hasVal {
				return nil, errPython
			}
			if err := apply(o, name, val); err != nil {
				return nil, err
			}
		case len(a) > 1 && a[0] == '-':
			rs := []rune(a[1:])
			for k := 0; k < len(rs); k++ {
				opt := "-" + string(rs[k])
				if takesValue(opt) {
					val := string(rs[k+1:])
					if val == "" {
						if i+1 >= len(argv) {
							return nil, errPython
						}
						i++
						val = argv[i]
					}
					if err := apply(o, opt, val); err != nil {
						return nil, err
					}
					break
				}
				if err := apply(o, opt, ""); err != nil {
					return nil, err
				}
			}
		default:
			o.args = append(o.args, a)
		}
	}
	return o, nil
}

func pyRepr(s string) string {
	q := "'"
	if strings.Contains(s, "'") && !strings.Contains(s, "\"") {
		q = "\""
	}
	r := strings.ReplaceAll(s, "\\", "\\\\")
	r = strings.ReplaceAll(r, q, "\\"+q)
	return q + r + q
}

func run(argv []string) int {
	o, err := parseArgs(argv)
	if err != nil {
		return 2
	}
	if o.listFonts || o.color == "list" || o.infoFont || o.load != "" {
		return 0 // out of scope for this task
	}
	if len(o.args) == 0 {
		fmt.Println("Usage: figlet [options] [text..]")
		return 1
	}
	text := []rune(strings.Join(o.args, " "))

	f, err := loadFont(o.font)
	if errors.Is(err, errFontNotFound) {
		fmt.Printf("pyfiglet error: requested font %s not found.\n", pyRepr(o.font))
		return 1
	}
	if err != nil {
		return 1
	}

	direction := o.direction
	if direction == "auto" {
		direction = "left-to-right"
		if f.printDirection != nil && *f.printDirection == 1 {
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

	r, err := newBuilder(text, f, direction, o.width, justify).render()
	if err != nil {
		return 1
	}
	if o.reverse {
		r = reverseFS(r)
	}
	if o.flip {
		r = flipFS(r)
	}
	if o.strip {
		r = stripSurroundingNewlines(r)
	} else if o.normalize {
		r = append(append([]rune{'\n'}, stripSurroundingNewlines(r)...), '\n')
	}
	w := os.Stdout
	w.WriteString(string(r))
	w.WriteString("\n")
	return 0
}

func main() {
	os.Exit(run(os.Args[1:]))
}
