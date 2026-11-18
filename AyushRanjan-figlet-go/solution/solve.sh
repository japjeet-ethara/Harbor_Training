#!/bin/bash
set -euo pipefail

cd /workspace/repo

if [ ! -d pyfiglet/fonts ] || [ -z "$(find pyfiglet/fonts -maxdepth 1 -type f -name '*.flf' -print -quit)" ]; then
  echo "prepared standard FIGlet fonts are missing under pyfiglet/fonts" >&2
  exit 1
fi

cat > go.mod <<'EOF'
module figletgo

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"bufio"
	"embed"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path"
	"strconv"
	"strings"
	"unicode"
)

//go:embed pyfiglet/fonts/*.flf
var fontFiles embed.FS

const usage = `Usage: pyfiglet [options] [text..]

Options:
  -f FONT, --font=FONT
  -w COLS, --width=COLS
  -j SIDE, --justify=SIDE (auto, left, center, right)
  -D DIRECTION, --direction=DIRECTION (auto, left-to-right, right-to-left)
  -r, --reverse
  -F, --flip
  -s, --strip-surrounding-newlines
  -n, --normalize-surrounding-newlines
`

type font struct {
	name          string
	height        int
	hardBlank     rune
	printDirection int
	smushMode     int
	glyphs        map[rune][]string
	widths        map[rune]int
}

type options struct {
	font, direction, justify string
	width                    int
	reverse, flip, strip, normalize bool
}

func main() { os.Exit(run(os.Args[1:], os.Stdout, os.Stderr)) }

func run(args []string, stdout, stderr *os.File) int {
	opts := options{font: "standard", direction: "auto", justify: "auto", width: 80}
	textArgs, err := parseArgs(args, &opts)
	if err != nil {
		fmt.Fprintf(stderr, "pyfiglet: %v\n%s", err, usage)
		return 2
	}
	if len(textArgs) == 0 {
		fmt.Fprint(stdout, usage)
		return 1
	}
	fontData, err := loadFont(opts.font)
	if err != nil {
		fmt.Fprintf(stdout, "pyfiglet error: requested font %q not found.\n", opts.font)
		return 1
	}
	direction := opts.direction
	if direction == "auto" {
		if fontData.printDirection == 1 {
			direction = "right-to-left"
		} else {
			direction = "left-to-right"
		}
	}
	justify := opts.justify
	if justify == "auto" {
		if direction == "right-to-left" {
			justify = "right"
		} else {
			justify = "left"
		}
	}
	out, err := render(strings.Join(textArgs, " "), fontData, direction, justify, opts.width)
	if err != nil {
		fmt.Fprintf(stderr, "pyfiglet: %v\n", err)
		return 1
	}
	if opts.reverse {
		out = reverseArt(out)
	}
	if opts.flip {
		out = flipArt(out)
	}
	if opts.strip {
		out = stripSurrounding(out)
	} else if opts.normalize {
		out = "\n" + stripSurrounding(out) + "\n"
	}
	fmt.Fprint(stdout, out)
	fmt.Fprint(stdout, "\n")
	return 0
}

func parseArgs(args []string, o *options) ([]string, error) {
	var positional []string
	endOptions := false
	for i := 0; i < len(args); i++ {
		a := args[i]
		if endOptions {
			positional = append(positional, a)
			continue
		}
		if a == "--" {
			endOptions = true
			continue
		}
		if a == "-r" || a == "--reverse" { o.reverse = true; continue }
		if a == "-F" || a == "--flip" { o.flip = true; continue }
		if a == "-s" || a == "--strip-surrounding-newlines" { o.strip = true; continue }
		if a == "-n" || a == "--normalize-surrounding-newlines" { o.normalize = true; continue }
		key, value, hasValue := strings.Cut(a, "=")
		if strings.HasPrefix(a, "--") {
			switch key {
			case "--font":
				v, err := optionValue(args, &i, value, hasValue, "--font"); if err != nil { return nil, err }; o.font = v
			case "--width":
				v, err := optionValue(args, &i, value, hasValue, "--width"); if err != nil { return nil, err }; n, e := strconv.Atoi(v); if e != nil { return nil, fmt.Errorf("option --width: invalid integer %q", v) }; o.width = n
			case "--justify":
				v, err := optionValue(args, &i, value, hasValue, "--justify"); if err != nil { return nil, err }; o.justify = v
			case "--direction":
				v, err := optionValue(args, &i, value, hasValue, "--direction"); if err != nil { return nil, err }; o.direction = v
			default: return nil, fmt.Errorf("no such option: %s", key)
			}
			continue
		}
		if strings.HasPrefix(a, "-") && a != "-" {
			if len(a) > 2 && strings.ContainsRune("fwjD", rune(a[1])) {
				key, value, hasValue = a[:2], a[2:], true
			} else { key, value, hasValue = a, "", false }
			switch key {
			case "-f":
				v, err := optionValue(args, &i, value, hasValue, "-f"); if err != nil { return nil, err }; o.font = v
			case "-w":
				v, err := optionValue(args, &i, value, hasValue, "-w"); if err != nil { return nil, err }; n, e := strconv.Atoi(v); if e != nil { return nil, fmt.Errorf("option -w: invalid integer %q", v) }; o.width = n
			case "-j":
				v, err := optionValue(args, &i, value, hasValue, "-j"); if err != nil { return nil, err }; o.justify = v
			case "-D":
				v, err := optionValue(args, &i, value, hasValue, "-D"); if err != nil { return nil, err }; o.direction = v
			case "-r", "-F", "-s", "-n": return nil, fmt.Errorf("no such option: %s", a)
			default: return nil, fmt.Errorf("no such option: %s", a)
			}
			continue
		}
		positional = append(positional, a)
	}
	if o.direction != "auto" && o.direction != "left-to-right" && o.direction != "right-to-left" { return nil, fmt.Errorf("option -D: invalid choice: %q", o.direction) }
	if o.justify != "auto" && o.justify != "left" && o.justify != "center" && o.justify != "right" { return nil, fmt.Errorf("option -j: invalid choice: %q", o.justify) }
	return positional, nil
}

