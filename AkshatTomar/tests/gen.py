#!/usr/bin/env python3
"""Generate deterministic titlecase fixtures from the original Python implementation."""

import random
import sys
from pathlib import Path

sys.dont_write_bytecode = True

TASK_ROOT = Path(__file__).resolve().parents[1]
PY_REPO = (TASK_ROOT / "../python-titlecase").resolve()

COUNT = 2000
DATA_DIR = Path(__file__).resolve().parent / "data"

SMALL = [
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
]

NORMAL = [
    "apple",
    "market",
    "summer",
    "bridge",
    "river",
    "light",
    "stone",
    "garden",
    "paper",
    "music",
    "history",
    "orange",
    "silver",
    "quiet",
    "yellow",
    "window",
    "forest",
    "ocean",
    "letter",
    "morning",
    "castle",
    "planet",
    "harbor",
    "copper",
    "meadow",
    "village",
    "captain",
    "winter",
    "golden",
    "silent",
    "public",
    "private",
    "second",
    "third",
    "north",
    "south",
    "eastern",
    "western",
    "little",
    "common",
    "modern",
    "ancient",
    "simple",
    "final",
    "early",
    "later",
    "open",
    "closed",
]

HONORIFICS = ["mr", "mrs", "ms", "dr", "Mr", "MRS", "MS", "Dr"]
MC_TAILS = [
    "clelland",
    "donald",
    "gregor",
    "intyre",
    "carthy",
    "kenna",
    "leod",
    "tavish",
    "mahon",
    "namara",
    "cormick",
    "pherson",
]
MC_PREFIXES = ["mc", "Mc", "MC"]
APOS_PREFIXES = ["d", "l", "o", "D", "L", "O"]
APOS_STEMS = [
    "grange",
    "angelo",
    "amico",
    "oliveira",
    "artagnan",
    "melveny",
    "doyle",
    "reilly",
    "brien",
    "connor",
    "hare",
    "neil",
]
APOS_MARKS = ["'", "\u2018"]
MIXED = [
    "iTunes",
    "eBay",
    "iPhone",
    "MacBook",
    "YouTube",
    "LinkedIn",
    "PowerPoint",
    "JavaScript",
    "OmniFocus",
    "OpenSSL",
    "IPv4",
    "FedEx",
]
ACRONYMS = ["cnn", "html", "gps", "nfl", "bbc", "rss", "lcd", "ftp", "sql", "pdf", "css", "php"]
SHORT_CONSONANTS = ["st", "rd", "nd", "th"]
INITIALISMS = ["d.c.", "a.b", "u.s.", "n.y.", "u.k."]
DOMAINS = ["example.com", "del.icio.us", "foo.com", "news.example.com", "bar.org"]
SUBPHRASE_MARKS = [":", ".", ";", "?", "!", "-", "\u2013", "\u2012", "\u2014", "\u2015"]

CATEGORIES = [
    "normal",
    "small",
    "apostrophe",
    "mc",
    "honorific",
    "url",
    "domain",
    "mixed",
    "acronym",
    "slash",
    "hyphen",
    "upper",
    "subphrase",
    "blank",
    "whitespace",
    "combo",
]


def word():
    return random.choice(NORMAL)


def words(count):
    return [word() for _ in range(count)]


def join(parts):
    return " ".join(parts)


def apos_word():
    token = random.choice(APOS_PREFIXES) + random.choice(APOS_MARKS) + random.choice(APOS_STEMS)
    if random.random() < 0.35:
        token += "'s"
    return token


def mc_name():
    return random.choice(MC_PREFIXES) + random.choice(MC_TAILS)


def url():
    host = random.choice(DOMAINS)
    scheme = random.choice(["http://", "https://"])
    path = random.choice(["", "/bar", "/a/b", "/index.html"])
    return scheme + host + path


def slash_word():
    pieces = [word(), random.choice(SMALL), word()]
    if random.random() < 0.5:
        pieces.append(word())
    return "/".join(pieces)


def hyphen_word():
    pieces = [word(), random.choice(SMALL), word()]
    if random.random() < 0.4:
        pieces = [word(), word()]
    return "-".join(pieces)


def quoted(token):
    mark = random.choice(["'", '"', "\u2018", "\u201c"])
    closing = {"'": "'", '"': '"', "\u2018": "\u2019", "\u201c": "\u201d"}[mark]
    return f"{mark}{token}{closing}"


