#!/usr/bin/env python3
"""Generate reproducible titlecase fixtures from the original Python implementation.

Expected files are produced only by calling titlecase() from ../python-titlecase.
"""

import random
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).resolve().parent / "data"
titlecase = None
COUNT = 2000

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]
WORDS = [
    "apple", "bridge", "castle", "dragon", "engine", "forest", "garden",
    "harbor", "island", "journal", "kingdom", "lantern", "mountain",
    "notebook", "orange", "palace", "quartz", "river", "silver", "temple",
    "umbrella", "valley", "window", "yellow", "zebra", "music", "dance",
    "story", "market", "captain", "winter", "summer", "paper", "stone",
    "cloud", "field", "rhythm", "style", "report", "letter",
]
ACRONYMS = ["cnn", "html", "php", "fbi", "nbc", "ghz", "csv", "sql", "xml"]
APOS = [
    "l'grange", "o'reilly", "o'clock", "d'artagnan", "l'amour", "o'brian",
    "l'GranGe", "O'GranGe", "o'grange's", "d'angelo", "O'Reilly", "l'grange's",
]
MC = ["mcclelland", "mcdonalds", "mcfoo", "mcbar", "MCFOO", "McTavish", "mccarthy", "mcneustadt"]
HONOR = ["mr", "mrs", "ms", "dr", "MR", "MRS", "MS", "Dr", "Mss"]
HOSTS = ["example.com", "del.icio.us", "http://foo.com", "blog.example.com", "e.g.", "i.e."]
MIXED = ["iTunes", "iPhone", "AT&T", "AT&T's", "MacDonalds", "OmniFocus", "PhD", "JavaScript"]
UNICODE_WORDS = ["niño", "crème", "brûlée", "ýæ", "ñø", "arrivé", "hier", "café", "naïve", "Ýæ", "Ñø"]

# Single-line examples from NOTES.md, including the cases that were easy to misread.
CANONICAL = [
    "l'grange",
    "my name is o'reilly",
    "o'grange's",
    "l'GranGe",
    "O'GranGe",
    "mcclelland",
    "foo-mcbar",
    "mcfoo-bar",
    "mac mc MAC MC machine",
    "Mr McTavish went to MacDonalds",
    "mr",
    "Mr mr Mrs Ms Mss Dr dr",
    "Mr. and Mrs. Person",
    "this is just an example.com",
    "this is something listed on del.icio.us",
    "this is http://foo.com",
    "iTunes should be unmolested",
    "What is AT&T's problem?",
    "this vs that",
    "this v that",
    "this v. that",
    "this vs. that",
    "word/word",
    "a title and/or string",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "Words with all consonants like cnn are acronyms",
    "foo bar 5th st",
    "FOO BAR 5TH ST",
    "34th 3rd 2nd",
    "yea no",
    "ýæ ñø",
    "YEA NO",
    "ÝÆ ÑØ",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "a thing",
    "text\twith\ttabs",
    "Q&A with steve jobs: 'that's what happens in technology'",
    "'by the Way, small word at the start but within quotes.'",
    '"Nothing to be Afraid of?"',
    "EPISODE 7 — THE FORCE AWAKENS",
    "episode 7 – The force awakens",
    "EL NIÑO A ARRIVÉ HIER",
    "crème brûlée",
    "'QUOTE' A GREAT",
    "“YOUNG AND RESTLESS”",
    "oblon, spivak, mcclelland, maier & neustadt",
    "a-b end-to-end two-not-three/three-by-four/five-and",
    "dance with me/let’s face the music and dance",
    "reading between the lines of steve jobs’s ‘thoughts on music’",
    "seriously, ‘repair permissions’ is voodoo",
    "generalissimo francisco franco: still dead; kieren McCarthy: still a jackass",
    "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
    "Snakes on a Plane - The TV Edit - The Famous Line",
    "Starting an Em Dash Delimited Sub-Phrase With a Small Word — a Trick, Perhaps?",
    "THE CASE OF X ≤ 7",
    "o'melveny/o'doyle",
    "Apple deal with AT&T falls through",
    "The SEC's Apple probe: what you need to know",
]


def words(n):
    return [random.choice(WORDS) for _ in range(n)]


