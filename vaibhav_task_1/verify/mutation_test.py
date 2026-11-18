#!/usr/bin/env python3
"""Test the tests: make small wrong changes to the oracle's Go code and check
that the HIDDEN behaviour set catches every one (score < 1.0).

Usage: python3 verify/mutation_test.py      (needs Go >= 1.23)
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK = os.path.join(ROOT, "titlecase-go")
solve = open(os.path.join(TASK, "solution", "solve.sh"), encoding="utf-8").read()
SRC = re.search(r"cat > main.go <<'GOSRC'\n(.*?)\nGOSRC\n", solve, re.S).group(1)

MUTANTS = [
    ("y counted as a consonant", 'runeSet("bcdfghjklmnpqrstvwxz")', 'runeSet("bcdfghjklmnpqrstvwxyz")'),
    ("acronym length > 1 instead of > 2", "allConsonants(w) && len(w) > 2", "allConsonants(w) && len(w) > 1"),
    ("left quote ‘ not accepted in d'/o'/l'", "w[1] != '\\'' && w[1] != '‘'", "w[1] != '\\''"),
    ("right quote ’ also accepted in d'/o'/l'", "w[1] != '\\'' && w[1] != '‘'", "w[1] != '\\'' && w[1] != '‘' && w[1] != '’'"),
    ("v\\.? not greedy", '"to", "v.", "v", "via",', '"to", "v", "v.", "via",'),
    ("no word boundary in SMALL_FIRST", "foldAt(w, k, a) && boundary(w, k+n)", "foldAt(w, k, a)"),
    ("SUBPHRASE case-insensitive", "string(s[i+2:i+2+len(ar)]) == a", "strings.EqualFold(string(s[i+2:i+2+len(ar)]), a)"),
    ("UC_ELSEWHERE counts the first letter", "for t := k + 1; t < j; t++", "for t := k; t < j; t++"),
    ("underscore not a word char in CAPFIRST", "\t\tif isWord(w[i]) {\n\t\t\tout[i] = unicode.ToUpper(w[i])",
     "\t\tif isWord(w[i]) && w[i] != '_' {\n\t\t\tout[i] = unicode.ToUpper(w[i])"),
    ("only ASCII space splits words", "\tcase r >= 0x09 && r <= 0x0d, r >= 0x1c && r <= 0x20:\n\t\treturn true",
     "\tcase r == ' ':\n\t\treturn true\n\tcase false:\n\t\treturn true"),
    ("Mc needs only one char after", "if len(w) < 4 {\n\t\treturn nil, nil, false", "if len(w) < 3 {\n\t\treturn nil, nil, false"),
    ("hyphen/slash parts use small-first/last", "parts[i] = titlecase(p, false)", "parts[i] = titlecase(p, true)"),
    ("all-caps detection disabled", "func isAllCaps(rs []rune) bool {\n", "func isAllCaps(rs []rune) bool {\n\treturn false\n"),
    ("SMALL_LAST ignores trailing punctuation", "if !match && len(s) >= 2 && isPunct(s[len(s)-1]) {", "if false {"),
    ("\\w is ASCII-only", "return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)",
     "return r == '_' || (r < 128 && (unicode.IsLetter(r) || unicode.IsNumber(r)))"),
    ("inline-period check after small words", "if inlinePeriod(w) || (!allCaps && ucElsewhere(w)) {",
     "if false {"),
    ("MC (all caps) prefix not handled", "|| (w[0] == 'M' && w[1] == 'C')", ""),
    ("Mr/Dr rule removed", "if mrMrsMsDr(w) {", "if false && mrMrsMsDr(w) {"),
    ("SUBPHRASE removed", "return string(subphrase(joined))", "return string(joined)"),
    ("initials kept in mixed-case lines too", "if allCaps && ucInitials(w) {", "if ucInitials(w) {"),
    ("o' handled like d'/l'", 'if !strings.ContainsRune("aeiouAEIOU", w[0]) {', "if true {"),
    ("'//' not excluded from slash rule", '!strings.Contains(ws, "//")', "true"),
]


def score(src, tmp, data):
    d = tempfile.mkdtemp(dir=tmp)
    open(os.path.join(d, "go.mod"), "w").write("module titlecase-go\n\ngo 1.23\n")
    open(os.path.join(d, "main.go"), "w").write(src)
    env = dict(os.environ, GOTOOLCHAIN="local", GOPROXY="off", GOFLAGS="-mod=mod")
    b = subprocess.run(["go", "build", "-o", "tc", "."], cwd=d, env=env, capture_output=True, text=True)
    if b.returncode:
        return None, b.stderr.strip().splitlines()[-1]
    out = subprocess.run([os.path.join(d, "tc")], input=data[0], capture_output=True).stdout.split(b"\n")[:-1]
    exp = data[1]
    return sum(1 for i, e in enumerate(exp) if i < len(out) and out[i] == e) / len(exp), ""


def main():
    data_dir = os.path.join(TASK, "tests", "data")
    data = (open(os.path.join(data_dir, "hidden_inputs.txt"), "rb").read(),
            open(os.path.join(data_dir, "hidden_expected.txt"), "rb").read().split(b"\n")[:-1])
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        base, err = score(SRC, tmp, data)
        print(f"{'unmutated oracle':<45} behaviour = {base}")
        assert base == 1.0, err
        for name, old, new in MUTANTS:
            if old not in SRC:
                print(f"{name:<45} MUTATION NOT APPLICABLE"); failures += 1; continue
            s, err = score(SRC.replace(old, new, 1), tmp, data)
            if s is None:
                print(f"{name:<45} (does not compile: {err})"); failures += 1; continue
            caught = s < 1.0
            failures += not caught
            print(f"{name:<45} behaviour = {s:.4f}  {'caught' if caught else 'NOT CAUGHT'}")
    print("RESULT:", "PASS — every mutant caught" if not failures else f"FAIL — {failures} problem(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
