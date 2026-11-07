"""Create deterministic visible and hidden corpora using the original source."""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "environment" / "repo"
sys.path.insert(0, str(REFERENCE))
from titlecase import titlecase  # noqa: E402

SMALL = ["a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to", "v", "via", "vs"]
WORDS = ["adventure", "chronicles", "galaxy", "harbor", "journey", "kingdom", "legend", "mystery", "night", "ocean", "planet", "quest", "return", "story", "tower", "worlds"]
SPECIAL = ["NASA", "BBC", "iPhone", "eBay", "mcdonald", "macarthur", "dr", "mrs", "o'connor", "d'artagnan", "state-of-the-art", "input/output", "A.B.", "x.y", "https://example.com"]
PUNCT = ["", "", "", ": the", " - a", "? an", "; the"]


def make_title(rng: random.Random) -> str:
    n = rng.randint(3, 9)
    tokens = [rng.choice(WORDS + SMALL + SPECIAL) for _ in range(n)]
    if rng.random() < 0.55:
        tokens[rng.randrange(n)] = rng.choice(SPECIAL)
    text = " ".join(tokens)
    if rng.random() < 0.25:
        text += rng.choice(PUNCT)
    if rng.random() < 0.20:
        text = text.upper()
    return text


def write_set(rng: random.Random, inputs: Path, expected: Path) -> None:
    values = [make_title(rng) for _ in range(2000)]
    inputs.write_text("\n".join(values) + "\n", encoding="utf-8")
    expected.write_text("\n".join(titlecase(value) for value in values) + "\n", encoding="utf-8")


def main() -> None:
    data = Path(__file__).resolve().parent / "data"
    data.mkdir(exist_ok=True)
    rng = random.Random(1)
    write_set(rng, data / "inputs.txt", data / "expected.txt")
    write_set(rng, data / "hidden_inputs.txt", data / "hidden_expected.txt")


if __name__ == "__main__":
    main()
