"""Test the tests: make one small wrong change to the Go port at a time and count the hidden lines it gets wrong.

Usage: python mutants.py <task folder> <out folder>
Writes one folder per mutant (go.mod + main.go) and names.txt. A second step builds and runs them in the Go container.
"""
import shutil
import sys
from pathlib import Path

task = Path(sys.argv[1])
out = Path(sys.argv[2])
src = (task / "solution" / "main.go").read_text(encoding="utf-8")
gomod = (task / "solution" / "go.mod").read_text(encoding="utf-8")

M = []  # (name, old, new)


def add(name, old, new, count=1):
    assert src.count(old) >= 1, f"{name}: text not found: {old!r}"
    M.append((name, old, new, count))


add("no_initials_rule", "if allCaps && ucInitials.MatchString(word) {", "if false && ucInitials.MatchString(word) {")
add("apos_always_upper", 'if strings.ContainsRune("aeiouAEIOU", r[0]) {', "if true {")
add("apos_always_lower", 'if strings.ContainsRune("aeiouAEIOU", r[0]) {', "if false {")
add("apos_rest_lowered", "string(r[3:])\n", "strings.ToLower(string(r[3:]))\n")
add("no_mc_rule", "if m := macMc.FindStringSubmatch(word); m != nil {", "if m := macMc.FindStringSubmatch(word); m != nil && false {")
add("mc_rest_flag_off", "return capitalize(m[1]) + titlecase(m[2], true)", "return capitalize(m[1]) + titlecase(m[2], false)")
add("mc_prefix_not_capitalized", "return capitalize(m[1]) + titlecase(m[2], true)", "return m[1] + titlecase(m[2], true)")
add("mc_needs_one_char", "`^([Mm]c|MC)(\\w.+)`", "`^([Mm]c|MC)(\\w.*)`")
add("no_mr_rule", "if mrMrsMsDr.MatchString(word) {", "if false && mrMrsMsDr.MatchString(word) {")
add("mr_rest_lowered", "r, size := utf8.DecodeRuneInString(word)\n\t\treturn strings.ToUpper(string(r)) + word[size:]", "return capitalize(word)")
add("no_inline_period", "if inlinePeriod.MatchString(word) || (!allCaps && ucElsewhere.MatchString(word)) {",
    "if !allCaps && ucElsewhere.MatchString(word) {")
add("inline_period_letters_only", "inlinePeriod = regexp.MustCompile(`\\w[.]\\w`)", "inlinePeriod = regexp.MustCompile(`[A-Za-z][.][A-Za-z]`)")
add("uc_elsewhere_also_in_caps_line", "if inlinePeriod.MatchString(word) || (!allCaps && ucElsewhere.MatchString(word)) {",
    "if inlinePeriod.MatchString(word) || ucElsewhere.MatchString(word) {")
add("no_uc_elsewhere", "if inlinePeriod.MatchString(word) || (!allCaps && ucElsewhere.MatchString(word)) {",
    "if inlinePeriod.MatchString(word) {")
add("uc_elsewhere_first_letter_counts", "]*?[a-zA-Z]+[A-Z]+?`)", "]*?[a-zA-Z]*[A-Z]+?`)")
add("uc_elsewhere_no_punct_prefix", "ucElsewhere = regexp.MustCompile(`^[` + punct + `]*?[a-zA-Z]+[A-Z]+?`)",
    "ucElsewhere = regexp.MustCompile(`^[a-zA-Z]+[A-Z]+?`)")
add("small_words_not_lowered", "if smallWords.MatchString(word) {\n\t\treturn strings.ToLower(word)", "if smallWords.MatchString(word) {\n\t\treturn word")
add("no_slash_rule", 'if strings.Contains(word, "/") && !strings.Contains(word, "//") {', 'if false && strings.Contains(word, "/") {')
add("slash_rule_ignores_double_slash", 'if strings.Contains(word, "/") && !strings.Contains(word, "//") {', 'if strings.Contains(word, "/") {')
add("no_hyphen_rule", 'if strings.Contains(word, "-") {', 'if false && strings.Contains(word, "-") {')
add("hyphen_before_slash", 'if strings.Contains(word, "/") && !strings.Contains(word, "//") {',
    'if strings.Contains(word, "-") {\n\t\treturn titleParts(word, "-")\n\t}\n\tif strings.Contains(word, "/") && !strings.Contains(word, "//") {')
