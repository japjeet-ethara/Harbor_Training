#!/usr/bin/env python3
"""Deterministic title fixtures for the titlecase-go Harbor task.

Inputs are generated with random.seed(1). Expected lines are produced only by
calling the original python-titlecase titlecase() function.
"""

import random
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO = (TASK_ROOT / "../python-titlecase").resolve()
sys.path.insert(0, str(REPO))

from titlecase import titlecase  # noqa: E402

DATA_DIR = TASK_ROOT / "tests" / "data"
COUNT = 2000

LEXICON = (
    "apple bridge castle market river stone garden silver copper winter summer "
    "captain pilot report system design public secret ancient modern bright "
    "quiet rapid lunar forest ocean valley signal memory packet server client "
    "module parser editor window button canvas north south east west alpha "
    "beta gamma delta paper ink press journal history science music light "
    "shadow flame cloud storm harbor launch archive manual guide protocol "
    "engine buffer socket thread cache index record field column query "
    "planet comet orbit rocket station capsule beacon compass lantern"
).split()

SMALL = ("of", "the", "in", "a", "an", "and", "for", "to", "on", "or", "via", "vs")
ACRONYMS = ("NASA", "HTML", "CNN", "TCP", "FBI", "IBM", "UDP")
HYPHENS = (
    "state-of-the-art",
    "end-to-end",
    "well-known",
    "five-and",
    "decision-making",
    "real-time",
    "mother-in-law",
    "a-b",
    "two-not-three",
)
PUNCT = (
    "Q&A",
    "i.e.",
    "e.g.",
    "U.S.",
    "D.C.",
    "AT&T",
    "3rd",
    "34th",
    "2nd",
    "example.com",
    "del.icio.us",
    "iTunes",
)
URLS = (
    "https://example.com",
    "https://example.com/docs",
    "http://foo.com",
    "https://nasa.gov/html",
    "http://example.com/a/b",
)
EMAILS = (
    "ada@example.com",
    "dev@nasa.gov",
    "qa@example.com",
    "editor@html.test",
)
APOSTROPHES = ("o'reilly", "o'brien", "l'grange", "o'grange's", "d'angelo", "l'GranGe")
MC_NAMES = ("mcgregor", "mctavish", "mcdonald", "McTavish", "macdonald", "mcclelland")

# Fixed single-line cases. The two lists differ so the hidden file is not a copy.
VISIBLE_SPECIAL = (
    "the lord of the rings",
    "a tale of two cities in the rain",
    "THIS IS A TEST",
    "this is a TEST",
    "Words with all consonants like cnn are acronyms",
    "NASA publishes the HTML guide",
    "this is http://foo.com",
    "mail ada@example.com in the morning",
    "end-to-end and state-of-the-art",
    "a title and/or string",
    "o'reilly and l'grange",
    "Mr mcTavish went to MacDonalds",
    "Q&A with steve jobs: 'that's what happens in technology'",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "Small word at end is nothing to be afraid of",
    '"Nothing to Be Afraid of?"',
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "A.B IS FINE",
    "FOO BAR 5TH ST",
    "34th 3rd 2nd",
    "iTunes should be unmolested",
    "this is just an example.com",
    "snakes on a plane — the famous line",
    "EPISODE 7 — THE FORCE AWAKENS",
    "foo//bar in the html spec",
    "a simple tcp and udp wrapper",
    "mac mc MAC MC machine",
    "'by the Way, small word at the start but within quotes.'",
    "the case of X ≤ 7",
    "EL NIÑO A ARRIVÉ HIER",
)

HIDDEN_SPECIAL = (
    "beauty and the beast in the night",
    "OF MICE AND MEN",
    "HTML AND NASA LEAD THE CNN DESK",
    "visit https://example.com/docs in the archive",
    "ping dev@nasa.gov for the html report",
    "well-known five-and decision-making",
    "word/word and north/south",
    "o'brien's l'grange bakery",
    "mcgregor versus mcdonald",
    "hello, world: a new hope",
    "an apple in the garden of the station",
    "this v that",
    "this vs. that",
    "this v. that",
    "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
    "reading between the lines of steve jobs’s ‘thoughts on music’",
    "generalissimo francisco franco: still dead; kieren McCarthy: still a jackass",
    "my name is o'reilly",
    "l'GranGe keeps its inner capital",
    "mccay-mcbut-mcdo mcdonalds/mcby",
    "oblon, spivak, mcclelland, maier & neustadt",
    "(hello world) in the html",
    "ÝÆ ÑØ",
    "ýæ ñø",
    "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
    "dance with me/let’s face the music and dance",
    "a-b end-to-end two-not-three/three-by-four/five-and",
    "THE CASE OF X ≤ 7",
    'sub-phrase with a small word in quotes: "a trick, perhaps?"',
    "sending UDP packets over PPPoE works great",
)


