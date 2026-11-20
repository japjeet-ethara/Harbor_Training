#!/usr/bin/env python3
"""Generate test inputs and freeze expected answers for the titlecase-go task.

Writes into tests/data/:
  inputs.txt           2000 titles (visible set, for local debugging)
  expected.txt         original Python titlecase() of each line in inputs.txt
  hidden_inputs.txt    2000 different titles (used for grading)
  hidden_expected.txt  original Python titlecase() of each line in hidden_inputs.txt

Expected answers are NEVER written by hand: they come from running the original
code in ../../python-titlecase (next to this task folder).

Run:  python tests/gen.py
"""

import random
import sys
from pathlib import Path

N_VISIBLE = 2000
N_HIDDEN = 2000

TESTS_DIR = Path(__file__).resolve().parent
DATA_DIR = TESTS_DIR / "data"
REPO_DIR = TESTS_DIR.parent.parent / "python-titlecase"

# NOTE: Reward Kit imports every .py file in tests/, so this module must do
# nothing on import. All side effects live in main().


def load_original_titlecase():
    """Import the ORIGINAL titlecase(), forced onto the stdlib `re` fallback.

    The library uses the third-party `regex` module if it is installed, which
    changes behaviour. Blocking it makes the answers independent of the machine.
    """
    sys.dont_write_bytecode = True      # do not leave __pycache__ in the repo
    sys.modules["regex"] = None         # `import regex` -> ImportError -> re
    sys.path.insert(0, str(REPO_DIR))
    import titlecase as tc_module

    assert tc_module.REGEX_AVAILABLE is False, "regex module must not be used"
    assert Path(tc_module.__file__).resolve().parent.parent == REPO_DIR.resolve()
    return tc_module.titlecase


# --- Word pools -------------------------------------------------------------
NORMAL = """
adventure after against age air all american answer army art back bad battle
beautiful before best big black blood blue book boy bridge broken brother city
cold come company country dark day dead death deep desert dog dream earth end
every eye fall family father fast fear fire first flight forest forever free
friend game garden girl gold good great green heart hero high history home hope
house hunt island journey king land last legend life light little long lost love
machine man mind moon mother mountain murder music night north old other people
power queen rain red return rich river road rose run science sea secret shadow
silent sky small song soul star stone story street summer sun sword theory time
tomorrow tower tree true war water west white wild wind winter woman world young
""".split()

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()

TRICKY = {
    # rule 13: all consonants -> ACRONYM (only if 3+ letters; y is a vowel)
    "consonants": ["bbc", "cnn", "nth", "psst", "cwm", "st", "tv", "xyz", "gym",
                   "rhythm", "html", "Bbc", "mr", "nbc"],
    # rule 6: Mc / MC (recursive on the rest), Mac is not special
    "mc": ["mcdonald", "McDonald", "MCDONALD", "mcdonald-smith", "mcintosh",
           "macdonald", "mc", "mcx", "Mcgee", "mcdonald's", "mc-hammer",
           "mcdonald/burger"],
    # rule 5: d' / o' / l' prefix (also curly apostrophe and 's suffix)
    "apos": ["o'neil", "d'artagnan", "l'oreal", "o'neil's", "o‘brien",
             "D'ANGELO", "O'NEIL", "don't", "it's", "y'all", "l'", "o'"],
    # rule 7: Mr / Mrs / Ms / Dr (only first letter uppercased)
    "title": ["mr", "MR", "Mrs", "mrs", "ms", "MS", "dr", "DR", "Dr.", "mrs.",
              "dR", "mRS"],
    # rule 8: inline period
    "period": ["example.com", "e.g.", "i.e.", "u.s.", "U.S.", "www.foo.org",
               "U.S.A.", "a.b", "v1.2", "node.js", "Ph.D."],
    # rule 4: uppercase initials (only kept in all-caps lines)
    "initials": ["U.S.", "A.B.", "J.R.R.", "X.", "U.S.A"],
    # rule 9: uppercase elsewhere (kept as written in mixed-case lines)
    "mixed": ["iPhone", "eBay", "NASA", "McKinsey", "YouTube", "iOS", "FBI",
              "macOS", "LaTeX", "PhD", "iPhone-case", "OK"],
    # rule 12: hyphens
    "hyphen": ["step-by-step", "x-ray", "a-ha", "well-known", "self-made",
               "-", "--", "pre-war", "the-end", "up-to-date", "Jean-Luc",
               "end-"],
    # rule 11: slashes (// disables the split)
    "slash": ["and/or", "this/that", "AND/OR", "w/o", "24/7", "http://foo",
              "http://example.com", "a/b/c", "/", "either/or", "of/the"],
    # rule 14: leading/trailing punctuation
    "punct": ['"hello"', "(world)", "'the'", "“quote”", "‘single’", "[bracket]",
              "...", "?!", "#tag", "@user", "the,", "of.", "in?!", "a:",
              "*star*", "_under_", "—dash", "(a)", "“the”"],
    # numbers and digits
    "number": ["2001", "3rd", "1.5", "100%", "x2", "007", "1st", "2nd-hand"],
    # non-ASCII letters (all in Unicode for many years)
    "unicode": ["élan", "über", "ÉCOLE", "straße", "GROß", "ñandú", "øresund",
                "Ærø", "çà", "éé", "ÉLAN", "þorn", "ıstanbul", "İSTANBUL"],
}
TRICKY_KINDS = list(TRICKY)

