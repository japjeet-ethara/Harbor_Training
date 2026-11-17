package main

// Port of class FigletFont: finding a font file and parsing it.

import (
	"embed"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// The font files live in the folder "fonts" of the repository and are built into the program,
// so it finds them from any working directory.
//
//go:embed fonts/*.flf
var fontFiles embed.FS

// FONT_DIRECTORIES of the original (the non-Windows branch).
var fontDirectories = []string{"/usr/local/share/pyfiglet/", "/usr/local/share/figlet", "/usr/share/figlet"}

type figletFont struct {
	name           string
	chars          map[rune][][]rune
	width          map[rune]int
	height         int
	hardBlank      string
	printDirection int // -1 when the header does not give one
	smushMode      int
}

type fontNotFound struct{ font string }

// preloadFont: the packaged font wins, then the working directory, then the system folders;
// ".tlf" is tried before ".flf".
func preloadFont(font string) string {
	var data []byte
	found := false
	for _, ext := range []string{"tlf", "flf"} {
		fn := font + "." + ext
		if d, err := fontFiles.ReadFile("fonts/" + fn); err == nil {
			data, found = d, true
			break
		}
		for _, location := range append([]string{"./"}, fontDirectories...) {
			full := filepath.Join(location, fn)
			if st, err := os.Stat(full); err == nil && st.Mode().IsRegular() {
				if d, err := os.ReadFile(full); err == nil {
					data, found = d, true
				}
				break
			}
		}
	}
	if !found || len(data) == 0 {
		panic(fontNotFound{font})
	}
	return decodeUTF8Replace(data)
}

// lineReader gives data.pop(0); running out of lines is the IndexError of the original.
type lineReader struct {
	lines []string
	pos   int
}

func (r *lineReader) more() bool { return r.pos < len(r.lines) }

func (r *lineReader) pop() string {
	if r.pos >= len(r.lines) {
		raise("pop from empty list")
	}
	r.pos++
	return r.lines[r.pos-1]
}

func loadFont(name string) *figletFont {
	f := &figletFont{name: name, chars: map[rune][][]rune{}, width: map[rune]int{}, printDirection: -1}

	// data = re.sub(r"[\u0085  ]", " ", self.data); data = data.splitlines()
	raw := preloadFont(name)
	raw = strings.NewReplacer("\u0085", " ", " ", " ", " ", " ").Replace(raw)
	data := &lineReader{lines: splitLines(raw)}

	// header = data.pop(0); reMagicNumber = '^[tf]lf2.'
	header := []rune(data.pop())
	if len(header) < 5 || (header[0] != 't' && header[0] != 'f') || header[1] != 'l' || header[2] != 'f' ||
		header[3] != '2' || header[4] == '\n' {
		raise("%s is not a valid figlet font", name)
	}
	parts := fields(string(header[5:]))
	if len(parts) < 6 {
		raise("malformed header for %s", name)
	}
	f.hardBlank = parts[0]
	nums := make([]int, 0, 7)
	for _, p := range parts[1:] {
		if len(nums) == 7 {
			break
		}
		n, err := strconv.Atoi(p)
		if err != nil {
			raise("invalid literal for int(): %q", p)
		}
		nums = append(nums, n)
	}
	height, oldLayout, commentLines := nums[0], nums[3], nums[4]
	fullLayout, hasFull := 0, false
	if len(parts) > 6 {
		f.printDirection = nums[5]
	}
	if len(parts) > 7 {
		fullLayout, hasFull = nums[6], true
	}
	// if the new layout style isn't available, convert old layout style
	if !hasFull {
		switch {
		case oldLayout == 0:
			fullLayout = 64
		case oldLayout < 0:
			fullLayout = 0
		default:
			fullLayout = (oldLayout & 31) | 128
		}
	}
	f.height = height
	f.smushMode = fullLayout

	for i := 0; i < commentLines; i++ {
		data.pop()
	}

	// __char: one character is `height` lines; the end mark is the last character of its first line
	// that is followed only by whitespace, and one or two of them are cut from the end of every line.
	readChar := func() (int, [][]rune) {
		var end rune
		haveEnd := false
		width := 0
		rows := make([][]rune, 0, height)
		for n := 0; n < height; n++ {
			line := []rune(data.pop())
			if !haveEnd {
				found := false
				for i := range line { // reEndMarker = r'(.)\s*$', leftmost match
					if allSpace(line[i+1:]) {
						end, found = line[i], true
						break
					}
				}
				if !found {
					raise("'NoneType' object has no attribute 'group'")
				}
				haveEnd = true
			}
			for i := range line { // end.sub('', line) with end + r'{1,2}\s*$', leftmost match
				if line[i] != end {
					continue
				}
				if allSpace(line[i+1:]) || (i+1 < len(line) && line[i+1] == end && allSpace(line[i+2:])) {
					line = line[:i]
					break
				}
			}
			if len(line) > width {
				width = len(line)
			}
			rows = append(rows, line)
		}
		return width, rows
	}
	empty := func(rows [][]rune) bool {
		for _, r := range rows {
			if len(r) > 0 {
				return false
			}
		}
		return true
	}

	// Load ASCII standard character set (32 - 127). The space is kept even when it is empty.
	for i := rune(32); i < 127; i++ {
		width, letter := readChar()
		if i == 32 || !empty(letter) {
			f.chars[i], f.width[i] = letter, width
		}
	}
	// Load German Umlaute - they follow directly after standard character 127
	if data.more() {
		for _, i := range "ÄÖÜäöüß" {
			width, letter := readChar()
			if !empty(letter) {
				f.chars[i], f.width[i] = letter, width
			}
		}
	}
	// Load the extended character set: only code lines that start with 0x are read
	for data.more() {
		line := strip(data.pop())
		code := line
		if k := strings.IndexByte(line, ' '); k >= 0 {
			code = line[:k]
		}
		if code == "" {
			continue
		}
		if len(code) >= 2 && code[0] == '0' && (code[1] == 'x' || code[1] == 'X') {
			n, err := strconv.ParseInt(code[2:], 16, 64)
			if err != nil || strings.ContainsAny(code[2:], "+-") {
				raise("invalid literal for int() with base 16: %q", code)
			}
			width, letter := readChar()
			if !empty(letter) {
				f.chars[rune(n)], f.width[rune(n)] = letter, width
			}
		}
	}
	return f
}
