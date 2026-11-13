"""Freeze titlecase answers from the original Python package.

Expected files are produced only by calling titlecase(). Do not edit them by hand.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
SOURCE = Path(__file__).resolve().parents[2] / "python-titlecase"

WORDS = [
    "lord", "rings", "apple", "steve", "jobs", "music", "plane", "force",
    "awakens", "washington", "problem", "technology", "string", "dance",
    "permissions", "voodoo", "jackass", "franco", "generalissimo", "still",
    "dead", "episode", "famous", "line", "nothing", "afraid", "quotes",
    "trick", "perhaps", "between", "reading", "thoughts", "repair",
    "seriously", "example", "listed", "something", "unmolested", "should",
    "consonants", "acronyms", "probe", "need", "know", "small", "start",
    "within", "end", "title", "machine", "spool", "gruber",
]
SMALL = ["a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "via", "vs", "v"]
MC = ["McTavish", "MacDonalds", "mcfoo", "MCFOO", "McCarthy", "mcdonalds", "mcby"]
APOS = ["o'reilly", "O'Reilly", "l'grange", "L'Grange", "o'clock", "d'angelo", "o'grady"]
URLS = ["http://foo.com", "example.com", "del.icio.us", "https://example.com/a"]
HYPHEN = ["end-to-end", "two-not-three", "a-b", "state-of-the-art", "mcfoo-mcbar"]
SLASH = ["word/word", "and/or", "three-by-four/five-and", "me/let"]
INITIALS = ["D.C.", "U.S.", "A.B.", "Q&A", "AT&T"]
UNICODE = ["niño", "arrivé", "crème", "brûlée", "él", "ÑØ", "ÝÆ"]


def one_title(rng: random.Random) -> str:
    kind = rng.randrange(12)
    if kind == 0:
        parts = [rng.choice(WORDS) for _ in range(rng.randint(2, 8))]
        parts.insert(rng.randint(0, len(parts)), rng.choice(SMALL))
        text = " ".join(parts)
    elif kind == 1:
        text = " ".join(rng.choice(WORDS) for _ in range(rng.randint(3, 7)))
        text = text.upper()
    elif kind == 2:
        text = f"{rng.choice(WORDS)} {rng.choice(MC)} {rng.choice(SMALL)} {rng.choice(WORDS)}"
    elif kind == 3:
        text = f"{rng.choice(WORDS)} {rng.choice(APOS)} {rng.choice(SMALL)} {rng.choice(WORDS)}"
    elif kind == 4:
        text = f"this is {rng.choice(URLS)}"
    elif kind == 5:
        text = f"{rng.choice(WORDS)} {rng.choice(HYPHEN)} {rng.choice(SLASH)}"
    elif kind == 6:
        text = f"{rng.choice(INITIALS)} with {rng.choice(WORDS)}: {rng.choice(SMALL)} {rng.choice(WORDS)}"
    elif kind == 7:
        text = f"{rng.choice(UNICODE)} {rng.choice(SMALL)} {rng.choice(UNICODE)}"
    elif kind == 8:
        text = f"Starting a sub-phrase: {rng.choice(SMALL)} {rng.choice(WORDS)}, perhaps?"
    elif kind == 9:
        text = f"iTunes CNN nasa {rng.choice(WORDS)} {rng.choice(SMALL)} {rng.choice(WORDS)}"
    elif kind == 10:
        text = f"Mr {rng.choice(MC)} vs. {rng.choice(WORDS)} — {rng.choice(SMALL)} {rng.choice(WORDS)}"
    else:
        text = f"'{rng.choice(SMALL)} {rng.choice(WORDS)}' and/or {rng.choice(HYPHEN)}"
    return text.replace("\n", " ").replace("\r", " ")


def write_pair(rng: random.Random, titlecase, inputs: Path, expected: Path, count: int) -> None:
    lines = [one_title(rng) for _ in range(count)]
    answers = [titlecase(line) for line in lines]
    inputs.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    expected.write_text("\n".join(answers) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    sys.path.insert(0, str(SOURCE))
    from titlecase import titlecase

    DATA.mkdir(parents=True, exist_ok=True)
    rng = random.Random(1)
    write_pair(rng, titlecase, DATA / "inputs.txt", DATA / "expected.txt", 2000)
    write_pair(
        rng,
        titlecase,
        DATA / "hidden_inputs.txt",
        DATA / "hidden_expected.txt",
        2000,
    )


if __name__ == "__main__":
    main()
