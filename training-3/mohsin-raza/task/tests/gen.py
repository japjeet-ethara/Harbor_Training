#!/usr/bin/env python3
"""Generate the visible and hidden test sets for the titlecase-go task.

Deterministic (random.seed(1)). Writes, next to this file:
  data/inputs.txt           2000 visible inputs
  data/expected.txt         answers for inputs.txt
  data/hidden_inputs.txt    2000 different inputs
  data/hidden_expected.txt  answers for hidden_inputs.txt

Expected answers are NEVER written by hand: every line is produced by running the
ORIGINAL python-titlecase `titlecase()` on the matching input line.

Reference setup (pinned): python-titlecase 2.4.1, commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167,
run WITHOUT the optional `regex` package (the library then falls back to the stdlib `re`).
This script blocks `regex` on purpose so the answers do not depend on what is installed.

Usage:  python tests/gen.py [path/to/python-titlecase]
"""
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = 2000

# --------------------------------------------------------------------------- word pools
NORMAL = """lord rings quick brown fox jumps over lazy dog journey end world war peace time machine
secret garden night day story tale city cities river mountain ocean forest silent loud green
red blue little big last first return king queen shadow light dark fire ice song music dance
love hate life death dream reality science fiction history future past present mystery book
letter window door house home road bridge island desert storm rain snow summer winter spring
autumn morning evening moon sun star planet space ship captain pirate treasure map compass
engine bicycle garden kitchen recipe soup bread cheese wine coffee tea chocolate language
learning programming computer network database server client protocol library framework
introduction guide handbook manual notes review analysis report summary chapter volume
beginning middle conclusion adventure hunter gatherer builder walker runner swimmer
understanding becoming remembering forgetting everything nothing something anyone someone
another together alone forever never always sometimes often rarely quickly slowly carefully
beautiful terrible wonderful strange familiar ancient modern electric digital analog
rhythm gym myth crypt lynx sky fly try why dry""".split()

SMALL = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or",
         "the", "to", "v", "v.", "via", "vs", "vs."]

ACRONYMS = ["NASA", "FBI", "CIA", "HTML", "CSS", "SQL", "USA", "UK", "EU", "UN", "NATO", "DNA",
            "RNA", "GPS", "PDF", "API", "CPU", "GPU", "RAM", "USB", "LED", "NBA", "BBC", "IBM",
            "AI", "ML", "OK", "TV", "DJ", "MC", "PhD", "CEO", "FAQ", "ASAP", "UFO"]

CONSONANTS = ["nth", "tsk", "psst", "brr", "html", "css", "sql", "cpp", "xml", "pdf", "hmm",
              "shh", "grrr", "wtf", "btw", "fyi", "pbs", "tv", "st", "dr", "mr", "ms", "nyc",
              "rv", "bbq", "lgbt", "cd", "dvd", "mph", "kph", "Html", "Css", "HTML5", "css3"]

CAMEL = ["iPhone", "iPad", "eBay", "macOS", "iOS", "PlayStation", "YouTube", "JavaScript",
         "TypeScript", "PostgreSQL", "GitHub", "LinkedIn", "WordPress", "OpenAI", "eBook",
         "mRNA", "pH", "iTunes", "xBox", "bLoCk", "aB", "Ab", "aBC", "_aB", "(iPod)", "\"eBay\""]

MAC = ["mcdonald", "McDonald", "MCDONALD", "mcgregor", "McGregor", "mcafee", "mcAfee", "mcd",
       "mc", "Mc", "MC", "mcx", "mc-donald", "mc'donald", "macdonald", "mcdonald's", "mc_x",
       "mcquire", "McKinley", "mcintosh", "mc.donald", "mcmc", "McMc", "mc1234", "mcéric"]

