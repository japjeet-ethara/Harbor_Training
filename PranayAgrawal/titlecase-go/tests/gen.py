#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate line-oriented fixtures for the Go titlecase port.

The input files contain one title per line.  The expected files are never
written by hand: every expected line is the return value of calling the
original Python ``titlecase()`` from ``../python-titlecase`` on the matching
input line, with the default arguments (the same contract the Go program is
graded on).

Tricky-case coverage follows the rules documented in NOTES.md:

  1. line splitting / blank lines
  2. preserved blank lines (not a default-argument behaviour; blank input
     lines are still represented)
  3. whitespace preservation (tabs, NBSP, hair space, six-per-em space)
  4. normalised whitespace (not a default-argument behaviour; tabbed input is
     still represented and its expected value comes from the default call)
  5. callback words (not a default-argument behaviour; the input line is still
     represented and its expected value comes from the default call)
  6. initials on a fully uppercase line
  7. d' / o' / l' forms, including the curly apostrophe
  8. Mc / mc / MC names
  9. Mr / Mrs / Ms / Dr
 10. words containing an inline period
 11. words that already contain an internal capital
 12. small words
 13. slash-separated pieces
 14. hyphen-separated pieces
 15. fully uppercase lines
 16. consonant-only acronyms
 17. ordinary first-letter capitalisation
 18. small words at the start or end of a line
 19. small words after subphrase punctuation and dashes

Run from anywhere with a Python 3 interpreter:

    python tests/gen.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_ROOT = HERE.parent
REPO = TASK_ROOT / "python-titlecase"
DATA_DIR = HERE / "data"

if not (REPO / "titlecase" / "__init__.py").is_file():
    raise SystemExit("cannot find the original implementation at %s" % REPO)

# Import the package from the repository, not from site-packages.  Do not
# leave a __pycache__ directory behind in the original repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO))
import titlecase as original  # noqa: E402
from titlecase import titlecase  # noqa: E402

try:
    Path(original.__file__).resolve().relative_to(REPO.resolve())
except ValueError:
    raise SystemExit(
        "imported titlecase from %s instead of %s"
        % (original.__file__, REPO)
    )

COUNT_PER_FILE = 2000
SEED = 1

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

NORMAL_WORDS = [
    "acorn", "adventure", "air", "ancient", "apple", "autumn", "banana",
    "basket", "beach", "bird", "black", "blue", "book", "bread", "bridge",
    "bright", "brown", "butter", "camera", "candle", "castle", "cheese",
    "city", "cloud", "coffee", "computer", "country", "dance", "dark",
    "dawn", "desert", "desk", "dream", "drum", "earth", "evening", "family",
    "field", "fire", "forest", "friend", "future", "garden", "golden",
    "guitar", "happy", "history", "island", "journey", "keyboard", "lamp",
    "letter", "light", "lightning", "loud", "mountain", "movie", "music",
    "mystery", "nature", "new", "ocean", "old", "orange", "paper", "people",
    "phone", "piano", "planet", "purple", "quiet", "rain", "river", "screen",
    "shadow", "silver", "slow", "snow", "spring", "star", "stone", "storm",
    "story", "strong", "summer", "sunrise", "sunset", "thunder", "travel",
    "tree", "village", "violin", "water", "weak", "white", "window",
    "winter", "yellow", "young",
]

INITIALS = [
    "A.B", "A.B.", "D.C.", "D.C", "U.S.A.", "U.K.", "N.Y.", "P.M.", "A.M.",
    "E.U.", "B.C.",
]

