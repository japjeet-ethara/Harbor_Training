#!/usr/bin/env python3
"""Generate deterministic titlecase inputs and expected outputs.

Expected lines are produced only by calling the original Python titlecase()
from ../python-titlecase (relative to this task). Nothing here hard-codes an
answer.

The Input examples in the task's NOTES.md are included as fixed titles.
They are split between the public and hidden sets, each title once.

Tricky cases mixed with ordinary words are the rules the original function
applies, including the ones a naive capitalizer gets wrong:

- ordinary words take a capital first letter
- small words stay lowercase in the middle (a, an, and, as, at, but, by, en,
  for, if, in, of, on, or, the, to, v, v., via, vs, vs.)
- a small word at the start or end is capitalized
- a small word after subphrase punctuation (: . ; ? ! or a dash) is capitalized
- hyphenated words are titlecased piece by piece
- a single slash splits a phrase; http:// and https:// stay whole
- a word with a period between letters (domains) is left unchanged
- a word that already has an internal capital (iTunes, AT&T) is left unchanged
- an all-caps line is normalized, while initials such as D.C. stay as written
- an all-consonant word longer than two letters is an acronym (cnn -> CNN);
  two-letter words such as st are not
- Mac/Mc names take a capital after the prefix
- Mr, Mrs, Ms, and Dr keep that short form
- o', l', and d' apostrophe names follow the special pattern
- leading quotes and punctuation stay, and the first letter is still capitalized
"""

import random
import sys
from pathlib import Path

random.seed(1)

DATA_DIR = Path(__file__).resolve().parent / "data"
# tests/gen.py -> task root -> directory that holds the sibling python-titlecase
ORIGINAL_REPO = Path(__file__).resolve().parents[2] / "python-titlecase"
NOTES_PATH = Path(__file__).resolve().parents[1] / "NOTES.md"
sys.path.insert(0, str(ORIGINAL_REPO))

from titlecase import titlecase  # noqa: E402

WORDS = [
    "apple", "bridge", "castle", "dance", "engine", "forest", "garden",
    "harbor", "island", "journal", "kingdom", "lantern", "music", "night",
    "orange", "planet", "quartz", "river", "silver", "thunder", "umbrella",
    "valley", "window", "yellow", "zebra", "market", "story", "captain",
    "winter", "summer", "paper", "stone", "cloud", "field", "house", "light",
    "dream", "voice", "water", "garden", "circle", "letter", "mirror",
    "north", "south", "east", "west", "public", "private", "golden",
    "silent", "broken", "ancient", "modern", "hidden", "open", "final",
]

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

BREAKS = [": ", "; ", ". ", "? ", "! ", " - ", " — ", " – ", " -- "]

INTERNAL = ["iTunes", "eBay", "AT&T", "OmniFocus", "iPhone", "YouTube", "Q&A"]

ACRONYMS = ["cnn", "html", "nyc", "rss", "ftp", "pdf", "gpl", "sql", "ibm"]

SHORT = ["st", "rd", "ln"]

HONORIFICS = ["mr", "Mr", "mrs", "Mrs", "ms", "Ms", "dr", "Dr", "MR", "DR"]

STEMS = [
    "donald", "donalds", "tavish", "clelland", "maier", "neustadt",
    "foo", "bar", "david", "cay", "intosh", "carthy",
]

APOS = [
    "o'reilly", "o'brien", "o'grange", "o'melveny", "o'doyle",
    "l'grange", "l'amour", "d'angelo", "d'artagnan",
    "O'Reilly", "l'Grange", "o'Grange",
]

DOMAINS = ["example.com", "del.icio.us", "foo.com", "news.example.org"]

UNICODE_LINES = [
    "el niño a arrivé hier",
    "EL NIÑO A ARRIVÉ HIER",
    "crème brûlée and café",
    "ýæ ñø",
    "ÝÆ ÑØ",
]


def vary(word):
    roll = random.randrange(3)
    if roll == 0:
        return word.lower()
    if roll == 1:
        return word.upper()
    if not word:
        return word
    return word[0].upper() + word[1:].lower()


def words(count):
    return [random.choice(WORDS) for _ in range(count)]


def phrase(count=None):
    count = count if count is not None else random.randint(2, 6)
    return " ".join(vary(word) for word in words(count))


def normal():
    return phrase(random.randint(3, 8))


def small_middle():
    return " ".join(
        [
            vary(random.choice(WORDS)),
            random.choice(SMALL),
            vary(random.choice(WORDS)),
            random.choice(SMALL),
            vary(random.choice(WORDS)),
        ]
    )


def small_edges():
    return " ".join(
        [
            random.choice(SMALL),
            phrase(random.randint(2, 4)),
            random.choice(SMALL),
        ]
    )


def subphrase():
    return (
        f"{phrase()}{random.choice(BREAKS)}"
        f"{random.choice(SMALL)} {phrase(random.randint(1, 4))}"
    )


def hyphenated():
    pieces = [
        vary(random.choice(WORDS)),
        random.choice(SMALL),
        vary(random.choice(WORDS)),
    ]
    if random.randrange(2):
        pieces.append(random.choice(SMALL))
    return f"{phrase(random.randint(1, 3))} {'-'.join(pieces)}"


def slashed():
    parts = []
    for _ in range(random.randint(2, 3)):
        if random.randrange(2):
            parts.append(random.choice(SMALL))
        else:
            parts.append(vary(random.choice(WORDS)))
    return f"{phrase(random.randint(1, 3))} {'/'.join(parts)} {vary(random.choice(WORDS))}"


def url():
    scheme = random.choice(["http://", "https://"])
    host = random.choice(DOMAINS)
    tail = random.choice(WORDS)
    return f"{phrase(random.randint(2, 4))} {scheme}{host}/{tail}"


