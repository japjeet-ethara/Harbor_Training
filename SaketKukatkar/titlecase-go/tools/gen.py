#!/usr/bin/env python3
"""Generate the frozen test data for the titlecase-go task.

Deterministic (random.seed(1)). Writes, under tests/data/:
  inputs.txt / expected.txt                  - 2000 visible titles + answers
  hidden_inputs.txt / hidden_expected.txt    - a different 2000 titles + answers

Every expected line is produced by running the ORIGINAL Python titlecase()
(python-titlecase 2.4.1, `regex` package installed). Nobody edits expected
files by hand.

Usage:  python tools/gen.py [--repo PATH_TO_python-titlecase] [--out DIR]
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)


def find_repo(cli):
    cands = [cli, os.environ.get("TITLECASE_REPO"),
             os.path.join(TASK, "..", "python-titlecase"),
             os.path.join(TASK, "environment", "python-titlecase")]
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "titlecase", "__init__.py")):
            return os.path.abspath(c)
    sys.exit("python-titlecase repo not found; pass --repo")


NORMAL = """the lord of the rings a tale of two cities war and peace pride and prejudice
quick brown fox jumps over lazy dog learning to code in the modern world guide
introduction history future science nature river mountain ocean garden kitchen
building better software for everyone rise fall empire secret life hidden world
how to cook dinner with friends on a budget travel notes from the road
what happens when machines think about the end of work beginning middle
silent night bright morning winter summer autumn spring story journey
complete handbook essays letters poems stories songs dreams memory memories
nobody knows why things happen as they do between east and west north south
about above after again against all almost along already also although always
among another any anyone around because before behind below beside between beyond
during each either enough every except inside instead into like near neither
nor off once only onto other outside over past since some than that their them
then there these they this those through throughout till under until upon
what when where whether which while who whom whose with within without
being doing going making taking having ever never maybe perhaps today tomorrow
a an and as at but by en for if in of on or the to v via vs
A An And As At But By En For If In Of On Or The To V Via Vs
A AN AND AS AT BUT BY EN FOR IF IN OF ON OR THE TO V VIA VS""".split()

TRICKY = ["v.", "vs.", "vs", "v", "V.", "Vs.", "VS.", "Mc", "mcdonald", "McDonald", "MCDONALD",
          "mcd", "mc", "Mcx", "mcx", "MCX", "mC", "macdonald", "MacDonald", "o'neil", "O'NEIL",
          "d'artagnan", "D'ARTAGNAN", "l'amour", "L'AMOUR", "d'a's", "o'er", "O\u2019Brien",
          "d\u2018or", "l'", "d'a", "iPhone", "eBay", "NASA", "NATO", "iOS", "tv", "sch", "rhythm",
          "nth", "xyz", "St", "st", "Mr", "mrs", "MS", "Dr", "dr.", "DR.", "MRS", "A.B.C.", "U.S.A.",
          "J.R.R.", "a.b", "A.B", "e.g.", "i.e.", "example.com", "www.site.org/path",
          "http://a-b.com/x-y", "https://x.y//z", "1.5", "3dogs", "x2", "2nd", "---", "-", "/", "//",
          "a/b", "and/or", "and/or/the", "a-b", "well-known", "state-of-the-art", "x-ray", "the-",
          "-the", "a--b", "to-do", "of-the", "a-to", "to-a", "(the)", "(a)", "(and", "\"quoted\"",
          "'single'", "\u201ccurly\u201d", "\u2018curly\u2019", "_under_", "[bracket]", "{brace}",
          "word:", "word;", "end?", "wow!", "dash\u2014dash", "en\u2013dash", "ok.", "e-mail",
          "re-enter", "pre/post", "\u00e4-\u00f6", "\u00e9lan", "\u00fcber", "\u00f1and\u00fa",
          "\u00f8re", "\u00c5NGSTR\u00d6M", "na\u00efve", "caf\u00e9", "\u0422\u0415\u0421\u0422",
          "\u043f\u0440\u0438\u0432\u0435\u0442", "\u043c\u0438\u0440", "\u0141\u00f3d\u017a",
          "x:", "to:", "a.", "the.", "of;", "in?", "an!", "\u2014", "\u2013", "A.I.", "a.i.", "U.S.",
          "PhD", "McDONALD", "ALLCAPS", "camelCase", "CamelCase", "iPad-pro", "NASA-rocket",
          "b/w", "c/o", "n/a", "N/A", "24/7", "1-2", "a1", "1a", "it's", "IT'S", "don't",
          "rock'n'roll", "o'clock", "'tis", "\u2019tis", "(mr.", "mr.)", "dr.-ing", "a.m.", "p.m."]

END_PUNCT = [":", ";", "?", "!", ".", ",", " -", " \u2013", " \u2014", ""]
SEPS = [" "] * 40 + ["  ", "\t", "\u00a0", " : ", " - "]


def style(word, rng, mode):
    if mode == "upper":
        return word.upper()
    if mode == "lower":
        return word.lower()
    r = rng.random()
    if r < 0.55:
        return word
    if r < 0.75:
        return word.lower()
    if r < 0.85:
        return word.upper()
    return word.capitalize()


def make_line(rng):
    if rng.random() < 0.12:
        line = rare_line(rng)
        if line.strip() and "\n" not in line and "\r" not in line:
            return line
    mode = rng.choices(["normal", "upper", "lower"], weights=[70, 14, 16])[0]
    n = rng.randint(1, 12)
    toks = []
    for _ in range(n):
        if rng.random() < 0.28:
            w = rng.choice(TRICKY)
        else:
            w = rng.choice(NORMAL)
        if rng.random() < 0.12:
            w = w + rng.choice(END_PUNCT).strip(" ")
        w = style(w, rng, mode)
        toks.append(w)
    out = toks[0]
    for t in toks[1:]:
        out += rng.choice(SEPS) + t
    r = rng.random()
    if r < 0.03:
        out = " " + out
    elif r < 0.06:
        out = out + " "
    elif r < 0.07:
        out = " " + out + "  "
    if not out.strip() or "\n" in out or "\r" in out:
        return make_line(rng)
    return out



SMALL_ONLY = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or",
              "the", "to", "v", "v.", "via", "vs", "vs."]
UPPER_WORDS = ["TOLKIEN", "LEWIS", "THE", "BOOK", "OF", "KINGS", "NASA", "FBI", "NEW", "YORK", "AND", "WAR"]


def rare_line(rng):
    """Targeted templates for rare paths (kept deterministic through rng)."""
    n = lambda: rng.choice(NORMAL)
    w = lambda: rng.choice(["site", "page", "host", "path", "docs", "files", "my", "blog", "data", "api"])
    s = lambda: rng.choice(SMALL_ONLY)
    up = lambda: rng.choice(UPPER_WORDS)
    p = lambda: rng.choice([":", ";", ".", "?", "!"])
    dsh = lambda: rng.choice(["-", "\u2013", "\u2014", "\u2012", "\u2015"])
    dotted = lambda: rng.choice(["v.", "vs.", "V.", "Vs."])
    small_start = lambda: rng.choice(["a", "an", "and", "as", "at", "but", "by", "for", "if", "in", "of", "on", "or", "the", "to", "via", "e", "i"])
    templates = [
        lambda: f"{n()}{p()} {dotted()} {small_start()} {n()}",
        lambda: f"{n()}{p()} {dotted()} {small_start()}. {small_start()} {n()}",
        lambda: f"{n()} {dsh()} {dotted()} {small_start()} {n()} {n()}",
        lambda: f"{n()}{p()} {s()}{p()} {s()} {n()}",
        lambda: f"{n()} {dotted()} {n()} {dotted()} {small_start()}",
        lambda: f"{n()} http://{w()}-{w()}/{w()}",
        lambda: f"ftp://{w()}/{w()}-{w()} {n()}",
        lambda: f"{n()} {w()}//{w()} {n()}",
        lambda: f"{w()}//{w()}-{w()}/{w()}",
        lambda: f"{n()} {w()}/{w()}/{w()} {n()}",
        lambda: f"J.R.R. {up()} AND C.S. {up()}",
        lambda: f"{up()} A.B. C.D.E. {up()}",
        lambda: f"{up()} U.S.A. {up()} J.",
        lambda: f"A.B.C. {up()} {up()} A.B",
        lambda: f"{n()} {s()} ",
        lambda: f" {s()} {n()}",
        lambda: f"  {n()} {s()}  ",
        lambda: f"{n()}. {small_start()} {n()}",
        lambda: f"{n()}.  {small_start()} {n()}",
        lambda: f"{n()}:\t{small_start()} {n()}",
        lambda: f"{n()} {s()}{p()}",
        lambda: f"({s()}) {n()} [{s()}]",
        lambda: f"\"{s()}\" {n()} '{s()}'",
        lambda: f"{n()} mc{w()} Mc{w()} MC{w().upper()} mC{w()}",
        lambda: f"o'{w()} d'{w()} l'{w()} O'{w().upper()} D\u2018{w()} d'a's L'AS'S",
    ]
    return rng.choice(templates)()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    ap.add_argument("--out", default=os.path.join(TASK, "tests", "data"))
    args = ap.parse_args()

    repo = find_repo(args.repo)
    sys.path.insert(0, repo)
    from titlecase import titlecase, REGEX_AVAILABLE
    if not REGEX_AVAILABLE:
        sys.exit("The `regex` package must be installed (pip install regex): the reference path is the Unicode-aware one")

    rng = random.Random(1)
    random.seed(1)  # as required; all draws below go through rng (seeded the same way)

    seen = set()

    def batch(n):
        lines = []
        while len(lines) < n:
            line = make_line(rng)
            if line in seen:
                continue
            seen.add(line)
            lines.append(line)
        return lines

    visible = batch(2000)
    hidden = batch(2000)

    os.makedirs(args.out, exist_ok=True)

    def write(name, lines):
        with open(os.path.join(args.out, name), "w", encoding="utf-8", newline="\n") as f:
            for l in lines:
                f.write(l + "\n")

    write("inputs.txt", visible)
    write("expected.txt", [titlecase(l) for l in visible])
    write("hidden_inputs.txt", hidden)
    write("hidden_expected.txt", [titlecase(l) for l in hidden])
    print("wrote 4 files to", args.out)


if __name__ == "__main__":
    main()
