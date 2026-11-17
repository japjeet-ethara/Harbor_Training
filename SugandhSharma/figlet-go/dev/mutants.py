"""Test the tests: make one small wrong change to the Go port at a time.

Usage (from the task folder):  python dev/mutants.py . ../scratch/mut
Writes one folder per broken variant (go.mod and the .go files) and names.txt.
dev/run_mutants.sh then builds every variant in the room image and counts the cases it gets wrong.
"""
import shutil
import sys
from pathlib import Path

task, out = Path(sys.argv[1]), Path(sys.argv[2])
sol = task / "solution"
src = {p.name: p.read_text(encoding="utf-8") for p in sorted(sol.glob("*.go"))}
gomod = (sol / "go.mod").read_text(encoding="utf-8")
M = []


def add(name, file, old, new):
    assert src[file].count(old) == 1, f"{name}: the text must be in {file} exactly once: {old!r}"
    M.append((name, file, old, new))


R, F, C = "render.go", "font.go", "main.go"

# the six smushing rules, kerning and universal smushing
add("rule1_equal_off", R, "if mode&smEqual != 0 && left == right {", "if false && left == right {")
add("rule2_lowline_off", R, "if mode&smLowline != 0 {", "if false {")
add("rule3_hierarchy_off", R, "if mode&smHierarchy != 0 {", "if false {")
add("rule3_hierarchy_one_class_missing", R, 'smushPair{"()", "<>"})', 'smushPair{"()", ""})')
add("rule3_hierarchy_slash_class_wrong", R, 'smushPair{`\\/`, "[]{}()<>"},', 'smushPair{`/`, "[]{}()<>"},')
add("rule4_pair_off", R, "if mode&smPair != 0 {", "if false {")
add("rule4_pair_one_order_only", R, "[]string{string(left) + string(right), string(right) + string(left)}",
    "[]string{string(left) + string(right)}")
add("rule5_bigx_off", R, "if mode&smBigX != 0 {", "if false {")
add("rule6_hardblank_off", R, "if mode&smHardblank != 0 && hard(left) && hard(right) {", "if false && hard(left) {")
add("hardblank_smushes_like_a_letter", R, "if hard(left) || hard(right) {\n\t\treturn 0, false", "if false {\n\t\treturn 0, false")
add("lowline_keeps_the_underscore", R,
    "if strings.ContainsRune(s.a, left) && strings.ContainsRune(s.b, right) {\n\t\t\treturn right, true",
    "if strings.ContainsRune(s.a, left) && strings.ContainsRune(s.b, right) {\n\t\t\treturn left, true")
add("universal_ignores_direction", R, "if b.direction == rightToLeft {\n\t\t\treturn left, true", "if false {\n\t\t\treturn left, true")
add("universal_hardblank_wins", R, "if hard(left) {\n\t\t\treturn right, true", "if false {\n\t\t\treturn right, true")
add("narrow_letters_may_smush", R, "if b.prevCharWidth < 2 || b.curCharWidth < 2 {", "if false {")
add("narrow_rule_previous_only", R, "if b.prevCharWidth < 2 || b.curCharWidth < 2 {", "if b.prevCharWidth < 2 {")
add("narrow_rule_current_only", R, "if b.prevCharWidth < 2 || b.curCharWidth < 2 {", "if b.curCharWidth < 2 {")
add("kerning_fonts_smush", R, "if mode&smSmush == 0 {\n\t\treturn 0, false", "if false {\n\t\treturn 0, false")
add("no_kerning_at_all", R, "if b.font.smushMode&(smSmush|smKern) == 0 {", "if true {")
add("amount_blank_edge_not_counted", R, "if ch1Empty || ch1 == ' ' {", "if ch1Empty {")
add("amount_smushable_edge_not_counted", R, "if _, ok := b.smushChars(ch1, ch2); ok {", "if _, ok := b.smushChars(ch1, ch2); ok && false {")
add("amount_not_capped_by_letter_width", R, "maxSmush := b.curCharWidth", "maxSmush := 1 << 20")
add("amount_ignores_direction", R, "\t\t\tlineLeft, lineRight = lineRight, lineLeft", "\t\t\tlineLeft, lineRight = lineLeft, lineRight")
add("smush_row_ignores_direction", R, "\t\taddLeft, addRight = addRight, addLeft", "\t\taddLeft, addRight = addLeft, addRight")

