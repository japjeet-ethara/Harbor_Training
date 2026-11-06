"""Generate deterministic titlecase fixtures from the original Python library.

Inputs are random, but random.seed(1) makes every run identical. Expected files
are produced only by calling titlecase() in ../python-titlecase. Do not paste
expected strings into this script.
"""

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
PY_TITLECASE = HERE.parent.parent / "python-titlecase"

COUNT = 2000

# Single-line inputs cited in NOTES.md. Rules 16 and 17 are about newlines
# inside one titlecase() string, so they are not stored in these line files.
NOTES_INPUTS = [
    "the lord of the rings",
    "a thing of",
    "'by the Way, small word at the start but within quotes.'",
    "this vs. that",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "iTunes should be unmolested",
    "this is http://foo.com",
    "o'grange",
    "l'grange",
    "mccarthy",
    "mr smith and dr jones",
    "a title and/or string",
    "end-to-end",
    "words with all consonants like cnn",
    "foo bar 5th st",
    "34th 3rd 2nd",
    "text\twith\ttabs",
    "a simple tcp and udp wrapper",
]

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

WORDS = [
    "apple", "bridge", "castle", "city", "copper", "evening", "family",
    "forest", "friend", "garden", "harbor", "history", "house", "lantern",
    "letter", "market", "morning", "mountain", "music", "north", "ocean",
    "paper", "people", "public", "quiet", "river", "school", "science",
    "shadow", "silver", "south", "stone", "street", "summer", "thunder",
    "velvet", "window", "winter", "yellow", "bright", "little", "green",
    "lord", "rings", "thing", "trick", "washington", "smith", "jones",
]

BREAKS = [": ", "; ", ". ", "? ", "! ", "- ", "– ", "‒ ", "— ", "― "]
SPACES = ["\t", "\u00a0", "\u2003", "  "]
INITIALS = ["D.C.", "A.B", "A.B.", "U.S.", "N.Y."]
KEPT = ["iTunes", "AT&T", "Q&A", "eBay"]
URLS = ["http://foo.com", "https://example.com/a", "foo.com", "news.bbc.co.uk"]
ACRONYMS = ["cnn", "bbc", "gps", "html", "sql", "ftp", "st", "rd"]
ORDINALS = ["34th", "3rd", "2nd", "5th", "1st", "10th"]
HONORIFICS = ["mr", "mrs", "ms", "dr", "mss", "MR", "DR"]


def phrase(n):
    return " ".join(random.choice(WORDS) for _ in range(n))


def small_middle():
    return f"{phrase(random.randint(1, 3))} {random.choice(SMALL)} {phrase(random.randint(1, 3))}"


def small_first_last():
    return f"{random.choice(SMALL)} {phrase(random.randint(1, 4))} {random.choice(SMALL)}"


def leading_punct():
    opening = random.choice(["'", '"', "(", "“", "‘"])
    closing = random.choice(["'", '"', ")", ".", ""])
    return f"{opening}{random.choice(SMALL)} {phrase(random.randint(2, 5))}{closing}"


def versus():
    return f"{random.choice(WORDS)} {random.choice(['v', 'v.', 'vs', 'vs.', 'via'])} {random.choice(WORDS)}"


def subphrase():
    return (
        f"{phrase(random.randint(2, 5))}"
        f"{random.choice(BREAKS)}"
        f"{random.choice(SMALL)} {phrase(random.randint(1, 4))}"
    )


def all_caps():
    return phrase(random.randint(3, 8)).upper()


def initials():
    return f"{random.choice(WORDS).upper()}, {random.choice(INITIALS)} {phrase(random.randint(2, 5)).upper()}"


def internal_caps():
    return f"{random.choice(KEPT)} {phrase(random.randint(1, 4))}"


def url_or_domain():
    return f"{phrase(random.randint(1, 3))} {random.choice(URLS)}"


def apostrophe():
    letter = random.choice(["d", "o", "l", "D", "O", "L"])
    mark = random.choice(["'", "‘"])
    rest = random.choice(["grange", "artagnan", "clock", "neil"])
    extra = phrase(random.randint(0, 3))
    core = f"{letter}{mark}{rest}"
    return f"{core} {extra}".strip()


