#!/usr/bin/env python3
"""Generate deterministic titlecase input and reference output data."""

from __future__ import annotations

import importlib.util
import random
from pathlib import Path

random.seed(1)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = Path(r"C:\Users\AdarshSahani\Desktop\python-titlecase\titlecase\__init__.py")
DATA = Path(__file__).resolve().parent / "data"


def load_original():
    spec = importlib.util.spec_from_file_location("original_titlecase", ORIGINAL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load original implementation: {ORIGINAL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.titlecase


def curated_titles():
    return [
        "the lord of the rings", "war and peace", "a tale of two cities",
        "the art of war", "hello: the world", "state-of-the-art",
        "mcdonald and mcnamara", "o'neil and d'artagnan", "dr smith and ms jones",
        "north/south and east/west", "NASA and HTML", "U.S.A. and the U.K.",
        "an example of a small word", "at the end of the road", "of mice and men",
        "in search of lost time", "a story: of the sea", "hello; and goodbye",
        "what? the answer", "stop! and go", "one - the other", "to be, or not to be",
        "(the beginning) and [the end]", "foo/bar/baz", "http://example.com/a/b",
        "mother-in-law's well-known book", "rock-n-roll", "x-ray and t-shirt",
        "mr smith", "mrs smith", "ms smith", "dr smith", "MRS JONES AND DR BROWN",
        "McDonald", "mccarthy", "MCINTYRE", "macdonald", "d'angelo", "l'esprit",
        "o'connor's book", "NASA's mission", "they're here", "dogs' toys",
        "iPhone and eBay", "mIXed CaSe", "XMLParser and IPv6Address",
        "foo.bar and example.com", "a.b test", "U.S.A.", "F.B.I. report",
        "NASA AND HTML", "THE LORD OF THE RINGS", "A TALE OF TWO CITIES",
        "THE QUICK BROWN FOX", "CNN vs BBC", "ABCDEF and XYZ",
        "bcdfghjklmnpqrstvwxz", "rhythms", "st", "tsk", "WHY",
        "café and the naïve", "élan vital", "über alles", "東京 and 京都",
        "доброе утро", "mañana será otro día", "straße und café",
        "  the  art   of war  ", "\tthe\tquick\tbrown fox\t", "a\u00a0tale\u00a0of two",
        "", "   ", "\t", "one\ntwo", "line one\rline two",
        "a: the beginning; of the end? and then! the conclusion",
        "foo—bar and foo–baz", "say “hello” to the world", "a/b-c/d",
        "one//two and three/four", "semi:colon and sub-phrase",
        "V. the winner vs. the runner-up", "en route to the city",
        "by and large, a matter of fact", "the end of a long, winding road",
    ]


def make_title():
    words = [
        "the", "a", "an", "and", "of", "to", "in", "on", "by", "vs", "via",
        "north", "south", "east", "west", "river", "moon", "star", "world",
        "NASA", "HTML", "iPhone", "McArthur", "o'brien", "d'angelo", "Dr",
        "Mrs", "Ms", "Mr", "café", "東京", "ABC", "rhythms", "bcdfg",
        "foo.bar", "U.S.A.", "eBay", "rock", "roll", "mother", "well",
    ]
    seps = [" ", "  ", "\t", "-", "–", "/", ": ", "; ", "? ", "! ", ", ", "'", ""]
    count = random.randint(2, 7)
    pieces = [random.choice(words)]
    for _ in range(count - 1):
        pieces.extend((random.choice(seps), random.choice(words)))
    value = "".join(pieces)
    # Include case and outer-whitespace variants while keeping one physical input line.
    variant = random.randrange(5)
    if variant == 0:
        value = value.upper()
    elif variant == 1:
        value = value.title()
    elif variant == 2:
        value = value.swapcase()
    if random.randrange(8) == 0:
        value = "  " + value
    if random.randrange(8) == 0:
        value += "  "
    return value


def build_titles(count, reserved):
    result = []
    seen = set(reserved)
    for value in curated_titles():
        if value not in seen and "\n" not in value and "\r" not in value:
            result.append(value)
            seen.add(value)
    while len(result) < count:
        value = make_title()
        if value not in seen and "\n" not in value and "\r" not in value:
            result.append(value)
            seen.add(value)
    return result


def write_lines(path, values):
    if len(values) != 2000:
        raise ValueError(f"{path} has {len(values)} records, expected 2000")
    if any("\n" in value or "\r" in value for value in values):
        raise ValueError(f"Embedded line break found in {path}")
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for value in values:
            stream.write(value + "\n")


def main():
    titlecase = load_original()
    DATA.mkdir(parents=True, exist_ok=True)
    visible = build_titles(2000, set())
    hidden = build_titles(2000, set(visible))
    if set(visible) & set(hidden):
        raise ValueError("Visible and hidden inputs overlap")

    write_lines(DATA / "inputs.txt", visible)
    write_lines(DATA / "expected.txt", [titlecase(value) for value in visible])
    write_lines(DATA / "hidden_inputs.txt", hidden)
    write_lines(DATA / "hidden_expected.txt", [titlecase(value) for value in hidden])

    for name in ("inputs.txt", "expected.txt", "hidden_inputs.txt", "hidden_expected.txt"):
        raw = (DATA / name).read_bytes()
        if raw.count(b"\n") != 2000:
            raise ValueError(f"{name} does not have exactly 2000 newline-delimited records")


if __name__ == "__main__":
    main()
