package main

import (
	"flag"
	"fmt"
	"os"
	"strings"
)

func main() {
	fontName := flag.String("f", "standard", "font")
	width := flag.Int("w", 80, "terminal width")
	justify := flag.String("j", "auto", "justification")
	direction := flag.String("D", "auto", "text direction")
	reverse := flag.Bool("r", false, "reverse output")
	flip := flag.Bool("F", false, "flip output")
	strip := flag.Bool("s", false, "strip surrounding newlines")
	normalize := flag.Bool("n", false, "normalize surrounding newlines")
	flag.Parse()

	if flag.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "usage: figlet [options] text")
		os.Exit(1)
	}
	if *width < 1 {
		fmt.Fprintln(os.Stderr, "width must be positive")
		os.Exit(1)
	}
	if !validChoice(*justify, "auto", "left", "center", "right") ||
		!validChoice(*direction, "auto", "left-to-right", "right-to-left") {
		fmt.Fprintln(os.Stderr, "invalid direction or justification")
		os.Exit(1)
	}

	font, err := loadFont(*fontName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyfiglet error: requested font %q not found.\n", *fontName)
		os.Exit(1)
	}

	renderer := newRenderer(font, *width, *direction, *justify)
	result := renderer.render(strings.Join(flag.Args(), " "))

	if *reverse {
		result = reverseOutput(result)
	}
	if *flip {
		result = flipOutput(result)
	}
	if *strip {
		result = stripOutput(result)
	} else if *normalize {
		result = "\n" + stripOutput(result) + "\n"
	}

	fmt.Print(result)
	fmt.Print("\n")
}

func validChoice(value string, choices ...string) bool {
	for _, choice := range choices {
		if value == choice {
			return true
		}
	}
	return false
}

func reverseOutput(input string) string {
	rows := strings.Split(strings.TrimSuffix(input, "\n"), "\n")
	for i, row := range rows {
		rows[i] = translateRow(row, reverseMap, true)
	}
	return strings.Join(rows, "\n") + "\n"
}

func flipOutput(input string) string {
	rows := strings.Split(strings.TrimSuffix(input, "\n"), "\n")
	for i, j := 0, len(rows)-1; i < j; i, j = i+1, j-1 {
		rows[i], rows[j] = rows[j], rows[i]
	}
	for i, row := range rows {
		rows[i] = translateRow(row, flipMap, false)
	}
	return strings.Join(rows, "\n") + "\n"
}

func translateRow(row, mapping string, reverse bool) string {
	table := []rune(mapping)
	runes := []rune(row)

	for i, ch := range runes {
		if ch >= 0 && int(ch) < len(table) {
			runes[i] = table[ch]
		}
	}

	if reverse {
		for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
			runes[i], runes[j] = runes[j], runes[i]
		}
	}
	return string(runes)
}

const reverseMap = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f" +
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
	"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"

const flipMap = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f" +
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
	"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"

func stripOutput(input string) string {
	rows := strings.Split(strings.TrimSuffix(input, "\n"), "\n")
	start := 0
	for start < len(rows) && strings.TrimSpace(rows[start]) == "" {
		start++
	}
	if start == len(rows) {
		return ""
	}
	return strings.TrimRight(strings.Join(rows[start:], "\n"), " \t\r\n")
}