def build(category, index):
    if category == "blank":
        return ""

    if category == "whitespace":
        left = word()
        right = word()
        forms = [
            f"{left}\t{right}",
            f"{left}  {right}",
            f"  {left} {right}",
            f"{left} {right}  ",
            f"{left}\t\t{random.choice(SMALL)}\t{right}",
            " " * (1 + index % 4),
            "\t",
            f"\t{left}\t",
            f"{left} \t {right}",
        ]
        return forms[index % len(forms)]

    if category == "normal":
        return join(words(random.randint(3, 7)))

    if category == "small":
        focus = SMALL[index % len(SMALL)]
        return join([word(), focus, word(), random.choice(SMALL), word()])

    if category == "apostrophe":
        return join([word(), apos_word(), random.choice(SMALL), apos_word(), word()])

    if category == "mc":
        return join([word(), mc_name(), random.choice(SMALL), mc_name(), word()])

    if category == "honorific":
        return join(
            [random.choice(HONORIFICS), word(), random.choice(SMALL), word(), word()]
        )

    if category == "url":
        return join([word(), random.choice(SMALL), url(), word()])

    if category == "domain":
        return join([word(), random.choice(SMALL), random.choice(DOMAINS), word()])

    if category == "mixed":
        return join([word(), random.choice(MIXED), random.choice(SMALL), random.choice(MIXED)])

    if category == "acronym":
        return join(
            [
                word(),
                random.choice(ACRONYMS),
                random.choice(SMALL),
                random.choice(SHORT_CONSONANTS),
                word(),
            ]
        )

    if category == "slash":
        return join([word(), slash_word(), random.choice(SMALL), word()])

    if category == "hyphen":
        return join([word(), hyphen_word(), random.choice(SMALL), hyphen_word()])

    if category == "upper":
        parts = [
            word(),
            random.choice(SMALL),
            random.choice(INITIALISMS),
            word(),
            random.choice(HONORIFICS),
            random.choice(ACRONYMS),
            word(),
        ]
        return join(parts).upper()

    if category == "subphrase":
        mark = SUBPHRASE_MARKS[index % len(SUBPHRASE_MARKS)]
        head = join(words(random.randint(2, 4)))
        tail = join([SMALL[index % len(SMALL)], word(), word()])
        line = f"{head}{mark} {tail}"
        if random.random() < 0.5:
            line = f"{quoted(word())} {line}"
        return line

    # combo: normal words plus every tricky shape on one line
    mark = random.choice(SUBPHRASE_MARKS)
    return join(
        [
            word(),
            random.choice(HONORIFICS),
            mc_name(),
            random.choice(SMALL),
            apos_word(),
            random.choice(MIXED),
            random.choice(ACRONYMS),
            hyphen_word(),
            slash_word(),
            random.choice(DOMAINS),
            url(),
            f"{mark} {random.choice(SMALL)}",
            word(),
        ]
    )


def collect(count, banned):
    lines = []
    attempts = 0
    while len(lines) < count:
        attempts += 1
        if attempts > count * 100:
            raise RuntimeError("could not generate enough distinct titles")
        category = CATEGORIES[len(lines) % len(CATEGORIES)]
        line = build(category, len(lines))
        if "\n" in line or "\r" in line:
            continue
        if line.strip() and line in banned:
            continue
        lines.append(line)
        if line.strip():
            banned.add(line)
    return lines


def answers(lines):
    sys.path.insert(0, str(PY_REPO))
    from titlecase import titlecase

    results = []
    for line in lines:
        result = titlecase(line)
        if not isinstance(result, str):
            raise TypeError("titlecase() did not return a string")
        if "\n" in result or "\r" in result:
            raise RuntimeError("titlecase() returned an embedded newline")
        results.append(result)
    return results


def write_lines(path, lines):
    text = "".join(f"{line}\n" for line in lines)
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    random.seed(1)
    banned = set()
    visible = collect(COUNT, banned)
    hidden = collect(COUNT, banned)
    if visible == hidden:
        raise RuntimeError("visible and hidden inputs are identical")
    visible_content = {line for line in visible if line.strip()}
    hidden_content = {line for line in hidden if line.strip()}
    if visible_content & hidden_content:
        raise RuntimeError("visible and hidden inputs share a non-blank line")

    visible_expected = answers(visible)
    hidden_expected = answers(hidden)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_lines(DATA_DIR / "inputs.txt", visible)
    write_lines(DATA_DIR / "expected.txt", visible_expected)
    write_lines(DATA_DIR / "hidden_inputs.txt", hidden)
    write_lines(DATA_DIR / "hidden_expected.txt", hidden_expected)

    for name, lines in (
        ("inputs.txt", visible),
        ("expected.txt", visible_expected),
        ("hidden_inputs.txt", hidden),
        ("hidden_expected.txt", hidden_expected),
    ):
        print(f"{name} {len(lines)}")


if __name__ == "__main__":
    main()
