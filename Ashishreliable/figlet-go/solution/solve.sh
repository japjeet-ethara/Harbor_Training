#!/bin/bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/workspace/repo}"
cd "$REPO_DIR"

# Keep the eight fonts we render with inside the repository, next to the
# program, and embed them at build time.
mkdir -p fonts
for font in standard slant small big mini banner shadow script; do
    cp "pyfiglet/fonts/${font}.flf" "fonts/${font}.flf"
done

cat > go.mod <<'GOMOD'
module figlet

go 1.23
GOMOD

cat > main.go <<'GO'
package main

import (
	"embed"
	"fmt"
	"os"
	"strconv"
	"strings"
	"unicode"
)

// The eight font families used by the task are embedded so the binary works
// from any working directory.
//
//go:embed fonts
var fontFS embed.FS

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

// Translation tables copied verbatim from pyfiglet's FigletString.
const reverseFirst128 = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x29\x28\x2a\x2b\x2c\x2d\x2e\x5c\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3e\x3d\x3c\x3f\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5d\x2f\x5b\x5e\x5f\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7d\x7c\x7b\x7e\x7f"

const flipFirst128 = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x5c\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x40\x56\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x57\x4e\x4f\x62\x51\x62\x53\x54\x55\x41\x4d\x58\x59\x5a\x5b\x2f\x5d\x76\x2d\x60\x61\x50\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x77\x6e\x6f\x70\x71\x72\x73\x74\x75\x5e\x6d\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f"

var reverseTable [256]rune
var flipTable [256]rune

func init() {
	for index, char := range []rune(reverseFirst128) {
		reverseTable[index] = char
	}
	for index, char := range []rune(flipFirst128) {
		flipTable[index] = char
	}
	for index := 0x80; index <= 0xff; index++ {
		reverseTable[index] = rune(index)
		flipTable[index] = rune(index)
	}
}

// ---------------------------------------------------------------------------
// Python-compatible helpers
// ---------------------------------------------------------------------------

func isLineBreak(char rune) bool {
	switch char {
	case '\n', '\r', '\v', '\f', '\x1c', '\x1d', '\x1e', '\u0085', '\u2028', '\u2029':
		return true
	}
	return false
}

// splitLines mirrors Python's str.splitlines().
func splitLines(text string) []string {
	chars := []rune(text)
	lines := make([]string, 0, 8)
	current := make([]rune, 0, 64)
	for index := 0; index < len(chars); index++ {
		char := chars[index]
		if isLineBreak(char) {
			lines = append(lines, string(current))
			current = current[:0]
			if char == '\r' && index+1 < len(chars) && chars[index+1] == '\n' {
				index++
			}
			continue
		}
		current = append(current, char)
	}
	if len(current) > 0 || (len(chars) > 0 && !isLineBreak(chars[len(chars)-1])) {
		lines = append(lines, string(current))
	}
	return lines
}

func trimRightSpaces(text string) string {
	chars := []rune(text)
	for len(chars) > 0 && chars[len(chars)-1] == ' ' {
		chars = chars[:len(chars)-1]
	}
	return string(chars)
}

func leadingSpaces(text string) int {
	count := 0
	for _, char := range text {
		if char != ' ' {
			break
		}
		count++
	}
	return count
}

func runeLen(text string) int {
	return len([]rune(text))
}

func sliceFrom(text string, start int) string {
	chars := []rune(text)
	if start <= 0 {
		return string(chars)
	}
	if start >= len(chars) {
		return ""
	}
	return string(chars[start:])
}

func copyRows(rows []string) []string {
	return append([]string(nil), rows...)
}

// ---------------------------------------------------------------------------
// Font parsing (port of FigletFont)
// ---------------------------------------------------------------------------

type font struct {
	hardBlank      rune
	height         int
	printDirection int
	smushMode      int
	chars          map[rune][]string
	widths         map[rune]int
}