def domain():
    return f"{phrase(random.randint(2, 5))} {random.choice(DOMAINS)}"


def internal_caps():
    return f"{phrase(random.randint(1, 4))} {random.choice(INTERNAL)} {phrase(random.randint(1, 3))}"


def all_caps():
    return phrase(random.randint(3, 7)).upper()


def initials():
    token = random.choice(["D.C.", "U.S.", "A.B.", "U.S.A", "A.B"])
    return f"{phrase(random.randint(2, 4)).upper()} {token} {phrase(random.randint(1, 3)).upper()}"


def acronym():
    return f"{phrase(random.randint(2, 4))} {random.choice(ACRONYMS)} {phrase(random.randint(1, 3))}"


def short_consonants():
    return f"{phrase(random.randint(2, 4))} {random.choice(SHORT)} {phrase(random.randint(1, 3))}"


def mac_mc():
    prefix = random.choice(["mc", "Mc", "mac", "Mac", "MC"])
    name = prefix + random.choice(STEMS)
    if random.randrange(3) == 0:
        name = f"{name}-{random.choice(['mc', 'Mc', 'mac'])}{random.choice(STEMS)}"
    return f"{random.choice(HONORIFICS)} {name} {phrase(random.randint(1, 4))}"


def apostrophe():
    word = random.choice(APOS)
    if random.randrange(4) == 0:
        word += "'s"
    return f"{phrase(random.randint(1, 4))} {word} {phrase(random.randint(1, 3))}"


def quoted():
    opening = random.choice(["'", '"', "‘", "“"])
    closing = {"'": "'", '"': '"', "‘": "’", "“": "”"}[opening]
    inner = f"{random.choice(SMALL)} {phrase(random.randint(2, 5))}"
    return f"{opening}{inner}{closing}"


def ordinals():
    ordinal = random.choice(["34th", "3rd", "2nd", "5th", "21st", "1st"])
    return f"{ordinal} {random.choice(SHORT)} {phrase(random.randint(1, 4))}"


def unicode_title():
    line = random.choice(UNICODE_LINES)
    if random.randrange(2):
        return f"{phrase(random.randint(1, 2))} {line}"
    return line


BUILDERS = [
    (8, normal),
    (3, small_middle),
    (3, small_edges),
    (3, subphrase),
    (2, hyphenated),
    (2, slashed),
    (2, url),
    (2, domain),
    (2, internal_caps),
    (2, all_caps),
    (2, initials),
    (2, acronym),
    (2, short_consonants),
    (2, mac_mc),
    (2, apostrophe),
    (2, quoted),
    (2, ordinals),
    (1, unicode_title),
]

WEIGHTED = []
for weight, builder in BUILDERS:
    WEIGHTED.extend([builder] * weight)


def one_title(seen):
    for _ in range(20):
        title = random.choice(WEIGHTED)()
        title = title.replace("\r", " ").replace("\n", " ").strip()
        if title and title not in seen:
            seen.add(title)
            return title
    title = f"{phrase()} {random.randrange(1_000_000)}"
    seen.add(title)
    return title


def make_titles(count, seen):
    return [one_title(seen) for _ in range(count)]


def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")


def notes_examples():
    """Return each NOTES.md Input example with its characters unchanged."""
    lines = NOTES_PATH.read_text(encoding="utf-8").splitlines()
    examples = []
    index = 0
    while index < len(lines):
        if lines[index].strip() != "Input:":
            index += 1
            continue
        index += 1
        while index < len(lines) and lines[index] == "":
            index += 1
        if index >= len(lines) or not lines[index].startswith("```"):
            raise RuntimeError("NOTES.md Input section is missing a code block")
        index += 1
        block = []
        while index < len(lines) and lines[index].strip() != "```":
            block.append(lines[index])
            index += 1
        if index >= len(lines):
            raise RuntimeError("NOTES.md Input code block is not closed")
        example = "\n".join(block)
        if example:
            examples.append(example)
        index += 1
    if len(examples) < 8:
        raise RuntimeError(
            f"NOTES.md produced {len(examples)} examples; expected at least 8"
        )
    return examples


def fixed_titles(seen):
    """Take NOTES.md examples into the shared set, skipping duplicates."""
    chosen = []
    for title in notes_examples():
        if "\n" in title or "\r" in title:
            raise RuntimeError("NOTES.md example contains a newline")
        if title in seen:
            continue
        seen.add(title)
        chosen.append(title)
    if len(chosen) > 2000:
        raise RuntimeError("NOTES.md has more examples than one dataset can hold")
    return chosen


def expected_for(lines):
    results = []
    for line in lines:
        result = titlecase(line)
        if "\n" in result or "\r" in result:
            raise RuntimeError("titlecase() returned more than one line")
        results.append(result)
    return results


def main():
    seen = set()
    fixed = fixed_titles(seen)
    public_fixed = fixed[0::2]
    hidden_fixed = fixed[1::2]
    public = public_fixed + make_titles(2000 - len(public_fixed), seen)
    hidden = hidden_fixed + make_titles(2000 - len(hidden_fixed), seen)
    if len(public) != 2000 or len(hidden) != 2000:
        raise RuntimeError("expected 2000 public and 2000 hidden inputs")
    if set(public) & set(hidden):
        raise RuntimeError("public and hidden inputs overlap")
    write_lines(DATA_DIR / "inputs.txt", public)
    write_lines(DATA_DIR / "hidden_inputs.txt", hidden)
    write_lines(DATA_DIR / "expected.txt", expected_for(public))
    write_lines(DATA_DIR / "hidden_expected.txt", expected_for(hidden))


if __name__ == "__main__":
    main()