TRICKY_WORDS = [
    # 6: initials on an all-caps line
    "A.B", "A.B.", "D.C.", "D.C", "U.S.A.", "U.K.", "N.Y.", "P.M.", "A.M.",
    "E.U.", "B.C.",
    # 7: d' / o' / l' forms
    "l'grange", "d'angelo", "o'neill", "l'amour", "d'artagnan", "o'brien",
    "l'ecole", "d'vorah", "o'grady", "o'grange's", "L'grange", "O'grange",
    "l'GranGe", "o'Grange", "o'melveny", "o'doyle",
    "l\u2018grange", "d\u2018angelo", "o\u2018neill",
    # 8: Mc / mc / MC names
    "mcclelland", "mcarthur", "mcdonald", "mcintosh", "mcgregor", "mcallister",
    "mcdowell", "mcgraw", "mckinsey", "mcadams", "mc", "mac", "macintosh",
    "MCGREGOR", "McIntosh", "mccay", "mcbut", "mcdo", "mcby", "mcdonalds",
    # 9: honorifics
    "mr", "mrs", "ms", "dr", "MR", "MRS", "MS", "DR", "dR", "Mr.", "Mrs.",
    "Ms.", "Dr.",
    # 10: inline periods
    "example.com", "del.icio.us", "foo.bar", "a.b", "x.y.z", "example.org",
    "http://foo.com", "https://example.com/path",
    # 11: internal capitals
    "iTunes", "eBay", "iPhone", "macOS", "mySQL", "youTube", "openAI",
    "JavaScript", "PostgreSQL",
    # 12: small words
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
    # 13: slash pieces
    "word/word", "and/or", "either/or", "TCP/IP", "read/write",
    "input/output", "his/her", "yes/no", "FTP/SFTP", "parent/child",
    "o'melveny/o'doyle", "a/b/c",
    # 14: hyphen pieces
    "end-to-end", "state-of-the-art", "mother-in-law", "up-to-date",
    "self-esteem", "e-mail", "x-ray", "re-enter", "twenty-one",
    "brother-in-law", "over-the-top", "mccay-mcbut-mcdo", "mcfoo-bar",
    # 16: consonant-only acronyms and short consonant words
    "cnn", "tcp", "udp", "bbc", "nbc", "dvd", "gps", "html", "css", "xml",
    "ftp", "vpn", "dns", "php", "json", "st", "sc", "ng", "ly", "ny", "dc",
    "tv",
]

# These are examples from NOTES.md, the repository's own tests, and a few
# deliberately awkward strings.  They are inputs only.  No expected output is
# stored in this file.
PUBLIC_CURATED = [
    # 1 / 2: line splitting and blank lines
    "Line number one",
    "and Line three",
    # 3: whitespace preservation
    "text\twith\ttabs",
    "a mix\u00a0of\tdifferent\u200aspace\u2006characters",
    "text\u00a0with\u00a0nonbreaking\u00a0spaces",
    # An empty input line, placed away from the start and end of the file so
    # that line readers which trim the whole file still see it.
    "",
    # 5: callback example, evaluated with the default arguments
    "a simple tcp and udp wrapper",
    # 6: initials on an all-caps line
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "FOO BAR 5TH ST",
    "EPISODE 7 \u2014 THE FORCE AWAKENS",
    # 7: d' / o' / l' forms
    "l'grange",
    "l'grange l'grange l'Grange l'Grange",
    "L'grange L'grange L'Grange L'Grange",
    "l'GranGe",
    "o'grange O'grange o'Grange O'Grange",
    "o'grange's O'grange's o'Grange's O'Grange's",
    "O'GranGe",
    "o'melveny/o'doyle o'Melveny/o'doyle O'melveny/o'doyle o'melveny/o'Doyle o'melveny/O'doyle",
    # 8: Mc / mc / MC names
    "mcclelland",
    "mccay-mcbut-mcdo mcdonalds/mcby",
    "oblon, spivak, mcclelland, maier & neustadt",
    "Mcoblon, spivak, mcclelland, mcmaier, & mcneustadt",
    "mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar",
    "Mr McTavish went to MacDonalds",
    "mac mc MAC MC machine",
    # 9: honorifics
    "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
    # 10: inline periods
    "example.com",
    "this is just an example.com",
    "this is something listed on del.icio.us",
    "this is http://foo.com",
    # 11: internal capitals
    "iTunes",
    "iTunes should be unmolested",
    "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
    # 12: small words
    "this v that",
    "this v. that",
    "this vs that",
    "this vs. that",
    # 13: slash pieces
    "word/word",
    "a title and/or string",
    "dance with me/let\u2019s face the music and dance",
    # 13 / 14: mixed slash and hyphen pieces
    "end-to-end",
    "a-b end-to-end two-not-three/three-by-four/five-and",
    # 15: all-caps lines
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "THE CASE OF X \u2264 7",
    # 16: consonant-only acronyms
    "cnn",
    "Words with all consonants like cnn are acronyms",
    # 17: ordinary capitalisation
    "yea no",
    "YEA NO",
    "a thing",
    # 18: small words first and last
    "Small word at end is nothing to be afraid of",
    "'by the Way, small word at the start but within quotes.'",
    '"Nothing to Be Afraid of?"',
    '"Nothing to be Afraid Of?"',
    # 19: subphrase punctuation
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'",
    'sub-phrase with a small word in quotes: "a trick, perhaps?"',
    "Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?",
    "Hyphen Delimited Sub-Phrase With a Small Word in Quotes - 'a Trick, Perhaps?'",
    'Hyphen Delimited sub-phrase with a small word in quotes - "a trick, perhaps?"',
    "Snakes on a Plane - The TV Edit - The Famous Line",
    "Starting an Em Dash Delimited Sub-Phrase With a Small Word \u2014 a Trick, Perhaps?",
    "Em Dash Delimited Sub-Phrase With a Small Word in Quotes \u2014 'a Trick, Perhaps?'",
    'Em Dash Delimited sub-phrase with a small word in quotes \u2014 "a trick, perhaps?"',
    "Snakes on a Plane \u2014 The TV Edit \u2014 The Famous Line",
    "episode 7 \u2013 The force awakens",
    "the case of X \u2264 7",
    # punctuation, apostrophes, smart quotes, and accents
    "Q&A with steve jobs: 'that's what happens in technology'",
    "What is AT&T's problem?",
    "Apple deal with AT&T falls through",
    "The SEC's Apple probe: what you need to know",
    "generalissimo francisco franco: still dead; kieren McCarthy: still a jackass",
    "O'Reilly should be untouched",
    "my name is o'reilly",
    "reading between the lines of steve jobs\u2019s \u2018thoughts on music\u2019",
    "seriously, \u2018repair permissions\u2019 is voodoo",
    "'QUOTE' A GREAT",
    "\u2018QUOTE\u2019 A GREAT",
    "\u201cYOUNG AND RESTLESS\u201d",
    "EL NI\u00d1O A ARRIV\u00c9 HIER",
    "\u00dd\u00c6 \u00d1\u00d8",
    "\u00fd\u00e6 \u00f1\u00f8",
    "34th 3rd 2nd",
    "foo bar 5th st",
]

