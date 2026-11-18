package main

import (
	"bufio"
	"embed"
	"fmt"
	"io"
	"strconv"
	"strings"
)

//go:embed fonts/*.flf
var fontFiles embed.FS

type Font struct {
	Name           string
	HardBlank      rune
	Height         int
	Baseline       int
	MaxLength      int
	PrintDirection int
	SmushMode      int
	Glyphs         map[rune][]string
	Widths         map[rune]int
}

func loadFont(name string) (*Font, error) {
	if strings.ContainsAny(name, `/\`) || strings.Contains(name, "..") {
		return nil, fmt.Errorf("invalid font name")
	}
	if !strings.HasSuffix(name, ".flf") {
		name += ".flf"
	}

	data, err := fontFiles.ReadFile("fonts/" + name)
	if err != nil {
		return nil, fmt.Errorf("font %q not found", name)
	}

	return parseFont(name, string(data))
}

func parseFont(name, data string) (*Font, error) {
	data = strings.NewReplacer("\u0085", " ", "\u2028", " ", "\u2029", " ").Replace(data)
	scanner := bufio.NewScanner(strings.NewReader(data))
	scanner.Buffer(make([]byte, 4096), 4*1024*1024)

	var lines []string
	for scanner.Scan() {
		lines = append(lines, strings.TrimSuffix(scanner.Text(), "\r"))
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	if len(lines) == 0 {
		return nil, fmt.Errorf("empty font")
	}

	header := strings.Fields(lines[0])
	if len(header) < 6 || (!strings.HasPrefix(lines[0], "flf2") && !strings.HasPrefix(lines[0], "tlf2")) {
		return nil, fmt.Errorf("invalid font header")
	}

	if len(header[0]) <= 5 ||
		(!strings.HasPrefix(header[0], "flf2a") &&
			!strings.HasPrefix(header[0], "tlf2a")) {
		return nil, fmt.Errorf("invalid font magic or hardblank")
	}
	hard := []rune(header[0][5:])
	if len(hard) != 1 {
		return nil, fmt.Errorf("invalid hardblank")
	}
	nums := make([]int, 5)
	for i := range nums {
		n, err := strconv.Atoi(header[i+1])
		if err != nil {
			return nil, fmt.Errorf("invalid font header: %w", err)
		}
		nums[i] = n
	}
	height, baseline, maxLength, oldLayout, comments := nums[0], nums[1], nums[2], nums[3], nums[4]
	if height < 1 || height > 256 || comments < 0 || comments > len(lines)-1 {
		return nil, fmt.Errorf("invalid font dimensions")
	}

	direction := 0
	if len(header) > 6 {
		direction, _ = strconv.Atoi(header[6])
	}
	layout := 0
	if len(header) > 7 {
		layout, _ = strconv.Atoi(header[7])
	} else if oldLayout == 0 {
		layout = 64
	} else if oldLayout > 0 {
		layout = (oldLayout & 31) | 128
	}

	f := &Font{
		Name: name, HardBlank: hard[0], Height: height, Baseline: baseline,
		MaxLength: maxLength, PrintDirection: direction, SmushMode: layout,
		Glyphs: make(map[rune][]string), Widths: make(map[rune]int),
	}

	pos := 1 + comments
	readGlyph := func() ([]string, int, error) {
		if pos+height > len(lines) {
			return nil, 0, io.ErrUnexpectedEOF
		}
		rows := make([]string, height)
		width := 0
		var end rune
		for i := 0; i < height; i++ {
			line := lines[pos]
			pos++
			rs := []rune(line)
			if i == 0 {
				if len(rs) == 0 {
					return nil, 0, fmt.Errorf("missing glyph endmark")
				}
				end = rs[len(rs)-1]
			}
			for len(rs) > 0 && rs[len(rs)-1] == end {
				rs = rs[:len(rs)-1]
			}
			rows[i] = string(rs)
			if len(rs) > width {
				width = len(rs)
			}
		}
		return rows, width, nil
	}

	for code := rune(32); code <= 126; code++ {
		rows, width, err := readGlyph()
		if err != nil {
			return nil, fmt.Errorf("glyph %d: %w", code, err)
		}
		if code == 32 || strings.Join(rows, "") != "" {
			f.Glyphs[code] = rows
			f.Widths[code] = width
		}
	}

	german := []rune("ÄÖÜäöüß")
	if pos < len(lines) {
		for _, code := range german {
			if pos >= len(lines) {
				break
			}
			rows, width, err := readGlyph()
			if err != nil {
				return nil, err
			}
			if strings.Join(rows, "") != "" {
				f.Glyphs[code] = rows
				f.Widths[code] = width
			}
		}
	}

	for pos < len(lines) {
		line := strings.TrimSpace(lines[pos])
		pos++
		if line == "" {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) == 0 || !strings.HasPrefix(strings.ToLower(fields[0]), "0x") {
			continue
		}
		code, err := strconv.ParseInt(fields[0], 0, 32)
		if err != nil {
			continue
		}
		rows, width, err := readGlyph()
		if err != nil {
			return nil, err
		}
		if strings.Join(rows, "") != "" {
			f.Glyphs[rune(code)] = rows
			f.Widths[rune(code)] = width
		}
	}

	return f, nil
}