func optionValue(args []string, i *int, value string, hasValue bool, name string) (string, error) {
	if hasValue { return value, nil }
	if *i+1 >= len(args) { return "", fmt.Errorf("%s requires an argument", name) }
	*i++
	return args[*i], nil
}

func loadFont(name string) (*font, error) {
	for _, ext := range []string{"tlf", "flf"} {
		filename := path.Join("pyfiglet", "fonts", name+"."+ext)
		data, err := fontFiles.ReadFile(filename)
		if err == nil { return parseFont(name, string(data)) }
	}
	return nil, fs.ErrNotExist
}

func parseFont(name, data string) (*font, error) {
	s := bufio.NewScanner(strings.NewReader(data))
	var lines []string
	for s.Scan() { lines = append(lines, strings.TrimSuffix(s.Text(), "\r")) }
	if err := s.Err(); err != nil { return nil, err }
	if len(lines) == 0 || len(lines[0]) < 6 || !(strings.HasPrefix(lines[0], "flf2") || strings.HasPrefix(lines[0], "tlf2")) { return nil, fmt.Errorf("invalid FIGlet font %s", name) }
	fields := strings.Fields(lines[0][6:])
	if len(fields) < 5 { return nil, fmt.Errorf("malformed font header %s", name) }
	hard := []rune(lines[0][5:6])[0]
	vals := make([]int, 7)
	for i := range vals { if i < len(fields) { n, e := strconv.Atoi(fields[i]); if e != nil { return nil, fmt.Errorf("malformed font header %s", name) }; vals[i] = n } }
	height, oldLayout, comments := vals[0], vals[3], vals[4]
	if height <= 0 || height > 100 || comments < 0 || comments > len(lines)-1 { return nil, fmt.Errorf("invalid font dimensions %s", name) }
	printDirection, fullLayout := 0, -1
	if len(fields) > 5 { printDirection, _ = strconv.Atoi(fields[5]) }
	if len(fields) > 6 { fullLayout, _ = strconv.Atoi(fields[6]) }
	if fullLayout < 0 {
		if oldLayout == 0 { fullLayout = 64 } else if oldLayout < 0 { fullLayout = 0 } else { fullLayout = (oldLayout & 31) | 128 }
	}
	idx := 1 + comments
	f := &font{name: name, height: height, hardBlank: hard, printDirection: printDirection, smushMode: fullLayout, glyphs: map[rune][]string{}, widths: map[rune]int{}}
	readGlyph := func() ([]string, int, error) {
		if idx+height > len(lines) { return nil, 0, errors.New("truncated glyph data") }
		rows := make([]string, height); width := 0; marker := rune(0)
		for row := 0; row < height; row++ {
			line := lines[idx]; idx++
			trimmed := strings.TrimRight(line, " \t\r\n")
			if row == 0 { r := []rune(trimmed); if len(r) == 0 { return nil, 0, errors.New("glyph has no end marker") }; marker = r[len(r)-1] }
			r := []rune(trimmed); remove := 0
			for remove < 2 && len(r) > 0 && r[len(r)-1] == marker { r = r[:len(r)-1]; remove++ }
			rows[row] = string(r); if len(r) > width { width = len(r) }
		}
		return rows, width, nil
	}
	for code := 32; code <= 126; code++ { rows, w, err := readGlyph(); if err != nil { return nil, fmt.Errorf("font %s: %w", name, err) }; if code == 32 || strings.Join(rows, "") != "" { f.glyphs[rune(code)] = rows; f.widths[rune(code)] = w } }
	for _, r := range "ÄÖÜäöüß" { if idx < len(lines) { rows, w, err := readGlyph(); if err != nil { return nil, err }; if strings.Join(rows, "") != "" { f.glyphs[r] = rows; f.widths[r] = w } } }
	for idx < len(lines) {
		line := strings.TrimSpace(lines[idx]); idx++
		if line == "" { continue }
		codeText := strings.Fields(line)[0]
		if !strings.HasPrefix(strings.ToLower(codeText), "0x") { continue }
		code, err := strconv.ParseInt(codeText[2:], 16, 32); if err != nil { continue }
		rows, w, err := readGlyph(); if err != nil { return nil, err }
		if strings.Join(rows, "") != "" { f.glyphs[rune(code)] = rows; f.widths[rune(code)] = w }
	}
	return f, nil
}