HIDDEN_CURATED = [
    # same categories as the public list, but different strings
    "One two three",
    "four and five",
    "tabbed\twords\there",
    "and\tthen\tmore",
    "alpha\u00a0beta\tgamma\u200adelta\u2006epsilon",
    "space\u00a0mix\there",
    "",

    "a simple dns and vpn wrapper",
    "NEW YORK, N.Y. SHOULD HOST THE EVENT",
    "THE A.B.C. OF D.C. IS EASY",
    "SEND IT TO THE U.K. OFFICE",
    "MEET AT 5 P.M. SHARP",
    "PLAIN UPPERCASE WORDS HERE",
    "l'oreal",
    "d'vorah",
    "o'brien",
    "l'ecole",
    "d\u2018artagnan",
    "o\u2018grady",
    "l'amour d'angelo o'neill",
    "mcdowell",
    "mcgraw",
    "mckinsey",
    "MCADAMS",
    "McAllister",
    "mc mrs dr",
    "mr",
    "mrs",
    "ms",
    "dr who",
    "THE DR AND MRS JONES",
    "foo.bar",
    "a.b.c",
    "go to example.org now",
    "x.y",
    "visit del.icio.us",
    "iPhone and macOS",
    "eBay sells stuff",
    "youTube videos",
    "mySQL query",
    "bat and ball",
    "in the middle of the night",
    "as soon as possible",
    "by the way",
    "one of us",
    "word/word/word",
    "his/her",
    "yes/no",
    "FTP/SFTP",
    "parent/child",
    "a // b",
    "well-known",
    "twenty-one",
    "brother-in-law",
    "over-the-top",
    "x-ray vision",
    "mccay-mcbut-mcdo mcfoo-mcbar",
    "THIS TITLE IS ENTIRELY UPPERCASE AND HAS SMALL WORDS",
    "ANOTHER ALL CAPS LINE WITH THE AND OF",
    "dvd",
    "gps and html",
    "the bbc and cnn",
    "css tricks",
    "php code",
    "one two",
    "hello there world",
    "the cat in the hat",
    "love is all around",
    "beginning and end",
    "a tale of two cities",
    "the end",
    "of mice and men",
    "to be or not to be",
    "Really? and then",
    "Stop: and go",
    "Wait; or hurry",
    "Now! and later",
    "Hyphen - and more",
    "En dash \u2013 or more",
    "Em dash \u2014 or more",
    "Figure dash \u2012 or more",
    "Horizontal bar \u2015 or more",
    "goodbye, world?",
    "[the] start",
    'quotes "and" things',
    "ending punctuation: no.",
    "i.e. this or that",
    "1st and 2nd place",
    "42 and 99",
    "\u00e9lan vital",
    "cr\u00e8me br\u00fbl\u00e9e",
    "Zo\u00eb\u2019s book",
    "\u00c0\u00c9 \u00ce\u00d5",
    "Q&A with steve wozniak",
    "What is AT&T's answer?",
    "Apple deal with AT&T is done",
    "The SEC's Google probe",
    "'by the way, small word at the start but within quotes.'",
    "O'Reilly should be left alone",
    "my name is o'brien",
    "reading between the lines of steve jobs\u2019s \u2018thoughts on music\u2019 and more",
    "seriously, \u2018repair permissions\u2019 is still voodoo",
    "'QUOTED' A GREAT",
    "\u2018QUOTED\u2019 A GREAT",
    "\u201cYOUNG AND HUNGRY\u201d",
    "EL NI\u00d1O A ARRIV\u00c9 ICI",
    "\u00dd\u00c6 \u00d1\u00d8 EXTRA",
    "\u00fd\u00e6 \u00f1\u00f8 extra",
    "21st 22nd 23rd",
    "baz qux 6th ave",
    "this v those",
    "this v. those",
    "this vs those",
    "this vs. those",
    "untouched by a small word",
    "the quick brown fox",
]