add("parts_flag_on", "parts[i] = titlecase(part, false)", "parts[i] = titlecase(part, true)")
add("no_caps_lowering", "if allCaps {\n\t\tword = strings.ToLower(word)", "if false {\n\t\tword = strings.ToLower(word)")
add("consonant_rule_len3", "utf8.RuneCountInString(word) > 2 &&", "utf8.RuneCountInString(word) > 3 &&")
add("consonant_rule_len1", "utf8.RuneCountInString(word) > 2 &&", "utf8.RuneCountInString(word) > 1 &&")
add("no_consonant_rule", "utf8.RuneCountInString(word) > 2 &&", "false &&")
add("consonants_include_y", "[bcdfghjklmnpqrstvwxz]", "[bcdfghjklmnpqrstvwxyz]")
add("capfirst_letters_only", "capFirst = regexp.MustCompile(`^[` + punct + `]*?(\\w)`)", "capFirst = regexp.MustCompile(`^[` + punct + `]*?([A-Za-z])`)")
add("capfirst_no_punct_prefix", "capFirst = regexp.MustCompile(`^[` + punct + `]*?(\\w)`)", "capFirst = regexp.MustCompile(`^(\\w)`)")
add("capfirst_any_prefix", "capFirst = regexp.MustCompile(`^[` + punct + `]*?(\\w)`)", "capFirst = regexp.MustCompile(`^\\W*?(\\w)`)")
add("capfirst_greedy_prefix", "capFirst = regexp.MustCompile(`^[` + punct + `]*?(\\w)`)", "capFirst = regexp.MustCompile(`^[` + punct + `]*([A-Za-z0-9])`)")
add("no_small_first", "if m := smallFirst.FindStringSubmatchIndex(tcLine[0]); m != nil {", "if m := smallFirst.FindStringSubmatchIndex(tcLine[0]); m != nil && false {")
add("small_first_no_punct_prefix", "smallFirst = regexp.MustCompile(`(?i)^([` + punct + `]*)(` + small + `)\\b`)",
    "smallFirst = regexp.MustCompile(`(?i)^()(` + small + `)\\b`)")
add("small_first_no_boundary", "smallFirst = regexp.MustCompile(`(?i)^([` + punct + `]*)(` + small + `)\\b`)",
    "smallFirst = regexp.MustCompile(`(?i)^([` + punct + `]*)(` + small + `)`)")
add("no_small_last", "if m := smallLast.FindStringIndex(tcLine[last]); m != nil {", "if m := smallLast.FindStringIndex(tcLine[last]); m != nil && false {")
add("small_last_no_punct", "smallLast = regexp.MustCompile(`(?i)\\b(` + small + `)[` + punct + `]?$`)", "smallLast = regexp.MustCompile(`(?i)\\b(` + small + `)$`)")
add("small_last_many_punct", "smallLast = regexp.MustCompile(`(?i)\\b(` + small + `)[` + punct + `]?$`)",
    "smallLast = regexp.MustCompile(`(?i)\\b(` + small + `)[` + punct + `]*$`)")
add("small_last_whole_word_only", "smallLast = regexp.MustCompile(`(?i)\\b(` + small + `)[` + punct + `]?$`)",
    "smallLast = regexp.MustCompile(`(?i)^(` + small + `)[` + punct + `]?$`)")
add("first_last_skip_empty_words",
    "\t\tif m := smallFirst.FindStringSubmatchIndex(tcLine[0]); m != nil {\n\t\t\tw := tcLine[0]\n\t\t\ttcLine[0] = w[:m[4]]",
    "\t\tfi := 0\n\t\tfor fi < len(tcLine)-1 && tcLine[fi] == \"\" {\n\t\t\tfi++\n\t\t}\n\t\tif fi > 0 {\n\t\t\ttcLine[0], tcLine[fi] = tcLine[fi], tcLine[0]\n\t\t}\n"
    "\t\tif m := smallFirst.FindStringSubmatchIndex(tcLine[0]); m != nil {\n\t\t\tw := tcLine[0]\n\t\t\ttcLine[0] = w[:m[4]]")
