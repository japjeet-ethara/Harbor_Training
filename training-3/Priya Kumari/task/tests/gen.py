#!/usr/bin/env python3
"""Generate deterministic, diverse titlecase fixtures using the reference."""

import random
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
DATA_DIR = TESTS_DIR / "data"
ORIGINAL = TESTS_DIR.parent.parent.parent / "python-titlecase"

COUNT = 100000

NORMAL_WORDS = [
    "apple", "bridge", "castle", "dancer", "engine", "forest", "garden",
    "harbor", "island", "jacket", "kettle", "lantern", "market", "needle",
    "orange", "palace", "quartz", "river", "silver", "temple", "umbrella",
    "valley", "window", "yellow", "zebra", "report", "history", "music",
    "paper", "captain", "letter", "season", "village", "morning", "copper",
    "silent", "public", "winter", "golden", "planet", "station", "system",
    "camera", "network", "machine", "science", "project", "company",
    "library", "mountain", "ocean", "picture", "computer", "archive",
]

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

APOSTROPHE_STEMS = [
    "grange", "clock", "melveny", "doyle", "amour", "angelo",
    "smith", "jackson", "connor", "wright", "ocean",
]

MC_STEMS = [
    "clelland", "donalds", "tavish", "foo", "bar", "maier",
    "cay", "by", "intosh", "gregor",
]

HOSTS = [
    "example.com", "del.icio.us", "http://foo.com", "iTunes",
    "AT&T", "Q&A", "PPPoE", "www.example.org",
]

ACRONYMS = [
    "cnn", "bbc", "html", "nyt", "st", "tv", "rfc", "sec",
    "NASA", "FBI", "USA", "HTML", "API", "CPU",
]

ORDINALS = ["34th", "3rd", "2nd", "5th", "21st", "101st", "12th"]

PUNCTUATION = [": ", ". ", "; ", "? ", "! ", " — ", " – ", " - "]

QUOTES = ['"', "'", "“", "‘"]

WHITESPACES = ["  ", "   ", "\t", "\u00a0", "\u200a", "\u2006"]

FIXED_CASES = [
    "WASHINGTON, D.C. SHOULD BE FIXED",
    "o'grange l'grange",
    "mcclelland",
    "mr smith and dr jones",
    "this is just an example.com",
    "iTunes should be unmolested",
    "this vs. that",
    "word/word",
    "end-to-end",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "words with all consonants like cnn",
    "hello world",
    "34th",
    "'by the Way, small word at the start but within quotes.'",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "Line number one",
    "and Line three",
    "text\twith\ttabs",
    "the end",
]

def word(rng):
    return rng.choice(NORMAL_WORDS)

def small_word(rng):
    return rng.choice(SMALL_WORDS)

def normal_phrase(rng, minimum=2, maximum=8):
    return " ".join(word(rng) for _ in range(rng.randint(minimum, maximum)))

def small_phrase(rng):
    parts = []
    for _ in range(rng.randint(3, 8)):
        parts.append(small_word(rng) if rng.random() < 0.5 else word(rng))
    return " ".join(parts)

def apostrophe_word(rng):
    prefix = rng.choice(["o", "O", "l", "L", "d", "D"])
    mark = rng.choice(["'", "’"])
    result = prefix + mark + rng.choice(APOSTROPHE_STEMS)
    if rng.random() < 0.35:
        result += "'s"
    return result

def mc_word(rng):
    return rng.choice(["mc", "Mc", "MC"]) + rng.choice(MC_STEMS)

def honorific_phrase(rng):
    title = rng.choice(["mr", "mrs", "ms", "dr", "MR", "MRS", "Dr"])
    return title + " " + word(rng)

def hyphenated(rng):
    parts = []
    for _ in range(rng.randint(2, 4)):
        parts.append(small_word(rng) if rng.random() < 0.45 else word(rng))
    return "-".join(parts)

def slashed(rng):
    parts = []
    for _ in range(rng.randint(2, 3)):
        parts.append(small_word(rng) if rng.random() < 0.45 else word(rng))
    return "/".join(parts)

