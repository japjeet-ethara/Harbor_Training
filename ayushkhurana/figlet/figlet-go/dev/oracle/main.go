// Command figlet is a Go port of the rendering path of pyfiglet 1.0.4
// (commit 255827efbc09d662875dad50fa0edc1e1263bf45): FigletFont.loadFont,
// FigletBuilder (smushing, wrapping, justification), FigletString.reverse/flip/strip
// and the options -f -w -j -D -r -F -s -n of main().
//
// The port follows the Python code line by line on purpose, including its quirks
// (an empty string "is in" every string, -s beats -n, ...). Standard library only.
package main

import (
	"embed"
	"fmt"
	"os"
	"strconv"
	"strings"
)

//go:embed fonts/*.flf
var fontFiles embed.FS

// ---------------------------------------------------------------- errors

type figletError struct{ msg string }

func fail(format string, a ...any) { panic(figletError{fmt.Sprintf(format, a...)}) }

type fontNotFound struct{ name string }

// ---------------------------------------------------------------- python string helpers

// pyIsSpace mirrors str.isspace() for one character.
func pyIsSpace(r rune) bool {
	switch r {
	case ' ', '\t', '\n', '\v', '\f', '\r', 0x1c, 0x1d, 0x1e, 0x1f, 0x85, 0xa0, 0x1680,
		0x2028, 0x2029, 0x202f, 0x205f, 0x3000:
		return true
	}
	return r >= 0x2000 && r <= 0x200a
}

// pySplitLines mirrors str.splitlines() (no keepends).
func pySplitLines(s string) []string {
	var out []string
	rs := []rune(s)
	start, i := 0, 0
	for i < len(rs) {
		switch rs[i] {
		case '\n', '\v', '\f', 0x1c, 0x1d, 0x1e, 0x85, 0x2028, 0x2029:
			out = append(out, string(rs[start:i]))
			i++
			start = i
		case '\r':
			out = append(out, string(rs[start:i]))
			i++
			if i < len(rs) && rs[i] == '\n' {
				i++
			}
			start = i
		default:
			i++
		}
	}
	if start < len(rs) {
		out = append(out, string(rs[start:]))
	}
	return out
}

func pyStrip(s string) string { return strings.TrimFunc(s, pyIsSpace) }

func pyRstrip(s string) string { return strings.TrimRightFunc(s, pyIsSpace) }

// rstripSpace / lstripSpace strip only the ASCII space, like lineLeft.rstrip(' ').
func rstripSpace(r []rune) []rune {
	n := len(r)
	for n > 0 && r[n-1] == ' ' {
		n--
	}
	return r[:n]
}

func lstripCount(r []rune) int {
	n := 0
	for n < len(r) && r[n] == ' ' {
		n++
	}
	return n
}

// sliceFrom mirrors r[n:] for any n, including negative.
func sliceFrom(r []rune, n int) []rune {
	if n < 0 {
		n += len(r)
		if n < 0 {
			n = 0
		}
	}
	if n > len(r) {
		n = len(r)
	}
	return r[n:]
}

func concat(a, b []rune) []rune {
	out := make([]rune, 0, len(a)+len(b))
	out = append(out, a...)
	return append(out, b...)
}

func repeatSpace(n int) []rune {
	if n <= 0 {
		return nil
	}
	out := make([]rune, n)
	for i := range out {
		out[i] = ' '
	}
	return out
}

// ---------------------------------------------------------------- font loading

type figFont struct {
	name           string
	height         int
	hardBlank      string
	printDirection int // -1 when the header has no such field
	smushMode      int
	chars          map[int][][]rune
	width          map[int]int
}

func rowsEmpty(rows [][]rune) bool {
	for _, r := range rows {
		if len(r) > 0 {
			return false
		}
	}
	return true
}

