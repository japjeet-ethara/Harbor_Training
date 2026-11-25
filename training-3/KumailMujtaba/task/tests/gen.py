# /// script
# requires-python = "==3.12.*"
# dependencies = ["regex==2026.9.29"]
# ///
"""Generate the titlecase-go test data. Run with: uv run tests/gen.py

Writes four files to tests/data/, one title per line:

    inputs.txt         2000 generated titles
    expected.txt       titlecase() of each line in inputs.txt
    hidden_inputs.txt  2000 further titles, none shared with inputs.txt
    hidden_expected.txt

Every expected line comes from running the original Python titlecase() with
default arguments. Nothing in this file states an expected answer.

Inputs never contain \\r or \\n, so each one is a single line. That leaves the
multi-line behaviour (NOTES.md rules 1 and 19) out of this data, along with the
non-default arguments (rules 2 and 3 in part).
"""

import random
import sys
from pathlib import Path

COUNT = 2000
TASK_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = TASK_DIR / "tests" / "data"

# The task may sit beside the repo or inside it.
REPO_CANDIDATES = [TASK_DIR.parent / "python-titlecase", TASK_DIR.parent]


def load_reference():
    for repo in REPO_CANDIDATES:
        if (repo / "titlecase" / "__init__.py").is_file():
            sys.path.insert(0, str(repo))
            break
    else:
        sys.exit(f"original titlecase not found in: {REPO_CANDIDATES}")

    import titlecase as reference

    if reference.__version__ != "2.4.1":
        sys.exit(f"expected titlecase 2.4.1, found {reference.__version__}")
    # Without regex, titlecase falls back to patterns that give different output.
    if not reference.REGEX_AVAILABLE:
        sys.exit("the regex package is required; run with: uv run tests/gen.py")
    return reference.titlecase


NORMAL_WORDS = """
river mountain garden history science market winter summer journey silver
quiet stone window letter engine forest harbor bridge shadow memory machine
language kitchen painter teacher village morning evening thunder ocean planet
library doctor student mirror lantern orchard railway stranger country simple
broken golden ancient modern hidden distant gentle sudden narrow crooked
walking running reading building finding keeping learning falling writing
""".split()

# Lists, not sets: set order changes between runs and would break repeatability.
TRICKS = {
    "initials": ["D.C.", "U.S.A.", "U.S.", "A.B.C.", "J.R.R.", "P.O.", "a.m.", "e.g."],
    "apostrophe_o": ["o'reilly", "o‘neil", "O'BRIEN", "o'reilly's", "o'connor's", "O'neil"],
    "apostrophe_dl": ["d'angelo", "l'grange", "L'OREAL", "d‘arcy", "D'Artagnan", "l'amour's"],
    "apostrophe_other": ["shouldn't", "don't", "rock'n'roll", "'tis", "dogs'", "it's"],
    "mc": ["mcclelland", "McDonald", "MCDONALD", "mcgregor", "mc", "mcx", "mcd", "mc12", "mc-hammer", "Mcintosh"],
    "honorific": ["mr", "mrs", "ms", "dr", "MR", "Mrs", "mS", "dR", "mr.", "dr."],
    "hostname": ["example.com", "foo.bar.org", "EXAMPLE.COM", "node.js", "v1.2", "3.x", "www.example.co.uk"],
    "mixed_case": ["iTunes", "eBay", "macOS", "AT&T", "Q&A", "iPhone", "YouTube", "GitHub", "aBC"],
    "small_word": "a an and as at but by en for if in of on or the to v v. via vs vs.".split(),
    "small_word_caps": "A AN AND THE OF TO Vs VS. V. Via".split(),
    "slash": ["word/word", "and/or", "this/that/other", "a/b", "the/of", "/usr/bin", "either/", "AT&T/iTunes", "mcdonald/o'reilly"],
    "url": ["http://example.com/path", "https://a.b/c", "//server/share", "ftp://host", "http://localhost"],
    "hyphen": ["end-to-end", "state-of-the-art", "mother-in-law", "-leading", "trailing-", "--", "a-b-c", "x-ray", "cnn-style", "WELL-KNOWN"],
    "consonants": ["cnn", "bbc", "nth", "st", "tv", "rhythm", "html", "sql", "psst", "BBC", "cnn's"],
    "digits": ["34th", "2nd", "1st", "3d", "123", "007", "9am", "1990s", "4x4"],
    "leading_punct": ["'by", "\"the", "(a", "[of]", "“quoted”", "‘single’", "#tag", "@name", "$100", "_foo", "...and"],
    "trailing_punct": ["of?", "the!", "a,", "to.", "by;", "in:", "on...", "and?!", "river)", "at—"],
    "subphrase": ["word: a", "word. the", "word; an", "word? of", "word! to", "word - a", "word – the", "word ‒ an", "word — of", "word ― to", "word:a", "word : the"],
    "unicode_letters": [
        "élan", "ÉCOLE", "straße", "ß", "ﬁsh", "ǆungla", "İstanbul",
        "слово", "СЛОВО", "λόγος",
        "ΣΑΣ", "éBay", "中文", "naïve", "café.bar", "фоО",
    ],
}

SPACES = ["\t", " ", " ", " ", "　", "  ", "   "]


def make_title(rng, category):
    """Build one title that contains at least one token from category."""
    tokens = [rng.choice(NORMAL_WORDS) for _ in range(rng.randint(2, 7))]
    for _ in range(rng.randint(0, 2)):
        pool = TRICKS[rng.choice(list(TRICKS))]
        tokens[rng.randrange(len(tokens))] = rng.choice(pool)
    tokens.insert(rng.randint(0, len(tokens)), rng.choice(TRICKS[category]))

    # The first and last positions get their own handling (rule 17).
    position = rng.random()
    if position < 0.15:
        tokens.insert(0, rng.choice(TRICKS["small_word"]))
    elif position < 0.30:
        tokens.append(rng.choice(TRICKS["small_word"] + TRICKS["trailing_punct"]))

    title = tokens[0]
    for token in tokens[1:]:
        title += (rng.choice(SPACES) if rng.random() < 0.08 else " ") + token

    edge = rng.random()
    if edge < 0.02:
        title = " " + title
    elif edge < 0.04:
        title += " "

    style = rng.random()
    if style < 0.18:
        title = title.upper()  # rules 4 and 14 need the whole line in capitals
    elif style < 0.24:
        title = title.lower()
    return title


def make_titles(rng, seen):
    categories = list(TRICKS)
    titles = []
    while len(titles) < COUNT:
        # Rotating through the categories gives each one an equal share.
        title = make_title(rng, categories[len(titles) % len(categories)])
        if title not in seen:
            seen.add(title)
            titles.append(title)
    return titles


def write_lines(path, lines):
    # newline="\n" stops Windows from writing \r\n, which would change the data.
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(line + "\n")


def main():
    titlecase = load_reference()
    random.seed(1)
    seen = set()
    inputs = make_titles(random, seen)
    hidden_inputs = make_titles(random, seen)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for prefix, titles in (("", inputs), ("hidden_", hidden_inputs)):
        expected = [titlecase(title) for title in titles]
        for title, result in zip(titles, expected):
            if "\n" in title or "\r" in title or "\n" in result or "\r" in result:
                sys.exit(f"not a single line: {title!r} -> {result!r}")
        write_lines(DATA_DIR / f"{prefix}inputs.txt", titles)
        write_lines(DATA_DIR / f"{prefix}expected.txt", expected)
    print(f"wrote {COUNT} + {COUNT} titles to {DATA_DIR}")


if __name__ == "__main__":
    main()