func endMarker(line string) (rune, error) {
	chars := []rune(line)
	if len(chars) == 0 {
		return 0, fmt.Errorf("empty font line")
	}
	last := -1
	for index := len(chars) - 1; index >= 0; index-- {
		if !unicode.IsSpace(chars[index]) {
			last = index
			break
		}
	}
	if last == -1 {
		return chars[0], nil
	}
	return chars[last], nil
}

// stripEndMarker is the equivalent of re.sub(re.escape(end)+r"{1,2}\s*$", "", line).
func stripEndMarker(line string, end rune) string {
	chars := []rune(line)
	for len(chars) > 0 && unicode.IsSpace(chars[len(chars)-1]) {
		chars = chars[:len(chars)-1]
	}
	for count := 0; count < 2 && len(chars) > 0 && chars[len(chars)-1] == end; count++ {
		chars = chars[:len(chars)-1]
	}
	return string(chars)
}

func atoiField(fields []string, index int) (int, error) {
	if index >= len(fields) {
		return 0, fmt.Errorf("missing font header field %d", index)
	}
	value, err := strconv.Atoi(fields[index])
	if err != nil {
		return 0, fmt.Errorf("bad font header field %d: %w", index, err)
	}
	return value, nil
}

func loadFont(name string) (*font, error) {
	data, err := fontFS.ReadFile("fonts/" + name + ".flf")
	if err != nil {
		return nil, fmt.Errorf("font %q not found", name)
	}

	text := strings.Map(func(char rune) rune {
		if char == '\u0085' || char == '\u2028' || char == '\u2029' {
			return ' '
		}
		return char
	}, string(data))

	lines := splitLines(text)
	if len(lines) == 0 {
		return nil, fmt.Errorf("empty font %q", name)
	}

	header := lines[0]
	lines = lines[1:]
	if len(header) < 5 || (header[0] != 'f' && header[0] != 't') || header[1:4] != "lf2" {
		return nil, fmt.Errorf("%q is not a valid figlet font", name)
	}
	header = header[5:]

	fields := strings.Fields(header)
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed header for %q", name)
	}

	hardBlankRunes := []rune(fields[0])
	if len(hardBlankRunes) == 0 {
		return nil, fmt.Errorf("empty hardblank for %q", name)
	}
	hardBlank := hardBlankRunes[0]

	height, err := atoiField(fields, 1)
	if err != nil {
		return nil, err
	}
	oldLayout, err := atoiField(fields, 3)
	if err != nil {
		return nil, err
	}
	commentLines, err := atoiField(fields, 5)
	if err != nil {
		return nil, err
	}

	printDirection := -1
	if len(fields) > 6 {
		if printDirection, err = atoiField(fields, 6); err != nil {
			return nil, err
		}
	}

	fullLayout := 0
	hasFullLayout := false
	if len(fields) > 7 {
		if fullLayout, err = atoiField(fields, 7); err != nil {
			return nil, err
		}
		hasFullLayout = true
	}
	if !hasFullLayout {
		if oldLayout == 0 {
			fullLayout = 64
		} else if oldLayout < 0 {
			fullLayout = 0
		} else {
			fullLayout = (oldLayout & 31) | 128
		}
	}

	for count := 0; count < commentLines; count++ {
		if len(lines) == 0 {
			return nil, fmt.Errorf("font %q ended in comments", name)
		}
		lines = lines[1:]
	}

	nextChar := func() (int, []string, error) {
		var end rune
		haveEnd := false
		width := 0
		rows := make([]string, 0, height)
		for row := 0; row < height; row++ {
			if len(lines) == 0 {
				return 0, nil, fmt.Errorf("font %q ended early", name)
			}
			line := lines[0]
			lines = lines[1:]
			if !haveEnd {
				end, err = endMarker(line)
				if err != nil {
					return 0, nil, fmt.Errorf("font %q: %w", name, err)
				}
				haveEnd = true
			}
			line = stripEndMarker(line, end)
			if lineWidth := runeLen(line); lineWidth > width {
				width = lineWidth
			}
			rows = append(rows, line)
		}
		return width, rows, nil
	}

	result := &font{
		hardBlank:      hardBlank,
		height:         height,
		printDirection: printDirection,
		smushMode:      fullLayout,
		chars:          make(map[rune][]string),
		widths:         make(map[rune]int),
	}

	for code := 32; code <= 126; code++ {
		width, rows, err := nextChar()
		if err != nil {
			return nil, err
		}
		if code == 32 || strings.Join(rows, "") != "" {
			result.chars[rune(code)] = rows
			result.widths[rune(code)] = width
		}
	}

	if len(lines) > 0 {
		for _, char := range []rune("ÄÖÜäöüß") {
			width, rows, err := nextChar()
			if err != nil {
				return nil, err
			}
			if strings.Join(rows, "") != "" {
				result.chars[char] = rows
				result.widths[char] = width
			}
		}
	}

	for len(lines) > 0 {
		line := strings.TrimSpace(lines[0])
		lines = lines[1:]
		token := line
		if space := strings.IndexByte(line, ' '); space >= 0 {
			token = line[:space]
		}
		if token == "" {
			continue
		}
		if len(token) >= 2 && token[0] == '0' && (token[1] == 'x' || token[1] == 'X') {
			code, err := strconv.ParseInt(token[2:], 16, 32)
			if err != nil {
				return nil, fmt.Errorf("font %q: bad code %q", name, token)
			}
			width, rows, err := nextChar()
			if err != nil {
				return nil, err
			}
			if strings.Join(rows, "") != "" {
				result.chars[rune(code)] = rows
				result.widths[rune(code)] = width
			}
		}
	}

	return result, nil
}

