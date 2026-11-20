#!/usr/bin/env python3
"""Generate inputs and freeze expected answers from the ORIGINAL Python titlecase().

Run on the host:  python tests/gen.py
Never edit the expected files by hand - they must come from the original code.
"""
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("TITLECASE_REPO", HERE.parent / "environment" / "python-titlecase"))
sys.path.insert(0, str(REPO))
from titlecase import titlecase  # noqa: E402

N = 2000
DATA = HERE / "data"

NORMAL = ("lord rings quick brown fox jumps over lazy dog history science winter summer garden river "
          "mountain system design theory practice letters stories journey kingdom machine language "
          "network window forest silver golden shadow memory empire harbor tasks hardening").split()
SMALL = ("a an and as at but by en for if in of on or the to v v. via vs vs.").split()
ACRONYMS = "NASA FBI USA UK DNA HTML SQL API CPU GPU NATO".split()
MIXED = "iPhone eBay macOS JavaScript YouTube PostgreSQL McDonald DeVry LaTeX iOS".split()
APOS = ["o'brien", "d'artagnan", "l'amour", "O'Neil", "don't", "it's", "rock'n'roll", "o\u2018hara", "L'Oreal"]
INITIALS = ["J.R.R.", "U.S.A.", "J.K.", "A.B.", "T.S.", "e.g.", "i.e.", "a.m.", "p.m."]
URLS = ["http://example.com/path", "https://foo.org/a/b?x=1", "www.example.com", "user@example.com",
        "example.com/page", "ftp://files.net/x"]
HYPHEN = ["state-of-the-art", "well-known", "x-ray", "mother-in-law", "up-to-date", "e-mail",
          "self-driving", "a-b-c", "re-enter", "short-lived"]
SLASH = ["and/or", "either/or", "24/7", "a/b/c", "input/output", "http//weird", "km/h"]
MAC = ["mcdonald", "macdonald", "mcDONALD", "MCDONALD", "mcallister", "machine", "mc"]
HONOR = ["mr", "mrs", "ms", "dr", "Mr.", "mrs.", "dr.", "MS"]
PUNCT_WORDS = ["\"quoted\"", "(parenthetical)", "'single'", "[bracket]", "word,", "word;", "word:", "word?",
               "word!", "\u2014dash", "\u2013en", "...", "&", "-", "--", "#hash", "$money", "50%", "100",
               "3rd", "2nd-place", "'tis", "\u2018quoted\u2019", "a:", "the:", "of."]
SUBPHRASE = ["Title: the story", "Note. a new day", "Wait; an answer", "Really? the end", "Stop! in time",
             "Dash - a thing", "Dash \u2013 the thing", "Dash \u2014 of mice"]


def token(r):
    pools = [NORMAL] * 8 + [SMALL] * 4 + [ACRONYMS, MIXED, APOS, INITIALS, URLS, HYPHEN, SLASH, MAC, HONOR,
                                          PUNCT_WORDS]
    w = r.choice(r.choice(pools))
    case = r.random()
    if case < 0.15:
        w = w.upper()
    elif case < 0.30:
        w = w.lower()
    elif case < 0.35:
        w = w.capitalize()
    return w


def make_title(r):
    if r.random() < 0.04:
        return r.choice(SUBPHRASE)
    n = r.randint(1, 12)
    words = [token(r) for _ in range(n)]
    seps = [r.choice([" "] * 20 + ["  ", "\t"]) for _ in range(n - 1)]
    s = words[0]
    for sep, w in zip(seps, words[1:]):
        s += sep + w
    mode = r.random()
    if mode < 0.12:
        s = s.upper()
    elif mode < 0.22:
        s = s.lower()
    if r.random() < 0.05:
        s = " " + s
    if r.random() < 0.05:
        s = s + " "
    if r.random() < 0.05:
        s = r.choice(['"', "'", "(", "\u2018"]) + s
    if r.random() < 0.05:
        s = s + r.choice(['"', ")", ".", "!", "?", ":", "'"])
    return s


def build(r, count, forbidden):
    seen, out = set(forbidden), []
    while len(out) < count:
        t = make_title(r)
        if t in seen or not t.strip() or "\n" in t or "\r" in t:
            continue
        seen.add(t)
        out.append(t)
    return out


def write(name, lines):
    (DATA / name).write_text("".join(l + "\n" for l in lines), encoding="utf-8", newline="")


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    random.seed(1)
    r = random
    inputs = build(r, N, [])
    hidden = build(r, N, inputs)
    for in_name, exp_name, lines in (("inputs.txt", "expected.txt", inputs),
                                     ("hidden_inputs.txt", "hidden_expected.txt", hidden)):
        expected = [titlecase(l) for l in lines]
        bad = [i for i, e in enumerate(expected) if "\n" in e or "\r" in e]
        assert not bad, f"expected output contains a newline for input lines {bad[:5]}"
        write(in_name, lines)
        write(exp_name, expected)
        print(f"wrote {in_name} / {exp_name}: {len(lines)} lines")


if __name__ == "__main__":
    main()