// endMarker mirrors reEndMarker = (.)\s*$ : the last non-space character
// (the first character when the whole line is blank).
func endMarker(line []rune) rune {
	if len(line) == 0 {
		fail("end marker not found")
	}
	for i := len(line) - 1; i >= 0; i-- {
		if !pyIsSpace(line[i]) {
			return line[i]
		}
	}
	return line[0]
}

// stripEnd removes, like the original's end-marker regular expression, one or two end-marker
// characters followed by optional whitespace from the end of the line.
func stripEnd(line []rune, end rune) []rune {
	allSpace := func(r []rune) bool {
		for _, c := range r {
			if !pyIsSpace(c) {
				return false
			}
		}
		return true
	}
	for p := 0; p < len(line); p++ {
		for k := 2; k >= 1; k-- {
			if p+k > len(line) {
				continue
			}
			ok := true
			for q := p; q < p+k; q++ {
				if line[q] != end {
					ok = false
					break
				}
			}
			if ok && allSpace(line[p+k:]) {
				return line[:p]
			}
		}
	}
	return line
}

func loadFont(name string) (f *figFont) {
	data, err := fontFiles.ReadFile("fonts/" + name + ".flf")
	if err != nil || len(data) == 0 {
		panic(fontNotFound{name})
	}
	defer func() {
		if r := recover(); r != nil {
			if fe, ok := r.(figletError); ok {
				panic(figletError{fmt.Sprintf("problem parsing %s font: %s", name, fe.msg)})
			}
			panic(r)
		}
	}()

	text := strings.ToValidUTF8(string(data), "�")
	text = strings.NewReplacer("\u0085", " ", " ", " ", " ", " ").Replace(text)
	lines := pySplitLines(text)
	pos := 0
	pop := func() string {
		if pos >= len(lines) {
			fail("unexpected end of font")
		}
		l := lines[pos]
		pos++
		return l
	}

	header := pop()
	// reMagicNumber = ^[tf]lf2.   (five characters)
	hr := []rune(header)
	if len(hr) < 5 || (hr[0] != 't' && hr[0] != 'f') || hr[1] != 'l' || hr[2] != 'f' || hr[3] != '2' {
		fail("%s is not a valid figlet font", name)
	}
	fields := strings.Fields(string(hr[5:]))
	if len(fields) < 6 {
		fail("malformed header for %s", name)
	}
	atoi := func(s string) int {
		n, err := strconv.Atoi(s)
		if err != nil {
			fail("bad number %q", s)
		}
		return n
	}
	f = &figFont{name: name, hardBlank: fields[0], printDirection: -1,
		chars: map[int][][]rune{}, width: map[int]int{}}
	f.height = atoi(fields[1])
	// fields: hardblank height baseline maxlength oldLayout commentLines [printDirection [fullLayout]]
	oldLayout := atoi(fields[4])
	commentLines := atoi(fields[5])
	if len(fields) > 6 {
		f.printDirection = atoi(fields[6])
	}
	fullLayout, haveFull := 0, false
	if len(fields) > 7 {
		fullLayout, haveFull = atoi(fields[7]), true
	}
	if !haveFull {
		switch {
		case oldLayout == 0:
			fullLayout = 64
		case oldLayout < 0:
			fullLayout = 0
		default:
			fullLayout = (oldLayout & 31) | 128
		}
	}
	f.smushMode = fullLayout

	for i := 0; i < commentLines; i++ {
		pop()
	}

	loadChar := func() (int, [][]rune) {
		var end rune
		haveEnd := false
		width := 0
		rows := make([][]rune, 0, f.height)
		for k := 0; k < f.height; k++ {
			line := []rune(pop())
			if !haveEnd {
				end = endMarker(line)
				haveEnd = true
			}
			line = stripEnd(line, end)
			if len(line) > width {
				width = len(line)
			}
			rows = append(rows, line)
		}
		return width, rows
	}

	for i := 32; i < 127; i++ {
		w, letter := loadChar()
		if i == 32 || !rowsEmpty(letter) {
			f.chars[i] = letter
			f.width[i] = w
		}
	}
	if pos < len(lines) {
		for _, c := range "ÄÖÜäöüß" {
			w, letter := loadChar()
			if !rowsEmpty(letter) {
				f.chars[int(c)] = letter
				f.width[int(c)] = w
			}
		}
	}
	for pos < len(lines) {
		line := pyStrip(pop())
		first := line
		if i := strings.IndexByte(line, ' '); i >= 0 {
			first = line[:i]
		}
		if first == "" {
			continue
		}
		if strings.HasPrefix(first, "0x") || strings.HasPrefix(first, "0X") {
			code, err := strconv.ParseInt(first[2:], 16, 64)
			if err != nil {
				fail("bad character code %q", first)
			}
			w, letter := loadChar()
			if !rowsEmpty(letter) {
				f.chars[int(code)] = letter
				f.width[int(code)] = w
			}
		}
	}
	return f
}