# wrapping
add("wrap_one_column_late", R, "if b.currentTotalWidth >= b.width {", "if b.currentTotalWidth > b.width {")
add("wrap_ignores_the_smush", R, "len(b.buffer[0]) + b.curCharWidth - b.maxSmush", "len(b.buffer[0]) + b.curCharWidth")
add("never_wraps_at_a_blank", R, "if c == ' ' {", "if false {")
add("blank_marker_after_the_blank", R,
    "\tif c == ' ' {\n\t\tb.blankMarkers = append(b.blankMarkers, blankMarker{copyBuffer(b.buffer), b.iterator})\n\t}\n\n\tif b.currentTotalWidth >= b.width {\n\t\tb.handleNewLine()\n\t} else {\n\t\tfor row := 0; row < b.font.height; row++ {\n\t\t\tb.addCurCharRowToBufferRow(curChar, row)\n\t\t}\n\t}",
    "\tif b.currentTotalWidth >= b.width {\n\t\tb.handleNewLine()\n\t} else {\n\t\tfor row := 0; row < b.font.height; row++ {\n\t\t\tb.addCurCharRowToBufferRow(curChar, row)\n\t\t}\n\t}\n\tif c == ' ' {\n\t\tb.blankMarkers = append(b.blankMarkers, blankMarker{copyBuffer(b.buffer), b.iterator})\n\t}")
add("line_break_in_text_ignored", R, "if c == '\\n' {", "if false {")
add("previous_width_forgotten_after_wrap", R, "\t\tb.handleNewLine()\n\t} else {", "\t\tb.handleNewLine()\n\t\treturn\n\t} else {")
add("too_wide_letter_one_column_early", R, "if b.width < b.font.width[c] {", "if b.width <= b.font.width[c] {")
add("empty_last_line_printed", R, "if len(b.buffer[0]) != 0 {", "if true {")

# justification and direction
add("right_without_the_spare_column", R, "b.width-len(buffer[row])-1)", "b.width-len(buffer[row]))")
add("center_rounds_up", R, "(b.width-len(buffer[row]))/2)", "(b.width-len(buffer[row])+1)/2)")
add("center_in_80_columns", R, "(b.width-len(buffer[row]))/2)", "(80-len(buffer[row]))/2)")
add("right_in_80_columns", R, "b.width-len(buffer[row])-1)", "80-len(buffer[row])-1)")
add("auto_justify_ignores_direction", C, 'if direction == rightToLeft {\n\t\t\tjustify = "right"', 'if false {\n\t\t\tjustify = "right"')
add("hardblanks_left_in", R, 'return strings.ReplaceAll(s, b.font.hardBlank, " ")', "return s")

# -r, -F, -s, -n
add("reverse_without_swapping_characters", R, "reverseRunes(translate(row, reverseMap))", "reverseRunes(row)")
add("reverse_without_mirroring_rows", R, "reverseRunes(translate(row, reverseMap))", "translate(row, reverseMap)")
add("flip_without_swapping_characters", R, "translate(rows[i], flipMap)", "rows[i]")
add("flip_keeps_row_order", R, "for i := len(rows) - 1; i >= 0; i-- {", "for i := 0; i < len(rows); i++ {")
add("strip_keeps_leading_rows", R, 'if strip(row) != "" || charsSeen {', 'if strip(row) != "" || charsSeen || true {')
add("strip_drops_inner_empty_rows", R, 'if strip(row) != "" || charsSeen {', 'if strip(row) != "" || (charsSeen && false) {')
add("strip_keeps_trailing_whitespace", R, "return rstrip(newFromList(out))", "return newFromList(out)")
add("strip_only_trailing_newlines", R, "return rstrip(newFromList(out))", 'return strings.TrimRight(newFromList(out), "\\n")')
add("normalize_without_first_newline", R, 'return "\\n" + stripSurroundingNewlines(s) + "\\n"', 'return stripSurroundingNewlines(s) + "\\n"')
add("n_wins_over_s", C,
    "\tif opts.strip {\n\t\tr = stripSurroundingNewlines(r)\n\t} else if opts.normal {\n\t\tr = normalizeSurroundingNewlines(r)\n\t}",
    "\tif opts.normal {\n\t\tr = normalizeSurroundingNewlines(r)\n\t} else if opts.strip {\n\t\tr = stripSurroundingNewlines(r)\n\t}")