PREFIXES = ["", "", "", "", "(", "'", '"', "[", "{", "\u2018", "\u201c"]
SUFFIXES = [
    "", "", "", "", ",", ".", ";", ":", "?", "!", "...", ")", "'", '"', "]",
    "}", "\u2019", "\u201d",
]
SEPARATORS = [
    " ", " ", " ", " ", " ", "  ", "\t", " \t", "\t ", "   ",
    "\u00a0", "\u200a", "\u2006", " \u00a0 ",
]

# A line-based fixture must not contain a character that a line reader might
# treat as a newline.  Tabs and ordinary Unicode spaces are allowed.
FORBIDDEN_LINE_CHARACTERS = "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"


def validate_title(title: str) -> None:
    if any(ch in title for ch in FORBIDDEN_LINE_CHARACTERS):
        raise ValueError("title contains a line break: %r" % title)
    if title != title.strip():
        raise ValueError("title has leading or trailing whitespace: %r" % title)


def decorate(word: str) -> str:
    return random.choice(PREFIXES) + word + random.choice(SUFFIXES)


def join_words(words: list[str]) -> str:
    parts = []
    for index, word in enumerate(words):
        if index:
            parts.append(random.choice(SEPARATORS))
        parts.append(word)
    return "".join(parts)


def random_case(word: str) -> str:
    roll = random.random()
    if roll < 0.55:
        return word
    if roll < 0.75:
        return word.capitalize()
    if roll < 0.90:
        return word.upper()
    if len(word) > 2 and word.isascii():
        index = random.randrange(1, len(word))
        return word[:index] + word[index].upper() + word[index + 1:]
    return word


def sentence_title() -> str:
    words = [
        random_case(random.choice(NORMAL_WORDS))
        for _ in range(random.randint(1, 9))
    ]
    for _ in range(random.randint(0, 3)):
        words.insert(random.randrange(len(words) + 1), random.choice(SMALL_WORDS))
    if random.random() < 0.55:
        words[random.randrange(len(words))] = random.choice(TRICKY_WORDS)
    for index in range(len(words)):
        if random.random() < 0.12:
            words[index] = decorate(words[index])
    if words and random.random() < 0.45:
        words[-1] += random.choice([",", ".", "!", "?", ":", ";"])
    return join_words(words)


def caps_title() -> str:
    words = []
    for _ in range(random.randint(2, 9)):
        roll = random.random()
        if roll < 0.55:
            words.append(random.choice(NORMAL_WORDS).upper())
        elif roll < 0.75:
            words.append(random.choice(SMALL_WORDS).upper())
        elif roll < 0.90:
            words.append(random.choice(INITIALS))
        else:
            words.append(random.choice(TRICKY_WORDS).upper())
    words.insert(random.randrange(len(words) + 1), random.choice(SMALL_WORDS).upper())
    if random.random() < 0.60:
        words.insert(random.randrange(len(words) + 1), random.choice(INITIALS))
    for index in range(len(words)):
        if random.random() < 0.10:
            words[index] = decorate(words[index])
    return join_words(words).upper()


def token_soup() -> str:
    words = []
    for _ in range(random.randint(1, 8)):
        roll = random.random()
        if roll < 0.55:
            words.append(random.choice(TRICKY_WORDS))
        elif roll < 0.80:
            words.append(random_case(random.choice(NORMAL_WORDS)))
        else:
            words.append(random.choice(SMALL_WORDS))
    for index in range(len(words)):
        if random.random() < 0.15:
            words[index] = decorate(words[index])
    return join_words(words)


