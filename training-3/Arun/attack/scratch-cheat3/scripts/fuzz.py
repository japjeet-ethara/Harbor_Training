"""Fuzzer: compare a Linux build of the Go port with the ORIGINAL Python titlecase().

Usage: python scripts/fuzz.py <path-to-go-binary-ending-in--linux> [count] [seed] [mode]
Needs the `regex` package, and Docker with the golang:1.23 image for a -linux binary.
mode = "narrow" (characters the task generator uses) or "wide" (extra Unicode).

Not part of the Harbor task; it only helps find lines where the port differs.
"""
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "environment"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "python-titlecase"))
import titlecase as T  # noqa: E402
from titlecase import titlecase  # noqa: E402

assert T.REGEX_AVAILABLE, "install the `regex` package: the reference behaviour needs it"

binary = sys.argv[1]
count = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
mode = sys.argv[4] if len(sys.argv) > 4 else "narrow"
rng = random.Random(seed)

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
WORDS = """lord rings war peace time mice men cat dog music face dance title string apple deal
problem probe trick plane edit line force case thing spool jobs thoughts permissions voodoo
caps name machine great young restless mix space characters hier yea no st nd th cnn tv hmm pfft
dvd html mph xyz rhythm my sky itunes iTunes AT&T NASA OmniFocus McCarthy eBay SEC's Q&A
mr mrs ms mss dr mc mac mctavish mcdonalds macdonalds mcfoo mcthe mcby mc1 mc_x
o'reilly d'angelo l'grange o'grange's o'as' o's' O'GranGe l'GranGe o‘neil
example.com del.icio.us http://foo.com e.g. i.e. u.s.a. node.js v.x vs.x in.a D.C. A.B A.BC. U.S.
and/or word/word him/her tcp/ip a/b/c http://foo.com/and/or x//y /x x/
end-to-end state-of-the-art e-mail two-not-three x-ray to-do a-b the-the - -- -a a-
34th 3rd 2nd 5th 2lmc 7 1984 3d (u)rware vapo(u)rware 5TH
niño arrivé café über ýæ ñø façade El NIÑO ARRIVÉ""".split()
PUNCT = list("!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~") + ["”", "’", "<", ">", "=", "^"]
SEPS = [" "] * 30 + ["  ", "\t", " ", " ", " ", ": ", " - ", " — ", " – ", "; ", "? ", "! ", ". ", ", "]
LETTERS = "abcdefghijklmnopqrstuvwxyz"
WIDE_LETTERS = "ßſKİıǅǆΣσςäÖøÅžŁđﬁŉµªº²½ẖẗẘẙẚ"
WIDE_SEPS = ["　", "​", "\x0b", "\x0c", "\x1c", "\x1f", "\x85", " ", "﻿", "­"]


def rand_case(w):
    r = rng.random()
    if r < 0.55:
        return w
    if r < 0.70:
        return w.upper()
    if r < 0.80:
        return w.capitalize()
    if r < 0.90:
        return "".join(c.upper() if rng.random() < 0.4 else c for c in w)
    return w.lower()


def rand_token():
    r = rng.random()
    if r < 0.25:
        w = rng.choice(SMALL)
    elif r < 0.80:
        w = rng.choice(WORDS)
    else:
        alphabet = LETTERS + ("" if mode == "narrow" else WIDE_LETTERS)
        w = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 6)))
    w = rand_case(w)
    if rng.random() < 0.18:
        w = rng.choice(PUNCT) + w
    if rng.random() < 0.22:
        w = w + rng.choice(PUNCT)
    if rng.random() < 0.05:
        k = rng.randint(0, len(w))
        w = w[:k] + rng.choice(PUNCT + list("0123456789")) + w[k:]
    return w


def rand_line():
    n = rng.randint(1, 8)
    seps = SEPS if mode == "narrow" else SEPS + WIDE_SEPS
    out = []
    if rng.random() < 0.03:
        out.append(rng.choice(seps))
    for i in range(n):
        out.append(rand_token())
        if i < n - 1:
            out.append(rng.choice(seps))
    if rng.random() < 0.03:
        out.append(rng.choice(seps))
    line = "".join(out)
    if rng.random() < 0.12:
        line = line.upper()
    return line


lines = []
seen = set()
while len(lines) < count:
    s = rand_line()
    if "\n" in s or "\r" in s or s in seen:
        continue
    seen.add(s)
    lines.append(s)

expected = [titlecase(s) for s in lines]
keep = [i for i, e in enumerate(expected) if "\n" not in e]
lines = [lines[i] for i in keep]
expected = [expected[i] for i in keep]

cmd = [binary]
if binary.endswith("-linux"):
    # A Linux build: run it inside the task's base image (Windows may block
    # locally built executables).
    b = Path(binary).resolve()
    cmd = ["docker", "run", "--rm", "-i", "-v", f"{b.parent}:/w:ro", "golang:1.23", f"/w/{b.name}"]
proc = subprocess.run(cmd, input=("\n".join(lines) + "\n").encode("utf-8"), capture_output=True)
if proc.returncode != 0:
    sys.exit(f"binary failed: {proc.stderr.decode('utf-8', 'replace')[:500]}")
actual = proc.stdout.decode("utf-8").split("\n")
if actual and actual[-1] == "":
    actual.pop()

sys.stdout.reconfigure(encoding="utf-8")
print(f"mode={mode} lines={len(lines)} output_lines={len(actual)}")
bad = 0
for i, (inp, exp) in enumerate(zip(lines, expected)):
    got = actual[i] if i < len(actual) else "<missing>"
    # Known limit: Python lower-cases a word-final Greek sigma to a different letter.
    if got != exp and got.replace("σ", "ς") != exp.replace("σ", "ς"):
        bad += 1
        if bad <= 15:
            print(f"DIFF input={inp!a}\n     want={exp!a}\n      got={got!a}")
print(f"mismatches: {bad} of {len(lines)}")
