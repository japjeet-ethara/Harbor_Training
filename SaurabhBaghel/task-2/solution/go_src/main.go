// Pure-Go port of pyfiglet (commit 255827efbc09d662875dad50fa0edc1e1263bf45).
//
// This is a line-by-line port of FigletFont, FigletBuilder and FigletString
// from pyfiglet/__init__.py. Strings are handled as []rune so that indexing
// and lengths match Python's code-point semantics. Where pyfiglet would raise
// an exception, this program exits with a non-zero status.
//
// Standard library only.
package main

import (
	"embed"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"
	"unicode"
)

//go:embed pyfiglet/fonts
var fontsFS embed.FS

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

// noChar stands for Python's empty string '' where a single character is expected.
const noChar rune = -1

// pyError mirrors a Python exception escaping pyfiglet.main().
type pyError struct{ msg string }

func raise(format string, a ...any) { panic(pyError{fmt.Sprintf(format, a...)}) }

// ─── Python string helpers ─────────────────────────────────────────────────

// pyIsSpace matches Python's str.isspace() for a single character.
func pyIsSpace(r rune) bool {
	if r >= 0x1c && r <= 0x1f {
		return true
	}
	return unicode.IsSpace(r)
}

// pySplitlines mirrors str.splitlines() (without keepends).
func pySplitlines(s []rune) [][]rune {
	var out [][]rune
	start := 0
	i := 0
	for i < len(s) {
		c := s[i]
		switch c {
		case '\n', '\r', '\v', '\f', 0x1c, 0x1d, 0x1e, 0x85, 0x2028, 0x2029:
			out = append(out, s[start:i])
			if c == '\r' && i+1 < len(s) && s[i+1] == '\n' {
				i++
			}
			i++
			start = i
		default:
			i++
		}
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}

func pyStrip(s []rune) []rune  { return pyRStrip(pyLStrip(s)) }
func pyLStrip(s []rune) []rune {
	i := 0
	for i < len(s) && pyIsSpace(s[i]) {
		i++
	}
	return s[i:]
}
func pyRStrip(s []rune) []rune {
	j := len(s)
	for j > 0 && pyIsSpace(s[j-1]) {
		j--
	}
	return s[:j]
}

// pyFields mirrors str.split() with no arguments.
func pyFields(s []rune) []string {
	var out []string
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
			out = append(out, string(s[i:j]))
		}
		i = j
	}
	return out
}

func pyInt(s string) int {
	n, err := strconv.Atoi(strings.TrimSpace(s))
	if err != nil {
		raise("invalid literal for int(): %q", s)
	}
	return n
}

// in mirrors Python's `ch in s` for a one-character (or empty) string ch.
func in(ch rune, s string) bool {
	if ch == noChar {
		return true
	}
	return strings.ContainsRune(s, ch)
}

func runeEq(s []rune, t string) bool { return string(s) == t }

// ─── FigletFont ────────────────────────────────────────────────────────────

type FigletFont struct {
	hardBlank      string
	hardBlankRune  rune // noChar-like sentinel when hardBlank is not one character
	height         int
	printDirection int // -1 when absent (None)
	smushMode      int
	chars          map[rune][][]rune
	width          map[rune]int
}

func preloadFont(name string) []rune {
	for _, ext := range []string{"tlf", "flf"} {
		data, err := fontsFS.ReadFile("pyfiglet/fonts/" + name + "." + ext)
		if err == nil && len(data) > 0 {
			return []rune(string(data)) // invalid UTF-8 -> U+FFFD, like decode('replace')
		}
	}
	return nil
}

// endMarkerChar mirrors reEndMarker.search(line).group(1) with r'(.)\s*$'.
func endMarkerChar(line []rune) rune {
	for i := 0; i < len(line); i++ {
		if line[i] == '\n' {
			continue
		}
		ok := true
		for _, c := range line[i+1:] {
			if !pyIsSpace(c) {
				ok = false
				break
			}
		}
		if ok {
			return line[i]
		}
	}
	raise("'NoneType' object has no attribute 'group'")
	return 0
}

