#!/usr/bin/env python3
"""Build the two title sets and freeze the right answers with the ORIGINAL library.

    python3 tests/gen.py

Writes, relative to the task folder:

    tests/data/sample/titles.txt   2000 titles anyone may look at
    tests/data/sample/answers.txt  what the original returns for them
    tests/data/graded/titles.txt   2000 other titles, used for the score
    tests/data/graded/answers.txt  what the original returns for them

The answers are never typed by hand: they come from running `titlecase()` of the
snapshot in environment/python-titlecase, with the `regex` package importable. The script
is deterministic (random.seed(1)), so running it again must leave the files unchanged.
"""

import random
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent.parent
SNAPSHOT = TASK_DIR / "environment" / "python-titlecase"
DATA = TASK_DIR / "tests" / "data"

SEED = 1
PER_SET = 2000

# ---- word material -------------------------------------------------------------------------

PLAIN = """
    lord rings night king queen river mountain summer winter story garden secret house
    letter window silver golden broken little great early final second table water fire
    morning evening shadow dream voice music silence island journey return memory promise
    forest ocean valley desert castle bridge harbour market tower village empire kingdom
    child mother father sister brother friend stranger doctor teacher soldier sailor poet
    love hope fear grief truth beauty courage freedom justice wisdom wonder danger glory
    red blue green black white yellow purple orange hidden lost found last first other
    young old quiet loud sweet bitter happy strange simple modern ancient wild gentle
    running walking falling rising dancing singing waiting learning leaving coming
    history science nature society culture language theory practice design method
    report guide notes review lesson chapter volume edition series season episode
    paris london tokyo berlin madrid delhi cairo sydney boston chicago denver austin
    monday friday sunday january april october january spring autumn century decade
""".split()

# Words with no vowel and no "y": three or more letters become an acronym, two do not.
CONSONANT_ONLY = "cnn bbc pbs nyc mph www tnt dvd hdtv cd tv st nd pm hmm brr pst nth".split()
# Look like acronyms but contain a vowel or a y, so they are not.
NOT_ACRONYM = "fbi nasa cia dna bmw gym fly sky dry myth".split()

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()

MIXED_CASE = "iTunes iPhone eBay YouTube PayPal LaTeX GitHub macOS iOS JavaScript".split()

MC_WORDS = "mcdonald McDonald MCDONALD mcfly mcthe mcgregor's mcx McDonald's mcfoo-bar".split()

TITLES_ABBR = "mr mrs ms dr Mr Mrs Ms Dr MR MRS MS DR mr. mrs. dr. mss drs".split()

APOSTROPHES = "o'neil O'Brien d'artagnan l'amour o'grange's d'Angelo l'Oréal o's' o'as' don't it's we'll".split()

DOTTED = "example.com e.g. i.e. u.s. D.C. U.S.A. A.B.C v1.2 version-2.0 www.site.org in.a".split()

DIGITS_FIRST = "3rd 42nd 1990s 100 2024 7up 1st 21st".split()

SLASHED = "tcp/ip and/or he/she input/output http://a.b yes/no/maybe on/off".split()

HYPHENATED = "end-to-end well-known x-ray to-do a-b the-the self-made twenty-one mother-in-law e-mail".split()

ACCENTED = "café señor niño arrivé naïve crème façade œuvre æsir ørsted straße über élan émile".split()

SYMBOLS = "at&t AT&T r&d c++ 100% ≤10 ¿que? ¡hola! €50 #hashtag @home 50/50 a+b".split()

WRAPPERS = [
    ("(", ")"), ("[", "]"), ('"', '"'), ("“", "”"), ("‘", "’"), ("'", "'"), ("", ","), ("", ":"),
    ("", ";"), ("", "?"), ("", "!"), ("", "."), ("", "..."), ("", "’s"), ("", "'s"),
]

SEPARATORS = [" - ", " – ", " — ", ": ", ". ", "; ", "? ", "! ", " / ", " & "]

ODD_SPACES = ["\t", " ", " ", " ", "　", "  "]

# Characters that must never appear: they would break "one line per title".
FORBIDDEN = set("\r\n\x0b\x0c\x1c\x1d\x1e\x1f\x85  ")


def pick_word(rng):
    roll = rng.random()
    if roll < 0.46:
        return rng.choice(PLAIN)
    if roll < 0.62:
        return rng.choice(SMALL)
    if roll < 0.67:
        return rng.choice(CONSONANT_ONLY)
    if roll < 0.70:
        return rng.choice(NOT_ACRONYM)
    if roll < 0.73:
        return rng.choice(MIXED_CASE)
    if roll < 0.76:
        return rng.choice(MC_WORDS)
    if roll < 0.79:
        return rng.choice(TITLES_ABBR)
    if roll < 0.82:
        return rng.choice(APOSTROPHES)
    if roll < 0.85:
        return rng.choice(DOTTED)
    if roll < 0.87:
        return rng.choice(DIGITS_FIRST)
    if roll < 0.90:
        return rng.choice(SLASHED)
    if roll < 0.94:
        return rng.choice(HYPHENATED)
    if roll < 0.97:
        return rng.choice(ACCENTED)
    return rng.choice(SYMBOLS)


def shape_word(rng, word):
    roll = rng.random()
    if roll < 0.08:
        word = word.upper()
    elif roll < 0.14:
        word = word.capitalize()
    elif roll < 0.16:
        word = word.title()
    if rng.random() < 0.18:
        left, right = rng.choice(WRAPPERS)
        word = left + word + right
    return word


def make_title(rng):
    count = rng.choice([1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9])
    words = [shape_word(rng, pick_word(rng)) for _ in range(count)]
    pieces = [words[0]]
    for word in words[1:]:
        roll = rng.random()
        if roll < 0.12:
            pieces.append(rng.choice(SEPARATORS))
        elif roll < 0.22:
            pieces.append(rng.choice(ODD_SPACES))
        else:
            pieces.append(" ")
        pieces.append(word)
    title = "".join(pieces)
    if rng.random() < 0.12:
        title = title.upper()
    if rng.random() < 0.05:
        title = rng.choice([" ", "\t", " "]) + title
    if rng.random() < 0.05:
        title = title + rng.choice([" ", "\t", " "])
    return title


def build_sets(rng):
    seen = set()
    sets = []
    for _ in range(2):
        titles = []
        while len(titles) < PER_SET:
            title = make_title(rng)
            if title in seen or FORBIDDEN & set(title):
                continue
            seen.add(title)
            titles.append(title)
        sets.append(titles)
    return sets


def load_original():
    sys.path.insert(0, str(SNAPSHOT))
    import titlecase  # noqa: E402  (the snapshot, not an installed package)

    if not titlecase.REGEX_AVAILABLE:
        sys.exit("the `regex` package is not importable; the answers must be frozen with it")
    return titlecase.titlecase


def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(line + "\n")


def main():
    original = load_original()
    rng = random.Random(SEED)
    sample, graded = build_sets(rng)
    for name, titles in (("sample", sample), ("graded", graded)):
        answers = [original(t) for t in titles]
        for t, a in zip(titles, answers):
            assert not (FORBIDDEN & set(a)), repr(t)
        write_lines(DATA / name / "titles.txt", titles)
        write_lines(DATA / name / "answers.txt", answers)
        changed = sum(1 for t, a in zip(titles, answers) if t != a)
        print(f"{name}: {len(titles)} titles, {changed} differ from their input")
    assert not set(sample) & set(graded)


if __name__ == "__main__":
    main()