// ---------------------------------------------------------------------------
// Renderer (port of FigletBuilder)
// ---------------------------------------------------------------------------

type blankMarker struct {
	rows     []string
	iterator int
}

type builder struct {
	text              []rune
	font              *font
	direction         string
	width             int
	justify           string
	iterator          int
	maxSmush          int
	curCharWidth      int
	prevCharWidth     int
	currentTotalWidth int
	blankMarkers      []blankMarker
	queue             [][]string
	buffer            []string
}

func newBuilder(text string, f *font, direction string, width int, justify string) *builder {
	return &builder{
		text:      []rune(text),
		font:      f,
		direction: direction,
		width:     width,
		justify:   justify,
		buffer:    make([]string, f.height),
	}
}

func (b *builder) isNotFinished() bool {
	return b.iterator < len(b.text)
}

func (b *builder) goToNextChar() {
	b.iterator++
}

func (b *builder) getCharAt(index int) ([]string, bool) {
	if index < 0 || index >= len(b.text) {
		return nil, false
	}
	rows, ok := b.font.chars[b.text[index]]
	return rows, ok
}

func (b *builder) getCurChar() ([]string, bool) {
	return b.getCharAt(b.iterator)
}

func (b *builder) addCharToProduct() error {
	curChar, ok := b.getCurChar()
	current := b.text[b.iterator]

	if current == '\n' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{copyRows(b.buffer), b.iterator})
		b.handleNewLine()
		return nil
	}
	if !ok {
		return nil
	}

	currentWidth := b.font.widths[current]
	if b.width < currentWidth {
		return fmt.Errorf("width is not enough to print this character")
	}
	b.curCharWidth = currentWidth
	b.maxSmush = b.currentSmushAmount(curChar)
	b.currentTotalWidth = runeLen(b.buffer[0]) + b.curCharWidth - b.maxSmush

	if current == ' ' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{copyRows(b.buffer), b.iterator})
	}

	if b.currentTotalWidth >= b.width {
		b.handleNewLine()
	} else {
		for row := 0; row < b.font.height; row++ {
			addLeft, addRight := b.smushRow(curChar, row)
			b.buffer[row] = addLeft + sliceFrom(addRight, b.maxSmush)
		}
	}

	b.prevCharWidth = b.curCharWidth
	return nil
}

