#!/bin/bash
set -euo pipefail

cd /workspace/repo

# 1. Clean up Python files and legacy assets
find /workspace/repo -name "*.py" -delete
find /workspace/repo -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf /workspace/repo/.github /workspace/repo/doc /workspace/repo/tools /workspace/repo/test-fonts

# 2. Consolidate font files (.flf) into /workspace/repo/fonts
mkdir -p /workspace/repo/fonts
if [ -d /workspace/repo/pyfiglet/fonts ]; then
  cp -f /workspace/repo/pyfiglet/fonts/*.flf /workspace/repo/fonts/ 2>/dev/null || true
fi
if [ -d /workspace/repo/pyfiglet/fonts-standard ]; then
  cp -f /workspace/repo/pyfiglet/fonts-standard/*.flf /workspace/repo/fonts/ 2>/dev/null || true
fi

# Remove remaining pyfiglet source dir
rm -rf /workspace/repo/pyfiglet

# 3. Create go.mod
cat << 'EOF' > /workspace/repo/go.mod
module figlet

go 1.23
EOF

# 4. Create Go FIGlet implementation
cat << 'EOF' > /workspace/repo/main.go
package main

import (
	"embed"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"
	"unicode/utf8"
)

//go:embed fonts/*.flf
var embeddedFonts embed.FS

type Font struct {
	name           string
	hardBlank      rune
	height         int
	baseline       int
	maxLength      int
	oldLayout      int
	commentLines   int
	printDirection int
	smushMode      int
	chars          map[rune][]string
	width          map[rune]int
}

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

func loadFont(name string) (*Font, error) {
	// Try embedded font first
	data, err := embeddedFonts.ReadFile("fonts/" + name + ".flf")
	if err != nil {
		data, err = embeddedFonts.ReadFile("fonts/" + name + ".tlf")
	}
	if err != nil {
		// Fallback to disk
		data, err = os.ReadFile("fonts/" + name + ".flf")
		if err != nil {
			data, err = os.ReadFile(name + ".flf")
		}
	}
	if err != nil {
		return nil, fmt.Errorf("font %s not found: %w", name, err)
	}

	content := string(data)
	content = strings.ReplaceAll(content, "\r\n", "\n")
	content = strings.ReplaceAll(content, "\r", "\n")
	lines := strings.Split(content, "\n")

	if len(lines) == 0 {
		return nil, fmt.Errorf("empty font file")
	}

	header := lines[0]
	lines = lines[1:]

	if !strings.HasPrefix(header, "flf2a") && !strings.HasPrefix(header, "tlf2a") {
		return nil, fmt.Errorf("invalid magic in %s", name)
	}

	header = header[5:] // skip magic
	fields := strings.Fields(header)
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed header in %s", name)
	}

	hardBlankRune, _ := utf8.DecodeRuneInString(fields[0])
	height, _ := strconv.Atoi(fields[1])
	baseline, _ := strconv.Atoi(fields[2])
	maxLength, _ := strconv.Atoi(fields[3])
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
		hardBlank:      hardBlankRune,
		height:         height,
		baseline:       baseline,
		maxLength:      maxLength,
		oldLayout:      oldLayout,
		commentLines:   commentLines,
		printDirection: printDirection,
		smushMode:      fullLayout,
		chars:          make(map[rune][]string),
		width:          make(map[rune]int),
	}

	// Skip comments
	if len(lines) < commentLines {
		return nil, fmt.Errorf("unexpected EOF in comments")
	}
	lines = lines[commentLines:]

	readGlyph := func() (int, []string, bool) {
		if len(lines) < height {
			return 0, nil, false
		}
		var glyph []string
		maxWidth := 0
		var endRune rune
		for row := 0; row < height; row++ {
			line := lines[row]
			if row == 0 {
				trimmed := strings.TrimRight(line, " \t\r")
				if len(trimmed) > 0 {
					endRune, _ = utf8.DecodeLastRuneInString(trimmed)
				}
			}
			trimmed := strings.TrimRight(line, " \t\r")
			for strings.HasSuffix(trimmed, string(endRune)) {
				trimmed = strings.TrimSuffix(trimmed, string(endRune))
			}
			line = trimmed
			if len(line) > maxWidth {
				maxWidth = len(line)
			}
			glyph = append(glyph, line)
		}
		lines = lines[height:]
		return maxWidth, glyph, true
	}

	// Standard ASCII 32..126
	for code := 32; code < 127; code++ {
		w, glyph, ok := readGlyph()
		if !ok {
			break
		}
		if code == 32 || strings.Join(glyph, "") != "" {
			font.chars[rune(code)] = glyph
			font.width[rune(code)] = w
		}
	}

	// German characters: Ä Ö Ü ä ö ü ß
	germanRunes := []rune{'Ä', 'Ö', 'Ü', 'ä', 'ö', 'ü', 'ß'}
	for _, gr := range germanRunes {
		w, glyph, ok := readGlyph()
		if !ok {
			break
		}
		if strings.Join(glyph, "") != "" {
			font.chars[gr] = glyph
			font.width[gr] = w
		}
	}

	// Extended characters (only 0x hex tags matching pyfiglet)
	for len(lines) > 0 {
		tagLine := strings.TrimSpace(lines[0])
		lines = lines[1:]
		if tagLine == "" {
			continue
		}
		tagField := strings.Fields(tagLine)[0]
		var code int64
		var err error
		if strings.HasPrefix(strings.ToLower(tagField), "0x") {
			code, err = strconv.ParseInt(tagField[2:], 16, 64)
		} else if strings.HasPrefix(strings.ToLower(tagField), "-0x") {
			code, err = strconv.ParseInt("-"+tagField[3:], 16, 64)
		} else {
			continue
		}
		if err != nil {
			continue
		}
		w, glyph, ok := readGlyph()
		if !ok {
			break
		}
		if strings.Join(glyph, "") != "" {
			font.chars[rune(code)] = glyph
			font.width[rune(code)] = w
		}
	}

	return font, nil
}

func smushChars(left, right rune, font *Font, dir string, prevWidth, curWidth int) (rune, bool) {
	if left == ' ' {
		return right, true
	}
	if right == ' ' {
		return left, true
	}

	if prevWidth < 2 || curWidth < 2 {
		return 0, false
	}

	if (font.smushMode & SM_SMUSH) == 0 {
		return 0, false
	}

	// Universal overlapping (rule 0: bits 0-5 are 0)
	if (font.smushMode & 63) == 0 {
		if left == font.hardBlank {
			return right, true
		}
		if right == font.hardBlank {
			return left, true
		}
		if dir == "right-to-left" {
			return left, true
		}
		return right, true
	}

	if (font.smushMode & SM_HARDBLANK) != 0 {
		if left == font.hardBlank && right == font.hardBlank {
			return left, true
		}
	}

	if left == font.hardBlank || right == font.hardBlank {
		return 0, false
	}

	// Rule 1: equal character
	if (font.smushMode & SM_EQUAL) != 0 {
		if left == right {
			return left, true
		}
	}

	// Rule 2: underscore
	if (font.smushMode & SM_LOWLINE) != 0 {
		target := `|/\[]{}()<>`
		if left == '_' && strings.ContainsRune(target, right) {
			return right, true
		}
		if right == '_' && strings.ContainsRune(target, left) {
			return left, true
		}
	}

	// Rule 3: hierarchy
	if (font.smushMode & SM_HIERARCHY) != 0 {
		classOf := func(r rune) int {
			switch r {
			case '|':
				return 1
			case '/', '\\':
				return 2
			case '[', ']':
				return 3
			case '{', '}':
				return 4
			case '(', ')':
				return 5
			case '<', '>':
				return 6
			default:
				return 0
			}
		}
		cLeft := classOf(left)
		cRight := classOf(right)
		if cLeft > 0 && cRight > 0 && cLeft != cRight {
			if cLeft > cRight {
				return left, true
			}
			return right, true
		}
	}

	// Rule 4: opposite pair
	if (font.smushMode & SM_PAIR) != 0 {
		s1 := string(left) + string(right)
		s2 := string(right) + string(left)
		if s1 == "[]" || s1 == "{}" || s1 == "()" || s2 == "[]" || s2 == "{}" || s2 == "()" {
			return '|', true
		}
	}

	// Rule 5: big X
	if (font.smushMode & SM_BIGX) != 0 {
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

func smushAmount(buffer, curChar []string, font *Font, dir string, curWidth, prevWidth int) int {
	if (font.smushMode & (SM_SMUSH | SM_KERN)) == 0 {
		return 0
	}

	maxSmush := curWidth
	for row := 0; row < font.height; row++ {
		lineLeft := buffer[row]
		lineRight := curChar[row]
		if dir == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}

		linebd := len(strings.TrimRight(lineLeft, " ")) - 1
		if linebd < 0 {
			linebd = 0
		}

		var ch1 rune
		if linebd < len(lineLeft) {
			ch1 = rune(lineLeft[linebd])
		}

		charbd := len(lineRight) - len(strings.TrimLeft(lineRight, " "))
		var ch2 rune
		if charbd < len(lineRight) {
			ch2 = rune(lineRight[charbd])
		}

		amt := charbd + len(lineLeft) - 1 - linebd
		if ch1 == 0 || ch1 == ' ' {
			amt++
		} else if ch2 != 0 {
			if _, ok := smushChars(ch1, ch2, font, dir, prevWidth, curWidth); ok {
				amt++
			}
		}

		if amt < maxSmush {
			maxSmush = amt
		}
	}

	return maxSmush
}

func smushRow(lineLeft, lineRight string, maxSmush int, font *Font, dir string, prevWidth, curWidth int) (string, string) {
	addLeft := lineLeft
	addRight := lineRight
	if dir == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}

	leftRunes := []rune(addLeft)
	rightRunes := []rune(addRight)

	for i := 0; i < maxSmush; i++ {
		idx := len(leftRunes) - maxSmush + i
		var leftRune rune
		if idx >= 0 && idx < len(leftRunes) {
			leftRune = leftRunes[idx]
		}
		var rightRune rune
		if i < len(rightRunes) {
			rightRune = rightRunes[i]
		}
		smushed, ok := smushChars(leftRune, rightRune, font, dir, prevWidth, curWidth)
		if ok && idx >= 0 && idx < len(leftRunes) {
			leftRunes[idx] = smushed
		}
	}

	addLeft = string(leftRunes)
	return addLeft, addRight
}

func cloneBuffer(buf []string) []string {
	res := make([]string, len(buf))
	copy(res, buf)
	return res
}

func justifyBuffer(buf []string, justify string, termWidth, height int) []string {
	res := make([]string, height)
	if justify == "right" {
		for row := 0; row < height; row++ {
			pad := termWidth - len(buf[row]) - 1
			if pad > 0 {
				res[row] = strings.Repeat(" ", pad) + buf[row]
			} else {
				res[row] = buf[row]
			}
		}
	} else if justify == "center" {
		for row := 0; row < height; row++ {
			pad := (termWidth - len(buf[row])) / 2
			if pad > 0 {
				res[row] = strings.Repeat(" ", pad) + buf[row]
			} else {
				res[row] = buf[row]
			}
		}
	} else {
		copy(res, buf)
	}
	return res
}

var reverseMap = [256]byte{
	0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
	0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f,
	' ', '!', '"', '#', '$', '%', '&', '\'', ')', '(', '*', '+', ',', '-', '.', '\\',
	'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '>', '=', '<', '?',
	'@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
	'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', ']', '/', '[', '^', '_',
	'`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
	'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '}', '|', '{', '~', 0x7f,
	0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f,
	0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0x9b, 0x9c, 0x9d, 0x9e, 0x9f,
	0xa0, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xae, 0xaf,
	0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf,
	0xc0, 0xc1, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xcb, 0xcc, 0xcd, 0xce, 0xcf,
	0xd0, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7, 0xd8, 0xd9, 0xda, 0xdb, 0xdc, 0xdd, 0xde, 0xdf,
	0xe0, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9, 0xea, 0xeb, 0xec, 0xed, 0xee, 0xef,
	0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9, 0xfa, 0xfb, 0xfc, 0xfd, 0xfe, 0xff,
}

var flipMap = [256]byte{
	0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
	0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f,
	' ', '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '\\',
	'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
	'@', 'V', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'W', 'N', 'O',
	'b', 'Q', 'b', 'S', 'T', 'U', 'A', 'M', 'X', 'Y', 'Z', '[', '/', ']', 'v', '-',
	'`', 'a', 'P', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'w', 'n', 'o',
	'p', 'q', 'r', 's', 't', 'u', '^', 'm', 'x', 'y', 'z', '{', '|', '}', '~', 0x7f,
	0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f,
	0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0x9b, 0x9c, 0x9d, 0x9e, 0x9f,
	0xa0, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xae, 0xaf,
	0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf,
	0xc0, 0xc1, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xcb, 0xcc, 0xcd, 0xce, 0xcf,
	0xd0, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7, 0xd8, 0xd9, 0xda, 0xdb, 0xdc, 0xdd, 0xde, 0xdf,
	0xe0, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9, 0xea, 0xeb, 0xec, 0xed, 0xee, 0xef,
	0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9, 0xfa, 0xfb, 0xfc, 0xfd, 0xfe, 0xff,
}

func reverseRow(row string) string {
	b := []byte(row)
	for i := 0; i < len(b); i++ {
		b[i] = reverseMap[b[i]]
	}
	for i, j := 0, len(b)-1; i < j; i, j = i+1, j-1 {
		b[i], b[j] = b[j], b[i]
	}
	return string(b)
}

func flipRow(row string) string {
	b := []byte(row)
	for i := 0; i < len(b); i++ {
		b[i] = flipMap[b[i]]
	}
	return string(b)
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
	res := strings.Join(out, "\n") + "\n"
	return strings.TrimRight(res, " \t\r\n")
}

func main() {
	fontFlag := flag.String("f", "standard", "font name")
	widthFlag := flag.Int("w", 80, "column width")
	justifyFlag := flag.String("j", "auto", "justification")
	dirFlag := flag.String("D", "auto", "direction")
	reverseFlag := flag.Bool("r", false, "reverse")
	flipFlag := flag.Bool("F", false, "flip")
	stripFlag := flag.Bool("s", false, "strip surrounding newlines")
	normFlag := flag.Bool("n", false, "normalize surrounding newlines")

	flag.Parse()

	args := flag.Args()
	if len(args) == 0 {
		os.Exit(1)
	}

	text := strings.Join(args, " ")

	font, err := loadFont(*fontFlag)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: requested font %q not found.\n", *fontFlag)
		os.Exit(1)
	}

	dir := *dirFlag
	if dir == "auto" {
		if font.printDirection == 1 {
			dir = "right-to-left"
		} else {
			dir = "left-to-right"
		}
	}

	justify := *justifyFlag
	if justify == "auto" {
		if dir == "left-to-right" {
			justify = "left"
		} else {
			justify = "right"
		}
	}

	width := *widthFlag

	runes := []rune(text)
	buffer := make([]string, font.height)
	var product [][]string

	type blankMarker struct {
		buf  []string
		iter int
	}
	var blankMarkers []blankMarker

	prevCharWidth := 0
	curCharWidth := 0
	maxSmush := 0

	cutBufferCommon := func(curChar []string) {
		buffer = make([]string, font.height)
		blankMarkers = nil
		prevCharWidth = 0
		if curChar != nil {
			maxSmush = smushAmount(buffer, curChar, font, dir, curCharWidth, prevCharWidth)
		}
	}

	cutBufferAtLastBlank := func(savedBuf []string, savedIter int) int {
		product = append(product, savedBuf)
		cutBufferCommon(nil)
		return savedIter
	}

	cutBufferAtLastChar := func(iter int) int {
		product = append(product, buffer)
		cutBufferCommon(nil)
		return iter - 1
	}

	handleNewLine := func(iter int) int {
		if len(blankMarkers) > 0 {
			last := blankMarkers[len(blankMarkers)-1]
			blankMarkers = blankMarkers[:len(blankMarkers)-1]
			return cutBufferAtLastBlank(last.buf, last.iter)
		}
		return cutBufferAtLastChar(iter)
	}

	for iter := 0; iter < len(runes); iter++ {
		r := runes[iter]
		if r == '\n' {
			blankMarkers = append(blankMarkers, blankMarker{cloneBuffer(buffer), iter})
			iter = handleNewLine(iter)
			continue
		}

		curChar, exists := font.chars[r]
		if !exists {
			continue
		}

		curCharWidth = font.width[r]
		if width < curCharWidth {
			return
		}

		maxSmush = smushAmount(buffer, curChar, font, dir, curCharWidth, prevCharWidth)
		currentTotalWidth := len(buffer[0]) + curCharWidth - maxSmush

		if r == ' ' {
			blankMarkers = append(blankMarkers, blankMarker{cloneBuffer(buffer), iter})
		}

		if currentTotalWidth >= width {
			iter = handleNewLine(iter)
		} else {
			for row := 0; row < font.height; row++ {
				addLeft, addRight := smushRow(buffer[row], curChar[row], maxSmush, font, dir, prevCharWidth, curCharWidth)
				buffer[row] = addLeft + addRight[maxSmush:]
			}
		}

		prevCharWidth = curCharWidth
	}

	if buffer[0] != "" {
		product = append(product, buffer)
	}

	var sb strings.Builder
	for _, buf := range product {
		buf = justifyBuffer(buf, justify, width, font.height)
		for _, row := range buf {
			row = strings.ReplaceAll(row, string(font.hardBlank), " ")
			sb.WriteString(row)
			sb.WriteString("\n")
		}
	}

	result := sb.String()

	if *reverseFlag {
		lines := strings.Split(result, "\n")
		if len(lines) > 0 && lines[len(lines)-1] == "" {
			lines = lines[:len(lines)-1]
		}
		for i, l := range lines {
			lines[i] = reverseRow(l)
		}
		result = strings.Join(lines, "\n") + "\n"
	}

	if *flipFlag {
		lines := strings.Split(result, "\n")
		if len(lines) > 0 && lines[len(lines)-1] == "" {
			lines = lines[:len(lines)-1]
		}
		var flipped []string
		for i := len(lines) - 1; i >= 0; i-- {
			flipped = append(flipped, flipRow(lines[i]))
		}
		result = strings.Join(flipped, "\n") + "\n"
	}

	if *stripFlag {
		result = stripSurroundingNewlines(result)
	} else if *normFlag {
		result = "\n" + stripSurroundingNewlines(result) + "\n"
	}

	os.Stdout.WriteString(result + "\n")
}
EOF

# 5. Build and verify
go build ./...
go build -o /tmp/figlet .

echo "Solution built successfully at /tmp/figlet"