# Separators between words: mostly a single space, sometimes other whitespace
# (tab, double space, NBSP) or a sub-phrase separator (rule 17).
SEPARATORS = [" "] * 30 + ["  ", "\t", " "] + [
    ": ", ". ", "; ", "? ", "! ", " - ", " – ", " — ", " ‒ ", " ― ", ", ",
]

# Characters that must never appear inside a title (they break "one per line").
FORBIDDEN = set("\r\n\v\f\x1c\x1d\x1e\x85  ")


def random_case(word):
    r = random.random()
    if r < 0.70:
        return word                      # as written in the pool (mostly lower)
    if r < 0.80:
        return word.upper()
    if r < 0.90:
        return word.capitalize()
    return "".join(c.upper() if random.random() < 0.5 else c for c in word)


def random_word():
    r = random.random()
    if r < 0.45:
        return random_case(random.choice(NORMAL))
    if r < 0.65:
        return random_case(random.choice(SMALL))
    return random.choice(TRICKY[random.choice(TRICKY_KINDS)])


def random_title():
    n = random.randint(1, 9)
    parts = [random_word()]
    for _ in range(n - 1):
        parts.append(random.choice(SEPARATORS))
        parts.append(random_word())
    title = "".join(parts)

    r = random.random()
    if r < 0.12:
        title = title.upper()            # all-caps line (rules 3 and 4)
    elif r < 0.17:
        title = title.title()            # Already Title Cased Input

    r = random.random()
    if r < 0.04:
        title = " " + title              # leading whitespace
    elif r < 0.08:
        title = title + " "              # trailing whitespace (gold case)
    return title


def make_titles(count, exclude, titlecase):
    """Unique titles that the original titlecase() actually CHANGES.

    A title that is already correct would let a program that just echoes its
    input score points without porting anything, so those are skipped.
    """
    titles, seen = [], set(exclude)
    while len(titles) < count:
        t = random_title()
        if not t or t in seen or FORBIDDEN & set(t):
            continue
        if titlecase(t) == t:
            continue
        seen.add(t)
        titles.append(t)
    return titles


def write_lines(path, lines):
    for line in lines:
        assert "\n" not in line and "\r" not in line, repr(line)
    # newline="" stops Windows from turning "\n" into "\r\n"
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("".join(line + "\n" for line in lines))


def main():
    titlecase = load_original_titlecase()
    random.seed(1)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    visible = make_titles(N_VISIBLE, exclude=(), titlecase=titlecase)
    hidden = make_titles(N_HIDDEN, exclude=visible, titlecase=titlecase)
    assert not set(visible) & set(hidden)

    for name, inputs in (("", visible), ("hidden_", hidden)):
        expected = [titlecase(line) for line in inputs]
        write_lines(DATA_DIR / f"{name}inputs.txt", inputs)
        write_lines(DATA_DIR / f"{name}expected.txt", expected)
        print(f"wrote {len(inputs)} lines -> {name}inputs.txt / {name}expected.txt")


if __name__ == "__main__":
    main()
