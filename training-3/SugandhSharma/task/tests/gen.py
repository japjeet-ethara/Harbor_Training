"""Makes the visible and the hidden title lists and freezes the answers of the ORIGINAL Python titlecase().

Run from the task folder:   python tests/gen.py
It needs the original project in the folder next to the task folder:   ../python-titlecase

Rules this script keeps:
- Every answer comes from running the original code. Nobody types an answer.
- The same run always writes the same four files (fixed seed).
- Everything is inside main(), behind the __main__ guard, because Reward Kit imports every .py file
  in /tests while grading. Without the guard, grading would try to regenerate the data and crash.
- The optional "regex" package is switched off, so the answers do not depend on the machine.
- Files are written as UTF-8 with "\n" line ends, also on Windows.
"""
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent.parent / "python-titlecase"
DATA = HERE / "data"
N = 2000

# Characters a title may contain: printable ASCII, tab, four curly quotes and four dashes.
ALLOWED = set(map(chr, range(32, 127))) | set("\t\u2018\u2019\u201c\u201d\u2012\u2013\u2014\u2015")

# The 34 characters of the original's PUNCT list, and six characters that look like punctuation but are
# NOT in that list. main() checks both lists against the original.
PUNCT = list("!\"\u201c#$%&'\u2018()*+,-\u2013\u2012\u2014\u2015./:;?@[\\]_`{|}~")
NOT_PUNCT = list("<=>^\u2019\u201d")

PLAIN = """time year people way day man thing woman life child world school state family student group country
problem hand part place case week company system program question work government number night point home water
room mother area money story fact month lot right study book eye job word business issue side kind head house
service friend father power hour game line end member law car city community name president team minute idea
kid body information back parent face others level office door health person art war history party result change
morning reason research girl guy moment air teacher force education river mountain garden silver shadow winter
summer letter secret kingdom return empire dragon forest island ocean bridge castle journey legend machine
theory guide introduction history practical modern complete short brief new old great little last first lost""".split()

SMALL = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to",
         "v", "v.", "via", "vs", "vs."]
SMALL_NO_DOT = [w for w in SMALL if "." not in w]

# Words that take a special path in the original code (the surprises of NOTES.md).
TRICKY = [
    "iPhone", "eBay", "macOS", "McDonald", "mcdonald", "MCDONALD", "mcgregor", "mcDonald", "Mcx", "MCx", "mcd", "mc",
    "mcdonald's", "macdonald", "mcthe", "mcand", "mcof", "MCIN", "mcvs.",
    "o'brien", "O'BRIEN", "d'artagnan", "l'amour", "o'clock", "d'oh", "D'OH", "l'x", "o'", "it's", "don't",
    "rock'n'roll", "o'brien's", "\u2018tis", "o\u2018neil",
    "mr", "mrs", "ms", "dr", "Mr", "MRS", "DR", "mr.", "dr.", "ph.d.",
    "J.R.R.", "U.S.A.", "u.s.a.", "e.g.", "i.e.", "A.B", "a.b", "v2.0", "3.5", "example.com",
    "www.example.com/the-page",
    "NASA", "nasa", "FBI", "tv", "TV", "hmm", "nth", "nth,", "St", "st", "xyz", "XYZ", "by", "rhythm", "PhD", "DNA",
    "ABc", "wOrld", "anVil", "i", "ii", "I",
    "state-of-the-art", "follow-up", "x-ray", "x-RAY", "mother-in-law", "e-mail", "t-shirt", "up-to-date",
    "in-and-out", "-", "--", "-the",
    "and/or", "either/or", "in/out", "x/y/z", "km/h", "a/b", "http://example.com/a-b", "//host/path", "c:/users",
    "x/iPhone-case", "a/mcx-y", "and/NASA-style", "km/eBay-like",
    "user@example.com", "at&t", "AT&T", "q&a", "R&D", "2nd", "3-d", "1984", "42", "__init__", "snake_case",
    "'the", "\"a", "\"the\"", "(of", "(of)", "[in]", "the)", "<the>", "=a=", "end.", "what?", "a?", "a?!",
    "wow!", "wait...", "one,", "two;", "so:", "&", "q&a?!", "b&to..", "x@in!)", "y+the;;",
    "\u2018quoted\u2019", "\u201cdouble\u201d", "\u2018the", "\u201ca", "\u2014", "\u2013", "dash\u2014joined",
    "en\u2013dash", "fig\u2012dash", "bar\u2015the",
]

LINKS = [": ", " - ", "; ", ". ", "? ", "! ", " \u2014 ", " \u2013 ", " \u2012 ", " \u2015 ",
         ": the ", ". a ", "? in ", "- to ", "; and ", "! or ", "\u2014 of ", "\u2013 by ", "\u2012 an ", "\u2015 if ",
         ":\tthe ", ".\ta "]


