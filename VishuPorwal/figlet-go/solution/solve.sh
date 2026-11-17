#!/bin/bash
set -euo pipefail

cd /workspace/repo

# Copy standard .flf fonts into fonts/ directory for go:embed
mkdir -p fonts
cp pyfiglet/fonts/*.flf fonts/

# Write go.mod
cat <<'EOF' > go.mod
module figlet

go 1.23
EOF

# Write main.go
cat <<'EOF' > main.go
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
	smEqual     = 1
	smLowline   = 2
	smHierarchy = 4
	smPair      = 8
	smBigX      = 16
	smHardblank = 32
	smKern      = 64
	smSmush     = 128
)

type Font struct {
	hardBlank      rune
	height         int
	baseLine       int
	maxLength      int
	oldLayout      int
	commentLines   int
	printDirection int
	smushMode      int
	chars          map[rune][]string
	width          map[rune]int
}

func loadFont(name string) (*Font, error) {
	cleanName := strings.TrimSuffix(name, ".flf")
	fileName := cleanName + ".flf"

	var data []byte
	var err error

	data, err = embeddedFonts.ReadFile("fonts/" + fileName)
	if err != nil {
		candidates := []string{
			"fonts/" + fileName,
			"pyfiglet/fonts/" + fileName,
			"pyfiglet/fonts-standard/" + fileName,
			"/workspace/repo/fonts/" + fileName,
			"/workspace/repo/pyfiglet/fonts/" + fileName,
			"/workspace/repo/pyfiglet/fonts-standard/" + fileName,
			fileName,
			name,
		}
		for _, c := range candidates {
			data, err = os.ReadFile(c)
			if err == nil {
				break
			}
		}
	}
	if err != nil || len(data) == 0 {
		return nil, fmt.Errorf("requested font %q not found", name)
	}

	return parseFont(string(data), name)
}

func parseFont(raw string, fontName string) (*Font, error) {
	reLineSplit := regexp.MustCompile("[\u0085\u2028\u2029]")
	raw = reLineSplit.ReplaceAllString(raw, " ")

	raw = strings.ReplaceAll(raw, "\r\n", "\n")
	raw = strings.ReplaceAll(raw, "\r", "\n")
	if strings.HasSuffix(raw, "\n") {
		raw = raw[:len(raw)-1]
	}
	lines := strings.Split(raw, "\n")
	if len(lines) == 0 {
		return nil, fmt.Errorf("%s is not a valid figlet font", fontName)
	}

	headerLine := lines[0]
	lines = lines[1:]

	reMagic := regexp.MustCompile(`^[tf]lf2.`)
	if !reMagic.MatchString(headerLine) {
		return nil, fmt.Errorf("%s is not a valid figlet font", fontName)
	}

	headerNoMagic := reMagic.ReplaceAllString(headerLine, "")
	fields := strings.Fields(headerNoMagic)
	if len(fields) < 6 {
		return nil, fmt.Errorf("malformed header for %s", fontName)
	}

	hardBlankRunes := []rune(fields[0])
	if len(hardBlankRunes) == 0 {
		return nil, fmt.Errorf("malformed header for %s", fontName)
	}
	hardBlank := hardBlankRunes[0]

	height, err := strconv.Atoi(fields[1])
	if err != nil {
		return nil, err
	}
	baseLine, _ := strconv.Atoi(fields[2])
	maxLength, _ := strconv.Atoi(fields[3])
	oldLayout, _ := strconv.Atoi(fields[4])
	commentLines, err := strconv.Atoi(fields[5])
	if err != nil {
		return nil, err
	}

	printDirection := 0
	if len(fields) > 6 {
		if val, err := strconv.Atoi(fields[6]); err == nil {
			printDirection = val
		}
	}

	fullLayout := -1
	if len(fields) > 7 {
		if val, err := strconv.Atoi(fields[7]); err == nil {
			fullLayout = val
		}
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

	if len(lines) < commentLines {
		return nil, fmt.Errorf("not enough lines for comments in %s", fontName)
	}
	lines = lines[commentLines:]

	font := &Font{
		hardBlank:      hardBlank,
		height:         height,
		baseLine:       baseLine,
		maxLength:      maxLength,
		oldLayout:      oldLayout,
		commentLines:   commentLines,
		printDirection: printDirection,
		smushMode:      fullLayout,
		chars:          make(map[rune][]string),
		width:          make(map[rune]int),
	}

	parseGlyph := func() (int, []string, bool) {
		if len(lines) < height {
			return 0, nil, false
		}
		var endRegex *regexp.Regexp
		rows := make([]string, 0, height)
		maxWidth := 0
		reEndMarker := regexp.MustCompile(`(.)\s*$`)

		for r := 0; r < height; r++ {
			line := lines[0]
			lines = lines[1:]
			if endRegex == nil {
				m := reEndMarker.FindStringSubmatch(line)
				if len(m) > 1 {
					endChar := m[1]
					endRegex = regexp.MustCompile(regexp.QuoteMeta(endChar) + `{1,2}\s*$`)
				}
			}
			if endRegex != nil {
				line = endRegex.ReplaceAllString(line, "")
			}
			lineLen := len([]rune(line))
			if lineLen > maxWidth {
				maxWidth = lineLen
			}
			rows = append(rows, line)
		}
		return maxWidth, rows, true
	}

	// Standard ASCII: 32 to 126
	for i := 32; i <= 126; i++ {
		w, rows, ok := parseGlyph()
		if !ok {
			break
		}
		allEmpty := true
		for _, r := range rows {
			if len(r) > 0 {
				allEmpty = false
				break
			}
		}
		if i == 32 || !allEmpty {
			font.chars[rune(i)] = rows
			font.width[rune(i)] = w
		}
	}

	// German Umlauts: ÄÖÜäöüß
	germanUmlauts := []rune{'Ä', 'Ö', 'Ü', 'ä', 'ö', 'ü', 'ß'}
	if len(lines) > 0 {
		for _, ch := range germanUmlauts {
			if len(lines) < height {
				break
			}
			w, rows, ok := parseGlyph()
			if !ok {
				break
			}
			allEmpty := true
			for _, r := range rows {
				if len(r) > 0 {
					allEmpty = false
					break
				}
			}
			if !allEmpty {
				font.chars[ch] = rows
				font.width[ch] = w
			}
		}
	}

	// Extended ASCII
	for len(lines) > 0 {
		line := strings.TrimSpace(lines[0])
		lines = lines[1:]
		if line == "" {
			continue
		}
		tok := strings.SplitN(line, " ", 2)[0]
		if strings.HasPrefix(strings.ToLower(tok), "0x") {
			code, err := strconv.ParseInt(tok[2:], 16, 64)
			if err == nil {
				w, rows, ok := parseGlyph()
				if ok {
					allEmpty := true
					for _, r := range rows {
						if len(r) > 0 {
							allEmpty = false
							break
						}
					}
					if !allEmpty {
						font.chars[rune(code)] = rows
						font.width[rune(code)] = w
					}
				}
			}
		}
	}

	return font, nil
}

type blankMarker struct {
	buffer   []string
	iterator int
}

type FigletBuilder struct {
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
	productQueue      [][]string
	buffer            []string
}

func newFigletBuilder(text string, font *Font, dir string, width int, justify string) *FigletBuilder {
	resolvedDir := dir
	if resolvedDir == "auto" {
		if font.printDirection == 1 {
			resolvedDir = "right-to-left"
		} else {
			resolvedDir = "left-to-right"
		}
	}

	resolvedJustify := justify
	if resolvedJustify == "auto" {
		if resolvedDir == "right-to-left" {
			resolvedJustify = "right"
		} else {
			resolvedJustify = "left"
		}
	}

	buf := make([]string, font.height)
	return &FigletBuilder{
		text:         []rune(text),
		font:         font,
		direction:    resolvedDir,
		width:        width,
		justify:      resolvedJustify,
		buffer:       buf,
		productQueue: make([][]string, 0),
	}
}

func (b *FigletBuilder) smushChars(left, right rune) (rune, bool) {
	if left == ' ' {
		return right, true
	}
	if right == ' ' {
		return left, true
	}
	if b.prevCharWidth < 2 || b.curCharWidth < 2 {
		return 0, false
	}
	if (b.font.smushMode & smSmush) == 0 {
		return 0, false
	}

	hb := b.font.hardBlank

	if (b.font.smushMode & 63) == 0 {
		if left == hb {
			return right, true
		}
		if right == hb {
			return left, true
		}
		if b.direction == "right-to-left" {
			return left, true
		}
		return right, true
	}

	if (b.font.smushMode & smHardblank) != 0 {
		if left == hb && right == hb {
			return left, true
		}
	}
	if left == hb || right == hb {
		return 0, false
	}

	if (b.font.smushMode & smEqual) != 0 {
		if left == right {
			return left, true
		}
	}

	const lowlineClass = `|/\[]{}()<>`
	if (b.font.smushMode & smLowline) != 0 {
		if left == '_' && strings.ContainsRune(lowlineClass, right) {
			return right, true
		}
		if right == '_' && strings.ContainsRune(lowlineClass, left) {
			return left, true
		}
	}

	if (b.font.smushMode & smHierarchy) != 0 {
		hierarchy := []struct {
			a, b string
		}{
			{"|", `/\[]{}()<>`},
			{`\/`, `[]{}()<>`},
			{"[]", `{}()<>`},
			{"{}", `()<>`},
			{"()", `<>`},
		}
		for _, pair := range hierarchy {
			if strings.ContainsRune(pair.a, left) && strings.ContainsRune(pair.b, right) {
				return right, true
			}
			if strings.ContainsRune(pair.a, right) && strings.ContainsRune(pair.b, left) {
				return left, true
			}
		}
	}

	if (b.font.smushMode & smPair) != 0 {
		if (left == '[' && right == ']') || (left == ']' && right == '[') ||
			(left == '{' && right == '}') || (left == '}' && right == '{') ||
			(left == '(' && right == ')') || (left == ')' && right == '(') {
			return '|', true
		}
	}

	if (b.font.smushMode & smBigX) != 0 {
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

func (b *FigletBuilder) smushAmount(buffer []string, curChar []string) int {
	if (b.font.smushMode & (smSmush | smKern)) == 0 {
		return 0
	}

	maxSmush := b.curCharWidth
	for row := 0; row < b.font.height; row++ {
		lineLeft := buffer[row]
		lineRight := curChar[row]
		if b.direction == "right-to-left" {
			lineLeft, lineRight = lineRight, lineLeft
		}

		trimmedLeft := strings.TrimRight(lineLeft, " ")
		leftRunes := []rune(lineLeft)
		trimmedLeftRunes := []rune(trimmedLeft)
		linebd := len(trimmedLeftRunes) - 1
		if linebd < 0 {
			linebd = 0
		}

		var ch1 rune
		if linebd < len(leftRunes) {
			ch1 = leftRunes[linebd]
		} else {
			linebd = 0
			ch1 = 0
		}

		trimmedRight := strings.TrimLeft(lineRight, " ")
		rightRunes := []rune(lineRight)
		trimmedRightRunes := []rune(trimmedRight)
		charbd := len(rightRunes) - len(trimmedRightRunes)
		var ch2 rune
		if charbd < len(rightRunes) {
			ch2 = rightRunes[charbd]
		} else {
			charbd = len(rightRunes)
			ch2 = 0
		}

		amt := charbd + len(leftRunes) - 1 - linebd

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

func (b *FigletBuilder) smushRow(curChar []string, row int) ([]rune, []rune) {
	addLeft := []rune(b.buffer[row])
	addRight := []rune(curChar[row])

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
		smushed, ok := b.smushChars(left, right)
		if ok && idx >= 0 && idx < len(addLeft) {
			addLeft[idx] = smushed
		}
	}
	return addLeft, addRight
}

func (b *FigletBuilder) addCurCharRowToBufferRow(curChar []string, row int) {
	addLeft, addRight := b.smushRow(curChar, row)
	var remainder []rune
	if b.maxSmush < len(addRight) {
		remainder = addRight[b.maxSmush:]
	}
	b.buffer[row] = string(append(addLeft, remainder...))
}

func (b *FigletBuilder) cutBufferCommon() {
	b.currentTotalWidth = 0
	b.buffer = make([]string, b.font.height)
	b.blankMarkers = nil
	b.prevCharWidth = 0
	if b.iterator >= 0 && b.iterator < len(b.text) {
		c := b.text[b.iterator]
		if curChar, ok := b.font.chars[c]; ok {
			b.maxSmush = b.smushAmount(b.buffer, curChar)
		}
	}
}

func (b *FigletBuilder) cutBufferAtLastBlank(saved []string, savedIter int) {
	b.productQueue = append(b.productQueue, saved)
	b.iterator = savedIter
	b.cutBufferCommon()
}

func (b *FigletBuilder) cutBufferAtLastChar() {
	flushed := make([]string, len(b.buffer))
	copy(flushed, b.buffer)
	b.productQueue = append(b.productQueue, flushed)
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

func (b *FigletBuilder) addCharToProduct() {
	c := b.text[b.iterator]

	if c == '\n' {
		saved := make([]string, len(b.buffer))
		copy(saved, b.buffer)
		b.blankMarkers = append(b.blankMarkers, blankMarker{
			buffer:   saved,
			iterator: b.iterator,
		})
		b.handleNewLine()
		return
	}

	curChar, ok := b.font.chars[c]
	if !ok {
		return
	}

	curWidth := b.font.width[c]
	if b.width < curWidth {
		return
	}

	b.curCharWidth = curWidth
	b.maxSmush = b.smushAmount(b.buffer, curChar)
	b.currentTotalWidth = len([]rune(b.buffer[0])) + b.curCharWidth - b.maxSmush

	if c == ' ' {
		saved := make([]string, len(b.buffer))
		copy(saved, b.buffer)
		b.blankMarkers = append(b.blankMarkers, blankMarker{
			buffer:   saved,
			iterator: b.iterator,
		})
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

func (b *FigletBuilder) render() string {
	for b.iterator < len(b.text) {
		b.addCharToProduct()
		b.iterator++
	}
	return b.returnProduct()
}

func (b *FigletBuilder) returnProduct() string {
	if len(b.buffer) > 0 && b.buffer[0] != "" {
		flushed := make([]string, len(b.buffer))
		copy(flushed, b.buffer)
		b.productQueue = append(b.productQueue, flushed)
	}
	var sb strings.Builder
	for _, buf := range b.productQueue {
		justified := b.justifyString(buf)
		replaced := b.replaceHardblanks(justified)
		sb.WriteString(replaced)
	}
	return sb.String()
}

func (b *FigletBuilder) justifyString(buffer []string) []string {
	out := make([]string, len(buffer))
	copy(out, buffer)
	if b.justify == "right" {
		for row := 0; row < b.font.height; row++ {
			pad := b.width - len([]rune(out[row])) - 1
			if pad > 0 {
				out[row] = strings.Repeat(" ", pad) + out[row]
			}
		}
	} else if b.justify == "center" {
		for row := 0; row < b.font.height; row++ {
			pad := (b.width - len([]rune(out[row]))) / 2
			if pad > 0 {
				out[row] = strings.Repeat(" ", pad) + out[row]
			}
		}
	}
	return out
}

func (b *FigletBuilder) replaceHardblanks(buffer []string) string {
	joined := strings.Join(buffer, "\n") + "\n"
	return strings.ReplaceAll(joined, string(b.font.hardBlank), " ")
}

func splitLines(s string) []string {
	if len(s) == 0 {
		return []string{}
	}
	hasTrailing := false
	if strings.HasSuffix(s, "\r\n") {
		s = s[:len(s)-2]
		hasTrailing = true
	} else if strings.HasSuffix(s, "\n") {
		s = s[:len(s)-1]
		hasTrailing = true
	}
	if len(s) == 0 && hasTrailing {
		return []string{""}
	}
	s = strings.ReplaceAll(s, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	return strings.Split(s, "\n")
}

func translateReverse(r rune) rune {
	switch r {
	case '(':
		return ')'
	case ')':
		return '('
	case '/':
		return '\\'
	case '\\':
		return '/'
	case '<':
		return '>'
	case '>':
		return '<'
	case '[':
		return ']'
	case ']':
		return '['
	case '{':
		return '}'
	case '}':
		return '{'
	default:
		return r
	}
}

func reverseFiglet(s string) string {
	lines := splitLines(s)
	out := make([]string, len(lines))
	for i, line := range lines {
		runes := []rune(line)
		n := len(runes)
		rev := make([]rune, n)
		for j := 0; j < n; j++ {
			rev[n-1-j] = translateReverse(runes[j])
		}
		out[i] = string(rev)
	}
	return strings.Join(out, "\n") + "\n"
}

func translateFlip(r rune) rune {
	switch r {
	case '/':
		return '\\'
	case '\\':
		return '/'
	case 'A':
		return 'V'
	case 'V':
		return 'A'
	case 'M':
		return 'W'
	case 'W':
		return 'M'
	case 'P':
		return 'b'
	case 'R':
		return 'b'
	case 'b':
		return 'P'
	case 'm':
		return 'w'
	case 'w':
		return 'm'
	case '^':
		return 'v'
	case 'v':
		return '^'
	case '_':
		return '-'
	default:
		return r
	}
}

func flipFiglet(s string) string {
	lines := splitLines(s)
	out := make([]string, len(lines))
	n := len(lines)
	for i := 0; i < n; i++ {
		line := lines[n-1-i]
		runes := []rune(line)
		flipped := make([]rune, len(runes))
		for j, r := range runes {
			flipped[j] = translateFlip(r)
		}
		out[i] = string(flipped)
	}
	return strings.Join(out, "\n") + "\n"
}

func stripSurroundingNewlines(s string) string {
	lines := splitLines(s)
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
	strip := false
	normalize := false

	args := os.Args[1:]
	var textArgs []string
	stopOptions := false

	for i := 0; i < len(args); {
		arg := args[i]
		if !stopOptions {
			if arg == "--" {
				stopOptions = true
				i++
				continue
			} else if arg == "-f" || arg == "--font" {
				if i+1 < len(args) {
					fontName = args[i+1]
					i += 2
					continue
				}
			} else if strings.HasPrefix(arg, "-f=") || strings.HasPrefix(arg, "--font=") {
				fontName = strings.SplitN(arg, "=", 2)[1]
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
			} else if strings.HasPrefix(arg, "-w=") || strings.HasPrefix(arg, "--width=") {
				if val, err := strconv.Atoi(strings.SplitN(arg, "=", 2)[1]); err == nil {
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
			} else if strings.HasPrefix(arg, "-j=") || strings.HasPrefix(arg, "--justify=") {
				justify = strings.SplitN(arg, "=", 2)[1]
				i++
				continue
			} else if arg == "-D" || arg == "--direction" {
				if i+1 < len(args) {
					direction = args[i+1]
					i += 2
					continue
				}
			} else if strings.HasPrefix(arg, "-D=") || strings.HasPrefix(arg, "--direction=") {
				direction = strings.SplitN(arg, "=", 2)[1]
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
				strip = true
				i++
				continue
			} else if arg == "-n" || arg == "--normalize-surrounding-newlines" {
				normalize = true
				i++
				continue
			}
		}
		textArgs = append(textArgs, arg)
		i++
	}

	if len(textArgs) == 0 {
		fmt.Fprintf(os.Stderr, "Usage: %s [options] [text..]\n", os.Args[0])
		os.Exit(1)
	}

	text := strings.Join(textArgs, " ")

	font, err := loadFont(fontName)
	if err != nil {
		fmt.Printf("pyfiglet error: requested font '%s' not found.\n", fontName)
		os.Exit(1)
	}

	builder := newFigletBuilder(text, font, direction, width, justify)
	r := builder.render()

	if reverse {
		r = reverseFiglet(r)
	}
	if flip {
		r = flipFiglet(r)
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

# Delete every Python file under /workspace/repo
find /workspace/repo -type f -iname "*.py" -delete
find /workspace/repo -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Clean build checks required by instruction.md
go build -o /tmp/figlet .
go build ./...
