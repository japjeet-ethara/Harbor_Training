#!/usr/bin/env python3
"""Generate deterministic titlecase fixtures from the original implementation.

Produces, next to this script:

    data/inputs.txt          2000 titles
    data/expected.txt        titlecase() of each input, one per line
    data/hidden_inputs.txt  2000 different titles
    data/hidden_expected.txt titlecase() of each hidden input, one per line

The expected files are produced *only* by importing and calling the original
Python implementation; no answer is written by hand.  The random seed is fixed,
so the same files are produced on every run.

Run:  python titlecase-go/tests/gen.py
"""

from __future__ import annotations

import hashlib
import random
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
PER_FILE = 2000
SEED = 1

# ---------------------------------------------------------------------------
# Locate and import the original library (never reimplement its behaviour).
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve()


def _find_original_repo() -> Path:
    """Return the checkout of python-titlecase used as the reference."""
    task_dir = _HERE.parents[1]           # .../titlecase-go
    candidates = [
        task_dir.parent / "python-titlecase",   # sibling of the task folder
        task_dir / "python-titlecase",          # inside the task folder
        _HERE.parent / "python-titlecase",      # next to tests/
        Path("/workspace/repo"),                # inside a running container
    ]
    for candidate in candidates:
        if (candidate / "titlecase" / "__init__.py").is_file():
            return candidate
    raise SystemExit(
        "Could not find the original python-titlecase checkout. Looked in:\n  "
        + "\n  ".join(str(c) for c in candidates)
    )


# Importing this module must have no side effects: rewardkit imports every
# ``*.py`` file in the verifier's tests directory during discovery, and this
# generator is not a criterion file.  The reference library is therefore
# imported inside ``main()`` only.

# ---------------------------------------------------------------------------
# Vocabulary and tricky cases.  Each tricky entry exercises one or more of the
# rules documented in NOTES.md, including the surprising ones (small words
# lower-cased mid-sentence, sub-phrase capitalisation after periods/dashes,
# all-caps lines, initials, Mc/Mac, apostrophe-second words, compounds, …).
# ---------------------------------------------------------------------------

NORMAL_WORDS = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "a", "tale", "of", "two", "cities", "war", "and", "peace", "lord",
    "rings", "great", "expectations", "pride", "prejudice", "moby", "dick",
    "crime", "punishment", "catcher", "rye", "brave", "new", "world",
    "nineteen", "eighty", "four", "animal", "farm", "old", "man", "sea",
    "sound", "fury", "gone", "wind", "sun", "also", "rises", "heart",
    "darkness", "clockwork", "orange", "handmaid", "story", "neverending",
    "hitchhiker", "guide", "galaxy", "dune", "foundation", "neuromancer",
    "snow", "crash", "infinite", "jest", "gravity", "rainbow", "catch",
    "twenty", "two", "slaughterhouse", "five", "breakfast", "champions",
    "mother", "night", "slaughter", "house", "bell", "jar", "bell",
    "mockingbird", "gatsby", "sun", "attracts", "farewell", "arms",
    "for", "whom", "bell", "tolls", "east", "eden", "grapes", "wrath",
    "their", "eyes", "were", "watching", "god", "passing", "things",
    "fall", "apart", "no", "country", "old", "men", "and", "the", "sea",
]

# Titles that already contain a tricky construct.  Kept ASCII-only so the
# fixtures do not depend on Unicode table differences between `regex` and `re`.
TRICKY = [
    # small words, including first/last position
    "the lord of the rings",
    "a tale of two cities",
    "the war of the worlds",
    "of mice and men",
    "to be or not to be",
    "what is it all about",
    "the end",
    "they walked in the",
    "go to the store and buy it",
    "a",
    "as you like it",
    # sub-phrase separators
    "hello: the world",
    "wait; the end",
    "stop. the beginning",
    "why? the reason",
    "wow! the answer",
    "hello - the world",
    "based on a true story -- the end",
    "word - the",
    "the end: the",
    "U.S.A. and e.g. examples",
    "hello. the world",
    # apostrophe-second words
    "don't stop",
    "o'reilly and sons",
    "l'oreal paris",
    "d'angelo's place",
    "it's the 1990s",
    "can't stop won't stop",
    # Mc / Mac prefixes
    "mcdonald and macarthur",
    "Mcdonald mcDonald",
    "MACARTHUR MCDONALD",
    "the mcDonald family",
    # titles
    "dr smith met mrs jones and ms doe",
    "mr and mrs smith",
    "dr. who and ms. marvel",
    # inline periods and initials
    "example.com and github.com",
    "the U.S. army",
    "U.S. ARMY AND A.B. JONES",
    "the U.S.A. army",
    "e.g. and i.e.",
    "node.js and vue.js",
    "j.r.r. tolkien wrote it",
    "U.S.A. and U.K.",
    # internally capitalised words
    "iPhone and eBay",
    "the openSSL project",
    "macOS and iOS",
    "youTube video",
    "eCommerce site",
    # slash compounds
    "read/write and/or up/down",
    "and/or",
    "input/output",
    "the and/or problem",
    # hyphen compounds
    "mother-in-law",
    "well-known fact-based",
    "x-ray and t-shirt and e-commerce",
    "a state-of-the-art solution",
    "twenty-one guns",
    # all-caps words and lines
    "THE QUICK BROWN FOX",
    "NASA AND THE U.S. ARMY",
    "HTTP the server AND the client",
    "HELLO WORLD",
    "THE OPENSSL THE PROJECT",
    "IBM and ATT",
    "the ARMY of the U.S.A.",
    "the MAN who fell",
    "word AND word",
    # consonant-only acronyms
    "nbc and brb and cnn",
    "the BBC and CNN",
    "xyz corp",
    # quotes, brackets and punctuation
    'the "the" end',
    "the 'the' (the) [the] {the}",
    "(the) start",
    "hello, world!",
    "the end.",
    "a:b the c",
    "foo: the bar; the baz? the qux!",
    # numbers
    "1st 2nd 3rd",
    "the 1990s called",
    "chapter 2: the return",
    # whitespace
    "hello   world",
    "a\tb",
    "  leading and trailing",
    "hello\tworld",
    # versus / abbreviations
    "e-mail vs. v. the thing",
    "ali vs. frazier",
    "case v. case",
    # more small-word and first/last combinations
    "see Appendix A U.S. Army",
    "the start of the end",
    "in the beginning",
    "up and down and all around",
    "what the but for",
]

