#!/usr/bin/env python3
"""Generate deterministic titlecase fixtures.

The vendored python-titlecase tree has no NOTES.md. Documented inputs are
taken from README.rst and titlecase/tests.py (the package's own edge-case
list). Expected lines are produced only by calling titlecase().
"""

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "environment" / "python-titlecase"
sys.path.insert(0, str(PACKAGE))

from titlecase import titlecase  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent / "data"
COUNT = 2000

# Inputs published by the library. Expected text is never stored here.
# The multiline package case is omitted because each fixture line must
# stay a single record.
DOCUMENTED = (
    "",
    "this is a test",
    "THIS IS A TEST",
    "this is a TEST",
    "a thing",
    "make me a title",
    "Can pipe and/or whatever else",
    "I LOVE TCP",
    "a simple tcp and udp wrapper",
    "word/word",
    "a title and/or string",
    "dance with me/let’s face the music and dance",
    "a-b end-to-end two-not-three/three-by-four/five-and",
    "34th 3rd 2nd",
    "Q&A with steve jobs: 'that's what happens in technology'",
    "What is AT&T's problem?",
    "Apple deal with AT&T falls through",
    "Words with all consonants like cnn are acronyms",
    "this v that",
    "this v. that",
    "this vs that",
    "this vs. that",
    "The SEC's Apple probe: what you need to know",
    "'by the Way, small word at the start but within quotes.'",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'",
    'sub-phrase with a small word in quotes: "a trick, perhaps?"',
    "Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?",
    "Hyphen Delimited Sub-Phrase With a Small Word in Quotes - 'a Trick, Perhaps?'",
    'Hyphen Delimited sub-phrase with a small word in quotes - "a trick, perhaps?"',
    "Snakes on a Plane - The TV Edit - The Famous Line",
    "Starting an Em Dash Delimited Sub-Phrase With a Small Word — a Trick, Perhaps?",
    "Em Dash Delimited Sub-Phrase With a Small Word in Quotes — 'a Trick, Perhaps?'",
    'Em Dash Delimited sub-phrase with a small word in quotes — "a trick, perhaps?"',
    "Snakes on a Plane — The TV Edit — The Famous Line",
    "EPISODE 7 — THE FORCE AWAKENS",
    "episode 7 – The force awakens",
    "THE CASE OF X ≤ 7",
    "the case of X ≤ 7",
    '"Nothing to Be Afraid of?"',
    '"Nothing to be Afraid Of?"',
    "2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'",
    "this is just an example.com",
    "this is something listed on del.icio.us",
    "iTunes should be unmolested",
    "reading between the lines of steve jobs’s ‘thoughts on music’",
    "seriously, ‘repair permissions’ is voodoo",
    "generalissimo francisco franco: still dead; kieren McCarthy: still a jackass",
    "O'Reilly should be untouched",
    "my name is o'reilly",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "Mr McTavish went to MacDonalds",
    "this is http://foo.com",
    "mac mc MAC MC machine",
    "FOO BAR 5TH ST",
    "foo bar 5th st",
    "l'grange l'grange l'Grange l'Grange",
    "L'grange L'grange L'Grange L'Grange",
    "l'GranGe",
    "o'grange O'grange o'Grange O'Grange",
    "o'grange's O'grange's o'Grange's O'Grange's",
    "O'GranGe",
    "o'melveny/o'doyle o'Melveny/o'doyle O'melveny/o'doyle o'melveny/o'Doyle o'melveny/O'doyle",
    "mccay-mcbut-mcdo mcdonalds/mcby",
    "oblon, spivak, mcclelland, maier & neustadt",
    "Mcoblon, spivak, mcclelland, mcmaier, & mcneustadt",
    "mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar",
    "'QUOTE' A GREAT",
    "‘QUOTE’ A GREAT",
    "“YOUNG AND RESTLESS”",
    "EL NIÑO A ARRIVÉ HIER",
    "YEA NO",
    "ÝÆ ÑØ",
    "yea no",
    "ýæ ñø",
    "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
    "a mix\u00a0of\tdifferent\u200aspace\u2006characters",
    "Line number one",
    "and Line three",
    "Leading blank",
    "Multi-blank",
    "Trailing Blank",
    "text\twith\ttabs",
    "text\u00a0with\u00a0nonbreaking\u00a0spaces",
)

