#!/usr/bin/env bash
set -euo pipefail

# STEP A — Copy the fonts
mkdir -p /workspace/repo/fonts
cp /workspace/repo/pyfiglet/fonts/*.flf /workspace/repo/fonts/

# STEP B — Delete every .py file under /workspace/repo
find /workspace/repo -name "*.py" -delete

# STEP C — Write go.mod
cat << 'EOF' > /workspace/repo/go.mod
module figlet

go 1.23
EOF

# STEP D — Write the Go implementation
cat << 'EOF' > /workspace/repo/main.go
package main

import (
	"embed"
	"fmt"
	"os"
	"regexp"
	"strconv"
	"strings"
)

//go:embed fonts/*.flf
var embeddedFonts embed.FS

const (
	SM_EQUAL     = 1
	SM_LOWLINE   = 2
	SM_HIERARCHY = 4
	SM_PAIR      = 8
	SM_BIGX      = 16
	SM_HARDBLANK = 32
	SM_KERN      = 64
	SM_SMUSH     = 128
)

type FigletFont struct {
	font           string
	height         int
	hardBlank      byte
	printDirection int // 0: left-to-right, 1: right-to-left
	smushMode      int
	chars          map[int][]string
	width          map[int]int
}

func loadFont(name string) (*FigletFont, error) {
	dataBytes, err := embeddedFonts.ReadFile("fonts/" + name + ".flf")
	if err != nil {
		return nil, fmt.Errorf("font %s not found: %w", name, err)
	}

	data := string(dataBytes)
	data = strings.ReplaceAll(data, "\u0085", " ")
	data = strings.ReplaceAll(data, "\u2028", " ")
	data = strings.ReplaceAll(data, "\u2029", " ")

	rawLines := strings.Split(data, "\n")
	for i := range rawLines {
		rawLines[i] = strings.TrimRight(rawLines[i], "\r")
	}

	if len(rawLines) == 0 {
		return nil, fmt.Errorf("empty font file")
	}

	header := rawLines[0]
	rawLines = rawLines[1:]

	reMagic := regexp.MustCompile(`^[tf]lf2.`)
	loc := reMagic.FindStringIndex(header)
	if loc == nil {
		return nil, fmt.Errorf("invalid magic number in %s", name)
	}
	header = header[loc[1]:]

	fields := strings.Fields(header)
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed header in %s", name)
	}

	hardBlank := fields[0][0]
	height, _ := strconv.Atoi(fields[1])
	oldLayout, _ := strconv.Atoi(fields[4])
	commentLines, _ := strconv.Atoi(fields[5])

	printDir := 0
	if len(fields) > 6 {
		printDir, _ = strconv.Atoi(fields[6])
	}

	var fullLayout *int
	if len(fields) > 7 {
		fl, err := strconv.Atoi(fields[7])
		if err == nil {
			fullLayout = &fl
		}
	}

	smushMode := 0
	if fullLayout == nil {
		if oldLayout == 0 {
			smushMode = 64
		} else if oldLayout < 0 {
			smushMode = 0
		} else {
			smushMode = (oldLayout & 31) | 128
		}
	} else {
		smushMode = *fullLayout
	}

	ff := &FigletFont{
		font:           name,
		height:         height,
		hardBlank:      hardBlank,
		printDirection: printDir,
		smushMode:      smushMode,
		chars:          make(map[int][]string),
		width:          make(map[int]int),
	}

	if len(rawLines) < commentLines {
		return nil, fmt.Errorf("not enough lines for comments")
	}
	rawLines = rawLines[commentLines:]

	reEndMarker := regexp.MustCompile(`(.)\s*$`)

	readChar := func() (int, []string, bool) {
		if len(rawLines) < height {
			return 0, nil, false
		}
		var charLines []string
		var endByte byte
		maxW := 0

		for row := 0; row < height; row++ {
			line := rawLines[0]
			rawLines = rawLines[1:]

			if row == 0 {
				m := reEndMarker.FindStringSubmatch(line)
				if len(m) > 1 && len(m[1]) > 0 {
					endByte = m[1][0]
				}
			}

			trimmed := strings.TrimRight(line, " \t\r")
			cnt := 0
			for len(trimmed) > 0 && trimmed[len(trimmed)-1] == endByte && cnt < 2 {
				trimmed = trimmed[:len(trimmed)-1]
				cnt++
			}
			line = trimmed

			if len(line) > maxW {
				maxW = len(line)
			}
			charLines = append(charLines, line)
		}
		return maxW, charLines, true
	}

	// ASCII standard: 32 - 126
	for i := 32; i < 127; i++ {
		w, letter, ok := readChar()
		if !ok {
			break
		}
		empty := true
		for _, l := range letter {
			if l != "" {
				empty = false
				break
			}
		}
		if i == 32 || !empty {
			ff.chars[i] = letter
			ff.width[i] = w
		}
	}

	// German Umlaute: ÄÖÜäöüß
	german := []rune{'Ä', 'Ö', 'Ü', 'ä', 'ö', 'ü', 'ß'}
	for _, r := range german {
		if len(rawLines) < height {
			break
		}
		w, letter, ok := readChar()
		if !ok {
			break
		}
		empty := true
		for _, l := range letter {
			if l != "" {
				empty = false
				break
			}
		}
		if !empty {
			ff.chars[int(r)] = letter
			ff.width[int(r)] = w
		}
	}

	// Extended characters (pyfiglet only matches ^0x)
	reHex := regexp.MustCompile(`(?i)^0x`)
	for len(rawLines) > 0 {
		line := strings.TrimSpace(rawLines[0])
		rawLines = rawLines[1:]
		if line == "" {
			continue
		}
		codeStr := strings.Fields(line)[0]
		if reHex.MatchString(codeStr) {
			c, err := strconv.ParseInt(codeStr[2:], 16, 64)
			if err != nil {
				continue
			}
			w, letter, ok := readChar()
			if !ok {
				break
			}
			empty := true
			for _, l := range letter {
				if l != "" {
					empty = false
					break
				}
			}
			if !empty {
				ff.chars[int(c)] = letter
				ff.width[int(c)] = w
			}
		}
	}

	return ff, nil
}

type blankMarker struct {
	buffer   []string
	iterator int
}

type FigletBuilder struct {
	text              []int
	direction         string
	width             int
	font              *FigletFont
	justify           string
	iterator          int
	maxSmush          int
	curCharWidth      int
	prevCharWidth     int
	currentTotalWidth int
	blankMarkers      []blankMarker
	productQueue      [][]string
	buffer            []string
}

func newFigletBuilder(text string, font *FigletFont, direction string, width int, justify string) *FigletBuilder {
	runes := []rune(text)
	textCodes := make([]int, len(runes))
	for i, r := range runes {
		textCodes[i] = int(r)
	}

	buf := make([]string, font.height)
	for i := range buf {
		buf[i] = ""
	}

	return &FigletBuilder{
		text:      textCodes,
		direction: direction,
		width:     width,
		font:      font,
		justify:   justify,
		buffer:    buf,
	}
}

func (b *FigletBuilder) isNotFinished() bool {
	return b.iterator < len(b.text)
}

func (b *FigletBuilder) goToNextChar() {
	b.iterator++
}

func (b *FigletBuilder) getCharAt(i int) []string {
	if i < 0 || i >= len(b.text) {
		return nil
	}
	c := b.text[i]
	return b.font.chars[c]
}

func (b *FigletBuilder) getCharWidthAt(i int) int {
	if i < 0 || i >= len(b.text) {
		return 0
	}
	c := b.text[i]
	return b.font.width[c]
}

func (b *FigletBuilder) getCurChar() []string {
	return b.getCharAt(b.iterator)
}

func (b *FigletBuilder) getCurWidth() int {
	return b.getCharWidthAt(b.iterator)
}

func (b *FigletBuilder) smushChars(left, right byte) (byte, bool) {
	if left == ' ' {
		return right, true
	}
	if right == ' ' {
		return left, true
	}
	if b.prevCharWidth < 2 || b.curCharWidth < 2 {
		return 0, false
	}
	if (b.font.smushMode & SM_SMUSH) == 0 {
		return 0, false
	}
	if (b.font.smushMode & 63) == 0 {
		if left == b.font.hardBlank {
			return right, true
		}
		if right == b.font.hardBlank {
			return left, true
		}
		if b.direction == "right-to-left" {
			return left, true
		}
		return right, true
	}
	if (b.font.smushMode & SM_HARDBLANK) != 0 {
		if left == b.font.hardBlank && right == b.font.hardBlank {
			return left, true
		}
	}
	if left == b.font.hardBlank || right == b.font.hardBlank {
		return 0, false
	}
	if (b.font.smushMode & SM_EQUAL) != 0 {
		if left == right {
			return left, true
		}
	}
	if (b.font.smushMode & SM_LOWLINE) != 0 {
		if left == '_' && strings.IndexByte("|/\\[]{}()<>", right) != -1 {
			return right, true
		}
		if right == '_' && strings.IndexByte("|/\\[]{}()<>", left) != -1 {
			return left, true
		}
	}
	if (b.font.smushMode & SM_HIERARCHY) != 0 {
		hierarchy := []struct {
			a, b string
		}{
			{"|", "/\\[]{}()<>"},
			{"/\\", "[]{}()<>"},
			{"[]", "{}()<>"},
			{"{}", "()<>"},
			{"()", "<>"},
		}
		for _, h := range hierarchy {
			if strings.IndexByte(h.a, left) != -1 && strings.IndexByte(h.b, right) != -1 {
				return right, true
			}
			if strings.IndexByte(h.a, right) != -1 && strings.IndexByte(h.b, left) != -1 {
				return left, true
			}
		}
	}
	if (b.font.smushMode & SM_PAIR) != 0 {
		p1 := string([]byte{left, right})
		p2 := string([]byte{right, left})
		if p1 == "[]" || p1 == "{}" || p1 == "()" ||
			p2 == "[]" || p2 == "{}" || p2 == "()" {
			return '|', true
		}
	}
	if (b.font.smushMode & SM_BIGX) != 0 {
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

func (b *FigletBuilder) smushAmount(curChar []string) int {
	if (b.font.smushMode & (SM_SMUSH | SM_KERN)) == 0 {
		return 0
	}
	maxSmush := b.curCharWidth
	for row := 0; row < b.font.height; row++ {
		lineLeft := b.buffer[row]
		lineRight := curChar[row]
		if b.direction == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}

		linebd := len(strings.TrimRight(lineLeft, " ")) - 1
		if linebd < 0 {
			linebd = 0
		}
		var ch1 byte
		if linebd < len(lineLeft) {
			ch1 = lineLeft[linebd]
		}

		charbd := len(lineRight) - len(strings.TrimLeft(lineRight, " "))
		var ch2 byte
		if charbd < len(lineRight) {
			ch2 = lineRight[charbd]
		}

		amt := charbd + len(lineLeft) - 1 - linebd
		if ch1 == 0 || ch1 == ' ' {
			amt++
		} else if ch2 != 0 {
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

func (b *FigletBuilder) smushRow(curChar []string, row int) (string, string) {
	addLeft := b.buffer[row]
	addRight := curChar[row]
	if b.direction == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}

	addLeftBytes := []byte(addLeft)
	for i := 0; i < b.maxSmush; i++ {
		idx := len(addLeftBytes) - b.maxSmush + i
		var left byte
		if idx >= 0 && idx < len(addLeftBytes) {
			left = addLeftBytes[idx]
		}
		var right byte
		if i < len(addRight) {
			right = addRight[i]
		}
		if smushed, ok := b.smushChars(left, right); ok {
			if idx >= 0 && idx < len(addLeftBytes) {
				addLeftBytes[idx] = smushed
			}
		}
	}
	return string(addLeftBytes), addRight
}

func (b *FigletBuilder) addCurCharRowToBufferRow(curChar []string, row int) {
	addLeft, addRight := b.smushRow(curChar, row)
	rem := ""
	if b.maxSmush < len(addRight) {
		rem = addRight[b.maxSmush:]
	}
	b.buffer[row] = addLeft + rem
}

func (b *FigletBuilder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([]string, b.font.height)
	for i := range b.buffer {
		b.buffer[i] = ""
	}
	b.blankMarkers = nil
	b.prevCharWidth = 0
	curChar := b.getCurChar()
	if curChar == nil {
		return
	}
	b.maxSmush = b.smushAmount(curChar)
}

func (b *FigletBuilder) cutBufferAtLastBlank(savedBuffer []string, savedIterator int) {
	b.productQueue = append(b.productQueue, savedBuffer)
	b.iterator = savedIterator
	b.cutBufferCommon()
}

func (b *FigletBuilder) cutBufferAtLastChar() {
	b.productQueue = append(b.productQueue, b.buffer)
	b.iterator--
	b.cutBufferCommon()
}

func (b *FigletBuilder) getLastBlank() ([]string, int) {
	if len(b.blankMarkers) == 0 {
		return nil, -1
	}
	last := b.blankMarkers[len(b.blankMarkers)-1]
	b.blankMarkers = b.blankMarkers[:len(b.blankMarkers)-1]
	return last.buffer, last.iterator
}

func (b *FigletBuilder) handleNewLine() {
	savedBuffer, savedIterator := b.getLastBlank()
	if savedIterator != -1 {
		b.cutBufferAtLastBlank(savedBuffer, savedIterator)
	} else {
		b.cutBufferAtLastChar()
	}
}

func (b *FigletBuilder) cloneBuffer() []string {
	cp := make([]string, len(b.buffer))
	copy(cp, b.buffer)
	return cp
}

func (b *FigletBuilder) addCharToProduct() {
	curChar := b.getCurChar()

	if b.text[b.iterator] == '\n' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{b.cloneBuffer(), b.iterator})
		b.handleNewLine()
		return
	}

	if curChar == nil {
		return
	}

	b.curCharWidth = b.getCurWidth()
	b.maxSmush = b.smushAmount(curChar)
	b.currentTotalWidth = len(b.buffer[0]) + b.curCharWidth - b.maxSmush

	if b.text[b.iterator] == ' ' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{b.cloneBuffer(), b.iterator})
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

func (b *FigletBuilder) justifyString(justify string, buf []string) []string {
	res := make([]string, len(buf))
	copy(res, buf)
	if justify == "right" {
		for row := 0; row < b.font.height; row++ {
			pad := b.width - len(res[row]) - 1
			if pad > 0 {
				res[row] = strings.Repeat(" ", pad) + res[row]
			}
		}
	} else if justify == "center" {
		for row := 0; row < b.font.height; row++ {
			pad := (b.width - len(res[row])) / 2
			if pad > 0 {
				res[row] = strings.Repeat(" ", pad) + res[row]
			}
		}
	}
	return res
}

func (b *FigletBuilder) replaceHardblanks(buf []string) string {
	joined := strings.Join(buf, "\n") + "\n"
	return strings.ReplaceAll(joined, string(b.font.hardBlank), " ")
}

func (b *FigletBuilder) returnProduct() string {
	if b.buffer[0] != "" {
		b.productQueue = append(b.productQueue, b.buffer)
	}
	var sb strings.Builder
	for _, buf := range b.productQueue {
		justified := b.justifyString(b.justify, buf)
		sb.WriteString(b.replaceHardblanks(justified))
	}
	return sb.String()
}

func reverseText(s string) string {
	var revMap [256]byte
	for i := 0; i < 256; i++ {
		revMap[i] = byte(i)
	}
	revMap['('] = ')'
	revMap[')'] = '('
	revMap['/'] = '\\'
	revMap['\\'] = '/'
	revMap['<'] = '>'
	revMap['>'] = '<'
	revMap['['] = ']'
	revMap[']'] = '['
	revMap['{'] = '}'
	revMap['}'] = '{'

	lines := strings.Split(s, "\n")
	if len(lines) > 0 && lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}

	for idx, row := range lines {
		b := []byte(row)
		rev := make([]byte, len(b))
		for i := 0; i < len(b); i++ {
			rev[len(b)-1-i] = revMap[b[i]]
		}
		lines[idx] = string(rev)
	}
	return strings.Join(lines, "\n") + "\n"
}

func flipText(s string) string {
	var flipMap [256]byte
	for i := 0; i < 256; i++ {
		flipMap[i] = byte(i)
	}
	flipMap['/'] = '\\'
	flipMap['\\'] = '/'
	flipMap['A'] = 'V'
	flipMap['V'] = 'A'
	flipMap['M'] = 'W'
	flipMap['W'] = 'M'
	flipMap['P'] = 'b'
	flipMap['R'] = 'b'
	flipMap['b'] = 'P'
	flipMap['m'] = 'w'
	flipMap['w'] = 'm'
	flipMap['^'] = 'v'
	flipMap['v'] = '^'
	flipMap['_'] = '-'

	lines := strings.Split(s, "\n")
	if len(lines) > 0 && lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}

	n := len(lines)
	flipped := make([]string, n)
	for i := 0; i < n; i++ {
		b := []byte(lines[n-1-i])
		for j := range b {
			b[j] = flipMap[b[j]]
		}
		flipped[i] = string(b)
	}
	return strings.Join(flipped, "\n") + "\n"
}

func stripSurroundingNewlines(s string) string {
	lines := strings.Split(s, "\n")
	if len(lines) > 0 && lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	var out []string
	charsSeen := false
	for _, row := range lines {
		if strings.TrimSpace(row) != "" || charsSeen {
			charsSeen = true
			out = append(out, row)
		}
	}
	joined := strings.Join(out, "\n") + "\n"
	return strings.TrimRight(joined, " \t\r\n")
}

func normalizeSurroundingNewlines(s string) string {
	return "\n" + stripSurroundingNewlines(s) + "\n"
}

func main() {
	fontName := "standard"
	width := 80
	justify := "auto"
	direction := "auto"
	reverse := false
	flip := false
	stripNewlines := false
	normNewlines := false

	var textArgs []string
	args := os.Args[1:]

	for i := 0; i < len(args); i++ {
		arg := args[i]
		if arg == "-f" || arg == "--font" {
			if i+1 < len(args) {
				fontName = args[i+1]
				i++
			}
		} else if strings.HasPrefix(arg, "-f=") || strings.HasPrefix(arg, "--font=") {
			fontName = strings.SplitN(arg, "=", 2)[1]
		} else if arg == "-w" || arg == "--width" {
			if i+1 < len(args) {
				fmt.Sscanf(args[i+1], "%d", &width)
				i++
			}
		} else if strings.HasPrefix(arg, "-w=") || strings.HasPrefix(arg, "--width=") {
			fmt.Sscanf(strings.SplitN(arg, "=", 2)[1], "%d", &width)
		} else if arg == "-j" || arg == "--justify" {
			if i+1 < len(args) {
				justify = args[i+1]
				i++
			}
		} else if strings.HasPrefix(arg, "-j=") || strings.HasPrefix(arg, "--justify=") {
			justify = strings.SplitN(arg, "=", 2)[1]
		} else if arg == "-D" || arg == "--direction" {
			if i+1 < len(args) && (args[i+1] == "left-to-right" || args[i+1] == "right-to-left" || args[i+1] == "auto") {
				direction = args[i+1]
				i++
			} else {
				direction = "right-to-left"
			}
		} else if strings.HasPrefix(arg, "-D=") || strings.HasPrefix(arg, "--direction=") {
			direction = strings.SplitN(arg, "=", 2)[1]
		} else if arg == "-r" || arg == "--reverse" {
			reverse = true
		} else if arg == "-F" || arg == "--flip" {
			flip = true
		} else if arg == "-s" || arg == "--strip-surrounding-newlines" {
			stripNewlines = true
		} else if arg == "-n" || arg == "--normalize-surrounding-newlines" {
			normNewlines = true
		} else {
			textArgs = append(textArgs, arg)
		}
	}

	if len(textArgs) == 0 {
		return
	}
	text := strings.Join(textArgs, " ")

	ff, err := loadFont(fontName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: requested font %q not found.\n", fontName)
		os.Exit(1)
	}

	effDir := direction
	if effDir == "auto" {
		if ff.printDirection == 0 {
			effDir = "left-to-right"
		} else if ff.printDirection == 1 {
			effDir = "right-to-left"
		} else {
			effDir = "left-to-right"
		}
	}

	effJust := justify
	if effJust == "auto" {
		if effDir == "left-to-right" {
			effJust = "left"
		} else {
			effJust = "right"
		}
	}

	builder := newFigletBuilder(text, ff, effDir, width, effJust)
	for builder.isNotFinished() {
		builder.addCharToProduct()
		builder.goToNextChar()
	}

	r := builder.returnProduct()
	if reverse {
		r = reverseText(r)
	}
	if flip {
		r = flipText(r)
	}
	if stripNewlines {
		r = stripSurroundingNewlines(r)
	} else if normNewlines {
		r = normalizeSurroundingNewlines(r)
	}

	os.Stdout.WriteString(r)
	os.Stdout.WriteString("\n")
}
EOF