func (b *builder) getLastBlank() (blankMarker, bool) {
	if len(b.blankMarkers) == 0 {
		return blankMarker{}, false
	}
	marker := b.blankMarkers[len(b.blankMarkers)-1]
	b.blankMarkers = b.blankMarkers[:len(b.blankMarkers)-1]
	return marker, true
}

func (b *builder) handleNewLine() {
	marker, ok := b.getLastBlank()
	if ok {
		b.cutBufferAtLastBlank(marker.rows, marker.iterator)
	} else {
		b.cutBufferAtLastChar()
	}
}

func (b *builder) cutBufferAtLastBlank(saved []string, savedIterator int) {
	b.queue = append(b.queue, saved)
	b.iterator = savedIterator
	b.cutBufferCommon()
}

func (b *builder) cutBufferAtLastChar() {
	b.queue = append(b.queue, b.buffer)
	b.iterator--
	b.cutBufferCommon()
}

func (b *builder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([]string, b.font.height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	curChar, ok := b.getCurChar()
	if !ok {
		return
	}
	b.maxSmush = b.currentSmushAmount(curChar)
}

func (b *builder) currentSmushAmount(curChar []string) int {
	return b.smushAmount(b.buffer, curChar)
}

func (b *builder) smushAmount(buffer, curChar []string) int {
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

		leftChars := []rune(lineLeft)
		rightChars := []rune(lineRight)

		linebd := runeLen(trimRightSpaces(lineLeft)) - 1
		if linebd < 0 {
			linebd = 0
		}

		ch1 := ""
		if linebd < len(leftChars) {
			ch1 = string(leftChars[linebd])
		} else {
			linebd = 0
			ch1 = ""
		}

		charbd := leadingSpaces(lineRight)
		ch2 := ""
		if charbd < len(rightChars) {
			ch2 = string(rightChars[charbd])
		} else {
			charbd = len(rightChars)
			ch2 = ""
		}

		amount := charbd + len(leftChars) - 1 - linebd
		if ch1 == "" || ch1 == " " {
			amount++
		} else if ch2 != "" && b.smushChars(ch1, ch2) != nil {
			amount++
		}

		if amount < maxSmush {
			maxSmush = amount
		}
	}

	return maxSmush
}

func (b *builder) smushChars(left, right string) *string {
	if left == " " {
		return &right
	}
	if right == " " {
		return &left
	}

	if b.prevCharWidth < 2 || b.curCharWidth < 2 {
		return nil
	}

	if b.font.smushMode&smSmush == 0 {
		return nil
	}

	if b.font.smushMode&63 == 0 {
		if left == string(b.font.hardBlank) {
			return &right
		}
		if right == string(b.font.hardBlank) {
			return &left
		}
		if b.direction == "right-to-left" {
			return &left
		}
		return &right
	}

	if b.font.smushMode&smHardblank != 0 {
		if left == string(b.font.hardBlank) && right == string(b.font.hardBlank) {
			return &left
		}
	}

	if left == string(b.font.hardBlank) || right == string(b.font.hardBlank) {
		return nil
	}

	if b.font.smushMode&smEqual != 0 {
		if left == right {
			return &left
		}
	}

	type smushPair struct {
		first  string
		second string
	}
	var smushes []smushPair

	if b.font.smushMode&smLowline != 0 {
		smushes = append(smushes, smushPair{"_", "|/\\[]{}()<>"})
	}
	if b.font.smushMode&smHierarchy != 0 {
		smushes = append(smushes,
			smushPair{"|", "/\\[]{}()<>"},
			smushPair{"\\/", "[]{}()<>"},
			smushPair{"[]", "{}()<>"},
			smushPair{"{}", "()<>"},
			smushPair{"()", "<>"},
		)
	}

	for _, pair := range smushes {
		if strings.Contains(pair.first, left) && strings.Contains(pair.second, right) {
			return &right
		}
		if strings.Contains(pair.first, right) && strings.Contains(pair.second, left) {
			return &left
		}
	}

	if b.font.smushMode&smPair != 0 {
		for _, pair := range []string{left + right, right + left} {
			if pair == "[]" || pair == "{}" || pair == "()" {
				pipe := "|"
				return &pipe
			}
		}
	}

	if b.font.smushMode&smBigX != 0 {
		if left == "/" && right == "\\" {
			pipe := "|"
			return &pipe
		}
		if right == "/" && left == "\\" {
			y := "Y"
			return &y
		}
		if left == ">" && right == "<" {
			x := "X"
			return &x
		}
	}

	return nil
}

