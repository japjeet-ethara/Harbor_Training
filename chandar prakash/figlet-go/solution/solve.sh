#!/bin/bash
set -e

cd /workspace/repo

# 1. Move/copy fonts to /workspace/repo/fonts
mkdir -p fonts
if [ -d pyfiglet/fonts ]; then
    cp pyfiglet/fonts/*.flf fonts/
elif [ -d pyfiglet/fonts-standard ]; then
    cp pyfiglet/fonts-standard/*.flf fonts/
fi

# 2. Delete every .py file in the repository
find /workspace/repo -type f -name "*.py" -delete
rm -rf pyfiglet

# 3. Create go.mod
cat << 'EOF' > go.mod
module figlet

go 1.23
EOF

# 4. Create main.go
cat << 'EOF' > main.go
package main

import (
	"embed"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"unicode/utf8"
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
	Name           string
	Height         int
	BaseLine       int
	MaxLength      int
	OldLayout      int
	CommentLines   int
	PrintDirection int
	SmushMode      int
	HardBlank      rune
	Chars          map[rune][]string
	Width          map[rune]int
}

var reMagic = regexp.MustCompile(`^[tf]lf2.`)
var reEndMarker = regexp.MustCompile(`(.)\s*$`)

func loadFont(fontName string) (*FigletFont, error) {
	var data []byte
	var err error

	fn := fontName
	if !strings.HasSuffix(fn, ".flf") && !strings.HasSuffix(fn, ".tlf") {
		fn = fontName + ".flf"
	}

	data, err = embeddedFonts.ReadFile("fonts/" + fn)
	if err != nil {
		paths := []string{
			fn,
			filepath.Join("fonts", fn),
			filepath.Join("pyfiglet", "fonts", fn),
			filepath.Join("/workspace/repo/fonts", fn),
			filepath.Join("/workspace/repo/pyfiglet/fonts", fn),
		}
		for _, p := range paths {
			if d, e := os.ReadFile(p); e == nil {
				data = d
				err = nil
				break
			}
		}
	}
	if err != nil {
		return nil, fmt.Errorf("font %s not found: %w", fontName, err)
	}

	raw := string(data)
	reUnicodeSplit := regexp.MustCompile("[\u0085\u2028\u2029]")
	raw = reUnicodeSplit.ReplaceAllString(raw, " ")

	lines := strings.Split(raw, "\n")
	for i := range lines {
		lines[i] = strings.TrimRight(lines[i], "\r")
	}

	if len(lines) == 0 {
		return nil, fmt.Errorf("empty font file")
	}

	header := lines[0]
	lines = lines[1:]

	if !reMagic.MatchString(header) {
		return nil, fmt.Errorf("invalid magic number in %s", fontName)
	}
	headerClean := reMagic.ReplaceAllString(header, "")
	fields := strings.Fields(headerClean)
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed header in %s", fontName)
	}

	hardBlankRune, _ := utf8.DecodeRuneInString(fields[0])
	height, _ := strconv.Atoi(fields[1])
	baseLine, _ := strconv.Atoi(fields[2])
	maxLength, _ := strconv.Atoi(fields[3])
	oldLayout, _ := strconv.Atoi(fields[4])
	commentLines, _ := strconv.Atoi(fields[5])

	printDirection := 0
	hasFullLayout := false
	fullLayout := 0
	if len(fields) > 6 {
		printDirection, _ = strconv.Atoi(fields[6])
	}
	if len(fields) > 7 {
		fullLayout, _ = strconv.Atoi(fields[7])
		hasFullLayout = true
	}

	smushMode := fullLayout
	if !hasFullLayout {
		if oldLayout == 0 {
			smushMode = 64
		} else if oldLayout < 0 {
			smushMode = 0
		} else {
			smushMode = (oldLayout & 31) | 128
		}
	}

	if len(lines) < commentLines {
		return nil, fmt.Errorf("file too short for comments")
	}
	lines = lines[commentLines:]

	font := &FigletFont{
		Name:           fontName,
		Height:         height,
		BaseLine:       baseLine,
		MaxLength:      maxLength,
		OldLayout:      oldLayout,
		CommentLines:   commentLines,
		PrintDirection: printDirection,
		SmushMode:      smushMode,
		HardBlank:      hardBlankRune,
		Chars:          make(map[rune][]string),
		Width:          make(map[rune]int),
	}

	readChar := func() (int, []string, bool) {
		if len(lines) < height {
			return 0, nil, false
		}
		var charLines []string
		width := 0
		var endSub *regexp.Regexp

		for row := 0; row < height; row++ {
			line := lines[row]
			if endSub == nil {
				m := reEndMarker.FindStringSubmatch(line)
				if len(m) > 1 {
					endChar := m[1]
					endSub = regexp.MustCompile(regexp.QuoteMeta(endChar) + `{1,2}\s*$`)
				}
			}
			if endSub != nil {
				line = endSub.ReplaceAllString(line, "")
			}
			w := utf8.RuneCountInString(line)
			if w > width {
				width = w
			}
			charLines = append(charLines, line)
		}
		lines = lines[height:]
		return width, charLines, true
	}

	for i := 32; i < 127; i++ {
		w, letter, ok := readChar()
		if !ok {
			break
		}
		if i == 32 || strings.Join(letter, "") != "" {
			font.Chars[rune(i)] = letter
			font.Width[rune(i)] = w
		}
	}

	for _, r := range "ÄÖÜäöüß" {
		if len(lines) >= height {
			w, letter, ok := readChar()
			if ok && strings.Join(letter, "") != "" {
				font.Chars[r] = letter
				font.Width[r] = w
			}
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
			if err == nil && len(lines) >= height {
				w, letter, ok := readChar()
				if ok && strings.Join(letter, "") != "" {
					font.Chars[rune(code)] = letter
					font.Width[rune(code)] = w
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

type FigletBuilder struct {
	Text          []rune
	Direction     string
	Width         int
	Font          *FigletFont
	Justify       string
	Iterator      int
	MaxSmush      int
	CurCharWidth  int
	PrevCharWidth int
	CurrentTotalW int
	BlankMarkers  []BlankMarker
	Buffer        []string
	ProductQueue  [][]string
}

func NewFigletBuilder(text string, font *FigletFont, direction string, width int, justify string) *FigletBuilder {
	b := &FigletBuilder{
		Text:      []rune(text),
		Direction: direction,
		Width:     width,
		Font:      font,
		Justify:   justify,
		Buffer:    make([]string, font.Height),
	}
	return b
}

func (b *FigletBuilder) getCharAt(i int) ([]string, bool) {
	if i < 0 || i >= len(b.Text) {
		return nil, false
	}
	c := b.Text[i]
	lines, ok := b.Font.Chars[c]
	return lines, ok
}

func (b *FigletBuilder) getCharWidthAt(i int) int {
	if i < 0 || i >= len(b.Text) {
		return 0
	}
	c := b.Text[i]
	return b.Font.Width[c]
}

func (b *FigletBuilder) getCurChar() ([]string, bool) {
	return b.getCharAt(b.Iterator)
}

func (b *FigletBuilder) getCurWidth() int {
	return b.getCharWidthAt(b.Iterator)
}

func (b *FigletBuilder) smushChars(left, right string) (string, bool) {
	if left == " " {
		return right, true
	}
	if right == " " {
		return left, true
	}
	if b.PrevCharWidth < 2 || b.CurCharWidth < 2 {
		return "", false
	}
	if (b.Font.SmushMode & SM_SMUSH) == 0 {
		return "", false
	}
	hardBlank := string(b.Font.HardBlank)

	if (b.Font.SmushMode & 63) == 0 {
		if left == hardBlank {
			return right, true
		}
		if right == hardBlank {
			return left, true
		}
		if b.Direction == "right-to-left" {
			return left, true
		}
		return right, true
	}

	if (b.Font.SmushMode & SM_HARDBLANK) != 0 {
		if left == hardBlank && right == hardBlank {
			return left, true
		}
	}

	if left == hardBlank || right == hardBlank {
		return "", false
	}

	if (b.Font.SmushMode & SM_EQUAL) != 0 {
		if left == right {
			return left, true
		}
	}

	type rulePair struct{ a, b string }
	var smushes []rulePair

	if (b.Font.SmushMode & SM_LOWLINE) != 0 {
		smushes = append(smushes, rulePair{"_", `|/\[]{}()<>`})
	}

	if (b.Font.SmushMode & SM_HIERARCHY) != 0 {
		smushes = append(smushes,
			rulePair{"|", `/\[]{}()<>`},
			rulePair{`\/`, `[]{}()<>`},
			rulePair{"[]", `{}()<>`},
			rulePair{"{}", `()<>`},
			rulePair{"()", `<>`},
		)
	}

	for _, rule := range smushes {
		if strings.ContainsAny(left, rule.a) && strings.ContainsAny(right, rule.b) {
			return right, true
		}
		if strings.ContainsAny(right, rule.a) && strings.ContainsAny(left, rule.b) {
			return left, true
		}
	}

	if (b.Font.SmushMode & SM_PAIR) != 0 {
		for _, pair := range []string{left + right, right + left} {
			if pair == "[]" || pair == "{}" || pair == "()" {
				return "|", true
			}
		}
	}

	if (b.Font.SmushMode & SM_BIGX) != 0 {
		if left == "/" && right == `\` {
			return "|", true
		}
		if right == "/" && left == `\` {
			return "Y", true
		}
		if left == ">" && right == "<" {
			return "X", true
		}
	}

	return "", false
}

func (b *FigletBuilder) smushAmount(buffer, curChar []string) int {
	if (b.Font.SmushMode & (SM_SMUSH | SM_KERN)) == 0 {
		return 0
	}
	maxSmush := b.CurCharWidth
	for row := 0; row < b.Font.Height; row++ {
		lineLeft := buffer[row]
		lineRight := curChar[row]
		if b.Direction == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}

		linebd := len(strings.TrimRight(lineLeft, " ")) - 1
		if linebd < 0 {
			linebd = 0
		}
		var ch1 string
		if linebd < len(lineLeft) {
			ch1 = string(lineLeft[linebd])
		} else {
			linebd = 0
			ch1 = ""
		}

		charbd := len(lineRight) - len(strings.TrimLeft(lineRight, " "))
		var ch2 string
		if charbd < len(lineRight) {
			ch2 = string(lineRight[charbd])
		} else {
			charbd = len(lineRight)
			ch2 = ""
		}

		amt := charbd + len(lineLeft) - 1 - linebd

		if ch1 == "" || ch1 == " " {
			amt++
		} else if ch2 != "" {
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

func (b *FigletBuilder) getLeftSmushedChar(i int, addLeft string) (string, int) {
	idx := len(addLeft) - b.MaxSmush + i
	if idx >= 0 && idx < len(addLeft) {
		return string(addLeft[idx]), idx
	}
	return "", idx
}

func (b *FigletBuilder) updateSmushedCharInLeftBuffer(addLeft string, idx int, smushed string) string {
	l := []rune(addLeft)
	if idx < 0 || idx >= len(l) {
		return addLeft
	}
	if smushed != "" {
		l[idx] = []rune(smushed)[0]
	}
	return string(l)
}

func (b *FigletBuilder) smushRow(curChar []string, row int) (string, string) {
	addLeft := b.Buffer[row]
	addRight := curChar[row]

	if b.Direction == "right-to-left" {
		addLeft, addRight = addRight, addLeft
	}

	for i := 0; i < b.MaxSmush; i++ {
		left, idx := b.getLeftSmushedChar(i, addLeft)
		var right string
		if i < len(addRight) {
			right = string(addRight[i])
		}
		smushed, _ := b.smushChars(left, right)
		addLeft = b.updateSmushedCharInLeftBuffer(addLeft, idx, smushed)
	}
	return addLeft, addRight
}

func (b *FigletBuilder) addCurCharRowToBufferRow(curChar []string, row int) {
	addLeft, addRight := b.smushRow(curChar, row)
	rightSuffix := ""
	if b.MaxSmush < len(addRight) {
		rightSuffix = addRight[b.MaxSmush:]
	}
	b.Buffer[row] = addLeft + rightSuffix
}

func (b *FigletBuilder) cutBufferCommon() {
	b.CurrentTotalW = 0
	b.Buffer = make([]string, b.Font.Height)
	b.BlankMarkers = nil
	b.PrevCharWidth = 0
	curChar, ok := b.getCurChar()
	if !ok {
		return
	}
	b.MaxSmush = b.smushAmount(b.Buffer, curChar)
}

func (b *FigletBuilder) cutBufferAtLastBlank(savedBuffer []string, savedIterator int) {
	bufCopy := make([]string, len(savedBuffer))
	copy(bufCopy, savedBuffer)
	b.ProductQueue = append(b.ProductQueue, bufCopy)
	b.Iterator = savedIterator
	b.cutBufferCommon()
}

func (b *FigletBuilder) cutBufferAtLastChar() {
	bufCopy := make([]string, len(b.Buffer))
	copy(bufCopy, b.Buffer)
	b.ProductQueue = append(b.ProductQueue, bufCopy)
	b.Iterator--
	b.cutBufferCommon()
}

func (b *FigletBuilder) getLastBlank() ([]string, int, bool) {
	if len(b.BlankMarkers) == 0 {
		return nil, -1, false
	}
	last := b.BlankMarkers[len(b.BlankMarkers)-1]
	b.BlankMarkers = b.BlankMarkers[:len(b.BlankMarkers)-1]
	return last.Buffer, last.Iterator, true
}

func (b *FigletBuilder) handleNewLine() {
	savedBuf, savedIter, ok := b.getLastBlank()
	if ok && savedIter != -1 {
		b.cutBufferAtLastBlank(savedBuf, savedIter)
	} else {
		b.cutBufferAtLastChar()
	}
}

func (b *FigletBuilder) AddCharToProduct() {
	curChar, ok := b.getCurChar()

	if b.Text[b.Iterator] == '\n' {
		bufCopy := make([]string, len(b.Buffer))
		copy(bufCopy, b.Buffer)
		b.BlankMarkers = append(b.BlankMarkers, BlankMarker{Buffer: bufCopy, Iterator: b.Iterator})
		b.handleNewLine()
		return
	}

	if !ok {
		return
	}

	b.CurCharWidth = b.getCurWidth()
	b.MaxSmush = b.smushAmount(b.Buffer, curChar)

	b.CurrentTotalW = len(b.Buffer[0]) + b.CurCharWidth - b.MaxSmush

	if b.Text[b.Iterator] == ' ' {
		bufCopy := make([]string, len(b.Buffer))
		copy(bufCopy, b.Buffer)
		b.BlankMarkers = append(b.BlankMarkers, BlankMarker{Buffer: bufCopy, Iterator: b.Iterator})
	}

	if b.CurrentTotalW >= b.Width {
		b.handleNewLine()
	} else {
		for row := 0; row < b.Font.Height; row++ {
			b.addCurCharRowToBufferRow(curChar, row)
		}
	}

	b.PrevCharWidth = b.CurCharWidth
}

func (b *FigletBuilder) GoToNextChar() {
	b.Iterator++
}

func (b *FigletBuilder) IsNotFinished() bool {
	return b.Iterator < len(b.Text)
}

func (b *FigletBuilder) justifyString(justify string, buffer []string) []string {
	res := make([]string, len(buffer))
	if justify == "right" {
		for row := 0; row < b.Font.Height; row++ {
			pad := b.Width - len(buffer[row]) - 1
			if pad > 0 {
				res[row] = strings.Repeat(" ", pad) + buffer[row]
			} else {
				res[row] = buffer[row]
			}
		}
	} else if justify == "center" {
		for row := 0; row < b.Font.Height; row++ {
			pad := (b.Width - len(buffer[row])) / 2
			if pad > 0 {
				res[row] = strings.Repeat(" ", pad) + buffer[row]
			} else {
				res[row] = buffer[row]
			}
		}
	} else {
		copy(res, buffer)
	}
	return res
}

func (b *FigletBuilder) replaceHardblanks(buffer []string) string {
	s := strings.Join(buffer, "\n") + "\n"
	return strings.ReplaceAll(s, string(b.Font.HardBlank), " ")
}

func (b *FigletBuilder) ReturnProduct() string {
	if b.Buffer[0] != "" {
		bufCopy := make([]string, len(b.Buffer))
		copy(bufCopy, b.Buffer)
		b.ProductQueue = append(b.ProductQueue, bufCopy)
	}
	var acc strings.Builder
	for _, buf := range b.ProductQueue {
		justified := b.justifyString(b.Justify, buf)
		acc.WriteString(b.replaceHardblanks(justified))
	}
	return acc.String()
}

func reverseString(s string) string {
	var out []string
	lines := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
	for _, row := range lines {
		runes := []rune(row)
		for i, r := range runes {
			switch r {
			case '(':
				runes[i] = ')'
			case ')':
				runes[i] = '('
			case '/':
				runes[i] = '\\'
			case '\\':
				runes[i] = '/'
			case '[':
				runes[i] = ']'
			case ']':
				runes[i] = '['
			case '{':
				runes[i] = '}'
			case '}':
				runes[i] = '{'
			case '<':
				runes[i] = '>'
			case '>':
				runes[i] = '<'
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
	var out []string
	lines := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
	for i := len(lines) - 1; i >= 0; i-- {
		runes := []rune(lines[i])
		for j, r := range runes {
			switch r {
			case '/':
				runes[j] = '\\'
			case '\\':
				runes[j] = '/'
			case 'A':
				runes[j] = 'V'
			case 'V':
				runes[j] = 'A'
			case 'M':
				runes[j] = 'W'
			case 'W':
				runes[j] = 'M'
			case 'P':
				runes[j] = 'b'
			case 'R':
				runes[j] = 'b'
			case 'b':
				runes[j] = 'P'
			case '^':
				runes[j] = 'v'
			case 'v':
				runes[j] = '^'
			case '_':
				runes[j] = '-'
			case 'm':
				runes[j] = 'w'
			case 'w':
				runes[j] = 'm'
			}
		}
		out = append(out, string(runes))
	}
	return strings.Join(out, "\n") + "\n"
}

func stripSurroundingNewlines(s string) string {
	var out []string
	lines := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
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
	fontName := "standard"
	width := 80
	justify := "auto"
	direction := "auto"
	reverse := false
	flip := false
	strip := false
	normalize := false

	var textArgs []string
	cliArgs := os.Args[1:]
	i := 0
	for i < len(cliArgs) {
		arg := cliArgs[i]
		if arg == "-f" && i+1 < len(cliArgs) {
			fontName = cliArgs[i+1]
			i += 2
		} else if strings.HasPrefix(arg, "-f=") {
			fontName = strings.TrimPrefix(arg, "-f=")
			i++
		} else if arg == "-w" && i+1 < len(cliArgs) {
			width, _ = strconv.Atoi(cliArgs[i+1])
			i += 2
		} else if strings.HasPrefix(arg, "-w=") {
			width, _ = strconv.Atoi(strings.TrimPrefix(arg, "-w="))
			i++
		} else if arg == "-j" && i+1 < len(cliArgs) {
			justify = cliArgs[i+1]
			i += 2
		} else if strings.HasPrefix(arg, "-j=") {
			justify = strings.TrimPrefix(arg, "-j=")
			i++
		} else if arg == "-D" && i+1 < len(cliArgs) {
			direction = cliArgs[i+1]
			i += 2
		} else if strings.HasPrefix(arg, "-D=") {
			direction = strings.TrimPrefix(arg, "-D=")
			i++
		} else if arg == "-r" {
			reverse = true
			i++
		} else if arg == "-F" {
			flip = true
			i++
		} else if arg == "-s" {
			strip = true
			i++
		} else if arg == "-n" {
			normalize = true
			i++
		} else {
			textArgs = cliArgs[i:]
			break
		}
	}

	if len(textArgs) == 0 {
		os.Exit(1)
	}

	text := strings.Join(textArgs, " ")

	f, err := loadFont(fontName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Font error: %v\n", err)
		os.Exit(1)
	}

	actualDir := direction
	if actualDir == "auto" {
		if f.PrintDirection == 1 {
			actualDir = "right-to-left"
		} else {
			actualDir = "left-to-right"
		}
	}

	actualJustify := justify
	if actualJustify == "auto" {
		if actualDir == "right-to-left" {
			actualJustify = "right"
		} else {
			actualJustify = "left"
		}
	}

	builder := NewFigletBuilder(text, f, actualDir, width, actualJustify)
	for builder.IsNotFinished() {
		builder.AddCharToProduct()
		builder.GoToNextChar()
	}

	r := builder.ReturnProduct()

	if reverse {
		r = reverseString(r)
	}
	if flip {
		r = flipString(r)
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