// stripEndMarker mirrors re.sub(re.escape(end) + r'{1,2}\s*$', '', line).
func stripEndMarker(line []rune, end rune) []rune {
	for i := 0; i < len(line); i++ {
		if line[i] != end {
			continue
		}
		for _, n := range []int{2, 1} { // greedy {1,2}
			if i+n > len(line) {
				continue
			}
			match := true
			for k := 0; k < n; k++ {
				if line[i+k] != end {
					match = false
				}
			}
			if !match {
				continue
			}
			rest := true
			for _, c := range line[i+n:] {
				if !pyIsSpace(c) {
					rest = false
					break
				}
			}
			if rest {
				return line[:i]
			}
		}
	}
	return line
}

func loadFont(name string) (*FigletFont, bool) {
	raw := preloadFont(name)
	if raw == nil {
		return nil, false
	}
	for i, r := range raw {
		if r == 0x85 || r == 0x2028 || r == 0x2029 {
			raw[i] = ' '
		}
	}
	data := pySplitlines(raw)
	pop := func() []rune {
		if len(data) == 0 {
			raise("pop from empty list")
		}
		l := data[0]
		data = data[1:]
		return l
	}

	header := pop()
	if len(header) < 5 || !(header[0] == 't' || header[0] == 'f') ||
		header[1] != 'l' || header[2] != 'f' || header[3] != '2' || header[4] == '\n' {
		raise("%s is not a valid figlet font", name)
	}
	fields := pyFields(header[5:])
	if len(fields) < 6 {
		raise("malformed header for %s", name)
	}

	f := &FigletFont{
		hardBlank:      fields[0],
		hardBlankRune:  -2,
		height:         pyInt(fields[1]),
		printDirection: -1,
		chars:          map[rune][][]rune{},
		width:          map[rune]int{},
	}
	if hb := []rune(fields[0]); len(hb) == 1 {
		f.hardBlankRune = hb[0]
	}
	_ = pyInt(fields[2])
	_ = pyInt(fields[3])
	oldLayout := pyInt(fields[4])
	commentLines := pyInt(fields[5])
	fullLayout := -1
	if len(fields) > 6 {
		f.printDirection = pyInt(fields[6])
	}
	if len(fields) > 7 {
		fullLayout = pyInt(fields[7])
	}
	if fullLayout == -1 && len(fields) <= 7 {
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

	readChar := func() (int, [][]rune) {
		width := 0
		var end rune
		haveEnd := false
		rows := make([][]rune, 0, f.height)
		for k := 0; k < f.height; k++ {
			line := pop()
			if !haveEnd {
				end = endMarkerChar(line)
				haveEnd = true
			}
			line = stripEndMarker(line, end)
			if len(line) > width {
				width = len(line)
			}
			rows = append(rows, line)
		}
		return width, rows
	}
	empty := func(rows [][]rune) bool {
		for _, r := range rows {
			if len(r) > 0 {
				return false
			}
		}
		return true
	}

	for i := 32; i < 127; i++ {
		w, letter := readChar()
		if i == 32 || !empty(letter) {
			f.chars[rune(i)] = letter
			f.width[rune(i)] = w
		}
	}
	if len(data) > 0 {
		for _, r := range "ÄÖÜäöüß" {
			w, letter := readChar()
			if !empty(letter) {
				f.chars[r] = letter
				f.width[r] = w
			}
		}
	}
	for len(data) > 0 {
		line := pyStrip(pop())
		tag := string(line)
		if sp := strings.IndexByte(tag, ' '); sp >= 0 {
			tag = tag[:sp]
		}
		if tag == "" {
			continue
		}
		if len(tag) >= 2 && tag[0] == '0' && (tag[1] == 'x' || tag[1] == 'X') {
			v, err := strconv.ParseInt(tag[2:], 16, 64)
			if err != nil {
				raise("invalid literal for int() with base 16: %q", tag)
			}
			w, letter := readChar()
			if !empty(letter) {
				f.chars[rune(v)] = letter
				f.width[rune(v)] = w
			}
		}
	}
	return f, true
}

// ─── FigletBuilder ─────────────────────────────────────────────────────────

type blankMarker struct {
	buffer   [][]rune
	iterator int
}

type FigletBuilder struct {
	text      []rune
	direction string
	width     int
	font      *FigletFont
	justify   string

	iterator          int
	maxSmush          int
	curCharWidth      int
	prevCharWidth     int
	currentTotalWidth int

	blankMarkers []blankMarker
	product      [][][]rune
	buffer       [][]rune
}

func newBuilder(text string, font *FigletFont, direction string, width int, justify string) *FigletBuilder {
	return &FigletBuilder{
		text:      []rune(text),
		direction: direction,
		width:     width,
		font:      font,
		justify:   justify,
		buffer:    make([][]rune, font.height),
	}
}

func copyBuf(b [][]rune) [][]rune {
	out := make([][]rune, len(b))
	copy(out, b)
	return out
}

func (b *FigletBuilder) addCharToProduct() {
	curChar := b.getCurChar()

	if b.text[b.iterator] == '\n' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{copyBuf(b.buffer), b.iterator})
		b.handleNewLine()
		return
	}
	if curChar == nil {
		return
	}
	if b.width < b.getCurWidth() {
		raise("Width is not enough to print this character")
	}
	b.curCharWidth = b.getCurWidth()
	b.maxSmush = b.smushAmount(b.buffer, curChar)

	b.currentTotalWidth = len(b.buffer[0]) + b.curCharWidth - b.maxSmush

	if b.text[b.iterator] == ' ' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{copyBuf(b.buffer), b.iterator})
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