add("no_subphrase", "matches := subphrase.FindAllStringSubmatchIndex(result, -1)", 'matches := subphrase.FindAllStringSubmatchIndex("", -1)')
add("subphrase_with_boundary", "[ ])(` + small + `)`)", "[ ])(` + small + `)\\b`)")
add("subphrase_ignores_case", "subphrase = regexp.MustCompile(`([:.;", "subphrase = regexp.MustCompile(`(?i)([:.;")
add("subphrase_any_space", "\\x{2015}][ ])(", "\\x{2015}]\\s)(")
add("capitalize_keeps_rest", "return strings.ToUpper(string(r)) + strings.ToLower(s[size:])", "return strings.ToUpper(string(r)) + s[size:]")
add("tab_is_not_a_space", "return unicode.IsSpace(r) || (r >= 0x1c && r <= 0x1f)", "return r == ' ' || (unicode.IsSpace(r) && false)")
add("caps_flag_ignores_case_less_lines", "allCaps := strings.ToUpper(line) == line", "allCaps := strings.ToUpper(line) == line && strings.ToLower(line) != line")

SMALLS = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v\\.?", "via", "vs\\.?"]
small_line = "const small = `" + "|".join(SMALLS) + "`"
assert small_line in src
for w in SMALLS:
    rest = [x for x in SMALLS if x != w]
    M.append(("small_list_without_" + w.replace("\\.?", "_dot"), small_line, "const small = `" + "|".join(rest) + "`", 1))

MARKS = [("colon", ":"), ("dot", "."), ("semicolon", ";"), ("question", "?"), ("bang", "!"), ("hyphen", "\\-"), ("u2013", "\\x{2013}"), ("u2012", "\\x{2012}"),
         ("u2014", "\\x{2014}"), ("u2015", "\\x{2015}")]
mark_cls = "[:.;?!\\-\\x{2013}\\x{2012}\\x{2014}\\x{2015}][ ]"
assert mark_cls in src
for name, tok in MARKS:
    M.append(("subphrase_mark_without_" + name, mark_cls, mark_cls.replace(tok, "", 1), 1))

PUNCTS = [("bang", "!"), ("dquote", '"'), ("u201C", "\\x{201C}"), ("hash", "#"), ("dollar", "$"), ("percent", "%"), ("amp", "&"),
          ("squote", "'"), ("u2018", "\\x{2018}"), ("lparen", "("), ("rparen", ")"), ("star", "*"), ("plus", "+"), ("comma", ","),
          ("hyphen", "\\-"), ("u2013", "\\x{2013}"), ("u2012", "\\x{2012}"), ("u2014", "\\x{2014}"), ("u2015", "\\x{2015}"),
          ("dot", "."), ("slash", "/"), ("colon", ":"), ("semicolon", ";"), ("question", "?"), ("at", "@"), ("lbracket", "\\["),
          ("backslash", "\\\\"), ("rbracket", "\\]"), ("underscore", "_"), ("lbrace", "{"), ("pipe", "|"), ("rbrace", "}"), ("tilde", "~")]
punct_line = [l for l in src.split("\n") if l.startswith("const punct = ")][0]
for name, tok in PUNCTS:
    assert tok in punct_line, name
    head, tail = punct_line.split(" = ", 1)
    M.append(("punct_without_" + name, punct_line, head + " = " + tail.replace(tok, "", 1), 1))
M.append(("punct_without_backtick", punct_line, punct_line.replace(' + "`" + ', ' + "" + '), 1))
for name, extra in [("lt", "<"), ("gt", ">"), ("eq", "="), ("caret", "\\^"), ("u2019", "\\x{2019}"), ("u201D", "\\x{201D}")]:
    M.append(("punct_with_extra_" + name, punct_line, punct_line.replace("`!\"", "`" + extra + "!\"", 1), 1))

if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
names = []
for name, old, new, count in M:
    text = src.replace(old, new, count)
    assert text != src, name
    d = out / name
    d.mkdir()
    (d / "go.mod").write_text(gomod, encoding="utf-8", newline="\n")
    (d / "main.go").write_text(text, encoding="utf-8", newline="\n")
    names.append(name)
(out / "names.txt").write_text("\n".join(names) + "\n", encoding="utf-8", newline="\n")
print(len(names), "mutants written")