func (b *builder) smushRow(curChar []string, row int) (string, string) {
	addLeft := b.buffer[row]
	addRight := curChar[row]
	if b.direction == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}

	for index := 0; index < b.maxSmush; index++ {
		leftChars := []rune(addLeft)
		position := len(leftChars) - b.maxSmush + index

		left := ""
		if position >= 0 && position < len(leftChars) {
			left = string(leftChars[position])
		}

		right := ""
		rightChars := []rune(addRight)
		if index < len(rightChars) {
			right = string(rightChars[index])
		}

		smushed := b.smushChars(left, right)
		if position >= 0 && position < len(leftChars) {
			parts := make([]string, len(leftChars))
			for spot, char := range leftChars {
				if spot == position {
					if smushed == nil {
						parts[spot] = ""
					} else {
						parts[spot] = *smushed
					}
				} else {
					parts[spot] = string(char)
				}
			}
			addLeft = strings.Join(parts, "")
		}
	}

	return addLeft, addRight
}

func (b *builder) justifyString(justify string, buffer []string) []string {
	for row := 0; row < b.font.height; row++ {
		width := b.width
		switch justify {
		case "right":
			padding := width - runeLen(buffer[row]) - 1
			if padding > 0 {
				buffer[row] = strings.Repeat(" ", padding) + buffer[row]
			}
		case "center":
			padding := (width - runeLen(buffer[row])) / 2
			if padding > 0 {
				buffer[row] = strings.Repeat(" ", padding) + buffer[row]
			}
		}
	}
	return buffer
}

func (b *builder) replaceHardblanks(buffer []string) string {
	text := strings.Join(buffer, "\n") + "\n"
	return strings.ReplaceAll(text, string(b.font.hardBlank), " ")
}

func (b *builder) returnProduct() string {
	if b.buffer[0] != "" {
		b.queue = append(b.queue, b.buffer)
	}

	var output strings.Builder
	for _, buffer := range b.queue {
		buffer = b.justifyString(b.justify, buffer)
		output.WriteString(b.replaceHardblanks(buffer))
	}
	return output.String()
}

func render(text string, f *font, direction string, justify string, width int) (string, error) {
	b := newBuilder(text, f, direction, width, justify)
	for b.isNotFinished() {
		if err := b.addCharToProduct(); err != nil {
			return "", err
		}
		b.goToNextChar()
	}
	return b.returnProduct(), nil
}

// ---------------------------------------------------------------------------
// FigletString transforms
// ---------------------------------------------------------------------------

func translate(text string, table *[256]rune) string {
	var output strings.Builder
	for _, char := range text {
		if char < 256 {
			char = table[char]
		}
		output.WriteRune(char)
	}
	return output.String()
}

func reverseRunes(text string) string {
	chars := []rune(text)
	for left, right := 0, len(chars)-1; left < right; left, right = left+1, right-1 {
		chars[left], chars[right] = chars[right], chars[left]
	}
	return string(chars)
}

func newFromList(rows []string) string {
	return strings.Join(rows, "\n") + "\n"
}

func reverseOutput(text string) string {
	rows := splitLines(text)
	output := make([]string, 0, len(rows))
	for _, row := range rows {
		output = append(output, reverseRunes(translate(row, &reverseTable)))
	}
	return newFromList(output)
}

