#!/bin/bash
set -euo pipefail

cd /workspace/repo

# 1. Ensure fonts directory exists and contains all .flf font files
mkdir -p /workspace/repo/fonts
if [ -d /workspace/repo/pyfiglet/fonts ]; then
    cp -n /workspace/repo/pyfiglet/fonts/*.flf /workspace/repo/fonts/ 2>/dev/null || true
fi
if [ -d /workspace/repo/pyfiglet/fonts-standard ]; then
    cp -n /workspace/repo/pyfiglet/fonts-standard/*.flf /workspace/repo/fonts/ 2>/dev/null || true
fi

# 2. Write go.mod
cat << 'EOF' > /workspace/repo/go.mod
module figlet

go 1.23
EOF

# 3. Write Go source
cat << 'EOF' > /workspace/repo/main.go
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

type Font struct {
	name           string
	height         int
	hardBlank      string
	printDirection int
	smushMode      int
	chars          map[int][]string
	width          map[int]int
}

func loadFontData(name string) (string, error) {
	clean := strings.TrimSuffix(name, ".flf")
	clean = strings.TrimSuffix(clean, ".tlf")

	embeddedPath := "fonts/" + clean + ".flf"
	if data, err := embeddedFonts.ReadFile(embeddedPath); err == nil {
		return string(data), nil
	}

	searchPaths := []string{
		filepath.Join("/workspace/repo/fonts", clean+".flf"),
		filepath.Join("/workspace/repo/pyfiglet/fonts", clean+".flf"),
		filepath.Join("/workspace/repo/pyfiglet/fonts-standard", clean+".flf"),
		clean + ".flf",
		filepath.Join("fonts", clean+".flf"),
	}
	for _, p := range searchPaths {
		if data, err := os.ReadFile(p); err == nil {
			return string(data), nil
		}
	}

	return "", fmt.Errorf("pyfiglet error: requested font %q not found.", name)
}

func parseFont(data string, name string) (*Font, error) {
	data = strings.ReplaceAll(data, "\u0085", " ")
	data = strings.ReplaceAll(data, "\u2028", " ")
	data = strings.ReplaceAll(data, "\u2029", " ")

	data = strings.ReplaceAll(data, "\r\n", "\n")
	data = strings.ReplaceAll(data, "\r", "\n")
	lines := strings.Split(data, "\n")

	if len(lines) == 0 {
		return nil, fmt.Errorf("empty font")
	}

	header := lines[0]
	if len(header) < 5 || (header[:4] != "flf2" && header[:4] != "tlf2") {
		return nil, fmt.Errorf("invalid magic number: %s", header)
	}

	header = header[5:]
	fields := strings.Fields(header)
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed header")
	}

	hardBlank := fields[0]
	height, _ := strconv.Atoi(fields[1])
	oldLayout, _ := strconv.Atoi(fields[4])
	commentLines, _ := strconv.Atoi(fields[5])

	printDirection := 0
	if len(fields) > 6 {
		printDirection, _ = strconv.Atoi(fields[6])
	}

	fullLayout := -1
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

	font := &Font{
		name:           name,
		height:         height,
		hardBlank:      hardBlank,
		printDirection: printDirection,
		smushMode:      fullLayout,
		chars:          make(map[int][]string),
		width:          make(map[int]int),
	}

	lines = lines[1+commentLines:]

	readChar := func() (int, []string) {
		if len(lines) < height {
			return 0, nil
		}
		charLines := make([]string, height)
		for row := 0; row < height; row++ {
			charLines[row] = lines[row]
		}
		lines = lines[height:]

		row0 := strings.TrimRight(charLines[0], " \t\r")
		if len(row0) == 0 {
			return 0, charLines
		}
		endChar := row0[len(row0)-1]

		maxWidth := 0
		for row := 0; row < height; row++ {
			l := strings.TrimRight(charLines[row], " \t\r")
			count := 0
			for count < 2 && len(l) > 0 && l[len(l)-1] == endChar {
				l = l[:len(l)-1]
				count++
			}
			charLines[row] = l
			if len(l) > maxWidth {
				maxWidth = len(l)
			}
		}
		return maxWidth, charLines
	}

	// 1. Standard ASCII 32..126
	for i := 32; i < 127; i++ {
		w, letter := readChar()
		allEmpty := true
		for _, row := range letter {
			if len(row) > 0 {
				allEmpty = false
				break
			}
		}
		if i == 32 || !allEmpty {
			font.chars[i] = letter
			font.width[i] = w
		}
	}

	// 2. German Umlaute: Ä, Ö, Ü, ä, ö, ü, ß
	german := []rune{'Ä', 'Ö', 'Ü', 'ä', 'ö', 'ü', 'ß'}
	if len(lines) >= height {
		for _, r := range german {
			if len(lines) < height {
				break
			}
			w, letter := readChar()
			allEmpty := true
			for _, row := range letter {
				if len(row) > 0 {
					allEmpty = false
					break
				}
			}
			if !allEmpty {
				font.chars[int(r)] = letter
				font.width[int(r)] = w
			}
		}
	}

	// 3. Extended characters
	for len(lines) > 0 {
		line := strings.TrimSpace(lines[0])
		lines = lines[1:]
		if len(line) == 0 {
			continue
		}
		parts := strings.SplitN(line, " ", 2)
		idStr := parts[0]
		if strings.HasPrefix(strings.ToLower(idStr), "0x") {
			val, err := strconv.ParseInt(idStr[2:], 16, 64)
			if err == nil {
				w, letter := readChar()
				allEmpty := true
				for _, row := range letter {
					if len(row) > 0 {
						allEmpty = false
						break
					}
				}
				if !allEmpty {
					font.chars[int(val)] = letter
					font.width[int(val)] = w
				}
			}
		}
	}

	return font, nil
}

func smushChars(left, right byte, font *Font, prevWidth, curWidth int, direction string) (byte, bool) {
	if left == ' ' {
		return right, true
	}
	if right == ' ' {
		return left, true
	}

	if prevWidth < 2 || curWidth < 2 {
		return 0, false
	}

	if (font.smushMode & 128) == 0 {
		return 0, false
	}

	hard := byte(font.hardBlank[0])

	if (font.smushMode & 63) == 0 {
		if left == hard {
			return right, true
		}
		if right == hard {
			return left, true
		}
		if direction == "right-to-left" {
			return left, true
		}
		return right, true
	}

	if (font.smushMode & 32) != 0 {
		if left == hard && right == hard {
			return left, true
		}
	}
	if left == hard || right == hard {
		return 0, false
	}

	if (font.smushMode & 1) != 0 {
		if left == right {
			return left, true
		}
	}

	if (font.smushMode & 2) != 0 {
		const set = "|/\\[]{}()<>"
		if left == '_' && strings.IndexByte(set, right) >= 0 {
			return right, true
		}
		if right == '_' && strings.IndexByte(set, left) >= 0 {
			return left, true
		}
	}

	if (font.smushMode & 4) != 0 {
		type pair struct{ a, b string }
		pairs := []pair{
			{"|", "/\\[]{}()<>"},
			{"/\\", "[]{}()<>"},
			{"[]", "{}()<>"},
			{"{}", "()<>"},
			{"()", "<>"},
		}
		for _, p := range pairs {
			if strings.IndexByte(p.a, left) >= 0 && strings.IndexByte(p.b, right) >= 0 {
				return right, true
			}
			if strings.IndexByte(p.a, right) >= 0 && strings.IndexByte(p.b, left) >= 0 {
				return left, true
			}
		}
	}

	if (font.smushMode & 8) != 0 {
		s := string([]byte{left, right})
		if s == "[]" || s == "][" || s == "{}" || s == "}{" || s == "()" || s == ")(" {
			return '|', true
		}
	}

	if (font.smushMode & 16) != 0 {
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

func smushAmount(buffer []string, curChar []string, font *Font, curCharWidth, prevCharWidth int, direction string) int {
	if (font.smushMode & (64 | 128)) == 0 {
		return 0
	}

	maxSmush := curCharWidth
	for row := 0; row < font.height; row++ {
		lineLeft := buffer[row]
		lineRight := curChar[row]
		if direction == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}

		trimmedLeft := strings.TrimRight(lineLeft, " ")
		linebd := len(trimmedLeft) - 1
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

		trimmedRight := strings.TrimLeft(lineRight, " ")
		charbd := len(lineRight) - len(trimmedRight)
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
			if _, ok := smushChars(ch1, ch2, font, prevCharWidth, curCharWidth, direction); ok {
				amt++
			}
		}

		if amt < maxSmush {
			maxSmush = amt
		}
	}
	return maxSmush
}

func smushRow(bufferRow, curCharRow string, maxSmush int, font *Font, prevWidth, curWidth int, direction string) (string, string) {
	addLeft := []byte(bufferRow)
	addRight := []byte(curCharRow)

	if direction == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}

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
		if smushed, ok := smushChars(left, right, font, prevWidth, curWidth, direction); ok {
			if idx >= 0 && idx < len(addLeft) {
				addLeft[idx] = smushed
			}
		}
	}
	return string(addLeft), string(addRight)
}

type blankMarker struct {
	buffer   []string
	iterator int
}

type FigletBuilder struct {
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
	blankMarkers      []blankMarker
	productQueue      [][]string
	buffer            []string
}

func (b *FigletBuilder) getCharAt(i int) []string {
	if i < 0 || i >= len(b.text) {
		return nil
	}
	c := int(b.text[i])
	return b.font.chars[c]
}

func (b *FigletBuilder) getCharWidthAt(i int) int {
	if i < 0 || i >= len(b.text) {
		return 0
	}
	c := int(b.text[i])
	return b.font.width[c]
}

func (b *FigletBuilder) getCurChar() []string {
	return b.getCharAt(b.iterator)
}

func (b *FigletBuilder) getCurWidth() int {
	return b.getCharWidthAt(b.iterator)
}

func (b *FigletBuilder) currentSmushAmount(curChar []string) int {
	return smushAmount(b.buffer, curChar, b.font, b.curCharWidth, b.prevCharWidth, b.direction)
}

func (b *FigletBuilder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([]string, b.font.height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	curChar := b.getCurChar()
	if curChar == nil {
		return
	}
	b.maxSmush = b.currentSmushAmount(curChar)
}

func (b *FigletBuilder) handleNewLine() {
	if len(b.blankMarkers) > 0 {
		marker := b.blankMarkers[len(b.blankMarkers)-1]
		b.blankMarkers = b.blankMarkers[:len(b.blankMarkers)-1]
		b.productQueue = append(b.productQueue, marker.buffer)
		b.iterator = marker.iterator
		b.cutBufferCommon()
	} else {
		b.productQueue = append(b.productQueue, b.buffer)
		b.iterator--
		b.cutBufferCommon()
	}
}

func (b *FigletBuilder) addCharToProduct() {
	curChar := b.getCurChar()

	if b.text[b.iterator] == '\n' {
		bufCopy := make([]string, b.font.height)
		copy(bufCopy, b.buffer)
		b.blankMarkers = append(b.blankMarkers, blankMarker{buffer: bufCopy, iterator: b.iterator})
		b.handleNewLine()
		return
	}

	if curChar == nil {
		return
	}

	charWidth := b.getCurWidth()
	if b.width < charWidth {
		fmt.Fprintf(os.Stderr, "Width is not enough to print this character\n")
		os.Exit(1)
	}

	b.curCharWidth = charWidth
	b.maxSmush = b.currentSmushAmount(curChar)

	b.currentTotalWidth = len(b.buffer[0]) + b.curCharWidth - b.maxSmush

	if b.text[b.iterator] == ' ' {
		bufCopy := make([]string, b.font.height)
		copy(bufCopy, b.buffer)
		b.blankMarkers = append(b.blankMarkers, blankMarker{buffer: bufCopy, iterator: b.iterator})
	}

	if b.currentTotalWidth >= b.width {
		b.handleNewLine()
	} else {
		for row := 0; row < b.font.height; row++ {
			addLeft, addRight := smushRow(b.buffer[row], curChar[row], b.maxSmush, b.font, b.prevCharWidth, b.curCharWidth, b.direction)
			var rightPart string
			if b.maxSmush < len(addRight) {
				rightPart = addRight[b.maxSmush:]
			}
			b.buffer[row] = addLeft + rightPart
		}
	}

	b.prevCharWidth = b.curCharWidth
}

func (b *FigletBuilder) returnProduct() string {
	if b.buffer[0] != "" {
		b.productQueue = append(b.productQueue, b.buffer)
	}
	var sb strings.Builder
	for _, buf := range b.productQueue {
		justified := justifyString(buf, b.justify, b.width, b.font.height)
		replaced := replaceHardblanks(justified, b.font.hardBlank)
		sb.WriteString(replaced)
	}
	return sb.String()
}

func justifyString(buffer []string, justify string, width, height int) []string {
	bufCopy := make([]string, height)
	copy(bufCopy, buffer)
	if justify == "right" {
		for row := 0; row < height; row++ {
			pad := width - len(bufCopy[row]) - 1
			if pad > 0 {
				bufCopy[row] = strings.Repeat(" ", pad) + bufCopy[row]
			}
		}
	} else if justify == "center" {
		for row := 0; row < height; row++ {
			pad := (width - len(bufCopy[row])) / 2
			if pad > 0 {
				bufCopy[row] = strings.Repeat(" ", pad) + bufCopy[row]
			}
		}
	}
	return bufCopy
}

func replaceHardblanks(buffer []string, hardBlank string) string {
	joined := strings.Join(buffer, "\n") + "\n"
	return strings.ReplaceAll(joined, hardBlank, " ")
}

var reverseMap [256]byte
var flipMap [256]byte

func init() {
	for i := 0; i < 256; i++ {
		reverseMap[i] = byte(i)
		flipMap[i] = byte(i)
	}
	reverseMap['('] = ')'
	reverseMap[')'] = '('
	reverseMap['/'] = '\\'
	reverseMap['\\'] = '/'
	reverseMap['<'] = '>'
	reverseMap['>'] = '<'
	reverseMap['['] = ']'
	reverseMap[']'] = '['
	reverseMap['{'] = '}'
	reverseMap['}'] = '{'

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
	flipMap['v'] = '^'
	flipMap['^'] = 'v'
	flipMap['_'] = '-'
}

func figletReverse(s string) string {
	lines := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
	out := make([]string, len(lines))
	for i, row := range lines {
		b := []byte(row)
		n := len(b)
		rev := make([]byte, n)
		for j := 0; j < n; j++ {
			rev[n-1-j] = reverseMap[b[j]]
		}
		out[i] = string(rev)
	}
	return strings.Join(out, "\n") + "\n"
}

func figletFlip(s string) string {
	lines := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
	out := make([]string, len(lines))
	for i := len(lines) - 1; i >= 0; i-- {
		b := []byte(lines[i])
		flipped := make([]byte, len(b))
		for j := 0; j < len(b); j++ {
			flipped[j] = flipMap[b[j]]
		}
		out[len(lines)-1-i] = string(flipped)
	}
	return strings.Join(out, "\n") + "\n"
}

func stripSurroundingNewlines(s string) string {
	lines := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
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

func isShortFlags(s string) bool {
	for _, c := range s {
		if c != 'r' && c != 'F' && c != 's' && c != 'n' {
			return false
		}
	}
	return true
}

func main() {
	fontName := "standard"
	width := 80
	justify := "auto"
	direction := "auto"
	reverse := false
	flip := false
	strip := false
	normalize := false
	var textParts []string

	args := os.Args[1:]
	for i := 0; i < len(args); i++ {
		arg := args[i]
		if arg == "-f" || arg == "--font" {
			if i+1 < len(args) {
				i++
				fontName = args[i]
			}
		} else if strings.HasPrefix(arg, "-f=") || strings.HasPrefix(arg, "--font=") {
			fontName = arg[strings.Index(arg, "=")+1:]
		} else if arg == "-w" || arg == "--width" {
			if i+1 < len(args) {
				i++
				width, _ = strconv.Atoi(args[i])
			}
		} else if strings.HasPrefix(arg, "-w=") || strings.HasPrefix(arg, "--width=") {
			width, _ = strconv.Atoi(arg[strings.Index(arg, "=")+1:])
		} else if arg == "-j" || arg == "--justify" {
			if i+1 < len(args) {
				i++
				justify = args[i]
			}
		} else if strings.HasPrefix(arg, "-j=") || strings.HasPrefix(arg, "--justify=") {
			justify = arg[strings.Index(arg, "=")+1:]
		} else if arg == "-D" || arg == "--direction" {
			if i+1 < len(args) {
				i++
				direction = args[i]
			}
		} else if strings.HasPrefix(arg, "-D=") || strings.HasPrefix(arg, "--direction=") {
			direction = arg[strings.Index(arg, "=")+1:]
		} else if arg == "-r" || arg == "--reverse" {
			reverse = true
		} else if arg == "-F" || arg == "--flip" {
			flip = true
		} else if arg == "-s" || arg == "--strip-surrounding-newlines" {
			strip = true
		} else if arg == "-n" || arg == "--normalize-surrounding-newlines" {
			normalize = true
		} else if strings.HasPrefix(arg, "-") && len(arg) > 1 && !strings.Contains(arg, "=") && isShortFlags(arg[1:]) {
			for _, c := range arg[1:] {
				switch c {
				case 'r':
					reverse = true
				case 'F':
					flip = true
				case 's':
					strip = true
				case 'n':
					normalize = true
				}
			}
		} else {
			textParts = append(textParts, arg)
		}
	}

	if len(textParts) == 0 {
		os.Exit(1)
	}

	text := strings.Join(textParts, " ")

	fontData, err := loadFontData(fontName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: requested font %q not found.\n", fontName)
		os.Exit(1)
	}

	font, err := parseFont(fontData, fontName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error parsing font %s: %v\n", fontName, err)
		os.Exit(1)
	}

	effDir := direction
	if effDir == "auto" {
		if font.printDirection == 1 {
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

	b := &FigletBuilder{
		text:      []rune(text),
		direction: effDir,
		width:     width,
		font:      font,
		justify:   effJust,
		buffer:    make([]string, font.height),
	}

	for b.iterator < len(b.text) {
		b.addCharToProduct()
		b.iterator++
	}

	r := b.returnProduct()
	if reverse {
		r = figletReverse(r)
	}
	if flip {
		r = figletFlip(r)
	}
	if strip {
		r = stripSurroundingNewlines(r)
	} else if normalize {
		r = normalizeSurroundingNewlines(r)
	}

	os.Stdout.WriteString(r)
	os.Stdout.WriteString("\n")
}
EOF

# 4. Remove all .py files under /workspace/repo
find /workspace/repo -type f -name "*.py" -delete

# 5. Check that go build ./... and go build -o /tmp/figlet . both succeed
cd /workspace/repo
go build ./...
go build -o /tmp/figlet .