def normal():
    count = random.randint(3, 8)
    parts = words(count)
    parts[random.randint(1, count - 2)] = random.choice(SMALL)
    if random.random() < 0.5:
        parts[0] = random.choice(SMALL)
    if random.random() < 0.5:
        parts[-1] = random.choice(SMALL)
    return " ".join(parts)


def all_caps():
    return normal().upper()


def initials():
    return normal().upper() + ", D.C. AND A.B."


def apostrophe():
    return f"{random.choice(['my name is', 'meet', 'the book by', 'a tale of'])} {random.choice(APOS)}"


def mc_name():
    return f"{random.choice(MC)}-{random.choice(WORDS + MC)} {normal()}"


def honorific():
    names = " ".join(random.choice(HONOR) for _ in range(random.randint(2, 4)))
    return f"{names}. and {random.choice(HONOR)} {normal()}"


def hostname():
    return f"{normal()} {random.choice(HOSTS)}"


def interior():
    return f"{random.choice(MIXED)} {normal()}"


def slash():
    if random.random() < 0.25:
        return f"see http://{random.choice(['foo.com', 'example.com'])} and {normal()}"
    left = random.choice(SMALL + WORDS)
    right = random.choice(SMALL + WORDS)
    return f"{normal()} {left}/{right}"


def hyphen():
    left = random.choice(SMALL + WORDS + MC)
    right = random.choice(SMALL + WORDS + MC)
    return f"{left}-{right} {normal()}"


def acronym():
    return f"{normal()} {random.choice(ACRONYMS)} {random.choice(['st', 'rd', 'by'])}"


def ordinal():
    return f"{random.choice(['34th', '3rd', '2nd', '5th', '21st'])} {normal()}"


def quoted():
    small = random.choice(SMALL)
    body = normal()
    mark = random.choice(["'", "‘", '"', "“"])
    close = {"'": "'", "‘": "’", '"': '"', "“": "”"}[mark]
    return f"{mark}{small} {body}{close}"


def subphrase():
    sep = random.choice([": ", "; ", "? ", "! ", " - ", " — ", " – ", " ― "])
    return f"{normal()}{sep}{random.choice(SMALL)} {normal()}"


def unicode_title():
    count = random.randint(2, 5)
    return " ".join(random.choice(UNICODE_WORDS) for _ in range(count))


def spaced():
    sep = random.choice(["\t", "\u00a0", "\u2006"])
    return sep.join(words(random.randint(2, 4)))


def caps_quote():
    return f"'QUOTE' A {random.choice(WORDS).upper()}"


BUILDERS = [
    normal,
    normal,
    all_caps,
    initials,
    apostrophe,
    mc_name,
    honorific,
    hostname,
    interior,
    slash,
    hyphen,
    acronym,
    ordinal,
    quoted,
    subphrase,
    unicode_title,
    spaced,
    caps_quote,
]


def random_title():
    return random.choice(BUILDERS)()


def plant(titles):
    slots = random.sample(range(len(titles)), len(CANONICAL))
    for slot, example in zip(slots, CANONICAL):
        titles[slot] = example
    return titles


def generate(count):
    titles = [random_title() for _ in range(count)]
    return plant(titles)


def write_pair(inputs_name, expected_name, titles):
    if len(titles) != COUNT:
        raise SystemExit(f"{inputs_name} has {len(titles)} titles, expected {COUNT}")
    expected = [titlecase(title) for title in titles]
    for title, result in zip(titles, expected):
        if "\n" in title or "\r" in title or "\n" in result or "\r" in result:
            raise SystemExit("a title or result contains a newline")
    data = DATA
    data.mkdir(parents=True, exist_ok=True)
    (data / inputs_name).write_text("\n".join(titles) + "\n", encoding="utf-8", newline="\n")
    (data / expected_name).write_text("\n".join(expected) + "\n", encoding="utf-8", newline="\n")


def main():
    global titlecase
    random.seed(1)
    sys.path.insert(0, str(TASK_ROOT.parent / "python-titlecase"))
    from titlecase import titlecase as original

    titlecase = original
    public = generate(COUNT)
    hidden = generate(COUNT)
    if public == hidden:
        raise SystemExit("public and hidden titles are identical")
    write_pair("inputs.txt", "expected.txt", public)
    write_pair("hidden_inputs.txt", "hidden_expected.txt", hidden)


if __name__ == "__main__":
    main()
