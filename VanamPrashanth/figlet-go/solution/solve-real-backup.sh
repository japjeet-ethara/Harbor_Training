#!/bin/bash
set -e

# Change to repository root
cd /workspace/repo

# 1. Create fonts folder and copy standard .flf fonts
mkdir -p fonts
if [ -d pyfiglet/fonts ]; then
    cp pyfiglet/fonts/*.flf fonts/
elif [ -d pyfiglet/fonts-standard ]; then
    cp pyfiglet/fonts-standard/*.flf fonts/
fi

# 2. Write go.mod
cat << 'EOF' > go.mod
module figlet

go 1.23
EOF

# 3. Write main.go
cat << 'EOF' > main.go
package main

import (
	"embed"
	"fmt"
	"os"
	"path/filepath"
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

type Font struct {
	Name           string
	Height         int
	Baseline       int
	MaxLength      int
	OldLayout      int
	CommentLines   int
	PrintDirection int
	SmushMode      int
	HardBlank      byte
	Chars          map[int][]string
	Width          map[int]int
}

func loadFont(name string) (*Font, error) {
	var data []byte

	// In embed.FS, paths must always use forward slashes
	embedPath := "fonts/" + name + ".flf"
	if content, readErr := embeddedFonts.ReadFile(embedPath); readErr == nil {
		data = content
	}

	if data == nil {
		diskPaths := []string{
			filepath.Join("fonts", name+".flf"),
			filepath.Join("pyfiglet", "fonts", name+".flf"),
			filepath.Join("pyfiglet", "fonts-standard", name+".flf"),
			name + ".flf",
		}
		for _, p := range diskPaths {
			if content, readErr := os.ReadFile(p); readErr == nil {
				data = content
				break
			}
		}
	}

	if data == nil {
		return nil, fmt.Errorf("requested font '%s' not found", name)
	}

	raw := string(data)
	// Replace unicode line splitting characters other than CRLF
	raw = strings.ReplaceAll(raw, "\u0085", " ")
	raw = strings.ReplaceAll(raw, "\u2028", " ")
	raw = strings.ReplaceAll(raw, "\u2029", " ")

	// Split lines
	raw = strings.ReplaceAll(raw, "\r\n", "\n")
	raw = strings.ReplaceAll(raw, "\r", "\n")
	lines := strings.Split(raw, "\n")
	if len(lines) == 0 {
		return nil, fmt.Errorf("empty font file")
	}

	headerLine := lines[0]
	lines = lines[1:]

	if len(headerLine) < 5 {
		return nil, fmt.Errorf("malformed header")
	}
	magic := headerLine[:4]
	if magic != "flf2" && magic != "tlf2" {
		return nil, fmt.Errorf("invalid magic number")
	}

	subbed := headerLine[5:]
	fields := strings.Fields(subbed)
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed header fields")
	}

	hardBlank := fields[0][0]
	height, _ := strconv.Atoi(fields[1])
	baseline, _ := strconv.Atoi(fields[2])
	maxLength, _ := strconv.Atoi(fields[3])
	oldLayout, _ := strconv.Atoi(fields[4])
	commentLines, _ := strconv.Atoi(fields[5])

	printDirection := 0
	if len(fields) > 6 {
		printDirection, _ = strconv.Atoi(fields[6])
	}

	var fullLayout *int
	if len(fields) > 7 {
		val, _ := strconv.Atoi(fields[7])
		fullLayout = &val
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

	if len(lines) < commentLines {
		return nil, fmt.Errorf("unexpected end of comments")
	}
	lines = lines[commentLines:]

	font := &Font{
		Name:           name,
		Height:         height,
		Baseline:       baseline,
		MaxLength:      maxLength,
		OldLayout:      oldLayout,
		CommentLines:   commentLines,
		PrintDirection: printDirection,
		SmushMode:      smushMode,
		HardBlank:      hardBlank,
		Chars:          make(map[int][]string),
		Width:          make(map[int]int),
	}

	ptr := 0
	readChar := func() (int, []string) {
		if ptr+height > len(lines) {
			return 0, nil
		}
		firstLine := lines[ptr]
		trimmed := strings.TrimRight(firstLine, " \t\r")
		if len(trimmed) == 0 {
			return 0, nil
		}
		endByte := trimmed[len(trimmed)-1]
		end1 := string([]byte{endByte})
		end2 := string([]byte{endByte, endByte})

		maxWidth := 0
		glyph := make([]string, height)
		for r := 0; r < height; r++ {
			line := lines[ptr]
			ptr++
			t := strings.TrimRight(line, " \t\r")
			if strings.HasSuffix(t, end2) {
				t = t[:len(t)-len(end2)]
			} else if strings.HasSuffix(t, end1) {
				t = t[:len(t)-len(end1)]
			}
			if len(t) > maxWidth {
				maxWidth = len(t)
			}
			glyph[r] = t
		}
		return maxWidth, glyph
	}

	// ASCII standard 32 - 126
	for i := 32; i < 127; i++ {
		w, letter := readChar()
		isEmpty := true
		for _, row := range letter {
			if row != "" {
				isEmpty = false
				break
			}
		}
		if i == 32 || !isEmpty {
			font.Chars[i] = letter
			font.Width[i] = w
		}
	}

	// German Umlaute
	umlaute := []int{196, 214, 220, 228, 246, 252, 223}
	for _, code := range umlaute {
		if ptr >= len(lines) {
			break
		}
		w, letter := readChar()
		isEmpty := true
		for _, row := range letter {
			if row != "" {
				isEmpty = false
				break
			}
		}
		if !isEmpty {
			font.Chars[code] = letter
			font.Width[code] = w
		}
	}

	// Extended characters
	for ptr < len(lines) {
		line := strings.TrimSpace(lines[ptr])
		ptr++
		if line == "" {
			continue
		}
		f := strings.SplitN(line, " ", 2)
		first := f[0]
		if strings.HasPrefix(strings.ToLower(first), "0x") {
			code64, err := strconv.ParseInt(first[2:], 16, 32)
			if err == nil {
				w, letter := readChar()
				isEmpty := true
				for _, row := range letter {
					if row != "" {
						isEmpty = false
						break
					}
				}
				if !isEmpty {
					font.Chars[int(code64)] = letter
					font.Width[int(code64)] = w
				}
			}
		}
	}

	return font, nil
}

type BlankMarker struct {
	Buffer   []string
	Iterator int
}

type Builder struct {
	text              []rune
	direction         string
	width             int
	font              *Font
	justify           string
	iterator          int
	maxSmush          int
	curCharWidth      int
	prevCharWidth     int
	currentTotalWidth int
	blankMarkers      []BlankMarker
	queue             [][]string
	buffer            []string
}

func NewBuilder(text string, font *Font, direction string, width int, justify string) *Builder {
	b := &Builder{
		text:      []rune(text),
		direction: direction,
		width:     width,
		font:      font,
		justify:   justify,
		buffer:    make([]string, font.Height),
	}
	return b
}

func (b *Builder) smushChars(left, right byte) (byte, bool) {
	if left == ' ' {
		return right, true
	}
	if right == ' ' {
		return left, true
	}

	if b.prevCharWidth < 2 || b.curCharWidth < 2 {
		return 0, false
	}

	if (b.font.SmushMode & SM_SMUSH) == 0 {
		return 0, false
	}

	hardBlank := b.font.HardBlank

	if (b.font.SmushMode & 63) == 0 {
		if left == hardBlank {
			return right, true
		}
		if right == hardBlank {
			return left, true
		}
		if b.direction == "right-to-left" {
			return left, true
		}
		return right, true
	}

	if (b.font.SmushMode & SM_HARDBLANK) != 0 {
		if left == hardBlank && right == hardBlank {
			return left, true
		}
	}

	if left == hardBlank || right == hardBlank {
		return 0, false
	}

	if (b.font.SmushMode & SM_EQUAL) != 0 {
		if left == right {
			return left, true
		}
	}

	if (b.font.SmushMode & SM_LOWLINE) != 0 {
		if left == '_' && strings.IndexByte("|/\\[]{}()<>", right) != -1 {
			return right, true
		}
		if right == '_' && strings.IndexByte("|/\\[]{}()<>", left) != -1 {
			return left, true
		}
	}

	if (b.font.SmushMode & SM_HIERARCHY) != 0 {
		levels := []string{
			"|",
			"/\\",
			"[]",
			"{}",
			"()",
			"<>",
		}
		levelOf := func(c byte) int {
			for lvl, chars := range levels {
				if strings.IndexByte(chars, c) != -1 {
					return lvl + 1
				}
			}
			return 0
		}
		lvl1 := levelOf(left)
		lvl2 := levelOf(right)
		if lvl1 > 0 && lvl2 > 0 && lvl1 != lvl2 {
			if lvl1 > lvl2 {
				return left, true
			}
			return right, true
		}
	}

	if (b.font.SmushMode & SM_PAIR) != 0 {
		pair := string([]byte{left, right})
		pairRev := string([]byte{right, left})
		if pair == "[]" || pair == "{}" || pair == "()" ||
			pairRev == "[]" || pairRev == "{}" || pairRev == "()" {
			return '|', true
		}
	}

	if (b.font.SmushMode & SM_BIGX) != 0 {
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

func (b *Builder) smushAmount(buffer []string, curChar []string) int {
	if (b.font.SmushMode & (SM_SMUSH | SM_KERN)) == 0 {
		return 0
	}

	maxSmush := b.curCharWidth
	for row := 0; row < b.font.Height; row++ {
		lineLeft := buffer[row]
		lineRight := curChar[row]
		if b.direction == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}

		rstripped := strings.TrimRight(lineLeft, " ")
		linebd := len(rstripped) - 1
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

		lstripped := strings.TrimLeft(lineRight, " ")
		charbd := len(lineRight) - len(lstripped)
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

func (b *Builder) getCurChar() []string {
	if b.iterator < 0 || b.iterator >= len(b.text) {
		return nil
	}
	c := int(b.text[b.iterator])
	return b.font.Chars[c]
}

func (b *Builder) getCurWidth() int {
	if b.iterator < 0 || b.iterator >= len(b.text) {
		return 0
	}
	c := int(b.text[b.iterator])
	return b.font.Width[c]
}

func (b *Builder) smushRow(curChar []string, row int) (string, string) {
	addLeft := []byte(b.buffer[row])
	addRight := []byte(curChar[row])

	if b.direction == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}

	for i := 0; i < b.maxSmush; i++ {
		idx := len(addLeft) - b.maxSmush + i
		var left byte
		if idx >= 0 && idx < len(addLeft) {
			left = addLeft[idx]
		}
		var right byte
		if i < len(addRight) {
			right = addRight[i]
		}
		smushed, ok := b.smushChars(left, right)
		if ok && idx >= 0 && idx < len(addLeft) {
			addLeft[idx] = smushed
		}
	}
	return string(addLeft), string(addRight)
}

func (b *Builder) addCurCharRowToBufferRow(curChar []string, row int) {
	addLeft, addRight := b.smushRow(curChar, row)
	rightRem := ""
	if b.maxSmush < len(addRight) {
		rightRem = addRight[b.maxSmush:]
	}
	b.buffer[row] = addLeft + rightRem
}

func (b *Builder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([]string, b.font.Height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	curChar := b.getCurChar()
	if curChar == nil {
		return
	}
	b.maxSmush = b.smushAmount(b.buffer, curChar)
}

func (b *Builder) cutBufferAtLastBlank(saved []string, savedIterator int) {
	b.queue = append(b.queue, saved)
	b.iterator = savedIterator
	b.cutBufferCommon()
}

func (b *Builder) cutBufferAtLastChar() {
	b.queue = append(b.queue, b.buffer)
	b.iterator--
	b.cutBufferCommon()
}

func (b *Builder) getLastBlank() (BlankMarker, bool) {
	if len(b.blankMarkers) == 0 {
		return BlankMarker{}, false
	}
	last := b.blankMarkers[len(b.blankMarkers)-1]
	b.blankMarkers = b.blankMarkers[:len(b.blankMarkers)-1]
	return last, true
}

func (b *Builder) handleNewLine() {
	if marker, ok := b.getLastBlank(); ok {
		b.cutBufferAtLastBlank(marker.Buffer, marker.Iterator)
	} else {
		b.cutBufferAtLastChar()
	}
}

func (b *Builder) copyBuffer() []string {
	cp := make([]string, len(b.buffer))
	copy(cp, b.buffer)
	return cp
}

func (b *Builder) addCharToProduct() {
	if b.text[b.iterator] == '\n' {
		b.blankMarkers = append(b.blankMarkers, BlankMarker{Buffer: b.copyBuffer(), Iterator: b.iterator})
		b.handleNewLine()
		return
	}

	curChar := b.getCurChar()
	if curChar == nil {
		return
	}

	b.curCharWidth = b.getCurWidth()
	b.maxSmush = b.smushAmount(b.buffer, curChar)
	b.currentTotalWidth = len(b.buffer[0]) + b.curCharWidth - b.maxSmush

	if b.text[b.iterator] == ' ' {
		b.blankMarkers = append(b.blankMarkers, BlankMarker{Buffer: b.copyBuffer(), Iterator: b.iterator})
	}

	if b.currentTotalWidth >= b.width {
		b.handleNewLine()
	} else {
		for row := 0; row < b.font.Height; row++ {
			b.addCurCharRowToBufferRow(curChar, row)
		}
	}

	b.prevCharWidth = b.curCharWidth
}

func (b *Builder) justifyBuffer(buf []string) []string {
	res := make([]string, len(buf))
	copy(res, buf)
	if b.justify == "right" {
		for row := 0; row < b.font.Height; row++ {
			pad := b.width - len(res[row]) - 1
			if pad < 0 {
				pad = 0
			}
			res[row] = strings.Repeat(" ", pad) + res[row]
		}
	} else if b.justify == "center" {
		for row := 0; row < b.font.Height; row++ {
			pad := (b.width - len(res[row])) / 2
			if pad < 0 {
				pad = 0
			}
			res[row] = strings.Repeat(" ", pad) + res[row]
		}
	}
	return res
}

func (b *Builder) replaceHardblanks(buf []string) string {
	s := strings.Join(buf, "\n") + "\n"
	return strings.ReplaceAll(s, string(b.font.HardBlank), " ")
}

func (b *Builder) Build() string {
	for b.iterator < len(b.text) {
		b.addCharToProduct()
		b.iterator++
	}

	if b.buffer[0] != "" {
		b.queue = append(b.queue, b.buffer)
	}

	var sb strings.Builder
	for _, buf := range b.queue {
		jBuf := b.justifyBuffer(buf)
		sb.WriteString(b.replaceHardblanks(jBuf))
	}
	return sb.String()
}

const reverseMap = "" +
	"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f" +
	"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f" +
	" !\"#$%&')(*+,-.\\" +
	"0123456789:;>=<?" +
	"@ABCDEFGHIJKLMNO" +
	"PQRSTUVWXYZ]/[^_" +
	"`abcdefghijklmno" +
	"pqrstuvwxyz}|{~\x7f" +
	"\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f" +
	"\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f" +
	"\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf" +
	"\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf" +
	"\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf" +
	"\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf" +
	"\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef" +
	"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"

const flipMap = "" +
	"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f" +
	"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f" +
	" !\"#$%&'()*+,-.\\" +
	"0123456789:;<=>?" +
	"@VBCDEFGHIJKLWNO" +
	"bQbSTUAMXYZ[/]v-" +
	"`aPcdefghijklwno" +
	"pqrstu^mxyz{|}~\x7f" +
	"\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f" +
	"\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f" +
	"\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf" +
	"\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf" +
	"\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf" +
	"\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf" +
	"\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef" +
	"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"

func reverseText(s string) string {
	rawLines := strings.Split(s, "\n")
	if len(rawLines) > 0 && rawLines[len(rawLines)-1] == "" {
		rawLines = rawLines[:len(rawLines)-1]
	}
	var out []string
	for _, row := range rawLines {
		runes := []rune(row)
		rev := make([]rune, len(runes))
		for i, r := range runes {
			if r < 256 {
				rev[len(runes)-1-i] = rune(reverseMap[r])
			} else {
				rev[len(runes)-1-i] = r
			}
		}
		out = append(out, string(rev))
	}
	return strings.Join(out, "\n") + "\n"
}

func flipText(s string) string {
	rawLines := strings.Split(s, "\n")
	if len(rawLines) > 0 && rawLines[len(rawLines)-1] == "" {
		rawLines = rawLines[:len(rawLines)-1]
	}
	var out []string
	for i := len(rawLines) - 1; i >= 0; i-- {
		row := rawLines[i]
		runes := []rune(row)
		fl := make([]rune, len(runes))
		for j, r := range runes {
			if r < 256 {
				fl[j] = rune(flipMap[r])
			} else {
				fl[j] = r
			}
		}
		out = append(out, string(fl))
	}
	return strings.Join(out, "\n") + "\n"
}

func stripSurroundingNewlines(s string) string {
	rawLines := strings.Split(s, "\n")
	if len(rawLines) > 0 && rawLines[len(rawLines)-1] == "" {
		rawLines = rawLines[:len(rawLines)-1]
	}
	var out []string
	charsSeen := false
	for _, row := range rawLines {
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
	direction := "auto"
	justify := "auto"
	useReverse := false
	useFlip := false
	useStrip := false
	useNormalize := false

	var textArgs []string

	args := os.Args[1:]
	for i := 0; i < len(args); i++ {
		arg := args[i]
		if arg == "-f" && i+1 < len(args) {
			fontName = args[i+1]
			i++
		} else if strings.HasPrefix(arg, "--font=") {
			fontName = arg[len("--font="):]
		} else if arg == "--font" && i+1 < len(args) {
			fontName = args[i+1]
			i++
		} else if arg == "-w" && i+1 < len(args) {
			width, _ = strconv.Atoi(args[i+1])
			i++
		} else if strings.HasPrefix(arg, "--width=") {
			width, _ = strconv.Atoi(arg[len("--width="):])
		} else if arg == "--width" && i+1 < len(args) {
			width, _ = strconv.Atoi(args[i+1])
			i++
		} else if arg == "-j" && i+1 < len(args) {
			justify = args[i+1]
			i++
		} else if strings.HasPrefix(arg, "--justify=") {
			justify = arg[len("--justify="):]
		} else if arg == "--justify" && i+1 < len(args) {
			justify = args[i+1]
			i++
		} else if arg == "-D" && i+1 < len(args) {
			direction = args[i+1]
			i++
		} else if strings.HasPrefix(arg, "--direction=") {
			direction = arg[len("--direction="):]
		} else if arg == "--direction" && i+1 < len(args) {
			direction = args[i+1]
			i++
		} else if arg == "-r" || arg == "--reverse" {
			useReverse = true
		} else if arg == "-F" || arg == "--flip" {
			useFlip = true
		} else if arg == "-s" || arg == "--strip-surrounding-newlines" {
			useStrip = true
		} else if arg == "-n" || arg == "--normalize-surrounding-newlines" {
			useNormalize = true
		} else if arg == "-c" || arg == "--color" || arg == "-L" || arg == "--load" {
			i++
		} else if strings.HasPrefix(arg, "-c=") || strings.HasPrefix(arg, "--color=") ||
			strings.HasPrefix(arg, "-L=") || strings.HasPrefix(arg, "--load=") {
		} else if arg == "-l" || arg == "--list_fonts" || arg == "-i" || arg == "--info_font" {
		} else {
			textArgs = append(textArgs, arg)
		}
	}

	text := strings.Join(textArgs, " ")

	font, err := loadFont(fontName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: requested font '%s' not found.\n", fontName)
		os.Exit(1)
	}

	resolvedDirection := direction
	if resolvedDirection == "auto" {
		if font.PrintDirection == 1 {
			resolvedDirection = "right-to-left"
		} else {
			resolvedDirection = "left-to-right"
		}
	}

	resolvedJustify := justify
	if resolvedJustify == "auto" {
		if resolvedDirection == "left-to-right" {
			resolvedJustify = "left"
		} else {
			resolvedJustify = "right"
		}
	}

	builder := NewBuilder(text, font, resolvedDirection, width, resolvedJustify)
	r := builder.Build()

	if useReverse {
		r = reverseText(r)
	}
	if useFlip {
		r = flipText(r)
	}
	if useStrip {
		r = stripSurroundingNewlines(r)
	} else if useNormalize {
		r = normalizeSurroundingNewlines(r)
	}

	os.Stdout.WriteString(r)
	os.Stdout.WriteString("\n")
}
EOF

# 4. Remove all Python files under /workspace/repo
find /workspace/repo -type f -name "*.py" -delete
find /workspace/repo -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 5. Build the figlet binary
go build -o /tmp/figlet .