APOS = ["o'neil", "O'Neil", "O'NEIL", "d'artagnan", "D'Artagnan", "l'amour", "L'AMOUR", "o'clock",
        "don't", "can't", "it's", "rock'n'roll", "o'brien's", "o'brien'", "l'ss", "d'ss",
        "l\u2018\u00e9t\u00e9", "d\u2018accord", "o\u2018hara", "d'", "o'", "d'a", "l's", "o'ss's",
        "d'ab'", "i'm", "we're", "'tis", "'80s", "d'arcy-smith", "o'neil/o'brien"]

TITLES = ["mr", "mrs", "ms", "dr", "MR", "MRS", "MS", "DR", "Mr", "Mrs", "Ms", "Dr", "dR", "mS",
          "mr.", "mrs.", "ms.", "dr.", "Dr.", "mr,", "(dr)", "mrss", "drs", "m", "mrr"]

INLINE = ["e.g.", "i.e.", "U.S.A.", "U.S.", "node.js", "www.example.com", "a.m.", "p.m.",
          "3.14", "v1.2", "foo.bar", "J.R.R.", "A.B.", "A.", "A.B", "a.b", "x.Y", "Ph.D.",
          "example.com/path", "end.of", "1.5x", "...", "a..b", "a.", ".a", ".NET", "S.H.I.E.L.D."]

SLASH = ["and/or", "TCP/IP", "either/or", "w/o", "a/b/c", "a//b", "/usr/bin", "dir/", "http://example.com/page",
         "https://github.com/ppannuto/python-titlecase", "ftp://x.y/z", "the/end", "of/the", "his/her",
         "24/7", "input/output", "yes/no/maybe", "/", "//", "a/", "/a", "AC/DC", "N/A", "b/w"]

HYPHEN = ["well-known", "state-of-the-art", "the-end", "self-", "-ish", "a-b", "e-mail", "x-ray",
          "SPIDER-MAN", "re-enter", "long-term", "mother-in-law", "up-to-date", "-", "--", "a-", "-a",
          "of-the", "low-level/high-level", "t-shirt", "rock-n-roll", "NASA-funded", "iPhone-like",
          "mc-donald", "o'neil-smith", "v-neck", "pre-1990", "A-Z", "a-to-z", "and-or"]

PUNCTW = ["(the)", "\"a\"", "'tis", "\u201cquoted\u201d", "\u2018single\u2019", "[of]", "end.", "wait!",
          "really?", "so,", "a:", "(a)", "-", "\u2014", "\u2013", "&", "$100", "#hashtag", "@user",
          "50%", "(v.)", "(vs.)", "\"of\"", "(in)", "to:", "of;", "the?", "a!", "an.", "(an)",
          "_the_", "*as*", "{if}", "<b>", "a_b", "x_Y", "tab\tbed", "!!!", "?!", "\u2018the\u2019", "\u201ca\u201d"]

UNICODE = ["caf\u00e9", "\u00fcber", "ni\u00f1o", "\u00c9clair", "\u00c9COLE", "na\u00efve", "se\u00f1or",
           "\u00e7ok", "\u00c5ngstr\u00f6m", "\u0153uvre", "\u00e0 la carte", "d\u00e9j\u00e0", "r\u00e9sum\u00e9",
           "\u00fcber-cool", "\u00e9t\u00e9", "\u00f1", "\u00e9", "\u00e9\u00e9\u00e9", "\u00c9T\u00c9"]

SUB_OPENERS = [":", ";", ".", "?", "!", "-", "\u2013", "\u2012", "\u2014", "\u2015"]

SEPARATORS = [" "] * 40 + ["  ", "\t", "\u00a0", " \t "]


def case_variant(rng, w):
    k = rng.random()
    if k < 0.45:
        return w
    if k < 0.65:
        return w.upper()
    if k < 0.80:
        return w.capitalize()
    if k < 0.90:
        return w.lower()
    return "".join(c.upper() if rng.random() < 0.5 else c.lower() for c in w)


