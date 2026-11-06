"""Generate fixed titlecase inputs, then expected lines from the original library.

The original package is ../python-titlecase relative to this task. Expected
files are whatever titlecase() returns; this script does not invent them.
"""

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Rules from NOTES.md. The strings below are the uncorrected examples.
SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

# 1. Callback words stay as the callback returned them.
# 2. All-caps initials made of capitals and periods stay as written.
# 3. d'/l'/o' words (straight or curly apostrophe, optional 's).
# 4. Mc / mc / Mac / mac / MC prefix, remainder titlecased.
# 5. Mr, Mrs, Ms, Dr capitalize only the first letter.
# 6. A letter, a period, and a letter stays unchanged.
# 7. An internal capital on a line that is not fully uppercase stays unchanged.
# 8. A small word in the middle of a line is lowercased.
# 9. A single slash is titlecased on each side; a small word there stays lowercase.
# 10. A word containing // stays one word.
# 11. A hyphenated word is titlecased on each side.
# 12. A fully uppercase line is lowercased, then titlecased.
# 13. A consonant-only word longer than two letters is an acronym (y is a vowel).
# 14. Any other word capitalizes its first letter only.
# 15. A small word at the start is capitalized, including after leading punctuation.
# 16. A small word at the end is capitalized, including before trailing punctuation.
# 17. A small word is capitalized after ": ", ". ", "; ", "? ", "! ", or a dash and a space.
# 18. The notes' blank-line phrases (a blank line itself is not emitted; each record is one title).
# 19. Original space characters, including tabs, are kept.
WRONG_EXAMPLES = [
    "a simple tcp and udp wrapper",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "l'grange",
    "mcclelland",
    "mr smith",
    "this is just an example.com",
    "iTunes should be unmolested",
    "this vs that",
    "a title and/or string",
    "this is http://foo.com",
    "end-to-end",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "Words with all consonants like cnn are acronyms",
    "yea no",
    "'by the Way, small word at the start but within quotes.'",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "Line number one",
    "and Line three",
    "text\twith\ttabs",
]

NORMAL_WORDS = [
    "simple", "title", "string", "wrapper", "problem", "words", "line",
    "start", "end", "quotes", "trick", "perhaps", "number", "three",
    "afraid", "nothing", "small", "word", "way", "fixed", "might",
    "addressed", "consonants", "acronyms", "example", "report", "market",
    "history", "garden", "river", "bridge", "yellow", "orange", "quiet",
    "people", "summer", "winter", "monday", "chapter", "notes", "final",
    "tcp", "udp", "washington", "smith", "grange", "clelland", "text",
    "tabs", "unmolested", "caps", "yea", "subphrase", "within",
]


def styled_normal() -> str:
    word = random.choice(NORMAL_WORDS)
    style = random.randrange(3)
    if style == 0:
        return word
    if style == 1:
        return word.upper()
    return word.capitalize()


def tricky() -> str:
    """One token that exercises a NOTES.md rule."""
    rule = random.randrange(16)
    if rule == 0:
        return random.choice(["D.C.", "U.S.", "U.S.A.", "A.B.", "Ph.D"])
    if rule == 1:
        lead = random.choice(list("dloDLO"))
        apos = random.choice(["'", "\u2018"])
        tail = random.choice(["grange", "angelo", "brien", "clock", "neil", "hare"])
        word = f"{lead}{apos}{tail}"
        if random.randrange(3) == 0:
            word += "'s"
        return word
    if rule == 2:
        prefix = random.choice(["Mc", "mc", "Mac", "mac", "MC"])
        rest = random.choice(["clelland", "donald", "arthur", "intosh", "mahon"])
        return prefix + rest
    if rule == 3:
        return random.choice(["mr", "mrs", "ms", "dr", "MR", "Mrs", "Dr"])
    if rule == 4:
        return random.choice(["example.com", "node.js", "e.g", "i.e", "www.bbc.co.uk"])
    if rule == 5:
        return random.choice(["iTunes", "iPhone", "eBay", "YouTube", "macOS"])
    if rule == 6:
        left = random.choice(SMALL_WORDS + ["read", "black", "and"])
        right = random.choice(SMALL_WORDS + ["or", "out", "white"])
        return f"{left}/{right}"
    if rule == 7:
        return random.choice([
            "http://foo.com",
            "https://example.com",
            "http://foo.com/a",
            "https://bbc.co.uk/news",
        ])
    if rule == 8:
        left = random.choice(SMALL_WORDS + ["end", "state", "well", "year"])
        mid = random.choice(SMALL_WORDS + ["to", "of", "known"])
        right = random.choice(["end", "art", "trip"])
        if random.randrange(2) == 0:
            return f"{left}-{mid}-{right}"
        return f"{left}-{mid}"
    if rule == 9:
        return random.choice(["cnn", "bbc", "nfl", "html", "sql", "gym", "tv", "St", "st"])
    if rule == 10:
        return random.choice(["yea", "no", "ok", "hello"])
    if rule == 11:
        return random.choice(["'by", '"the', "(a", "'of", "'vs"])
    if rule == 12:
        return random.choice(NORMAL_WORDS).upper()
    if rule == 13:
        return random.choice(["tcp", "udp", "TCP", "UDP"])
    if rule == 14:
        return "text\twith\ttabs"
    return random.choice(WRONG_EXAMPLES)