func (b *FigletBuilder) returnProduct() string {
	if len(b.buffer[0]) != 0 {
		b.product = append(b.product, b.buffer)
	}
	var sb strings.Builder
	for _, buf := range b.product {
		buf = b.justifyString(buf)
		sb.WriteString(b.replaceHardblanks(buf))
	}
	return sb.String()
}

func (b *FigletBuilder) getCharAt(i int) [][]rune {
	if i < 0 || i >= len(b.text) {
		return nil
	}
	return b.font.chars[b.text[i]]
}

func (b *FigletBuilder) getCurChar() [][]rune { return b.getCharAt(b.iterator) }
func (b *FigletBuilder) getCurWidth() int     { return b.font.width[b.text[b.iterator]] }

func (b *FigletBuilder) smushRow(curChar [][]rune, row int) ([]rune, []rune) {
	addLeft := b.buffer[row]
	addRight := curChar[row]
	if b.direction == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}
	addLeft = append([]rune(nil), addLeft...)

	for i := 0; i < b.maxSmush; i++ {
		// getLeftSmushedChar
		idx := len(addLeft) - b.maxSmush + i
		left := noChar
		if idx >= 0 && idx < len(addLeft) {
			left = addLeft[idx]
		}
		if i >= len(addRight) {
			raise("string index out of range")
		}
		right := addRight[i]
		smushed, ok := b.smushChars(left, right)

		// updateSmushedCharInLeftBuffer
		if idx < 0 || idx > len(addLeft) {
			continue
		}
		if idx == len(addLeft) {
			raise("list assignment index out of range")
		}
		if !ok {
			raise("sequence item: expected str instance, NoneType found")
		}
		if smushed == noChar {
			addLeft = append(addLeft[:idx:idx], addLeft[idx+1:]...)
		} else {
			addLeft[idx] = smushed
		}
	}
	return addLeft, addRight
}

func (b *FigletBuilder) addCurCharRowToBufferRow(curChar [][]rune, row int) {
	addLeft, addRight := b.smushRow(curChar, row)
	tail := []rune{}
	if b.maxSmush < len(addRight) {
		tail = addRight[b.maxSmush:]
	}
	nr := make([]rune, 0, len(addLeft)+len(tail))
	nr = append(nr, addLeft...)
	nr = append(nr, tail...)
	b.buffer[row] = nr
}