type builder struct {
	text []rune
	f *font
	direction, justify string
	width, iterator int
	prevWidth, curWidth, maxSmush int
	buffer []string
	queue [][]string
	blanks []savedBuffer
}
type savedBuffer struct { rows []string; index int }

func render(text string, f *font, direction, justify string, width int) (string, error) {
	b := &builder{text: []rune(text), f: f, direction: direction, justify: justify, width: width, buffer: make([]string, f.height)}
	for b.iterator < len(b.text) { if err := b.addChar(); err != nil { return "", err }; b.iterator++ }
	if b.buffer[0] != "" { b.queue = append(b.queue, cloneRows(b.buffer)) }
	var out strings.Builder
	for _, rows := range b.queue {
		for i := range rows { rows[i] = b.justifyRow(rows[i]) }
		for _, row := range rows { out.WriteString(strings.ReplaceAll(row, string(f.hardBlank), " ")); out.WriteByte('\n') }
	}
	return out.String(), nil
}
func cloneRows(rows []string) []string { return append([]string(nil), rows...) }
func (b *builder) addChar() error {
	c := b.text[b.iterator]
	if c == '\n' { b.blanks = append(b.blanks, savedBuffer{cloneRows(b.buffer), b.iterator}); b.handleNewline(); return nil }
	cur, ok := b.f.glyphs[c]; if !ok { return nil }
	b.curWidth = b.f.widths[c]
	b.maxSmush = b.smushAmount(cur)
	total := len([]rune(b.buffer[0])) + b.curWidth - b.maxSmush
	if c == ' ' { b.blanks = append(b.blanks, savedBuffer{cloneRows(b.buffer), b.iterator}) }
	if b.width < b.curWidth { return fmt.Errorf("Width is not enough to print this character") }
	if total >= b.width { b.handleNewline(); return nil }
	for row := 0; row < b.f.height; row++ { b.addCharRow(cur, row) }
	b.prevWidth = b.curWidth
	return nil
}
func (b *builder) addCharRow(cur []string, row int) {
	left, right := b.buffer[row], cur[row]
	if b.direction == "right-to-left" { left, right = right, left }
	lr, rr := []rune(left), []rune(right)
	for i := 0; i < b.maxSmush; i++ {
		idx := len(lr)-b.maxSmush+i
		l := rune(0); if idx >= 0 && idx < len(lr) { l = lr[idx] }
		if i < len(rr) { rr[i] = b.smushChar(l, rr[i]) }
		if idx >= 0 && idx < len(lr) { lr[idx] = rr[i] }
	}
	b.buffer[row] = string(lr) + string(rr[b.maxSmush:])
}
func (b *builder) smushAmount(cur []string) int {
	if b.f.smushMode&(64|128) == 0 { return 0 }
	max := b.curWidth
	for row := 0; row < b.f.height; row++ {
		left, right := b.buffer[row], cur[row]
		if b.direction == "right-to-left" { left, right = right, left }
		lr, rr := []rune(left), []rune(right)
		bd := len(strings.TrimRight(left, " "))-1; if bd < 0 { bd = 0 }
		ch1 := rune(0); if bd < len(lr) { ch1 = lr[bd] } else { bd = 0 }
		charbd := 0; for charbd < len(rr) && rr[charbd] == ' ' { charbd++ }
		ch2 := rune(0); if charbd < len(rr) { ch2 = rr[charbd] }
		amt := charbd+len(lr)-1-bd
		if ch1 == 0 || ch1 == ' ' { amt++ } else if ch2 != 0 && b.smushChar(ch1, ch2) != 0 { amt++ }
		if amt < max { max = amt }
	}
	if max < 0 { return 0 }; return max
}
func (b *builder) smushChar(left, right rune) rune {
	if left == ' ' { return right }; if right == ' ' { return left }
	if b.prevWidth < 2 || b.curWidth < 2 { return 0 }
	if b.f.smushMode&128 == 0 { return 0 }
	if b.f.smushMode&63 == 0 { if left == b.f.hardBlank { return right }; if right == b.f.hardBlank { return left }; if b.direction == "right-to-left" { return left }; return right }
	if b.f.smushMode&32 != 0 && left == b.f.hardBlank && right == b.f.hardBlank { return left }
	if left == b.f.hardBlank || right == b.f.hardBlank { return 0 }
	if b.f.smushMode&1 != 0 && left == right { return left }
	if b.f.smushMode&2 != 0 { a, c := "_", "|/\\[]{}()<>"; if strings.ContainsRune(a,left) && strings.ContainsRune(c,right) { return right }; if strings.ContainsRune(a,right) && strings.ContainsRune(c,left) { return left } }
	if b.f.smushMode&4 != 0 {
		pairs := [][2]string{{"|", "/\\[]{}()<>"}, {"/\\", "[]{}()<>"}, {"[]", "{}()<>"}, {"{}", "()<>"}, {"()", "<>"}}
		for _, p := range pairs { if strings.ContainsRune(p[0],left) && strings.ContainsRune(p[1],right) { return right }; if strings.ContainsRune(p[0],right) && strings.ContainsRune(p[1],left) { return left } }
	}
	if b.f.smushMode&8 != 0 { pair := string([]rune{left,right}); rev := string([]rune{right,left}); if pair == "[]" || pair == "{}" || pair == "()" || rev == "[]" || rev == "{}" || rev == "()" { return '|' } }
	if b.f.smushMode&16 != 0 { if left == '/' && right == '\\' { return '|' }; if right == '/' && left == '\\' { return 'Y' }; if left == '>' && right == '<' { return 'X' } }
	return 0
}
func (b *builder) handleNewline() {
	if len(b.blanks) > 0 { saved := b.blanks[len(b.blanks)-1]; b.blanks = b.blanks[:len(b.blanks)-1]; b.queue = append(b.queue, saved.rows); b.iterator = saved.index } else { b.queue = append(b.queue, cloneRows(b.buffer)); b.iterator-- }
	b.buffer = make([]string,b.f.height); b.prevWidth = 0
	if b.iterator >= 0 && b.iterator < len(b.text) { if cur, ok := b.f.glyphs[b.text[b.iterator]]; ok { b.curWidth=b.f.widths[b.text[b.iterator]]; b.maxSmush=b.smushAmount(cur) } }
}
func (b *builder) justifyRow(row string) string {
	n := b.width-len([]rune(row)); if b.justify == "right" { n-- }; if b.justify == "center" { n /= 2 }; if n < 0 { n=0 }; if b.justify == "right" || b.justify == "center" { return strings.Repeat(" ",n)+row }; return row
}