def join(parts: list[str]) -> str:
    sep = random.choice([" ", " ", " ", "\t", "  ", "\u00a0"])
    return sep.join(parts)


def make_title() -> str:
    mode = random.randrange(6)
    if mode == 0:
        return random.choice(WRONG_EXAMPLES)
    if mode == 1:
        example = random.choice(WRONG_EXAMPLES)
        left = [styled_normal() for _ in range(random.randint(1, 3))]
        right = [styled_normal() for _ in range(random.randint(1, 3))]
        return join(left + [example] + right)

    parts: list[str] = []
    for _ in range(random.randint(3, 8)):
        roll = random.randrange(10)
        if roll < 4:
            parts.append(styled_normal())
        elif roll < 6:
            parts.append(random.choice(SMALL_WORDS))
        else:
            parts.append(tricky())
    parts.append(styled_normal())
    parts.append(tricky())
    random.shuffle(parts)
    line = join(parts)
    if random.randrange(5) == 0:
        line = line.upper()
    if random.randrange(4) == 0:
        punct = random.choice([": ", ". ", "; ", "? ", "! ", " - ", " \u2013 "])
        line = f"{line}{punct}{random.choice(SMALL_WORDS)} {styled_normal()}"
    if random.randrange(5) == 0:
        line = f"{random.choice(['\'', '\"', '('])}{random.choice(SMALL_WORDS)} {line}"
    if random.randrange(5) == 0:
        line = f"{line} {random.choice(SMALL_WORDS)}{random.choice(['', '.', '!', '?'])}"
    return line


def generate(count: int, seen: set[str]) -> list[str]:
    rows: list[str] = []
    while len(rows) < count:
        line = make_title()
        if line in seen or "\n" in line or "\r" in line:
            continue
        seen.add(line)
        rows.append(line)
    return rows


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            if "\n" in line or "\r" in line:
                raise SystemExit(f"refusing to write a multiline record to {path}")
            handle.write(line)
            handle.write("\n")


def main() -> None:
    candidates = [
        HERE.parent / ".." / "python-titlecase",
        HERE.parent / ".." / "project" / "python-titlecase",
    ]
    source = next(
        (path.resolve() for path in candidates if (path / "titlecase" / "__init__.py").is_file()),
        None,
    )
    if source is None:
        searched = ", ".join(str(path.resolve()) for path in candidates)
        sys.stderr.write(f"original titlecase package not found. Looked in: {searched}\n")
        raise SystemExit(1)
    sys.path.insert(0, str(source))
    from titlecase import titlecase

    random.seed(1)
    seen: set[str] = set()
    inputs = generate(2000, seen)
    hidden = generate(2000, seen)
    if inputs == hidden:
        raise SystemExit("visible and hidden inputs must differ")

    expected = [titlecase(line) for line in inputs]
    hidden_expected = [titlecase(line) for line in hidden]

    data = HERE / "data"
    write_lines(data / "inputs.txt", inputs)
    write_lines(data / "hidden_inputs.txt", hidden)
    write_lines(data / "expected.txt", expected)
    write_lines(data / "hidden_expected.txt", hidden_expected)
    print(f"wrote 2000 lines to {data / 'inputs.txt'} and {data / 'expected.txt'}")
    print(f"wrote 2000 lines to {data / 'hidden_inputs.txt'} and {data / 'hidden_expected.txt'}")


if __name__ == "__main__":
    main()
