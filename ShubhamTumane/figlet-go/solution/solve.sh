#!/usr/bin/env bash
set -euo pipefail

cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete

mkdir -p /workspace/repo/fonts
if [ -d /workspace/repo/pyfiglet/fonts ]; then
    cp -f /workspace/repo/pyfiglet/fonts/*.flf /workspace/repo/fonts/
fi

cat << 'EOF' > /workspace/repo/go.mod
module figletgo

go 1.23
EOF

cat << 'EOF' > /workspace/repo/main.go
package main

import (
"embed"
"fmt"
"os"
"path/filepath"
"regexp"
"strconv"
"strings"
"unicode"
)

//go:embed fonts/*.flf
var embeddedFonts embed.FS

const (
SmEqual     = 1
SmLowline   = 2
SmHierarchy = 4
SmPair      = 8
SmBigX      = 16
SmHardblank = 32
SmKern      = 64
SmSmush     = 128
)

type Font struct {
Hardblank      rune
Height         int
Baseline       int
MaxLength      int
OldLayout      int
CommentLines   int
PrintDirection int
FullLayout     int
HasFullLayout  bool
SmushMode      int
Chars          map[rune][][]rune
Widths         map[rune]int
}

var reMagic = regexp.MustCompile(`^[tf]lf2.`)

func parseFontData(raw string) (*Font, error) {
// Match pyfiglet line splitting (CRLF/LF/CR only, replace unicode line separators with space)
replacer := strings.NewReplacer("\u0085", " ", "\u2028", " ", "\u2029", " ")
raw = replacer.Replace(raw)
raw = strings.ReplaceAll(raw, "\r\n", "\n")
raw = strings.ReplaceAll(raw, "\r", "\n")
lines := strings.Split(raw, "\n")
if len(lines) == 0 || !reMagic.MatchString(lines[0]) {
return nil, fmt.Errorf("invalid flf header")
}

headerLine := reMagic.ReplaceAllString(lines[0], "")
header := strings.Fields(headerLine)
if len(header) < 6 {
return nil, fmt.Errorf("incomplete flf header")
}

hbRunes := []rune(header[0])
hardblank := ' '
if len(hbRunes) > 0 {
hardblank = hbRunes[0]
}
height, _ := strconv.Atoi(header[1])
baseline, _ := strconv.Atoi(header[2])
maxLen, _ := strconv.Atoi(header[3])
oldLayout, _ := strconv.Atoi(header[4])
commentLines, _ := strconv.Atoi(header[5])
printDir := 0
if len(header) > 6 {
printDir, _ = strconv.Atoi(header[6])
}
fullLayout := 0
hasFull := false
if len(header) > 7 {
fullLayout, _ = strconv.Atoi(header[7])
hasFull = true
} else {
if oldLayout == 0 {
fullLayout = 64
} else if oldLayout < 0 {
fullLayout = 0
} else {
fullLayout = (oldLayout & 31) | 128
}
}

f := &Font{
Hardblank:      hardblank,
Height:         height,
Baseline:       baseline,
MaxLength:      maxLen,
OldLayout:      oldLayout,
CommentLines:   commentLines,
PrintDirection: printDir,
FullLayout:     fullLayout,
HasFullLayout:  hasFull,
SmushMode:      fullLayout,
Chars:          make(map[rune][][]rune),
Widths:         make(map[rune]int),
}

idx := 1 + commentLines
readGlyph := func() (int, [][]rune, bool) {
if idx+height > len(lines) {
return 0, nil, false
}
glyph := make([][]rune, height)
w := 0
var endRe *regexp.Regexp
for r := 0; r < height; r++ {
line := lines[idx+r]
if endRe == nil {
trimmed := strings.TrimRight(line, " \t\r\n")
tRunes := []rune(trimmed)
if len(tRunes) > 0 {
endCh := string(tRunes[len(tRunes)-1])
endRe = regexp.MustCompile(regexp.QuoteMeta(endCh) + `{1,2}\s*$`)
}
}
if endRe != nil {
line = endRe.ReplaceAllString(line, "")
}
runes := []rune(line)
if len(runes) > w {
w = len(runes)
}
glyph[r] = runes
}
idx += height
return w, glyph, true
}

joinedNonEmpty := func(g [][]rune) bool {
for _, row := range g {
if len(row) > 0 {
return true
}
}
return false
}

for ch := rune(32); ch < 127; ch++ {
if w, g, ok := readGlyph(); ok {
if ch == 32 || joinedNonEmpty(g) {
f.Chars[ch] = g
f.Widths[ch] = w
}
}
}
for _, ch := range []rune{'Ä', 'Ö', 'Ü', 'ä', 'ö', 'ü', 'ß'} {
if w, g, ok := readGlyph(); ok && joinedNonEmpty(g) {
f.Chars[ch] = g
f.Widths[ch] = w
}
}
for idx < len(lines) {
tagLine := strings.TrimSpace(lines[idx])
idx++
if tagLine == "" {
continue
}
codeStr := strings.SplitN(tagLine, " ", 2)[0]
if strings.HasPrefix(codeStr, "0x") || strings.HasPrefix(codeStr, "0X") {
code, err := strconv.ParseInt(codeStr[2:], 16, 64)
w, g, ok := readGlyph()
if !ok {
break
}
if err == nil && code >= 0 && joinedNonEmpty(g) {
f.Chars[rune(code)] = g
f.Widths[rune(code)] = w
}
}
}
return f, nil
}

func loadFont(name string) (*Font, error) {
base := name
if !strings.HasSuffix(base, ".flf") {
base += ".flf"
}
if data, err := embeddedFonts.ReadFile("fonts/" + filepath.Base(base)); err == nil {
return parseFontData(string(data))
}
for _, p := range []string{name, base, filepath.Join("/workspace/repo/fonts", filepath.Base(base)), filepath.Join("/workspace/repo/pyfiglet/fonts", filepath.Base(base))} {
if data, err := os.ReadFile(p); err == nil {
return parseFontData(string(data))
}
}
return nil, fmt.Errorf("font not found: %s", name)
}

var reverseMap = []rune(
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
"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff")

var flipMap = []rune(
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
"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff")

type BlankMarker struct {
Buf  [][]rune
Iter int
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
queue             [][][]rune
buffer            [][]rune
}

func newBuilder(text string, font *Font, direction string, width int, justify string) *Builder {
buf := make([][]rune, font.Height)
for i := range buf {
buf[i] = []rune{}
}
return &Builder{
text:      []rune(text),
direction: direction,
width:     width,
font:      font,
justify:   justify,
buffer:    buf,
}
}

func cloneBuffer(b [][]rune) [][]rune {
c := make([][]rune, len(b))
for i := range b {
cp := make([]rune, len(b[i]))
copy(cp, b[i])
c[i] = cp
}
return c
}

func (b *Builder) smushChars(left, right rune) (rune, bool) {
if left == ' ' {
return right, true
}
if right == ' ' {
return left, true
}
if b.prevCharWidth < 2 || b.curCharWidth < 2 {
return 0, false
}
if (b.font.SmushMode & SmSmush) == 0 {
return 0, false
}
if (b.font.SmushMode & 63) == 0 {
if left == b.font.Hardblank {
return right, true
}
if right == b.font.Hardblank {
return left, true
}
if b.direction == "right-to-left" {
return left, true
}
return right, true
}
if (b.font.SmushMode & SmHardblank) != 0 {
if left == b.font.Hardblank && right == b.font.Hardblank {
return left, true
}
}
if left == b.font.Hardblank || right == b.font.Hardblank {
return 0, false
}
if (b.font.SmushMode & SmEqual) != 0 {
if left == right {
return left, true
}
}
if (b.font.SmushMode & SmLowline) != 0 {
if left == '_' && strings.ContainsRune(`|/\[]{}()<>`, right) {
return right, true
}
if right == '_' && strings.ContainsRune(`|/\[]{}()<>`, left) {
return left, true
}
}
if (b.font.SmushMode & SmHierarchy) != 0 {
pairs := [][2]string{
{"|", `/\[]{}()<>`},
{`\/`, "[]{}()<>"},
{"[]", "{}()<>"},
{"{}", "()<>"},
{"()", "<>"},
}
for _, p := range pairs {
if strings.ContainsRune(p[0], left) && strings.ContainsRune(p[1], right) {
return right, true
}
if strings.ContainsRune(p[0], right) && strings.ContainsRune(p[1], left) {
return left, true
}
}
}
if (b.font.SmushMode & SmPair) != 0 {
s := string([]rune{left, right})
r := string([]rune{right, left})
if s == "[]" || r == "[]" || s == "{}" || r == "{}" || s == "()" || r == "()" {
return '|', true
}
}
if (b.font.SmushMode & SmBigX) != 0 {
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

func (b *Builder) smushAmount(curChar [][]rune) int {
if (b.font.SmushMode & (SmSmush | SmKern)) == 0 {
return 0
}
maxSmush := b.curCharWidth
for row := 0; row < b.font.Height; row++ {
lineLeft := b.buffer[row]
lineRight := curChar[row]
if b.direction == "right-to-left" {
lineLeft, lineRight = lineRight, lineLeft
}

rEnd := len(lineLeft)
for rEnd > 0 && lineLeft[rEnd-1] == ' ' {
rEnd--
}
linebd := rEnd - 1
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
}

charbd := 0
for charbd < len(lineRight) && lineRight[charbd] == ' ' {
charbd++
}
var ch2 rune
hasCh2 := false
if charbd < len(lineRight) {
ch2 = lineRight[charbd]
hasCh2 = true
}

amt := charbd + len(lineLeft) - 1 - linebd
if !hasCh1 || ch1 == ' ' {
amt++
} else if hasCh2 {
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

func (b *Builder) addCurCharRowToBufferRow(curChar [][]rune, row int) {
addLeft := make([]rune, len(b.buffer[row]))
copy(addLeft, b.buffer[row])
addRight := make([]rune, len(curChar[row]))
copy(addRight, curChar[row])

if b.direction == "right-to-left" {
addLeft, addRight = addRight, addLeft
}

for i := 0; i < b.maxSmush; i++ {
idx := len(addLeft) - b.maxSmush + i
var left rune
hasLeft := false
if idx >= 0 && idx < len(addLeft) {
left = addLeft[idx]
hasLeft = true
}
right := addRight[i]
if hasLeft {
if sm, ok := b.smushChars(left, right); ok && idx >= 0 && idx < len(addLeft) {
addLeft[idx] = sm
}
}
}

b.buffer[row] = append(addLeft, addRight[b.maxSmush:]...)
}

func (b *Builder) cutBufferCommon() {
b.currentTotalWidth = 0
b.buffer = make([][]rune, b.font.Height)
for i := range b.buffer {
b.buffer[i] = []rune{}
}
b.blankMarkers = nil
b.prevCharWidth = 0
if b.iterator >= 0 && b.iterator < len(b.text) {
c := b.text[b.iterator]
if curChar, ok := b.font.Chars[c]; ok {
b.maxSmush = b.smushAmount(curChar)
}
}
}

func (b *Builder) handleNewLine() {
if len(b.blankMarkers) > 0 {
last := b.blankMarkers[len(b.blankMarkers)-1]
b.blankMarkers = b.blankMarkers[:len(b.blankMarkers)-1]
b.queue = append(b.queue, last.Buf)
b.iterator = last.Iter
b.cutBufferCommon()
} else {
b.queue = append(b.queue, b.buffer)
b.iterator--
b.cutBufferCommon()
}
}

func (b *Builder) render() (string, error) {
for b.iterator < len(b.text) {
c := b.text[b.iterator]
if c == '\n' {
b.blankMarkers = append(b.blankMarkers, BlankMarker{Buf: cloneBuffer(b.buffer), Iter: b.iterator})
b.handleNewLine()
b.iterator++
continue
}
curChar, ok := b.font.Chars[c]
if !ok {
b.iterator++
continue
}
curW := b.font.Widths[c]
if b.width < curW {
return "", fmt.Errorf("width too narrow")
}
b.curCharWidth = curW
b.maxSmush = b.smushAmount(curChar)
b.currentTotalWidth = len(b.buffer[0]) + b.curCharWidth - b.maxSmush

if c == ' ' {
b.blankMarkers = append(b.blankMarkers, BlankMarker{Buf: cloneBuffer(b.buffer), Iter: b.iterator})
}
if b.currentTotalWidth >= b.width {
b.handleNewLine()
} else {
for row := 0; row < b.font.Height; row++ {
b.addCurCharRowToBufferRow(curChar, row)
}
}
b.prevCharWidth = b.curCharWidth
b.iterator++
}

if len(b.buffer[0]) != 0 {
b.queue = append(b.queue, b.buffer)
}

var acc strings.Builder
for _, buf := range b.queue {
for row := 0; row < b.font.Height; row++ {
line := string(buf[row])
if b.justify == "right" {
pad := b.width - len(buf[row]) - 1
if pad > 0 {
line = strings.Repeat(" ", pad) + line
}
} else if b.justify == "center" {
pad := (b.width - len(buf[row])) / 2
if pad > 0 {
line = strings.Repeat(" ", pad) + line
}
}
line = strings.ReplaceAll(line, string(b.font.Hardblank), " ")
acc.WriteString(line)
acc.WriteByte('\n')
}
}
return acc.String(), nil
}

func reverseFiglet(s string) string {
lines := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
out := make([]string, len(lines))
for i, line := range lines {
runes := []rune(line)
rev := make([]rune, len(runes))
for j, r := range runes {
if int(r) < len(reverseMap) {
r = reverseMap[r]
}
rev[len(runes)-1-j] = r
}
out[i] = string(rev)
}
return strings.Join(out, "\n") + "\n"
}

func flipFiglet(s string) string {
lines := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
out := make([]string, len(lines))
for i := range lines {
runes := []rune(lines[len(lines)-1-i])
mapped := make([]rune, len(runes))
for j, r := range runes {
if int(r) < len(flipMap) {
r = flipMap[r]
}
mapped[j] = r
}
out[i] = string(mapped)
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
return strings.TrimRightFunc(joined, unicode.IsSpace)
}

func normalizeSurroundingNewlines(s string) string {
return "\n" + stripSurroundingNewlines(s) + "\n"
}

func main() {
fontName, width, justify, direction := "standard", 80, "auto", "auto"
reverse, flip, stripNL, normNL := false, false, false, false
var textArgs []string
args := os.Args[1:]
for i := 0; i < len(args); i++ {
arg := args[i]
if arg == "--" {
textArgs = append(textArgs, args[i+1:]...)
break
}
if len(arg) > 1 && arg[0] == '-' {
switch arg {
case "-f":
if i+1 < len(args) {
i++
fontName = args[i]
}
case "-w":
if i+1 < len(args) {
i++
if v, err := strconv.Atoi(args[i]); err == nil {
width = v
}
}
case "-j":
if i+1 < len(args) {
i++
justify = args[i]
}
case "-D":
if i+1 < len(args) {
i++
direction = args[i]
}
case "-r":
reverse = true
case "-F":
flip = true
case "-s":
stripNL = true
case "-n":
normNL = true
}
} else {
textArgs = append(textArgs, arg)
}
}

font, err := loadFont(fontName)
if err != nil {
os.Exit(1)
}

dir := direction
if dir == "auto" {
if font.PrintDirection == 1 {
dir = "right-to-left"
} else {
dir = "left-to-right"
}
}
just := justify
if just == "auto" {
if dir == "right-to-left" {
just = "right"
} else {
just = "left"
}
}

text := strings.Join(textArgs, " ")
b := newBuilder(text, font, dir, width, just)
out, err := b.render()
if err != nil {
os.Exit(1)
}
if reverse {
out = reverseFiglet(out)
}
if flip {
out = flipFiglet(out)
}
if stripNL {
out = stripSurroundingNewlines(out)
} else if normNL {
out = normalizeSurroundingNewlines(out)
}
fmt.Println(out)
}
EOF

go build -o /tmp/figlet .
go build ./...
