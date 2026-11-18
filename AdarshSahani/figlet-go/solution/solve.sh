#!/bin/bash
set -euo pipefail

cd /workspace/repo
mkdir -p fonts
cp pyfiglet/fonts/*.flf fonts/

cat > go.mod <<'GO_MOD'
module figlet

go 1.23
GO_MOD

cat > main.go <<'GO_SOURCE'
package main

import (
	"embed"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"unicode"
)

//go:embed fonts/*.flf
var fontFiles embed.FS

type Font struct {
	height         int
	hardBlank      rune
	printDirection *int
	smushMode      int
	chars          map[rune][]string
	widths         map[rune]int
}

type blankMarker struct {
	buffer   []string
	iterator int
}

type Builder struct {
	text              []rune
	font              *Font
	direction         string
	width             int
	justify           string
	iterator          int
	maxSmush          int
	curCharWidth      int
	prevCharWidth     int
	currentTotalWidth int
	blankMarkers      []blankMarker
	buffer            []string
	product           [][]string
}

func main() {
	fontName, width, justify, direction, reverse, flip, strip, normalize, text, err := parseArgs(os.Args[1:])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	font, err := loadFont(fontName)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if direction == "auto" {
		if font.printDirection != nil && *font.printDirection == 1 {
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
	result, err := renderText(text, font, direction, width, justify)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if reverse {
		result = reverseArt(result)
	}
	if flip {
		result = flipArt(result)
	}
	if strip {
		result = stripSurroundingNewlines(result)
	} else if normalize {
		result = "\n" + stripSurroundingNewlines(result) + "\n"
	}
	_, _ = os.Stdout.Write([]byte(result + "\n"))
}

func parseArgs(args []string) (font string, width int, justify, direction string, reverse, flip, strip, normalize bool, text string, err error) {
	font, width, justify, direction = "standard", 80, "auto", "auto"
	var words []string
	for i := 0; i < len(args); i++ {
		arg := args[i]
		if arg == "--" {
			words = append(words, args[i+1:]...)
			break
		}
		name, value, hasValue := strings.Cut(arg, "=")
		switch name {
		case "-f", "--font":
			if !hasValue {
				i++
				if i >= len(args) {
					return "", 0, "", "", false, false, false, false, "", fmt.Errorf("%s requires a font", name)
				}
				value = args[i]
			}
			font = value
		case "-w", "--width":
			if !hasValue {
				i++
				if i >= len(args) {
					return "", 0, "", "", false, false, false, false, "", fmt.Errorf("%s requires a width", name)
				}
				value = args[i]
			}
			width, err = strconv.Atoi(value)
			if err != nil {
				return "", 0, "", "", false, false, false, false, "", fmt.Errorf("invalid width %q", value)
			}
		case "-j", "--justify":
			if !hasValue {
				i++
				if i >= len(args) {
					return "", 0, "", "", false, false, false, false, "", fmt.Errorf("%s requires a value", name)
				}
				value = args[i]
			}
			justify = value
		case "-D", "--direction":
			if !hasValue {
				i++
				if i >= len(args) {
					return "", 0, "", "", false, false, false, false, "", fmt.Errorf("%s requires a value", name)
				}
				value = args[i]
			}
			direction = value
		case "-r", "--reverse":
			reverse = true
		case "-F", "--flip":
			flip = true
		case "-s", "--strip-surrounding-newlines":
			strip = true
		case "-n", "--normalize-surrounding-newlines":
			normalize = true
		default:
			words = append(words, arg)
		}
	}
	text = strings.Join(words, " ")
	return
}

func loadFont(name string) (*Font, error) {
	if data, err := os.ReadFile(name); err == nil {
		return parseFont(data, name)
	}
	base := filepath.Base(name)
	if filepath.Ext(base) == "" {
		base += ".flf"
	}
	data, err := fs.ReadFile(fontFiles, "fonts/"+base)
	if err != nil {
		return nil, fmt.Errorf("font not found: %s", name)
	}
	return parseFont(data, name)
}

func parseFont(data []byte, name string) (*Font, error) {
	contents := string(data)
	contents = strings.NewReplacer("\u0085", " ", "\u2028", " ", "\u2029", " ").Replace(contents)
	contents = strings.ReplaceAll(contents, "\r\n", "\n")
	contents = strings.ReplaceAll(contents, "\r", "\n")
	lines := strings.Split(contents, "\n")
	if len(lines) > 0 && lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	if len(lines) == 0 {
		return nil, fmt.Errorf("empty font: %s", name)
	}
	header := []rune(lines[0])
	if len(header) < 5 || (header[0] != 'f' && header[0] != 't') || string(header[1:4]) != "lf2" {
		return nil, fmt.Errorf("invalid FIGlet font: %s", name)
	}
	fields := strings.Fields(string(header[5:]))
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed FIGlet header: %s", name)
	}
	ints := make([]int, 5)
	for i := range ints {
		v, err := strconv.Atoi(fields[i+1])
		if err != nil {
			return nil, fmt.Errorf("malformed FIGlet header: %s", name)
		}
		ints[i] = v
	}
	font := &Font{
		height:    ints[0],
		hardBlank: []rune(fields[0])[0],
		chars:     make(map[rune][]string),
		widths:    make(map[rune]int),
	}
	oldLayout, commentLines := ints[3], ints[4]
	if len(fields) > 6 {
		v, err := strconv.Atoi(fields[6])
		if err != nil {
			return nil, fmt.Errorf("malformed print direction in %s", name)
		}
		font.printDirection = &v
	}
	if len(fields) > 7 {
		v, err := strconv.Atoi(fields[7])
		if err != nil {
			return nil, fmt.Errorf("malformed layout in %s", name)
		}
		font.smushMode = v
	} else if oldLayout == 0 {
		font.smushMode = 64
	} else if oldLayout < 0 {
		font.smushMode = 0
	} else {
		font.smushMode = (oldLayout & 31) | 128
	}
	lines = lines[1:]
	if commentLines < 0 || commentLines > len(lines) {
		return nil, fmt.Errorf("invalid comment count in %s", name)
	}
	lines = lines[commentLines:]

	popLine := func() (string, error) {
		if len(lines) == 0 {
			return "", fmt.Errorf("truncated glyph data in %s", name)
		}
		line := lines[0]
		lines = lines[1:]
		return line, nil
	}
	readGlyph := func() ([]string, int, error) {
		first, err := popLine()
		if err != nil {
			return nil, 0, err
		}
		trimmed := strings.TrimRightFunc(first, unicode.IsSpace)
		endRunes := []rune(trimmed)
		if len(endRunes) == 0 {
			return nil, 0, fmt.Errorf("missing glyph end marker in %s", name)
		}
		endMarker := endRunes[len(endRunes)-1]
		rows := make([]string, 0, font.height)
		maxWidth := 0
		process := func(line string) string {
			r := []rune(strings.TrimRightFunc(line, unicode.IsSpace))
			if len(r) > 0 && r[len(r)-1] == endMarker {
				r = r[:len(r)-1]
				if len(r) > 0 && r[len(r)-1] == endMarker {
					r = r[:len(r)-1]
				}
			}
			return string(r)
		}
		line := process(first)
		rows = append(rows, line)
		maxWidth = len([]rune(line))
		for row := 1; row < font.height; row++ {
			line, err = popLine()
			if err != nil {
				return nil, 0, err
			}
			line = process(line)
			rows = append(rows, line)
			if n := len([]rune(line)); n > maxWidth {
				maxWidth = n
			}
		}
		return rows, maxWidth, nil
	}
	for code := rune(32); code < 127; code++ {
		rows, width, err := readGlyph()
		if err != nil {
			return nil, err
		}
		if code == 32 || strings.Join(rows, "") != "" {
			font.chars[code] = rows
			font.widths[code] = width
		}
	}
	if len(lines) > 0 {
		umlauts := []rune{'\u00c4', '\u00d6', '\u00dc', '\u00e4', '\u00f6', '\u00fc', '\u00df'}
		for _, code := range umlauts {
			rows, width, err := readGlyph()
			if err != nil {
				return nil, err
			}
			if strings.Join(rows, "") != "" {
				font.chars[code] = rows
				font.widths[code] = width
			}
		}
	}
	for len(lines) > 0 {
		line, _ := popLine()
		line = strings.TrimSpace(line)
		parts := strings.Fields(line)
		if len(parts) == 0 || !strings.HasPrefix(strings.ToLower(parts[0]), "0x") {
			continue
		}
		value, err := strconv.ParseInt(parts[0][2:], 16, 32)
		if err != nil {
			continue
		}
		rows, width, err := readGlyph()
		if err != nil {
			return nil, err
		}
		if strings.Join(rows, "") != "" {
			code := rune(value)
			font.chars[code] = rows
			font.widths[code] = width
		}
	}
	return font, nil
}

func renderText(text string, font *Font, direction string, width int, justify string) (string, error) {
	if width <= 0 {
		return "", fmt.Errorf("width must be positive")
	}
	b := &Builder{
		text:      []rune(text),
		font:      font,
		direction: direction,
		width:     width,
		justify:   justify,
		buffer:    make([]string, font.height),
	}
	for b.iterator < len(b.text) {
		b.addCharToProduct()
		b.iterator++
	}
	if len(b.buffer) > 0 && b.buffer[0] != "" {
		b.product = append(b.product, append([]string(nil), b.buffer...))
	}
	var out strings.Builder
	for _, rows := range b.product {
		for i := range rows {
			rows[i] = b.justifyRow(rows[i])
			rows[i] = strings.ReplaceAll(rows[i], string(font.hardBlank), " ")
		}
		out.WriteString(strings.Join(rows, "\n"))
		out.WriteByte('\n')
	}
	return out.String(), nil
}

func (b *Builder) addCharToProduct() {
	code := b.text[b.iterator]
	if code == '\n' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{append([]string(nil), b.buffer...), b.iterator})
		b.handleNewLine()
		return
	}
	char, ok := b.font.chars[code]
	if !ok {
		return
	}
	b.curCharWidth = b.font.widths[code]
	if b.width < b.curCharWidth {
		return
	}
	b.maxSmush = b.smushAmount(char)
	b.currentTotalWidth = len([]rune(b.buffer[0])) + b.curCharWidth - b.maxSmush
	if code == ' ' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{append([]string(nil), b.buffer...), b.iterator})
	}
	if b.currentTotalWidth >= b.width {
		b.handleNewLine()
	} else {
		for row := 0; row < b.font.height; row++ {
			b.addCurCharRowToBufferRow(char, row)
		}
	}
	b.prevCharWidth = b.curCharWidth
}

func (b *Builder) handleNewLine() {
	if len(b.blankMarkers) > 0 {
		marker := b.blankMarkers[len(b.blankMarkers)-1]
		b.blankMarkers = b.blankMarkers[:len(b.blankMarkers)-1]
		b.product = append(b.product, marker.buffer)
		b.iterator = marker.iterator
		b.cutBufferCommon()
		return
	}
	b.product = append(b.product, append([]string(nil), b.buffer...))
	b.iterator--
	b.cutBufferCommon()
}

func (b *Builder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([]string, b.font.height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	if b.iterator < 0 || b.iterator >= len(b.text) {
		return
	}
	char, ok := b.font.chars[b.text[b.iterator]]
	if !ok {
		return
	}
	b.maxSmush = b.smushAmount(char)
}

func (b *Builder) justifyRow(row string) string {
	n := len([]rune(row))
	padding := 0
	switch b.justify {
	case "right":
		padding = b.width - n - 1
	case "center":
		padding = (b.width - n) / 2
	}
	if padding > 0 {
		return strings.Repeat(" ", padding) + row
	}
	return row
}

func (b *Builder) smushAmount(curChar []string) int {
	if b.font.smushMode&(128|64) == 0 {
		return 0
	}
	maxSmush := b.curCharWidth
	for row := 0; row < b.font.height; row++ {
		lineLeft, lineRight := b.buffer[row], curChar[row]
		if b.direction == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}
		leftRunes, rightRunes := []rune(lineLeft), []rune(lineRight)
		leftEnd := len(leftRunes)
		for leftEnd > 0 && leftRunes[leftEnd-1] == ' ' {
			leftEnd--
		}
		linebd := leftEnd - 1
		if linebd < 0 {
			linebd = 0
		}
		ch1 := rune(0)
		if linebd < len(leftRunes) {
			ch1 = leftRunes[linebd]
		} else {
			linebd = 0
		}
		charbd := 0
		for charbd < len(rightRunes) && rightRunes[charbd] == ' ' {
			charbd++
		}
		ch2 := rune(0)
		if charbd < len(rightRunes) {
			ch2 = rightRunes[charbd]
		}
		amt := charbd + len(leftRunes) - 1 - linebd
		if ch1 == 0 || ch1 == ' ' {
			amt++
		} else if ch2 != 0 {
			if _, ok := b.smushChar(ch1, ch2); ok {
				amt++
			}
		}
		if amt < maxSmush {
			maxSmush = amt
		}
	}
	return maxSmush
}

func (b *Builder) addCurCharRowToBufferRow(curChar []string, row int) {
	left, right := b.smushRow(curChar, row)
	rightRunes := []rune(right)
	if b.maxSmush > len(rightRunes) {
		b.buffer[row] = left
	} else {
		b.buffer[row] = left + string(rightRunes[b.maxSmush:])
	}
}

func (b *Builder) smushRow(curChar []string, row int) (string, string) {
	addLeft, addRight := b.buffer[row], curChar[row]
	if b.direction == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}
	leftRunes, rightRunes := []rune(addLeft), []rune(addRight)
	for i := 0; i < b.maxSmush; i++ {
		idx := len(leftRunes) - b.maxSmush + i
		left := rune(0)
		if idx >= 0 && idx < len(leftRunes) {
			left = leftRunes[idx]
		}
		right := rune(0)
		if i < len(rightRunes) {
			right = rightRunes[i]
		}
		if smushed, ok := b.smushChar(left, right); ok && idx >= 0 && idx < len(leftRunes) {
			leftRunes[idx] = smushed
		}
	}
	if b.maxSmush > len(rightRunes) {
		return string(leftRunes), ""
	}
	return string(leftRunes), string(rightRunes)
}

func (b *Builder) smushChar(left, right rune) (rune, bool) {
	if left == ' ' {
		return right, true
	}
	if right == ' ' {
		return left, true
	}
	if b.prevCharWidth < 2 || b.curCharWidth < 2 {
		return 0, false
	}
	if b.font.smushMode&128 == 0 {
		return 0, false
	}
	if b.font.smushMode&63 == 0 {
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
	if b.font.smushMode&32 != 0 && left == b.font.hardBlank && right == b.font.hardBlank {
		return left, true
	}
	if left == b.font.hardBlank || right == b.font.hardBlank {
		return 0, false
	}
	if b.font.smushMode&1 != 0 && left == right {
		return left, true
	}
	if b.font.smushMode&2 != 0 {
		if left == '_' && strings.ContainsRune("|/\\[]{}()<>" , right) {
			return right, true
		}
		if right == '_' && strings.ContainsRune("|/\\[]{}()<>" , left) {
			return left, true
		}
	}
	if b.font.smushMode&4 != 0 {
		rules := [][2]string{{"|", "/\\[]{}()<>"}, {"/\\", "[]{}()<>"}, {"[]", "{}()<>"}, {"{}", "()<>"}, {"()", "<>"}}
		for _, rule := range rules {
			if strings.ContainsRune(rule[0], left) && strings.ContainsRune(rule[1], right) {
				return right, true
			}
			if strings.ContainsRune(rule[0], right) && strings.ContainsRune(rule[1], left) {
				return left, true
			}
		}
	}
	if b.font.smushMode&8 != 0 {
		pairs := []string{string(left) + string(right), string(right) + string(left)}
		for _, pair := range pairs {
			if pair == "[]" || pair == "{}" || pair == "()" {
				return '|', true
			}
		}
	}
	if b.font.smushMode&16 != 0 {
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

func reverseArt(input string) string {
	lines := outputLines(input)
	for i, line := range lines {
		r := []rune(line)
		for j := range r {
			r[j] = reverseRune(r[j])
		}
		for left, right := 0, len(r)-1; left < right; left, right = left+1, right-1 {
			r[left], r[right] = r[right], r[left]
		}
		lines[i] = string(r)
	}
	return strings.Join(lines, "\n") + "\n"
}

func flipArt(input string) string {
	lines := outputLines(input)
	for left, right := 0, len(lines)-1; left < right; left, right = left+1, right-1 {
		lines[left], lines[right] = lines[right], lines[left]
	}
	for i, line := range lines {
		r := []rune(line)
		for j := range r {
			r[j] = flipRune(r[j])
		}
		lines[i] = string(r)
	}
	return strings.Join(lines, "\n") + "\n"
}

func outputLines(input string) []string {
	lines := strings.Split(input, "\n")
	if len(lines) > 0 && lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	return lines
}

func stripSurroundingNewlines(input string) string {
	lines := outputLines(input)
	kept := make([]string, 0, len(lines))
	seen := false
	for _, line := range lines {
		if strings.TrimSpace(line) != "" || seen {
			seen = true
			kept = append(kept, line)
		}
	}
	joined := strings.Join(kept, "\n") + "\n"
	return strings.TrimRightFunc(joined, unicode.IsSpace)
}

func reverseRune(r rune) rune {
	pairs := map[rune]rune{'(': ')', ')': '(', '/': '\\', '\\': '/', '<': '>', '>': '<', '[': ']', ']': '[', '{': '}', '}': '{'}
	if v, ok := pairs[r]; ok {
		return v
	}
	return r
}

func flipRune(r rune) rune {
	pairs := map[rune]rune{'/': '\\', '\\': '/', 'A': 'V', 'M': 'W', 'P': 'b', 'R': 'b', 'V': 'A', 'W': 'M', '^': 'v', '_': '-', 'b': 'P', 'm': 'w', 'v': '^', 'w': 'm'}
	if v, ok := pairs[r]; ok {
		return v
	}
	return r
}
GO_SOURCE

gofmt -w main.go
go build ./...
find . -type f -name '*.py' -delete
rm -rf pyfiglet