def one_word(rng):
    r = rng.random()
    if r < 0.55:
        return rng.choice(PLAIN)
    if r < 0.80:
        return rng.choice(SMALL)
    return rng.choice(TRICKY)


def one_title(rng):
    words = [one_word(rng) for _ in range(rng.randint(1, 9))]
    if rng.random() < 0.35:                       # a small word first or last
        words[rng.choice([0, -1])] = rng.choice(SMALL)
    title = " ".join(words)
    if rng.random() < 0.25:                       # two parts with a sub-phrase mark between them
        title = title + rng.choice(LINKS) + " ".join(one_word(rng) for _ in range(rng.randint(1, 4)))
    style = rng.random()
    if style < 0.20:
        title = title.upper()                     # an all-capitals line takes another path in the code
    elif style < 0.30:
        title = title.title()
    elif style < 0.36:
        title = "".join(c.upper() if rng.random() < 0.3 else c for c in title)
    if rng.random() < 0.05:
        title = title.replace(" ", "  ", 1)       # a double space
    if rng.random() < 0.03:
        title = title.replace(" ", "\t", 1)       # a tab
    if rng.random() < 0.04:
        title = " " + title                       # a leading space
    if rng.random() < 0.04:
        title = title + " "                       # a trailing space
    return title


def coverage_titles(rng):
    """Titles built on purpose: every character of PUNCT and NOT_PUNCT decides the answer of several lines.

    Without them, a port with one character missing from (or added to) its punctuation list passes every line.
    """
    def plain(lo, hi):
        return [rng.choice(PLAIN) for _ in range(rng.randint(lo, hi))]

    titles = []
    for c in PUNCT + NOT_PUNCT:
        for _ in range(2):
            # last word: a small word after "&", followed by the character
            last = rng.choice(PLAIN)[0] + "&" + rng.choice(SMALL_NO_DOT) + c
            titles.append(" ".join(plain(1, 3) + [last]))
            # a word in the middle that starts with the character
            titles.append(" ".join(plain(1, 2) + [c + rng.choice(PLAIN)] + plain(1, 2)))
        # first word: the character, then a small word
        titles.append(" ".join([c + rng.choice(SMALL_NO_DOT)] + plain(1, 3)))
        # a small last word followed by two characters: the original allows only one
        last = rng.choice(PLAIN)[0] + "&" + rng.choice(SMALL_NO_DOT) + c + rng.choice(PUNCT)
        titles.append(" ".join(plain(1, 3) + [last]))
    return titles


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(line + "\n")


def main():
    sys.dont_write_bytecode = True                # no __pycache__ folder inside the original project
    sys.modules["regex"] = None                   # always the standard-library code path of the original
    sys.path.insert(0, str(ORIGINAL))
    import titlecase as original
    assert original.REGEX_AVAILABLE is False, "the regex package must stay switched off"

    in_punct = re.compile("[%s]" % original.PUNCT)
    assert all(in_punct.fullmatch(c) for c in PUNCT), "PUNCT here differs from the original"
    assert not any(in_punct.fullmatch(c) for c in NOT_PUNCT), "NOT_PUNCT here differs from the original"
    assert {c for c in ALLOWED if in_punct.fullmatch(c)} == set(PUNCT), "PUNCT here is not complete"
    assert set(PUNCT + NOT_PUNCT) <= ALLOWED

    random.seed(1)
    rng = random.Random(1)
    seen = set()

    def take(title, into):
        # Drop titles the original leaves unchanged (fixed points of titlecase). The graded set then holds
        # only titles that need real work, so a program that just echoes its input scores 0 and cannot ride
        # the free build point over the 0.2 cheat bar.
        if (title and set(title) <= ALLOWED and title not in seen
                and original.titlecase(title) != title):
            seen.add(title)
            into.append(title)

    lists = []
    for _ in range(2):                            # first the visible list, then the hidden list
        titles = []
        for title in coverage_titles(rng):
            take(title, titles)
        while len(titles) < N:
            take(one_title(rng), titles)
        rng.shuffle(titles)
        lists.append(titles)
    visible, hidden = lists
    assert len(visible) == N and len(hidden) == N
    assert not set(visible) & set(hidden), "the two lists must not share a title"

    DATA.mkdir(exist_ok=True)
    for name, lines in (("inputs", visible), ("hidden_inputs", hidden)):
        answers = [original.titlecase(line) for line in lines]
        assert all("\n" not in a and "\r" not in a for a in answers), "an answer contains a line break"
        write_lines(DATA / f"{name}.txt", lines)
        write_lines(DATA / f"{name.replace('inputs', 'expected')}.txt", answers)
    print("wrote", 2 * N, "titles and their answers to", DATA)


if __name__ == "__main__":
    main()
