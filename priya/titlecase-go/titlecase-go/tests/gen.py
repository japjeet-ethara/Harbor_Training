#!/usr/bin/env python3
"""Generate deterministic titlecase fixtures.

Expected files are produced by running the original Python titlecase(),
not by hand.
"""

import random
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
DATA_DIR = TESTS_DIR / "data"
# ../python-titlecase relative to the Harbor task directory.
ORIGINAL = TESTS_DIR.parent.parent / "python-titlecase"

COUNT = 2000

# Ordinary vocabulary mixed into every batch of titles.
NORMAL_WORDS = [
    "apple", "bridge", "castle", "dancer", "engine", "forest", "garden",
    "harbor", "island", "jacket", "kettle", "lantern", "market", "needle",
    "orange", "palace", "quartz", "river", "silver", "temple", "umbrella",
    "valley", "window", "yellow", "zebra", "report", "history", "music",
    "paper", "garden", "captain", "letter", "season", "village", "morning",
    "copper", "silent", "public", "winter", "golden",
]

# Small words from the New York Times list, plus v and vs.
SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

# Single-line inputs pasted from the NOTES.md rule list.
RULE_EXAMPLES = [
    "text\twith\ttabs",
    "the end",
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
]

# Recorded NOTES.md outputs. These are inputs here so the original
# titlecase() can supply the real expected line. Multiline samples are
# split so every generated file stays one title per line.
WRONG_EXAMPLES = [
    "Text With Tabs",
    "the End",
    "Washington, D.C. Should Be Fixed",
    "O'Grange l'Grange",
    "McClelland",
    "Mr Smith and Dr Jones",
    "This Is Just an example.com",
    "iTunes Should Be Unmolested",
    "This vs. That",
    "Word/Word",
    "End-to-End",
    "This Is All Caps and Should Be Addressed",
    "Words With All Consonants Like CNN",
    "Hello World",
    "34th 3rd 2nd",
    "'By the Way, Small Word at the Start but Within Quotes.'",
    "Small Word at End Is Nothing to Be Afraid Of",
    "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?",
    "Line Number One",
    "And Line Three",
]

NOTES_EXAMPLES = RULE_EXAMPLES + WRONG_EXAMPLES

APOSTROPHE_STEMS = ["grange", "clock", "melveny", "doyle", "amour", "angelo"]
MC_STEMS = ["clelland", "donalds", "tavish", "foo", "bar", "maier", "cay", "by"]
HOSTS = ["example.com", "del.icio.us", "http://foo.com", "iTunes", "AT&T", "Q&A", "PPPoE"]
ACRONYMS = ["cnn", "bbc", "html", "nyt", "st", "tv", "rfc", "sec"]
ORDINALS = ["34th", "3rd", "2nd", "5th", "21st"]
SUBPHRASE_MARKS = [": ", ". ", "; ", "? ", "! ", " - ", " — ", " – ", " ‒ ", " ― "]


def pick_words(n, pool):
    return [random.choice(pool) for _ in range(n)]


def normal_phrase():
    return " ".join(pick_words(random.randint(2, 8), NORMAL_WORDS))


def small_phrase():
    parts = []
    for _ in range(random.randint(3, 8)):
        pool = SMALL_WORDS if random.random() < 0.45 else NORMAL_WORDS
        parts.append(random.choice(pool))
    return " ".join(parts)


def apostrophe_word():
    prefix = random.choice(["o", "O", "l", "L", "d", "D"])
    mark = random.choice(["'", "‘"])
    word = prefix + mark + random.choice(APOSTROPHE_STEMS)
    if random.random() < 0.35:
        word += "'s"
    return word


def mc_word():
    return random.choice(["mc", "Mc", "MC"]) + random.choice(MC_STEMS)


def honorific_phrase():
    title = random.choice(["mr", "mrs", "ms", "dr", "MR", "MRS", "Dr"])
    return title + " " + random.choice(NORMAL_WORDS)


def hyphenated():
    count = random.randint(2, 4)
    parts = []
    for _ in range(count):
        pool = SMALL_WORDS if random.random() < 0.4 else NORMAL_WORDS
        parts.append(random.choice(pool))
    return "-".join(parts)


def slashed():
    count = random.randint(2, 3)
    parts = []
    for _ in range(count):
        pool = SMALL_WORDS if random.random() < 0.4 else NORMAL_WORDS
        parts.append(random.choice(pool))
    return "/".join(parts)


def initials_phrase():
    head = " ".join(word.upper() for word in pick_words(random.randint(2, 5), NORMAL_WORDS))
    initials = random.choice(["D.C.", "A.B", "A.B.", "U.S.A."])
    tail = random.choice(NORMAL_WORDS).upper()
    return f"{head} {initials} {tail}"


def subphrase():
    mark = random.choice(SUBPHRASE_MARKS)
    small = random.choice(["a", "an", "the", "of", "and"])
    return normal_phrase() + mark + small + " " + normal_phrase()


def quoted_small_start():
    opener = random.choice(["'", "‘", '"', "“"])
    closer = {"'": "'", "‘": "’", '"': '"', "“": "”"}[opener]
    return opener + random.choice(SMALL_WORDS) + " " + normal_phrase() + closer


def mixed_whitespace():
    gap = random.choice(["\t", "\u00a0", "\u200a", "\u2006", "  "])
    return gap.join(pick_words(random.randint(2, 6), NORMAL_WORDS))


def tricky_fragment():
    kind = random.randrange(12)
    if kind == 0:
        return random.choice(NOTES_EXAMPLES)
    if kind == 1:
        return apostrophe_word()
    if kind == 2:
        return mc_word()
    if kind == 3:
        return honorific_phrase()
    if kind == 4:
        return hyphenated()
    if kind == 5:
        return slashed()
    if kind == 6:
        return random.choice(HOSTS)
    if kind == 7:
        return random.choice(ACRONYMS)
    if kind == 8:
        return random.choice(ORDINALS)
    if kind == 9:
        return initials_phrase()
    if kind == 10:
        return quoted_small_start()
    return mixed_whitespace()


def make_title():
    """One title: normal words, or normal words mixed with a tricky case."""
    mode = random.randrange(6)
    if mode == 0:
        return normal_phrase()
    if mode == 1:
        return small_phrase()
    if mode == 2:
        return normal_phrase().upper()
    if mode == 3:
        return random.choice(NOTES_EXAMPLES)
    if mode == 4:
        return subphrase()
    parts = [normal_phrase(), tricky_fragment()]
    if random.random() < 0.5:
        parts.append(random.choice(SMALL_WORDS))
    if random.random() < 0.5:
        parts.append(normal_phrase())
    if random.random() < 0.25:
        parts.append(tricky_fragment())
    return " ".join(parts)


def generate(count):
    titles = []
    for _ in range(count):
        title = make_title().replace("\r", " ").replace("\n", " ")
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
    random.seed(1)
    sys.path.insert(0, str(ORIGINAL))
    from titlecase import titlecase

    visible = generate(COUNT)
    hidden = generate(COUNT)
    write_lines(DATA_DIR / "inputs.txt", visible)
    write_lines(DATA_DIR / "hidden_inputs.txt", hidden)
    write_lines(DATA_DIR / "expected.txt", expect(visible, titlecase))
    write_lines(DATA_DIR / "hidden_expected.txt", expect(hidden, titlecase))


if __name__ == "__main__":
    main()
