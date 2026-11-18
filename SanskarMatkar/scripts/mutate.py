#!/usr/bin/env python3
"""Plant small bugs in the oracle's Go code and check the hidden set catches each.
Run from a folder holding the oracle's main.go and go.mod (e.g. after solve.sh)."""
import subprocess, shutil, pathlib, sys
src = pathlib.Path('main.go').read_text()
D = str(pathlib.Path(__file__).resolve().parents[1] / 'tests' / 'data') + '/'
inp = open(D+'hidden_inputs.txt','rb').read()
exp = open(D+'hidden_expected.txt','rb').read().split(b'\n')[:-1]
M = [
 ("y treated as consonant",          '"bcdfghjklmnpqrstvwxz"', '"bcdfghjklmnpqrstvwxyz"'),
 ("ASCII-only \\s (Go default)",      'case r == 0x85, r == 0xa0,', 'case false,'),
 ("ASCII-only \\w (Go default)",      "return r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)", "return r == '_' || (r < 128 && (unicode.IsLetter(r) || unicode.IsNumber(r)))"),
 ("’ (U+2019) counted as PUNCT",      "'―', '.', '/', ':',", "'―', '’', '.', '/', ':',"),
 ("no sub-phrase rule",               "return subphrase(b.String())", "return b.String()"),
 ("sub-phrase case-insensitive",      "string(r[i+2:e]) == w", "foldEq(r[i+2:e], w)"),
 ("capitalize keeps rest's case",     "return string(unicode.ToTitle(r[0])) + lower(string(r[1:]))", "return string(unicode.ToTitle(r[0])) + string(r[1:])"),
 ("hyphen parts keep first/last rule","parts[i] = titlecase(p, false)\n\t\t}\n\t\treturn strings.Join(parts, \"-\")", "parts[i] = titlecase(p, true)\n\t\t}\n\t\treturn strings.Join(parts, \"-\")"),
 ("Mc recursion without first/last",  "return capitalize(p) + titlecase(rest, true)", "return capitalize(p) + titlecase(rest, false)"),
 ("all-caps check skipped",           "allCaps := upper(line) == line", "allCaps := false"),
 ("small-first ignores \\b",          "foldEq(r[k:e], w) && boundary(r, e)", "foldEq(r[k:e], w)"),
 ("v. tried after v (non-greedy)",    '"to", "v.", "v", "via", "vs.", "vs"}', '"to", "v", "v.", "via", "vs", "vs."}'),
 ("trim leading/trailing spaces",     "func titlecaseLine(line string, smallFirstLast bool) string {", "func titlecaseLine(line string, smallFirstLast bool) string {\n\tline = strings.TrimSpace(line)"),
]
for name, a, b in M:
    assert src.count(a) == 1, name
    pathlib.Path('/tmp/mut').mkdir(exist_ok=True)
    shutil.copy('go.mod', '/tmp/mut/go.mod')
    pathlib.Path('/tmp/mut/main.go').write_text(src.replace(a, b))
    subprocess.run(['go','build','-o','/tmp/mut/tc','.'], cwd='/tmp/mut', check=True)
    got = subprocess.run(['/tmp/mut/tc'], input=inp, capture_output=True).stdout.split(b'\n')[:-1]
    ok = sum(g == e for g, e in zip(got, exp))
    print(f"{name:36s} behaviour = {ok/len(exp):.4f}  reward = {(2+4*ok/len(exp))/6:.3f}  {'CAUGHT' if ok < len(exp) else 'MISSED'}")
