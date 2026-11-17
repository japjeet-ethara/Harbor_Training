// Go port of pyfiglet 1.0.4 (commit 255827efbc09): the command-line program that draws text in
// large letters. This file is main() of the original: the options, class Figlet and the output.
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

// pyError stands for an exception the original does not catch: it ends with status 1 and prints nothing.
type pyError struct{ msg string }

func raise(format string, a ...any) { panic(pyError{fmt.Sprintf(format, a...)}) }

// usageError stands for parser.error() of optparse: status 2.
type usageError struct{ msg string }

func usage(format string, a ...any) { panic(usageError{fmt.Sprintf(format, a...)}) }

type options struct {
	font, direction, justify      string
	width                         int
	reverse, flip, strip, normal  bool
	listFonts, infoFont, hasColor bool
	load                          string
}

// The options of the original: long name, and whether a value follows.
var longNames = []string{"font", "direction", "justify", "width", "reverse", "normalize-surrounding-newlines",
	"strip-surrounding-newlines", "flip", "list_fonts", "info_font", "load", "color", "version", "help"}
var shortToLong = map[rune]string{'f': "font", 'D': "direction", 'j': "justify", 'w': "width", 'r': "reverse",
	'n': "normalize-surrounding-newlines", 's': "strip-surrounding-newlines", 'F': "flip", 'l': "list_fonts",
	'i': "info_font", 'L': "load", 'c': "color", 'h': "help"}
var takesValue = map[string]bool{"font": true, "direction": true, "justify": true, "width": true, "load": true,
	"color": true}

// parseInt is _parse_int of optparse: 0x.. is hexadecimal, 0b.. binary, a leading 0 octal.
func parseInt(val string) (int, bool) {
	radix, digits := 10, val
	lower := strings.ToLower(val)
	switch {
	case strings.HasPrefix(lower, "0x"):
		radix, digits = 16, val[2:]
	case strings.HasPrefix(lower, "0b"):
		radix, digits = 2, val[2:]
		if digits == "" {
			digits = "0"
		}
	case strings.HasPrefix(val, "0"):
		radix = 8
	}
	n, err := strconv.ParseInt(digits, radix, 64)
	return int(n), err == nil
}

func (o *options) set(name, value string) {
	choice := func(allowed ...string) string {
		for _, a := range allowed {
			if value == a {
				return value
			}
		}
		usage("option --%s: invalid choice: %q", name, value)
		return ""
	}
	switch name {
	case "font":
		o.font = value
	case "direction":
		o.direction = choice("auto", "left-to-right", rightToLeft)
	case "justify":
		o.justify = choice("auto", "left", "center", "right")
	case "width":
		n, ok := parseInt(value)
		if !ok {
			usage("option --width: invalid integer value: %q", value)
		}
		o.width = n
	case "reverse":
		o.reverse = true
	case "flip":
		o.flip = true
	case "strip-surrounding-newlines":
		o.strip = true
	case "normalize-surrounding-newlines":
		o.normal = true
	case "list_fonts":
		o.listFonts = true
	case "info_font":
		o.infoFont = true
	case "load":
		o.load = value
	case "color":
		o.hasColor = value != ":"
	case "version":
		fmt.Println("1.0.4")
		os.Exit(0)
	case "help":
		printHelp()
		os.Exit(0)
	}
}

func matchLong(name string) string { // exact name first, then a unique beginning
	var hits []string
	for _, l := range longNames {
		if l == name {
			return l
		}
		if strings.HasPrefix(l, name) {
			hits = append(hits, l)
		}
	}
	if len(hits) == 1 {
		return hits[0]
	}
	if len(hits) == 0 {
		usage("no such option: --%s", name)
	}
	usage("ambiguous option: --%s", name)
	return ""
}