def pick_word(rng):
    k = rng.random()
    if k < 0.38:
        return rng.choice(NORMAL)
    if k < 0.56:
        return case_variant(rng, rng.choice(SMALL))
    if k < 0.62:
        return rng.choice(ACRONYMS)
    if k < 0.66:
        return case_variant(rng, rng.choice(CONSONANTS))
    if k < 0.70:
        return rng.choice(CAMEL)
    if k < 0.74:
        return case_variant(rng, rng.choice(MAC))
    if k < 0.78:
        return case_variant(rng, rng.choice(APOS)) if rng.random() < 0.5 else rng.choice(APOS)
    if k < 0.82:
        return rng.choice(TITLES)
    if k < 0.86:
        return rng.choice(INLINE)
    if k < 0.90:
        return rng.choice(SLASH)
    if k < 0.94:
        return rng.choice(HYPHEN)
    if k < 0.97:
        return rng.choice(PUNCTW)
    return rng.choice(UNICODE)


def make_title(rng):
    r = rng.random()
    if r < 0.01:
        return rng.choice(["", " ", "  ", "\t", "\u00a0"])
    n = rng.choice([1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 10])
    words = []
    for _ in range(n):
        w = pick_word(rng)
        if rng.random() < 0.10:                      # word followed by a sub-phrase opener
            words.append(w + rng.choice(SUB_OPENERS))
            words.append(case_variant(rng, rng.choice(SMALL)) if rng.random() < 0.8 else rng.choice(NORMAL))
        else:
            words.append(w)
    out = words[0]
    for w in words[1:]:
        out += rng.choice(SEPARATORS) + w
    if rng.random() < 0.03:
        out = " " + out
    if rng.random() < 0.03:
        out = out + " "
    m = rng.random()
    if m < 0.15:
        out = out.upper()
    elif m < 0.22:
        out = out.lower()
    elif m < 0.26:
        out = out.title()
    return out


def clean(line):
    # one title per line: never allow line breaks in an input
    for bad in ("\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
        assert bad not in line, repr(line)
    return line


def find_repo():
    candidates = []
    if len(sys.argv) > 1:
        candidates.append(Path(sys.argv[1]))
    if os.environ.get("TITLECASE_REPO"):
        candidates.append(Path(os.environ["TITLECASE_REPO"]))
    candidates += [HERE.parents[1] / "python-titlecase",          # sibling of the task folder
                   HERE.parent / "environment" / "python-titlecase"]
    for c in candidates:
        if (c / "titlecase" / "__init__.py").is_file():
            return c
    sys.exit("cannot find python-titlecase; pass its path as the first argument")


def load_original(repo):
    # Block the optional `regex` package so the reference is the stdlib-`re` code path.
    sys.modules["regex"] = None
    sys.path.insert(0, str(repo))
    import titlecase
    assert titlecase.REGEX_AVAILABLE is False, "reference must run without the regex package"
    assert titlecase.__version__ == "2.4.1", titlecase.__version__
    return titlecase.titlecase


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(line + "\n")


def main():
    random.seed(1)
    rng = random.Random(1)
    titlecase = load_original(find_repo())

    seen, sets = set(), []
    for _ in range(2):
        lines = []
        while len(lines) < N:
            t = clean(make_title(rng))
            if t in seen:
                continue
            seen.add(t)
            lines.append(t)
        sets.append(lines)

    data = HERE / "data"
    data.mkdir(exist_ok=True)
    for (inp, exp), lines in zip((("inputs.txt", "expected.txt"), ("hidden_inputs.txt", "hidden_expected.txt")), sets):
        answers = [titlecase(line) for line in lines]          # the ORIGINAL code is the truth
        for a in answers:
            assert "\n" not in a and "\r" not in a
        write_lines(data / inp, lines)
        write_lines(data / exp, answers)
        print(f"wrote {inp} / {exp}: {len(lines)} lines")


if __name__ == "__main__":
    main()
