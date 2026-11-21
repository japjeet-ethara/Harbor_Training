#!/usr/bin/env python3
"""Generate deterministic titlecase fixtures.

Inputs are synthetic. Expected outputs come only from the original
python-titlecase ``titlecase()`` function, using the third-party ``regex``
package. Each input is one line and is passed to ``titlecase()`` on its own.
"""

import random
import sys
from pathlib import Path

import regex
from regex import DEFAULT_VERSION  # third-party package; stdlib re has neither

REPO = Path(__file__).resolve().parent.parent
SIBLING = REPO.parent / "python-titlecase"
sys.path.insert(0, str(SIBLING))

from titlecase import REGEX_AVAILABLE
from titlecase import titlecase

DATA_DIR = Path(__file__).resolve().parent / "data"
COUNT = 2000

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]
WORDS = [
    "life", "web", "design", "string", "title", "state", "art", "music",
    "world", "bridge", "market", "report", "system", "garden", "river",
    "stone", "paper", "signal", "office", "summer", "winter", "public",
    "record", "simple", "modern", "ancient", "quiet", "bright", "silver",
    "golden", "harbor", "island", "forest", "valley", "castle", "engine",
    "letter", "window", "shadow", "memory", "future", "history", "science",
    "nature", "people", "family", "school", "city", "country", "ocean",
    "mountain", "answer", "question", "problem", "machine", "language",
    "story", "editor", "filter", "manual", "style", "phrase", "token",
]
CONS = ["cnn", "html", "css", "ftp", "nbc", "bbc", "nyt", "gps", "lcd", "pdf", "sql", "xml", "bbc"]
MIXED = ["iTunes", "iPhone", "eBay", "AT&T", "AT&T's", "IPv6", "JavaScript", "YouTube", "PhD"]
DOMAINS = ["example.com", "del.icio.us", "foo.bar", "news.example.com", "whitehouse.gov"]
URLS = ["http://foo", "http://foo.com", "https://example.com", "http://bar"]
APOS = [
    "l'grange", "L'grange", "l'GranGe", "o'grange", "O'Grange", "d'angelo",
    "D'angelo", "o'grange's", "O'Grange's", "it's", "o'reilly", "O'Reilly",
]
MC_NAMES = [
    "mcclelland", "mcmaier", "mcneustadt", "mctavish", "mcdonalds",
    "MCFOO", "McFoo", "mcfoo", "Mcoblon", "mcbar",
]
DELIMS = [":", ";", ".", "?", "!", "-", "\u2013", "\u2012", "\u2014", "\u2015"]

# Single-line examples from python-titlecase/NOTES.md and the library tests.
CANONICAL = [
    "life via the web",
    "'by the Way, small word at the start but within quotes.'",
    '"Nothing to Be Afraid of?"',
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "state-of-the-art design",
    "a title and/or string",
    "visit http://foo today",
    "L'grange",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "Words with all consonants like cnn are acronyms",
    "iTunes should be unmolested",
    "this is just an example.com",
    "text\twith\ttabs",
    "oblon, spivak, mcclelland, maier & neustadt",
    "see d.c. now",
    "What is AT&T's problem?",
    "five-and",
    "it's fine",
    "rhythm",
    "st",
    "this is http://foo.com",
    "a-b end-to-end two-not-three/three-by-four/five-and",
    "EL NI\u00d1O A ARRIV\u00c9 HIER",
    "Mr McTavish went to MacDonalds",
    "O'Reilly should be untouched",
    "my name is o'reilly",
    "l'GranGe",
    "o'grange's O'grange's o'Grange's O'Grange's",
    "mac mc MAC MC machine",
    "\u201cYOUNG AND RESTLESS\u201d",
    "a mix\u00a0of\tdifferent\u200aspace\u2006characters",
    "Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?",
    "Snakes on a Plane \u2014 The TV Edit \u2014 The Famous Line",
    "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
]


def _word():
    return random.choice(WORDS)


def _words(n):
    return [_word() for _ in range(n)]


def normal(_i):
    parts = _words(random.randint(3, 8))
    for idx in range(len(parts)):
        if random.randrange(2):
            parts[idx] = parts[idx].capitalize()
    if not any(ch.islower() for part in parts for ch in part):
        parts[0] = parts[0].lower()
    if random.randrange(5) == 0:
        parts[-1] = parts[-1] + random.choice([".", "?", "!"])
    return " ".join(parts)


def small_middle(_i):
    left = [w.capitalize() for w in _words(random.randint(1, 3))]
    right = [w.capitalize() for w in _words(random.randint(1, 3))]
    return " ".join(left + [random.choice(SMALL)] + right)


def small_start(_i):
    punct = random.choice(["", "'", '"', "(", "\u201c", "\u2018"])
    end = random.choice(["", ".", "?", "!", "'", '"'])
    body = " ".join(_words(random.randint(2, 5)))
    return f"{punct}{random.choice(SMALL)} {body}{end}"


def small_end(_i):
    punct = random.choice(["", "?", ".", "!", '"', "'"])
    body = " ".join(w.capitalize() for w in _words(random.randint(2, 5)))
    return f"{body} {random.choice(SMALL)}{punct}"


def subphrase(i):
    delim = DELIMS[i % len(DELIMS)]
    left = " ".join(w.capitalize() for w in _words(random.randint(2, 4)))
    right = " ".join(_words(random.randint(1, 3)))
    return f"{left}{delim} {random.choice(SMALL)} {right}"