// ---------------------------------------------------------------- layout engine (FigletBuilder)

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
	buf [][]rune
	it  int
}

type builder struct {
	text      []int
	direction string
	width     int
	font      *figFont
	justify   string

	iterator, maxSmush                             int
	curCharWidth, prevCharWidth, currentTotalWidth int

	blankMarkers []marker
	product      [][][]rune
	buffer       [][]rune
}

func newBuilder(text string, font *figFont, direction string, width int, justify string) *builder {
	b := &builder{direction: direction, width: width, font: font, justify: justify}
	for _, r := range text {
		b.text = append(b.text, int(r))
	}
	b.buffer = make([][]rune, font.height)
	return b
}

func copyBuffer(buf [][]rune) [][]rune {
	out := make([][]rune, len(buf))
	copy(out, buf)
	return out
}

func (b *builder) getCharAt(i int) [][]rune {
	if i < 0 || i >= len(b.text) {
		return nil
	}
	return b.font.chars[b.text[i]] // nil when the font has no such character
}

func (b *builder) getCurChar() [][]rune { return b.getCharAt(b.iterator) }

func (b *builder) getCurWidth() int { return b.font.width[b.text[b.iterator]] }

func (b *builder) addCharToProduct() {
	curChar := b.getCurChar()

	if b.text[b.iterator] == '\n' {
		b.blankMarkers = append(b.blankMarkers, marker{copyBuffer(b.buffer), b.iterator})
		b.handleNewLine()
		return
	}
	if curChar == nil {
		return
	}
	if b.width < b.getCurWidth() {
		fail("Width is not enough to print this character")
	}
	b.curCharWidth = b.getCurWidth()
	b.maxSmush = b.smushAmount(b.buffer, curChar)

	b.currentTotalWidth = len(b.buffer[0]) + b.curCharWidth - b.maxSmush

	if b.text[b.iterator] == ' ' {
		b.blankMarkers = append(b.blankMarkers, marker{copyBuffer(b.buffer), b.iterator})
	}

	if b.currentTotalWidth >= b.width {
		b.handleNewLine()
	} else {
		for row := 0; row < b.font.height; row++ {
			b.addCurCharRowToBufferRow(curChar, row)
		}
	}
	b.prevCharWidth = b.curCharWidth
}

func (b *builder) emptyBuffer() [][]rune { return make([][]rune, b.font.height) }

func (b *builder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = b.emptyBuffer()
	b.blankMarkers = nil
	b.prevCharWidth = 0
	curChar := b.getCurChar()
	if curChar == nil {
		return
	}
	b.maxSmush = b.smushAmount(b.buffer, curChar)
}

func (b *builder) handleNewLine() {
	if n := len(b.blankMarkers); n > 0 {
		m := b.blankMarkers[n-1]
		b.blankMarkers = b.blankMarkers[:n-1]
		b.product = append(b.product, m.buf)
		b.iterator = m.it
	} else {
		b.product = append(b.product, b.buffer)
		b.iterator--
	}
	// The original loops forever for some width/letter pairs; fail instead of hanging.
	if len(b.product) > 1000000 {
		fail("endless loop")
	}
	b.cutBufferCommon()
}