func (b *FigletBuilder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([][]rune, b.font.height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	curChar := b.getCurChar()
	if curChar == nil {
		return
	}
	b.maxSmush = b.smushAmount(b.buffer, curChar)
}

func (b *FigletBuilder) handleNewLine() {
	if n := len(b.blankMarkers); n > 0 {
		m := b.blankMarkers[n-1]
		b.blankMarkers = b.blankMarkers[:n-1]
		// cutBufferAtLastBlank
		b.product = append(b.product, m.buffer)
		b.iterator = m.iterator
		b.cutBufferCommon()
		return
	}
	// cutBufferAtLastChar
	b.product = append(b.product, b.buffer)
	b.iterator--
	b.cutBufferCommon()
}

func (b *FigletBuilder) justifyString(buffer [][]rune) [][]rune {
	out := copyBuf(buffer)
	switch b.justify {
	case "right":
		for row := 0; row < b.font.height; row++ {
			pad := b.width - len(out[row]) - 1
			out[row] = append([]rune(spaces(pad)), out[row]...)
		}
	case "center":
		for row := 0; row < b.font.height; row++ {
			pad := (b.width - len(out[row])) / 2 // int() truncates toward zero, as Go does
			out[row] = append([]rune(spaces(pad)), out[row]...)
		}
	}
	return out
}

func spaces(n int) string {
	if n <= 0 {
		return ""
	}
	return strings.Repeat(" ", n)
}

func (b *FigletBuilder) replaceHardblanks(buffer [][]rune) string {
	rows := make([]string, len(buffer))
	for i, r := range buffer {
		rows[i] = string(r)
	}
	s := strings.Join(rows, "\n") + "\n"
	return strings.ReplaceAll(s, b.font.hardBlank, " ")
}

func (b *FigletBuilder) smushAmount(buffer, curChar [][]rune) int {
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

		linebd := len(trimRightSpace(lineLeft)) - 1
		if linebd < 0 {
			linebd = 0
		}
		ch1 := noChar
		if linebd < len(lineLeft) {
			ch1 = lineLeft[linebd]
		} else {
			linebd = 0
		}

		charbd := len(lineRight) - len(trimLeftSpace(lineRight))
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

func trimRightSpace(s []rune) []rune {
	j := len(s)
	for j > 0 && s[j-1] == ' ' {
		j--
	}
	return s[:j]
}

func trimLeftSpace(s []rune) []rune {
	i := 0
	for i < len(s) && s[i] == ' ' {
		i++
	}
	return s[i:]
}

// smushChars returns (result, true), or (_, false) for Python's None.
// A result of noChar stands for Python's ''.
func (b *FigletBuilder) smushChars(left, right rune) (rune, bool) {
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

	type pairRule struct{ a, b string }
	var smushes []pairRule
	if mode&smLowline != 0 {
		smushes = append(smushes, pairRule{"_", `|/\[]{}()<>`})
	}
	if mode&smHierarchy != 0 {
		smushes = append(smushes,
			pairRule{"|", `/\[]{}()<>`},
			pairRule{`\/`, `[]{}()<>`},
			pairRule{"[]", `{}()<>`},
			pairRule{"{}", `()<>`},
			pairRule{"()", `<>`},
		)
	}
	for _, s := range smushes {
		if in(left, s.a) && in(right, s.b) {
			return right, true
		}
		if in(right, s.a) && in(left, s.b) {
			return left, true
		}
	}

	if mode&smPair != 0 {
		for _, p := range [][2]rune{{left, right}, {right, left}} {
			pair := pairString(p[0], p[1])
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

func pairString(a, b rune) string {
	var sb strings.Builder
	if a != noChar {
		sb.WriteRune(a)
	}
	if b != noChar {
		sb.WriteRune(b)
	}
	return sb.String()
}

// ─── FigletString ──────────────────────────────────────────────────────────

const reverseMap = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f" +
	"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f" +
	" !\"#$%&')(*+,-.\\" +
	"0123456789:;>=<?" +
	"@ABCDEFGHIJKLMNO" +
	"PQRSTUVWXYZ]/[^_" +
	"`abcdefghijklmno" +
	"pqrstuvwxyz}|{~\x7f"

const flipMap = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f" +
	"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f" +
	" !\"#$%&'()*+,-.\\" +
	"0123456789:;<=>?" +
	"@VBCDEFGHIJKLWNO" +
	"bQbSTUAMXYZ[/]v-" +
	"`aPcdefghijklwno" +
	"pqrstu^mxyz{|}~\x7f"

// translate mirrors str.translate with pyfiglet's 256-entry tables; entries
// 128-255 are identity, and characters >= 256 are left unchanged.
func translate(row []rune, table string) []rune {
	out := make([]rune, len(row))
	for i, c := range row {
		if c >= 0 && c < 128 {
			out[i] = rune(table[c])
		} else {
			out[i] = c
		}
	}
	return out
}

func newFromList(rows [][]rune) string {
	parts := make([]string, len(rows))
	for i, r := range rows {
		parts[i] = string(r)
	}
	return strings.Join(parts, "\n") + "\n"
}

func reverseString(s string) string {
	var out [][]rune
	for _, row := range pySplitlines([]rune(s)) {
		t := translate(row, reverseMap)
		for i, j := 0, len(t)-1; i < j; i, j = i+1, j-1 {
			t[i], t[j] = t[j], t[i]
		}
		out = append(out, t)
	}
	return newFromList(out)
}

func flipString(s string) string {
	rows := pySplitlines([]rune(s))
	var out [][]rune
	for i := len(rows) - 1; i >= 0; i-- {
		out = append(out, translate(rows[i], flipMap))
	}
	return newFromList(out)
}

func stripSurroundingNewlines(s string) string {
	var out [][]rune
	charsSeen := false
	for _, row := range pySplitlines([]rune(s)) {
		if len(pyStrip(row)) != 0 || charsSeen {
			charsSeen = true
			out = append(out, row)
		}
	}
	return string(pyRStrip([]rune(newFromList(out))))
}

func normalizeSurroundingNewlines(s string) string {
	return "\n" + stripSurroundingNewlines(s) + "\n"
}

// ─── main ──────────────────────────────────────────────────────────────────

type choiceFlag struct {
	value   string
	choices []string
}

func (c *choiceFlag) String() string { return c.value }
func (c *choiceFlag) Set(v string) error {
	for _, ch := range c.choices {
		if v == ch {
			c.value = v
			return nil
		}
	}
	return fmt.Errorf("invalid choice: %q (choose from %s)", v, strings.Join(c.choices, ", "))
}

func main() {
	os.Exit(run())
}

func run() (code int) {
	defer func() {
		if r := recover(); r != nil {
			if e, ok := r.(pyError); ok {
				fmt.Fprintln(os.Stderr, "figlet error:", e.msg)
				code = 1
				return
			}
			panic(r)
		}
	}()

	fs := flag.NewFlagSet("figlet", flag.ContinueOnError)
	font := fs.String("f", "standard", "font to render with")
	direction := &choiceFlag{"auto", []string{"auto", "left-to-right", "right-to-left"}}
	fs.Var(direction, "D", "direction: auto, left-to-right, right-to-left")
	justify := &choiceFlag{"auto", []string{"auto", "left", "center", "right"}}
	fs.Var(justify, "j", "justify: auto, left, center, right")
	width := fs.Int("w", 80, "terminal width for wrapping/justification")
	reverse := fs.Bool("r", false, "mirror image of output text")
	normalize := fs.Bool("n", false, "one empty line before and after")
	strip := fs.Bool("s", false, "remove empty leading and trailing lines")
	flip := fs.Bool("F", false, "flip rendered output text over")
	if err := fs.Parse(os.Args[1:]); err != nil {
		return 2
	}
	args := fs.Args()
	if len(args) == 0 {
		fs.Usage()
		return 1
	}
	text := strings.Join(args, " ")

	f, ok := loadFont(*font)
	if !ok {
		fmt.Printf("pyfiglet error: requested font '%s' not found.\n", *font)
		return 1
	}

	dir := direction.value
	if dir == "auto" {
		if f.printDirection == 1 {
			dir = "right-to-left"
		} else {
			dir = "left-to-right"
		}
	}
	jus := justify.value
	if jus == "auto" {
		if dir == "right-to-left" {
			jus = "right"
		} else {
			jus = "left"
		}
	}

	b := newBuilder(text, f, dir, *width, jus)
	for b.iterator < len(b.text) {
		b.addCharToProduct()
		b.iterator++
	}
	r := b.returnProduct()

	if *reverse {
		r = reverseString(r)
	}
	if *flip {
		r = flipString(r)
	}
	if *strip {
		r = stripSurroundingNewlines(r)
	} else if *normalize {
		r = normalizeSurroundingNewlines(r)
	}

	os.Stdout.WriteString(r)
	os.Stdout.WriteString("\n")
	return 0
}
