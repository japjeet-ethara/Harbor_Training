package main

// Port of class FigletBuilder (the rendering engine) and of class FigletString.
// The rules are ported one by one, in the order of the Python code; none is invented here.

import "strings"

// constants.. lifted from figlet222
const (
	smEqual     = 1   // smush equal chars (not hardblanks)
	smLowline   = 2   // smush _ with any char in hierarchy
	smHierarchy = 4   // hierarchy: |, /\, [], {}, (), <>
	smPair      = 8   // [ + ] -> |, { + } -> |, ( + ) -> |
	smBigX      = 16  // / + \ -> |, \ + / -> Y, > + < -> X
	smHardblank = 32  // hardblank + hardblank -> hardblank
	smKern      = 64  // kerning: letters move together until they touch
	smSmush     = 128 // smushing: letters may share one column
)

const rightToLeft = "right-to-left"

type blankMarker struct {
	buffer   [][]rune
	iterator int
}

type figletBuilder struct {
	text      []rune
	direction string
	width     int
	font      *figletFont
	justify   string

	iterator          int
	maxSmush          int
	curCharWidth      int
	prevCharWidth     int
	currentTotalWidth int

	blankMarkers []blankMarker
	queue        [][][]rune // FigletProduct.queue
	buffer       [][]rune
}

func newBuilder(text string, font *figletFont, direction string, width int, justify string) *figletBuilder {
	return &figletBuilder{text: []rune(text), direction: direction, width: width, font: font, justify: justify,
		buffer: make([][]rune, font.height)}
}

// render is FigletRenderingEngine.render.
func render(text string, font *figletFont, direction string, width int, justify string) string {
	b := newBuilder(text, font, direction, width, justify)
	steps, limit := 0, 100*len(b.text)+1000
	for b.iterator < len(b.text) { // while builder.isNotFinished()
		b.addCharToProduct()
		b.iterator++ // goToNextChar
		if steps++; steps > limit {
			raise("the original never finishes on this input") // a character exactly as wide as the window
		}
	}
	return b.returnProduct()
}

func copyBuffer(buffer [][]rune) [][]rune {
	c := make([][]rune, len(buffer))
	copy(c, buffer) // the rows themselves are never changed in place
	return c
}

func (b *figletBuilder) addCharToProduct() {
	c := b.text[b.iterator]
	curChar, known := b.font.chars[c]

	// if the character is a newline, we flush the buffer
	if c == '\n' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{copyBuffer(b.buffer), b.iterator})
		b.handleNewLine()
		return
	}
	if !known {
		return
	}
	if b.width < b.font.width[c] {
		raise("Width is not enough to print this character")
	}
	b.curCharWidth = b.font.width[c]
	b.maxSmush = b.smushAmount(b.buffer, curChar)

	b.currentTotalWidth = len(b.buffer[0]) + b.curCharWidth - b.maxSmush

	if c == ' ' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{copyBuffer(b.buffer), b.iterator})
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

func (b *figletBuilder) returnProduct() string {
	if len(b.buffer[0]) != 0 {
		b.queue = append(b.queue, b.buffer) // flushLastBuffer
	}
	// formatProduct
	var acc strings.Builder
	for _, buffer := range b.queue {
		buffer = b.justifyString(buffer)
		acc.WriteString(b.replaceHardblanks(buffer))
	}
	return acc.String()
}

// smushRow returns the left and the right part of one row after the overlapping columns were merged.
func (b *figletBuilder) smushRow(curChar [][]rune, row int) (addLeft, addRight []rune) {
	addLeft, addRight = b.buffer[row], curChar[row]
	if b.direction == rightToLeft {
		addLeft, addRight = addRight, addLeft
	}
	for i := 0; i < b.maxSmush; i++ {
		idx := len(addLeft) - b.maxSmush + i // getLeftSmushedChar
		if i >= len(addRight) {
			raise("string index out of range")
		}
		if idx < 0 || idx >= len(addLeft) {
			continue // nothing on the left at this column: the original leaves the left part as it is
		}
		smushed, ok := b.smushChars(addLeft[idx], addRight[i])
		if !ok {
			raise("sequence item: expected str instance, NoneType found")
		}
		merged := make([]rune, len(addLeft)) // updateSmushedCharInLeftBuffer
		copy(merged, addLeft)
		merged[idx] = smushed
		addLeft = merged
	}
	return addLeft, addRight
}

func (b *figletBuilder) addCurCharRowToBufferRow(curChar [][]rune, row int) {
	addLeft, addRight := b.smushRow(curChar, row)
	joined := make([]rune, 0, len(addLeft)+len(addRight))
	joined = append(joined, addLeft...)
	if b.maxSmush < len(addRight) {
		joined = append(joined, addRight[b.maxSmush:]...)
	}
	b.buffer[row] = joined
}