func (b *builder) addCurCharRowToBufferRow(curChar [][]rune, row int) {
	addLeft, addRight := b.smushRow(curChar, row)
	b.buffer[row] = concat(addLeft, sliceFrom(addRight, b.maxSmush))
}

func (b *builder) smushRow(curChar [][]rune, row int) ([]rune, []rune) {
	addLeft := b.buffer[row]
	addRight := curChar[row]
	if b.direction == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}
	addLeft = append([]rune(nil), addLeft...) // never write into the font's own rows
	for i := 0; i < b.maxSmush; i++ {
		left, idx := "", len(addLeft)-b.maxSmush+i
		if idx >= 0 && idx < len(addLeft) {
			left = string(addLeft[idx])
		}
		right := string(addRight[i]) // IndexError in Python when out of range
		smushed, ok := b.smushChars(left, right)
		if idx < 0 || idx > len(addLeft) {
			continue
		}
		if idx == len(addLeft) {
			fail("list assignment index out of range")
		}
		if !ok {
			fail("smushed character is None")
		}
		rs := []rune(smushed)
		if len(rs) == 1 {
			addLeft[idx] = rs[0]
		} else { // an empty string would delete the character, as ''.join does
			addLeft = append(addLeft[:idx], append(rs, addLeft[idx+1:]...)...)
		}
	}
	return addLeft, addRight
}

