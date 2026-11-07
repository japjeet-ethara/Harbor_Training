"""Generate titlecase fixtures from the original Python implementation.

random.seed(1) fixes the titles. Expected lines are whatever
../python-titlecase titlecase() returns for those titles. This file does not
record correct outputs.
"""

import random
import sys
from pathlib import Path

# ../python-titlecase from the titlecase-go task directory.
# Imported lazily so loading this file (Reward Kit imports every tests/*.py)
# does not require the Python package to be installed.
PYTHON_TITLECASE = Path(__file__).resolve().parents[1].parent / "python-titlecase"

DATA_DIR = Path(__file__).resolve().parent / "data"
COUNT = 2000

# Ordinary words. Small words are separate so they show up inside titles.
NORMAL_WORDS = [
    "apple", "bridge", "candle", "castle", "cedar", "captain", "compass",
    "copper", "crystal", "dragon", "falcon", "forest", "garden", "ginger",
    "glacier", "golden", "granite", "harbor", "heron", "island", "jasper",
    "journey", "lantern", "letter", "maple", "marble", "market", "meadow",
    "mirror", "mountain", "orange", "orchard", "otter", "pebble", "pencil",
    "pirate", "prairie", "public", "purple", "queen", "river", "saddle",
    "saffron", "secret", "silver", "sparrow", "story", "summer", "thunder",
    "topaz", "velvet", "village", "violin", "walnut", "willow", "window",
    "winter", "yellow", "beacon", "badger", "birch", "button", "canyon",
    "indigo", "cobalt",
]

# Rule 11. New York Times small words, plus v and vs.
SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

# Tricky tokens and the single-line inputs from NOTES.md. A naive
# "capitalize every word" pass gets these wrong. Multiline NOTES examples
# are not stored here: each generated title is one line.
TRICKY = [
    # Rule 5. All-caps initials (A. or A.B, repeated).
    "A.B.",
    "A.B.C.",
    "D.C.",
    "U.S.",
    "SEE A.B. TODAY",
    # Rule 6. d/o/l plus straight or curly apostrophe, optional 's.
    "d'artagnan",
    "o'clock",
    "o'reilly",
    "o'reilly's",
    "l'grange",
    "l'amour",
    "O'GranGe",
    "l'GranGe",
    "o\u2018clock",
    "l\u2018grange",
    "d'angelo",
    "o'malley",
    "o'brien's",
    # Rule 7. Mc / MC and at least two more characters.
    "mcdonald",
    "MCDONALD",
    "mcgregor",
    "McTavish",
    "mcfoo-bar",
    "mcclelland",
    # Rule 8. Mr, Mrs, Ms, Dr.
    "mr",
    "mrs",
    "ms",
    "dr",
    "MR",
    "Dr",
    "mrs smith",
    # Rule 9. Internal period between letters.
    "example.com",
    "del.icio.us",
    "e.g.",
    "i.e.",
    "D.C. weather",
    "http://foo.com",
    # Rule 10. Capital later in the word, line not all caps.
    "iPhone",
    "iTunes",
    "AT&T",
    "Q&A",
    "OmniFocus",
    "iPhone release",
    # Rule 12. Single slash is split; // is not.
    "word/word",
    "and/or",
    "war/peace",
    "me/let",
    # Rule 13. Hyphenated compounds; inner small words stay lower.
    "end-to-end",
    "mother-in-law",
    "well-known",
    "a-b",
    "two-not-three",
    # Rule 15. All-consonant acronyms longer than two letters; "st" is not.
    "html",
    "css",
    "cnn",
    "nyc",
    "gps",
    "nfl",
    "st",
    "tv",
    "html and css",
    # Rule 16. Leading punctuation, and tokens with no letter.
    "34th",
    "3rd",
    "2nd",
    "5th",
    "21st",
    '"the',
    "'by",
    # Rule 17. Small word first or last.
    "the end of the",
    "hello world",
    # Rule 18. Small word after : ; . ? ! or a dash and a space.
    "hello: the world",
    "still dead; kieren",
    # Whole-line uppercase (rule 14) is also applied at random below.
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    # Preserved whitespace (rule 3).
    "text\twith\ttabs",
    "a simple tcp and udp wrapper",
    "this via that",
]

# Separators. Several of these are the subphrase breaks in rule 18
# (punctuation or dash, then a space). Others keep unusual spaces (rule 3).
SEPARATORS = [
    " ",
    " ",
    " ",
    "  ",
    "\t",
    "\u00a0",
    "\u200a",
    "\u2006",
    ": ",
    "; ",
    ". ",
    "? ",
    "! ",
    " - ",
    " \u2013 ",
    " \u2014 ",
    " \u2012 ",
    " \u2015 ",
]


def make_title():
    """One title: normal words mixed with tricky cases. No line breaks."""
    if random.random() < 0.08:
        return random.choice(TRICKY)

    count = random.randint(3, 7)
    parts = []
    for _ in range(count):
        roll = random.random()
        if roll < 0.25:
            parts.append(random.choice(SMALL_WORDS))
        elif roll < 0.60:
            parts.append(random.choice(TRICKY))
        else:
            parts.append(random.choice(NORMAL_WORDS))

    text = parts[0]
    for part in parts[1:]:
        text += random.choice(SEPARATORS) + part

    if random.random() < 0.08:
        text = '"' + text + '"'
    elif random.random() < 0.04:
        text = "\u201c" + text + "\u201d"
    elif random.random() < 0.04:
        text = "'" + text

    # Rule 14: an entire uppercase line is lowercased before later rules.
    if random.random() < 0.12:
        text = text.upper()
    return text


def titles(count, seen):
    """Draw `count` titles that are not already in `seen`.

    Rejected duplicates still consume random draws, so the sequence stays
    fixed for seed 1. A title accepted here is recorded in `seen` and will
    not be emitted again.
    """
    made = []
    while len(made) < count:
        title = make_title()
        if "\n" in title or "\r" in title:
            raise SystemExit("generated title contains a line break")
        if title in seen:
            continue
        seen.add(title)
        made.append(title)
    return made


def write_lines(path, lines):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")


def expected_for(lines):
    """Run the original titlecase() on every line. Do not invent results."""
    sys.path.insert(0, str(PYTHON_TITLECASE))
    from titlecase import titlecase

    results = []
    for line in lines:
        result = titlecase(line)
        if "\n" in result or "\r" in result:
            raise SystemExit("titlecase() returned a line break")
        results.append(result)
    return results


def main():
    random.seed(1)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    seen = set()
    public = titles(COUNT, seen)
    hidden = titles(COUNT, seen)
    if set(public) & set(hidden):
        raise SystemExit("a title appears in both datasets")

    write_lines(DATA_DIR / "inputs.txt", public)
    write_lines(DATA_DIR / "hidden_inputs.txt", hidden)
    write_lines(DATA_DIR / "expected.txt", expected_for(public))
    write_lines(DATA_DIR / "hidden_expected.txt", expected_for(hidden))


if __name__ == "__main__":
    main()