func (b *figletBuilder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([][]rune, b.font.height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	if b.iterator < 0 || b.iterator >= len(b.text) {
		return
	}
	curChar, known := b.font.chars[b.text[b.iterator]]
	if !known {
		return
	}
	b.maxSmush = b.smushAmount(b.buffer, curChar)
}

func (b *figletBuilder) handleNewLine() {
	if n := len(b.blankMarkers); n > 0 { // cutBufferAtLastBlank
		last := b.blankMarkers[n-1]
		b.blankMarkers = b.blankMarkers[:n-1]
		b.queue = append(b.queue, last.buffer)
		b.iterator = last.iterator
		b.cutBufferCommon()
	} else { // cutBufferAtLastChar
		b.queue = append(b.queue, b.buffer)
		b.iterator--
		b.cutBufferCommon()
	}
}

func (b *figletBuilder) justifyString(buffer [][]rune) [][]rune {
	pad := func(row []rune, n int) []rune {
		if n <= 0 {
			return row
		}
		return append([]rune(strings.Repeat(" ", n)), row...)
	}
	switch b.justify {
	case "right":
		for row := 0; row < b.font.height; row++ {
			buffer[row] = pad(buffer[row], b.width-len(buffer[row])-1)
		}
	case "center":
		for row := 0; row < b.font.height; row++ {
			buffer[row] = pad(buffer[row], (b.width-len(buffer[row]))/2) // int(x / 2) rounds towards zero, as Go does
		}
	}
	return buffer
}

func (b *figletBuilder) replaceHardblanks(buffer [][]rune) string {
	rows := make([]string, len(buffer))
	for i, r := range buffer {
		rows[i] = string(r)
	}
	s := strings.Join(rows, "\n") + "\n"
	return strings.ReplaceAll(s, b.font.hardBlank, " ")
}

func rstripSpaces(rs []rune) int { // len(line.rstrip(' '))
	n := len(rs)
	for n > 0 && rs[n-1] == ' ' {
		n--
	}
	return n
}

// smushAmount: how many columns the next character may move into the line so far.
func (b *figletBuilder) smushAmount(buffer [][]rune, curChar [][]rune) int {
	if b.font.smushMode&(smSmush|smKern) == 0 {
		return 0
	}
	maxSmush := b.curCharWidth
	for row := 0; row < b.font.height; row++ {
		lineLeft, lineRight := buffer[row], curChar[row]
		if b.direction == rightToLeft {
			lineLeft, lineRight = lineRight, lineLeft
		}

		// Only strip ascii space to match figlet exactly.
		linebd := rstripSpaces(lineLeft) - 1
		if linebd < 0 {
			linebd = 0
		}
		var ch1 rune
		ch1Empty := false
		if linebd < len(lineLeft) {
			ch1 = lineLeft[linebd]
		} else {
			linebd = 0
			ch1Empty = true
		}

		charbd := 0 // len(lineRight) - len(lineRight.lstrip(' '))
		for charbd < len(lineRight) && lineRight[charbd] == ' ' {
			charbd++
		}
		var ch2 rune
		ch2Empty := false
		if charbd < len(lineRight) {
			ch2 = lineRight[charbd]
		} else {
			charbd = len(lineRight)
			ch2Empty = true
		}

		amt := charbd + len(lineLeft) - 1 - linebd

		if ch1Empty || ch1 == ' ' {
			amt++
		} else if !ch2Empty {
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

// smushChars: the character two touching characters become, and false when they may not share a column.
func (b *figletBuilder) smushChars(left, right rune) (rune, bool) {
	mode := b.font.smushMode
	hard := func(r rune) bool { return string(r) == b.font.hardBlank }

	if left == ' ' {
		return right, true
	}
	if right == ' ' {
		return left, true
	}

	// Disallows overlapping if previous or current char has a width of 1 or zero
	if b.prevCharWidth < 2 || b.curCharWidth < 2 {
		return 0, false
	}

	// kerning only
	if mode&smSmush == 0 {
		return 0, false
	}

	// smushing by universal overlapping
	if mode&63 == 0 {
		// Ensure preference to visible characters.
		if hard(left) {
			return right, true
		}
		if hard(right) {
			return left, true
		}
		// The dominant character is the later one in the user's text.
		if b.direction == rightToLeft {
			return left, true
		}
		return right, true
	}

	if mode&smHardblank != 0 && hard(left) && hard(right) {
		return left, true
	}
	if hard(left) || hard(right) {
		return 0, false
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
			smushPair{"()", "<>"})
	}
	for _, s := range smushes {
		if strings.ContainsRune(s.a, left) && strings.ContainsRune(s.b, right) {
			return right, true
		}
		if strings.ContainsRune(s.a, right) && strings.ContainsRune(s.b, left) {
			return left, true
		}
	}

	if mode&smPair != 0 {
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

// ---- class FigletString ----

// translation map for reversing ascii art: ( <-> ), / <-> \, < <-> >, [ <-> ], { <-> }
var reverseMap = map[rune]rune{
	'(': ')', ')': '(', '/': '\\', '\\': '/', '<': '>', '>': '<', '[': ']', ']': '[', '{': '}', '}': '{',
}

// translation map for flipping ascii art, copied from __flip_map__ (it is not symmetric)
var flipMap = map[rune]rune{
	'/': '\\', '\\': '/', 'A': 'V', 'V': 'A', 'M': 'W', 'W': 'M', 'P': 'b', 'R': 'b', 'b': 'P',
	'^': 'v', 'v': '^', '_': '-', 'm': 'w', 'w': 'm',
}

func newFromList(rows []string) string { return strings.Join(rows, "\n") + "\n" }

func figletReverse(s string) string {
	rows := splitLines(s)
	out := make([]string, len(rows))
	for i, row := range rows {
		out[i] = reverseRunes(translate(row, reverseMap))
	}
	return newFromList(out)
}

func figletFlip(s string) string {
	rows := splitLines(s)
	out := make([]string, 0, len(rows))
	for i := len(rows) - 1; i >= 0; i-- {
		out = append(out, translate(rows[i], flipMap))
	}
	return newFromList(out)
}

// stripSurroundingNewlines drops empty leading rows, keeps everything after the first row with
// something in it, and then removes all whitespace from the end of the whole text.
func stripSurroundingNewlines(s string) string {
	var out []string
	charsSeen := false
	for _, row := range splitLines(s) {
		if strip(row) != "" || charsSeen {
			charsSeen = true
			out = append(out, row)
		}
	}
	return rstrip(newFromList(out))
}

func normalizeSurroundingNewlines(s string) string {
	return "\n" + stripSurroundingNewlines(s) + "\n"
}
