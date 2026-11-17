#!/bin/bash
set -euo pipefail

cd /workspace/repo

# 1. Prepare fonts directory for Go embedding
mkdir -p fonts
if [ -d pyfiglet/fonts ]; then
    cp pyfiglet/fonts/*.flf fonts/ 2>/dev/null || true
fi
if [ -d pyfiglet/fonts-standard ]; then
    cp pyfiglet/fonts-standard/*.flf fonts/ 2>/dev/null || true
fi

# 2. Write go.mod
cat << 'EOF' > go.mod
module figlet

go 1.23
EOF

# 3. Write Go implementation
cat << 'EOF' > main.go
/*
The MIT License (MIT)
Copyright © 2007-2018
  Christopher Jones <cjones@insub.org>
  Stefano Rivera <stefano@rivera.za.net>
  Peter Waller <p@pwaller.net>
  And various contributors (see git history).

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
*/

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

//go:embed fonts/*.flf
var embeddedFonts embed.FS

func loadFontData(fontName string) ([]byte, error) {
	clean := strings.ToLower(strings.TrimSuffix(strings.TrimSuffix(fontName, ".flf"), ".tlf"))
	if data, err := embeddedFonts.ReadFile("fonts/" + clean + ".flf"); err == nil {
		return data, nil
	}
	candidates := []string{
		"fonts/" + clean + ".flf",
		clean + ".flf",
		clean + ".tlf",
		filepath.Join("/workspace/repo/fonts", clean+".flf"),
		filepath.Join("/workspace/repo/pyfiglet/fonts", clean+".flf"),
		filepath.Join("/workspace/repo/pyfiglet/fonts-standard", clean+".flf"),
	}
	for _, p := range candidates {
		if data, err := os.ReadFile(p); err == nil {
			return data, nil
		}
	}
	return nil, fmt.Errorf("font %s not found", fontName)
}

type Font struct {
	height      int
	hardBlank   rune
	printDir    int
	hasPrintDir bool
	smushMode   int
	chars       map[rune][][]rune
	width       map[rune]int
}

var reMagic = regexp.MustCompile(`^[tf]lf2.`)