func flipOutput(text string) string {
	rows := splitLines(text)
	output := make([]string, 0, len(rows))
	for index := len(rows) - 1; index >= 0; index-- {
		output = append(output, translate(rows[index], &flipTable))
	}
	return newFromList(output)
}

func stripSurroundingNewlines(text string) string {
	rows := splitLines(text)
	output := make([]string, 0, len(rows))
	seen := false
	for _, row := range rows {
		if strings.TrimSpace(row) != "" || seen {
			seen = true
			output = append(output, row)
		}
	}
	return strings.TrimRightFunc(newFromList(output), unicode.IsSpace)
}

// ---------------------------------------------------------------------------
// Command line
// ---------------------------------------------------------------------------

type options struct {
	font      string
	width     int
	justify   string
	direction string
	reverse   bool
	flip      bool
	strip     bool
	normalize bool
	text      []string
}

func parseOptions(args []string) (options, bool) {
	result := options{
		font:      "standard",
		width:     80,
		justify:   "auto",
		direction: "auto",
	}

	next := func(index *int) (string, bool) {
		if *index+1 >= len(args) {
			return "", false
		}
		*index = *index + 1
		return args[*index], true
	}

	for index := 0; index < len(args); index++ {
		arg := args[index]
		switch arg {
		case "-f", "--font":
			value, ok := next(&index)
			if !ok {
				return result, false
			}
			result.font = value
		case "-w", "--width":
			value, ok := next(&index)
			if !ok {
				return result, false
			}
			width, err := strconv.Atoi(value)
			if err != nil {
				return result, false
			}
			result.width = width
		case "-j", "--justify":
			value, ok := next(&index)
			if !ok {
				return result, false
			}
			result.justify = value
		case "-D", "--direction":
			value, ok := next(&index)
			if !ok {
				return result, false
			}
			result.direction = value
		case "-r", "--reverse":
			result.reverse = true
		case "-F", "--flip":
			result.flip = true
		case "-s", "--strip-surrounding-newlines":
			result.strip = true
		case "-n", "--normalize-surrounding-newlines":
			result.normalize = true
		default:
			if strings.HasPrefix(arg, "--font=") {
				result.font = strings.TrimPrefix(arg, "--font=")
			} else if strings.HasPrefix(arg, "--width=") {
				width, err := strconv.Atoi(strings.TrimPrefix(arg, "--width="))
				if err != nil {
					return result, false
				}
				result.width = width
			} else if strings.HasPrefix(arg, "--justify=") {
				result.justify = strings.TrimPrefix(arg, "--justify=")
			} else if strings.HasPrefix(arg, "--direction=") {
				result.direction = strings.TrimPrefix(arg, "--direction=")
			} else {
				result.text = append(result.text, arg)
			}
		}
	}

	return result, true
}

func main() {
	opts, ok := parseOptions(os.Args[1:])
	if !ok || len(opts.text) == 0 {
		os.Exit(1)
	}

	f, err := loadFont(opts.font)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: %v\n", err)
		os.Exit(1)
	}

	direction := opts.direction
	if direction == "auto" {
		if f.printDirection == 1 {
			direction = "right-to-left"
		} else {
			direction = "left-to-right"
		}
	}

	justify := opts.justify
	if justify == "auto" {
		if direction == "left-to-right" {
			justify = "left"
		} else {
			justify = "right"
		}
	}

	rendered, err := render(strings.Join(opts.text, " "), f, direction, justify, opts.width)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: %v\n", err)
		os.Exit(1)
	}

	if opts.reverse {
		rendered = reverseOutput(rendered)
	}
	if opts.flip {
		rendered = flipOutput(rendered)
	}
	if opts.strip {
		rendered = stripSurroundingNewlines(rendered)
	} else if opts.normalize {
		rendered = "\n" + stripSurroundingNewlines(rendered) + "\n"
	}

	fmt.Print(rendered)
	fmt.Print("\n")
}
GO

# The finished repository must contain no Python at all.
find . -name '*.py' -delete
find . -type d -name '__pycache__' -prune -exec rm -rf {} +

go build ./...