def mc_name():
    prefix = random.choice(["mc", "MC", "Mc"])
    rest = random.choice(["carthy", "donald", "intyre", "gregor"])
    extra = phrase(random.randint(0, 3))
    return f"{prefix}{rest} {extra}".strip()


def honorific():
    return (
        f"{random.choice(HONORIFICS)} {random.choice(WORDS)} and "
        f"{random.choice(['mr', 'mrs', 'ms', 'dr'])} {random.choice(WORDS)}"
    )


def slash():
    left = random.choice(WORDS + SMALL)
    right = random.choice(WORDS + SMALL)
    tail = phrase(random.randint(0, 2))
    return f"{phrase(random.randint(1, 3))} {left}/{right} {tail}".strip()


def hyphen():
    if random.random() < 0.5:
        parts = [random.choice(WORDS), random.choice(SMALL), random.choice(WORDS)]
    else:
        parts = [random.choice(WORDS) for _ in range(random.randint(2, 3))]
    tail = phrase(random.randint(0, 2))
    head = phrase(random.randint(0, 2))
    return f"{head} {'-'.join(parts)} {tail}".strip()


def acronym():
    tail = phrase(random.randint(0, 2))
    return f"{phrase(random.randint(1, 4))} {random.choice(ACRONYMS)} {tail}".strip()


def digits():
    chunks = []
    for _ in range(random.randint(2, 5)):
        if random.random() < 0.6:
            chunks.append(random.choice(ORDINALS))
        else:
            chunks.append(random.choice(WORDS))
    return " ".join(chunks)


def odd_spaces():
    sep = random.choice(SPACES)
    return sep.join(random.choice(WORDS) for _ in range(random.randint(2, 5)))


def notes_exact():
    return random.choice(NOTES_INPUTS)


def notes_embedded():
    example = random.choice(NOTES_INPUTS)
    side = random.randrange(3)
    if side == 0:
        return f"{phrase(random.randint(1, 3))} {example}"
    if side == 1:
        return f"{example} {phrase(random.randint(1, 3))}"
    return f"{phrase(1)} {example} {phrase(1)}"


def normal():
    n = random.randint(2, 8)
    parts = [random.choice(WORDS) for _ in range(n)]
    if n >= 3 and random.random() < 0.5:
        parts[random.randrange(1, n - 1)] = random.choice(SMALL)
    return " ".join(parts)


TRICKY = [
    small_middle,
    small_first_last,
    leading_punct,
    versus,
    subphrase,
    all_caps,
    initials,
    internal_caps,
    url_or_domain,
    apostrophe,
    mc_name,
    honorific,
    slash,
    hyphen,
    acronym,
    digits,
    odd_spaces,
    notes_exact,
    notes_embedded,
]


def make_title():
    if random.random() < 0.34:
        return normal()
    return random.choice(TRICKY)()


def write_lines(path, lines):
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="\n")


def expect(lines):
    out = []
    for index, line in enumerate(lines):
        if "\n" in line or "\r" in line:
            raise SystemExit(f"input {index} contains a newline")
        result = titlecase(line)
        if "\n" in result or "\r" in result:
            raise SystemExit(f"titlecase() split input {index} across lines: {line!r}")
        out.append(result)
    return out


def main():
    sys.path.insert(0, str(PY_TITLECASE))
    global titlecase
    from titlecase import titlecase  # noqa: E402

    random.seed(1)
    visible = [make_title() for _ in range(COUNT)]
    hidden = [make_title() for _ in range(COUNT)]
    if visible == hidden:
        raise SystemExit("visible and hidden inputs were identical")

    DATA.mkdir(parents=True, exist_ok=True)
    write_lines(DATA / "inputs.txt", visible)
    write_lines(DATA / "expected.txt", expect(visible))
    write_lines(DATA / "hidden_inputs.txt", hidden)
    write_lines(DATA / "hidden_expected.txt", expect(hidden))


if __name__ == "__main__":
    main()