// parseArgs follows optparse: options and text may be mixed, "--" ends the options, short options
// may be joined (-rF, -w40) and long options may be shortened.
func parseArgs(argv []string) (options, []string) {
	o := options{font: "standard", direction: "auto", justify: "auto", width: 80}
	var text []string
	rargs := argv
	for len(rargs) > 0 {
		arg := rargs[0]
		rargs = rargs[1:]
		switch {
		case arg == "--":
			return o, append(text, rargs...)
		case strings.HasPrefix(arg, "--"):
			name, value, hasValue := arg[2:], "", false
			if k := strings.IndexByte(name, '='); k >= 0 {
				name, value, hasValue = name[:k], name[k+1:], true
			}
			long := matchLong(name)
			if takesValue[long] {
				if !hasValue {
					if len(rargs) == 0 {
						usage("--%s option requires 1 argument", long)
					}
					value, rargs = rargs[0], rargs[1:]
				}
			} else if hasValue {
				usage("--%s option does not take a value", long)
			}
			o.set(long, value)
		case len(arg) > 1 && arg[0] == '-':
			cluster := []rune(arg[1:])
			for i := 0; i < len(cluster); i++ {
				long, ok := shortToLong[cluster[i]]
				if !ok {
					usage("no such option: -%c", cluster[i])
				}
				if !takesValue[long] {
					o.set(long, "")
					continue
				}
				value := string(cluster[i+1:])
				if value == "" {
					if len(rargs) == 0 {
						usage("-%c option requires 1 argument", cluster[i])
					}
					value, rargs = rargs[0], rargs[1:]
				}
				o.set(long, value)
				break
			}
		default:
			text = append(text, arg)
		}
	}
	return o, text
}

func printHelp() {
	fmt.Println("Usage: figlet [options] [text..]")
	fmt.Println()
	fmt.Println("Options:")
	fmt.Println("  -f FONT       font to render with (default: standard)")
	fmt.Println("  -D DIRECTION  auto, left-to-right or right-to-left (default: auto)")
	fmt.Println("  -j SIDE       auto, left, center or right; defaults to the print direction")
	fmt.Println("  -w COLS       terminal width for wrapping and justification (default: 80)")
	fmt.Println("  -r            show the mirror image of the output")
	fmt.Println("  -F            flip the output over")
	fmt.Println("  -s            remove empty leading and trailing lines")
	fmt.Println("  -n            one empty line before and after the output")
}

func run(argv []string) (status int) {
	defer func() {
		switch e := recover().(type) {
		case nil:
		case usageError:
			fmt.Fprintln(os.Stderr, "figlet: error:", e.msg)
			status = 2
		case pyError:
			fmt.Fprintln(os.Stderr, "figlet: error:", e.msg)
			status = 1
		case fontNotFound:
			fmt.Printf("pyfiglet error: requested font '%s' not found.\n", e.font)
			status = 1
		default:
			panic(e)
		}
	}()

	opts, args := parseArgs(argv)
	if opts.listFonts || opts.infoFont || opts.load != "" || opts.hasColor {
		usage("the options -l, -i, -L and -c are not part of this port")
	}
	if len(args) == 0 {
		printHelp()
		return 1
	}
	text := strings.Join(args, " ")

	// class Figlet: the direction and the justification that "auto" stands for
	font := loadFont(opts.font)
	direction := opts.direction
	if direction == "auto" {
		direction = "left-to-right"
		if font.printDirection == 1 {
			direction = rightToLeft
		}
	}
	justify := opts.justify
	if justify == "auto" {
		justify = "left"
		if direction == rightToLeft {
			justify = "right"
		}
	}

	r := render(text, font, direction, opts.width, justify)
	if opts.reverse {
		r = figletReverse(r)
	}
	if opts.flip {
		r = figletFlip(r)
	}
	if opts.strip {
		r = stripSurroundingNewlines(r)
	} else if opts.normal {
		r = normalizeSurroundingNewlines(r)
	}

	out := bufio.NewWriter(os.Stdout)
	out.WriteString(r)
	out.WriteString("\n")
	out.Flush()
	return 0
}

func main() {
	os.Exit(run(os.Args[1:]))
}