func (b *builder) smushAmount(buffer [][]rune, curChar [][]rune) int {
	if b.font.smushMode&(smSmush|smKern) == 0 {
		return 0
	}
	maxSmush := b.curCharWidth
	for row := 0; row < b.font.height; row++ {
		lineLeft := buffer[row]
		lineRight := curChar[row]
		if b.direction == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}

		linebd := len(rstripSpace(lineLeft)) - 1
		if linebd < 0 {
			linebd = 0
		}
		ch1 := ""
		if linebd < len(lineLeft) {
			ch1 = string(lineLeft[linebd])
		} else {
			linebd = 0
		}

		charbd := lstripCount(lineRight)
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

// smushChars mirrors FigletBuilder.smushChars; ok == false is Python's None.
func (b *builder) smushChars(left, right string) (string, bool) {
	if left == " " {
		return right, true
	}
	if right == " " {
		return left, true
	}
	if b.prevCharWidth < 2 || b.curCharWidth < 2 {
		return "", false
	}
	mode := b.font.smushMode
	if mode&smSmush == 0 {
		return "", false
	}
	hb := b.font.hardBlank
	if mode&63 == 0 { // universal overlapping
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
	if mode&smHardblank != 0 {
		if left == hb && right == hb {
			return left, true
		}
	}
	if left == hb || right == hb {
		return "", false
	}
	if mode&smEqual != 0 {
		if left == right {
			return left, true
		}
	}

	type rule struct{ a, b string }
	var smushes []rule
	if mode&smLowline != 0 {
		smushes = append(smushes, rule{"_", `|/\[]{}()<>`})
	}
	if mode&smHierarchy != 0 {
		smushes = append(smushes,
			rule{"|", `/\[]{}()<>`},
			rule{`\/`, "[]{}()<>"},
			rule{"[]", "{}()<>"},
			rule{"{}", "()<>"},
			rule{"()", "<>"},
		)
	}
	// strings.Contains(a, "") is true, exactly like Python's "" in a.
	for _, s := range smushes {
		if strings.Contains(s.a, left) && strings.Contains(s.b, right) {
			return right, true
		}
		if strings.Contains(s.a, right) && strings.Contains(s.b, left) {
			return left, true
		}
	}

	if mode&smPair != 0 {
		for _, pair := range []string{left + right, right + left} {
			if pair == "[]" || pair == "{}" || pair == "()" {
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

func (b *builder) justifyString(buffer [][]rune) [][]rune {
	switch b.justify {
	case "right":
		for row := 0; row < b.font.height; row++ {
			buffer[row] = concat(repeatSpace(b.width-len(buffer[row])-1), buffer[row])
		}
	case "center":
		for row := 0; row < b.font.height; row++ {
			buffer[row] = concat(repeatSpace((b.width-len(buffer[row]))/2), buffer[row])
		}
	}
	return buffer
}

func (b *builder) render() string {
	for b.iterator < len(b.text) {
		b.addCharToProduct()
		b.iterator++
	}
	if len(b.buffer[0]) != 0 {
		b.product = append(b.product, b.buffer)
	}
	var sb strings.Builder
	for _, buf := range b.product {
		buf = b.justifyString(buf)
		rows := make([]string, len(buf))
		for i, r := range buf {
			rows[i] = string(r)
		}
		s := strings.Join(rows, "\n") + "\n"
		sb.WriteString(strings.ReplaceAll(s, b.font.hardBlank, " "))
	}
	return sb.String()
}

// ---------------------------------------------------------------- FigletString operations

var reversePairs = map[rune]rune{
	'(': ')', ')': '(', '<': '>', '>': '<', '[': ']', ']': '[', '{': '}', '}': '{',
	'/': '\\', '\\': '/',
}

var flipPairs = map[rune]rune{
	'/': '\\', '\\': '/', 'A': 'V', 'V': 'A', 'M': 'W', 'W': 'M', 'P': 'b', 'R': 'b',
	'b': 'P', 'm': 'w', 'w': 'm', '^': 'v', 'v': '^', '_': '-',
}

func translate(s string, table map[rune]rune) string {
	rs := []rune(s)
	for i, r := range rs {
		if t, ok := table[r]; ok {
			rs[i] = t
		}
	}
	return string(rs)
}

func newFromList(rows []string) string { return strings.Join(rows, "\n") + "\n" }

func reverseText(s string) string {
	var out []string
	for _, row := range pySplitLines(s) {
		rs := []rune(translate(row, reversePairs))
		for i, j := 0, len(rs)-1; i < j; i, j = i+1, j-1 {
			rs[i], rs[j] = rs[j], rs[i]
		}
		out = append(out, string(rs))
	}
	return newFromList(out)
}

func flipText(s string) string {
	rows := pySplitLines(s)
	var out []string
	for i := len(rows) - 1; i >= 0; i-- {
		out = append(out, translate(rows[i], flipPairs))
	}
	return newFromList(out)
}

func stripSurroundingNewlines(s string) string {
	var out []string
	seen := false
	for _, row := range pySplitLines(s) {
		if pyStrip(row) != "" || seen {
			seen = true
			out = append(out, row)
		}
	}
	return pyRstrip(newFromList(out))
}

// ---------------------------------------------------------------- command line (optparse subset)

type options struct {
	font, direction, justify string
	width                    int
	reverse, normalize       bool
	strip, flip              bool
}

func usageError(msg string) {
	fmt.Fprintf(os.Stderr, "Usage: figlet [options] [text..]\n\nfiglet: error: %s\n", msg)
	os.Exit(2)
}

type optSpec struct {
	short   string
	long    string
	hasVal  bool
	handler string
}

var optTable = []optSpec{
	{"f", "font", true, "font"},
	{"D", "direction", true, "direction"},
	{"j", "justify", true, "justify"},
	{"w", "width", true, "width"},
	{"r", "reverse", false, "reverse"},
	{"n", "normalize-surrounding-newlines", false, "normalize"},
	{"s", "strip-surrounding-newlines", false, "strip"},
	{"F", "flip", false, "flip"},
}

func contains(list []string, v string) bool {
	for _, x := range list {
		if x == v {
			return true
		}
	}
	return false
}

func (o *options) set(name, val string) {
	switch name {
	case "font":
		o.font = val
	case "direction":
		if !contains([]string{"auto", "left-to-right", "right-to-left"}, val) {
			usageError(fmt.Sprintf("option -D: invalid choice: %q", val))
		}
		o.direction = val
	case "justify":
		if !contains([]string{"auto", "left", "center", "right"}, val) {
			usageError(fmt.Sprintf("option -j: invalid choice: %q", val))
		}
		o.justify = val
	case "width":
		n, err := strconv.Atoi(val)
		if err != nil {
			usageError(fmt.Sprintf("option -w: invalid integer value: %q", val))
		}
		o.width = n
	case "reverse":
		o.reverse = true
	case "normalize":
		o.normalize = true
	case "strip":
		o.strip = true
	case "flip":
		o.flip = true
	}
}

func parseArgs(argv []string) (options, []string) {
	o := options{font: "standard", direction: "auto", justify: "auto", width: 80}
	var rest []string
	for i := 0; i < len(argv); i++ {
		a := argv[i]
		switch {
		case a == "--":
			rest = append(rest, argv[i+1:]...)
			return o, rest
		case strings.HasPrefix(a, "--"):
			name, val, hasEq := strings.Cut(a[2:], "=")
			var match []optSpec
			for _, s := range optTable { // optparse accepts unambiguous prefixes
				if s.long == name {
					match = []optSpec{s}
					break
				}
				if strings.HasPrefix(s.long, name) {
					match = append(match, s)
				}
			}
			if len(match) != 1 {
				usageError("no such option: " + a)
			}
			s := match[0]
			if s.hasVal {
				if !hasEq {
					i++
					if i >= len(argv) {
						usageError("--" + s.long + " option requires an argument")
					}
					val = argv[i]
				}
				o.set(s.handler, val)
			} else {
				if hasEq {
					usageError("--" + s.long + " option does not take a value")
				}
				o.set(s.handler, "")
			}
		case len(a) > 1 && a[0] == '-':
			cluster := []rune(a[1:])
			for k := 0; k < len(cluster); k++ {
				var s *optSpec
				for j := range optTable {
					if optTable[j].short == string(cluster[k]) {
						s = &optTable[j]
					}
				}
				if s == nil {
					usageError("no such option: -" + string(cluster[k]))
				}
				if !s.hasVal {
					o.set(s.handler, "")
					continue
				}
				val := string(cluster[k+1:])
				if val == "" {
					i++
					if i >= len(argv) {
						usageError("-" + s.short + " option requires an argument")
					}
					val = argv[i]
				}
				o.set(s.handler, val)
				break
			}
		default:
			rest = append(rest, a)
		}
	}
	return o, rest
}

func run(o options, text string) (out string, code int) {
	defer func() {
		if r := recover(); r != nil {
			switch e := r.(type) {
			case fontNotFound:
				out, code = fmt.Sprintf("pyfiglet error: requested font '%s' not found.\n", e.name), 1
			case figletError:
				fmt.Fprintln(os.Stderr, "pyfiglet.FigletError:", e.msg)
				out, code = "", 1
			default:
				panic(r)
			}
		}
	}()
	font := loadFont(o.font)

	direction := o.direction
	if direction == "auto" {
		if font.printDirection == 1 {
			direction = "right-to-left"
		} else {
			direction = "left-to-right"
		}
	}
	justify := o.justify
	if justify == "auto" {
		if direction == "left-to-right" {
			justify = "left"
		} else {
			justify = "right"
		}
	}

	r := newBuilder(text, font, direction, o.width, justify).render()
	if o.reverse {
		r = reverseText(r)
	}
	if o.flip {
		r = flipText(r)
	}
	if o.strip {
		r = stripSurroundingNewlines(r)
	} else if o.normalize {
		r = "\n" + stripSurroundingNewlines(r) + "\n"
	}
	return r + "\n", 0
}

func main() {
	o, args := parseArgs(os.Args[1:])
	if len(args) == 0 {
		fmt.Println("Usage: figlet [options] [text..]")
		os.Exit(1)
	}
	out, code := run(o, strings.Join(args, " "))
	if out != "" {
		os.Stdout.WriteString(out)
	}
	os.Exit(code)
}
