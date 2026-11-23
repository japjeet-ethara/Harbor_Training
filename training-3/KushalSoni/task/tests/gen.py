"""Generate fixed titlecase fixtures from the original Python implementation."""

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "environment" / "python-titlecase"))

try:
    from titlecase import titlecase
except ImportError:
    titlecase = None

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
    "quick",
    "brown",
    "fox",
    "jumps",
    "over",
    "lazy",
    "dog",
    "history",
    "science",
    "market",
    "report",
    "final",
    "draft",
    "notes",
    "project",
    "guide",
    "chapter",
    "review",
    "simple",
    "wrapper",
    "remote",
    "village",
    "golden",
    "river",
    "ancient",
    "bridge",
    "public",
    "library",
    "winter",
    "storm",
    "open",
    "source",
    "design",
    "pattern",
    "user",
    "manual",
    "silent",
    "harbor",
    "copper",
    "lantern",
    "morning",
    "paper",
    "secret",
    "garden",
    "silver",
    "compass",
    "northern",
    "light",
    "broken",
    "window",
    "clever",
    "machine",
    "quiet",
    "street",
    "yellow",
    "bicycle",
    "famous",
    "painter",
    "little",
    "theater",
    "crystal",
    "radio",
    "hidden",
    "valley",
]
PRESERVED = ["NASA", "HTML", "iPhone", "macOS", "eBay"]
URLS = ["example.com", "https://google.com", "support@example.com"]


def phrase(min_n=3, max_n=7):
    count = random.randint(min_n, max_n)
    parts = []
    for index in range(count):
        if index not in (0, count - 1) and random.random() < 0.45:
            parts.append(random.choice(SMALL))
        else:
            parts.append(random.choice(NORMAL))
    return " ".join(parts)


def title():
    kind = random.choice(
        [
            "normal",
            "normal",
            "normal",
            "small",
            "colon",
            "hyphen",
            "slash",
            "quotes",
            "brackets",
            "acronym",
            "url",
        ]
    )
    if kind == "normal":
        return phrase()
    if kind == "small":
        return " ".join(
            [
                random.choice(SMALL),
                random.choice(NORMAL),
                random.choice(SMALL),
                random.choice(NORMAL),
                random.choice(SMALL),
            ]
        )
    if kind == "colon":
        return f"{phrase(2, 4)}: {random.choice(SMALL)} {phrase(2, 4)}"
    if kind == "hyphen":
        if random.random() < 0.5:
            return f"{phrase(1, 3)} state-of-the-art {phrase(1, 3)}"
        left = random.choice(NORMAL)
        middle = random.choice(["of", "the", "and", "to"])
        right = random.choice(NORMAL)
        return f"{phrase(1, 2)} {left}-{middle}-{right} {phrase(1, 2)}"
    if kind == "slash":
        if random.random() < 0.5:
            return f"{phrase(1, 3)} input/output {phrase(1, 3)}"
        return (
            f"{phrase(1, 2)} {random.choice(NORMAL)}/{random.choice(NORMAL)} "
            f"{phrase(1, 2)}"
        )
    if kind == "quotes":
        if random.random() < 0.5:
            return f'{phrase(1, 3)} "the ring" {phrase(1, 3)}'
        small = random.choice(SMALL)
        word = random.choice(NORMAL)
        return f'{phrase(1, 2)} "{small} {word}" {phrase(1, 2)}'
    if kind == "brackets":
        small = random.choice(SMALL)
        word = random.choice(NORMAL)
        bracketed = random.choice([f"({small} {word})", f"[{small} {word}]"])
        return f"{phrase(1, 3)} {bracketed} {phrase(1, 2)}"
    if kind == "acronym":
        return f"{phrase(1, 3)} {random.choice(PRESERVED)} {phrase(1, 3)}"
    return f"{phrase(1, 3)} {random.choice(URLS)} {phrase(1, 3)}"


def write_pair(source_path, expected_path, lines):
    expected = []
    for line in lines:
        if "\n" in line or "\r" in line:
            raise SystemExit("generated title contains a line break")
        result = titlecase(line)
        if not isinstance(result, str) or "\n" in result or "\r" in result:
            raise SystemExit("titlecase() did not return a single line")
        expected.append(result)
    source_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    expected_path.write_text("\n".join(expected) + "\n", encoding="utf-8")


def main():
    if titlecase is None:
        raise SystemExit("titlecase() is not importable")
    random.seed(1)
    data = Path(__file__).resolve().parent / "data"
    data.mkdir(parents=True, exist_ok=True)
    inputs = [title() for _ in range(2000)]
    hidden = [title() for _ in range(2000)]
    if inputs == hidden:
        raise SystemExit("hidden inputs must be a different set")
    write_pair(data / "inputs.txt", data / "expected.txt", inputs)
    write_pair(data / "hidden_inputs.txt", data / "hidden_expected.txt", hidden)


if __name__ == "__main__":
    main()
