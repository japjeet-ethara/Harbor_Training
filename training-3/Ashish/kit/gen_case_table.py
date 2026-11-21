"""Generate the Unicode tables that task/solution/solve.sh embeds.

Usage:
    python gen_case_table.py <out_dir>            # runs Go in docker itself
    python gen_case_table.py <out_dir> --probe-output go_props.txt

Why this exists. The Go port has to reproduce CPython's titlecase() byte for
byte, but Go and CPython disagree about Unicode in three ways that matter:

  1. str.upper()/lower()/capitalize() are FULL case mappings and may change
     length ('ss' for the sharp s, 'FI' for the fi ligature). Go's
     unicode.ToUpper/ToLower/ToTitle are simple one-rune mappings and cannot
     express those at all.
  2. Go 1.23 ships Unicode 15.0, CPython 3.14 ships Unicode 16.0, so thousands
     of code points are letters to Python and unassigned to Go. That breaks
     \\w, \\b and CAPFIRST, not just casing.
  3. Python's \\s (str.isspace()) includes U+001C..U+001F; Go's
     unicode.IsSpace does not.

The point of generating rather than hand-listing is that the port must be
correct for inputs the exam does not contain. Listing only the characters the
exam happens to use would be tuning the port to the exam.

Outputs <out_dir>/case_table.txt and <out_dir>/ranges.txt, ready to paste into
solve.sh in place of the //__CASE_TABLE__ and //__RANGE_TABLES__ markers.
"""
import os
import subprocess
import sys
import tempfile
import unicodedata

GO_IMAGE = "golang:1.23"

GO_PROBE = r'''package main

import (
	"bufio"
	"fmt"
	"os"
	"unicode"
	"unicode/utf8"
)

func main() {
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for cp := 0; cp <= 0x10FFFF; cp++ {
		if cp >= 0xD800 && cp <= 0xDFFF {
			continue
		}
		r := rune(cp)
		if !utf8.ValidRune(r) {
			continue
		}
		word := 0
		if r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r) {
			word = 1
		}
		space := 0
		if unicode.IsSpace(r) {
			space = 1
		}
		cased := 0
		if unicode.IsUpper(r) || unicode.IsLower(r) || unicode.IsTitle(r) {
			cased = 1
		}
		// code point, simple upper, simple lower, simple title, \w, \s, Cased
		fmt.Fprintf(w, "%x %x %x %x %d %d %d\n", cp,
			unicode.ToUpper(r), unicode.ToLower(r), unicode.ToTitle(r),
			word, space, cased)
	}
}
'''


def run_go_probe():
    """Build and run the Go probe in docker, returning its stdout."""
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "main.go"), "w", encoding="utf-8") as f:
            f.write(GO_PROBE)
        with open(os.path.join(tmp, "go.mod"), "w", encoding="utf-8") as f:
            f.write("module caseprobe\n\ngo 1.23\n")
        return subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "-v", f"{tmp}:/w", "-w", "/w",
             GO_IMAGE, "sh", "-c", "go build -buildvcs=false -o /tmp/p . && /tmp/p"],
            capture_output=True, text=True, encoding="utf-8", check=True).stdout


def go_literal(s):
    """A Go string literal. Above the BMP this MUST be \\U with eight hex
    digits: Go reads \\u as exactly four, so \\u10d50 silently compiles as
    U+10D5 followed by '0'. That bug produced 44 rows of corrupt data that
    still built cleanly."""
    out = []
    for ch in s:
        o = ord(ch)
        if 0x20 <= o <= 0x7E and ch not in '"\\':
            out.append(ch)
        elif o <= 0xFFFF:
            out.append("\\u%04x" % o)
        else:
            out.append("\\U%08x" % o)
    return '"' + "".join(out) + '"'


def to_ranges(code_points):
    out = []
    for cp in sorted(code_points):
        if out and cp == out[-1][1] + 1:
            out[-1][1] = cp
        else:
            out.append([cp, cp])
    return out


def emit_range_table(name, code_points, comment):
    rs = to_ranges(code_points)
    r16 = [r for r in rs if r[1] <= 0xFFFF]
    r32 = [r for r in rs if r[1] > 0xFFFF]
    lines = [comment, "var %s = &unicode.RangeTable{" % name]
    if r16:
        lines.append("\tR16: []unicode.Range16{")
        lines += ["\t\t{0x%04x, 0x%04x, 1}," % (a, b) for a, b in r16]
        lines.append("\t},")
    if r32:
        lines.append("\tR32: []unicode.Range32{")
        lines += ["\t\t{0x%04x, 0x%04x, 1}," % (a, b) for a, b in r32]
        lines.append("\t},")
    lines.append("}")
    return "\n".join(lines), len(code_points), len(rs)


def main():
    out_dir = sys.argv[1]
    probe = None
    if "--probe-output" in sys.argv:
        probe = open(sys.argv[sys.argv.index("--probe-output") + 1],
                     encoding="utf-8").read()
    if probe is None:
        probe = run_go_probe()

    case_rows, word_gap, space_gap, cased_gap = [], [], [], []
    seen = 0
    for row in probe.splitlines():
        cp_s, gu_s, gl_s, gt_s, gw, gs, gc = row.split()
        cp = int(cp_s, 16)
        ch = chr(cp)
        seen += 1
        go_up, go_low, go_title = (chr(int(x, 16)) for x in (gu_s, gl_s, gt_s))
        py_up, py_low, py_title = ch.upper(), ch.lower(), ch.capitalize()
        if (py_up, py_low, py_title) != (go_up, go_low, go_title):
            case_rows.append("\t0x%04X: {%s, %s, %s}," % (
                cp, go_literal(py_up), go_literal(py_low), go_literal(py_title)))
        if (1 if (ch == "_" or ch.isalnum()) else 0) != int(gw):
            word_gap.append(cp)
        if (1 if ch.isspace() else 0) != int(gs):
            space_gap.append(cp)
        if (1 if unicodedata.category(ch) in ("Lu", "Ll", "Lt") else 0) != int(gc):
            cased_gap.append(cp)

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "case_table.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(case_rows) + "\n")

    word_src, word_n, word_r = emit_range_table(
        "unicode16Word", word_gap,
        "// unicode16Word holds the code points that CPython 3.14 (Unicode 16) counts as\n"
        "// str.isalnum() but that Go 1.23 (Unicode 15) still sees as unassigned, so\n"
        "// unicode.IsLetter/IsNumber return false for them. Without this, \\w, \\b and\n"
        "// CAPFIRST all disagree with the original on those code points. Generated by\n"
        "// diffing the two implementations over every code point.")
    cased_src, cased_n, cased_r = emit_range_table(
        "unicode16Cased", cased_gap,
        "// unicode16Cased is the same gap for the Cased property (Lu, Ll, Lt), used by\n"
        "// the Final_Sigma rule.")
    with open(os.path.join(out_dir, "ranges.txt"), "w", encoding="utf-8") as f:
        f.write(word_src + "\n\n" + cased_src + "\n")

    print("code points compared            %d" % seen)
    print("full-case-mapping disagreements %d rows" % len(case_rows))
    print("  of those above the BMP        %d" % sum(1 for r in case_rows if "\\U" in r))
    print("\\w gap  (python yes, go no)     %d code points in %d ranges" % (word_n, word_r))
    print("Cased gap                       %d code points in %d ranges" % (cased_n, cased_r))
    print("\\s gap                          %d code points: %s"
          % (len(space_gap), [hex(c) for c in space_gap]))
    print("\nwrote %s/case_table.txt and %s/ranges.txt" % (out_dir, out_dir))


if __name__ == "__main__":
    main()