PUNCT_END = ["", "", "", ".", "!", "?", ":", ";"]
JOIN_SEPARATORS = [" ", " ", " ", " ", "  ", "\t"]


def _retitle(text: str) -> str:
    """Return one of several casing variants of a normal sentence."""
    style = random.randrange(5)
    if style == 0:
        return text
    if style == 1:
        return text.capitalize()
    if style == 2:
        return text.upper()
    if style == 3:
        words = text.split(" ")
        index = random.randrange(len(words))
        words[index] = words[index].upper()
        return " ".join(words)
    words = text.split(" ")
    index = random.randrange(len(words))
    words[index] = words[index].capitalize()
    return " ".join(words)


def _normal_sentence(min_words: int = 3, max_words: int = 8) -> str:
    words = [random.choice(NORMAL_WORDS) for _ in range(random.randint(min_words, max_words))]
    return _retitle(" ".join(words))


def _join(parts: list[str]) -> str:
    separator = random.choice(JOIN_SEPARATORS)
    return separator.join(parts)


def _make_title() -> str:
    kind = random.random()

    if kind < 0.28:  # plain sentence
        title = _normal_sentence()
    elif kind < 0.62:  # tricky phrase embedded in normal words
        before = _normal_sentence(1, 3)
        after = _normal_sentence(0, 3)
        parts = [p for p in (before, random.choice(TRICKY), after) if p]
        title = _join(parts)
    elif kind < 0.82:  # one or two tricky phrases
        count = random.choice([1, 1, 1, 2])
        title = _join([random.choice(TRICKY) for _ in range(count)])
    elif kind < 0.92:  # all-caps line (exercises the all-caps path)
        words = [random.choice(NORMAL_WORDS) for _ in range(random.randint(3, 6))]
        title = " ".join(words).upper()
    else:  # punctuation around a normal sentence
        title = f"\"{_normal_sentence(2, 5)}\"{random.choice(PUNCT_END)}"

    if random.random() < 0.25:
        title = title + random.choice(PUNCT_END)
    if random.random() < 0.08:
        title = title + "  " + random.choice(NORMAL_WORDS)

    return title


def _generate(count: int, forbidden: set[str]) -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()
    attempts = 0
    while len(titles) < count:
        attempts += 1
        if attempts > count * 500:
            raise SystemExit(f"Could not generate {count} unique titles")
        title = _make_title()
        if not title or title in seen or title in forbidden:
            continue
        # Keep every fixture a single, non-empty line without stray whitespace.
        if "\n" in title or "\r" in title:
            continue
        title = title.strip()
        if not title or title in seen or title in forbidden:
            continue
        seen.add(title)
        titles.append(title)
    return titles


def _write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> None:
    repo = _find_original_repo()
    sys.path.insert(0, str(repo))

    # The only source of expected output is the original implementation.
    from titlecase import __version__ as reference_version
    from titlecase import titlecase

    random.seed(SEED)

    inputs = _generate(PER_FILE, set())
    hidden_inputs = _generate(PER_FILE, set(inputs))
    assert len(inputs) == PER_FILE and len(hidden_inputs) == PER_FILE
    assert not (set(inputs) & set(hidden_inputs))

    expected = [titlecase(line) for line in inputs]
    hidden_expected = [titlecase(line) for line in hidden_inputs]

    for line in expected + hidden_expected:
        assert "\n" not in line and "\r" not in line

    _write_lines(DATA_DIR / "inputs.txt", inputs)
    _write_lines(DATA_DIR / "expected.txt", expected)
    _write_lines(DATA_DIR / "hidden_inputs.txt", hidden_inputs)
    _write_lines(DATA_DIR / "hidden_expected.txt", hidden_expected)

    print(f"reference: {repo} (titlecase {reference_version})")
    for name in ("inputs.txt", "expected.txt", "hidden_inputs.txt", "hidden_expected.txt"):
        path = DATA_DIR / name
        print(f"{path.name}: {sum(1 for _ in path.open(encoding='utf-8'))} lines, sha256:{_digest(path)}")


if __name__ == "__main__":
    main()