func parseFont(fontName string, rawData []byte) (*Font, error) {
	rawStr := strings.Map(func(r rune) rune {
		if r == '\u0085' || r == '\u2028' || r == '\u2029' {
			return ' '
		}
		return r
	}, string(rawData))

	rawStr = strings.ReplaceAll(rawStr, "\r\n", "\n")
	rawStr = strings.ReplaceAll(rawStr, "\r", "\n")
	lines := strings.Split(rawStr, "\n")

	if len(lines) == 0 {
		return nil, fmt.Errorf("empty font file")
	}

	header := lines[0]
	if !reMagic.MatchString(header) {
		return nil, fmt.Errorf("%s is not a valid figlet font", fontName)
	}

	header = reMagic.ReplaceAllString(header, "")
	fields := strings.Fields(header)
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed header for %s", fontName)
	}

	hardBlankRunes := []rune(fields[0])
	if len(hardBlankRunes) == 0 {
		return nil, fmt.Errorf("missing hardblank")
	}
	hardBlank := hardBlankRunes[0]

	height, err := strconv.Atoi(fields[1])
	if err != nil {
		return nil, err
	}
	oldLayout, err := strconv.Atoi(fields[4])
	if err != nil {
		return nil, err
	}
	commentLines, err := strconv.Atoi(fields[5])
	if err != nil {
		return nil, err
	}

	printDir := 0
	hasPrintDir := false
	if len(fields) > 6 {
		if pd, err := strconv.Atoi(fields[6]); err == nil {
			printDir = pd
			hasPrintDir = true
		}
	}

	fullLayout := 0
	hasFullLayout := false
	if len(fields) > 7 {
		if fl, err := strconv.Atoi(fields[7]); err == nil {
			fullLayout = fl
			hasFullLayout = true
		}
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

	font := &Font{
		height:      height,
		hardBlank:   hardBlank,
		printDir:    printDir,
		hasPrintDir: hasPrintDir,
		smushMode:   fullLayout,
		chars:       make(map[rune][][]rune),
		width:       make(map[rune]int),
	}

	lineIdx := 1 + commentLines

	readChar := func() (int, [][]rune) {
		maxWidth := 0
		var glyph [][]rune
		var endMarker rune
		hasEndMarker := false

		for h := 0; h < height; h++ {
			if lineIdx >= len(lines) {
				glyph = append(glyph, []rune{})
				continue
			}
			line := lines[lineIdx]
			lineIdx++

			lineRunes := []rune(line)
			if !hasEndMarker {
				lastIdx := len(lineRunes) - 1
				for lastIdx >= 0 && (lineRunes[lastIdx] == ' ' || lineRunes[lastIdx] == '\t' || lineRunes[lastIdx] == '\r') {
					lastIdx--
				}
				if lastIdx >= 0 {
					endMarker = lineRunes[lastIdx]
					hasEndMarker = true
				}
			}

			for len(lineRunes) > 0 && (lineRunes[len(lineRunes)-1] == ' ' || lineRunes[len(lineRunes)-1] == '\t' || lineRunes[len(lineRunes)-1] == '\r') {
				lineRunes = lineRunes[:len(lineRunes)-1]
			}
			if hasEndMarker && len(lineRunes) > 0 && lineRunes[len(lineRunes)-1] == endMarker {
				lineRunes = lineRunes[:len(lineRunes)-1]
				if len(lineRunes) > 0 && lineRunes[len(lineRunes)-1] == endMarker {
					lineRunes = lineRunes[:len(lineRunes)-1]
				}
			}

			if len(lineRunes) > maxWidth {
				maxWidth = len(lineRunes)
			}
			glyph = append(glyph, lineRunes)
		}
		return maxWidth, glyph
	}

	allEmpty := func(glyph [][]rune) bool {
		for _, row := range glyph {
			if len(row) > 0 {
				return false
			}
		}
		return true
	}

	for i := 32; i <= 126; i++ {
		if lineIdx+height <= len(lines) {
			w, g := readChar()
			if i == 32 || !allEmpty(g) {
				font.chars[rune(i)] = g
				font.width[rune(i)] = w
			}
		}
	}

	german := []rune{'Ä', 'Ö', 'Ü', 'ä', 'ö', 'ü', 'ß'}
	for _, r := range german {
		if lineIdx+height <= len(lines) {
			w, g := readChar()
			if !allEmpty(g) {
				font.chars[r] = g
				font.width[r] = w
			}
		}
	}

	for lineIdx < len(lines) {
		line := strings.TrimSpace(lines[lineIdx])
		lineIdx++
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, " ", 2)
		codeStr := parts[0]
		if strings.HasPrefix(strings.ToLower(codeStr), "0x") {
			if val, err := strconv.ParseInt(codeStr[2:], 16, 64); err == nil {
				if lineIdx+height <= len(lines) {
					w, g := readChar()
					if !allEmpty(g) {
						font.chars[rune(val)] = g
						font.width[rune(val)] = w
					}
				}
			}
		}
	}

	return font, nil
}

func smushChars(left, right rune, hardBlank rune, smushMode int, direction string, prevCharWidth, curCharWidth int) *rune {
	if left == ' ' {
		res := right
		return &res
	}
	if right == ' ' {
		res := left
		return &res
	}

	if prevCharWidth < 2 || curCharWidth < 2 {
		return nil
	}

	if (smushMode & SM_SMUSH) == 0 {
		return nil
	}

	if (smushMode & 63) == 0 {
		if left == hardBlank {
			res := right
			return &res
		}
		if right == hardBlank {
			res := left
			return &res
		}
		if direction == "right-to-left" {
			res := left
			return &res
		} else {
			res := right
			return &res
		}
	}

	if (smushMode & SM_HARDBLANK) != 0 {
		if left == hardBlank && right == hardBlank {
			res := left
			return &res
		}
	}

	if left == hardBlank || right == hardBlank {
		return nil
	}

	if (smushMode & SM_EQUAL) != 0 {
		if left == right {
			res := left
			return &res
		}
	}

	type classPair struct {
		a string
		b string
	}
	var smushes []classPair

	if (smushMode & SM_LOWLINE) != 0 {
		smushes = append(smushes, classPair{a: "_", b: `|/\[]{}()<>`})
	}

	if (smushMode & SM_HIERARCHY) != 0 {
		smushes = append(smushes,
			classPair{a: `|`, b: `/\[]{}()<>`},
			classPair{a: `/\\`, b: `[]{}()<>`},
			classPair{a: `[]`, b: `{}()<>`},
			classPair{a: `{}` , b: `()<>`},
			classPair{a: `()`, b: `<>`},
		)
	}

	for _, pair := range smushes {
		if strings.ContainsRune(pair.a, left) && strings.ContainsRune(pair.b, right) {
			res := right
			return &res
		}
		if strings.ContainsRune(pair.a, right) && strings.ContainsRune(pair.b, left) {
			res := left
			return &res
		}
	}

	if (smushMode & SM_PAIR) != 0 {
		pair1 := string([]rune{left, right})
		pair2 := string([]rune{right, left})
		if pair1 == "[]" || pair1 == "{}" || pair1 == "()" ||
			pair2 == "[]" || pair2 == "{}" || pair2 == "()" {
			res := '|'
			return &res
		}
	}

	if (smushMode & SM_BIGX) != 0 {
		if left == '/' && right == '\\' {
			res := '|'
			return &res
		}
		if right == '/' && left == '\\' {
			res := 'Y'
			return &res
		}
		if left == '>' && right == '<' {
			res := 'X'
			return &res
		}
	}

	return nil
}