# Same rules, different sentences, so the hidden file is not a copy.
HIDDEN_ANCHORS = (
    "an owl and a fox in the glen",
    "by the river vs the open sea",
    "v. the statute in a later chapter",
    "via the old road to the harbor",
    "state-of-the-art end-to-end design",
    "read/write and/or input/output",
    "o'brien met l'equipe and d'angelo",
    "mrs mcintyre and dr mcleod",
    "MR MS MSS DR AT THE GATE",
    "notes from A.B. and N.Y. office",
    "the iPhone and eBay AT&T store",
    "question: a small start?",
    "aside — an extra clause",
    "pause – a short break",
    "list ‒ an item here",
    "bar ― a final mark",
    "  spaced   title  ",
    "ALL CAPS LINE ABOUT THE CNN HTML",
    "keep the short st and the long html",
    "EL NIÑO VISITS THE CAFÉ",
    "5th and 34th st west",
    "visit example.com before noon",
    "see http://example.com/docs today",
    "Q&A: an answer for later",
    "'the quote' sits at the start",
    "mcfoo-mcbar and mcdonalds/mcby today",
    "O'Hara's l'grange and d'Artagnan",
    "Mr. and Mrs. Quinn of D.C.",
    "iTunes OmniFocus and MacDonalds remain",
    "“a quoted and small phrase”",
    "WHAT IS AT&T DOING IN D.C.",
    "this is a NASA memo",
    "foo\tbar\tbaz and a tail",
    "mix\u2006of\u200athin spaces and the end",
    "nothing to be afraid of",
    "a-b c-d and e-f-g",
    "word/word/word and/or more",
    "episode 3 — the hidden cut",
    "ÝÆ AND ÑØ AGAIN",
    "yea and no for the record",
)

SMALL = (
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "by",
    "en",
    "for",
    "if",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "v",
    "v.",
    "via",
    "vs",
    "vs.",
)

LEXICON = (
    "apple",
    "bridge",
    "canvas",
    "delta",
    "ember",
    "falcon",
    "garden",
    "harbor",
    "island",
    "junction",
    "kernel",
    "lantern",
    "meadow",
    "north",
    "orbit",
    "prairie",
    "quartz",
    "river",
    "summit",
    "timber",
    "union",
    "valley",
    "willow",
    "yellow",
    "zephyr",
    "report",
    "story",
    "notes",
    "guide",
    "letter",
    "review",
    "chapter",
    "paper",
    "essay",
    "digest",
    "manual",
    "sketch",
    "column",
    "brief",
    "record",
    "update",
    "journal",
    "primer",
    "survey",
    "outline",
    "london",
    "paris",
    "oslo",
    "lima",
    "cairo",
    "delhi",
    "accra",
    "quito",
    "hanoi",
    "suva",
)

SUBPHRASE_MARKS = (": ", ". ", "; ", "? ", "! ", " - ", " — ", " – ", " ‒ ", " ― ")
APOS = ("o'", "l'", "d'", "O'", "L'", "D'", "o‘", "l‘", "d‘")
WHITESPACE = ("  ", "\t", "\u00a0", "\u2006", "\u200a", " \t ")


def _word(rng):
    return rng.choice(LEXICON)


def _small(rng):
    return rng.choice(SMALL)


def _case(text, rng, allow_upper=True):
    roll = rng.randrange(4)
    if roll == 0:
        return text.lower()
    if roll == 1 and allow_upper:
        return text.upper()
    return text


def build(index, rng):
    """Build one single-line title. index keeps the result unique."""
    left = _word(rng)
    mid = _word(rng)
    right = _word(rng)
    small = _small(rng)
    kind = index % 24
    token = str(index)

    if kind == 0:
        text = f"{left} {mid} {right} {token}"
    elif kind == 1:
        text = f"{left} {small} {mid} {token} {right}"
    elif kind == 2:
        text = f"{small} {left} {token} {mid}"
    elif kind == 3:
        text = f"{left} {token} {mid} {small}"
    elif kind == 4:
        text = f"{left}-{small}-{mid} end-to-end {token}"
    elif kind == 5:
        text = f"{left}/{mid} and/or {right}/{token}"
    elif kind == 6:
        text = f"see http://{left}.example.com/{token} for the {small} notes"
    elif kind == 7:
        mark = APOS[index % len(APOS)]
        text = f"{mark}{left} and {mark}{mid}'s {token} file"
    elif kind == 8:
        text = f"mc{left} visited MC{mid.upper()} and Mac{right.capitalize()} {token}"
    elif kind == 9:
        text = f"mr {left} and mrs {mid} met dr {right} and mss {token}"
    elif kind == 10:
        text = f"memo from A.B. {left} in D.C. file {token}"
    elif kind == 11:
        text = f"iTunes and OmniFocus keep the AT&T plan {token}"
    elif kind == 12:
        mark = SUBPHRASE_MARKS[index % len(SUBPHRASE_MARKS)]
        text = f"{left} {token}{mark}{small} {mid}"
    elif kind == 13:
        text = f"'{small} {left}' says \"{mid}\" {token}"
    elif kind == 14:
        text = f"{left} cnn html tcp and st {token}"
    elif kind == 15:
        gap = WHITESPACE[index % len(WHITESPACE)]
        text = f"{gap}{left}{gap}{small}{gap}{mid}{gap}{token}{gap}"
    elif kind == 16:
        text = f"{left} {small} {mid} {right} {token}".upper()
    elif kind == 17:
        text = f"el niño {left} arrivé at the café {token}"
    elif kind == 18:
        text = f"{token}th street and 3rd {left} avenue"
    elif kind == 19:
        text = f"{left} listed on del.icio.us page {token}"
    elif kind == 20:
        text = f"Q&A on {left} & {mid} {token}"
    elif kind == 21:
        text = f"this is a {mid.upper()} {left} {token}"
    elif kind == 22:
        text = f"mc{left}-bar MC{mid.upper()}-BAR mc{left}-mc{right} {token}"
    else:
        text = f"({left}) [{token}] {{the {small} {mid}}}"

    if kind not in (15, 16):
        text = _case(text, rng, allow_upper=(kind not in (10, 11, 21)))
    if "\n" in text or "\r" in text:
        raise RuntimeError(f"builder produced a broken line at {index}")
    return text


