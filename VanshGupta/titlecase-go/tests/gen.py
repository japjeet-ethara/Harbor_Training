#!/usr/bin/env python3
"""Generate deterministic titlecase fixtures.

Expected files are produced only by calling the original Python titlecase().
"""

import random
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(__file__).resolve().parent / "data"
TITLECASE_ROOT = (TASK_ROOT / ".." / "python-titlecase").resolve()

COUNT = 2000

# Ordinary words. Tricky patterns below come from the NOTES.md rules.
NORMAL_WORDS = [
    "apple", "river", "market", "stone", "garden", "bridge", "silver",
    "window", "letter", "summer", "winter", "orange", "purple", "yellow",
    "candle", "forest", "mountain", "harbor", "captain", "violin", "pencil",
    "castle", "button", "mirror", "pocket", "village", "island", "valley",
    "morning", "evening", "picture", "language", "history", "science",
    "people", "family", "friend", "school", "office", "street", "flower",
    "shadow", "copper", "basket", "camera", "dragon", "eagle", "falcon",
    "guitar", "hammer", "jacket", "kettle", "lemon", "needle", "ocean",
    "planet", "quartz", "rabbit", "saddle", "timber", "umbrella", "voyage",
    "walnut", "yellow", "zebra", "author", "border", "circle", "diamond",
]

# Small words from NOTES.md rule 13.
SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

# Input examples from NOTES.md. Multiline examples are split into the
# titles they contain so each fixture stays one line.
NOTES_EXAMPLES = [
    "Line number one",
    "and Line three",
    "text\twith\ttabs",
    "a simple tcp and udp wrapper",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "l'grange l'grange l'Grange l'Grange",
    "my name is o'reilly",
    "oblon, spivak, mcclelland, maier & neustadt",
    "Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person",
    "this is just an example.com",
    "iTunes should be unmolested",
    "this v that",
    "a title and/or string",
    "a-b end-to-end two-not-three/three-by-four/five-and",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "Words with all consonants like cnn are acronyms",
    "FOO BAR 5TH ST",
    "reading between the lines of steve jobs\u2019s \u2018thoughts on music\u2019",
    "34th 3rd 2nd",
    "'by the Way, small word at the start but within quotes.'",
    '"Nothing to Be Afraid of?"',
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "this shouldn't",
    "get mangled",
]


def styled_word(word):
    style = random.randrange(4)
    if style == 0:
        return word.lower()
    if style == 1:
        return word.upper()
    if style == 2:
        return word.capitalize()
    return word


def normal_phrase(count=None):
    if count is None:
        count = random.randint(2, 6)
    return " ".join(styled_word(random.choice(NORMAL_WORDS)) for _ in range(count))