def hyphen(_i):
    kind = random.randrange(4)
    if kind == 0:
        return f"{_word()}-of-the-{_word()} {_word()}"
    if kind == 1:
        return f"{_word()}-and"
    if kind == 2:
        return f"five-and {_word()}"
    return f"{_word()}-{_word()}/{_word()}-by-{_word()}/five-and"


def slash(_i):
    kind = random.randrange(3)
    if kind == 0:
        return f"{random.choice(SMALL)} {_word()} and/or {_word()}"
    if kind == 1:
        return f"{_word()}/{_word()}"
    return f"{_word()} {_word()}/or {_word()}"


def url(_i):
    return f"visit {random.choice(URLS)} {_word()} today"


def apostrophe(_i):
    return f"{random.choice(APOS)} {_word()} {random.choice(APOS)}"


def allcaps_initials(_i):
    city = random.choice(["WASHINGTON", "BOSTON", "AUSTIN", "DENVER"])
    initials = random.choice(["D.C.", "U.S.", "A.B.", "N.Y."])
    tail = " ".join(w.upper() for w in _words(random.randint(3, 6)))
    return f"{city}, {initials} {tail} AND MORE"


def allcaps(_i):
    parts = [w.upper() for w in _words(random.randint(3, 7))]
    parts.insert(1, random.choice(["AND", "THE", "OF", "TO", "A", "VIA", "VS"]))
    return " ".join(parts)


def consonants(_i):
    return (
        f"{_word().capitalize()} with {random.choice(CONS)} "
        f"and rhythm but not st"
    )


def mixed_preserve(_i):
    return f"keep {random.choice(MIXED)} {random.choice(SMALL)} {_word()}"


def dotted(_i):
    return f"this is just an {random.choice(DOMAINS)} {_word()}"


def spaced(_i):
    sep = random.choice(["\t", "\u00a0", "\u200a", "\u2006", "  "])
    return sep.join(_words(random.randint(3, 5)))


def mc_name(_i):
    return f"oblon, spivak, {random.choice(MC_NAMES)}, maier & neustadt"


def unicode_title(_i):
    return random.choice([
        "el ni\u00f1o arrived yesterday",
        "EL NI\u00d1O A ARRIV\u00c9 HIER",
        "cr\u00e8me br\u00fbl\u00e9e on the menu",
        "\u00fd\u00e6 \u00f1\u00f8",
        "\u00dd\u00c6 \u00d1\u00d8",
        "YEA NO",
        "yea no",
    ])


def quotes(_i):
    pairs = [("'", "'"), ('"', '"'), ("\u201c", "\u201d"), ("\u2018", "\u2019")]
    open_q, close_q = random.choice(pairs)
    inner = f"{random.choice(SMALL)} {_word()}"
    return f"{_word().capitalize()} {open_q}{inner}{close_q}"


def honorifics(_i):
    if random.randrange(2) == 0:
        return "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person"
    return f"Mr {random.choice(MC_NAMES)} went to see Dr {_word()}"


def ordinals(_i):
    return (
        f"{random.choice(['34th', '3rd', '2nd', '5th'])} "
        f"{_word()} Q&A {_word()}"
    )


def small_chain(_i):
    return " ".join(random.choice(SMALL) for _ in range(random.randint(3, 6)))


SPECIALS = [
    small_middle,
    small_start,
    small_end,
    subphrase,
    hyphen,
    slash,
    url,
    apostrophe,
    allcaps_initials,
    allcaps,
    consonants,
    mixed_preserve,
    dotted,
    spaced,
    mc_name,
    unicode_title,
    quotes,
    honorifics,
    ordinals,
    small_chain,
]


def generate_line(i):
    if i % 4 != 3:
        return normal(i)
    return SPECIALS[(i // 4) % len(SPECIALS)](i)


def generate_batch(start, count):
    return [generate_line(start + offset) for offset in range(count)]


def expected_lines(lines):
    rendered = []
    for index, line in enumerate(lines):
        result = titlecase(line)
        if not isinstance(result, str):
            raise SystemExit(f"titlecase() returned {type(result).__name__} at {index}")
        if "\n" in line or "\r" in line or "\n" in result or "\r" in result:
            raise SystemExit(f"line break in record {index}")
        rendered.append(result)
    return rendered


def write_lines(path, lines):
    if len(lines) != COUNT:
        raise SystemExit(f"{path.name} has {len(lines)} lines, expected {COUNT}")
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    path.write_bytes(payload)


def main():
    if not REGEX_AVAILABLE:
        raise SystemExit("titlecase imported re instead of the regex package")
    if regex.__name__ != "regex":
        raise SystemExit("third-party regex package is not active")
    # Touch the imported constant so a stdlib fallback cannot satisfy this file.
    if DEFAULT_VERSION is None:
        raise SystemExit("regex.DEFAULT_VERSION is missing")

    random.seed(1)
    visible = generate_batch(0, COUNT)
    hidden = generate_batch(COUNT, COUNT)
    if visible == hidden:
        raise SystemExit("visible and hidden inputs are identical")

    for index, sample in enumerate(CANONICAL):
        visible[index] = sample

    if visible == hidden:
        raise SystemExit("visible and hidden inputs are identical after samples")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_lines(DATA_DIR / "inputs.txt", visible)
    write_lines(DATA_DIR / "hidden_inputs.txt", hidden)
    write_lines(DATA_DIR / "expected.txt", expected_lines(visible))
    write_lines(DATA_DIR / "hidden_expected.txt", expected_lines(hidden))


if __name__ == "__main__":
    main()
