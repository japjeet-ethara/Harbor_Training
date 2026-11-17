#!/usr/bin/env python3
"""Freeze pyfiglet's answers into tests/data/{visible,hidden}.jsonl.

Runs on the author's laptop, never inside Docker. It expects the pyfiglet
checkout from Step 1 next to the task folder, with the font setup done:

    ../pyfiglet                      (commit 255827efbc09d662875dad50fa0edc1e1263bf45)
    ../pyfiglet/pyfiglet/fonts/      (a copy of pyfiglet/fonts-standard/)

Every "out" comes from running the ORIGINAL pyfiglet main() in a fresh
process with the case's args. Nothing is written by hand. Cases where
pyfiglet crashes (for example "Width is not enough to print this
character") or never finishes (a glyph exactly as wide as -w) are dropped
and a new case is drawn in their place, so the files hold only answers the
original really produces.

Usage:  python tests/gen.py
"""

import json
import os
import random
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYFIGLET = HERE.parent.parent / "pyfiglet"
DATA = HERE / "data"
N_CASES = 2000
TIMEOUT_SEC = 20
WORKERS = 8

# The eight required fonts, plus ivrit (its header asks for right-to-left,
# so it is the only way to test "-D auto" picking right-to-left).
FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
EXTRA_FONTS = ["ivrit"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFY = ["auto", "left", "center", "right"]
DIRECTION = ["auto", "left-to-right", "right-to-left"]

WORDS = (
    "hello world figlet python go port shout giant letters smush kern wrap "
    "center mirror flip banner shadow script slant small big mini harbor "
    "twin exam test answer secret quick brown fox jumps over the lazy dog "
    "AVATAR WAVE MAP VIM bump PRAM wolf Rust 2024 v1.2.3 x86_64 a I ok"
).split()

# Rare cases found while reading FigletBuilder (see NOTES.md).
TRICKY = [
    "|_|", "||", "|", "__", "_|_", "/\\", "\\/", "/\\/\\", "\\\\//", "><", "<>",
    "[]", "][", "{}", "}{", "()", ")(", "[|]", "{_}", "(/)", "<_>", "|/\\|",
    "_/", "\\_", "/_\\", "[_]", "{|}", "(|)", "<|>", "x_y", "a|b", "$", "$$",
    "a$b", "q", "Ww", "MW", "VA", "Pb", "^v", "|_|  |_|", "_ _", "/ \\",
    "| / \\ _ [ ] { } ( ) < >", "|/\\_[]{}()<>",
    # every pair of hierarchy classes, both orders
    "{(", "({", "{<", "<{", "[{", "{[", "[(", "([", "(<", "<(", "[<", "<[",
    "|{", "}|", "|(", ")|", "|[", "]|", "|<", ">|", "/{", "}\\", "/(", ")\\",
    "<{[(|)]}>", "{[(<>)]}", "([{|}])", "_{_", "_(_", "_<_", "_[_",
]
DOUBLE_SPACE = ["a  b", "  lead", "trail  ", "x   y", "hello  world", " ", "   "]
LATIN1 = ["é", "ß", "ñ", "Ä", "Ö", "Ü", "ä", "ö", "ü", "ÿ", "ç", "Ångström",
          "straße", "niño", "café", "Größe", "über", "¡olé!", "©®", "±§"]
MISSING = ["€", "日本", "☃", "😀", "\t", "Ω", "→", " ", "\x7f", "\x01", "ǅ"]
NEWLINES = ["one\ntwo", "\n", "a\n\nb", "\nlead", "trail\n", "x \ny"]


def word():
    return random.choice(WORDS)


def sentence(lo, hi):
    return " ".join(word() for _ in range(random.randint(lo, hi)))


def make_text():
    kind = random.choices(
        ["words", "tricky", "mix", "long", "double", "latin", "missing", "newline", "empty"],
        weights=[16, 22, 18, 12, 8, 9, 8, 5, 2],
    )[0]
    if kind == "words":
        return sentence(1, 3)
    if kind == "tricky":
        return random.choice(TRICKY)
    if kind == "mix":
        parts = [random.choice(TRICKY + LATIN1 + DOUBLE_SPACE + MISSING + [word()] * 6)
                 for _ in range(random.randint(2, 4))]
        return random.choice(["", " "]).join(parts)
    if kind == "long":
        return sentence(5, 14)
    if kind == "double":
        return random.choice(DOUBLE_SPACE).replace("a", word(), 1)
    if kind == "latin":
        return random.choice(LATIN1 + [w + random.choice(LATIN1) for w in WORDS[:5]])
    if kind == "missing":
        return word() + random.choice(MISSING) + random.choice(["", word()])
    if kind == "newline":
        return random.choice(NEWLINES)
    return ""


def make_args():
    """Options (in random order, each one or two tokens), then the text."""
    roll = random.random
    groups = []
    font = random.choice(FONTS) if roll() < 0.92 else random.choice(EXTRA_FONTS)
    if font != "standard" or roll() < 0.7:  # sometimes rely on the default font
        groups.append(["-f", font])
    # Right-to-left and narrow widths are where the hard rules live, so both
    # get extra weight.
    if roll() < 0.9:
        groups.append(["-w", str(random.choices(WIDTHS, weights=[3, 3, 2, 2, 2, 1])[0])])
    if roll() < 0.85:
        groups.append(["-j", random.choice(JUSTIFY)])
    if roll() < 0.85:
        groups.append(["-D", random.choices(DIRECTION, weights=[1, 1, 2])[0]])
    for flag in ["-r", "-F", "-s", "-n"]:
        if random.randrange(4) == 0:  # each flag is on in 1 of 4 cases
            groups.append([flag])
    random.shuffle(groups)
    args = [tok for g in groups for tok in g]

    text = make_text()
    pieces = text.split(" ")
    # Sometimes pass the text as several arguments; pyfiglet joins them with
    # one space. Never let a piece look like an option.
    if len(pieces) > 1 and roll() < 0.25 and not any(p.startswith("-") for p in pieces):
        return args + pieces
    return args + [text]


def option(args, name):
    """Value of option `name` in a case's args, or None."""
    for i, tok in enumerate(args[:-1]):
        if tok == name and (i == 0 or args[i - 1] not in ("-f", "-w", "-j", "-D")):
            return args[i + 1]
    return None


DRIVER = r"""
import io, json, sys
sys.path.insert(0, sys.argv[1])
import pyfiglet
args = json.loads(sys.stdin.read())
buf = io.BytesIO()
sys.stdout = io.TextIOWrapper(buf, encoding="utf-8")
sys.argv = ["pyfiglet"] + args
rc = pyfiglet.main()
sys.__stdout__.buffer.write(buf.getvalue())
sys.exit(rc or 0)
"""


def run_original(args, cwd):
    """Return pyfiglet's exact stdout as text, or None if it fails or hangs."""
    env = dict(os.environ, PYTHONHASHSEED="0", APPDATA=cwd, PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run(
            [sys.executable, "-I", "-c", DRIVER, str(PYFIGLET)],
            input=json.dumps(args).encode(), capture_output=True,
            timeout=TIMEOUT_SEC, cwd=cwd, env=env,
        )
    except subprocess.TimeoutExpired:
        return None
    if p.returncode != 0:
        return None
    return p.stdout.decode("utf-8")


def build(n, seen, cwd, pool, label):
    cases = []
    dropped = 0
    while len(cases) < n:
        batch = []
        while len(batch) < (n - len(cases)) + 64:
            args = make_args()
            key = json.dumps(args)
            if key in seen:
                continue
            seen.add(key)
            batch.append(args)
        outs = list(pool.map(lambda a: run_original(a, cwd), batch))
        for args, out in zip(batch, outs):
            if len(cases) == n:
                break
            if out is None:
                dropped += 1
                continue
            cases.append({"args": args, "out": out})
    print(f"{label}: {len(cases)} cases, {dropped} dropped (pyfiglet crashed or hung)")
    return cases


def write(path, cases):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=True) + "\n")


def main():
    fonts_dir = PYFIGLET / "pyfiglet" / "fonts"
    if not (fonts_dir / "standard.flf").is_file():
        sys.exit(f"missing {fonts_dir}: run the font setup step from the Makefile first:\n"
                 "  mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/")
    random.seed(7)
    DATA.mkdir(exist_ok=True)
    seen = set()
    with tempfile.TemporaryDirectory() as cwd, ThreadPoolExecutor(WORKERS) as pool:
        visible = build(N_CASES, seen, cwd, pool, "visible")
        hidden = build(N_CASES, seen, cwd, pool, "hidden")
    write(DATA / "visible.jsonl", visible)
    write(DATA / "hidden.jsonl", hidden)

    for label, cases in (("visible", visible), ("hidden", hidden)):
        rtl = sum(1 for c in cases if option(c["args"], "-D") == "right-to-left")
        narrow = sum(1 for c in cases if option(c["args"], "-w") in ("10", "20"))
        both = sum(1 for c in cases if option(c["args"], "-D") == "right-to-left"
                   and option(c["args"], "-w") in ("10", "20"))
        print(f"{label}: right-to-left {rtl}, width 10/20 {narrow}, both {both}")


if __name__ == "__main__":
    main()