def tricky_fragment():
    """One fragment that exercises a NOTES.md rule."""
    kind = random.randrange(24)
    if kind == 0:
        # Rules 1 and 2: the non-blank lines of the blank-line example.
        return random.choice(["Line number one", "and Line three"])
    if kind == 1:
        # Rule 3: tabs and other space characters stay between words.
        words = [random.choice(NORMAL_WORDS) for _ in range(3)]
        separator = random.choice(["\t", "\u00a0", "\u2003", "  "])
        return separator.join(words)
    if kind == 2:
        # Rule 4 uses the same tabbed input under a non-default option.
        return "text\twith\ttabs"
    if kind == 3:
        # Rule 5: the callback example, generated with no callback.
        return "a simple tcp and udp wrapper"
    if kind == 4:
        # Rule 6: dotted initials on an all-caps line.
        initials = random.choice(["D.C.", "U.S.", "A.B", "N.Y.", "D.C"])
        words = [random.choice(NORMAL_WORDS).upper() for _ in range(3)]
        return " ".join([words[0] + ",", initials, words[1], words[2]])
    if kind == 5:
        # Rule 7: d' / l' plus an apostrophe, optional 's.
        lead = random.choice(["d", "D", "l", "L"])
        apostrophe = random.choice(["'", "\u2018"])
        stem = random.choice(["grange", "amour", "Grange", "artagnan"])
        word = lead + apostrophe + stem
        if random.random() < 0.4:
            word += "'s"
        return word
    if kind == 6:
        # Rule 8: leading o before the apostrophe.
        apostrophe = random.choice(["'", "\u2018"])
        stem = random.choice(["reilly", "brien", "Reilly", "malley"])
        return "o" + apostrophe + stem
    if kind == 7:
        # Rule 9: Mc / mc / MC and at least two more word characters.
        prefix = random.choice(["Mc", "mc", "MC"])
        rest = random.choice(["clelland", "donald", "gregor", "intosh", "kenzie"])
        return prefix + rest
    if kind == 8:
        # Rule 10: honorifics. Mss is in the NOTES.md example.
        return random.choice(["m", "mr", "mrs", "ms", "dr", "MR", "Mrs", "Dr", "Mss"])
    if kind == 9:
        # Rule 11: a letter, a period, and another letter.
        return random.choice(NORMAL_WORDS) + "." + random.choice(["com", "org", "net"])
    if kind == 10:
        # Rule 12: a capital later in the word, on a line that has lowercase.
        return random.choice(["iTunes", "iPhone", "macOS", "eBay", "YouTube"])
    if kind == 11:
        # Rule 13: a small word between ordinary words.
        return " ".join([
            random.choice(NORMAL_WORDS),
            random.choice(SMALL_WORDS),
            random.choice(NORMAL_WORDS),
        ])
    if kind == 12:
        # Rule 14: split on / unless the word contains //.
        if random.random() < 0.7:
            left = random.choice(SMALL_WORDS + NORMAL_WORDS)
            right = random.choice(SMALL_WORDS + NORMAL_WORDS)
            return left + "/" + right
        return "http://example.com/docs"
    if kind == 13:
        # Rule 15: split on each hyphen.
        parts = [
            random.choice(SMALL_WORDS + NORMAL_WORDS)
            for _ in range(random.randint(2, 4))
        ]
        return "-".join(parts)
    if kind == 14:
        # Rule 16: a line with no lowercase letters.
        words = [random.choice(NORMAL_WORDS).upper() for _ in range(4)]
        words.insert(1, random.choice(["AND", "OF", "THE", "TO"]))
        return " ".join(words)
    if kind == 15:
        # Rule 17: more than two letters, consonants only. Y is a vowel.
        consonants = "bcdfghjklmnpqrstvwxz"
        length = random.randint(3, 5)
        return "".join(random.choice(consonants) for _ in range(length))
    if kind == 16:
        # Rule 18: a consonant-only word of one or two letters.
        return random.choice(["st", "ST", "ft", "mt", "bl", "b"])
    if kind == 17:
        # Rule 19: leading punctuation, then a letter.
        mark = random.choice(["'", '"', "\u2018", "\u201c", "("])
        return mark + random.choice(NORMAL_WORDS)
    if kind == 18:
        # Rule 20: a digit is the first word character, so the rest stays put.
        number = random.choice([1, 2, 3, 4, 21, 22, 23, 34])
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
        if 10 <= number % 100 <= 20:
            suffix = "th"
        return str(number) + suffix
    if kind == 19:
        # Rule 21: a small word at the start, including after punctuation.
        small = random.choice(SMALL_WORDS)
        if random.random() < 0.5:
            return random.choice(["'", '"', "\u2018"]) + small
        return small
    if kind == 20:
        # Rule 22: a small word at the end, punctuation allowed after it.
        return random.choice(SMALL_WORDS) + random.choice(["", "?", "!", ".", ","])
    if kind == 21:
        # Rule 23: a small word after a subphrase marker and a space.
        marker = random.choice([":", ".", ";", "?", "!", "-", "\u2013", "\u2012", "\u2014", "\u2015"])
        small = random.choice(["a", "an", "the", "of", "to", "in", "and"])
        return "phrase" + marker + " " + small
    # Rule 24: each of the two lines in the newline example.
    return random.choice(["this shouldn't", "get mangled"])


def make_title():
    """Mix ordinary words with a NOTES.md example or a generated tricky case."""
    roll = random.random()
    if roll < 0.2:
        return random.choice(NOTES_EXAMPLES)
    if roll < 0.28:
        # Keep all-caps and start/end cases intact as a whole line.
        return tricky_fragment()

    chunks = [normal_phrase(random.randint(1, 4)), tricky_fragment()]
    if random.random() < 0.55:
        chunks.append(tricky_fragment())
    if random.random() < 0.8:
        chunks.append(normal_phrase(random.randint(1, 3)))
    start = random.randrange(len(chunks))
    chunks = chunks[start:] + chunks[:start]
    separator = "\t" if random.random() < 0.08 else " "
    return separator.join(chunks)


def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            if "\n" in line or "\r" in line:
                raise SystemExit("a generated line contains a line break: %r" % (line,))
            handle.write(line + "\n")


def titlecase_lines(titlecase, lines):
    results = []
    for line in lines:
        result = titlecase(line)
        if not isinstance(result, str):
            raise SystemExit("titlecase() did not return a string for %r" % (line,))
        if "\n" in result or "\r" in result:
            raise SystemExit("titlecase() returned a line break for %r" % (line,))
        results.append(result)
    return results


def main():
    random.seed(1)
    sys.path.insert(0, str(TITLECASE_ROOT))
    from titlecase import titlecase

    visible = [make_title() for _ in range(COUNT)]
    hidden = [make_title() for _ in range(COUNT)]
    if visible == hidden:
        raise SystemExit("hidden inputs were identical to the visible inputs")

    write_lines(DATA_DIR / "inputs.txt", visible)
    write_lines(DATA_DIR / "hidden_inputs.txt", hidden)
    write_lines(DATA_DIR / "expected.txt", titlecase_lines(titlecase, visible))
    write_lines(DATA_DIR / "hidden_expected.txt", titlecase_lines(titlecase, hidden))


if __name__ == "__main__":
    main()