def _words(count):
    return [random.choice(LEXICON) for _ in range(count)]


def _sentence():
    """A normal phrase that still contains a small word."""
    left = _words(random.randint(1, 3))
    right = _words(random.randint(1, 3))
    return " ".join(left + [random.choice(SMALL)] + right)


def make_title(index, specials):
    """One title. index selects the shape; random supplies the words."""
    if index % 40 == 0:
        return specials[(index // 40) % len(specials)]

    kind = index % 7
    if kind == 0:
        title = _sentence()
    elif kind == 1:
        title = " ".join(
            (
                random.choice(SMALL),
                random.choice(LEXICON),
                random.choice(("of", "the", "in")),
                random.choice(LEXICON),
                random.choice(("in", "of", "the")),
                random.choice(LEXICON),
            )
        )
    elif kind == 2:
        title = " ".join(
            (
                random.choice(ACRONYMS),
                random.choice(LEXICON),
                random.choice(SMALL),
                random.choice(("HTML", "NASA", "CNN")),
                random.choice(LEXICON),
            )
        )
    elif kind == 3:
        title = " ".join(
            (
                random.choice(("see", "open", "visit", "read")),
                random.choice(URLS),
                random.choice(SMALL),
                random.choice(LEXICON),
            )
        )
    elif kind == 4:
        title = " ".join(
            (
                random.choice(("mail", "ask", "ping", "copy")),
                random.choice(EMAILS),
                random.choice(SMALL),
                random.choice(LEXICON),
            )
        )
    elif kind == 5:
        title = " ".join(
            (
                random.choice(PUNCT),
                random.choice(("with", "for", "after")),
                random.choice(LEXICON),
                ":",
                random.choice(SMALL),
                random.choice(LEXICON),
            )
        )
    else:
        title = " ".join(
            (
                random.choice(HYPHENS),
                random.choice(SMALL),
                random.choice(HYPHENS),
                random.choice(APOSTROPHES),
                random.choice(MC_NAMES),
            )
        )

    # Some lines are shouted so all-caps behavior is in both files.
    if index % 11 == 0:
        title = title.upper()
    return title


def generate(count, specials):
    lines = [make_title(i, specials) for i in range(count)]
    for line in lines:
        if "\n" in line or "\r" in line:
            raise SystemExit("generated title contains a newline: %r" % line)
    return lines


def write_lines(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_expected(source, dest):
    incoming = source.read_text(encoding="utf-8").splitlines()
    outgoing = []
    for line in incoming:
        result = titlecase(line)
        if "\n" in result or "\r" in result:
            raise SystemExit("titlecase() split a line: %r -> %r" % (line, result))
        outgoing.append(result)
    if len(outgoing) != len(incoming):
        raise SystemExit("line count changed for %s" % source.name)
    write_lines(dest, outgoing)


def main():
    random.seed(1)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    visible = generate(COUNT, VISIBLE_SPECIAL)
    hidden = generate(COUNT, HIDDEN_SPECIAL)
    if visible == hidden:
        raise SystemExit("visible and hidden inputs are identical")

    inputs_path = DATA_DIR / "inputs.txt"
    hidden_inputs_path = DATA_DIR / "hidden_inputs.txt"
    write_lines(inputs_path, visible)
    write_lines(hidden_inputs_path, hidden)
    write_expected(inputs_path, DATA_DIR / "expected.txt")
    write_expected(hidden_inputs_path, DATA_DIR / "hidden_expected.txt")

    print("wrote %s titles in %s" % (COUNT, DATA_DIR))


if __name__ == "__main__":
    main()
