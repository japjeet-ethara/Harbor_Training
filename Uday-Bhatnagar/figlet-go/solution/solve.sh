#!/bin/bash
set -euo pipefail
cd /workspace/repo
mkdir -p fonts
cp pyfiglet/fonts/*.flf fonts/
cat > go.mod <<'FIGLET_ORACLE_EOF'
module figletport

go 1.23

FIGLET_ORACLE_EOF
cat > main.go <<'FIGLET_ORACLE_EOF'
package main

import (
	"embed"
	"fmt"
	"os"
	"strconv"
	"strings"
	"unicode"
)

//go:embed fonts/*.flf
var fonts embed.FS

type Font struct {
	h, mode, dir int
	hard         string
	chars        map[rune][]string
	widths       map[rune]int
}

func load(name string) Font {
	b, e := fonts.ReadFile("fonts/" + strings.TrimSuffix(name, ".flf") + ".flf")
	if e != nil {
		panic(e)
	}
	s := strings.NewReplacer("\r\n", "\n", "\r", "\n", "\u0085", " ", "\u2028", " ", "\u2029", " ").Replace(string(b))
	lines := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
	head := strings.Fields(lines[0][5:])
	n := func(i int) int { v, _ := strconv.Atoi(head[i]); return v }
	f := Font{h: n(1), hard: head[0], chars: map[rune][]string{}, widths: map[rune]int{}}
	old := n(4)
	if old == 0 {
		f.mode = 64
	} else if old > 0 {
		f.mode = (old & 31) | 128
	}
	if len(head) > 6 {
		f.dir = n(6)
	}
	if len(head) > 7 {
		f.mode = n(7)
	}
	pos := 1 + n(5)
	read := func(c rune) {
		rows := []string{}
		w := 0
		end := rune(0)
		for j := 0; j < f.h; j++ {
			r := []rune(lines[pos])
			pos++
			if j == 0 {
				t := []rune(strings.TrimRightFunc(string(r), unicode.IsSpace))
				end = t[len(t)-1]
			}
			t := []rune(strings.TrimRightFunc(string(r), unicode.IsSpace))
			k := len(t)
			count := 0
			for k > 0 && t[k-1] == end && count < 2 {
				k--
				count++
			}
			if count > 0 {
				r = t[:k]
			}
			row := string(r)
			rows = append(rows, row)
			if len(r) > w {
				w = len(r)
			}
		}
		if c == ' ' || strings.Join(rows, "") != "" {
			f.chars[c] = rows
			f.widths[c] = w
		}
	}
	for c := rune(32); c < 127; c++ {
		read(c)
	}
	if pos < len(lines) {
		for _, c := range "ÄÖÜäöüß" {
			read(c)
		}
	}
	for pos < len(lines) {
		line := strings.TrimSpace(lines[pos])
		pos++
		tag := strings.SplitN(line, " ", 2)[0]
		if strings.HasPrefix(strings.ToLower(tag), "0x") {
			v, _ := strconv.ParseInt(tag[2:], 16, 32)
			read(rune(v))
		}
	}
	return f
}

type Builder struct {
	f                Font
	rtl              bool
	width, prev, cur int
}

func (b *Builder) smush(l, r string) (string, bool) {
	if l == " " {
		return r, true
	}
	if r == " " {
		return l, true
	}
	if b.prev < 2 || b.cur < 2 || b.f.mode&128 == 0 {
		return "", false
	}
	m := b.f.mode
	if m&63 == 0 {
		if l == b.f.hard {
			return r, true
		}
		if r == b.f.hard || b.rtl {
			return l, true
		}
		return r, true
	}
	if m&32 != 0 && l == b.f.hard && r == b.f.hard {
		return l, true
	}
	if l == b.f.hard || r == b.f.hard {
		return "", false
	}
	if m&1 != 0 && l == r {
		return l, true
	}
	pairs := [][2]string{}
	if m&2 != 0 {
		pairs = append(pairs, [2]string{"_", `|/\[]{}()<>`})
	}
	if m&4 != 0 {
		pairs = append(pairs, [2]string{"|", `/\[]{}()<>`}, [2]string{`\/`, "[]{}()<>"}, [2]string{"[]", "{}()<>"}, [2]string{"{}", "()<>"}, [2]string{"()", "<>"})
	}
	for _, p := range pairs {
		if strings.Contains(p[0], l) && strings.Contains(p[1], r) {
			return r, true
		}
		if strings.Contains(p[0], r) && strings.Contains(p[1], l) {
			return l, true
		}
	}
	if m&8 != 0 {
		for _, p := range []string{l + r, r + l} {
			if p == "[]" || p == "{}" || p == "()" {
				return "|", true
			}
		}
	}
	if m&16 != 0 {
		if l == "/" && r == `\` {
			return "|", true
		}
		if l == `\` && r == "/" {
			return "Y", true
		}
		if l == ">" && r == "<" {
			return "X", true
		}
	}
	return "", false
}
func (b *Builder) amount(buf, ch []string) int {
	if b.f.mode&192 == 0 {
		return 0
	}
	mx := b.cur
	for i := 0; i < b.f.h; i++ {
		l, r := buf[i], ch[i]
		if b.rtl {
			l, r = r, l
		}
		lr, rr := []rune(l), []rune(r)
		bd := len([]rune(strings.TrimRight(l, " "))) - 1
		if bd < 0 {
			bd = 0
		}
		c1 := ""
		if bd < len(lr) {
			c1 = string(lr[bd])
		} else {
			bd = 0
		}
		cb := len(rr) - len([]rune(strings.TrimLeft(r, " ")))
		c2 := ""
		if cb < len(rr) {
			c2 = string(rr[cb])
		}
		a := cb + len(lr) - 1 - bd
		_, ok := b.smush(c1, c2)
		if c1 == "" || c1 == " " || (c2 != "" && ok) {
			a++
		}
		if a < mx {
			mx = a
		}
	}
	return mx
}
func (b *Builder) render(text, justify string) string {
	type blank struct {
		buf []string
		i   int
	}
	var blanks []blank
	var product [][]string
	buf := make([]string, b.f.h)
	chars := []rune(text)
	reset := func() { buf = make([]string, b.f.h); blanks = nil; b.prev = 0 }
	cut := func(i *int) {
		if len(blanks) > 0 {
			v := blanks[len(blanks)-1]
			product = append(product, v.buf)
			*i = v.i
		} else {
			product = append(product, buf)
			*i--
		}
		reset()
	}
	for i := 0; i < len(chars); i++ {
		c := chars[i]
		if c == '\n' {
			blanks = append(blanks, blank{append([]string{}, buf...), i})
			cut(&i)
			continue
		}
		ch, ok := b.f.chars[c]
		if !ok {
			continue
		}
		b.cur = b.f.widths[c]
		if b.width < b.cur {
			panic("width too small")
		}
		amt := b.amount(buf, ch)
		total := len([]rune(buf[0])) + b.cur - amt
		if c == ' ' {
			blanks = append(blanks, blank{append([]string{}, buf...), i})
		}
		if total >= b.width {
			cut(&i)
		} else {
			for row := 0; row < b.f.h; row++ {
				l, r := []rune(buf[row]), []rune(ch[row])
				if b.rtl {
					l, r = r, l
				}
				for j := 0; j < amt; j++ {
					idx := len(l) - amt + j
					left := ""
					if idx >= 0 && idx < len(l) {
						left = string(l[idx])
					}
					v, _ := b.smush(left, string(r[j]))
					if idx >= 0 && idx < len(l) {
						l[idx] = []rune(v)[0]
					}
				}
				buf[row] = string(l) + string(r[amt:])
			}
		}
		b.prev = b.cur
	}
	if buf[0] != "" {
		product = append(product, buf)
	}
	var out strings.Builder
	for _, rows := range product {
		for _, r := range rows {
			pad := 0
			if justify == "right" {
				pad = b.width - len([]rune(r)) - 1
			}
			if justify == "center" {
				pad = (b.width - len([]rune(r))) / 2
			}
			if pad > 0 {
				out.WriteString(strings.Repeat(" ", pad))
			}
			out.WriteString(strings.ReplaceAll(r, b.f.hard, " "))
			out.WriteByte('\n')
		}
	}
	return out.String()
}
func transform(s, table string, rev, flip bool) string {
	rows := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
	if s == "" {
		rows = nil
	}
	if flip {
		for i, j := 0, len(rows)-1; i < j; i, j = i+1, j-1 {
			rows[i], rows[j] = rows[j], rows[i]
		}
	}
	mapping := []rune(table)
	for i, row := range rows {
		r := []rune(row)
		for j, c := range r {
			if c >= 32 && c < 128 {
				r[j] = mapping[c-32]
			}
		}
		if rev {
			for a, z := 0, len(r)-1; a < z; a, z = a+1, z-1 {
				r[a], r[z] = r[z], r[a]
			}
		}
		rows[i] = string(r)
	}
	return strings.Join(rows, "\n") + "\n"
}
func main() {
	defer func() {
		if e := recover(); e != nil {
			fmt.Fprintln(os.Stderr, e)
			os.Exit(1)
		}
	}()
	font, dir, just := "standard", "auto", "auto"
	width := 80
	rev, flip, strip, norm := false, false, false, false
	var texts []string
	args := os.Args[1:]
	end := false
	for i := 0; i < len(args); i++ {
		a := args[i]
		if a == "--" && !end {
			end = true
			continue
		}
		if !end && strings.HasPrefix(a, "-") && a != "-" {
			switch a {
			case "-f", "--font", "-D", "--direction", "-j", "--justify", "-w", "--width":
				i++
				v := args[i]
				switch a {
				case "-f", "--font":
					font = v
				case "-D", "--direction":
					dir = v
				case "-j", "--justify":
					just = v
				default:
					width, _ = strconv.Atoi(v)
				}
			case "-r", "--reverse":
				rev = true
			case "-F", "--flip":
				flip = true
			case "-s", "--strip-surrounding-newlines":
				strip = true
			case "-n", "--normalize-surrounding-newlines":
				norm = true
			default:
				panic("unknown option " + a)
			}
		} else {
			texts = append(texts, a)
		}
	}
	f := load(font)
	if dir == "auto" {
		dir = "left-to-right"
		if f.dir == 1 {
			dir = "right-to-left"
		}
	}
	if just == "auto" {
		just = "left"
		if dir == "right-to-left" {
			just = "right"
		}
	}
	b := Builder{f: f, rtl: dir == "right-to-left", width: width}
	s := b.render(strings.Join(texts, " "), just)
	if rev {
		s = transform(s, reverseTable, true, false)
	}
	if flip {
		s = transform(s, flipTable, false, true)
	}
	if strip || norm {
		rows := strings.Split(strings.TrimSuffix(s, "\n"), "\n")
		for len(rows) > 0 && strings.TrimSpace(rows[0]) == "" {
			rows = rows[1:]
		}
		s = strings.TrimRightFunc(strings.Join(rows, "\n")+"\n", unicode.IsSpace)
		if norm && !strip {
			s = "\n" + s + "\n"
		}
	}
	fmt.Print(s + "\n")
}

FIGLET_ORACLE_EOF
cat > tables.go <<'FIGLET_ORACLE_EOF'
package main
const reverseTable = " !\"#$%&')(*+,-.\\0123456789:;>=<?@ABCDEFGHIJKLMNOPQRSTUVWXYZ]/[^_`abcdefghijklmnopqrstuvwxyz}|{~\u007f"
const flipTable = " !\"#$%&'()*+,-.\\0123456789:;<=>?@VBCDEFGHIJKLWNObQbSTUAMXYZ[/]v-`aPcdefghijklwnopqrstu^mxyz{|}~\u007f"

FIGLET_ORACLE_EOF
find /workspace/repo -type f -name '*.py' -delete
go build ./...