# main()
add("auto_direction_ignores_font_header", C, "if font.printDirection == 1 {", "if false {")
add("default_width_79", C, 'justify: "auto", width: 80}', 'justify: "auto", width: 79}')
add("default_font_slant", C, 'o := options{font: "standard",', 'o := options{font: "slant",')
add("text_arguments_joined_without_space", C, 'text := strings.Join(args, " ")', 'text := strings.Join(args, "")')
add("no_final_newline", C, '\tout.WriteString("\\n")\n', "")

# font file parsing
add("german_letters_not_loaded", F, "\tif data.more() {\n\t\tfor _, i := range", "\tif false {\n\t\tfor _, i := range")
add("hex_coded_letters_not_loaded", F, "if len(code) >= 2 && code[0] == '0' && (code[1] == 'x' || code[1] == 'X') {", "if false {")
add("only_one_end_mark_cut", F, " || (i+1 < len(line) && line[i+1] == end && allSpace(line[i+2:]))", "")
add("empty_letters_kept", F, "if i == 32 || !empty(letter) {", "if true {")
add("old_layout_not_masked", F, "fullLayout = (oldLayout & 31) | 128", "fullLayout = oldLayout | 128")
add("width_is_first_row_only", F, "\t\t\tif len(line) > width {", "\t\t\tif n == 0 {")

reverse_block = src[R][src[R].index("var reverseMap"):src[R].index("var flipMap")]
for a, b in [("(", ")"), ("/", "\\\\"), ("<", ">"), ("[", "]"), ("{", "}")]:
    old = "'%s': '%s', '%s': '%s'" % (a, b, b, a)
    name = {"(": "round", "/": "slash", "<": "angle", "[": "square", "{": "curly"}[a]
    assert reverse_block.count(old) == 1, name
    M.append(("reverse_map_without_" + name, R, reverse_block, reverse_block.replace(old, "'\\x00': '\\x00'", 1)))

FLIP = [("slash", "'/': '\\\\', "), ("backslash", "'\\\\': '/', "), ("capital_A", "'A': 'V', "),
        ("capital_V", "'V': 'A', "), ("capital_M", "'M': 'W', "), ("capital_W", "'W': 'M', "),
        ("capital_P", "'P': 'b', "), ("capital_R", "'R': 'b', "), ("small_b", "'b': 'P',"),
        ("caret", "'^': 'v', "), ("small_v", "'v': '^', "), ("underscore", "'_': '-', "),
        ("small_m", "'m': 'w', "), ("small_w", "'w': 'm',")]
flip_block = src[R][src[R].index("var flipMap"):src[R].index("func newFromList")]
for name, old in FLIP:
    assert flip_block.count(old) == 1, name
    M.append(("flip_map_without_" + name, R, flip_block, flip_block.replace(old, "", 1)))

if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
names = []
for name, file, old, new in M:
    changed = src[file].replace(old, new, 1)
    assert changed != src[file], name
    d = out / name
    d.mkdir()
    (d / "go.mod").write_text(gomod, encoding="utf-8", newline="\n")
    for fn, text in src.items():
        (d / fn).write_text(changed if fn == file else text, encoding="utf-8", newline="\n")
    names.append(name)
(out / "names.txt").write_text("\n".join(names) + "\n", encoding="utf-8", newline="\n")
print(len(names), "broken variants written")
