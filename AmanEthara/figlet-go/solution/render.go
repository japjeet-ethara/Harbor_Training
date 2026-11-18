package main

import "strings"

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

type Renderer struct {
	font      *Font
	width     int
	direction int
	justify   string
}

type blankMarker struct {
	rows  []string
	index int
}

func newRenderer(f *Font, width int, direction, justify string) *Renderer {
	dir := f.PrintDirection
	if direction == "left-to-right" {
		dir = 0
	} else if direction == "right-to-left" {
		dir = 1
	}

	if justify == "auto" {
		if dir == 1 {
			justify = "right"
		} else {
			justify = "left"
		}
	}

	return &Renderer{
		font:      f,
		width:     width,
		direction: dir,
		justify:   justify,
	}
}

func cloneRows(rows []string) []string {
	return append([]string(nil), rows...)
}

func (r *Renderer) render(text string) string {
	buffer := make([]string, r.font.Height)
	var product [][]string
	var markers []blankMarker

	runes := []rune(text)
	prevWidth := 0
	curWidth := 0
	maxSmush := 0

	reset := func() {
		buffer = make([]string, r.font.Height)
		markers = nil
		prevWidth = 0
	}

	appendBuffer := func(rows []string) {
		product = append(product, cloneRows(rows))
	}

	cutAtLastChar := func() {
		appendBuffer(buffer)
		reset()
	}

	cutAtLastBlank := func(marker blankMarker) {
		appendBuffer(marker.rows)
		reset()
	}

	for i := 0; i < len(runes); {
		ch := runes[i]

		if ch == '\n' {
			markers = append(markers, blankMarker{
				rows:  cloneRows(buffer),
				index: i,
			})

			m := markers[len(markers)-1]
			cutAtLastBlank(m)
			i = m.index + 1
			continue
		}

		glyph, ok := r.font.Glyphs[ch]
		if !ok {
			i++
			continue
		}

		curWidth = r.font.Widths[ch]

		if r.width > 0 && curWidth > r.width {
			// pyfiglet raises CharNotPrinted for an oversized glyph.
			i++
			continue
		}

		maxSmush = r.smushAmount(buffer, glyph, prevWidth, curWidth)
		currentTotalWidth := len([]rune(buffer[0])) + curWidth - maxSmush

		if ch == ' ' {
			markers = append(markers, blankMarker{
				rows:  cloneRows(buffer),
				index: i,
			})
		}

		if r.width > 0 && currentTotalWidth >= r.width {
			if len(markers) > 0 {
				m := markers[len(markers)-1]
				cutAtLastBlank(m)
				i = m.index + 1
			} else {
				cutAtLastChar()
			}
			continue
		}

		for row := 0; row < r.font.Height; row++ {
			buffer[row] = r.addCharRow(buffer[row], glyph[row], maxSmush, prevWidth, curWidth)
		}

		prevWidth = curWidth
		i++
	}

	if buffer[0] != "" {
		appendBuffer(buffer)
	}

	var result strings.Builder

	for _, rows := range product {
		for _, row := range rows {
			runes := []rune(row)

			switch r.justify {
			case "right":
				n := r.width - len(runes) - 1
				if n > 0 {
					result.WriteString(strings.Repeat(" ", n))
				}
			case "center":
				n := (r.width - len(runes)) / 2
				if n > 0 {
					result.WriteString(strings.Repeat(" ", n))
				}
			}

			result.WriteString(strings.ReplaceAll(
				row,
				string(r.font.HardBlank),
				" ",
			))
			result.WriteByte('\n')
		}
	}

	return result.String()
}

