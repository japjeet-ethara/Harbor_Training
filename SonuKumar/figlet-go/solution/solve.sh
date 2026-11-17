#!/bin/bash
set -e

REPO_DIR="/workspace/repo"
cd "$REPO_DIR"

# Ensure fonts are in repo
mkdir -p "$REPO_DIR/fonts"
if [ -d "$REPO_DIR/pyfiglet/fonts" ]; then
    cp -r "$REPO_DIR/pyfiglet/fonts"/* "$REPO_DIR/fonts/"
fi

# Write go.mod
cat <<'EOF' > "$REPO_DIR/go.mod"
module figlet

go 1.23
EOF

# Write main.go
cat <<'EOF' > "$REPO_DIR/main.go"
package main

import (
	"embed"
	"fmt"
	"os"
	"path/filepath"
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

const reverseMap = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !\"#$%&')(*+,-.\\0123456789:;>=<?@ABCDEFGHIJKLMNOPQRSTUVWXYZ]/[^_`abcdefghijklmnopqrstuvwxyz}|{~\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"

const flipMap = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !\"#$%&'()*+,-.\\0123456789:;<=>?@VBCDEFGHIJKLWNObQbSTUAMXYZ[/]v-`aPcdefghijklwnopqrstu^mxyz{|}~\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"

var reEndMarker = regexp.MustCompile(`(.)\s*$`)

type Font struct {
	name           string
	hardBlank      byte
	height         int
	baseLine       int
	maxLength      int
	oldLayout      int
	commentLines   int
	printDirection int
	smushMode      int
	chars          map[int][]string
	charWidth      map[int]int
}

func loadFontData(fontName string) ([]byte, error) {
	candidates := []string{
		filepath.Join("fonts", fontName+".flf"),
		filepath.Join("pyfiglet", "fonts", fontName+".flf"),
		fontName + ".flf",
	}
	for _, p := range candidates {
		if data, err := os.ReadFile(p); err == nil {
			return data, nil
		}
	}
	return embeddedFonts.ReadFile("fonts/" + fontName + ".flf")
}

func parseFont(fontName string, rawData []byte) (*Font, error) {
	s := string(rawData)
	s = strings.ReplaceAll(s, "\u0085", " ")
	s = strings.ReplaceAll(s, "\u2028", " ")
	s = strings.ReplaceAll(s, "\u2029", " ")

	lines := strings.Split(s, "\n")
	for i := range lines {
		lines[i] = strings.TrimRight(lines[i], "\r")
	}

	if len(lines) == 0 {
		return nil, fmt.Errorf("empty font")
	}

	headerLine := lines[0]
	lines = lines[1:]

	if !strings.HasPrefix(headerLine, "flf2") && !strings.HasPrefix(headerLine, "tlf2") {
		return nil, fmt.Errorf("invalid magic")
	}

	if len(headerLine) >= 5 {
		headerLine = headerLine[5:]
	}
	fields := strings.Fields(headerLine)
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed header")
	}

	hardBlank := fields[0][0]
	height, _ := strconv.Atoi(fields[1])
	baseLine, _ := strconv.Atoi(fields[2])
	maxLength, _ := strconv.Atoi(fields[3])
	oldLayout, _ := strconv.Atoi(fields[4])
	commentLines, _ := strconv.Atoi(fields[5])

	printDir := 0
	fullLayout := -1
	if len(fields) > 6 {
		printDir, _ = strconv.Atoi(fields[6])
	}
	if len(fields) > 7 {
		fullLayout, _ = strconv.Atoi(fields[7])
	}
	if fullLayout == -1 {
		if oldLayout == 0 {
			fullLayout = 64
		} else if oldLayout < 0 {
			fullLayout = 0
		} else {
			fullLayout = (oldLayout & 31) | 128
		}
	}

	f := &Font{
		name:           fontName,
		hardBlank:      hardBlank,
		height:         height,
		baseLine:       baseLine,
		maxLength:      maxLength,
		oldLayout:      oldLayout,
		commentLines:   commentLines,
		printDirection: printDir,
		smushMode:      fullLayout,
		chars:          make(map[int][]string),
		charWidth:      make(map[int]int),
	}

	if len(lines) < commentLines {
		return nil, fmt.Errorf("truncated comments")
	}
	lines = lines[commentLines:]

	parseChar := func() (int, []string, bool) {
		if len(lines) < height {
			return 0, nil, false
		}
		var endChar byte
		var endRe *regexp.Regexp
		width := 0
		charLines := make([]string, 0, height)

		for row := 0; row < height; row++ {
			line := lines[0]
			lines = lines[1:]

			if endRe == nil {
				m := reEndMarker.FindStringSubmatch(line)
				if len(m) > 1 {
					endChar = m[1][0]
					pattern := regexp.QuoteMeta(string(endChar)) + `{1,2}\s*$`
					endRe = regexp.MustCompile(pattern)
				}
			}
			if endRe != nil {
				line = endRe.ReplaceAllString(line, "")
			}
			if len(line) > width {
				width = len(line)
			}
			charLines = append(charLines, line)
		}
		return width, charLines, true
	}

	for i := 32; i < 127; i++ {
		w, letter, ok := parseChar()
		if !ok {
			break
		}
		allEmpty := true
		for _, l := range letter {
			if len(l) > 0 {
				allEmpty = false
				break
			}
		}
		if i == 32 || !allEmpty {
			f.chars[i] = letter
			f.charWidth[i] = w
		}
	}

	umlaute := []rune{'Ä', 'Ö', 'Ü', 'ä', 'ö', 'ü', 'ß'}
	for _, r := range umlaute {
		if len(lines) < height {
			break
		}
		w, letter, ok := parseChar()
		if !ok {
			break
		}
		allEmpty := true
		for _, l := range letter {
			if len(l) > 0 {
				allEmpty = false
				break
			}
		}
		if !allEmpty {
			f.chars[int(r)] = letter
			f.charWidth[int(r)] = w
		}
	}

	for len(lines) > 0 {
		line := strings.TrimSpace(lines[0])
		lines = lines[1:]
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, " ", 2)
		codeStr := parts[0]
		if strings.HasPrefix(strings.ToLower(codeStr), "0x") {
			code, err := strconv.ParseInt(codeStr[2:], 16, 64)
			if err != nil {
				continue
			}
			w, letter, ok := parseChar()
			if !ok {
				break
			}
			allEmpty := true
			for _, l := range letter {
				if len(l) > 0 {
					allEmpty = false
					break
				}
			}
			if !allEmpty {
				f.chars[int(code)] = letter
				f.charWidth[int(code)] = w
			}
		}
	}

	return f, nil
}

func smushChars(left, right byte, hardBlank byte, smushMode int, dir string, prevW, curW int) (byte, bool) {
	if left == ' ' {
		return right, true
	}
	if right == ' ' {
		return left, true
	}

	if prevW < 2 || curW < 2 {
		return 0, false
	}

	if (smushMode & SM_SMUSH) == 0 {
		return 0, false
	}

	if (smushMode & 63) == 0 {
		if left == hardBlank {
			return right, true
		}
		if right == hardBlank {
			return left, true
		}
		if dir == "right-to-left" {
			return left, true
		}
		return right, true
	}

	if (smushMode & SM_HARDBLANK) != 0 {
		if left == hardBlank && right == hardBlank {
			return left, true
		}
	}

	if left == hardBlank || right == hardBlank {
		return 0, false
	}

	if (smushMode & SM_EQUAL) != 0 {
		if left == right {
			return left, true
		}
	}

	if (smushMode & SM_LOWLINE) != 0 {
		const hierarchyChars = "|/\\[]{}()<>"
		if left == '_' && strings.IndexByte(hierarchyChars, right) != -1 {
			return right, true
		}
		if right == '_' && strings.IndexByte(hierarchyChars, left) != -1 {
			return left, true
		}
	}

	if (smushMode & SM_HIERARCHY) != 0 {
		hClass := func(b byte) int {
			switch b {
			case '|':
				return 0
			case '/', '\\':
				return 1
			case '[', ']':
				return 2
			case '{', '}':
				return 3
			case '(', ')':
				return 4
			case '<', '>':
				return 5
			default:
				return -1
			}
		}
		cL := hClass(left)
		cR := hClass(right)
		if cL != -1 && cR != -1 && cL != cR {
			if cL < cR {
				return right, true
			}
			return left, true
		}
	}

	if (smushMode & SM_PAIR) != 0 {
		pair := string([]byte{left, right})
		if pair == "[]" || pair == "][" || pair == "{}" || pair == "}{" || pair == "()" || pair == ")(" {
			return '|', true
		}
	}

	if (smushMode & SM_BIGX) != 0 {
		if left == '/' && right == '\\' {
			return '|', true
		}
		if left == '\\' && right == '/' {
			return 'Y', true
		}
		if left == '>' && right == '<' {
			return 'X', true
		}
	}

	return 0, false
}

func smushAmount(buffer []string, curChar []string, font *Font, dir string, curW, prevW int) int {
	if (font.smushMode & (SM_SMUSH | SM_KERN)) == 0 {
		return 0
	}
	maxSmush := curW
	for row := 0; row < font.height; row++ {
		lineLeft := buffer[row]
		lineRight := curChar[row]
		if dir == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}

		trimmedL := strings.TrimRight(lineLeft, " ")
		linebd := len(trimmedL) - 1
		if linebd < 0 {
			linebd = 0
		}
		var ch1 byte
		if linebd < len(lineLeft) {
			ch1 = lineLeft[linebd]
		} else {
			linebd = 0
			ch1 = 0
		}

		trimmedR := strings.TrimLeft(lineRight, " ")
		charbd := len(lineRight) - len(trimmedR)
		var ch2 byte
		if charbd < len(lineRight) {
			ch2 = lineRight[charbd]
		} else {
			charbd = len(lineRight)
			ch2 = 0
		}

		amt := charbd + len(lineLeft) - 1 - linebd
		if ch1 == 0 || ch1 == ' ' {
			amt++
		} else if ch2 != 0 {
			if _, ok := smushChars(ch1, ch2, font.hardBlank, font.smushMode, dir, prevW, curW); ok {
				amt++
			}
		}

		if amt < maxSmush {
			maxSmush = amt
		}
	}
	return maxSmush
}

func smushRow(bufferRow, curCharRow string, font *Font, dir string, maxSmush int, curW, prevW int) (string, string) {
	addLeft := bufferRow
	addRight := curCharRow
	if dir == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}

	leftBytes := []byte(addLeft)
	for i := 0; i < maxSmush; i++ {
		idx := len(addLeft) - maxSmush + i
		var left byte
		if idx >= 0 && idx < len(addLeft) {
			left = addLeft[idx]
		}
		var right byte
		if i < len(addRight) {
			right = addRight[i]
		}
		smushed, ok := smushChars(left, right, font.hardBlank, font.smushMode, dir, prevW, curW)
		if ok && idx >= 0 && idx < len(leftBytes) {
			leftBytes[idx] = smushed
		}
	}
	return string(leftBytes), addRight
}

func addCurCharRowToBufferRow(bufferRow, curCharRow string, font *Font, dir string, maxSmush int, curW, prevW int) string {
	addLeft, addRight := smushRow(bufferRow, curCharRow, font, dir, maxSmush, curW, prevW)
	if maxSmush < len(addRight) {
		return addLeft + addRight[maxSmush:]
	}
	return addLeft
}

type blankMarker struct {
	buffer   []string
	iterator int
}

type FigletBuilder struct {
	text               []int
	direction          string
	width              int
	font               *Font
	justify            string
	iterator           int
	maxSmush           int
	curCharWidth       int
	prevCharWidth      int
	currentTotalWidth  int
	blankMarkers       []blankMarker
	queue              [][]string
	buffer             []string
}

func newBuilder(text string, font *Font, direction string, width int, justify string) *FigletBuilder {
	runes := []rune(text)
	textCodes := make([]int, len(runes))
	for i, r := range runes {
		textCodes[i] = int(r)
	}

	b := &FigletBuilder{
		text:      textCodes,
		direction: direction,
		width:     width,
		font:      font,
		justify:   justify,
		buffer:    make([]string, font.height),
	}
	return b
}

func (b *FigletBuilder) getCurChar() []string {
	if b.iterator < 0 || b.iterator >= len(b.text) {
		return nil
	}
	c := b.text[b.iterator]
	return b.font.chars[c]
}

func (b *FigletBuilder) getCurWidth() int {
	if b.iterator < 0 || b.iterator >= len(b.text) {
		return 0
	}
	c := b.text[b.iterator]
	return b.font.charWidth[c]
}

func (b *FigletBuilder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([]string, b.font.height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	curChar := b.getCurChar()
	if curChar != nil {
		b.maxSmush = smushAmount(b.buffer, curChar, b.font, b.direction, b.curCharWidth, b.prevCharWidth)
	}
}

func (b *FigletBuilder) cutBufferAtLastBlank(savedBuffer []string, savedIterator int) {
	bufCopy := make([]string, len(savedBuffer))
	copy(bufCopy, savedBuffer)
	b.queue = append(b.queue, bufCopy)
	b.iterator = savedIterator
	b.cutBufferCommon()
}

func (b *FigletBuilder) cutBufferAtLastChar() {
	bufCopy := make([]string, len(b.buffer))
	copy(bufCopy, b.buffer)
	b.queue = append(b.queue, bufCopy)
	b.iterator--
	b.cutBufferCommon()
}

func (b *FigletBuilder) handleNewLine() {
	if len(b.blankMarkers) > 0 {
		last := b.blankMarkers[len(b.blankMarkers)-1]
		b.blankMarkers = b.blankMarkers[:len(b.blankMarkers)-1]
		b.cutBufferAtLastBlank(last.buffer, last.iterator)
	} else {
		b.cutBufferAtLastChar()
	}
}

func (b *FigletBuilder) copyBuffer() []string {
	c := make([]string, len(b.buffer))
	copy(c, b.buffer)
	return c
}

func (b *FigletBuilder) addCharToProduct() {
	if b.text[b.iterator] == int('\n') {
		b.blankMarkers = append(b.blankMarkers, blankMarker{buffer: b.copyBuffer(), iterator: b.iterator})
		b.handleNewLine()
		return
	}

	curChar := b.getCurChar()
	if curChar == nil {
		return
	}

	curW := b.getCurWidth()
	if b.width < curW {
		return
	}

	b.curCharWidth = curW
	b.maxSmush = smushAmount(b.buffer, curChar, b.font, b.direction, b.curCharWidth, b.prevCharWidth)
	b.currentTotalWidth = len(b.buffer[0]) + b.curCharWidth - b.maxSmush

	if b.text[b.iterator] == int(' ') {
		b.blankMarkers = append(b.blankMarkers, blankMarker{buffer: b.copyBuffer(), iterator: b.iterator})
	}

	if b.currentTotalWidth >= b.width {
		b.handleNewLine()
	} else {
		for row := 0; row < b.font.height; row++ {
			b.buffer[row] = addCurCharRowToBufferRow(b.buffer[row], curChar[row], b.font, b.direction, b.maxSmush, b.curCharWidth, b.prevCharWidth)
		}
	}

	b.prevCharWidth = b.curCharWidth
}

func (b *FigletBuilder) returnProduct() string {
	if b.buffer[0] != "" {
		bufCopy := make([]string, len(b.buffer))
		copy(bufCopy, b.buffer)
		b.queue = append(b.queue, bufCopy)
	}

	var sb strings.Builder
	for _, buf := range b.queue {
		justified := b.justifyBuffer(buf)
		replaced := b.replaceHardblanks(justified)
		sb.WriteString(replaced)
	}
	return sb.String()
}

func (b *FigletBuilder) justifyBuffer(buf []string) []string {
	res := make([]string, len(buf))
	copy(res, buf)

	if b.justify == "right" {
		for row := 0; row < b.font.height; row++ {
			padLen := b.width - len(res[row]) - 1
			if padLen > 0 {
				res[row] = strings.Repeat(" ", padLen) + res[row]
			}
		}
	} else if b.justify == "center" {
		for row := 0; row < b.font.height; row++ {
			padLen := (b.width - len(res[row])) / 2
			if padLen > 0 {
				res[row] = strings.Repeat(" ", padLen) + res[row]
			}
		}
	}
	return res
}

func (b *FigletBuilder) replaceHardblanks(buf []string) string {
	s := strings.Join(buf, "\n") + "\n"
	return strings.ReplaceAll(s, string(b.font.hardBlank), " ")
}

func renderText(text string, font *Font, direction, justify string, width int) string {
	if direction == "auto" {
		if font.printDirection == 1 {
			direction = "right-to-left"
		} else {
			direction = "left-to-right"
		}
	}
	if justify == "auto" {
		if direction == "right-to-left" {
			justify = "right"
		} else {
			justify = "left"
		}
	}

	b := newBuilder(text, font, direction, width, justify)
	for b.iterator < len(b.text) {
		b.addCharToProduct()
		b.iterator++
	}
	return b.returnProduct()
}

func pySplitLines(s string) []string {
	if len(s) == 0 {
		return nil
	}
	s = strings.ReplaceAll(s, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	lines := strings.Split(s, "\n")
	if len(lines) > 0 && lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	return lines
}

func reverseFiglet(s string) string {
	lines := pySplitLines(s)
	var out []string
	for _, row := range lines {
		b := []byte(row)
		for i, c := range b {
			b[i] = reverseMap[c]
		}
		for i, j := 0, len(b)-1; i < j; i, j = i+1, j-1 {
			b[i], b[j] = b[j], b[i]
		}
		out = append(out, string(b))
	}
	return strings.Join(out, "\n") + "\n"
}

func flipFiglet(s string) string {
	lines := pySplitLines(s)
	var out []string
	for i := len(lines) - 1; i >= 0; i-- {
		row := lines[i]
		b := []byte(row)
		for j, c := range b {
			b[j] = flipMap[c]
		}
		out = append(out, string(b))
	}
	return strings.Join(out, "\n") + "\n"
}

func stripSurroundingNewlines(s string) string {
	lines := pySplitLines(s)
	var out []string
	charsSeen := false
	for _, row := range lines {
		if strings.TrimSpace(row) != "" || charsSeen {
			charsSeen = true
			out = append(out, row)
		}
	}
	res := strings.Join(out, "\n") + "\n"
	return strings.TrimRight(res, " \t\r\n")
}

func normalizeSurroundingNewlines(s string) string {
	return "\n" + stripSurroundingNewlines(s) + "\n"
}

func main() {
	args := os.Args[1:]

	fontName := "standard"
	width := 80
	justify := "auto"
	direction := "auto"
	rev := false
	flip := false
	strip := false
	norm := false
	var textParts []string

	for i := 0; i < len(args); i++ {
		a := args[i]
		switch a {
		case "-f", "--font":
			if i+1 < len(args) {
				fontName = args[i+1]
				i++
			}
		case "-w", "--width":
			if i+1 < len(args) {
				width, _ = strconv.Atoi(args[i+1])
				i++
			}
		case "-j", "--justify":
			if i+1 < len(args) {
				justify = args[i+1]
				i++
			}
		case "-D", "--direction":
			if i+1 < len(args) {
				direction = args[i+1]
				i++
			}
		case "-r", "--reverse":
			rev = true
		case "-F", "--flip":
			flip = true
		case "-s", "--strip-surrounding-newlines":
			strip = true
		case "-n", "--normalize-surrounding-newlines":
			norm = true
		default:
			textParts = append(textParts, a)
		}
	}

	if len(textParts) == 0 {
		return
	}

	text := strings.Join(textParts, " ")

	rawData, err := loadFontData(fontName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: requested font %q not found.\n", fontName)
		os.Exit(1)
	}

	font, err := parseFont(fontName, rawData)
	if err != nil {
		fmt.Fprintf(os.Stderr, "font parse error: %v\n", err)
		os.Exit(1)
	}

	rendered := renderText(text, font, direction, justify, width)

	if rev {
		rendered = reverseFiglet(rendered)
	}
	if flip {
		rendered = flipFiglet(rendered)
	}

	if strip {
		rendered = stripSurroundingNewlines(rendered)
		os.Stdout.WriteString(rendered + "\n")
	} else if norm {
		rendered = normalizeSurroundingNewlines(rendered)
		os.Stdout.WriteString(rendered + "\n")
	} else {
		os.Stdout.WriteString(rendered + "\n")
	}
}
EOF

# Delete all python files
find "$REPO_DIR" -name "*.py" -type f -delete
find "$REPO_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf "$REPO_DIR/pyfiglet"

echo "Solution written and repository cleaned successfully."