def initials_phrase(rng):
    head = " ".join(word(rng).upper() for _ in range(rng.randint(2, 5)))
    initials = rng.choice(["D.C.", "A.B", "A.B.", "U.S.A.", "J.R.R."])
    tail = rng.choice(NORMAL_WORDS).upper()
    return f"{head} {initials} {tail}"

def subphrase(rng):
    mark = rng.choice(PUNCTUATION)
    small = rng.choice(["a", "an", "the", "of", "and", "in", "to"])
    return normal_phrase(rng) + mark + small + " " + normal_phrase(rng)

def quoted_small_start(rng):
    opener = rng.choice(QUOTES)
    closer = {"“": "”", "‘": "’", '"': '"', "'": "'"}[opener]
    return opener + small_word(rng) + " " + normal_phrase(rng) + closer

def mixed_whitespace(rng):
    words = [
        small_word(rng) if rng.random() < 0.3 else word(rng)
        for _ in range(rng.randint(2, 6))
    ]

    # Either uniform whitespace throughout or mixed combinations between words
    if rng.random() < 0.5:
        gap = rng.choice(WHITESPACES)
        middle = gap.join(words)
    else:
        parts = [words[0]]
        for w in words[1:]:
            parts.append(rng.choice(WHITESPACES))
            parts.append(w)
        middle = "".join(parts)

    # Optional leading and trailing whitespace variations
    leading = rng.choice(WHITESPACES) if rng.random() < 0.35 else ""
    trailing = rng.choice(WHITESPACES) if rng.random() < 0.35 else ""

    return f"{leading}{middle}{trailing}"

def punctuation_chain(rng):
    pieces = []
    for _ in range(rng.randint(3, 6)):
        pieces.append(
            rng.choice([
                word(rng), small_word(rng), apostrophe_word(rng),
                mc_word(rng), rng.choice(ACRONYMS),
            ])
        )
    return rng.choice(PUNCTUATION).join(pieces)

def composite_title(rng):
    """Combine several independently tricky features."""
    pieces = []

    pieces.append(rng.choice([
        normal_phrase(rng, 1, 3),
        small_phrase(rng),
        word(rng).upper(),
    ]))

    for _ in range(rng.randint(2, 4)):
        pieces.append(rng.choice([
            small_word(rng),
            apostrophe_word(rng),
            mc_word(rng),
            honorific_phrase(rng),
            hyphenated(rng),
            slashed(rng),
            rng.choice(HOSTS),
            rng.choice(ACRONYMS),
            rng.choice(ORDINALS),
            initials_phrase(rng),
            quoted_small_start(rng),
            subphrase(rng),
        ]))

    if rng.random() < 0.5:
        pieces.append(normal_phrase(rng, 1, 3))

    return " ".join(pieces)

def make_title(rng):
    # Balanced generation modes. Each mode is sampled independently.
    mode = rng.randrange(11)

    if mode == 0:
        return normal_phrase(rng)

    if mode == 1:
        return small_phrase(rng)

    if mode == 2:
        return normal_phrase(rng).upper()

    if mode == 3:
        return rng.choice(FIXED_CASES)

    if mode == 4:
        return subphrase(rng)

    if mode == 5:
        return hyphenated(rng)

    if mode == 6:
        return slashed(rng)

    if mode == 7:
        return punctuation_chain(rng)

    if mode == 8:
        return quoted_small_start(rng)

    if mode == 9:
        return mixed_whitespace(rng)

    return composite_title(rng)

def generate(count, seed):
    rng = random.Random(seed)
    titles = []

    for _ in range(count):
        title = make_title(rng)
        title = title.replace("\r", " ").replace("\n", " ")
        titles.append(title)

    return titles

def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")

def expect(lines, titlecase):
    return [titlecase(line) for line in lines]

def main():
    sys.path.insert(0, str(ORIGINAL))
    from titlecase import titlecase

    visible = generate(COUNT, seed=1)
    hidden = generate(COUNT, seed=2)

    write_lines(DATA_DIR / "inputs.txt", visible)
    write_lines(DATA_DIR / "hidden_inputs.txt", hidden)
    write_lines(DATA_DIR / "expected.txt", expect(visible, titlecase))
    write_lines(DATA_DIR / "hidden_expected.txt", expect(hidden, titlecase))

if __name__ == "__main__":
    main()