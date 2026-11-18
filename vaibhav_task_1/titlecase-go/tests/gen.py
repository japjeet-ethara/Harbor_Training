#!/usr/bin/env python3
"""Generate the titlecase-go answer sheets.

Writes, deterministically (random.seed(1)):
  tests/data/inputs.txt            2000 titles  (visible / development set)
  tests/data/hidden_inputs.txt     2000 other titles (used for grading)
  tests/data/expected.txt          original titlecase() of each visible title
  tests/data/hidden_expected.txt   original titlecase() of each hidden title

Expected answers are NEVER written by hand: they come from running the
ORIGINAL python-titlecase code (default location ../../python-titlecase
relative to this file, i.e. next to the task folder; override with --repo).

The third-party `regex` package is blocked before import, so the module always
takes its stdlib `re` fallback branch — the branch the instruction names as the
reference. This makes the answers independent of what is installed locally.

Usage:  python3 tests/gen.py [--repo PATH_TO_python-titlecase]
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
N = 2000

# ---------------------------------------------------------------- word pools
NORMAL = """
lord rings tale two cities war peace guide galaxy history world time machine
house mirth age innocence sound fury grapes wrath old man sea catcher rye
great expectations pride prejudice brave new animal farm heart darkness
little women moby dick crime punishment brothers karamazov sun also rises
farewell arms invisible bell jar road kill mockingbird gatsby ulysses
beloved hamlet macbeth othello tempest dream summer night winter king queen
prince castle river mountain forest island desert ocean city village garden
secret life art science love death hope fear light dark fire ice stone glass
iron gold silver water wind earth sky star moon planet rocket launch report
update review analysis future past present guide introduction handbook manual
lessons notes story stories journey return rise fall empire republic
apple banana cherry orange umbrella engine idea echo oyster eagle inside
yellow young yesterday year yard you your by-pass
rhythm myth gym lynx crypt hymn nymph sly fly dry try
nth brr shh tsk hmm grr pst cwm crwth
running jumped quickly slowly between among under over through without
about after before during against within upon toward towards
is was are were be been being has have had do does did will would can could
it its this that these those what which who whom whose why how when where
""".split()

SMALL = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
         "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs."]

ACCENTED = """café élan über niño ñandú façade àla crème brûlée naïve résumé
déjà vu señor jalapeño garçon smörgåsbord fjörd zoë noël ångström
München Zürich São Paulo Ébène Çava Ölmez Ñu éé ÉCOLE""".split()

APOS_BASE = ["artagnan", "neil", "oreal", "reilly", "brien", "angelo",
             "alembert", "hara", "connor", "amour", "est", "x", "a", "s",
             "ARTAGNAN", "Neil", "NEIL"]

MC_BASE = ["donald", "kenzie", "carthy", "gregor", "intosh", "queen", "lean",
           "x", "a", "DONALD", "Donald", "kinley", "mahon", "-test", "e", "1"]

INITIALS = ["U.S.A.", "U.S.", "F.B.I.", "A.B.C.D.", "U.S", "E.U.", "U.K.",
            "J.R.R.", "A.", "Z.", "U.SA", "A.B", "A.B.C", "u.s.a.", "Ph.D.",
            "a.m.", "p.m.", "i.e.", "e.g.", "etc."]

UC_ELSE = ["iPhone", "eBay", "macOS", "iOS", "QuickTime", "JavaScript",
           "PostgreSQL", "YouTube", "GitHub", "LaTeX", "aBc", "xY", "iPad",
           "McDonald", "NASA", "FBI", "IBM", "TV", "OK", "PhD", "DVDs",
           "_xYz", "(iPad)", "“iPhone”", "-iOS", "x86", "ABC123"]

URLS = ["http://example.com", "https://www.example.org/path",
        "example.com", "www.test.co.uk", "node.js", "foo.bar", "v1.2.3",
        "3.14", "ftp://files.example.net/a-b/c", "user@example.com",
        "a.b", "file.txt", "//double", "http://a/b-c"]

CONSONANT = ["xml", "html", "css", "bbc", "pdf", "ftp", "ssh", "st", "dr",
             "mr", "mrs", "ms", "Mr", "MRS", "Dr.", "mr.", "ms.", "nyc",
             "cnn", "dvd", "tv", "sql", "rss", "http", "www", "brb", "xkcd",
             "nth", "ZZZ", "Hmm", "pp", "bk", "crwth"]

NUMBERS = ["1st", "2nd", "3rd", "19th", "100", "2024", "3d", "4k", "1080p",
           "10x", "2x4", "1,000", "$5", "50%", "#1", "007"]

UNDERS = ["_private", "__init__", "snake_case", "_", "__", "a_b", "_the",
          "the_", "_a", "x_Y"]

PUNCT_PREFIX = ['"', '“', '‘', "'", '(', '[', '{', '_', '-', '—', '–', '*',
                '...', '#', '@', '~', '`', '/', '<']
PUNCT_SUFFIX = [',', '.', ':', ';', '?', '!', ')', ']', '”', '’', '"', "'",
                '...', '—', '-', '–', '?!', '.)', '"', '>', '/', '_', '}']
SEPARATORS = [" - ", " — ", " – ", " ‒ ", " ― ", ": ", "; ", "? ", "! ",
              ". ", ", ", " / ", " & ", " + "]
SPACES = [" ", " ", " ", " ", " ", " ", " ", " ", "  ", "\t", " ", "   "]


def apos_word(r):
    first = r.choice("dolDOL")
    quote = r.choice(["'", "'", "‘", "’"])
    base = r.choice(APOS_BASE)
    tail = r.choice(["", "", "", "'s", "s'", "'ss", "ss", "’s", "-x"])
    return first + quote + base + tail


def mc_word(r):
    return r.choice(["mc", "Mc", "MC", "mC", "mac", "Mac"]) + r.choice(MC_BASE) + \
        r.choice(["", "", "", "'s", "-smith", "/x"])


def compound(r, sep):
    parts = []
    for _ in range(r.randint(2, 4)):
        parts.append(r.choice([r.choice(NORMAL), r.choice(SMALL),
                               r.choice(NORMAL).upper(), r.choice(UC_ELSE),
                               r.choice(CONSONANT), "", r.choice(ACCENTED)]))
    return sep.join(parts)


def special_token(r):
    kind = r.randrange(14)
    if kind == 0:
        return apos_word(r)
    if kind == 1:
        return mc_word(r)
    if kind == 2:
        return r.choice(INITIALS)
    if kind == 3:
        return r.choice(UC_ELSE)
    if kind == 4:
        return r.choice(URLS)
    if kind == 5:
        return r.choice(CONSONANT)
    if kind == 6:
        return compound(r, "-")
    if kind == 7:
        return compound(r, "/")
    if kind == 8:
        return r.choice(NUMBERS)
    if kind == 9:
        return r.choice(UNDERS)
    if kind == 10:
        return r.choice(ACCENTED)
    if kind == 11:
        return r.choice(["and/or", "w/o", "up-to-date", "step-by-step",
                         "x-ray", "self-aware", "-leading", "trailing-",
                         "re-the", "of-the", "a-b-c", "--", "-", "/", "'",
                         "—", "...", "&", "v.", "vs.", "Vs", "VIA", "AND"])
    if kind == 12:
        return r.choice(SMALL).upper()
    return r.choice(SMALL)


def token(r):
    x = r.random()
    if x < 0.45:
        t = r.choice(NORMAL)
    elif x < 0.70:
        t = r.choice(SMALL)
    else:
        t = special_token(r)
    # random casing of plain words
    c = r.random()
    if c < 0.08:
        t = t.upper()
    elif c < 0.16:
        t = t.capitalize()
    elif c < 0.19:
        t = "".join(ch.upper() if r.random() < 0.4 else ch for ch in t)
    # punctuation wrapping
    if r.random() < 0.12:
        t = r.choice(PUNCT_PREFIX) + t
    if r.random() < 0.15:
        t = t + r.choice(PUNCT_SUFFIX)
    return t


def make_line(r):
    style = r.random()
    if style < 0.03:
        return r.choice(["", " ", "  ", "\t", "   "])
    n = r.randint(1, 10)
    out = []
    for i in range(n):
        out.append(token(r))
        if i < n - 1:
            out.append(r.choice(SEPARATORS) if r.random() < 0.12 else r.choice(SPACES))
    line = "".join(out)
    if r.random() < 0.05:
        line = r.choice([" ", "  ", "\t"]) + line
    if r.random() < 0.05:
        line = line + r.choice([" ", "  ", "\t"])
    s = r.random()
    if s < 0.15:
        line = line.upper()           # all-caps lines
    elif s < 0.22:
        line = " ".join(w.capitalize() for w in line.split(" "))
    return line


def check_line(line):
    assert "\n" not in line and "\r" not in line, repr(line)
    # keep inside the alphabet promised by the instruction
    for ch in line:
        assert ch == "\t" or ch == " " or 0x20 <= ord(ch) < 0x7f or \
            ch in "“”‘’–‒—―" or ch.isalpha(), repr((ch, line))
        assert ch not in "ßſıİµ  \x85", repr((ch, line))
    return line


def load_titlecase(repo):
    sys.modules["regex"] = None          # force the stdlib `re` fallback
    sys.path.insert(0, os.path.abspath(repo))
    import titlecase as tc
    assert tc.REGEX_AVAILABLE is False, "regex must be blocked"
    src = os.path.abspath(tc.__file__)
    assert src.startswith(os.path.abspath(repo)), src
    return tc.titlecase, src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.join(HERE, "..", "..", "python-titlecase"))
    args = ap.parse_args()
    titlecase, src = load_titlecase(args.repo)

    random.seed(1)
    r = random.Random(1)
    seen = {}
    sets = []
    for _ in range(2):
        lines = []
        while len(lines) < N:
            line = check_line(make_line(r))
            if line in seen:
                continue
            seen[line] = True
            lines.append(line)
        sets.append(lines)
    visible, hidden = sets

    os.makedirs(DATA, exist_ok=True)
    for name, lines in (("inputs", visible), ("hidden_inputs", hidden)):
        exp_name = "expected" if name == "inputs" else "hidden_expected"
        expected = []
        for line in lines:
            out = titlecase(line)
            assert "\n" not in out and "\r" not in out, repr((line, out))
            expected.append(out)
        for fname, rows in ((name, lines), (exp_name, expected)):
            with open(os.path.join(DATA, fname + ".txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write("".join(row + "\n" for row in rows))
    print(f"reference: {src}")
    print(f"wrote {len(visible)} visible and {len(hidden)} hidden titles to {DATA}")


if __name__ == "__main__":
    main()