func splitLines(s string) []string { if s == "" { return nil }; s = strings.TrimSuffix(s,"\n"); if s == "" { return []string{""} }; return strings.Split(s,"\n") }
func reverseArt(s string) string {
	var out []string
	for _, row := range splitLines(s) { r:=[]rune(row); for i,c:=range r { r[i]=reverseMap(c) }; for i,j:=0,len(r)-1;i<j;i,j=i+1,j-1 { r[i],r[j]=r[j],r[i] }; out=append(out,string(r)) }
	return strings.Join(out,"\n")+"\n"
}
func flipArt(s string) string { rows:=splitLines(s); for i,j:=0,len(rows)-1;i<j;i,j=i+1,j-1 { rows[i],rows[j]=rows[j],rows[i] }; for i,row:=range rows { r:=[]rune(row); for j,c:=range r { r[j]=flipMap(c) }; rows[i]=string(r) }; return strings.Join(rows,"\n")+"\n" }
func reverseMap(r rune) rune { switch r { case '(':return ')';case ')':return '(';case '/':return '\\';case '\\':return '/';case '<':return '>';case '>':return '<';case '[':return ']';case ']':return '[';case '{':return '}';case '}':return '{' };return r }
func flipMap(r rune) rune { switch r { case 'A':return 'V';case 'M':return 'W';case 'P':return 'b';case 'R':return 'b';case 'V':return 'A';case 'W':return 'M';case '/':return '\\';case '\\':return '/';case '^':return 'v';case '_':return '-';case 'b':return 'P';case 'v':return '^';case 'w':return 'm';case 'm':return 'w' };return r }
func stripSurrounding(s string) string { var kept []string; seen:=false; for _,row:=range splitLines(s) { if strings.TrimSpace(row)!="" || seen { seen=true; kept=append(kept,row) } }; return strings.TrimRightFunc(strings.Join(kept,"\n")+newlineIfAny(kept),unicode.IsSpace) }
func newlineIfAny(rows []string) string { if len(rows)==0{return ""};return "\n" }
EOF

gofmt -w main.go

# The Go source and embedded font data are ready before Python sources are removed.
find /workspace/repo -type f -name '*.py' -delete

go build ./...
