"""Freeze titlecase answers from the original Python function.

Run from anywhere. random.seed(1) makes both files identical across runs.
Expected files are never written by hand.
"""

import random
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
COUNT = 2000

WORDS = [
    "the", "of", "and", "a", "an", "in", "on", "to", "for", "but", "or", "nor",
    "vs.", "vs", "v", "v.", "via", "NASA", "iPhone", "iTunes", "e-mail",
    "O'Neil", "o'reilly", "l'grange", "mcdonald", "http://example.com/x",
    "https://en.wikipedia.org/wiki/Title_case", "3rd", "34th", "5th",
    "U.S.A.", "D.C.", "dr.", "Dr", "Mr", "Mrs", "Ms", "(the)", "CNN", "HTML",
    "AT&T", "Q&A", "McDonalds", "mcfoo", "example.com", "del.icio.us",
    "end-to-end", "and/or", "foo//bar", "PPPoE", "gym", "rhythm", "St",
    "nino", "cafe", "STATE", "episode",
]

SEPARATORS = [": ", "; ", ". ", "? ", "! ", " - ", " — ", " – ", " / "]


def make_title(rng: random.Random) -> str:
    kind = rng.randrange(12)
    if kind == 0:
        title = " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 9)))
    elif kind == 1:
        title = " ".join(rng.choice(WORDS) for _ in range(rng.randint(2, 8))).upper()
    elif kind == 2:
        left = rng.choice(WORDS)
        right = rng.choice(WORDS)
        title = f"{left}-{right}"
        if rng.randrange(2) == 0:
            title = f"{title}-{rng.choice(WORDS)}"
    elif kind == 3:
        title = f"{rng.choice(WORDS)}/{rng.choice(WORDS)}"
    elif kind == 4:
        title = rng.choice(SEPARATORS).join(
            rng.choice(WORDS) for _ in range(rng.randint(2, 4))
        )
    elif kind == 5:
        title = f"{rng.choice(['O', 'o', 'L', 'l', 'D'])}'{rng.choice(['neil', 'grange', 'angelo', 'Reilly'])}"
    elif kind == 6:
        title = f"{rng.choice(['Mr', 'mr', 'Mrs', 'Ms', 'Dr', 'dr', 'Mc', 'mc', 'MC'])} {rng.choice(WORDS)}"
    elif kind == 7:
        title = f"{rng.choice(WORDS)}  {rng.choice(WORDS)}\t{rng.choice(WORDS)}"
    elif kind == 8:
        title = f"({rng.choice(WORDS)}) {rng.choice(WORDS)}?"
    elif kind == 9:
        title = f"{rng.choice(['http://foo.com', 'example.com', 'iTunes', 'AT&T', 'Q&A', 'e.g'])} {rng.choice(WORDS)}"
    elif kind == 10:
        title = f"{rng.choice(WORDS)} of the {rng.choice(WORDS)}"
    else:
        title = rng.choice(
            [
                "the lord of the rings",
                "a title and/or string",
                "nothing to be afraid of",
                "this v. that",
                "this vs. that",
                "EPISODE 7 — THE FORCE AWAKENS",
                "Words with all consonants like cnn",
                "mac mc MAC MC machine",
                "WASHINGTON, D.C. SHOULD BE FIXED",
            ]
        )
    return title.replace("\n", " ").replace("\r", " ")


def write_pair(rng: random.Random, titlecase, inputs_name: str, expected_name: str, count: int) -> None:
    titles = [make_title(rng) for _ in range(count)]
    expected = [titlecase(title) for title in titles]
    for title, answer in zip(titles, expected):
        if "\n" in title or "\r" in title or "\n" in answer or "\r" in answer:
            raise SystemExit(f"newline leaked into a title: {title!r} -> {answer!r}")
    (DATA / inputs_name).write_text("\n".join(titles) + "\n", encoding="utf-8", newline="\n")
    (DATA / expected_name).write_text("\n".join(expected) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo))
    from titlecase import titlecase

    DATA.mkdir(parents=True, exist_ok=True)
    rng = random.Random(1)
    write_pair(rng, titlecase, "inputs.txt", "expected.txt", COUNT)
    write_pair(rng, titlecase, "hidden_inputs.txt", "hidden_expected.txt", COUNT)


if __name__ == "__main__":
    main()