def _acceptable(text):
    if "\n" in text or "\r" in text:
        return False
    output = titlecase(text)
    if "\n" in output or "\r" in output:
        return False
    return True


def collect(anchors, count, blocked, start):
    chosen = []
    seen = set(blocked)
    for text in anchors:
        if text in seen or not _acceptable(text):
            continue
        chosen.append(text)
        seen.add(text)
    index = start
    while len(chosen) < count:
        text = build(index, random)
        index += 1
        if text in seen or not _acceptable(text):
            continue
        chosen.append(text)
        seen.add(text)
        if index > start + count * 20:
            raise RuntimeError("could not assemble enough unique titles")
    if len(chosen) != count:
        raise RuntimeError(f"expected {count} titles, collected {len(chosen)}")
    return chosen


def _require_rules(label, lines):
    blob_lower = "\n".join(lines).lower()
    checks = {
        "small word": any(f" {word} " in f" {line.lower()} " for line in lines for word in ("and", "the", "of", "vs")),
        "hyphen": "-" in blob_lower,
        "slash": "/" in blob_lower,
        "apostrophe": "'" in blob_lower or "‘" in blob_lower or "’" in blob_lower,
        "mc/mac": "mc" in blob_lower or "mac" in blob_lower,
        "honorific": any(word in blob_lower.split() for word in ("mr", "mrs", "ms", "dr", "mr.", "mrs.")),
        "initials": "a.b" in blob_lower or "d.c" in blob_lower,
        "internal capital": any(any(c.islower() and d.isupper() for c, d in zip(line, line[1:])) for line in lines),
        "punctuation": any(mark in blob_lower for mark in (":", "—", "–", "?", "!", ";")),
        "whitespace": any(any(ch.isspace() and ch != " " for ch in line) or "  " in line for line in lines),
        "uppercase line": any(line.isupper() and any(ch.isalpha() for ch in line) for line in lines),
        "consonant acronym": any(word in blob_lower.split() for word in ("cnn", "html", "tcp")),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError(f"{label} is missing rule coverage: {', '.join(missing)}")


def _write(path, lines):
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="\n")


def _read_back(path):
    text = path.read_text(encoding="utf-8")
    if "\r" in text:
        raise RuntimeError(f"{path} contains a carriage return")
    return text.splitlines()


def main():
    random.seed(1)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    visible = collect(DOCUMENTED, COUNT, blocked=(), start=0)
    hidden = collect(HIDDEN_ANCHORS, COUNT, blocked=set(visible), start=1_000_000)
    random.shuffle(visible)
    random.shuffle(hidden)

    if len(set(visible)) != COUNT or len(set(hidden)) != COUNT:
        raise RuntimeError("a dataset contains duplicate titles")
    if set(visible) == set(hidden) or set(visible) & set(hidden):
        raise RuntimeError("visible and hidden datasets are not different")

    visible_out = [titlecase(line) for line in visible]
    hidden_out = [titlecase(line) for line in hidden]
    for label, src, out in (
        ("visible", visible, visible_out),
        ("hidden", hidden, hidden_out),
    ):
        if len(out) != COUNT:
            raise RuntimeError(f"{label} output count is {len(out)}")
        for item in src + out:
            if "\n" in item or "\r" in item:
                raise RuntimeError(f"{label} record contains a newline")

    _require_rules("visible", visible)
    _require_rules("hidden", hidden)

    inputs_path = DATA_DIR / "inputs.txt"
    expected_path = DATA_DIR / "expected.txt"
    hidden_inputs_path = DATA_DIR / "hidden_inputs.txt"
    hidden_expected_path = DATA_DIR / "hidden_expected.txt"
    _write(inputs_path, visible)
    _write(expected_path, visible_out)
    _write(hidden_inputs_path, hidden)
    _write(hidden_expected_path, hidden_out)

    written = {
        "visible inputs": _read_back(inputs_path),
        "visible outputs": _read_back(expected_path),
        "hidden inputs": _read_back(hidden_inputs_path),
        "hidden outputs": _read_back(hidden_expected_path),
    }
    for name, lines in written.items():
        if len(lines) != COUNT:
            raise RuntimeError(f"{name} wrote {len(lines)} lines")
        print(f"{name}: {len(lines)}")


if __name__ == "__main__":
    main()