func (r *Renderer) addCharRow(left, right string, overlap, prevWidth, curWidth int) string {
	addLeft := []rune(left)
	addRight := []rune(right)

	if r.direction == 1 {
		addLeft, addRight = addRight, addLeft
	}

	for i := 0; i < overlap; i++ {
		idx := len(addLeft) - overlap + i

		var leftChar rune
		if idx >= 0 && idx < len(addLeft) {
			leftChar = addLeft[idx]
		}

		var rightChar rune
		if i >= 0 && i < len(addRight) {
			rightChar = addRight[i]
		}

		smushed := r.smushChars(leftChar, rightChar, prevWidth, curWidth)

		if idx >= 0 && idx < len(addLeft) {
			addLeft[idx] = smushed
		}
	}

	return string(addLeft) + string(addRight[minInt(overlap, len(addRight)):])
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func (r *Renderer) smushAmount(buffer, glyph []string, prevWidth, curWidth int) int {
	if r.font.SmushMode&(smSmush|smKern) == 0 {
		return 0
	}

	maxSmush := curWidth

	for row := 0; row < r.font.Height; row++ {
		lineLeft := []rune(buffer[row])
		lineRight := []rune(glyph[row])

		if r.direction == 1 {
			lineLeft, lineRight = lineRight, lineLeft
		}

		lineBD := len(lineLeft) - 1
		for lineBD >= 0 && lineLeft[lineBD] == ' ' {
			lineBD--
		}

		var ch1 rune
		if lineBD >= 0 {
			ch1 = lineLeft[lineBD]
		} else {
			lineBD = 0
		}

		charBD := 0
		for charBD < len(lineRight) && lineRight[charBD] == ' ' {
			charBD++
		}

		var ch2 rune
		if charBD < len(lineRight) {
			ch2 = lineRight[charBD]
		}

		amount := charBD + len(lineLeft) - 1 - lineBD

		if ch1 == 0 || ch1 == ' ' {
			amount++
		} else if ch2 != 0 && r.smushChars(ch1, ch2, prevWidth, curWidth) != 0 {
			amount++
		}

		if amount < maxSmush {
			maxSmush = amount
		}
	}

	return maxSmush
}

func (r *Renderer) smushChars(left, right rune, prevWidth, curWidth int) rune {
	if left == ' ' {
		return right
	}
	if right == ' ' {
		return left
	}

	if prevWidth < 2 || curWidth < 2 {
		return 0
	}

	mode := r.font.SmushMode

	if mode&smSmush == 0 {
		return 0
	}

	if mode&63 == 0 {
		if left == r.font.HardBlank {
			return right
		}
		if right == r.font.HardBlank {
			return left
		}
		if r.direction == 1 {
			return left
		}
		return right
	}

	if mode&smHardblank != 0 &&
		left == r.font.HardBlank &&
		right == r.font.HardBlank {
		return left
	}

	if left == r.font.HardBlank || right == r.font.HardBlank {
		return 0
	}

	if mode&smEqual != 0 && left == right {
		return left
	}

	if mode&smLowline != 0 {
		pairs := "|/\\[]{}()<>"
		if left == '_' && strings.ContainsRune(pairs, right) {
			return right
		}
		if right == '_' && strings.ContainsRune(pairs, left) {
			return left
		}
	}

	if mode&smHierarchy != 0 {
		groups := []struct {
			strong string
			weak   string
		}{
			{"|", "/\\[]{}()<>"},
			{"/\\", "[]{}()<>"},
			{"[]", "{}()<>"},
			{"{}", "()<>"},
			{"()", "<>"},
		}

		for _, group := range groups {
			if strings.ContainsRune(group.strong, left) &&
				strings.ContainsRune(group.weak, right) {
				return right
			}
			if strings.ContainsRune(group.strong, right) &&
				strings.ContainsRune(group.weak, left) {
				return left
			}
		}
	}

	if mode&smPair != 0 {
		pair := string([]rune{left, right})
		reverse := string([]rune{right, left})

		if pair == "[]" || pair == "{}" || pair == "()" ||
			reverse == "[]" || reverse == "{}" || reverse == "()" {
			return '|'
		}
	}

	if mode&smBigX != 0 {
		switch {
		case left == '/' && right == '\\':
			return '|'
		case left == '\\' && right == '/':
			return 'Y'
		case left == '>' && right == '<':
			return 'X'
		}
	}

	return 0
}