type blankMarker struct {
	buffer   [][]rune
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
	buffer            [][]rune
	productQueue      [][][]rune
}

func copyBuffer(buf [][]rune) [][]rune {
	cp := make([][]rune, len(buf))
	for i := range buf {
		cp[i] = append([]rune{}, buf[i]...)
	}
	return cp
}

func (b *Builder) getCurChar() [][]rune {
	if b.iterator < 0 || b.iterator >= len(b.text) {
		return nil
	}
	c := b.text[b.iterator]
	return b.font.chars[c]
}

func (b *Builder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([][]rune, b.font.height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	curChar := b.getCurChar()
	if curChar == nil {
		return
	}
	b.maxSmush = b.smushAmount(curChar)
}

func (b *Builder) handleNewLine() {
	if len(b.blankMarkers) > 0 {
		last := b.blankMarkers[len(b.blankMarkers)-1]
		b.blankMarkers = b.blankMarkers[:len(b.blankMarkers)-1]
		b.productQueue = append(b.productQueue, last.buffer)
		b.iterator = last.iterator
		b.cutBufferCommon()
	} else {
		b.productQueue = append(b.productQueue, copyBuffer(b.buffer))
		b.iterator--
		b.cutBufferCommon()
	}
}

func (b *Builder) smushAmount(curChar [][]rune) int {
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

		rstripLen := len(lineLeft)
		for rstripLen > 0 && lineLeft[rstripLen-1] == ' ' {
			rstripLen--
		}
		linebd := rstripLen - 1
		if linebd < 0 {
			linebd = 0
		}

		var ch1 rune
		hasCh1 := false
		if linebd < len(lineLeft) {
			ch1 = lineLeft[linebd]
			hasCh1 = true
		} else {
			linebd = 0
			hasCh1 = false
		}

		lstripStart := 0
		for lstripStart < len(lineRight) && lineRight[lstripStart] == ' ' {
			lstripStart++
		}
		charbd := lstripStart
		var ch2 rune
		hasCh2 := false
		if charbd < len(lineRight) {
			ch2 = lineRight[charbd]
			hasCh2 = true
		} else {
			charbd = len(lineRight)
			hasCh2 = false
		}

		amt := charbd + len(lineLeft) - 1 - linebd

		if !hasCh1 || ch1 == ' ' {
			amt++
		} else if hasCh2 && smushChars(ch1, ch2, b.font.hardBlank, b.font.smushMode, b.direction, b.prevCharWidth, b.curCharWidth) != nil {
			amt++
		}

		if amt < maxSmush {
			maxSmush = amt
		}
	}

	return maxSmush
}

func (b *Builder) smushRow(curChar [][]rune, row int) ([]rune, []rune) {
	addLeft := append([]rune{}, b.buffer[row]...)
	addRight := append([]rune{}, curChar[row]...)

	if b.direction == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}

	for i := 0; i < b.maxSmush; i++ {
		idx := len(addLeft) - b.maxSmush + i
		var left rune
		if idx >= 0 && idx < len(addLeft) {
			left = addLeft[idx]
		}
		var right rune
		if i < len(addRight) {
			right = addRight[i]
		}
		smushed := smushChars(left, right, b.font.hardBlank, b.font.smushMode, b.direction, b.prevCharWidth, b.curCharWidth)
		if smushed != nil && idx >= 0 && idx < len(addLeft) {
			addLeft[idx] = *smushed
		}
	}
	return addLeft, addRight
}

func (b *Builder) addCurCharRowToBufferRow(curChar [][]rune, row int) {
	addLeft, addRight := b.smushRow(curChar, row)
	res := append([]rune{}, addLeft...)
	if b.maxSmush < len(addRight) {
		res = append(res, addRight[b.maxSmush:]...)
	}
	b.buffer[row] = res
}