def punctuation_title() -> str:
    small_a = random.choice(SMALL_WORDS)
    small_b = random.choice(SMALL_WORDS)
    first = random.choice(NORMAL_WORDS)
    second = random.choice(NORMAL_WORDS)
    template = random.choice([
        "{first} {small_a}: {small_b} {second}",
        "{first} {small_a}: {small_b} {second}?",
        "{first} {small_a}; {small_b} {second}",
        "{first} {small_a}. {small_b} {second}",
        "{first} {small_a}! {small_b} {second}",
        "{first} {small_a} - {small_b} {second}",
        "{first} {small_a} \u2013 {small_b} {second}",
        "{first} {small_a} \u2014 {small_b} {second}",
        "{first} {small_a} \u2012 {small_b} {second}",
        "{first} {small_a} \u2015 {small_b} {second}",
        "'{small_a} {first}' and {small_b} {second}",
        '"{small_a} {first}" and {small_b} {second}',
        "({small_a}) {first} and {small_b} {second}",
        "[{small_a}] {first} and {small_b} {second}",
        "{small_a} {first} and {small_b} {second}",
        "{first}, {small_a} {second}!",
        "{first}? {small_a} {second}",
        "{first}/{second}/{small_a}",
        "{first}-{small_a}-{second}",
        "{first} {second} {small_a}?",
    ])
    return template.format(
        first=first, second=second, small_a=small_a, small_b=small_b
    )


def whitespace_title() -> str:
    words = [
        random.choice(NORMAL_WORDS + SMALL_WORDS)
        for _ in range(random.randint(2, 7))
    ]
    if random.random() < 0.50:
        words[random.randrange(len(words))] = random.choice(TRICKY_WORDS)
    return join_words(words)


def random_title() -> str:
    roll = random.random()
    if roll < 0.30:
        return sentence_title()
    if roll < 0.52:
        return caps_title()
    if roll < 0.74:
        return token_soup()
    if roll < 0.90:
        return punctuation_title()
    return whitespace_title()


def build_titles(curated: list[str], count: int, used: set[str]) -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()
    for title in curated:
        validate_title(title)
        if title in used or title in seen:
            continue
        titles.append(title)
        seen.add(title)
    attempts = 0
    while len(titles) < count:
        attempts += 1
        if attempts > count * 1000:
            raise RuntimeError("could not generate enough distinct titles")
        title = random_title()
        validate_title(title)
        if title in used or title in seen:
            continue
        titles.append(title)
        seen.add(title)
    if len(titles) != count:
        raise RuntimeError("expected %d titles, got %d" % (count, len(titles)))
    return titles


def titlecase_lines(titles: list[str]) -> list[str]:
    expected = []
    for title in titles:
        result = titlecase(title)
        if any(ch in result for ch in FORBIDDEN_LINE_CHARACTERS):
            raise ValueError("expected output contains a line break: %r" % result)
        expected.append(result)
    return expected


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")


def main() -> None:
    random.seed(SEED)

    used: set[str] = set()
    public_titles = build_titles(PUBLIC_CURATED, COUNT_PER_FILE, used)
    used.update(public_titles)
    # The empty title is the line-oriented way to exercise blank-line input,
    # so it is deliberately allowed to occur in both fixtures.
    hidden_titles = build_titles(HIDDEN_CURATED, COUNT_PER_FILE, used - {""})

    overlap = set(public_titles) & set(hidden_titles)
    if overlap - {""}:
        raise RuntimeError("public and hidden inputs overlap")

    public_expected = titlecase_lines(public_titles)
    hidden_expected = titlecase_lines(hidden_titles)

    write_lines(DATA_DIR / "inputs.txt", public_titles)
    write_lines(DATA_DIR / "expected.txt", public_expected)
    write_lines(DATA_DIR / "hidden_inputs.txt", hidden_titles)
    write_lines(DATA_DIR / "hidden_expected.txt", hidden_expected)

    branch = "regex" if getattr(original, "REGEX_AVAILABLE", False) else "stdlib re"
    print("titlecase module: %s" % original.__file__)
    print("titlecase version: %s" % original.__version__)
    print("regex branch: %s" % branch)
    print("wrote %d public titles and %d hidden titles to %s"
          % (len(public_titles), len(hidden_titles), DATA_DIR))


if __name__ == "__main__":
    main()