func (b *Builder) addCharToProduct() {
	curRune := b.text[b.iterator]

	if curRune == '\n' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{buffer: copyBuffer(b.buffer), iterator: b.iterator})
		b.handleNewLine()
		return
	}

	curChar, ok := b.font.chars[curRune]
	if !ok {
		return
	}

	charWidth := b.font.width[curRune]
	if b.width < charWidth {
		fmt.Fprintf(os.Stderr, "pyfiglet error: Width is not enough to print this character\n")
		os.Exit(1)
	}

	b.curCharWidth = charWidth
	b.maxSmush = b.smushAmount(curChar)

	buf0Len := 0
	if len(b.buffer) > 0 {
		buf0Len = len(b.buffer[0])
	}
	b.currentTotalWidth = buf0Len + b.curCharWidth - b.maxSmush

	if curRune == ' ' {
		b.blankMarkers = append(b.blankMarkers, blankMarker{buffer: copyBuffer(b.buffer), iterator: b.iterator})
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

func (b *Builder) justifyBuffer(buf [][]rune) [][]rune {
	result := make([][]rune, len(buf))
	for row := 0; row < b.font.height; row++ {
		rowRunes := buf[row]
		pad := 0
		if b.justify == "right" {
			pad = b.width - len(rowRunes) - 1
		} else if b.justify == "center" {
			pad = (b.width - len(rowRunes)) / 2
		}
		if pad > 0 {
			spaces := []rune(strings.Repeat(" ", pad))
			result[row] = append(spaces, rowRunes...)
		} else {
			result[row] = append([]rune{}, rowRunes...)
		}
	}
	return result
}

func (b *Builder) returnProduct() string {
	if len(b.buffer) > 0 && len(b.buffer[0]) > 0 {
		b.productQueue = append(b.productQueue, copyBuffer(b.buffer))
	}

	var sb strings.Builder
	for _, buf := range b.productQueue {
		justified := b.justifyBuffer(buf)
		for row := 0; row < b.font.height; row++ {
			rowRunes := justified[row]
			rowStr := string(rowRunes)
			if b.font.hardBlank != 0 {
				rowStr = strings.ReplaceAll(rowStr, string(b.font.hardBlank), " ")
			}
			sb.WriteString(rowStr)
			sb.WriteString("\n")
		}
	}
	return sb.String()
}

func splitlines(s string) []string {
	if len(s) == 0 {
		return nil
	}
	s = strings.ReplaceAll(s, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	if strings.HasSuffix(s, "\n") {
		s = s[:len(s)-1]
	}
	return strings.Split(s, "\n")
}

func reverseString(s string) string {
	lines := splitlines(s)
	var out []string
	for _, line := range lines {
		runes := []rune(line)
		for idx, r := range runes {
			switch r {
			case '(':
				runes[idx] = ')'
			case ')':
				runes[idx] = '('
			case '/':
				runes[idx] = '\\'
			case '\\':
				runes[idx] = '/'
			case '<':
				runes[idx] = '>'
			case '>':
				runes[idx] = '<'
			case '[':
				runes[idx] = ']'
			case ']':
				runes[idx] = '['
			case '{':
				runes[idx] = '}'
			case '}':
				runes[idx] = '{'
			}
		}
		for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
			runes[i], runes[j] = runes[j], runes[i]
		}
		out = append(out, string(runes))
	}
	return strings.Join(out, "\n") + "\n"
}

func flipString(s string) string {
	lines := splitlines(s)
	for i, j := 0, len(lines)-1; i < j; i, j = i+1, j-1 {
		lines[i], lines[j] = lines[j], lines[i]
	}
	var out []string
	for _, line := range lines {
		runes := []rune(line)
		for idx, r := range runes {
			switch r {
			case '/':
				runes[idx] = '\\'
			case '\\':
				runes[idx] = '/'
			case '^':
				runes[idx] = 'v'
			case 'v':
				runes[idx] = '^'
			case 'A':
				runes[idx] = 'V'
			case 'V':
				runes[idx] = 'A'
			case 'M':
				runes[idx] = 'W'
			case 'W':
				runes[idx] = 'M'
			case 'P':
				runes[idx] = 'b'
			case 'R':
				runes[idx] = 'b'
			case 'b':
				runes[idx] = 'P'
			case 'm':
				runes[idx] = 'w'
			case 'w':
				runes[idx] = 'm'
			case '_':
				runes[idx] = '-'
			case '-':
				runes[idx] = '-'
			}
		}
		out = append(out, string(runes))
	}
	return strings.Join(out, "\n") + "\n"
}

func stripSurroundingNewlines(s string) string {
	lines := splitlines(s)
	charsSeen := false
	var out []string
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

func resolveDirection(optDirection string, fontPrintDir int, hasPrintDir bool) string {
	if optDirection == "auto" {
		if hasPrintDir && fontPrintDir == 1 {
			return "right-to-left"
		}
		return "left-to-right"
	}
	return optDirection
}

func resolveJustify(optJustify string, resolvedDir string) string {
	if optJustify == "auto" {
		if resolvedDir == "right-to-left" {
			return "right"
		}
		return "left"
	}
	return optJustify
}

func main() {
	fontName := "standard"
	width := 80
	justify := "auto"
	direction := "auto"
	reverse := false
	flip := false
	stripNewlines := false
	normalizeNewlines := false

	var textArgs []string
	args := os.Args[1:]
	i := 0
	for i < len(args) {
		arg := args[i]
		if arg == "--" {
			textArgs = append(textArgs, args[i+1:]...)
			break
		}

		if strings.HasPrefix(arg, "-") && len(arg) > 1 {
			if arg == "-f" || arg == "--font" {
				if i+1 < len(args) {
					fontName = args[i+1]
					i += 2
					continue
				}
			} else if strings.HasPrefix(arg, "-f") {
				fontName = arg[2:]
				i++
				continue
			} else if arg == "-w" || arg == "--width" {
				if i+1 < len(args) {
					if val, err := strconv.Atoi(args[i+1]); err == nil {
						width = val
					}
					i += 2
					continue
				}
			} else if strings.HasPrefix(arg, "-w") {
				if val, err := strconv.Atoi(arg[2:]); err == nil {
					width = val
				}
				i++
				continue
			} else if arg == "-j" || arg == "--justify" {
				if i+1 < len(args) {
					justify = args[i+1]
					i += 2
					continue
				}
			} else if strings.HasPrefix(arg, "-j") {
				justify = arg[2:]
				i++
				continue
			} else if arg == "-D" || arg == "--direction" {
				if i+1 < len(args) {
					direction = args[i+1]
					i += 2
					continue
				}
			} else if strings.HasPrefix(arg, "-D") {
				direction = arg[2:]
				i++
				continue
			} else if arg == "-r" || arg == "--reverse" {
				reverse = true
				i++
				continue
			} else if arg == "-F" || arg == "--flip" {
				flip = true
				i++
				continue
			} else if arg == "-s" || arg == "--strip-surrounding-newlines" {
				stripNewlines = true
				i++
				continue
			} else if arg == "-n" || arg == "--normalize-surrounding-newlines" {
				normalizeNewlines = true
				i++
				continue
			} else if !strings.HasPrefix(arg, "--") {
				allFlags := true
				for _, c := range arg[1:] {
					if c != 'r' && c != 'F' && c != 's' && c != 'n' {
						allFlags = false
						break
					}
				}
				if allFlags {
					for _, c := range arg[1:] {
						switch c {
						case 'r':
							reverse = true
						case 'F':
							flip = true
						case 's':
							stripNewlines = true
						case 'n':
							normalizeNewlines = true
						}
					}
					i++
					continue
				}
			}
		}

		textArgs = append(textArgs, arg)
		i++
	}

	if len(textArgs) == 0 {
		fmt.Printf("Usage: figlet [options] [text..]\n")
		os.Exit(1)
	}

	text := strings.Join(textArgs, " ")

	fontBytes, err := loadFontData(fontName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: requested font '%s' not found.\n", fontName)
		os.Exit(1)
	}

	font, err := parseFont(fontName, fontBytes)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: %v\n", err)
		os.Exit(1)
	}

	resolvedDir := resolveDirection(direction, font.printDir, font.hasPrintDir)
	resolvedJustify := resolveJustify(justify, resolvedDir)

	builder := &Builder{
		text:      []rune(text),
		font:      font,
		direction: resolvedDir,
		width:     width,
		justify:   resolvedJustify,
		buffer:    make([][]rune, font.height),
	}

	for builder.iterator < len(builder.text) {
		builder.addCharToProduct()
		builder.iterator++
	}

	r := builder.returnProduct()

	if reverse {
		r = reverseString(r)
	}
	if flip {
		r = flipString(r)
	}
	if stripNewlines {
		r = stripSurroundingNewlines(r)
	} else if normalizeNewlines {
		r = normalizeSurroundingNewlines(r)
	}

	os.Stdout.WriteString(r)
	os.Stdout.WriteString("\n")
}
EOF

# 4. Remove all .py files under /workspace/repo
find /workspace/repo -type f -name "*.py" -delete
find /workspace/repo -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 5. Format and verify builds
gofmt -w .
go build -o /tmp/figlet .
go build ./...
